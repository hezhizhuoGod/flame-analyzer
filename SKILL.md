# Flame Analyzer

高性能火焰图分析器，提取 TopN 热路径并生成结构化报告和AI分析提示。

## 🚀 新特性 (v2.0)

- ✨ **可配置化**: 支持JSON配置文件自定义分析参数
- 🛡️ **增强验证**: 全面的输入验证和异常处理机制
- 📊 **进度可视**: 可选的进度条显示（安装tqdm库）
- 🧪 **单元测试**: 完整的测试覆盖确保代码质量
- 📝 **详细日志**: 可配置的日志记录系统
- 🔧 **内存优化**: 支持大型火焰图文件处理

## Usage

执行 /scripts/flame_analyzer.py 脚本，传入火焰图 HTML 文件路径和可选参数：

```bash
/flame-analyzer <html_path> [output_dir] [config_file]
```

## Parameters

- `html_path` - async-profiler 生成的 HTML 火焰图文件路径（必需）
- `output_dir` - 输出目录（可选，默认当前目录）
- `config_file` - JSON 配置文件路径（可选，使用默认配置）

## Configuration

创建 JSON 配置文件自定义分析行为：

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

### 配置参数说明

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| max_depth | int | 200 | 最大路径深度，超过则截断 |
| min_pct | float | 0.005 | 最小占比阈值（0.5%），低于此值的路径被过滤 |
| top_n_paths | int | 5 | 提取的热路径数量 |
| encoding | str | "utf-8" | 文件编码格式 |
| enable_logging | bool | false | 是否启用日志记录 |
| log_level | str | "INFO" | 日志级别（DEBUG/INFO/WARNING/ERROR） |

## Examples

```bash
# 基本用法：分析当前目录的火焰图文件
/flame-analyzer profile.html

# 指定输出目录
/flame-analyzer data/cpu-profile.html ./analysis

# 使用自定义配置文件
/flame-analyzer profile.html ./output config/debug.json

# 预置配置快速使用
/flame-analyzer profile.html ./output config/quick.json    # 快速分析（Top10，浅层）
/flame-analyzer profile.html ./output config/debug.json   # 调试模式（详细日志）
```

## Output

该命令会在输出目录生成两个文件：

1. **hotpaths.md** - 详细的热路径分析报告
    - TopN 性能热点路径
    - 采样百分比和调用栈信息
    - 结构化的性能分析数据

2. **analysis_prompt.md** - AI 分析提示文档
    - 预构建的性能分析 prompt
    - 可直接用于获取优化建议

## Features

### 核心功能
- ✅ 自动解析 async-profiler HTML 格式
- ✅ 提取关键性能热点（可配置TopN）
- ✅ 生成结构化分析报告
- ✅ 支持中文输出和 UTF-8 编码
- ✅ 智能过滤低频调用（可配置阈值）
- ✅ 生成 AI 优化分析 prompt

### 增强特性
- 🛡️ 全面的输入验证和错误处理
- 📊 进度条显示（可选，需安装tqdm）
- 🔧 大文件优化处理（分块读取）
- 📝 可配置的日志记录系统
- ⚙️ JSON 配置文件支持
- 🧪 完整的单元测试覆盖

## Installation

1. **基础安装**（仅使用标准库）：
```bash
# 无需额外安装，Python 3.7+ 即可运行
python scripts/flame_analyzer.py profile.html
```

2. **增强体验**（推荐）：
```bash
# 安装可选依赖获得进度条显示
pip install -r requirements.txt
python scripts/flame_analyzer.py profile.html
```

## Validation

脚本会自动验证：
- 输入文件是否存在且可读
- 文件是否为有效的火焰图格式
- 文件大小和内容完整性
- 输出目录权限和可写性
- 配置文件格式正确性

## Error Handling

| 异常类型 | 说明 | 解决方法 |
|---------|------|----------|
| FileNotFoundError | 火焰图文件不存在 | 检查文件路径是否正确 |
| ValidationError | 文件内容验证失败 | 确保是valid async-profiler输出 |
| ParseError | 解析失败 | 检查文件格式和编码 |
| PermissionError | 输出目录无写权限 | 检查目录权限或更换输出目录 |

## Testing

运行单元测试确保代码质量：

```bash
cd tests
python test_flame_analyzer.py
```

## Tips

- 确保 HTML 文件是 async-profiler 生成的标准格式
- 大型火焰图文件（>100MB）可能需要几分钟处理时间
- 使用debug配置文件可以获得详细的分析日志
- 生成的报告可以直接用于性能优化分析
- 安装 tqdm 库可获得更好的用户体验