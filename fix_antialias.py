#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复easyocr中的ANTIALIAS问题
在Pillow 10.0.0+中，Image.ANTIALIAS已被弃用，替换为Image.Resampling.LANCZOS
"""

import os
import sys
import shutil
from pathlib import Path

def find_easyocr_utils():
    """查找easyocr的utils.py文件"""
    try:
        import easyocr
        easyocr_path = Path(easyocr.__file__).parent
        utils_path = easyocr_path / "utils.py"
        if utils_path.exists():
            return str(utils_path)
    except ImportError:
        pass
    
    # 尝试在虚拟环境中查找
    venv_path = Path("venv")
    if venv_path.exists():
        for site_packages in ["lib/python3.8/site-packages", "lib64/python3.8/site-packages"]:
            utils_path = venv_path / site_packages / "easyocr" / "utils.py"
            if utils_path.exists():
                return str(utils_path)
    
    return None

def backup_file(file_path):
    """备份原文件"""
    backup_path = file_path + ".backup"
    if not os.path.exists(backup_path):
        shutil.copy2(file_path, backup_path)
        print(f"✅ 已备份原文件到: {backup_path}")
    return backup_path

def fix_antialias_issue(file_path):
    """修复ANTIALIAS问题"""
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已经修复
        if 'Image.Resampling.LANCZOS' in content:
            print("✅ 文件已经修复过了")
            return True
        
        # 备份原文件
        backup_file(file_path)
        
        # 替换ANTIALIAS为Resampling.LANCZOS
        # 首先添加必要的import
        if 'from PIL import Image' in content and 'Image.Resampling' not in content:
            content = content.replace(
                'from PIL import Image',
                'from PIL import Image, ImageOps'
            )
        
        # 替换ANTIALIAS的使用
        content = content.replace(
            'Image.ANTIALIAS',
            'Image.Resampling.LANCZOS'
        )
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 已修复文件: {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 修复easyocr中的ANTIALIAS问题...")
    
    # 查找utils.py文件
    utils_path = find_easyocr_utils()
    if not utils_path:
        print("❌ 找不到easyocr的utils.py文件")
        return False
    
    print(f"📁 找到文件: {utils_path}")
    
    # 修复文件
    if fix_antialias_issue(utils_path):
        print("🎉 修复完成！")
        print("\n现在可以正常运行PDF隐私遮盖系统了。")
        return True
    else:
        print("❌ 修复失败")
        return False

if __name__ == "__main__":
    main()
