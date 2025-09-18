#!/bin/bash
# PDF隐私遮盖系统启动脚本（包含ANTIALIAS修复）

echo "🚀 启动PDF隐私遮盖系统..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行 install.sh"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 检查并应用ANTIALIAS修复
echo "🔧 检查ANTIALIAS修复..."
if [ -f "fix_antialias.py" ]; then
    python fix_antialias.py
    if [ $? -eq 0 ]; then
        echo "✅ ANTIALIAS修复检查完成"
    else
        echo "⚠️  ANTIALIAS修复可能有问题，但继续启动..."
    fi
else
    echo "⚠️  未找到fix_antialias.py，跳过修复检查"
fi

# 运行系统测试
echo "🧪 运行系统测试..."
python test_system.py

# 启动应用
echo "🌐 启动Web应用..."
echo "访问地址: http://localhost:6001"
echo "按 Ctrl+C 停止服务"
echo ""

python app.py
