'''
Date: 2025-04-01 17:14:16
LastEditors: Zfj
LastEditTime: 2025-04-01 17:14:19
FilePath: /python-ocr/setup.py
Description: 
'''
from cx_Freeze import setup, Executable
import sys
import os

base = None
if sys.platform == "win32":
    base = "Win32GUI"

# 增强的构建配置
build_options = {
    # 保留核心包，去除可能自动包含的冗余依赖
    "packages": [
        "tkinter", "PIL", "pymupdf", "pandas",
        "sqlite3", "lxml"
    ],
    "excludes": [
        "pytz",  # pandas可能自动包含pytz
        "pandas.testing",
        "pandas._libs.tslibs",
        "numpy",  # 如果未直接使用
        "scipy",
        "matplotlib",
        "notebook",
        "tornado"
    ],
    # 新增压缩选项
    "compress": True,
    # 禁用非必要选项
    "include_msvcr": False,
    "bin_includes": [
        "vcruntime140.dll",
        "msvcp140.dll"
    ],
}

setup(
    name = "PDFInspector",
    version = "1.0",
    description = "戴德图纸品检系统",
    options = {"build_exe": build_options},
    executables = [Executable("ocr.py", base=base, target_name="PDFInspector.exe")]
)