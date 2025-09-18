#!/bin/bash

# PDF隐私信息遮盖系统启动脚本

echo "=========================================="
echo "    PDF隐私信息遮盖系统"
echo "=========================================="

# 检查Python版本
python_version=$(python3 --version 2>&1)
if [[ $? -ne 0 ]]; then
    echo "错误: 未找到Python3，请先安装Python 3.7+"
    exit 1
fi

echo "Python版本: $python_version"

# 检查虚拟环境
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "提示: 建议在虚拟环境中运行"
    echo "创建虚拟环境: python3 -m venv venv"
    echo "激活虚拟环境: source venv/bin/activate"
    echo ""
fi

# 检查依赖
echo "检查Python依赖..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo "安装Python依赖..."
    pip3 install -r requirements.txt
    if [[ $? -ne 0 ]]; then
        echo "错误: 依赖安装失败"
        exit 1
    fi
fi

# 检查系统依赖
echo "检查系统依赖..."
if ! command -v tesseract &> /dev/null; then
    echo "警告: 未找到tesseract，OCR功能可能无法使用"
    echo "请安装: sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim"
fi

if ! command -v pdftoppm &> /dev/null; then
    echo "警告: 未找到poppler-utils，图片处理功能可能无法使用"
    echo "请安装: sudo apt-get install poppler-utils"
fi

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p uploads processed

# 启动应用
echo ""
echo "启动应用..."
echo "访问地址: http://localhost:6001"
echo "按 Ctrl+C 停止应用"
echo ""

python3 app.py

