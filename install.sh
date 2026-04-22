#!/bin/bash
# install.sh - Flame Analyzer 一键安装脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目信息
REPO_URL="https://github.com/YOUR_USERNAME/flame-analyzer"
INSTALL_DIR="$HOME/.flame-analyzer"
BIN_DIR="$HOME/.local/bin"
VERSION="2.0.0"

# 打印带颜色的消息
print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查Python环境
check_python() {
    print_status "检查Python环境..."

    if ! command_exists python3; then
        print_error "未找到Python3，请先安装Python 3.7或更高版本"
        exit 1
    fi

    python_version=$(python3 -c "import sys; print('{}.{}'.format(sys.version_info.major, sys.version_info.minor))")
    required_version="3.7"

    if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
        print_error "Python版本过低，需要3.7+，当前版本: $python_version"
        exit 1
    fi

    print_success "Python环境检查通过: $python_version"
}

# 检查Git
check_git() {
    print_status "检查Git..."

    if ! command_exists git; then
        print_error "未找到Git，请先安装Git"
        exit 1
    fi

    print_success "Git检查通过"
}

# 创建安装目录
setup_directories() {
    print_status "设置安装目录..."

    # 创建安装目录
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$BIN_DIR"

    print_success "目录创建完成"
}

# 下载源码
download_source() {
    print_status "下载Flame Analyzer源码..."

    # 如果已存在，则更新
    if [ -d "$INSTALL_DIR/.git" ]; then
        print_status "检测到已有安装，正在更新..."
        cd "$INSTALL_DIR"
        git pull origin main
    else
        # 删除可能存在的旧目录
        rm -rf "$INSTALL_DIR"
        git clone "$REPO_URL" "$INSTALL_DIR"
    fi

    cd "$INSTALL_DIR"
    print_success "源码下载完成"
}

# 安装依赖
install_dependencies() {
    print_status "安装Python依赖..."

    # 检查pip
    if ! command_exists pip3; then
        print_warning "未找到pip3，尝试使用python3 -m pip"
        pip_cmd="python3 -m pip"
    else
        pip_cmd="pip3"
    fi

    # 尝试安装可选依赖
    if $pip_cmd install --user -r requirements.txt 2>/dev/null; then
        print_success "依赖安装成功（包含进度条支持）"
    else
        print_warning "可选依赖安装失败，将使用基础功能（无进度条）"
    fi
}

# 运行测试
run_tests() {
    print_status "运行测试验证安装..."

    cd "$INSTALL_DIR"

    # 运行基础测试
    if python3 -m pytest tests/ -v --tb=short 2>/dev/null || python3 tests/test_flame_analyzer.py; then
        print_success "测试通过"
    else
        print_warning "测试失败，但安装可以继续使用"
    fi
}

# 创建可执行文件
create_executable() {
    print_status "创建全局命令..."

    # 创建wrapper脚本
    cat > "$BIN_DIR/flame-analyzer" << EOF
#!/bin/bash
# Flame Analyzer 全局命令wrapper

INSTALL_DIR="$INSTALL_DIR"

if [ ! -f "\$INSTALL_DIR/scripts/flame_analyzer.py" ]; then
    echo "错误: Flame Analyzer未正确安装"
    echo "请重新运行安装脚本: curl -fsSL $REPO_URL/raw/main/install.sh | bash"
    exit 1
fi

cd "\$INSTALL_DIR"
python3 scripts/flame_analyzer.py "\$@"
EOF

    chmod +x "$BIN_DIR/flame-analyzer"

    # 检查PATH
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        print_warning "需要将 $BIN_DIR 添加到PATH中"

        # 尝试添加到shell配置文件
        for shell_rc in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
            if [ -f "$shell_rc" ]; then
                if ! grep -q "$BIN_DIR" "$shell_rc"; then
                    echo "export PATH=\"\$PATH:$BIN_DIR\"" >> "$shell_rc"
                    print_status "已添加到 $shell_rc"
                fi
                break
            fi
        done

        print_warning "请重新启动终端或运行: export PATH=\"\$PATH:$BIN_DIR\""
    fi

    print_success "全局命令创建完成"
}

# 创建桌面快捷方式 (可选)
create_shortcuts() {
    print_status "创建快捷方式..."

    # 创建简化的别名脚本
    cat > "$INSTALL_DIR/quick-analyze" << 'EOF'
#!/bin/bash
# 快速分析脚本

if [ $# -eq 0 ]; then
    echo "用法: ./quick-analyze <html文件> [输出目录]"
    echo "示例: ./quick-analyze profile.html"
    echo "      ./quick-analyze profile.html ./results"
    exit 1
fi

HTML_FILE="$1"
OUTPUT_DIR="${2:-.}"

python3 scripts/flame_analyzer.py "$HTML_FILE" "$OUTPUT_DIR"
EOF

    chmod +x "$INSTALL_DIR/quick-analyze"

    print_success "快捷方式创建完成"
}

# 运行演示
run_demo() {
    print_status "运行安装演示..."

    cd "$INSTALL_DIR"

    if python3 demo.py; then
        print_success "演示运行成功"
    else
        print_warning "演示运行失败，但不影响正常使用"
    fi
}

# 显示安装完成信息
show_completion() {
    echo ""
    echo "==================================================================================="
    echo -e "${GREEN}🎉 Flame Analyzer v$VERSION 安装完成！${NC}"
    echo "==================================================================================="
    echo ""
    echo -e "${BLUE}📦 安装位置:${NC} $INSTALL_DIR"
    echo -e "${BLUE}🔗 全局命令:${NC} flame-analyzer"
    echo -e "${BLUE}📚 文档:${NC} $INSTALL_DIR/README.md"
    echo ""
    echo -e "${YELLOW}🚀 快速开始:${NC}"
    echo "   flame-analyzer your_profile.html                  # 基础分析"
    echo "   flame-analyzer your_profile.html -o ./results     # 指定输出目录"
    echo "   flame-analyzer your_profile.html --debug          # 调试模式"
    echo ""
    echo -e "${YELLOW}📖 更多用法:${NC}"
    echo "   flame-analyzer --help                             # 查看帮助"
    echo "   cd $INSTALL_DIR && python3 demo.py               # 运行演示"
    echo "   cd $INSTALL_DIR && ./quick-analyze profile.html  # 快速分析"
    echo ""
    echo -e "${YELLOW}🔧 配置文件:${NC}"
    echo "   $INSTALL_DIR/config/default.json                  # 默认配置"
    echo "   $INSTALL_DIR/config/quick.json                    # 快速配置"
    echo "   $INSTALL_DIR/config/debug.json                    # 调试配置"
    echo ""
    echo -e "${YELLOW}⚡ 提示:${NC}"
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        echo "   请重新启动终端，或运行: export PATH=\"\$PATH:$BIN_DIR\""
    else
        echo "   全局命令已可用，可以在任意目录使用 flame-analyzer"
    fi
    echo ""
    echo -e "${BLUE}🐛 反馈和支持:${NC} $REPO_URL/issues"
    echo "==================================================================================="
}

# 主安装流程
main() {
    echo ""
    echo "🔥 Flame Analyzer 一键安装脚本 v$VERSION"
    echo "==================================================================================="

    # 检查权限
    if [ "$EUID" -eq 0 ]; then
        print_warning "检测到root权限，建议使用普通用户安装"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    # 执行安装步骤
    check_python
    check_git
    setup_directories
    download_source
    install_dependencies
    run_tests
    create_executable
    create_shortcuts
    run_demo
    show_completion
}

# 错误处理
trap 'print_error "安装过程中发生错误，请检查输出并重试"' ERR

# 运行主程序
main "$@"