#!/bin/bash
# test_installation.sh - 测试安装是否成功

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_test() { echo -e "${YELLOW}[TEST]${NC} $1"; }
print_pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
print_fail() { echo -e "${RED}[FAIL]${NC} $1"; }

echo "🧪 Flame Analyzer 安装测试"
echo "=========================="

# 测试1: 检查Python环境
print_test "检查Python环境..."
if python3 --version >/dev/null 2>&1; then
    python_version=$(python3 --version)
    print_pass "Python环境: $python_version"
else
    print_fail "Python3未安装或不可用"
    exit 1
fi

# 测试2: 检查脚本文件
print_test "检查核心脚本..."
if [ -f "scripts/flame_analyzer.py" ]; then
    print_pass "主脚本文件存在"
else
    print_fail "scripts/flame_analyzer.py 未找到"
    exit 1
fi

# 测试3: 检查配置文件
print_test "检查配置文件..."
config_files=("config/default.json" "config/quick.json" "config/debug.json")
for config in "${config_files[@]}"; do
    if [ -f "$config" ]; then
        print_pass "$config 存在"
    else
        print_fail "$config 未找到"
        exit 1
    fi
done

# 测试4: 运行帮助命令
print_test "测试帮助命令..."
if python3 scripts/flame_analyzer.py --help >/dev/null 2>&1; then
    print_pass "帮助命令正常"
else
    print_fail "帮助命令失败"
    exit 1
fi

# 测试5: 运行单元测试
print_test "运行单元测试..."
if [ -f "tests/test_flame_analyzer.py" ]; then
    if cd tests && python3 test_flame_analyzer.py >/dev/null 2>&1; then
        print_pass "单元测试通过"
        cd ..
    else
        print_fail "单元测试失败"
        cd ..
        exit 1
    fi
else
    print_fail "测试文件未找到"
    exit 1
fi

# 测试6: 运行演示
print_test "运行演示程序..."
if python3 demo.py >/dev/null 2>&1; then
    print_pass "演示程序正常"
else
    print_fail "演示程序失败"
    exit 1
fi

# 测试7: 检查输出文件
print_test "检查输出文件..."
if [ -f "demo_output/hotpaths.md" ] && [ -f "demo_output/analysis_prompt.md" ]; then
    print_pass "输出文件生成正常"
else
    print_fail "输出文件生成失败"
    exit 1
fi

# 测试8: 检查全局命令 (如果存在)
print_test "检查全局命令..."
if command -v flame-analyzer >/dev/null 2>&1; then
    print_pass "全局命令可用"
else
    print_fail "全局命令不可用 (可能需要重启终端)"
fi

echo ""
echo "🎉 所有测试通过！Flame Analyzer 安装成功！"
echo ""
echo "快速开始:"
echo "  python3 scripts/flame_analyzer.py your_profile.html"
echo "  或者使用全局命令: flame-analyzer your_profile.html"
echo ""