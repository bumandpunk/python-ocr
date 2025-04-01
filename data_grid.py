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
        self.frame = ttk.Frame(parent, width=760)  # 增加到800宽度
        self.frame.pack_propagate(False)
        self.frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=2, pady=2)
        
        # 工具栏
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(fill=tk.X, pady=5)
        
        ttk.Label(toolbar, text="零件号:").pack(side=tk.LEFT)
        self.part_number_entry = ttk.Entry(toolbar, width=15)
        self.part_number_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(toolbar, text="获取PDF", command=self.app.fetch_pdf).pack(side=tk.LEFT)
        # 修改工具栏，移除之前的删除行和增加行按钮
        # 只保留上传数据按钮
        ttk.Button(toolbar, text="增加行", command=self.add_row).pack(side=tk.LEFT, padx=5)
        ttk.Label(toolbar, text="出货数量:").pack(side=tk.LEFT)
        self.shipment_quantity_entry = ttk.Entry(toolbar, width=8)
        self.shipment_quantity_entry.pack(side=tk.LEFT, padx=5)
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
        col_widths = [5, 7, 7, 7, 7, 7, 7, 7]
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
        self.frame.config(width=750)
    
    def update_data(self, detection_items, filename):
        """增量更新数据表格"""
        # 清除所有现有行（保留表头）
        for widget in self.grid_frame.grid_slaves():
            if int(widget.grid_info()["row"]) > 1:  # 保留表头两行
                widget.destroy()
        
        # 更新文件名显示
        self.filename_label.config(text=f"当前文件: {filename}")
        
        # 如果有数据才创建行（包括新增行）
        if detection_items:
            for row, item in enumerate(detection_items):
                self._create_row(row+2, item)  # 创建所有行，包括新增行
        
        current_rows = len(self.app.detection_items)
        new_rows = len(detection_items)
        
        # 创建所有行
        for row in range(new_rows):
            # 跳过新增行的PDF标注更新
            if not detection_items[row].get("is_new", False):
                self._create_row(row+2, detection_items[row])
        
        # 只更新变化的行
        if new_rows > current_rows:
            for row in range(current_rows, new_rows):
                self._create_row(row+2, detection_items[row])
        elif new_rows < current_rows:
            for row in range(new_rows, current_rows):
                for widget in self.grid_frame.grid_slaves(row=row+2):
                    widget.destroy()
        
        # 更新内容
        for row in range(min(current_rows, new_rows)):
            self._update_row(row+2, detection_items[row])
        
        # 统一在这里更新文件名显示
        self.filename_label.config(text=f"当前文件: {filename}")
    
    def _create_row(self, row, item):
        """创建单行数据"""
        # 修改序号计算方式 - 使用行号减2作为序号（因为表头占用了前两行）
        ttk.Label(self.grid_frame, text=str(row-1), width=4, anchor="center",
                relief="solid").grid(row=row, column=0, sticky="nsew")
        
        # 检测值 (仅新增行可编辑)
        if item.get("is_new", False):
            entry = ttk.Entry(self.grid_frame, width=10, justify="center")
            entry.insert(0, item["text"])
        else:
            entry = ttk.Label(self.grid_frame, text=item["text"], width=10, 
                             anchor="center", relief="solid")
        entry.grid(row=row, column=1, sticky="nsew")
        
        # 实测值
        for col in range(2, 8):
            entry = ttk.Entry(self.grid_frame, width=8, justify="center")
            entry.insert(0, item["measured"])
            entry.grid(row=row, column=col, sticky="nsew")
            entry.bind("<FocusIn>", lambda e, r=row-2: self.select_row(r))
            entry.bind("<Return>", self.handle_enter)
            entry.bind("<Tab>", self.handle_tab)
            entry.bind("<Down>", self.handle_down)
            entry.bind("<Right>", self.handle_right)
        
        # 删除按钮
        del_btn = ttk.Button(self.grid_frame, text="×", width=1,
                           command=lambda r=row-2: self.delete_row(r))
        del_btn.grid(row=row, column=8, sticky="nsew")
        del_btn.configure(takefocus=False)
    
    def _update_row(self, row, item):
        """更新单行数据"""
        # 更新检测值
        widgets = self.grid_frame.grid_slaves(row=row, column=1)
        if widgets:
            widget = widgets[0]
            if isinstance(widget, ttk.Entry):
                widget.delete(0, tk.END)
                widget.insert(0, item["text"])
            elif isinstance(widget, ttk.Label):
                widget.config(text=item["text"])
        
        # 更新实测值
        for col in range(2, 8):
            widgets = self.grid_frame.grid_slaves(row=row, column=col)
            if widgets and isinstance(widgets[0], ttk.Entry):
                widgets[0].delete(0, tk.END)
                widgets[0].insert(0, item["measured"])
        
        # 移除下面这行，因为filename更新应该在update_data方法中统一处理
        # self.filename_label.config(text=f"当前文件: {filename}")
    
    def _add_rows(self, start, end, items):
        """添加新行（优化版）"""
        for row in range(start, end):
            self._create_row(row+2, items[row])
    
    def _remove_rows(self, start, end):
        """移除多余行"""
        for row in range(start, end):
            for widget in self.grid_frame.grid_slaves(row=row+2):
                widget.destroy()
    
        # 移除下面这两行，因为它们已经在update_data方法中被调用
        # self.clear_data()
        # self.filename_label.config(text=f"当前文件: {filename}")
        
        # 调整列宽配置，减少前面列的宽度
        entry_widths = [4, 10, 8, 8, 8, 8, 8, 8, 4]  # 序号和删除按钮列宽减小
        headers = ["序号", "检测值", "实测值1", "实测值2", "实测值3", "实测值4", "实测值5", "实测值6", ""]
        
        # 更新列头
        for col, (text, width) in enumerate(zip(headers, entry_widths)):
            ttk.Label(self.grid_frame, text=text, width=width, anchor="center",
                     relief="solid").grid(row=1, column=col, sticky="nsew")
            self.grid_frame.columnconfigure(col, minsize=width*10, weight=1)
        
        for row, item in enumerate(detection_items, start=2):
            # 序号
            ttk.Label(self.grid_frame, text=str(row-1), width=entry_widths[0], anchor="center",
                     relief="solid").grid(row=row, column=0, sticky="nsew")
            
            # 检测值 (仅新增行可编辑)
            if item.get("is_new", False):  # 新增行标记
                entry = ttk.Entry(self.grid_frame, width=entry_widths[1], justify="center")
                entry.insert(0, item["text"])
                entry.grid(row=row, column=1, sticky="nsew")
            else:
                ttk.Label(self.grid_frame, text=item["text"], width=entry_widths[1], 
                         anchor="center", relief="solid").grid(row=row, column=1, sticky="nsew")
            
            # 实测值
            for col in range(2, 8):
                entry = ttk.Entry(self.grid_frame, width=entry_widths[col], justify="center")
                entry.insert(0, item["measured"])
                entry.grid(row=row, column=col, sticky="nsew")
                entry.bind("<FocusIn>", lambda e, r=row-2: self.app.data_grid.select_row(r))
                entry.bind("<Return>", self.handle_enter)
                entry.bind("<Tab>", self.handle_tab)
                entry.bind("<Down>", self.handle_down)
                entry.bind("<Right>", self.handle_right)
            
            # 在update_data方法中找到删除按钮创建部分
            # 删除按钮
            del_btn = ttk.Button(self.grid_frame, text="×", width=1,
                               command=lambda r=row-2: self.delete_row(r))
            del_btn.grid(row=row, column=8, sticky="nsew")
            del_btn.configure(takefocus=False)  # 禁止获取焦点
        
        # 更新列配置
        for col in range(9):  # 现在有9列
            self.grid_frame.columnconfigure(col, minsize=entry_widths[col]*10 if col < len(entry_widths) else 50, weight=1)

    def delete_row(self, row_index):
        """删除指定行（优化性能版）"""
        if not messagebox.askyesno("确认", "确定要删除当前行吗？"):
            return
            
        # 确保索引有效
        if 0 <= row_index < len(self.app.detection_items):
            # 批量收集要销毁的组件
            widgets_to_destroy = list(self.grid_frame.grid_slaves(row=row_index+2))
            
            # 从数据源中删除
            deleted_item = self.app.detection_items.pop(row_index)
            
            # 一次性销毁组件
            for widget in widgets_to_destroy:
                widget.destroy()
            
            # 合并重编号和布局更新到单个操作
            self._renumber_and_update(row_index, deleted_item)

    def _renumber_and_update(self, row_index, deleted_item):
        """重新编号并更新布局（优化性能）"""
        # 批量更新序号标签
        for idx in range(row_index, len(self.app.detection_items)):
            if widgets := self.grid_frame.grid_slaves(row=idx+3, column=0):
                widgets[0].config(text=str(idx+1))
        
        # 延迟更新PDF标记（仅当需要时）
        if (hasattr(self.app, 'pdf_viewer') and 
            hasattr(self.app, 'selected_index') and 
            self.app.selected_index >= 0):
            self.app.pdf_viewer.frame.after_idle(
                lambda: self.app.pdf_viewer.show_page()
            )
        
        # 自动选择行（如果有剩余行）
        new_index = max(0, min(row_index - 1, len(self.app.detection_items) - 1))
        self.app.selected_index = new_index if self.app.detection_items else None
        
        # 轻量级布局更新
        self.data_canvas.config(scrollregion=self.data_canvas.bbox("all"))

    def _update_pdf_annotations(self, deleted_item):
        """更新PDF标注"""
        # 获取当前页的所有项目
        current_page = deleted_item["page"] - 1
        page_items = [item for item in self.app.detection_items 
                     if item["page"]-1 == current_page]
        
        # 强制PDF重新渲染
        if hasattr(self.app, 'pdf_viewer'):
            self.app.pdf_viewer.show_page()

    def save_all_entered_values(self):
        """保存所有已输入的值到数据模型"""
        for idx, item in enumerate(self.app.detection_items):
            # 保存检测值
            widgets = self.grid_frame.grid_slaves(row=idx+2, column=1)
            if widgets:
                widget = widgets[0]
                if isinstance(widget, ttk.Entry):
                    item["text"] = widget.get()
                elif isinstance(widget, ttk.Label):
                    item["text"] = widget.cget("text")
            
            # 保存实测值
            for col in range(2, 8):
                widgets = self.grid_frame.grid_slaves(row=idx+2, column=col)
                if widgets and isinstance(widgets[0], ttk.Entry):
                    item["measured"] = widgets[0].get()
    
    
    def clear_data(self):
        """清除旧数据"""
        # 强制垃圾回收
        import gc
        for widget in self.grid_frame.grid_slaves():
            if int(widget.grid_info()["row"]) > 1:
                widget.destroy()
                widget = None
        gc.collect()
    
    def select_row(self, row_index):
        """选择行"""
        if not 0 <= row_index < len(self.app.detection_items):
            return
            
        self.app.selected_index = row_index
        target_page = self.app.detection_items[row_index]["page"] - 1
        
        if target_page != self.app.current_page:
            self.app.current_page = target_page
            self.app.pdf_viewer.show_page()
        else:
            # 同页时强制刷新高亮
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
        
        # 计算下一个焦点位置
        if current_col < 7:  # 在实测值列内
            next_col = current_col + 1
            next_row = current_row
        else:  # 最后一列，跳转到下一行第一列
            next_col = 1  # 检测值列
            next_row = current_row + 1 if current_row < len(self.app.detection_items) - 1 else current_row
        
        # 确保不会导航到无效位置
        if next_row >= len(self.app.detection_items):
            next_row = len(self.app.detection_items) - 1
        
        self.focus_cell(next_row, next_col)
        # 跳过删除按钮列(第8列)
        if current_col >= 7:  # 实测值6是第7列(0-based)
            next_row = current_row + 1 if current_row < len(self.app.detection_items) - 1 else current_row
            self.focus_cell(next_row, 1)  # 跳转到检测值列
        else:
            self.focus_cell(current_row, current_col + 1)
        # 推测此处缺少对应的if语句，补充完整的if-elif结构
        if current_row < len(self.app.detection_items) - 1:
            # 这里可以添加if条件满足时的代码逻辑
            pass
        elif current_row < len(self.app.detection_items) - 1:
            # 这里可以添加elif条件满足时的代码逻辑
            pass
            self.focus_cell(current_row + 1, 1)  # 下一行的检测值列(第1列)
    
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
            
        data = {
            "filename": self.filename_label.cget("text").replace("当前文件: ", ""),
            "shipment_quantity": self.shipment_quantity_entry.get(),
            "items": []
        }
        
        for idx, item in enumerate(self.app.detection_items):
            measured_values = []
            for col in range(2, 8):
                widgets = self.grid_frame.grid_slaves(row=idx+2, column=col)
                if widgets and isinstance(widgets[0], ttk.Entry):
                    measured_values.append(widgets[0].get())
                else:
                    measured_values.append("")
            
            data["items"].append({
                "检测值": item["text"],
                "实测值1": measured_values[0],
                "实测值2": measured_values[1],
                "实测值3": measured_values[2],
                "实测值4": measured_values[3],
                "实测值5": measured_values[4],
                "实测值6": measured_values[5]
            })
        
        return data

    def upload_data(self):
        """上传表格数据"""
        table_data = self.get_table_data()
        if table_data is None:
            messagebox.showwarning("警告", "没有可上传的数据")
            return
        
        try:
            success = self.app.api_client.upload_inspection_data(table_data)
            if success:
                # 保留当前文件名
                current_filename = self.filename_label.cget("text")
                # 清空数据但保留文件名
                self.app.detection_items = []
                self.update_data(self.app.detection_items, current_filename)
                messagebox.showinfo("成功", "数据上传成功")
        except Exception as e:
            messagebox.showerror("错误", str(e))

  

    def add_row(self):
        """在末尾添加新行"""
        new_row = {
            "text": "",  # 改为空字符串
            "measured": "",  # 改为空字符串 
            "page": 1,
            "is_new": True,  # 标记为新增行
            "coordinates": (0, 0, 0, 0)  # 添加默认坐标，避免PDF处理器报错
        }
        
        self.app.detection_items.append(new_row)
        
        # 强制更新表格数据
        self.update_data(self.app.detection_items, 
                       self.filename_label.cget("text").replace("当前文件: ", ""))
        
        # 自动滚动到底部
        self.data_canvas.yview_moveto(1.0)
        
        # 自动选中新添加的行
        self.app.selected_index = len(self.app.detection_items) - 1
        self.select_row(self.app.selected_index)
        
        # 强制更新布局并重新计算滚动区域
        self.grid_frame.update_idletasks()
        self.data_canvas.config(scrollregion=self.data_canvas.bbox("all"))
        self.data_canvas.xview_moveto(0)  # 确保从最左侧开始显示

    def _handle_grid_event(self, event):
        """统一处理网格事件"""
        # 添加事件去重
        if not hasattr(self, '_last_event_time'):
            self._last_event_time = 0
            
        current_time = time.time()
        if current_time - self._last_event_time < 0.1:  # 100ms防抖
            return
        self._last_event_time = current_time
        
        widget = event.widget
        if widget in self.grid_frame.grid_slaves():
            if event.keysym == "Return":
                self.handle_enter(event)
            elif event.keysym == "Tab":
                self.handle_tab(event)
            elif event.keysym == "Down":
                self.handle_down(event)
            elif event.keysym == "Right":
                self.handle_right(event)

    def _save_row_values(self, row_index):
        """保存指定行的数据"""
        if row_index >= len(self.app.detection_items):
            return
            
        item = self.app.detection_items[row_index]
        # 保存检测值
        widgets = self.grid_frame.grid_slaves(row=row_index+2, column=1)
        if widgets and isinstance(widgets[0], ttk.Entry):
            item["text"] = widgets[0].get()
        
        # 保存实测值
        for col in range(2, 8):
            widgets = self.grid_frame.grid_slaves(row=row_index+2, column=col)
            if widgets and isinstance(widgets[0], ttk.Entry):
                item["measured"] = widgets[0].get()