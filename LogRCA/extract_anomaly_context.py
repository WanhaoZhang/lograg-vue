import json
import re
from collections import defaultdict, Counter
from typing import List, Dict, Any, Set, Tuple
import os
import time
import yaml
import argparse
from tqdm import tqdm

# 读取配置文件
def load_config(config_path="config.yaml"):
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config

def read_anomaly_vms(file_path: str) -> List[str]:
    """读取包含异常VM ID的文件"""
    with open(file_path, 'r') as f:
        # 跳过第一行注释
        next(f)
        return [line.strip() for line in f if line.strip()]

def normalize_log(log_line: str) -> str:
    """
    标准化日志行，移除时间戳、ID等变动部分
    """
    # 移除日期时间格式 (如 "2023-05-20 15:30:45.123")
    normalized = re.sub(r'\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?', 'TIMESTAMP', log_line)
    
    # 移除十六进制ID (如 "0x1a2b3c4d")
    normalized = re.sub(r'0x[0-9a-fA-F]+', 'HEX_ID', normalized)
    
    # 移除UUID格式 (如 "550e8400-e29b-41d4-a716-446655440000")
    normalized = re.sub(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', 'UUID', normalized)
    
    # 移除IP地址 (如 "192.168.1.1")
    normalized = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', 'IP_ADDR', normalized)
    
    # 移除单独的数字 (如单独的数字如 "123" 或 "456")
    normalized = re.sub(r'\b\d+\b', 'NUMBER', normalized)
    
    # 移除引号内容
    normalized = re.sub(r'"[^"]*"', 'QUOTED_STRING', normalized)
    normalized = re.sub(r"'[^']*'", 'QUOTED_STRING', normalized)
    
    return normalized

def extract_log_template(logs: List[str]) -> Dict[str, List[int]]:
    """
    提取日志模板，将相似日志归为一组
    返回模板到日志索引的映射
    """
    templates = {}  # 模板 -> [日志索引列表]
    
    for i, log in enumerate(logs):
        # 标准化日志行
        normalized = normalize_log(log)
        
        # 添加到相应模板组
        if normalized not in templates:
            templates[normalized] = []
        templates[normalized].append(i)
    
    return templates

def are_logs_similar(log1: str, log2: str) -> bool:
    """
    判断两个日志是否相似，使用更精确的日志比较逻辑
    """
    # 标准化并比较
    norm1 = normalize_log(log1)
    norm2 = normalize_log(log2)
    
    # 完全相同的模板视为相似
    if norm1 == norm2:
        return True
    
    # 计算标准化后的单词级别的差异
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    # 如果共同词占比超过85%则视为相似
    common_words = words1.intersection(words2)
    total_words = words1.union(words2)
    if len(total_words) == 0:
        return False
    
    similarity = len(common_words) / len(total_words)
    return similarity > 0.85

def filter_similar_logs(logs: List[str]) -> List[str]:
    """
    更智能地过滤相似日志
    使用日志模板提取和更精确的相似度判断
    """
    if not logs:
        return []
    
    # 提取日志模板和对应索引
    templates = extract_log_template(logs)
    
    # 为每个模板组保留一个代表性日志
    unique_logs = []
    for indices in templates.values():
        if indices:  # 如果该模板组有日志
            # 保留第一条作为代表
            unique_logs.append(logs[indices[0]])
    
    return unique_logs

def extract_log_context(log_file: str, vm_ids: List[str], context_size: int = 3) -> List[Dict[str, Any]]:
    """提取异常日志及其上下文"""
    results = []
    
    print("读取日志文件...")
    # 读取所有日志行
    with open(log_file, 'r') as f:
        log_lines = f.readlines()
    
    print(f"处理 {len(log_lines)} 行日志...")
    # 为每个VM ID创建一个进度条
    for vm_id in vm_ids:
        print(f"处理VM ID: {vm_id}")
        anomaly_count = 0
        
        # 使用tqdm创建进度条
        vm_results = []  # 临时存储当前VM的结果
        for i in tqdm(range(len(log_lines)), desc=f"查找 {vm_id}"):
            line = log_lines[i]
            if vm_id in line:
                anomaly_count += 1
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
                
                # 收集上文和下文
                before_lines = [log_lines[j].strip() for j in range(start_idx, i)]
                after_lines = [log_lines[j].strip() for j in range(i + 1, end_idx)]
                
                # 添加到临时结果
                vm_results.append((anomaly_record, before_lines, after_lines))
        
        print(f"找到 {anomaly_count} 条包含 {vm_id} 的异常日志")
        
        if vm_results:
            print(f"对VM ID: {vm_id} 的上下文进行去重...")
            # 批量处理所有上下文进行更高效的去重
            for anomaly_record, before_lines, after_lines in vm_results:
                # 对上文和下文应用相似度过滤
                filtered_before = filter_similar_logs(before_lines)
                filtered_after = filter_similar_logs(after_lines)
                
                # 限制上下文长度
                anomaly_record['context_before'] = filtered_before[:context_size]
                anomaly_record['context_after'] = filtered_after[:context_size]
                
                # 添加到最终结果列表
                results.append(anomaly_record)
    
    return results

def main():
    start_time = time.time()
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="提取异常日志及其上下文")
    parser.add_argument("--config", type=str, default="config.yaml", help="配置文件路径")
    parser.add_argument("--anomaly-file", type=str, help="异常VM ID文件路径")
    parser.add_argument("--log-file", type=str, help="日志文件路径")
    parser.add_argument("--output", type=str, help="输出文件路径")
    parser.add_argument("--context-size", type=int, help="上下文大小")
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 文件路径
    anomaly_vms_file = args.anomaly_file or os.path.join(script_dir, config['source_code']['openstack_dir'], 'anomaly_labels.txt')
    log_file = args.log_file or os.path.join(script_dir, config['source_code']['openstack_dir'], 'openstack_abnormal.log')
    output_file = args.output or os.path.join(script_dir, config['output']['output_dir'], config['output']['anomaly_context_file'])
    
    # 上下文大小
    context_size = args.context_size or config['log_analysis']['context_size']
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    print(f"开始处理异常日志...")
    print(f"异常VM ID文件: {anomaly_vms_file}")
    print(f"日志文件: {log_file}")
    print(f"输出文件: {output_file}")
    print(f"上下文大小: {context_size}")
    
    # 读取异常VM ID
    vm_ids = read_anomaly_vms(anomaly_vms_file)
    print(f"读取到 {len(vm_ids)} 个异常VM ID")
    
    # 提取日志上下文
    results = extract_log_context(log_file, vm_ids, context_size)
    
    # 保存结果
    print(f"保存结果到 {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # 统计去重前后的日志数量
    total_before_logs = sum(len(result['context_before']) for result in results)
    total_after_logs = sum(len(result['context_after']) for result in results)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n处理完成！用时: {duration:.2f} 秒")
    print(f"找到 {len(results)} 条异常日志记录")
    print(f"总共提取了 {total_before_logs} 条上文和 {total_after_logs} 条下文")

if __name__ == '__main__':
    main() 