import os
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename
from pdf_processor import PDFProcessor
import magic

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'
app.config['MAX_CONTENT_LENGTH'] = 1000 * 1024 * 1024  # 1000MB max file size

# 确保上传和处理目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# 允许的文件类型
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    """检查文件类型是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """处理PDF文件上传"""
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file and allowed_file(file.filename):
        # 生成唯一文件名
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # 保存文件
        file.save(filepath)
        
        # 验证文件确实是PDF
        try:
            file_type = magic.from_file(filepath, mime=True)
            if file_type != 'application/pdf':
                os.remove(filepath)
                return jsonify({'error': '文件不是有效的PDF格式'}), 400
        except Exception as e:
            os.remove(filepath)
            return jsonify({'error': f'文件验证失败: {str(e)}'}), 400
        
        return jsonify({
            'success': True,
            'filename': unique_filename,
            'original_name': filename,
            'message': '文件上传成功'
        })
    
    return jsonify({'error': '不支持的文件类型'}), 400

@app.route('/preview/<filename>')
def preview_pdf(filename):
    """预览PDF文件"""
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': '文件不存在'}), 404
    
    try:
        processor = PDFProcessor(filepath)
        preview_info = processor.get_preview_info()
        return jsonify(preview_info)
    except Exception as e:
        return jsonify({'error': f'预览失败: {str(e)}'}), 500

@app.route('/mask/<filename>', methods=['POST'])
def mask_pdf(filename):
    """遮盖PDF中的隐私信息"""
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': '文件不存在'}), 404
    
    try:
        processor = PDFProcessor(filepath)
        mask_result = processor.mask_privacy_info()
        
        # 保存处理后的文件
        output_filename = f"masked_{filename}"
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
        processor.save_masked_pdf(output_path)
        
        mask_result['output_file'] = output_filename
        return jsonify(mask_result)
    
    except Exception as e:
        return jsonify({'error': f'遮盖处理失败: {str(e)}'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """下载处理后的文件"""
    filepath = os.path.join(app.config['PROCESSED_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': '文件不存在'}), 404
    
    return send_file(filepath, as_attachment=True)

@app.route('/view/<filename>')
def view_file(filename):
    """查看处理后的文件"""
    filepath = os.path.join(app.config['PROCESSED_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': '文件不存在'}), 404
    
    return send_file(filepath, mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=6001)

