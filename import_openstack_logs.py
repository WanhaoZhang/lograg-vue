#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import datetime
import pymongo
from datetime import datetime, timedelta
import sys

def connect_mongodb(uri="mongodb://localhost:27017/", db_name="log-analysis"):
    """连接到MongoDB数据库"""
    try:
        client = pymongo.MongoClient(uri)
        db = client[db_name]
        print(f"成功连接到MongoDB: {db_name}")
        return db
    except Exception as e:
        print(f"连接MongoDB失败: {e}")
        sys.exit(1)

def import_openstack_logs(db, csv_path):
    """从CSV文件导入OpenStack日志到MongoDB"""
    collection = db.logs
    
    # 检查是否需要删除已有的OpenStack日志
    existing_logs = collection.count_documents({"service": "openstack-service"})
    if existing_logs > 0:
        confirm = input(f"发现{existing_logs}条OpenStack日志记录，是否删除? (y/n): ")
        if confirm.lower() == 'y':
            collection.delete_many({"service": "openstack-service"})
            print(f"已删除{existing_logs}条OpenStack日志记录")
    
    # 读取CSV文件并导入数据
    logs_to_insert = []
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # 转换日期时间字符串为MongoDB日期对象
            try:
                timestamp = datetime.strptime(row['timestamp'], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                print(f"警告: 无法解析时间戳 '{row['timestamp']}'，使用当前时间")
                timestamp = datetime.now()
            
            # 构建日志文档
            log_doc = {
                "timestamp": timestamp,
                "service": "openstack-service",
                "component": row.get('component', 'unknown'),
                "level": row.get('level', 'INFO'),
                "message": row.get('message', ''),
                "requestId": row.get('request_id', f"req-{timestamp.strftime('%Y%m%d%H%M%S')}"),
                "sourceIp": row.get('source_ip', '127.0.0.1'),
                "status": row.get('status', 'unknown'),
                "isRecent": True,
                "importedAt": datetime.now(),
                "details": {
                    "instanceId": row.get('instance_id', ''),
                    "userId": row.get('user_id', ''),
                    "projectId": row.get('project_id', ''),
                    "resourceType": row.get('resource_type', ''),
                    "resourceId": row.get('resource_id', ''),
                    "errorCode": row.get('error_code', '')
                },
                "originalService": row.get('original_service', ''),
                "stackTrace": row.get('stack_trace', '')
            }
            
            # 如果CSV中没有stack_trace字段，但有message字段，则生成一个模拟的堆栈跟踪
            if not row.get('stack_trace') and row.get('message'):
                component = row.get('component', 'unknown')
                log_doc["stackTrace"] = f"Error: {row.get('message')}\n"
                log_doc["stackTrace"] += f"at {component}.process ({component}.py:120)\n"
                log_doc["stackTrace"] += f"at OpenStack.API.call (API.py:85)\n"
                log_doc["stackTrace"] += f"at Client.request (client.py:245)"
            
            # 如果CSV中没有summary字段，则生成一个摘要
            if not row.get('summary'):
                log_doc["summary"] = f"OpenStack {component} 服务出现 {row.get('level')} 级别问题: {row.get('message')}。可能与资源分配或状态同步有关。"
            else:
                log_doc["summary"] = row.get('summary')
            
            logs_to_insert.append(log_doc)
    
    # 批量插入数据
    if logs_to_insert:
        result = collection.insert_many(logs_to_insert)
        print(f"成功导入 {len(result.inserted_ids)} 条OpenStack日志记录")
    else:
        print("CSV文件中没有有效的日志记录")

def main():
    if len(sys.argv) < 2:
        print("使用方法: python import_openstack_logs.py <csv_file_path> [mongodb_uri]")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    mongodb_uri = sys.argv[2] if len(sys.argv) > 2 else "mongodb://localhost:27017/"
    
    # 连接MongoDB
    db = connect_mongodb(mongodb_uri)
    
    # 导入日志
    import_openstack_logs(db, csv_path)

if __name__ == "__main__":
    main() 

# python import_openstack_logs.py openstack_logs.csv mongodb://localhost:27017/