# PDF隐私信息遮盖系统

这是一个专门用于检测和遮盖PDF文件中隐私信息的Web应用程序。系统能够自动识别并遮盖身份证号码、手机号码、身份证地址、社保/养老编号、条形码/二维码，以及自动删除指定章节（技术方案、报价清单、财务报告仅保留封面），保护用户隐私与商业机密。

## 功能特性

- 🔒 **隐私信息检测**：自动检测PDF中的身份证号码、手机号码
- 🖼️ **图片OCR识别**：使用OCR技术识别图片中的文字信息
- ✅ **智能遮盖**：自动遮盖检测到的隐私信息，使用PDF红线（Redaction）永久移除底层内容
- 🧾 **章节删除**：按关键词删除技术方案、报价清单、财务报告（保留财务报告封面）
- 🧩 **二维码/条形码识别**：识别并遮盖证书二维码、社保条形码
- 📊 **详细报告**：提供遮盖处理的详细统计和位置信息
- 🌐 **Web界面**：友好的用户界面，支持拖拽上传
- 📱 **响应式设计**：支持各种设备访问

## 系统要求

- Python 3.7+
- Linux/Windows/macOS
- 至少2GB可用内存
- 支持PDF处理的系统库

## 安装步骤

### 1. 克隆项目

```bash
git clone <repository-url>
cd pdf-privacy-masker
```

### 2. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 3. 安装系统依赖

#### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-sim
sudo apt-get install -y poppler-utils
sudo apt-get install -y libmagic1
sudo apt-get install -y libzbar0   # 用于pyzbar
```

#### CentOS/RHEL:
```bash
sudo yum install -y tesseract tesseract-langpack-chi-sim
sudo yum install -y poppler-utils
sudo yum install -y file-devel
sudo yum install -y zbar           # 用于pyzbar
```

#### macOS:
```bash
brew install tesseract tesseract-lang
brew install poppler
brew install libmagic
brew install zbar                  # 用于pyzbar
```

### 4. 运行应用

```bash
python app.py
```

应用将在 `http://localhost:6001` 启动。

## 使用方法

### 1. 上传PDF文件
- 拖拽PDF文件到上传区域，或点击"选择文件"按钮
- 支持的文件格式：PDF
- 最大文件大小：50MB

### 2. 预览文件
- 点击"预览文件"按钮查看PDF内容
- 显示页数、文件大小和第一页文本预览

### 3. 开始遮盖
- 点击"开始遮盖"按钮
- 系统将自动检测并遮盖隐私信息
- 处理过程中显示进度条

### 4. 查看结果
- 显示检测到的隐私信息总数
- 成功遮盖和失败遮盖的统计
- 详细的处理报告，包括页码和位置信息

### 5. 下载文件
- 下载处理后的PDF文件
- 在线查看遮盖效果

## 隐私信息类型

系统能够检测和遮盖以下类型的隐私信息：

### 文本中的隐私信息
- **身份证号码**：更严格的18位身份证（含出生日期校验）
- **手机号码**：11位中国大陆手机号码
- **身份证地址**：识别“住址/地址/户籍地址”后的地址文本
- **社保/养老编号**：通用9-20位数字串（排除身份证/手机号）
- **条形码号**：10-32位数字串

### 图片中的隐私信息
- **身份证号码/手机号码/姓名**：通过OCR识别
- **二维码/条形码**：OpenCV/pyzbar识别并遮盖

## 技术架构

- **后端框架**：Flask
- **PDF处理**：PyMuPDF (fitz)
- **图像处理**：OpenCV, Pillow
- **OCR识别**：EasyOCR
- **前端界面**：Bootstrap 5, JavaScript
- **文件处理**：pdf2image, PyPDF2

## 配置说明

### 环境变量

可以在 `app.py` 中修改以下配置：

```python
app.config['SECRET_KEY'] = 'your-secret-key-here'  # 修改为你的密钥
app.config['MAX_CONTENT_LENGTH'] = 1000 * 1024 * 1024  # 最大文件大小
```

### OCR配置

在 `pdf_processor.py` 中可以调整OCR参数：

```python
self.ocr_reader = easyocr.Reader(['ch_sim', 'en'])  # 支持中文简体和英文
```

## 注意事项

1. **处理时间**：大文件或包含大量图片的PDF处理时间较长
2. **内存使用**：处理大文件时可能需要较多内存
3. **OCR准确性**：图片质量影响OCR识别准确性
4. **文件备份**：建议在处理前备份原始文件
5. **电子印章保护**：内置红色章印检测，尽量避免误遮盖电子印章区域

## 故障排除

### 常见问题

1. **OCR初始化失败**
   - 检查是否安装了tesseract
   - 确认语言包是否正确安装

2. **PDF处理失败**
   - 检查PDF文件是否损坏
   - 确认文件格式是否为标准PDF

3. **内存不足**
   - 减少同时处理的文件数量
   - 增加系统可用内存

4. **ANTIALIAS错误**
   - 如果出现 `module 'PIL.Image' has no attribute 'ANTIALIAS'` 错误
   - 运行修复脚本：`python fix_antialias.py`
   - 或参考 `ANTIALIAS_FIX.md` 进行手动修复

5. **pyzbar依赖问题**
   - 需要安装系统库 `zbar`
   - Ubuntu/Debian: `sudo apt-get install -y libzbar0`
   - CentOS/RHEL: `sudo yum install -y zbar`
   - macOS: `brew install zbar`

## 安全说明

- 上传的文件仅用于处理，不会永久存储
- 处理完成后，原始文件和处理后的文件会保存在本地
- 建议定期清理 `uploads` 和 `processed` 目录

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 发送邮件至：[your-email@example.com]

---

**免责声明**：本工具仅用于保护个人隐私，请确保在合法合规的前提下使用。使用者需自行承担使用风险。

