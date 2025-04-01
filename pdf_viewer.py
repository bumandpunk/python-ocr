'''
Date: 2025-03-31 16:32:36
LastEditors: Zfj
LastEditTime: 2025-03-31 16:38:51
FilePath: /python-ocr/pdf_viewer.py
Description: PDF查看器相关功能
'''
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import io

class PDFViewer:
    def __init__(self, app):
        self.app = app
        self.frame = None
        self.pdf_canvas = None
        self.zoom_scale = None
        self.tk_img = None
        self._pending_show_page = None  # 新增防抖标志
    
    def create_widgets(self, parent):
        """创建PDF查看器界面"""
        self.frame = ttk.Frame(parent)
        self.frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=2, pady=5)
        
        self.pdf_canvas = tk.Canvas(self.frame, bg='white')
        self.pdf_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.zoom_scale = ttk.Scale(self.frame, from_=0.5, to=2.0, value=1.0,
                                  command=self.update_zoom)
        self.zoom_scale.pack(fill=tk.X, padx=5, pady=5)
    
    def on_window_resize(self):
        """窗口大小变化时的处理"""
        if self.pdf_canvas:
            self.pdf_canvas.config(
                width=self.frame.winfo_width(),
                height=self.frame.winfo_height()
            )
            # 窗口大小变化后重新居中显示
            if hasattr(self.app, 'selected_index') and self.app.selected_index >= 0:
                self.show_page()
    
    def show_page(self):
        """显示当前页PDF（带防抖）"""
        if self._pending_show_page:
            self.frame.after_cancel(self._pending_show_page)
        
        self._pending_show_page = self.frame.after(100, self._real_show_page)
    
    def _real_show_page(self):
        """实际的页面渲染逻辑"""
        self._pending_show_page = None
        if not self.app.pdf_path:
            return
            
        # 新增：同步当前选中索引有效性检查
        if self.app.selected_index >= len(self.app.detection_items):
            self.app.selected_index = -1
            
        pix = self.app.pdf_processor.render_page(
            self.app.pdf_path,
            self.app.current_page,
            self.app.zoom_level
        )
        
        # 转换基础图像
        img = Image.open(io.BytesIO(pix.tobytes()))
        
        # 仅在有效索引时添加标注
        if 0 <= self.app.selected_index < len(self.app.detection_items):
            img = self.app.pdf_processor.add_annotations(
                img,
                self.app.detection_items,
                self.app.current_page,
                self.app.selected_index,
                self.app.zoom_level
            )

        # 更新显示（始终渲染基础PDF）
        self.tk_img = ImageTk.PhotoImage(img)
        self.pdf_canvas.delete("all")
        
        # 计算居中位置
        canvas_width = self.pdf_canvas.winfo_width()
        canvas_height = self.pdf_canvas.winfo_height()
        img_width, img_height = img.size
        
        # 自动滚动到选中区域前添加二次校验
        valid_selection = (
            self.app.selected_index >= 0 and 
            self.app.selected_index < len(self.app.detection_items) and 
            "coordinates" in self.app.detection_items[self.app.selected_index]
        )
        if valid_selection:
            item = self.app.detection_items[self.app.selected_index]
            if "coordinates" in item:
                x1, y1, x2, y2 = item["coordinates"]
                center_x = (x1 + x2) / 2 * self.app.zoom_level
                center_y = (y1 + y2) / 2 * self.app.zoom_level
                
                # 计算滚动位置使高亮区域居中
                scroll_x = max(0, center_x - canvas_width / 2)
                scroll_y = max(0, center_y - canvas_height / 2)
                
                # 设置滚动区域并定位
                self.pdf_canvas.config(scrollregion=(0, 0, img_width, img_height))
                self.pdf_canvas.xview_moveto(scroll_x / img_width)
                self.pdf_canvas.yview_moveto(scroll_y / img_height)
        self.pdf_canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)
    
    def update_zoom(self, value):
        """更新缩放级别"""
        self.app.zoom_level = float(value)
        # 清除缓存强制重新渲染
        self.app.pdf_processor.page_cache.clear()
        self.show_page()
    
    def clear_page(self):
        """清除PDF显示（使用正确的canvas引用）"""
        if hasattr(self, 'pdf_canvas'):  # 使用实际存在的属性名
            self.pdf_canvas.delete("all")
        self.current_page = 0
        self.pdf_images = []
        if hasattr(self, '_pdf_document'):
            del self._pdf_document