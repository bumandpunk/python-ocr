'''
Date: 2025-03-31 16:30:52
LastEditors: Zfj
LastEditTime: 2025-04-01 14:21:23
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
    
    # 在process_pdf方法中确保提取坐标
    def process_pdf(self, pdf_path):
        """处理PDF文件并提取检测项"""
        self.detection_items = []  # 重置检测项列表
        doc = fitz.open(pdf_path)
        
        try:
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                blocks = page.get_text("words")
                
                for block in blocks:
                    text = block[4].strip()
                    if re.fullmatch(r'^\d+\.\d{2}$', text):
                        self.detection_items.append({  # 改为实例属性
                            "page": page_num + 1,
                            "text": text,
                            "measured": "",
                            "coordinates": (block[0], block[1], block[2], block[3])
                        })
        finally:
            doc.close()
        
        return self.detection_items
    
    def render_page(self, pdf_path, page_num, zoom_level):
        """渲染PDF页面（带缓存优化）"""
        import threading
        if not hasattr(self, '_render_thread'):
            self._render_thread = threading.Thread(
                target=self._render_page_async,  # 现在这个方法已定义
                args=(pdf_path, page_num, zoom_level)
            )
            self._render_thread.start()
        cache_key = (pdf_path, page_num, round(zoom_level, 2))
        
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

    # 如果需要异步渲染，可以添加这个方法
    def _render_page_async(self, pdf_path, page_num, zoom_level):
        """异步渲染PDF页面"""
        try:
            self.render_page(pdf_path, page_num, zoom_level)
        except Exception as e:
            print(f"异步渲染失败: {e}")
    
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
    
    def remove_item_from_cache(self, text, page):
        """强化缓存清理"""
        # 清除整个页面的缓存（修改为模糊清理）
        for key in list(self.page_cache.keys()):
            if key[1] == page:  # 匹配页码
                del self.page_cache[key]
        
        # 精确移除检测项（新增坐标校验）
        self.detection_items = [
            item for item in self.detection_items 
            if not (item["text"] == text 
                   and item["page"] == page + 1)
            # 移除错误的坐标校验条件
        ]