'''
Date: 2025-03-31 16:32:48
LastEditors: Zfj
LastEditTime: 2025-04-02 09:46:34
FilePath: /python-ocr/api_client.py
Description: API客户端功能
'''
import requests
import tempfile
import json
import tkinter.messagebox as messagebox

class APIClient:
    access_token = None  # 新增类变量
    
    def __init__(self, app=None):
        self.base_url = "https://tp.cewaycloud.com"
        self.headers = {
            'Authorization': f'Bearer {APIClient.access_token}',
            'platform-id': '1689154431733325826',
            'tenant-id': '1660451255092543490',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.app = app  # Store app reference
    def btoa(text):
        return base64.b64encode(text.encode('utf-8')).decode('utf-8')
    
    @classmethod
    def fetch_token(cls, username, password):
        import base64
        
        # 添加缺失的URL定义
        url = 'https://tp.cewaycloud.com/auth/oauth/token?randomStr=blockPuzzle&code=&grant_type=password'
        
        auth_str = base64.b64encode(b'social:social').decode('utf-8')
        headers = {
            'accept': 'application/json',
            'authorization': f"Basic {auth_str}",
            'content-type': 'application/x-www-form-urlencoded',
            'platform-id': '1689154431733325826',
            'tenant-id': '1660451255092543490'
        }
        data = {
            'username': username,
            'password': password
        }
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            # 将token存入类变量
            cls.access_token = response.json()['access_token']
            return cls.access_token
        
        else:
            print('Error fetching token:', response.text)
            return None
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
            # 处理shipment_quantity字段 - 同时支持中英文逗号
            quantity_str = str(table_data["shipment_quantity"])
            quantities = quantity_str.replace('，', ',').split(',')
            
            for i, quantity in enumerate(quantities):
                # Safely check for loading label
                if hasattr(self, 'app') and hasattr(self.app, 'data_grid'):
                    self.app.data_grid.set_loading(f"正在上传...")
                
                payload = {
                    "shipment_quantity": quantity.strip(),
                    "part_no": table_data["part_no"],
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
                            "test_result": "通过" 
                        } for item in table_data['items']
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
        finally:
            if hasattr(self, 'app') and hasattr(self.app, 'data_grid'):
                self.app.data_grid.clear_loading()