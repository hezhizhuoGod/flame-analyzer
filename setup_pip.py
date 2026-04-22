#!/usr/bin/env python3
"""
setup.py - Flame Analyzer Python包安装配置
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取README文件
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# 读取requirements
requirements = []
requirements_file = this_directory / "requirements.txt"
if requirements_file.exists():
    with open(requirements_file, encoding='utf-8') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="flame-analyzer",
    version="2.0.0",
    author="Flame Analyzer Contributors",
    author_email="your.email@example.com",
    description="高性能Java火焰图分析器，自动提取热路径并生成AI优化建议",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/YOUR_USERNAME/flame-analyzer",
    project_urls={
        "Bug Reports": "https://github.com/YOUR_USERNAME/flame-analyzer/issues",
        "Source": "https://github.com/YOUR_USERNAME/flame-analyzer",
        "Documentation": "https://github.com/YOUR_USERNAME/flame-analyzer/blob/main/README.md",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Debuggers",
        "Topic :: System :: Monitoring",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    python_requires=">=3.7",
    install_requires=[
        # 无必需依赖，纯Python标准库实现
    ],
    extras_require={
        "progress": ["tqdm>=4.60.0"],  # 进度条支持
        "dev": [
            "pytest>=6.0",
            "flake8",
            "black",
            "mypy",
        ],
    },
    entry_points={
        "console_scripts": [
            "flame-analyzer=flame_analyzer.main:main",
        ],
    },
    package_data={
        "flame_analyzer": [
            "config/*.json",
            "templates/*.md",
        ],
    },
    include_package_data=True,
    keywords=[
        "java", "performance", "profiling", "flame-graph",
        "async-profiler", "optimization", "analysis", "ai"
    ],
    platforms=["any"],
    zip_safe=False,
)