'''
Date: 2025-03-31 16:30:29
LastEditors: Zfj
LastEditTime: 2025-03-31 16:37:58
FilePath: /python-ocr/pdf_inspector.py
Description: 主应用类
'''
import tkinter as tk
from tkinter import ttk
from pdf_processor import PDFProcessor
from data_grid import DataGrid
from pdf_viewer import PDFViewer
from api_client import APIClient

class PDFInspectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF检测项分析系统")
        self.root.attributes('-fullscreen', True)
        
        # 初始化组件
        self.pdf_processor = PDFProcessor()
        self.api_client = APIClient()
        self.data_grid = DataGrid(self)
        self.pdf_viewer = PDFViewer(self)
        
        # 初始化变量
        self.pdf_path = ""
        self.detection_items = []
        self.current_page = 0
        self.zoom_level = 1.0
        self.selected_index = -1
        
        # 设置界面
        self.create_widgets()
        self.setup_bindings()
        
    def create_widgets(self):
        """创建主界面布局"""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧数据面板
        self.data_grid.create_widgets(main_frame)
        
        # 右侧PDF面板
        self.pdf_viewer.create_widgets(main_frame)
    
    def setup_bindings(self):
        """设置事件绑定"""
        self.root.bind("<Escape>", self.toggle_fullscreen)
        self.root.bind("<Configure>", self.on_window_resize)
    
    def toggle_fullscreen(self, event=None):
        """切换全屏模式"""
        self.root.attributes('-fullscreen', not self.root.attributes('-fullscreen'))
    
    def on_window_resize(self, event):
        """窗口大小变化时的自适应布局"""
        self.data_grid.on_window_resize()
        self.pdf_viewer.on_window_resize()
    
    def fetch_pdf(self):
        """获取PDF文件"""
        part_number = self.data_grid.get_part_number()
        if not part_number:
            tk.messagebox.showerror("错误", "请输入零件号")
            return
        
        try:
            pdf_data, original_filename = self.api_client.fetch_pdf(part_number)
            self.pdf_path = self.pdf_processor.save_temp_pdf(pdf_data)
            self.detection_items = self.pdf_processor.process_pdf(self.pdf_path)
            
            # 更新UI
            self.data_grid.update_data(self.detection_items, original_filename)
            self.pdf_viewer.show_page()
            
        except Exception as e:
            tk.messagebox.showerror("错误", f"获取PDF失败: {str(e)}")
            self.pdf_path = ""
    
    # 删除整个export_excel方法