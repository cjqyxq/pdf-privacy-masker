# 🚀 PDF隐私信息遮盖系统 - 快速启动指南

## 📋 系统要求

- **操作系统**：Linux (Ubuntu/Debian/CentOS), Windows, macOS
- **Python版本**：3.7 或更高版本
- **内存要求**：至少 2GB 可用内存
- **磁盘空间**：至少 500MB 可用空间

## ⚡ 一键安装（推荐）

### 方法1：自动安装脚本
```bash
# 下载项目后，进入项目目录
cd pdf-privacy-masker

# 给安装脚本添加执行权限
chmod +x install.sh

# 运行自动安装脚本
./install.sh
```

### 方法2：手动安装
```bash
# 1. 安装系统依赖
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-sim poppler-utils libmagic1

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 3. 安装Python依赖
pip install -r requirements.txt
```

## 🎯 快速启动

### 启动系统
```bash
# 方法1：使用启动脚本（推荐）
./run.sh

# 方法2：直接运行
python app.py

# 方法3：激活虚拟环境后运行
source venv/bin/activate
python app.py
```

### 访问系统
打开浏览器访问：`http://localhost:5000`

## 📱 使用步骤

### 第1步：上传PDF文件
- 拖拽PDF文件到上传区域
- 或点击"选择文件"按钮
- 支持最大50MB的PDF文件

### 第2步：预览文件
- 点击"预览文件"按钮
- 查看文件基本信息和第一页内容

### 第3步：开始遮盖
- 点击"开始遮盖"按钮
- 系统自动检测并遮盖隐私信息
- 等待处理完成

### 第4步：查看结果
- 查看检测到的隐私信息统计
- 了解每处隐私信息的位置
- 下载处理后的文件

## 🧪 测试系统

运行测试脚本验证系统是否正常：
```bash
python test_system.py
```

## 🔧 常见问题

### Q: 安装失败怎么办？
A: 检查Python版本是否为3.7+，确保有足够的磁盘空间和网络连接。

### Q: OCR功能不工作？
A: 确保已安装Tesseract和中文语言包：
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim
```

### Q: PDF处理失败？
A: 检查PDF文件是否损坏，确保文件格式为标准PDF。

### Q: 内存不足？
A: 减少同时处理的文件数量，或增加系统可用内存。

## 📞 获取帮助

- 查看详细文档：`README.md`
- 查看项目总结：`PROJECT_SUMMARY.md`
- 运行系统测试：`python test_system.py`

## 🎉 恭喜！

现在您已经成功安装并启动了PDF隐私信息遮盖系统！

系统特点：
- ✅ 自动检测身份证号码和手机号码
- ✅ 智能识别图片中的隐私信息
- ✅ 完全遮盖，保护隐私安全
- ✅ 详细处理报告，透明操作
- ✅ 用户友好界面，操作简单

开始使用您的隐私保护工具吧！

