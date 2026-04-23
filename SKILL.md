---
name: flame-analyzer
description: |
  分析 async-profiler 生成的 Java HTML 火焰图，自动提取 TopN 热路径并生成结构化报告和 AI 优化分析提示。
tools:
  - Bash
  - Read
  - Write
  - Glob
---

当用户请求分析火焰图时，按以下步骤执行：

## 执行步骤

1. **确认输入参数**
   - `html_path`（必需）：async-profiler 生成的 HTML 火焰图文件路径
   - `output_dir`（可选）：输出目录，默认为当前目录
   - `config_file`（可选）：JSON 配置文件路径

2. **验证文件**
   - 确认 `html_path` 文件存在且可读
   - 如未提供参数，询问用户提供火焰图文件路径

3. **运行分析脚本**

```bash
python scripts/flame_analyzer.py <html_path> [output_dir] [config_file]
```

示例：
```bash
# 基本分析
python scripts/flame_analyzer.py profile.html

# 指定输出目录
python scripts/flame_analyzer.py data/cpu-profile.html ./analysis

# 使用自定义配置
python scripts/flame_analyzer.py profile.html ./output config/debug.json
```

4. **读取并展示结果**
   - 读取生成的 `hotpaths.md`，向用户展示 TopN 热路径摘要
   - 告知用户 `analysis_prompt.md` 已生成，可用于进一步 AI 优化分析

5. **提供优化建议**（可选）
   - 如用户希望，读取 `analysis_prompt.md` 内容并直接进行性能优化分析

## 配置说明

如需自定义分析行为，可创建 JSON 配置文件：

```json
{
  "max_depth": 200,
  "min_pct": 0.005,
  "top_n_paths": 5,
  "encoding": "utf-8",
  "enable_logging": false,
  "log_level": "INFO"
}
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `max_depth` | 200 | 最大路径深度，超过则截断 |
| `min_pct` | 0.005 | 最小占比阈值（0.5%），低于此值的路径被过滤 |
| `top_n_paths` | 5 | 提取的热路径数量 |
| `encoding` | "utf-8" | 文件编码格式 |
| `enable_logging` | false | 是否启用日志记录 |
| `log_level` | "INFO" | 日志级别（DEBUG/INFO/WARNING/ERROR） |

预置配置文件：
- `config/quick.json`：快速预览（Top10，2% 阈值，浅层分析）
- `config/debug.json`：调试模式（详细日志，1% 阈值）

## 输出文件

脚本在输出目录生成：
用户没配置输出目录时，默认为 flame-output目录
- **`hotpaths.md`**：TopN 热路径结构化分析报告（含调用栈和采样百分比）
- **`analysis_prompt.md`**：预构建的 AI 性能优化分析 prompt

## 错误处理

| 错误 | 解决方法 |
|------|----------|
| 文件不存在 | 检查 `html_path` 路径是否正确 |
| 文件格式无效 | 确认是 async-profiler 标准 HTML 输出 |
| 输出目录无权限 | 检查目录写权限或更换输出目录 |
| 解析失败 | 检查文件编码，尝试添加 `"encoding": "utf-8"` 配置 |

## 注意事项

- 仅支持 async-profiler 生成的 HTML 格式火焰图
- 大型文件（>100MB）处理可能需要数分钟
- 安装 `tqdm` 可获得进度条显示：`pip install tqdm`
