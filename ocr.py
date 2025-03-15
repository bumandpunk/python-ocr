"""
PDF检测项交互分析系统（增强版）
依赖：pip install pytz pandas pymupdf pillow
"""

import tkinter as tk
from tkinter import ttk, filedialog
import fitz
import pandas as pd
from PIL import Image, ImageTk, ImageDraw
import io
import re

class PDFInspectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF检测项分析系统")
        self.root.attributes('-fullscreen', True)  # 设置为全屏模式
        
        # 新增全屏切换快捷键（ESC键退出全屏）
        self.root.bind("<Escape>", self.toggle_fullscreen)

        # 初始化变量
        self.pdf_path = ""
        self.detection_items = []
        self.current_page = 0
        self.zoom_level = 1.0
        self.selected_index = -1

        # 界面初始化
        self.create_widgets()
        
        # 修复macOS输入法问题
        if root.tk.call('tk', 'windowingsystem') == 'aqua':
            root.tk.call('::tk::unsupported::MacWindowStyle', 'style', root._w, 'plain')
    def toggle_fullscreen(self, event=None):
        """切换全屏模式"""
        self.root.attributes('-fullscreen', not self.root.attributes('-fullscreen'))
    def create_widgets(self):
        """创建界面布局"""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧数据面板
        left_panel = ttk.Frame(main_frame, width=400)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

        # 右侧PDF面板
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 创建控件
        self.create_data_grid(left_panel)
        self.create_pdf_viewer(right_panel)

    def create_data_grid(self, parent):
        """创建增强型数据表格"""
        # 工具栏
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=5)
        
        ttk.Button(toolbar, text="上传PDF", command=self.upload_pdf).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="导出Excel", command=self.export_excel).pack(side=tk.LEFT, padx=5)

        # 表格容器
        self.grid_frame = ttk.Frame(parent)
        self.grid_frame.pack(fill=tk.BOTH, expand=True)

        # 列标题
        headers = ["序号", "检测值", "实测值1", "实测值2", "实测值3"]
        for col, text in enumerate(headers):
            ttk.Label(self.grid_frame, text=text, width=10, borderwidth=1, relief="solid",
                     anchor="center").grid(row=0, column=col, sticky="nsew")

        # 配置网格布局
        for i in range(5):
            self.grid_frame.columnconfigure(i, weight=1)

    def create_pdf_viewer(self, parent):
        """创建PDF查看区域"""
        self.canvas = tk.Canvas(parent, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 缩放控件
        self.zoom_scale = ttk.Scale(parent, from_=0.5, to=2.0, value=1.0,
                                  command=self.update_zoom)
        self.zoom_scale.pack(fill=tk.X, padx=5, pady=5)

    def create_data_rows(self):
        """动态创建数据行"""
        # 清除旧数据
        for widget in self.grid_frame.grid_slaves():
            if int(widget.grid_info()["row"]) > 0:
                widget.destroy()

        # 创建新行
        for row, item in enumerate(self.detection_items, start=1):
            # 序号
            ttk.Label(self.grid_frame, text=str(row), width=10, anchor="center",
                     relief="solid").grid(row=row, column=0, sticky="nsew")
            
            # 检测值
            ttk.Label(self.grid_frame, text=item["text"], width=10, anchor="center",
                     relief="solid").grid(row=row, column=1, sticky="nsew")
            
            # 实测值（可编辑）
            entry = ttk.Entry(self.grid_frame, width=10, justify="center")
            entry.insert(0, item["measured"])
            entry.grid(row=row, column=2, sticky="nsew")
            entry.bind("<FocusIn>", lambda e, r=row-1: self.select_row(r))
            entry.bind("<Return>", self.handle_enter)
            entry.bind("<Tab>", self.handle_tab)
            entry.bind("<Down>", self.handle_down)
            entry.bind("<Right>", self.handle_right)

            entry = ttk.Entry(self.grid_frame, width=10, justify="center")
            entry.insert(0, item["measured"])
            entry.grid(row=row, column=3, sticky="nsew")
            entry.bind("<FocusIn>", lambda e, r=row-1: self.select_row(r))
            entry.bind("<Return>", self.handle_enter)
            entry.bind("<Tab>", self.handle_tab)
            entry.bind("<Down>", self.handle_down)
            entry.bind("<Right>", self.handle_right)

            entry = ttk.Entry(self.grid_frame, width=10, justify="center")
            entry.insert(0, item["measured"])
            entry.grid(row=row, column=4, sticky="nsew")
            entry.bind("<FocusIn>", lambda e, r=row-1: self.select_row(r))
            entry.bind("<Return>", self.handle_enter)
            entry.bind("<Tab>", self.handle_tab)
            entry.bind("<Down>", self.handle_down)
            entry.bind("<Right>", self.handle_right)
            
    def select_row(self, row_index):
        """选择行并更新PDF显示"""
        self.selected_index = row_index
        target_page = self.detection_items[row_index]["page"] - 1
        
        if target_page != self.current_page:
            self.current_page = target_page
            self.show_page()
        else:
            self.highlight_selected_item()
            
    def highlight_selected_item(self):
        """高亮当前选中项"""
        if self.selected_index >= 0:
            self.show_page()

    def handle_enter(self, event):
        """回车键处理：向下换行"""
        current_row = self.get_current_row(event)
        if current_row < len(self.detection_items) - 1:
            self.focus_cell(current_row + 1, 2)

    def handle_tab(self, event):
        """Tab键处理：向右换列（循环到下一行）"""
        current_row = self.get_current_row(event)
        self.focus_cell(current_row + 1, 2)

    def handle_down(self, event):
        """向下箭头处理"""
        self.handle_enter(event)

    def handle_right(self, event):
        """向右箭头处理：同行下一个单元格"""
        current_row = self.get_current_row(event)
        self.focus_cell(current_row, 2)  # 实测值已经是最后一列，保持原样

    def get_current_row(self, event):
        """获取当前行号"""
        widget = event.widget
        info = widget.grid_info()
        return int(info["row"]) - 1  # 减去标题行

    def focus_cell(self, row, col):
        """聚焦指定单元格"""
        if row >= len(self.detection_items):
            return
            
        children = self.grid_frame.children
        for child in children.values():
            info = child.grid_info()
            if int(info["row"]) == row+1 and int(info["column"]) == col:
                child.focus_set()
                break

    def upload_pdf(self):
        """上传PDF文件"""
        file_path = filedialog.askopenfilename(filetypes=[("PDF文件", "*.pdf")])
        if file_path:
            self.pdf_path = file_path
            self.process_pdf()
            self.create_data_rows()
            self.show_page()

    def process_pdf(self):
        """处理PDF文件"""
        self.detection_items = []
        doc = fitz.open(self.pdf_path)
        
        try:
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                blocks = page.get_text("blocks")
                
                for block in blocks:
                    text = block[4].strip()
                    if re.match(r'^\s*\d+\.\d{2}\s*$', text):
                        self.detection_items.append({
                            "page": page_num + 1,
                            "text": text,
                            "measured": "",
                            "coordinates": (block[0], block[1], block[2], block[3])
                        })
        finally:
            doc.close()

    def show_page(self):
        """显示当前页PDF"""
        if not self.pdf_path:
            return
            
        doc = fitz.open(self.pdf_path)
        try:
            page = doc.load_page(self.current_page)
            zoom_matrix = fitz.Matrix(self.zoom_level, self.zoom_level)
            pix = page.get_pixmap(matrix=zoom_matrix)
            img = Image.open(io.BytesIO(pix.tobytes()))
            img = self.add_annotations(img, page)
            
            self.tk_img = ImageTk.PhotoImage(img)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)
        finally:
            doc.close()

    def add_annotations(self, img, page):
        """添加标注框"""
        draw = ImageDraw.Draw(img)
        current_items = [item for item in self.detection_items 
                        if item["page"]-1 == self.current_page]
        
        for idx, item in enumerate(current_items):
            x0, y0, x1, y1 = item["coordinates"]
            rect = [
                x0 * self.zoom_level,
                y0 * self.zoom_level,
                x1 * self.zoom_level,
                y1 * self.zoom_level
            ]
            
            # 高亮当前选中项
            global_idx = self.current_page * 100 + idx  # 简化的全局索引计算
            if global_idx == self.selected_index:
                draw.rectangle(rect, outline="red", width=3)
            else:
                draw.rectangle(rect, outline="blue", width=2)
        
        return img

    def update_zoom(self, value):
        """更新缩放级别"""
        self.zoom_level = float(value)
        self.show_page()

    def export_excel(self):
        """导出Excel文件"""
        if not self.detection_items:
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx")]
        )
        if file_path:
            data = []
            for idx, item in enumerate(self.detection_items):
                # 获取三个实测值输入框的值
                measured1 = self.grid_frame.grid_slaves(row=idx+1, column=2)[0].get()
                measured2 = self.grid_frame.grid_slaves(row=idx+1, column=3)[0].get()
                measured3 = self.grid_frame.grid_slaves(row=idx+1, column=4)[0].get()
                
                data.append({
                    "序号": idx+1,
                    "检测值": item["text"],
                    "实测值1": measured1,
                    "实测值2": measured2,
                    "实测值3": measured3
                })
            
            pd.DataFrame(data).to_excel(file_path, index=False)

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFInspectorApp(root)
    root.mainloop()