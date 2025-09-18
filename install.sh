#!/bin/bash

# PDF隐私信息遮盖系统安装脚本

echo "=========================================="
echo "    PDF隐私信息遮盖系统 - 安装脚本"
echo "=========================================="

# 检测操作系统
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if command -v apt-get &> /dev/null; then
        OS="ubuntu"
    elif command -v yum &> /dev/null; then
        OS="centos"
    else
        OS="unknown"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    OS="unknown"
fi

echo "检测到操作系统: $OS"

# 安装系统依赖
install_system_deps() {
    case $OS in
        "ubuntu")
            echo "正在安装Ubuntu/Debian系统依赖..."
            sudo apt-get update
            sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-sim
            sudo apt-get install -y poppler-utils
            sudo apt-get install -y libmagic1
            sudo apt-get install -y python3-pip python3-venv
            ;;
        "centos")
            echo "正在安装CentOS/RHEL系统依赖..."
            sudo yum install -y tesseract tesseract-langpack-chi-sim
            sudo yum install -y poppler-utils
            sudo yum install -y file-devel
            sudo yum install -y python3-pip python3-venv
            ;;
        "macos")
            echo "正在安装macOS系统依赖..."
            if ! command -v brew &> /dev/null; then
                echo "请先安装Homebrew: https://brew.sh/"
                exit 1
            fi
            brew install tesseract tesseract-lang
            brew install poppler
            brew install libmagic
            ;;
        *)
            echo "不支持的操作系统，请手动安装依赖"
            echo "参考README.md中的安装说明"
            return 1
            ;;
    esac
}

# 创建Python虚拟环境
create_venv() {
    echo "创建Python虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    
    echo "升级pip..."
    pip install --upgrade pip
    
    echo "安装Python依赖..."
    pip install -r requirements.txt
    
    if [[ $? -eq 0 ]]; then
        echo "✅ Python依赖安装成功"
    else
        echo "❌ Python依赖安装失败"
        return 1
    fi
}

# 创建必要的目录
create_directories() {
    echo "创建必要的目录..."
    mkdir -p uploads processed static templates
    echo "✅ 目录创建完成"
}

# 验证安装
verify_installation() {
    echo "验证安装..."
    
    # 检查Python包
    source venv/bin/activate
    python3 -c "import flask, fitz, PIL, cv2, easyocr, pdf2image, magic" 2>/dev/null
    if [[ $? -eq 0 ]]; then
        echo "✅ Python包安装验证通过"
    else
        echo "❌ Python包安装验证失败"
        return 1
    fi
    
    # 检查系统工具
    if command -v tesseract &> /dev/null; then
        echo "✅ Tesseract OCR 可用"
    else
        echo "❌ Tesseract OCR 不可用"
        return 1
    fi
    
    if command -v pdftoppm &> /dev/null; then
        echo "✅ Poppler-utils 可用"
    else
        echo "❌ Poppler-utils 不可用"
        return 1
    fi
    
    echo "✅ 系统依赖验证通过"
}

# 主安装流程
main() {
    echo "开始安装PDF隐私信息遮盖系统..."
    
    # 安装系统依赖
    install_system_deps
    if [[ $? -ne 0 ]]; then
        echo "系统依赖安装失败，请检查错误信息"
        exit 1
    fi
    
    # 创建虚拟环境并安装Python依赖
    create_venv
    if [[ $? -ne 0 ]]; then
        echo "Python依赖安装失败，请检查错误信息"
        exit 1
    fi
    
    # 创建目录
    create_directories
    
    # 验证安装
    verify_installation
    if [[ $? -ne 0 ]]; then
        echo "安装验证失败，请检查错误信息"
        exit 1
    fi
    
    echo ""
    echo "🎉 安装完成！"
    echo ""
    echo "使用方法:"
    echo "1. 激活虚拟环境: source venv/bin/activate"
    echo "2. 运行系统: python app.py"
    echo "3. 或使用启动脚本: ./run.sh"
    echo "4. 访问地址: http://localhost:5000"
    echo ""
    echo "测试系统:"
    echo "python test_system.py"
}

# 检查是否以root权限运行
if [[ $EUID -eq 0 ]]; then
    echo "请不要以root权限运行此脚本"
    exit 1
fi

# 运行主安装流程
main

