"""
flame_analyzer.py
~~~~~~~~~~~~~~~~
解析 async-profiler 生成的 HTML 火焰图，提取 Top5 热路径，
并生成结构化 Markdown 报告和 AI Agent 分析 Prompt。

用法:
    python flame_analyzer.py <html_path> [output_dir]

输出:
    <output_dir>/hotpaths.md          — 热路径结构化报告
    <output_dir>/analysis_prompt.md   — AI Agent 分析 Prompt
"""

import io
import re
import heapq
import sys
import logging
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

# 可选的进度条支持
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

    # 提供一个简单的进度条替代
    class tqdm:
        def __init__(self, iterable=None, desc=None, total=None, **kwargs):
            self.iterable = iterable
            self.desc = desc or ""
            self.total = total
            self.count = 0

        def __enter__(self):
            if self.desc:
                print(f"{self.desc}...")
            return self

        def __exit__(self, *args):
            if self.desc:
                print(f"{self.desc}...完成")

        def __iter__(self):
            for item in self.iterable:
                yield item
                self.count += 1

        def update(self, n=1):
            self.count += n

# ─────────────────────────────────────────────
# 配置和异常类
# ─────────────────────────────────────────────

@dataclass
class AnalyzerConfig:
    """火焰图分析器配置"""
    max_depth: int = 200
    min_pct: float = 0.005
    top_n_paths: int = 5
    encoding: str = "utf-8"
    enable_logging: bool = False
    log_level: str = "INFO"

    @classmethod
    def from_file(cls, config_path: str) -> "AnalyzerConfig":
        """从JSON配置文件加载配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            return cls(**config_data)
        except Exception as e:
            logging.warning(f"无法加载配置文件 {config_path}: {e}，使用默认配置")
            return cls()


class FlameAnalyzerError(Exception):
    """火焰图分析器基础异常"""
    pass


class ParseError(FlameAnalyzerError):
    """解析错误"""
    pass


class ValidationError(FlameAnalyzerError):
    """验证错误"""
    pass


# ─────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────

@dataclass
class Frame:
    """火焰图中的单个调用帧"""
    level: int
    left: int
    width: int
    title: str
    children: List["Frame"] = field(default_factory=list)
    parent: Optional["Frame"] = field(default=None, repr=False)

    @property
    def right(self) -> int:
        return self.left + self.width

    def short_title(self) -> str:
        """去掉包名前缀，保留类名.方法名"""
        t = self.title
        # 去掉 io/opentelemetry/... 之类的路径，保留最后两段
        if "/" in t:
            parts = t.split("/")
            t = parts[-1]
        return t


@dataclass
class HotPath:
    """一条完整的热路径"""
    frames: List[Frame]          # 从 root 到叶节点（或截断点）的帧序列
    leaf_width: int              # 叶节点（最深处）的采样数
    root_samples: int            # 总采样数
    truncated: bool = False      # 是否被截断
    truncated_levels: int = 0    # 省略的层数

    @property
    def percentage(self) -> float:
        return 100.0 * self.leaf_width / self.root_samples if self.root_samples else 0.0

    @property
    def leaf_frame(self) -> Frame:
        return self.frames[-1]


# ─────────────────────────────────────────────
# 第一层：解析 HTML，构建调用树
# ─────────────────────────────────────────────

# 正则：匹配 f(level, left, width, type, 'title'[, ...])
# title 可能含转义字符，用 (?:[^'\\]|\\.)* 处理
# 编译时添加 MULTILINE 标志以提升性能
_FRAME_RE = re.compile(
    r"f\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*\d+\s*,'((?:[^'\\]|\\.)*)'",
    re.MULTILINE
)


def parse_flame_html(html_path: str, config: AnalyzerConfig = None) -> List[Frame]:
    """
    解析 async-profiler HTML 火焰图文件，提取所有帧数据。

    Args:
        html_path: HTML 文件路径
        config: 分析器配置

    Returns:
        帧列表，每个帧含 level/left/width/title

    Raises:
        FileNotFoundError: 文件不存在时
        ParseError: 文件格式不正确时
        ValidationError: 文件内容验证失败时
    """
    if config is None:
        config = AnalyzerConfig()

    path = Path(html_path)
    if not path.exists():
        raise FileNotFoundError(f"火焰图文件不存在: {html_path}")

    # 验证文件大小
    file_size = path.stat().st_size
    if file_size == 0:
        raise ValidationError(f"文件为空: {html_path}")
    if file_size > 100 * 1024 * 1024:  # 100MB限制
        logging.warning(f"文件较大 ({file_size / (1024*1024):.1f}MB)，处理可能需要较长时间")

    try:
        # 分块读取大文件
        if file_size > 10 * 1024 * 1024:  # 10MB以上文件分块处理
            content = _read_large_file(path, config.encoding)
        else:
            content = path.read_text(encoding=config.encoding, errors="replace")
    except Exception as e:
        raise ParseError(f"读取文件失败: {e}")

    # 验证是否为有效的火焰图文件
    if "f(" not in content:
        raise ValidationError("文件不包含火焰图数据（未找到 'f(' 模式）")

    matches = _FRAME_RE.findall(content)
    if not matches:
        raise ParseError("未找到有效的帧数据")

    frames = []
    try:
        for i, (level_s, left_s, width_s, title_raw) in enumerate(matches):
            # 处理转义字符：\' → '，\\ → \
            title = title_raw.replace("\\'", "'").replace("\\\\", "\\")

            frame = Frame(
                level=int(level_s),
                left=int(left_s),
                width=int(width_s),
                title=title,
            )

            # 基本验证
            if frame.level < 0 or frame.width <= 0:
                logging.warning(f"跳过无效帧 #{i}: level={frame.level}, width={frame.width}")
                continue

            frames.append(frame)
    except ValueError as e:
        raise ParseError(f"帧数据解析失败: {e}")

    if not frames:
        raise ParseError("没有解析到有效的帧数据")

    logging.info(f"成功解析 {len(frames):,} 个帧")
    return frames


def _read_large_file(path: Path, encoding: str) -> str:
    """分块读取大文件"""
    content_parts = []
    chunk_size = 1024 * 1024  # 1MB chunks

    with open(path, 'r', encoding=encoding, errors="replace") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            content_parts.append(chunk)

    return ''.join(content_parts)


def build_call_tree(frames: List[Frame]) -> Frame:
    """
    根据 level + 区间包含关系构建调用树，返回 root 节点。

    父节点条件：
        parent.level == child.level - 1
        AND parent.left <= child.left
        AND parent.right >= child.right

    孤儿节点（找不到父节点）挂到 root 下。

    Args:
        frames: parse_flame_html 返回的帧列表

    Returns:
        root Frame（level == 0 的节点）
    """
    if not frames:
        raise ValueError("帧列表为空，无法构建调用树")

    # 找到 root（level == 0）
    root_candidates = [f for f in frames if f.level == 0]
    if not root_candidates:
        raise ValueError("未找到 level=0 的根节点")
    root = root_candidates[0]

    # 按 level 分组，便于快速查找父节点
    levels: dict[int, List[Frame]] = {}
    for f in frames:
        levels.setdefault(f.level, []).append(f)

    # 从 level=1 开始，为每个节点寻找父节点
    for level_idx in sorted(k for k in levels if k > 0):
        parent_level = levels.get(level_idx - 1, [])
        for child in levels[level_idx]:
            parent_found = False
            for parent in parent_level:
                if (parent.left <= child.left and parent.right >= child.right):
                    parent.children.append(child)
                    child.parent = parent
                    parent_found = True
                    break
            # 孤儿节点挂到 root
            if not parent_found and child is not root:
                root.children.append(child)
                child.parent = root

    return root


# ─────────────────────────────────────────────
# 第二层：提取 TopN 热路径
# ─────────────────────────────────────────────

def extract_top_hotpaths(root: Frame, root_samples: int, config: AnalyzerConfig = None) -> List[HotPath]:
    """
    提取 TopN 热路径。

    策略：
    - 用优先队列按分叉点节点 width 降序取候选
    - 从分叉点开始贪心往下走（每步取最宽子节点）到叶节点，得到完整路径
    - 路径代表性宽度 = 分叉点节点的 width（不是真叶节点的 width）
    - 同一分叉点不重复，保证路径多样性
    - 分叉点占比 < config.min_pct 时过滤

    Args:
        root: 调用树根节点
        root_samples: 总采样数
        config: 分析器配置

    Returns:
        最多 config.top_n_paths 条热路径列表，按占比降序排列
    """
    if config is None:
        config = AnalyzerConfig()

    if root_samples <= 0:
        raise ValidationError(f"无效的总采样数: {root_samples}")

    results: List[HotPath] = []
    visited: set = set()  # 已处理的分叉点节点 id

    # 堆元素：(-branch_width, node_id, path_to_branch, branch_node)
    heap: list = []
    for child in sorted(root.children, key=lambda c: c.width, reverse=True):
        heapq.heappush(heap, (-child.width, id(child), [root], child))

    while heap and len(results) < config.top_n_paths:
        neg_width, node_id, path_prefix, branch_node = heapq.heappop(heap)

        if node_id in visited:
            continue
        visited.add(node_id)

        branch_width = branch_node.width
        if branch_width / root_samples < config.min_pct:
            continue  # 该分支占比太低，跳过

        # 从 branch_node 贪心往下走到叶节点，拼接完整路径
        full_path = list(path_prefix) + [branch_node]
        cur = branch_node
        depth = 1  # 已经包含了branch_node

        while cur.children and depth < config.max_depth:
            best = max(cur.children, key=lambda c: c.width)
            full_path.append(best)
            cur = best
            depth += 1

        # 检查是否被截断
        truncated = depth >= config.max_depth and cur.children
        truncated_levels = _count_max_depth(cur) if truncated else 0

        results.append(HotPath(
            frames=full_path,
            leaf_width=branch_width,   # 用分叉点宽度代表路径热度
            root_samples=root_samples,
            truncated=truncated,
            truncated_levels=truncated_levels,
        ))

        # 把 branch_node 的次宽子节点入堆，形成下一批候选路径
        if branch_node.children:
            for child in sorted(branch_node.children, key=lambda c: c.width, reverse=True)[1:]:
                if id(child) not in visited:
                    heapq.heappush(heap, (-child.width, id(child), list(path_prefix) + [branch_node], child))

    logging.info(f"提取到 {len(results)} 条热路径")
    return results


def _find_max_leaf_width(node: Frame) -> int:
    """找到子树中最宽叶节点的 width"""
    if not node.children:
        return node.width
    return max(_find_max_leaf_width(c) for c in node.children)


def _count_max_depth(node: Frame) -> int:
    """统计子树的最大深度"""
    if not node.children:
        return 0
    return 1 + max(_count_max_depth(c) for c in node.children)


# ─────────────────────────────────────────────
# 第三层：生成热路径 Markdown 报告
# ─────────────────────────────────────────────

def write_hotpaths_md(
    hotpaths: List[HotPath],
    output_path: str,
    source_file: str,
    root_samples: int,
    config: AnalyzerConfig = None,
) -> None:
    """
    将 TopN 热路径写入结构化 Markdown 报告。

    Args:
        hotpaths: 热路径列表
        output_path: 输出文件路径
        source_file: 原始火焰图文件名
        root_samples: 总采样数
        config: 分析器配置
    """
    if config is None:
        config = AnalyzerConfig()

    lines = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    source_name = Path(source_file).name

    # ── 头部元信息 ──
    lines.append("# 火焰图热路径分析报告\n")
    lines.append(f"> **文件**: `{source_name}`  ")
    lines.append(f"> **总采样**: {root_samples:,} samples  ")
    lines.append(f"> **分析时间**: {now}  ")
    lines.append(f"> **提取策略**: Top{config.top_n_paths} 热路径（占比 ≥ {config.min_pct*100:.1f}%，完整调用链路）\n")

    # ── TopN 占比概览 ──
    lines.append("## 概览\n")
    lines.append("| # | 叶节点函数 | 占比 | 采样数 |")
    lines.append("|---|-----------|------|--------|")
    for i, hp in enumerate(hotpaths, 1):
        leaf_name = hp.leaf_frame.short_title()
        suffix = " *(截断)*" if hp.truncated else ""
        lines.append(f"| {i} | `{leaf_name}`{suffix} | {hp.percentage:.2f}% | {hp.leaf_width:,} |")
    lines.append("")

    # ── 每条热路径详情 ──
    for i, hp in enumerate(hotpaths, 1):
        lines.append(f"---\n")
        lines.append(f"## 🔥 热路径 #{i} — 占比 {hp.percentage:.2f}% ({hp.leaf_width:,} samples)\n")

        # 树形展示：完整输出所有层，display_depth 从 0 开始连续编号
        lines.append("```")
        frames = hp.frames
        total = len(frames)

        def _render(display_depth: int, frame: Frame, is_last: bool) -> str:
            prefix = _tree_prefix(display_depth, is_last)
            pct_str = f"{100.0 * frame.width / root_samples:.2f}%"
            return f"{prefix}{frame.title} ({pct_str})"

        for idx in range(total):
            is_last = (idx == total - 1) and not hp.truncated
            lines.append(_render(idx, frames[idx], is_last))

        if hp.truncated:
            indent = "   " * total
            lines.append(f"{indent}... (后续约 {hp.truncated_levels} 层已截断)")
        lines.append("```\n")

    output = "\n".join(lines)
    Path(output_path).write_text(output, encoding=config.encoding)
    logging.info(f"热路径报告已写入: {output_path}")


def _tree_prefix(depth: int, is_last: bool) -> str:
    """生成树形缩进前缀"""
    if depth == 0:
        return ""
    indent = "   " * (depth - 1)
    connector = "└─ " if is_last else "├─ "
    return indent + connector

# ─────────────────────────────────────────────
# 第四层：生成 AI Agent 分析 Prompt
# ─────────────────────────────────────────────

def gen_analysis_prompt(hotpaths_md_path: str, output_path: str) -> None:
    """
    读取 hotpaths.md，生成面向 AI Agent 的结构化分析 Prompt。

    Prompt 结构（三段式）：
        1. 角色定义
        2. 热路径数据（内嵌 hotpaths.md 全文）
        3. 结构化分析任务（四项）

    Args:
        hotpaths_md_path: hotpaths.md 文件路径
        output_path: 输出 analysis_prompt.md 路径
    """
    hotpaths_content = Path(hotpaths_md_path).read_text(encoding="utf-8")

    prompt = f"""# Java 性能分析 Prompt

> 本文件由 flame_analyzer.py 自动生成，可直接作为 AI Agent 的输入 Prompt。

---

## 【角色定义】

你是一位资深 Java 性能工程师，拥有以下专业能力：
- 深入理解 JVM 运行原理（GC、JIT、类加载、线程模型）
- 熟悉 Java 并发编程和锁竞争分析
- 擅长解读 async-profiler / JFR / arthas 等性能工具输出
- 能够从调用栈数据中快速定位性能瓶颈并给出可落地的优化方案

---

## 【热路径数据】

以下是从 async-profiler 火焰图中自动提取的 Top5 热路径数据：

{hotpaths_content}

---

## 【分析任务】

请针对上述热路径数据，依次完成以下四项分析：

### 任务一：热点诊断

对每条热路径进行逐一分析：
- 识别真正的 CPU 热点函数（区分业务代码 vs JVM 框架/OpenTelemetry 开销）
- 判断热点类型：CPU 密集 / IO 等待 / 锁阻塞 / 内存分配 / 其他
- 评估每条路径的优化价值（高/中/低）

### 任务二：模式识别

从全局视角识别以下常见性能模式（有则分析，无则注明）：
- **锁竞争**：是否出现 `ObjectMonitor`、`synchronized`、`ReentrantLock` 相关调用？
- **GC 压力**：是否有频繁对象分配或 GC 相关调用链？
- **IO 阻塞**：是否有 Socket/File/DB 相关的阻塞调用？
- **框架开销**：Spring/OpenTelemetry/动态代理等框架本身的 CPU 占比是否过高？

### 任务三：优化建议

针对识别出的热点，结合项目代码分析，给出具体可操作的优化建议：

每条建议须包含：
- **问题描述**：具体是什么导致了性能消耗
- **优化方向**：代码级（算法/数据结构改进）/ JVM 参数级 / 架构级
- **改动范围**：需要修改哪些类/方法/配置
- **预期收益**：预计可降低多少 CPU 占比

### 任务四：优先级排序

将所有优化建议按「收益/难度」矩阵排序，输出如下格式：

| 优先级 | 优化项 | 预期收益 | 实施难度 | 推荐理由 |
|--------|--------|----------|----------|----------|
| P0 | ... | 高 | 低 | ... |
| P1 | ... | 中 | 中 | ... |
| P2 | ... | 低 | 高 | ... |

---

## 【输出要求】

- 使用 Markdown 格式输出，结构清晰
- 函数名用反引号标注，如 `ConcurrentHashMap.replaceNode`
- 每项分析都需有据可依（引用热路径数据中的具体数字）
- 优化建议须具体可执行，避免泛泛而谈
"""

    Path(output_path).write_text(prompt, encoding="utf-8")
    logging.info(f"分析 Prompt 已写入: {output_path}")


# ─────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────

def main(html_path: str, output_dir: str = ".", config_path: str = None) -> None:
    """
    串联四层逻辑，解析火焰图并生成输出文件。

    Args:
        html_path: async-profiler HTML 文件路径
        output_dir: 输出目录（默认当前目录）
        config_path: 配置文件路径（可选）
    """
    # 加载配置
    config = AnalyzerConfig.from_file(config_path) if config_path else AnalyzerConfig()

    # 配置日志
    if config.enable_logging:
        logging.basicConfig(
            level=getattr(logging, config.log_level, logging.INFO),
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    hotpaths_md = str(output_path / "hotpaths.md")
    prompt_md = str(output_path / "analysis_prompt.md")

    print(f"\n[flame_analyzer] 开始分析: {Path(html_path).name}")
    print("─" * 60)
    print(f"输出目录: {output_path.absolute()}")
    print(f"配置: 最大深度={config.max_depth}, 最小占比={config.min_pct*100:.1f}%, Top路径数={config.top_n_paths}")
    print("─" * 60)

    start_time = datetime.now()

    try:
        # Step 1: 解析 HTML，构建调用树
        with tqdm(desc="Step 1: 解析 HTML 火焰图", unit="frames") as pbar:
            frames = parse_flame_html(html_path, config)
            pbar.total = len(frames)
            pbar.update(len(frames))

        with tqdm(desc="构建调用树", total=1) as pbar:
            root = build_call_tree(frames)
            root_samples = root.width
            pbar.update(1)

        print(f"  解析完成: {len(frames):,} 个帧，总采样 {root_samples:,}")

        # Step 2: 提取 TopN 热路径
        with tqdm(desc="Step 2: 提取热路径", total=config.top_n_paths) as pbar:
            hotpaths = extract_top_hotpaths(root, root_samples, config)
            pbar.total = len(hotpaths)
            pbar.update(len(hotpaths))

        print(f"  提取完成: {len(hotpaths)} 条热路径")
        for i, hp in enumerate(hotpaths, 1):
            print(f"     #{i}: {hp.percentage:.2f}% — {hp.leaf_frame.short_title()}")

        # Step 3: 生成热路径报告
        with tqdm(desc="Step 3: 生成热路径报告", total=1) as pbar:
            write_hotpaths_md(hotpaths, hotpaths_md, html_path, root_samples, config)
            pbar.update(1)

        # Step 4: 生成分析 Prompt
        with tqdm(desc="Step 4: 生成 AI 分析 Prompt", total=1) as pbar:
            gen_analysis_prompt(hotpaths_md, prompt_md)
            pbar.update(1)

        # 计算耗时
        elapsed = datetime.now() - start_time
        elapsed_str = f"{elapsed.total_seconds():.1f}s"

        print("─" * 60)
        print(f"[flame_analyzer] 分析完成！耗时: {elapsed_str}")
        print(f"输出文件:")
        print(f"   {Path(hotpaths_md).name} — 热路径分析报告")
        print(f"   {Path(prompt_md).name} — AI 分析 Prompt")
        print(f"\n提示:")
        print(f"   1. 可使用 AI 工具分析 {Path(prompt_md).name} 获得优化建议")
        print(f"   2. 查看 {Path(hotpaths_md).name} 了解详细的热路径信息")
        if not TQDM_AVAILABLE:
            print(f"   3. 安装 tqdm (pip install tqdm) 获得更好的进度显示\n")

    except (FileNotFoundError, ParseError, ValidationError) as e:
        print(f"分析失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"意外错误: {e}")
        if config.enable_logging:
            logging.exception("详细错误信息:")
        sys.exit(1)


if __name__ == "__main__":
    # Windows 下强制 stdout 使用 UTF-8，避免 GBK 编码错误
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    if len(sys.argv) < 2:
        print("用法: python flame_analyzer.py <html_path> [output_dir] [config_file]")
        print("参数:")
        print("  html_path   - async-profiler HTML 火焰图文件路径")
        print("  output_dir  - 输出目录（可选，默认当前目录）")
        print("  config_file - JSON配置文件路径（可选）")
        print("\n示例:")
        print("  python flame_analyzer.py profile.html")
        print("  python flame_analyzer.py profile.html ./output")
        print("  python flame_analyzer.py profile.html ./output config.json")
        print("\n配置文件示例 (config.json):")
        config_example = {
            "max_depth": 150,
            "min_pct": 0.01,
            "top_n_paths": 3,
            "encoding": "utf-8",
            "enable_logging": True,
            "log_level": "DEBUG"
        }
        print(json.dumps(config_example, indent=2, ensure_ascii=False))
        sys.exit(1)

    _html_path = sys.argv[1]
    _output_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    _config_path = sys.argv[3] if len(sys.argv) > 3 else None

    main(_html_path, _output_dir, _config_path)
