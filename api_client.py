'''
Date: 2025-03-31 16:32:48
LastEditors: Zfj
LastEditTime: 2025-03-31 16:38:57
FilePath: /python-ocr/api_client.py
Description: API客户端功能
'''
import requests
import tempfile
import json
import tkinter.messagebox as messagebox

class APIClient:
    def __init__(self):
        self.base_url = "https://tp.cewaycloud.com"
        self.headers = {
            'authorization': 'Bearer 2c3e37de-3c7d-42eb-8418-86a55059055e',
            'platform-id': '1689154431733325826',
            'tenant-id': '1660451255092543490',
            'content-type': 'application/json;charset=UTF-8'
        }
    
    def fetch_pdf(self, part_number):
        """获取PDF文件"""
        payload = {
            "templateId": "1737101682450153472",
            "current": 1,
            "size": 10,
            "queryFieldList": [{
                "fieldName": "seq_id",
                "fieldValue": part_number,
                "operType": "fuzzy"
            }]
        }
        
        response = requests.post(
            f'{self.base_url}/fd/formInstance/page',
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()
        if data['code'] != 0 or not data['data']['records']:
            raise ValueError("未找到相关PDF文档")
        
        # 解析JSON字符串获取文件信息
        up_mod = data['data']['records'][0]['up_mod']
        file_info = json.loads(up_mod)[0]
        
        # 获取原始文件名和文件路径
        original_filename = file_info['originalFileName']
        file_path = file_info['fileName']
        
        # 下载PDF文件
        pdf_url = f"{self.base_url}{file_path}"
        pdf_response = requests.get(pdf_url)
        pdf_response.raise_for_status()
        
        return pdf_response.content, original_filename