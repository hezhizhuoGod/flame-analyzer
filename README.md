# 🔥 Flame Analyzer

[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Stars](https://img.shields.io/github/stars/hezhizhuoGod/flame-analyzer)](https://github.com/hezhizhuoGod/flame-analyzer)

高性能Java火焰图分析器，自动提取热路径并生成AI优化建议。专为Java性能调优设计，支持async-profiler生成的HTML火焰图。

## 🚀 一键使用（推荐）



### 💾 本地安装（可选）

如果你希望本地安装以便反复使用：

```bash
 npx skills add  https://github.com/hezhizhuoGod/flame-analyzer

```

安装后使用：
```bash
flame-analyzer profile.html
```


## 📖 使用方法

### 基础用法

```bash
# 分析单个火焰图（生成 hotpaths.md 和 analysis_prompt.md）
python3 flame_analyzer.py profile.html

# 指定输出目录
python3 flame_analyzer.py profile.html output/

# 带详细配置的完整命令示例
python3 flame_analyzer.py profile.html analysis/ config.json
```

### 配置文件示例

创建 `config.json` 自定义分析参数：

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

### 输出文件

分析完成后会生成两个关键文件：

1. **hotpaths.md** - 详细的性能热点分析报告
   ```
   # 性能热点分析报告
   ## Top 5 热路径
   ### 路径 1 (15.23%)
   └── com.example.service.UserService.processUser()
       └── com.example.dao.UserDao.findById()
           └── java.sql.PreparedStatement.executeQuery()
   ```

2. **analysis_prompt.md** - AI分析提示（可直接用于ChatGPT/Claude）
   ```
   你是一位资深的Java性能优化专家，请分析以下火焰图热路径数据...
   ```

## 🔧 高级用法

### 批量处理

```bash
# 处理目录下所有HTML文件
for file in *.html; do
    curl -fsSL https://raw.githubusercontent.com/hezhizhuoGod/flame-analyzer/main/scripts/flame_analyzer.py | python3 - "$file" "./results/$(basename "$file" .html)"
done

# 并行处理（已安装时）
find . -name "*.html" | xargs -P 4 -I {} flame-analyzer {} -o ./results
```



## 📊 典型应用场景

- **🔥 生产问题排查**: 快速定位线上性能瓶颈
- **⚡ 应用性能调优**: 识别CPU热点和优化目标
- **🔍 微服务调用分析**: 跟踪跨服务性能问题
- **📈 性能回归检测**: CI/CD中自动化性能监控
- **🎯 代码Review**: 为性能优化提供数据支持

## 🛠️ 依赖要求

- **必需**: Python 3.7+ （仅标准库）
- **可选**: `tqdm` - 提供进度条显示（`pip install tqdm`）

## 🐳 Docker 使用

```bash
# 构建镜像
docker build -t flame-analyzer https://github.com/hezhizhuoGod/flame-analyzer.git

# 分析火焰图
docker run --rm -v $(pwd):/workspace flame-analyzer /workspace/profile.html
```

## 🤝 贡献指南

欢迎提交Issues和Pull Requests！

1. Fork 本项目
2. 创建特性分支: `git checkout -b feature/awesome-feature`
3. 提交更改: `git commit -m 'Add awesome feature'`
4. 推送分支: `git push origin feature/awesome-feature`
5. 创建 Pull Request

## 📄 开源许可

本项目基于 [MIT License](LICENSE) 开源，欢迎自由使用和分发。

## 🔗 相关链接

- 📚 [详细文档](https://github.com/hezhizhuoGod/flame-analyzer/wiki)
- 🐛 [问题反馈](https://github.com/hezhizhuoGod/flame-analyzer/issues)
- 💡 [功能建议](https://github.com/hezhizhuoGod/flame-analyzer/discussions)
- ⭐ [给个Star支持](https://github.com/hezhizhuoGod/flame-analyzer)

## 🎯 核心优势

| 传统方式 | Flame Analyzer |
|---------|----------------|
| 手动分析火焰图 | 自动提取热点路径 |
| 经验依赖判断 | AI辅助分析建议 |
| 文本化输出 | 结构化Markdown报告 |
| 工具链复杂 | 一键下载使用 |

---

> 💡 **提示**: 如果你是性能调优新手，建议先阅读生成的 `analysis_prompt.md` 文件，它包含了专业的AI分析提示，可以直接用于获取优化建议。

⭐ **如果这个工具对你有帮助，请给个Star支持一下！**