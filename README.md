# 🔥 Flame Analyzer

[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-green.svg)](tests/)

高性能Java火焰图分析器，自动提取热路径并生成AI优化建议。专为Java性能调优设计，支持async-profiler生成的HTML火焰图。

## ✨ 特性

- 🔍 **智能解析**: 自动解析async-profiler HTML火焰图格式
- 🎯 **热点提取**: 智能提取TopN性能热路径
- 📊 **结构化报告**: 生成Markdown格式的分析报告
- 🤖 **AI集成**: 自动生成面向AI的性能分析prompt
- ⚙️ **高度可配置**: 支持JSON配置文件自定义分析参数
- 🛡️ **稳定可靠**: 完整的异常处理和输入验证
- 📈 **进度可视**: 可选的进度条显示

## 🚀 快速开始

### 一键安装

```bash
# 方式1: 使用curl (推荐)
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/flame-analyzer/main/install.sh | bash

# 方式2: 使用wget
wget -qO- https://raw.githubusercontent.com/YOUR_USERNAME/flame-analyzer/main/install.sh | bash

# 方式3: 手动克隆
git clone https://github.com/YOUR_USERNAME/flame-analyzer.git
cd flame-analyzer
./install.sh
```

### 基础用法

```bash
# 分析单个火焰图
flame-analyzer profile.html

# 指定输出目录
flame-analyzer profile.html -o ./analysis

# 使用配置文件
flame-analyzer profile.html -c config/debug.json

# 快速模式
flame-analyzer profile.html --quick

# 调试模式
flame-analyzer profile.html --debug
```

## 📦 安装方式

### 1. 一键安装脚本 (推荐)

```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/flame-analyzer/main/install.sh | bash
```

安装脚本会：
- 自动检测Python环境
- 安装可选依赖
- 创建全局命令链接
- 运行测试验证安装

### 2. 手动安装

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/flame-analyzer.git
cd flame-analyzer

# 安装依赖 (可选)
pip install -r requirements.txt

# 运行测试
python -m pytest tests/

# 创建命令别名
echo 'alias flame-analyzer="python $(pwd)/scripts/flame_analyzer.py"' >> ~/.bashrc
source ~/.bashrc
```

### 3. Docker安装

```bash
# 使用Docker运行
docker run --rm -v $(pwd):/workspace your_username/flame-analyzer profile.html
```

## 📖 详细用法

### 命令行选项

```
flame-analyzer [OPTIONS] HTML_FILE

位置参数:
  HTML_FILE          async-profiler生成的HTML火焰图文件

可选参数:
  -h, --help         显示帮助信息
  -o, --output DIR   输出目录 (默认: .)
  -c, --config FILE  配置文件路径
  -q, --quick        快速分析模式
  -d, --debug        调试模式 (详细日志)
  -v, --version      显示版本信息
```

### 配置文件

支持JSON格式的配置文件：

```json
{
  "max_depth": 200,       // 最大分析深度
  "min_pct": 0.005,      // 最小占比阈值 (0.5%)
  "top_n_paths": 5,      // 提取热路径数量
  "encoding": "utf-8",   // 文件编码
  "enable_logging": false, // 启用日志
  "log_level": "INFO"    // 日志级别
}
```

### 预设配置

项目提供三种预设配置：

| 配置 | 用途 | 参数 |
|------|------|------|
| `default.json` | 标准分析 | 5条路径，0.5%阈值 |
| `quick.json` | 快速预览 | 10条路径，2%阈值，浅层 |
| `debug.json` | 详细分析 | 3条路径，1%阈值，详细日志 |

### 输出文件

工具生成两个主要文件：

1. **hotpaths.md** - 热路径分析报告
   - TopN热路径的完整调用链
   - 占比、采样数、函数名信息
   - 树形结构展示

2. **analysis_prompt.md** - AI分析提示
   - 预构建的性能分析prompt
   - 包含角色定义、数据和任务
   - 可直接用于ChatGPT/Claude等AI工具

## 🔧 高级用法

### 批量分析

```bash
# 分析目录下所有HTML文件
for file in *.html; do
    flame-analyzer "$file" -o "./results/$(basename "$file" .html)"
done

# 使用xargs并行处理
find . -name "*.html" | xargs -P 4 -I {} flame-analyzer {} -o ./results
```

### 集成到CI/CD

```yaml
# .github/workflows/performance.yml
- name: Analyze Performance
  run: |
    flame-analyzer profile.html -o ./performance-report
    # 上传报告到artifact或发送到监控系统
```

### 与其他工具协作

```bash
# 与async-profiler结合使用
java -jar async-profiler.jar -d 30 -f profile.html $PID
flame-analyzer profile.html -o ./analysis

# 与JProfiler结合
# 导出JProfiler火焰图后使用本工具分析
```

## 📊 使用场景

- **Java应用性能调优**: 识别CPU热点和瓶颈
- **微服务性能分析**: 跟踪跨服务调用链性能
- **生产问题排查**: 定位线上性能问题根因
- **代码优化验证**: 对比优化前后的性能数据
- **CI/CD性能监控**: 自动化性能回归检测

## 🧪 测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行演示
python demo.py

# 测试安装
./test_installation.sh
```

## 📝 开发

### 项目结构

```
flame-analyzer/
├── scripts/
│   └── flame_analyzer.py      # 主程序
├── tests/
│   └── test_flame_analyzer.py # 单元测试
├── config/
│   ├── default.json          # 默认配置
│   ├── quick.json            # 快速配置
│   └── debug.json            # 调试配置
├── install.sh                # 安装脚本
├── requirements.txt          # Python依赖
└── README.md                 # 项目文档
```

### 贡献指南

1. Fork 项目
2. 创建特性分支: `git checkout -b feature/amazing-feature`
3. 提交更改: `git commit -m 'Add amazing feature'`
4. 推送分支: `git push origin feature/amazing-feature`
5. 创建Pull Request

### 本地开发

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/flame-analyzer.git
cd flame-analyzer

# 安装开发依赖
pip install -r requirements.txt
pip install pytest

# 运行测试
python -m pytest tests/ -v

# 运行代码检查 (可选)
pip install flake8 black
flake8 scripts/
black scripts/
```

## 🐳 Docker

### 构建镜像

```bash
docker build -t flame-analyzer .
```

### 使用Docker

```bash
# 分析本地文件
docker run --rm -v $(pwd):/workspace flame-analyzer /workspace/profile.html

# 交互式使用
docker run --rm -it -v $(pwd):/workspace flame-analyzer bash
```

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源。

## 🤝 致谢

- [async-profiler](https://github.com/jvm-profiling-tools/async-profiler) - 优秀的Java性能分析工具
- [tqdm](https://github.com/tqdm/tqdm) - 进度条库
- 所有贡献者和用户的反馈

## 📞 支持

- 🐛 [报告Bug](https://github.com/YOUR_USERNAME/flame-analyzer/issues)
- 💡 [功能建议](https://github.com/YOUR_USERNAME/flame-analyzer/issues)
- 📧 邮件: your.email@example.com
- 📚 [文档](https://github.com/YOUR_USERNAME/flame-analyzer/wiki)

## 🔖 版本历史

- **v2.0.0** (2024-04-22): 重大更新
  - 添加配置文件支持
  - 增强错误处理和验证
  - 完整的单元测试覆盖
  - 进度条和用户体验优化
- **v1.0.0**: 初始版本
  - 基础火焰图解析功能
  - 热路径提取和报告生成

---

⭐ 如果这个项目对你有帮助，请给个star支持一下！