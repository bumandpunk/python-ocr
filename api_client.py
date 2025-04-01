'''
Date: 2025-03-31 16:32:48
LastEditors: Zfj
LastEditTime: 2025-04-01 10:01:54
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
    
    def upload_inspection_data(self, table_data):
        """上传检测数据"""
        try:
            payload = {
                "shipment_quantity": table_data["shipment_quantity"],
                "select_part": "1906612977607086080",
                "customer_name": "",
                "product_name": table_data['filename'],
                "drawing_number": "",
                "material_name": "",
                "project_number": "",
                "standard": "",
                "inspection_date": "2025-03-31",
                "visual_inspection": [],
                "a174340265468111707": [
                    {
                        "testing_method": "全检",
                        "inspection_items": item["检测值"],
                        "measuring_instrument": "DC",
                        "test_result_1": item["实测值1"],
                        "test_result_2": item["实测值2"],
                        "test_result_3": item["实测值3"],
                        "test_result_4": item["实测值4"],
                        "test_result_5": item["实测值5"],
                        "test_result_6": item["实测值6"],
                        "test_result": "通过" if all(v == item["实测值1"] for v in [item["实测值1"], item["实测值2"], item["实测值3"]]) else "不通过"
                    } for item in table_data['data']
                ],
                "templateId": "1905622813184503808"
            }
            
            response = requests.post(
                f'{self.base_url}/fd/formInstance',
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return True
        except Exception as e:
            raise Exception(f"上传失败: {str(e)}")