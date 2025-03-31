'''
Date: 2025-03-31 16:30:52
LastEditors: Zfj
LastEditTime: 2025-03-31 16:38:08
FilePath: /python-ocr/pdf_processor.py
Description: PDF处理相关功能
'''
import fitz
import re
import tempfile
from PIL import Image, ImageDraw

class PDFProcessor:
    def __init__(self):
        self.page_cache = {}
        self.current_pixmap = None
    
    def save_temp_pdf(self, pdf_data):
        """保存PDF到临时文件"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(pdf_data)
            return tmp_file.name
    
    def process_pdf(self, pdf_path):
        """处理PDF文件并提取检测项"""
        detection_items = []
        doc = fitz.open(pdf_path)
        
        try:
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                blocks = page.get_text("words")
                
                for block in blocks:
                    text = block[4].strip()
                    if re.fullmatch(r'^\d+\.\d{2}$', text):
                        detection_items.append({
                            "page": page_num + 1,
                            "text": text,
                            "measured": "",
                            "coordinates": (block[0], block[1], block[2], block[3])
                        })
        finally:
            doc.close()
        
        return detection_items
    
    def render_page(self, pdf_path, page_num, zoom_level):
        """渲染PDF页面"""
        cache_key = (page_num, round(zoom_level, 2))
        
        if cache_key in self.page_cache:
            return self.page_cache[cache_key]
        
        doc = fitz.open(pdf_path)
        try:
            page = doc.load_page(page_num)
            zoom_matrix = fitz.Matrix(zoom_level, zoom_level)
            pix = page.get_pixmap(matrix=zoom_matrix)
            self.page_cache[cache_key] = pix
            return pix
        finally:
            doc.close()
    
    def add_annotations(self, img, items, current_page, selected_index, zoom_level):
        """添加标注到图像"""
        draw = ImageDraw.Draw(img)
        current_items = [item for item in items if item["page"]-1 == current_page]
        
        for idx, item in enumerate(current_items):
            x0, y0, x1, y1 = item["coordinates"]
            rect = [
                x0 * zoom_level,
                y0 * zoom_level,
                x1 * zoom_level,
                y1 * zoom_level
            ]
            
            global_idx = current_page * 100 + idx
            if global_idx == selected_index:
                draw.rectangle(rect, outline="red", width=3)
            else:
                draw.rectangle(rect, outline="blue", width=2)
        
        return img