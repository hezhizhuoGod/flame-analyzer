# Dockerfile - Flame Analyzer Docker镜像

FROM python:3.9-slim

LABEL maintainer="your.email@example.com"
LABEL version="2.0.0"
LABEL description="Flame Analyzer - Java Performance Analysis Tool"

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建工作目录
RUN mkdir -p /workspace
WORKDIR /workspace

# 设置入口点
ENTRYPOINT ["python", "/app/scripts/flame_analyzer.py"]

# 默认命令
CMD ["--help"]

# 元数据
LABEL usage="docker run --rm -v \$(pwd):/workspace flame-analyzer profile.html"
LABEL example="docker run --rm -v \$(pwd):/workspace flame-analyzer profile.html -o ./analysis"