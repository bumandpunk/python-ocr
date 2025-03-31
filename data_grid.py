import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd

class DataGrid: 
    def __init__(self, app):
        self.app = app
        self.frame = None
        self.data_canvas = None
        self.grid_frame = None
        self.part_number_entry = None
        self.filename_label = None
    
    
    def create_widgets(self, parent):
        """创建数据表格界面"""
        self.frame = ttk.Frame(parent, width=630)
        self.frame.pack_propagate(False)
        self.frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=2, pady=2)
        
        # 工具栏
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(fill=tk.X, pady=5)
        
        ttk.Label(toolbar, text="零件号:").pack(side=tk.LEFT)
        self.part_number_entry = ttk.Entry(toolbar, width=15)
        self.part_number_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(toolbar, text="获取PDF", command=self.app.fetch_pdf).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="上传数据", command=self.upload_data).pack(side=tk.LEFT, padx=5)
        # 删除导出Excel按钮
        
        # 数据表格容器
        container = ttk.Frame(self.frame)
        container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        self.data_canvas = tk.Canvas(container, bg='white')
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.data_canvas.yview)
        
        self.data_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 内部框架
        self.grid_frame = ttk.Frame(self.data_canvas)
        self.data_canvas.create_window((0, 0), window=self.grid_frame, anchor=tk.NW)
        
        # 文件头
        self.filename_label = ttk.Label(self.grid_frame, text="当前文件: 未选择", anchor="center",
                                     relief="solid", font=('Helvetica', 9, 'bold'))
        self.filename_label.grid(row=0, column=0, columnspan=8, sticky="nsew")
        
        # 列头
        col_widths = [5, 8, 8, 8, 8, 8, 8, 8]
        headers = ["序号", "检测值", "实测值1", "实测值2", "实测值3", "实测值4", "实测值5", "实测值6"]
        for col, (text, width) in enumerate(zip(headers, col_widths)):
            ttk.Label(self.grid_frame, text=text, width=width, anchor="center",
                     relief="solid").grid(row=1, column=col, sticky="nsew")
            self.grid_frame.columnconfigure(col, minsize=width*10, weight=1)
        
        # 绑定事件
        self.data_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.data_canvas.bind("<Enter>", lambda e: self.data_canvas.focus_set())
        self.grid_frame.bind("<Configure>", lambda e: self.data_canvas.configure(
            scrollregion=self.data_canvas.bbox("all")
        ))
        self.data_canvas.configure(yscrollcommand=scrollbar.set)
    
    def on_window_resize(self):
        """窗口大小变化时的处理"""
        self.frame.config(width=630)
    
    def update_data(self, detection_items, filename):
        """更新数据表格"""
        self.clear_data()
        self.filename_label.config(text=f"当前文件: {filename}")
        
        entry_widths = [5, 8, 8, 8, 8, 8, 8, 8]
        for row, item in enumerate(detection_items, start=2):
            # 序号
            ttk.Label(self.grid_frame, text=str(row-1), width=entry_widths[0], anchor="center",
                     relief="solid").grid(row=row, column=0, sticky="nsew")
            
            # 检测值
            ttk.Label(self.grid_frame, text=item["text"], width=entry_widths[1], anchor="center",
                     relief="solid").grid(row=row, column=1, sticky="nsew")
            
            # 实测值
            for col in range(2, 8):
                entry = ttk.Entry(self.grid_frame, width=entry_widths[col], justify="center")
                entry.insert(0, item["measured"])
                entry.grid(row=row, column=col, sticky="nsew")
                
                # 事件绑定
                entry.bind("<FocusIn>", lambda e, r=row-2: self.app.data_grid.select_row(r))
                entry.bind("<Return>", self.handle_enter)
                entry.bind("<Tab>", self.handle_tab)
                entry.bind("<Down>", self.handle_down)
                entry.bind("<Right>", self.handle_right)
    
    def clear_data(self):
        """清除旧数据"""
        for widget in self.grid_frame.grid_slaves():
            if int(widget.grid_info()["row"]) > 1:
                widget.destroy()
    
    def select_row(self, row_index):
        """选择行"""
        self.app.selected_index = row_index
        target_page = self.app.detection_items[row_index]["page"] - 1
        
        if target_page != self.app.current_page:
            self.app.current_page = target_page
            self.app.pdf_viewer.show_page()
    
    def get_part_number(self):
        """获取零件号"""
        return self.part_number_entry.get().strip()
    
  
    def _on_mousewheel(self, event):
        """处理鼠标滚轮"""
        self.data_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def handle_enter(self, event):
        """回车键处理"""
        current_row = self.get_current_row(event)
        current_col = self.get_current_column(event)
        
        if current_row < len(self.app.detection_items) - 1:
            self.focus_cell(current_row + 1, current_col)
    
    def handle_tab(self, event):
        """Tab键处理"""
        current_row = self.get_current_row(event)
        current_col = self.get_current_column(event)
        
        if current_col < 7:
            self.focus_cell(current_row, current_col + 1)
        else:
            self.focus_cell(current_row + 1, 2)
    
    def handle_down(self, event):
        """向下箭头"""
        self.handle_enter(event)
    
    def handle_right(self, event):
        """向右箭头"""
        current_row = self.get_current_row(event)
        current_col = self.get_current_column(event)
        
        if current_col < 7:
            self.focus_cell(current_row, current_col + 1)
        else:
            self.focus_cell(current_row + 1, 2)
    
    def get_current_row(self, event):
        """获取当前行"""
        widget = event.widget
        info = widget.grid_info()
        return int(info["row"]) - 2
    
    def get_current_column(self, event):
        """获取当前列"""
        widget = event.widget
        info = widget.grid_info()
        return int(info["column"])
    
    def focus_cell(self, row, col):
        """聚焦指定单元格"""
        if row >= len(self.app.detection_items):
            return
            
        children = self.grid_frame.children
        for child in children.values():
            info = child.grid_info()
            if int(info["row"]) == row+2 and int(info["column"]) == col:
                child.focus_set()
                break
    
    def get_table_data(self):
        """获取表格数据"""
        if not hasattr(self.app, 'detection_items') or not self.app.detection_items:
            return None
            
        data = []
        for idx, item in enumerate(self.app.detection_items):
            measured_values = []
            for col in range(2, 8):
                entry = self.grid_frame.grid_slaves(row=idx+2, column=col)[0]
                measured_values.append(entry.get())
            
            data.append({
                "序号": idx+1,
                "检测值": item["text"],
                "实测值1": measured_values[0],
                "实测值2": measured_values[1],
                "实测值3": measured_values[2],
                "实测值4": measured_values[3],
                "实测值5": measured_values[4],
                "实测值6": measured_values[5]
            })
        
        return {
            "filename": self.filename_label.cget("text").replace("当前文件: ", ""),
            "data": data
        }

    def upload_data(self):
        """上传表格数据"""
        table_data = self.get_table_data()
        if table_data is None:
            messagebox.showwarning("警告", "没有可上传的数据")
            return
        
        # 这里可以添加你的上传逻辑
        # 例如: requests.post("你的API地址", json=table_data)
        messagebox.showinfo("成功", f"数据已准备上传:\n文件名: {table_data['filename']}\n数据条数: {len(table_data['data'])}")