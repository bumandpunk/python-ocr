'''
Date: 2025-03-31 16:30:16
LastEditors: Zfj
LastEditTime: 2025-04-07 09:45:45
FilePath: /python-ocr/main.py
Description: 
'''
import tkinter as tk
from pdf_inspector import PDFInspectorApp
from api_client import APIClient

if __name__ == "__main__":
    # 获取token
    token = APIClient.fetch_token("im0199", "JFat0Zdc")
    if not token:
        raise RuntimeError("获取token失败")
    
    # 创建并配置APIClient
    api_client = APIClient()
    APIClient.access_token = token  # 确保类变量被正确设置
    
    # 创建应用
    root = tk.Tk()
    app = PDFInspectorApp(root, api_client)
    root.mainloop()