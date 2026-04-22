@echo off
REM install.bat - Flame Analyzer Windows 安装脚本

setlocal enabledelayedexpansion

REM 项目信息
set REPO_URL=https://github.com/YOUR_USERNAME/flame-analyzer
set INSTALL_DIR=%USERPROFILE%\.flame-analyzer
set VERSION=2.0.0

echo.
echo 🔥 Flame Analyzer Windows 安装脚本 v%VERSION%
echo =======================================================================

REM 检查Python环境
echo [INFO] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 未找到Python，请先安装Python 3.7或更高版本
    echo [INFO] 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [SUCCESS] Python环境检查通过: %PYTHON_VERSION%

REM 检查Git
echo [INFO] 检查Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 未找到Git，请先安装Git
    echo [INFO] 下载地址: https://git-scm.com/download/win
    pause
    exit /b 1
)
echo [SUCCESS] Git检查通过

REM 创建安装目录
echo [INFO] 设置安装目录...
if exist "%INSTALL_DIR%" (
    echo [INFO] 检测到已有安装，正在更新...
    cd /d "%INSTALL_DIR%"
    git pull origin main
) else (
    git clone "%REPO_URL%" "%INSTALL_DIR%"
)

cd /d "%INSTALL_DIR%"
echo [SUCCESS] 源码下载完成

REM 安装依赖
echo [INFO] 安装Python依赖...
python -m pip install --user -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo [WARNING] 可选依赖安装失败，将使用基础功能
) else (
    echo [SUCCESS] 依赖安装成功
)

REM 运行测试
echo [INFO] 运行测试验证安装...
python tests\test_flame_analyzer.py >nul 2>&1
if errorlevel 1 (
    echo [WARNING] 测试失败，但不影响正常使用
) else (
    echo [SUCCESS] 测试通过
)

REM 创建批处理命令
echo [INFO] 创建全局命令...
set BAT_FILE=%USERPROFILE%\flame-analyzer.bat

echo @echo off > "%BAT_FILE%"
echo REM Flame Analyzer 全局命令 >> "%BAT_FILE%"
echo cd /d "%INSTALL_DIR%" >> "%BAT_FILE%"
echo python scripts\flame_analyzer.py %%* >> "%BAT_FILE%"

echo [SUCCESS] 全局命令创建完成

REM 运行演示
echo [INFO] 运行安装演示...
python demo.py
if errorlevel 1 (
    echo [WARNING] 演示运行失败，但不影响正常使用
) else (
    echo [SUCCESS] 演示运行成功
)

REM 显示完成信息
echo.
echo =======================================================================
echo 🎉 Flame Analyzer v%VERSION% 安装完成！
echo =======================================================================
echo.
echo 📦 安装位置: %INSTALL_DIR%
echo 🔗 全局命令: %BAT_FILE%
echo 📚 文档: %INSTALL_DIR%\README.md
echo.
echo 🚀 快速开始:
echo    "%BAT_FILE%" your_profile.html
echo    "%BAT_FILE%" your_profile.html -o .\results
echo    "%BAT_FILE%" your_profile.html --debug
echo.
echo 📖 更多用法:
echo    "%BAT_FILE%" --help
echo    cd "%INSTALL_DIR%" ^&^& python demo.py
echo.
echo 💡 提示: 建议将 %USERPROFILE% 添加到系统PATH中
echo       这样就可以直接使用 flame-analyzer 命令
echo.
echo 🐛 反馈和支持: %REPO_URL%/issues
echo =======================================================================

pause