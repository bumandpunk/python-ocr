'''
Date: 2025-03-31 16:30:16
LastEditors: Zfj
LastEditTime: 2025-04-01 15:55:07
FilePath: /python-ocr/main.py
Description: 
'''
import tkinter as tk
from pdf_inspector import PDFInspectorApp
from api_client import APIClient

if __name__ == "__main__":
    # 先获取token（示例账号密码，请替换为实际值）
    APIClient.fetch_token("im0204", "JFat0Zdc")
    
    # 然后创建应用
    root = tk.Tk()
    app = PDFInspectorApp(root)
    root.mainloop()