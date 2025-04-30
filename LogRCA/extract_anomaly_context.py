import json
import re
from collections import defaultdict
from typing import List, Dict, Any
import os

def read_anomaly_vms(file_path: str) -> List[str]:
    """读取包含异常VM ID的文件"""
    with open(file_path, 'r') as f:
        # 跳过第一行注释
        next(f)
        return [line.strip() for line in f if line.strip()]

def extract_log_context(log_file: str, vm_ids: List[str], context_size: int = 10) -> List[Dict[str, Any]]:
    """提取异常日志及其上下文"""
    results = []
    
    # 读取所有日志行
    with open(log_file, 'r') as f:
        log_lines = f.readlines()
    
    # 遍历日志寻找异常
    for i, line in enumerate(log_lines):
        for vm_id in vm_ids:
            if vm_id in line:
                # 获取上下文
                start_idx = max(0, i - context_size)
                end_idx = min(len(log_lines), i + context_size + 1)
                
                # 创建新的记录
                anomaly_record = {
                    'vm_id': vm_id,
                    'anomaly_log': line.strip(),
                    'context_before': [],
                    'context_after': []
                }
                
                # 添加去重的上文（最多10条）
                before_lines = set(log_lines[j].strip() for j in range(start_idx, i))
                anomaly_record['context_before'] = list(before_lines)[:context_size]
                
                # 添加去重的下文（最多10条）
                after_lines = set(log_lines[j].strip() for j in range(i + 1, end_idx))
                anomaly_record['context_after'] = list(after_lines)[:context_size]
                
                # 添加到结果列表
                results.append(anomaly_record)
    
    return results

def main():
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 文件路径
    anomaly_vms_file = os.path.join(script_dir, 'OpenStack', 'anomaly_labels.txt')
    log_file = os.path.join(script_dir, 'OpenStack', 'openstack_abnormal.log')
    output_file = os.path.join('output/anomaly_context.json')
    
    # 读取异常VM ID
    vm_ids = read_anomaly_vms(anomaly_vms_file)
    
    # 提取日志上下文
    results = extract_log_context(log_file, vm_ids)
    
    # 保存结果
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"处理完成。找到 {len(results)} 条异常日志记录。")

if __name__ == '__main__':
    main() 