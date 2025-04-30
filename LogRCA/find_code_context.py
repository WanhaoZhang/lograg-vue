import json
import os
import re
import subprocess
import hashlib
from collections import defaultdict
from tqdm import tqdm
import glob

# 日志语句模式，扩展匹配范围
LOG_CODE_PATTERN = re.compile(
    r"(LOG\.\w+\(|logging\.\w+\(|\.\w+_log\(|\w+log\(|print\()"
)

# 创建日志片段到代码的缓存，避免重复搜索
CODE_CACHE = {}

def extract_log_info(log_line):
    """解析日志行，提取详细信息"""
    # 更强大的OpenStack日志解析正则表达式
    LOG_PATTERN = re.compile(
        r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+) "
        r"(?P<pid>\d+) (?P<level>\w+) (?P<module>[\w\.]+) "
        r"\[(?:req-)?(?P<request_id>[\w-]+)(?:.*?)\] "
        r"(?:(?P<ip>[\d\.]+) \"(?P<method>\w+) (?P<api_path>[^\s\"]+).*?\"|(?P<message>.*))"
    )
    
    match = LOG_PATTERN.search(log_line)
    if not match:
        # 尝试使用简化的模式匹配
        simple_pattern = re.compile(
            r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+).*?"
            r"(?P<level>\w+) (?P<module>[\w\.]+).*?"
            r"(?P<message>.*)"
        )
        match = simple_pattern.search(log_line)
        if not match:
            # 如果还是匹配不上，提取关键信息
            parts = log_line.split()
            if len(parts) > 4:
                return {
                    "full_text": log_line.strip(),
                    "message": " ".join(parts[4:])
                }
            return {"full_text": log_line.strip()}
    
    info = {
        "full_text": log_line.strip()
    }
    
    # 提取所有匹配的字段
    for field in ["timestamp", "pid", "level", "module", "request_id", "method", "api_path", "message"]:
        if match.group(field):
            info[field] = match.group(field).strip()
    
    return info

def extract_keywords(message, min_length=4):
    """从日志消息中提取关键词"""
    if not message:
        return []
    
    # 移除变量值：数字、引号内容、UUID、路径等
    cleaned = re.sub(r'\d+', ' ', message)
    cleaned = re.sub(r'[\'"][^\'"]*[\'"]', ' ', cleaned)
    cleaned = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', ' ', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\/\w+\/\w+', ' ', cleaned)
    
    # 提取所有单词
    words = re.findall(r'\b\w+\b', cleaned.lower())
    
    # 过滤短词和常见词
    common_words = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'not', 'have', 'has', 'been', 'was', 'were'}
    keywords = [w for w in words if len(w) >= min_length and w not in common_words]
    
    return keywords

def find_all_python_files(source_dir):
    """找到源码目录下所有的Python文件"""
    return glob.glob(f"{source_dir}/**/*.py", recursive=True)

def find_module_files(module_name, source_dir):
    """查找可能包含指定模块的Python文件"""
    potential_files = []
    
    # 尝试直接基于模块名查找
    module_path_parts = module_name.split('.')
    for i in range(len(module_path_parts)):
        partial_module = '.'.join(module_path_parts[i:])
        
        # 使用glob模式匹配
        pattern = f"{source_dir}/**/*{partial_module.replace('.', '/')}*.py"
        module_files = glob.glob(pattern, recursive=True)
        potential_files.extend(module_files)
        
        # 尝试找到包含模块名的文件
        last_part = module_path_parts[-1]
        pattern = f"{source_dir}/**/*{last_part}*.py"
        name_files = glob.glob(pattern, recursive=True)
        potential_files.extend(name_files)
    
    # 去重
    return list(set(potential_files))

def find_exact_log_statement(log_info, source_dir):
    """尝试在源码中找到与日志消息匹配的LOG语句"""
    if not log_info:
        return None
    
    # 检查缓存
    cache_key = log_info.get('full_text', '')[:100]  # 使用前100个字符作为缓存键
    if cache_key in CODE_CACHE:
        return CODE_CACHE[cache_key]
    
    message = log_info.get('message', '')
    if not message and 'full_text' in log_info:
        parts = log_info['full_text'].split(' ', 4)
        if len(parts) > 4:
            message = parts[4]
    
    if not message:
        return None
    
    # 提取关键词
    keywords = extract_keywords(message)
    if not keywords:
        return None
    
    # 确定要搜索的文件
    potential_files = []
    
    # 如果有模块信息，优先基于模块查找
    if 'module' in log_info:
        module_files = find_module_files(log_info['module'], source_dir)
        potential_files.extend(module_files)
    
    # 如果没有找到文件或文件数量太少，尝试基于关键词搜索整个源码
    if len(potential_files) < 5:
        for keyword in keywords[:2]:  # 只使用前两个关键词避免搜索过多
            cmd = f"grep -l '{keyword}' {source_dir}/**/*.py 2>/dev/null || true"
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.stdout:
                    keyword_files = result.stdout.splitlines()
                    potential_files.extend(keyword_files)
            except Exception:
                pass
    
    # 去重
    potential_files = list(set(potential_files))
    
    # 如果仍然没有找到文件，返回所有Python文件（最后的尝试）
    if not potential_files:
        try:
            all_files_cmd = f"find {source_dir} -name '*.py' | head -50"  # 限制文件数量
            result = subprocess.run(all_files_cmd, shell=True, capture_output=True, text=True)
            if result.stdout:
                potential_files = result.stdout.splitlines()
        except Exception:
            pass
    
    # 在每个文件中搜索日志语句
    best_match = None
    best_score = 0
    
    for py_file in potential_files:
        # 检查文件是否存在
        if not os.path.exists(py_file):
            continue
            
        try:
            # 读取文件内容
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                file_content = f.read()
            
            # 在文件中查找所有LOG语句
            log_lines = []
            for i, line in enumerate(file_content.splitlines(), 1):
                if LOG_CODE_PATTERN.search(line):
                    log_lines.append((i, line))
            
            # 对每个LOG语句计算与日志消息的匹配分数
            for line_num, line in log_lines:
                match_score = calculate_match_score(line, message, keywords)
                if match_score > best_score:
                    best_score = match_score
                    best_match = {
                        'file': py_file,
                        'line_number': line_num,
                        'log_statement': line.strip(),
                        'context': get_file_context(py_file, line_num),
                        'match_score': match_score
                    }
        except Exception as e:
            print(f"处理文件 {py_file} 时出错: {str(e)}")
    
    # 只有当匹配分数足够高时才返回结果
    result = best_match if best_score > 0.3 else None
    
    # 保存到缓存
    CODE_CACHE[cache_key] = result
    
    return result

def calculate_match_score(code_line, log_message, keywords):
    """计算代码行与日志消息的匹配分数"""
    # 基本分数：每个关键词在代码行中出现+0.2分
    score = 0.0
    for keyword in keywords:
        if keyword.lower() in code_line.lower():
            score += 0.2
    
    # 如果包含LOG语句模式，额外加分
    if LOG_CODE_PATTERN.search(code_line):
        score += 0.1
    
    # 如果日志消息的重要部分在代码行中，大幅加分
    msg_parts = re.split(r'[^\w]+', log_message.lower())
    msg_parts = [p for p in msg_parts if len(p) > 3]
    for part in msg_parts:
        if part in code_line.lower():
            score += 0.3
    
    # 归一化分数
    return min(score, 1.0)

def get_file_context(file_path, line_number, context_lines=5):
    """获取文件中指定行的上下文"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            all_lines = f.readlines()
        
        start_line = max(0, line_number - context_lines - 1)
        end_line = min(len(all_lines), line_number + context_lines)
        
        context = []
        for i in range(start_line, end_line):
            line_info = {
                'line_number': i + 1,
                'content': all_lines[i].rstrip()
            }
            context.append(line_info)
        
        return context
    except Exception as e:
        print(f"获取文件 {file_path} 上下文时出错: {str(e)}")
        return []

def find_code_for_logs(anomaly_data, source_dir):
    """为异常日志和上下文日志查找代码上下文"""
    results = []
    
    # 遍历每条异常记录
    for i, record in enumerate(tqdm(anomaly_data, desc="处理异常记录")):
        vm_id = record['vm_id']
        anomaly_log = record['anomaly_log']
        context_before = record['context_before']
        context_after = record['context_after']
        
        # 为异常日志查找代码上下文
        anomaly_info = extract_log_info(anomaly_log)
        print(f"\n处理VM ID: {vm_id}的异常日志")
        print(f"日志内容: {anomaly_log[:100]}...")
        
        code_context = find_exact_log_statement(anomaly_info, source_dir)
        if code_context:
            print(f"找到匹配代码! 文件: {os.path.basename(code_context['file'])}, 行: {code_context['line_number']}")
        else:
            print("未找到匹配代码")
        
        # 创建结果记录
        result_record = {
            'vm_id': vm_id,
            'anomaly_log': {
                'text': anomaly_log,
                'parsed_info': anomaly_info,
                'code_context': code_context
            },
            'context_before': [],
            'context_after': []
        }
        
        # 为上文日志查找代码上下文
        print(f"处理 {len(context_before)} 条上文日志...")
        for log in tqdm(context_before, desc="处理上文"):
            log_info = extract_log_info(log)
            code = find_exact_log_statement(log_info, source_dir)
            
            result_record['context_before'].append({
                'text': log,
                'parsed_info': log_info,
                'code_context': code
            })
        
        # 为下文日志查找代码上下文
        print(f"处理 {len(context_after)} 条下文日志...")
        for log in tqdm(context_after, desc="处理下文"):
            log_info = extract_log_info(log)
            code = find_exact_log_statement(log_info, source_dir)
            
            result_record['context_after'].append({
                'text': log,
                'parsed_info': log_info,
                'code_context': code
            })
        
        results.append(result_record)
        
        # 输出当前找到的匹配率
        found_anomaly = 1 if result_record['anomaly_log']['code_context'] else 0
        found_before = sum(1 for item in result_record['context_before'] if item['code_context'])
        found_after = sum(1 for item in result_record['context_after'] if item['code_context'])
        
        total_before = len(result_record['context_before'])
        total_after = len(result_record['context_after'])
        
        print(f"当前匹配率 - 异常日志: {found_anomaly}/1, 上文: {found_before}/{total_before}, 下文: {found_after}/{total_after}")
    
    return results

def main():
    print("开始查找日志对应的代码上下文...")
    
    # 设置路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 尝试不同的可能路径
    possible_paths = [
        os.path.join(script_dir, 'anomaly_context.json'),
        os.path.join(script_dir, 'output', 'anomaly_context.json'),
        os.path.join(script_dir, 'OpenStack', 'anomaly_context.json')
    ]
    
    # 找到存在的文件路径
    input_file = None
    for path in possible_paths:
        if os.path.exists(path):
            input_file = path
            break
    
    if not input_file:
        print("错误: 无法找到anomaly_context.json文件，请先运行extract_anomaly_context.py")
        print("尝试查找的路径:")
        for path in possible_paths:
            print(f"- {path}")
        return
    
    output_file = os.path.join('output', 'code_context.json')
    source_dir = os.path.join(script_dir, 'nova-13.0.0')
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 读取异常日志数据
    print(f"读取文件: {input_file}")
    with open(input_file, 'r') as f:
        anomaly_data = json.load(f)
    
    print(f"找到 {len(anomaly_data)} 条异常记录")
    
    # 查找代码上下文
    results = find_code_for_logs(anomaly_data, source_dir)
    
    # 保存结果
    print(f"保存结果到: {output_file}")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # 统计找到代码上下文的日志数量
    anomaly_with_code = sum(1 for r in results if r['anomaly_log']['code_context'])
    before_with_code = sum(sum(1 for log in r['context_before'] if log['code_context']) for r in results)
    after_with_code = sum(sum(1 for log in r['context_after'] if log['code_context']) for r in results)
    
    total_before = sum(len(r['context_before']) for r in results)
    total_after = sum(len(r['context_after']) for r in results)
    
    print(f"\n处理完成！")
    print(f"异常日志找到代码上下文: {anomaly_with_code}/{len(results)} ({100*anomaly_with_code/len(results):.1f}%)")
    print(f"上文日志找到代码上下文: {before_with_code}/{total_before} ({100*before_with_code/total_before:.1f}% 如果有)")
    print(f"下文日志找到代码上下文: {after_with_code}/{total_after} ({100*after_with_code/total_after:.1f}% 如果有)")
    print(f"总体匹配率: {100*(anomaly_with_code+before_with_code+after_with_code)/(len(results)+total_before+total_after):.1f}%")

if __name__ == "__main__":
    main() 