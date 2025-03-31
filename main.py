'''
Date: 2025-03-31 16:30:16
LastEditors: Zfj
LastEditTime: 2025-03-31 16:30:23
FilePath: /python-ocr/main.py
Description: 
'''
import tkinter as tk
from pdf_inspector import PDFInspectorApp

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFInspectorApp(root)
    root.mainloop()