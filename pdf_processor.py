import os
import re
import fitz  # PyMuPDF
from PIL import Image
import numpy as np
import cv2
import easyocr
from pdf2image import convert_from_path
import tempfile
import json
from typing import List, Tuple, Dict, Any, Optional

# 修复Pillow 10.0+的ANTIALIAS问题
try:
    # 在Pillow 10.0+中，ANTIALIAS被移除，使用LANCZOS替代
    if not hasattr(Image, 'ANTIALIAS'):
        Image.ANTIALIAS = Image.Resampling.LANCZOS
except AttributeError:
    # 如果Resampling也不存在，使用LANCZOS常量
    Image.ANTIALIAS = Image.LANCZOS

try:
    from pyzbar.pyzbar import decode as zbar_decode, ZBarSymbol
except Exception:
    zbar_decode = None
    ZBarSymbol = None

class PDFProcessor:
    def __init__(self, pdf_path):
        """初始化PDF处理器"""
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.mask_results = {
            'total_found': 0,
            'successful_masks': 0,
            'failed_masks': 0,
            'details': []
        }
        
        # 初始化OCR读取器
        try:
            self.ocr_reader = easyocr.Reader(['ch_sim', 'en'])
        except Exception as e:
            print(f"OCR初始化失败: {e}")
            self.ocr_reader = None
        
        # 隐私信息正则表达式与关键词
        self.patterns = {
            'id_card': r'\b\d{6}(19|20)\d{2}(0[1-9]|1[0-2])([0-2][0-9]|3[0-1])\d{3}[\dXx]\b',  # 更严格的身份证
            'phone': r'\b1[3-9]\d{9}\b',      # 手机号码
            'ssn_cn_generic': r'\b\d{9,20}\b',  # 社保/个人编号（通用数字序列）
            'barcode_num': r'\b\d{10,32}\b',    # 条形码号（常见长度）
            'address_label': r'(住址|地址|户籍地址)[:：]\s*([^\n\r]{4,50})',  # 身份证地址，更精确
            'name': r'[\u4e00-\u9fa5]{2,4}',  # 中文姓名（备用，但需要上下文验证）
        }

        # 章节关键词
        self.section_keywords = {
            'tech_plan': ['技术方案', '技术实施方案', '技术标'],
            'quotation': ['报价清单', '投标报价', '商务报价'],
            'finance': ['财务报告', '审计报告']
        }
    
    def get_preview_info(self):
        """获取PDF预览信息"""
        try:
            page_count = len(self.doc)
            first_page_text = ""
            
            if page_count > 0:
                first_page = self.doc[0]
                first_page_text = first_page.get_text()
                # 限制预览文本长度
                if len(first_page_text) > 500:
                    first_page_text = first_page_text[:500] + "..."
            
            return {
                'page_count': page_count,
                'first_page_preview': first_page_text,
                'file_size': os.path.getsize(self.pdf_path)
            }
        except Exception as e:
            return {'error': f'获取预览信息失败: {str(e)}'}
    
    def detect_text_privacy(self, text):
        """检测文本中的隐私信息"""
        privacy_info = []
        
        # 检测身份证号码
        id_matches = re.finditer(self.patterns['id_card'], text)
        for match in id_matches:
            privacy_info.append({
                'type': '身份证号码',
                'value': match.group(),
                'start': match.start(),
                'end': match.end(),
                'pattern': 'text'
            })
        
        # 检测手机号码
        phone_matches = re.finditer(self.patterns['phone'], text)
        for match in phone_matches:
            privacy_info.append({
                'type': '手机号码',
                'value': match.group(),
                'start': match.start(),
                'end': match.end(),
                'pattern': 'text'
            })

        # 检测身份证地址（提取值部分进行遮盖）
        try:
            for match in re.finditer(self.patterns['address_label'], text):
                label_val = match.group(0)
                val = match.group(2) if match.lastindex and match.lastindex >= 2 else None
                if val and len(val.strip()) >= 4:
                    # 进一步验证是否为真实地址（包含省市区等关键词）
                    address_keywords = ['省', '市', '区', '县', '镇', '乡', '村', '街道', '路', '号', '栋', '单元']
                    if any(keyword in val for keyword in address_keywords):
                        privacy_info.append({
                            'type': '身份证地址',
                            'value': val.strip(),
                            'start': match.start(),
                            'end': match.end(),
                            'pattern': 'text'
                        })
        except Exception:
            pass

        # 社保/个人编号、条形码号（仅在相关上下文中检测）
        for key, ptn, label, context_keywords in [
            ('ssn_cn_generic', self.patterns['ssn_cn_generic'], '社保/个人编号', ['社保', '养老', '个人编号', '社会保障']),
            ('barcode_num', self.patterns['barcode_num'], '条形码号', ['条形码', '条码', '码号'])
        ]:
            try:
                for match in re.finditer(ptn, text):
                    num = match.group()
                    # 避免与手机号/身份证重复
                    if re.fullmatch(self.patterns['phone'], num) or re.fullmatch(self.patterns['id_card'], num):
                        continue
                    
                    # 检查上下文是否包含相关关键词
                    context_start = max(0, match.start() - 50)
                    context_end = min(len(text), match.end() + 50)
                    context = text[context_start:context_end]
                    
                    if any(keyword in context for keyword in context_keywords):
                        privacy_info.append({
                            'type': label,
                            'value': num,
                            'start': match.start(),
                            'end': match.end(),
                            'pattern': 'text'
                        })
            except Exception:
                continue
        
        return privacy_info
    
    def detect_image_privacy(self, page_num):
        """检测图片中的隐私信息"""
        privacy_info = []
        
        try:
            # 将PDF页面转换为图片
            with tempfile.TemporaryDirectory() as temp_dir:
                images = convert_from_path(self.pdf_path, first_page=page_num+1, last_page=page_num+1)
                if not images:
                    return privacy_info
                
                image = images[0]
                image_path = os.path.join(temp_dir, f'page_{page_num}.png')
                image.save(image_path, 'PNG')
                img_w, img_h = image.size
                
                # 使用OCR检测图片中的文字
                if self.ocr_reader:
                    results = self.ocr_reader.readtext(image_path)
                    
                    for (bbox, text, confidence) in results:
                        if confidence > 0.5:  # 置信度阈值
                            # 检测身份证号码
                            id_matches = re.finditer(self.patterns['id_card'], text)
                            for match in id_matches:
                                privacy_info.append({
                                    'type': '身份证号码(图片)',
                                    'value': match.group(),
                                    'bbox': bbox,
                                    'img_size': (img_w, img_h),
                                    'confidence': confidence,
                                    'pattern': 'image'
                                })
                            
                            # 检测手机号码
                            phone_matches = re.finditer(self.patterns['phone'], text)
                            for match in phone_matches:
                                privacy_info.append({
                                    'type': '手机号码(图片)',
                                    'value': match.group(),
                                    'bbox': bbox,
                                    'img_size': (img_w, img_h),
                                    'confidence': confidence,
                                    'pattern': 'image'
                                })
                            
                            # 检测姓名（仅在身份证/证书上下文中）
                            if len(text) >= 2 and len(text) <= 4:
                                if re.match(r'^[\u4e00-\u9fa5]+$', text):
                                    # 检查上下文是否包含身份证或证书相关关键词
                                    context_keywords = ['姓名', '身份证', '证书', '持证人', '申请人']
                                    # 获取周围文本作为上下文
                                    context_text = ""
                                    for (ctx_bbox, ctx_text, ctx_conf) in results:
                                        if ctx_conf > 0.3:  # 降低置信度要求获取更多上下文
                                            context_text += ctx_text + " "
                                    
                                    # 只有在包含相关关键词时才遮盖姓名
                                    if any(keyword in context_text for keyword in context_keywords):
                                        privacy_info.append({
                                            'type': '姓名(图片)',
                                            'value': text,
                                            'bbox': bbox,
                                            'img_size': (img_w, img_h),
                                            'confidence': confidence,
                                            'pattern': 'image'
                                        })

                # 二维码 & 条形码检测（仅在证书/身份证上下文中）
                try:
                    # 检查页面是否包含证书或身份证相关关键词
                    page_text = ""
                    for (_, text, _) in results:
                        page_text += text + " "
                    
                    # 只有在包含相关关键词时才检测二维码/条形码
                    cert_keywords = ['证书', '身份证', '持证人', '二维码', '条码', '验证码']
                    should_detect_codes = any(keyword in page_text for keyword in cert_keywords)
                    
                    if should_detect_codes:
                        # OpenCV QR 检测
                        qr_detector = cv2.QRCodeDetector()
                        img_cv = cv2.imread(image_path)
                        if img_cv is not None:
                            data, points, _ = qr_detector.detectAndDecode(img_cv)
                            if points is not None and len(points) == 4 and data:  # 必须有数据才遮盖
                                pts = points.reshape(4, 2).tolist()
                                privacy_info.append({
                                    'type': '二维码',
                                    'value': data,
                                    'bbox': pts,
                                    'img_size': (img_w, img_h),
                                    'confidence': 0.99,
                                    'pattern': 'image'
                                })
                        # pyzbar 条形码/二维码检测
                        if zbar_decode is not None:
                            img_pil = Image.open(image_path).convert('RGB')
                            # 仅检测常见码制，避免触发zbar的DataBar断言警告
                            symbols = None
                            if ZBarSymbol is not None:
                                symbols = [
                                    ZBarSymbol.QRCODE,
                                    ZBarSymbol.CODE128,
                                    ZBarSymbol.CODE39,
                                    ZBarSymbol.EAN13,
                                    ZBarSymbol.EAN8,
                                    ZBarSymbol.UPCA,
                                    ZBarSymbol.UPCE,
                                    ZBarSymbol.ITF
                                ]
                            try:
                                objs = zbar_decode(img_pil, symbols=symbols) if symbols else zbar_decode(img_pil)
                            except Exception:
                                objs = []
                            for obj in objs:
                                # 只处理有实际数据的码
                                if obj.data:
                                    rect = obj.rect  # left, top, width, height
                                    bbox = [rect.left, rect.top, rect.left + rect.width, rect.top + rect.height]
                                    privacy_info.append({
                                        'type': '条形码/二维码',
                                        'value': obj.data.decode('utf-8', errors='ignore'),
                                        'bbox': bbox,
                                        'img_size': (img_w, img_h),
                                        'confidence': 0.99,
                                        'pattern': 'image'
                                    })
                except Exception:
                    pass
        
        except Exception as e:
            print(f"图片隐私检测失败 (页面 {page_num}): {e}")
        
        return privacy_info
    
    def _rect_overlap_ratio(self, a: fitz.Rect, b: fitz.Rect) -> float:
        inter = a & b
        if inter.is_empty or a.is_empty:
            return 0.0
        return (inter.width * inter.height) / (a.width * a.height)

    def _detect_seal_regions(self, page: fitz.Page) -> List[fitz.Rect]:
        """检测电子印章区域（红色圆形/椭圆区域近似）。返回需要保护的区域。"""
        protected_rects: List[fitz.Rect] = []
        try:
            pix = page.get_pixmap(alpha=False)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
            if img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            # 转HSV，寻找高饱和度红色
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            lower_red1 = np.array([0, 80, 80])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([160, 80, 80])
            upper_red2 = np.array([180, 255, 255])
            mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            mask = cv2.bitwise_or(mask1, mask2)
            mask = cv2.medianBlur(mask, 5)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            page_w, page_h = float(page.rect.width), float(page.rect.height)
            scale_x = page_w / float(pix.w)
            scale_y = page_h / float(pix.h)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < 500:  # 忽略太小的噪声
                    continue
                x, y, w, h = cv2.boundingRect(cnt)
                rect = fitz.Rect(x * scale_x, y * scale_y, (x + w) * scale_x, (y + h) * scale_y)
                protected_rects.append(rect)
        except Exception:
            return []
        return protected_rects

    def mask_text_privacy(self, page, privacy_info):
        """遮盖文本中的隐私信息（使用红线永久遮盖）"""
        for info in privacy_info:
            try:
                if info['pattern'] == 'text':
                    # 创建遮盖矩形
                    text_instances = page.search_for(info['value'])
                    for inst in text_instances:
                        rect = fitz.Rect(inst)
                        # 保护电子印章：若大幅重叠则跳过
                        protect_regions = self._detect_seal_regions(page)
                        if any(self._rect_overlap_ratio(rect, pr) > 0.5 for pr in protect_regions):
                            continue
                        # 添加红线注释并应用
                        page.add_redact_annot(rect, fill=(1, 1, 1))
                        
                        # 记录成功遮盖
                        self.mask_results['successful_masks'] += 1
                        self.mask_results['details'].append({
                            'page': page.number + 1,
                            'type': info['type'],
                            'value': info['value'],
                            'status': '成功',
                            'pattern': 'text'
                        })
                
            except Exception as e:
                print(f"文本遮盖失败: {e}")
                self.mask_results['failed_masks'] += 1
                self.mask_results['details'].append({
                    'page': page.number + 1,
                    'type': info['type'],
                    'value': info['value'],
                    'status': '失败',
                    'pattern': 'text',
                    'error': str(e)
                })
    
    def mask_image_privacy(self, page, privacy_info):
        """遮盖图片中的隐私信息（使用红线永久遮盖）"""
        for info in privacy_info:
            try:
                if info['pattern'] == 'image':
                    # 获取边界框坐标
                    bbox = info['bbox']
                    page_w = float(page.rect.width)
                    page_h = float(page.rect.height)
                    img_w, img_h = info.get('img_size', (None, None))

                    # 计算缩放比例（从图像像素坐标到PDF坐标）
                    if img_w and img_h and img_w > 0 and img_h > 0:
                        scale_x = page_w / float(img_w)
                        scale_y = page_h / float(img_h)
                    else:
                        # 缺少图像尺寸时，退化为1:1（可能不准确，但避免报错）
                        scale_x = 1.0
                        scale_y = 1.0

                    x1_img = y1_img = x2_img = y2_img = None

                    # EasyOCR 通常返回四点多边形：[[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
                    if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
                        if all(isinstance(pt, (list, tuple)) and len(pt) == 2 for pt in bbox):
                            xs = [float(pt[0]) for pt in bbox]
                            ys = [float(pt[1]) for pt in bbox]
                            x1_img, y1_img = min(xs), min(ys)
                            x2_img, y2_img = max(xs), max(ys)
                        elif all(isinstance(val, (int, float)) for val in bbox):
                            x1_img, y1_img, x2_img, y2_img = map(float, bbox)

                    if None in (x1_img, y1_img, x2_img, y2_img):
                        raise ValueError(f"无法解析bbox格式: {bbox}")

                    # 缩放到PDF坐标
                    x1 = x1_img * scale_x
                    y1 = y1_img * scale_y
                    x2 = x2_img * scale_x
                    y2 = y2_img * scale_y

                    # 确保坐标有效
                    if x2 <= x1:
                        x1, x2 = min(x1, x2), max(x1, x2)
                    if y2 <= y1:
                        y1, y2 = min(y1, y2), max(y1, y2)

                    rect = fitz.Rect(float(x1), float(y1), float(x2), float(y2))
                    # 保护电子印章：若大幅重叠则跳过
                    protect_regions = self._detect_seal_regions(page)
                    if any(self._rect_overlap_ratio(rect, pr) > 0.5 for pr in protect_regions):
                        continue
                    page.add_redact_annot(rect, fill=(1, 1, 1))
                    
                    # 记录成功遮盖
                    self.mask_results['successful_masks'] += 1
                    self.mask_results['details'].append({
                        'page': page.number + 1,
                        'type': info['type'],
                        'value': info['value'],
                        'status': '成功',
                        'pattern': 'image'
                    })
                
            except Exception as e:
                print(f"图片遮盖失败: {e}")
                self.mask_results['failed_masks'] += 1
                self.mask_results['details'].append({
                    'page': page.number + 1,
                    'type': info['type'],
                    'value': info['value'],
                    'status': '失败',
                    'pattern': 'image',
                    'error': str(e)
                })

    def _mark_pages_for_removal(self) -> Dict[str, List[int]]:
        """根据章节关键词标记需要删除的页面。
        - 技术方案：包含关键词的页全部删除
        - 报价清单：包含关键词的页全部删除
        - 财务报告：保留首次出现页，其后的连续财务页尽量删除，直到遇到明显新章节
        """
        pages_to_remove: List[int] = []
        finance_pages_to_remove: List[int] = []
        first_finance_kept: Optional[int] = None

        def contains_any(text: str, keys: List[str]) -> bool:
            return any(k in text for k in keys)

        n_pages = len(self.doc)
        for i in range(n_pages):
            try:
                text = self.doc[i].get_text() or ''
            except Exception:
                text = ''
            if contains_any(text, self.section_keywords['tech_plan']):
                pages_to_remove.append(i)
            if contains_any(text, self.section_keywords['quotation']):
                pages_to_remove.append(i)
            if contains_any(text, self.section_keywords['finance']):
                if first_finance_kept is None:
                    first_finance_kept = i
                else:
                    finance_pages_to_remove.append(i)

        # 尝试扩展财务报告连续页（启发式）：在首个财务页之后，直到出现“第.*章|附录|结束|目 录”等新章节/目录停止
        if first_finance_kept is not None:
            stop_markers = ['第', '章', '附录', '结束', '目 录', '目录', '技术方案', '报价']
            for j in range(first_finance_kept + 1, n_pages):
                if j in finance_pages_to_remove:
                    continue
                try:
                    t = self.doc[j].get_text() or ''
                except Exception:
                    t = ''
                if any(m in t for m in stop_markers):
                    break
                finance_pages_to_remove.append(j)

        return {
            'remove_pages': sorted(list(set(pages_to_remove))),
            'remove_finance_pages': sorted(list(set(finance_pages_to_remove)))
        }
    
    def mask_privacy_info(self):
        """遮盖PDF中的所有隐私信息"""
        try:
            for page_num in range(len(self.doc)):
                page = self.doc[page_num]
                
                # 获取页面文本
                text = page.get_text()
                
                # 检测文本中的隐私信息
                text_privacy = self.detect_text_privacy(text)
                
                # 检测图片中的隐私信息
                image_privacy = self.detect_image_privacy(page_num)
                
                # 统计检测到的隐私信息
                total_privacy = text_privacy + image_privacy
                self.mask_results['total_found'] += len(total_privacy)
                
                # 遮盖文本隐私信息
                if text_privacy:
                    self.mask_text_privacy(page, text_privacy)
                
                # 遮盖图片隐私信息
                if image_privacy:
                    self.mask_image_privacy(page, image_privacy)

                # 应用当前页的红线遮盖，使内容不可逆
                try:
                    page.apply_redactions()
                except Exception:
                    pass
            # 章节删除
            rm = self._mark_pages_for_removal()
            remove_list = sorted(list(set(rm['remove_pages'] + rm['remove_finance_pages'])), reverse=True)
            for idx in remove_list:
                try:
                    self.doc.delete_page(idx)
                    self.mask_results['details'].append({
                        'page': idx + 1,
                        'type': '章节删除',
                        'value': '章节页',
                        'status': '已删除',
                        'pattern': 'section'
                    })
                except Exception as e:
                    self.mask_results['details'].append({
                        'page': idx + 1,
                        'type': '章节删除',
                        'value': '章节页',
                        'status': '失败',
                        'pattern': 'section',
                        'error': str(e)
                    })
            
            return self.mask_results
            
        except Exception as e:
            return {
                'error': f'隐私信息遮盖失败: {str(e)}',
                'total_found': self.mask_results['total_found'],
                'successful_masks': self.mask_results['successful_masks'],
                'failed_masks': self.mask_results['failed_masks'],
                'details': self.mask_results['details']
            }
    
    def save_masked_pdf(self, output_path):
        """保存遮盖后的PDF"""
        try:
            # 使用增强调优选项，清理被遮盖对象，减少被恢复风险
            self.doc.save(output_path, deflate=True, garbage=4, clean=True, incremental=False)
            return True
        except Exception as e:
            print(f"保存PDF失败: {e}")
            return False
    
    def close(self):
        """关闭PDF文档"""
        if self.doc:
            self.doc.close()
    
    def __del__(self):
        """析构函数"""
        self.close()

