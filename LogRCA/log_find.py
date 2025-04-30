import re
import os
import subprocess
import argparse
import sys
import json
import hashlib
from collections import defaultdict

# python log_find.py --source nova-13.0.0/ --log OpenStack/test.log --output output.txt -v
def parse_arguments():
    """ 解析命令行参数 """
    parser = argparse.ArgumentParser(description='通过OpenStack日志查找对应源码')
    parser.add_argument('--source', '-s', required=True, help='OpenStack源码目录路径')
    parser.add_argument('--log', '-l', required=True, help='日志文件路径')
    parser.add_argument('--output', '-o', default='log_to_source_mapping.txt', help='输出文件路径')
    parser.add_argument('--cache', '-c', action='store_true', help='启用源码缓存加速搜索')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细搜索过程')
    return parser.parse_args()

# 更强大的OpenStack日志解析正则表达式
LOG_PATTERN = re.compile(
    r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+) "
    r"(?P<pid>\d+) (?P<level>\w+) (?P<module>[\w\.]+) "
    r"\[(?:req-)?(?P<request_id>[\w-]+)(?:.*?)\] "
    r"(?:(?P<ip>[\d\.]+) \"(?P<method>\w+) (?P<api_path>[^\s\"]+).*?\"|(?P<message>.*))"
)

# 识别常见异常和错误信息的正则表达式
ERROR_PATTERN = re.compile(
    r"(?:Exception|Error|Traceback|Failed|failed|error|异常|错误|失败)"
)

# 识别可能包含LOG语句的模式
LOG_CODE_PATTERN = re.compile(
    r"(LOG\.\w+\(|logging\.\w+\()"
)

# 源码缓存，用于加速搜索
SOURCE_CACHE = {
    'modules': {},    # 模块映射到文件路径
    'api_paths': {},  # API路径映射到可能的处理函数
    'log_statements': {}  # 模块映射到LOG语句
}

def build_source_cache(source_dir, verbose=False):
    """构建源码缓存以加速搜索"""
    if verbose:
        print("构建源码缓存...")
    
    # 找出所有Python文件
    find_cmd = f"find {source_dir} -name '*.py' | sort"
    result = subprocess.run(find_cmd, shell=True, capture_output=True, text=True)
    if not result.stdout:
        print(f"警告: 在 {source_dir} 中未找到Python文件")
        return
        
    py_files = [f for f in result.stdout.splitlines() if f.strip()]
    total_files = len(py_files)
    
    # 分析每个Python文件
    for idx, py_file in enumerate(py_files, 1):
        if verbose:
            print(f"\r处理Python文件 {idx}/{total_files}: {os.path.basename(py_file)}", end="")
        
        # 读取文件内容
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            if verbose:
                print(f"\n无法读取 {py_file}: {str(e)}")
            continue
            
        # 提取模块名（基于文件路径）
        rel_path = os.path.relpath(py_file, source_dir)
        module_name = os.path.splitext(rel_path)[0].replace('/', '.')
        SOURCE_CACHE['modules'][module_name] = py_file
        
        # 查找API定义
        api_defs = find_api_definitions(content)
        for api_path in api_defs:
            if api_path not in SOURCE_CACHE['api_paths']:
                SOURCE_CACHE['api_paths'][api_path] = []
            SOURCE_CACHE['api_paths'][api_path].append({
                'file': py_file,
                'module': module_name,
                'line_numbers': api_defs[api_path]
            })
            
        # 查找LOG语句
        log_statements = find_log_statements(content)
        if log_statements:
            SOURCE_CACHE['log_statements'][module_name] = {
                'file': py_file,
                'statements': log_statements
            }
            
    if verbose:
        print("\n源码缓存构建完成！")
        print(f"- 模块数量: {len(SOURCE_CACHE['modules'])}")
        print(f"- API路径数量: {len(SOURCE_CACHE['api_paths'])}")
        print(f"- 带日志语句的模块数量: {len(SOURCE_CACHE['log_statements'])}")

def find_api_definitions(content):
    """分析文件内容，查找API定义"""
    api_defs = {}
    
    # 1. 寻找常见的API路由注册模式
    route_patterns = [
        r'@.*?route\([\'"]([^\'"]+)[\'"]',  # Flask/Pecan 风格的路由装饰器
        r'\.route\([\'"]([^\'"]+)[\'"]',    # Flask/Bottle 风格的路由方法
        r'router\.add_route\([\'"].*?[\'"], [\'"]([^\'"]+)[\'"]',  # Web框架路由注册
        r'\'OPTIONS\', \'([^\']+)\'',        # Nova/Neutron API定义
        r'\'([/\w]+)\': {',                  # API URL映射结构
    ]
    
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        for pattern in route_patterns:
            matches = re.findall(pattern, line)
            for match in matches:
                api_path = match
                # 确保API路径以/开头
                if not api_path.startswith('/'):
                    api_path = '/' + api_path
                    
                # 存储行号
                if api_path not in api_defs:
                    api_defs[api_path] = []
                api_defs[api_path].append(i)
                
    return api_defs

def find_log_statements(content):
    """分析文件内容，查找LOG语句及其上下文"""
    log_statements = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines, 1):
        if LOG_CODE_PATTERN.search(line):
            # 提取上下文 (前后各2行)
            start = max(0, i-3)
            end = min(len(lines), i+2)
            context = lines[start:end]
            
            # 创建日志语句条目
            log_entry = {
                'line_number': i,
                'log_text': line.strip(),
                'context': context,
                'hash': hashlib.md5(line.strip().encode()).hexdigest()[:8]
            }
            log_statements.append(log_entry)
            
    return log_statements

def extract_log_info(log_line):
    """解析日志行，提取详细信息"""
    match = LOG_PATTERN.search(log_line)
    if not match:
        return None
        
    info = {
        "timestamp": match.group("timestamp"),
        "pid": match.group("pid"),
        "level": match.group("level"),
        "module": match.group("module"),
        "request_id": match.group("request_id"),
        "full_text": log_line.strip()
    }
    
    # 提取消息或API信息
    if match.group("api_path"):
        info["method"] = match.group("method")
        info["api_path"] = match.group("api_path")
    
    if match.group("message"):
        info["message"] = match.group("message").strip()
        
        # 检查是否包含错误信息
        if ERROR_PATTERN.search(info["message"]):
            info["contains_error"] = True
            
            # 尝试提取异常名称
            exception_match = re.search(r'([\w\.]+Exception|[\w\.]+Error)', info["message"])
            if exception_match:
                info["exception_type"] = exception_match.group(1)
    
    return info

def find_exact_log_statement(log_info, source_dir, use_cache=False):
    """尝试在源码中找到与日志消息完全匹配的LOG语句"""
    if not log_info or 'message' not in log_info:
        return []
    
    # 准备搜索的文本（去除变量值）
    message = log_info['message']
    # 将消息中的数字、引号内容等替换为通配符
    search_text = re.sub(r'(\d+|"[^"]*"|\'[^\']*\')', '.*', message)
    # 将特殊字符转义
    search_text = re.escape(search_text).replace(r'\.\*', '.*')
    
    # 首先尝试基于模块名找到可能的源文件
    module_name = log_info['module']
    potential_files = []
    
    if use_cache and SOURCE_CACHE['modules']:
        # 从缓存中查找匹配模块
        for cached_module in SOURCE_CACHE['modules']:
            if cached_module.endswith(module_name) or module_name.endswith(cached_module):
                potential_files.append(SOURCE_CACHE['modules'][cached_module])
    else:
        # 手动搜索匹配模块的文件
        module_path_parts = module_name.split('.')
        for i in range(len(module_path_parts)):
            partial_module = '.'.join(module_path_parts[i:])
            find_cmd = f"find {source_dir} -path '*/{'/'.join(partial_module.split('.'))}*.py'"
            result = subprocess.run(find_cmd, shell=True, capture_output=True, text=True)
            if result.stdout:
                potential_files.extend([f for f in result.stdout.splitlines() if f.strip()])
    
    # 在可能的文件中搜索日志语句
    exact_matches = []
    
    for py_file in potential_files:
        grep_cmd = f"grep -n '{search_text}' {py_file}"
        result = subprocess.run(grep_cmd, shell=True, capture_output=True, text=True)
        
        if result.stdout:
            for line in result.stdout.splitlines():
                parts = line.split(':', 1)
                if len(parts) >= 2:
                    line_num = parts[0]
                    line_content = parts[1]
                    # 确认这是一个LOG语句
                    if LOG_CODE_PATTERN.search(line_content):
                        exact_matches.append({
                            'file': py_file,
                            'line_number': line_num,
                            'log_statement': line_content.strip(),
                            'match_type': '精确匹配',
                            'score': 10  # 高分表示高度相关
                        })
    
    # 如果没有找到精确匹配，尝试使用更宽松的搜索
    if not exact_matches:
        # 提取关键词
        keywords = re.findall(r'\b\w{4,}\b', message)
        if len(keywords) >= 2:
            keyword_pattern = '|'.join(keywords)
            for py_file in potential_files:
                grep_cmd = f"grep -n '{keyword_pattern}' {py_file}"
                result = subprocess.run(grep_cmd, shell=True, capture_output=True, text=True)
                
                if result.stdout:
                    for line in result.stdout.splitlines():
                        parts = line.split(':', 1)
                        if len(parts) >= 2:
                            line_num = parts[0]
                            line_content = parts[1]
                            if LOG_CODE_PATTERN.search(line_content):
                                # 计算关键词匹配数量作为分数
                                score = sum(1 for kw in keywords if kw.lower() in line_content.lower())
                                exact_matches.append({
                                    'file': py_file,
                                    'line_number': line_num,
                                    'log_statement': line_content.strip(),
                                    'match_type': '关键词匹配',
                                    'score': min(score, 9)  # 基于匹配关键词的数量评分(最高9分)
                                })
    
    # 按匹配分数排序
    return sorted(exact_matches, key=lambda x: x['score'], reverse=True)

def find_source_by_api(api_path, source_dir, use_cache=False, verbose=False):
    """查找处理指定API的源代码"""
    if not api_path:
        return []
    
    matches = []
    
    # 标准化API路径
    if not api_path.startswith('/'):
        api_path = '/' + api_path
    
    # 从缓存中搜索精确匹配
    if use_cache and SOURCE_CACHE['api_paths']:
        if api_path in SOURCE_CACHE['api_paths']:
            for entry in SOURCE_CACHE['api_paths'][api_path]:
                matches.append({
                    'file': entry['file'],
                    'module': entry['module'],
                    'line_numbers': entry['line_numbers'],
                    'match_type': '精确API路径匹配',
                    'score': 10
                })
    
    # 如果没有精确匹配，或未使用缓存，进行更灵活的搜索
    if not matches:
        # 将API路径分解为组件进行搜索
        path_parts = [p for p in api_path.split('/') if p]
        
        # 生成搜索模式
        search_patterns = []
        
        # 对于每个路径组件
        for part in path_parts:
            # 跳过版本号组件(如v1, v2)和纯数字ID
            if re.match(r'^v\d+$', part) or part.isdigit():
                continue
                
            # 添加可能的路由定义模式
            search_patterns.extend([
                f"route.*{part}",
                f"router.*{part}",
                f"@.*{part}",
                f"'{part}'",
                f"\"{part}\"",
                f"def {part}",
                f"class {part}"
            ])
        
        if verbose and search_patterns:
            print(f"搜索API路径: {api_path}")
            print(f"  使用以下模式: {search_patterns[:3]}...")
        
        # 对每个模式进行搜索
        for pattern in search_patterns:
            grep_cmd = f"grep -rn --include='*.py' '{pattern}' {source_dir}"
            result = subprocess.run(grep_cmd, shell=True, capture_output=True, text=True)
            
            if result.stdout:
                for line in result.stdout.splitlines():
                    try:
                        file_path, line_num, content = line.split(':', 2)
                        
                        # 计算匹配分数：基于匹配的路径组件数量
                        score = sum(1 for part in path_parts if part in content and not part.isdigit())
                        
                        # 额外的上下文匹配点
                        if 'route' in content.lower() or 'controller' in content.lower():
                            score += 2
                        if 'class' in content.lower() and any(part in content for part in path_parts):
                            score += 1
                            
                        matches.append({
                            'file': file_path,
                            'line_number': line_num,
                            'content': content.strip(),
                            'match_type': '路由模式匹配',
                            'score': min(score, 9)  # 最高9分
                        })
                    except ValueError:
                        continue  # 跳过格式不正确的行
    
    # 对匹配结果去重和排序
    unique_matches = {}
    for match in matches:
        key = f"{match['file']}:{match.get('line_number', 0)}"
        if key not in unique_matches or match['score'] > unique_matches[key]['score']:
            unique_matches[key] = match
    
    return sorted(unique_matches.values(), key=lambda x: x['score'], reverse=True)

def find_source_by_module(module_name, source_dir, use_cache=False, verbose=False):
    """查找与日志模块关联的源代码文件"""
    if not module_name:
        return []
    
    matches = []
    
    # 使用缓存进行模块查找
    if use_cache and SOURCE_CACHE['modules']:
        # 尝试直接匹配或子模块匹配
        for cached_module in SOURCE_CACHE['modules']:
            if module_name == cached_module or module_name.startswith(cached_module + '.'):
                matches.append({
                    'file': SOURCE_CACHE['modules'][cached_module],
                    'module': cached_module,
                    'match_type': '精确模块匹配',
                    'score': 10
                })
            elif cached_module.endswith(module_name) or cached_module.endswith('.' + module_name):
                matches.append({
                    'file': SOURCE_CACHE['modules'][cached_module],
                    'module': cached_module,
                    'match_type': '模块名后缀匹配',
                    'score': 8
                })
    
    # 如果没有从缓存中找到匹配，或未使用缓存
    if not matches:
        # 将模块名分解为组件
        module_parts = module_name.split('.')
        
        # 创建可能的模块路径模式
        module_patterns = []
        
        # 对于每个模块层级
        for i in range(len(module_parts)):
            # 获取从当前位置到末尾的子模块路径
            sub_module = '.'.join(module_parts[i:])
            # 获取从开始到当前位置的子模块路径
            parent_module = '.'.join(module_parts[:i+1])
            
            module_patterns.extend([
                f"/{'/'.join(sub_module.split('.'))}",
                f"import {sub_module}",
                f"from {parent_module} import",
                sub_module.replace('.', '/')
            ])
        
        if verbose and module_patterns:
            print(f"搜索模块: {module_name}")
            print(f"  使用以下模式: {module_patterns[:3]}...")
        
        # 搜索每个模式
        for pattern in module_patterns:
            find_cmd = f"find {source_dir} -path '*{pattern}*.py' -o -path '*{pattern}*/__init__.py'"
            result = subprocess.run(find_cmd, shell=True, capture_output=True, text=True)
            
            if result.stdout:
                for file_path in result.stdout.splitlines():
                    if os.path.isfile(file_path):
                        # 转换文件路径为Python模块
                        rel_path = os.path.relpath(file_path, source_dir)
                        if rel_path.endswith('__init__.py'):
                            rel_path = os.path.dirname(rel_path)
                        else:
                            rel_path = os.path.splitext(rel_path)[0]
                        
                        file_module = rel_path.replace('/', '.')
                        
                        # 计算匹配分数
                        score = 5  # 基础分
                        
                        # 检查模块名匹配度
                        if file_module == module_name:
                            score = 10  # 完全匹配
                        elif file_module.endswith(module_name):
                            score = 8   # 后缀匹配
                        elif module_name.endswith(file_module):
                            score = 7   # 前缀匹配
                        elif any(part in file_module for part in module_parts):
                            # 部分组件匹配
                            score += sum(1 for part in module_parts if part in file_module.split('.'))
                            
                        matches.append({
                            'file': file_path,
                            'module': file_module,
                            'match_type': '模块路径匹配',
                            'score': min(score, 10)  # 最高10分
                        })
    
    # 对匹配结果去重和排序
    unique_matches = {}
    for match in matches:
        key = match['file']
        if key not in unique_matches or match['score'] > unique_matches[key]['score']:
            unique_matches[key] = match
    
    return sorted(unique_matches.values(), key=lambda x: x['score'], reverse=True)

def get_file_context(file_path, line_number, context_lines=3):
    """获取文件中指定行的上下文内容"""
    if not os.path.isfile(file_path):
        return []
        
    try:
        line_number = int(line_number)
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)
        
        context = []
        for i in range(start, end):
            prefix = "-> " if i == line_number - 1 else "   "
            context.append(f"{prefix}{i+1}: {lines[i].rstrip()}")
            
        return context
    except Exception as e:
        return [f"无法读取文件上下文: {str(e)}"]

def analyze_logs(log_file_path, source_dir, use_cache=False, verbose=False):
    """分析日志文件并查找对应的源码位置"""
    results = []
    
    # 检查文件和目录是否存在
    if not os.path.isfile(log_file_path):
        print(f"错误: 日志文件 '{log_file_path}' 不存在")
        sys.exit(1)
        
    if not os.path.isdir(source_dir):
        print(f"错误: 源码目录 '{source_dir}' 不存在")
        sys.exit(1)
    
    # 如果启用缓存，先构建源码缓存
    if use_cache:
        build_source_cache(source_dir, verbose)
    
    try:
        # 读取日志文件
        with open(log_file_path, 'r', encoding='utf-8') as log_file:
            log_lines = log_file.readlines()
            
        total_lines = len(log_lines)
        print(f"开始分析 {total_lines} 行日志...")
        
        # 处理每一行日志
        for idx, line in enumerate(log_lines, 1):
            if verbose:
                print(f"\r处理日志行 {idx}/{total_lines}...", end="")
            else:
                # 简单进度条
                if idx % 10 == 0 or idx == total_lines:
                    print(f"\r处理进度: {idx}/{total_lines} [{idx/total_lines*100:.1f}%]", end="")
            
            # 解析日志信息
            log_info = extract_log_info(line)
            if not log_info:
                continue
                
            log_entry = {
                "log_text": line.strip(),
                "log_info": log_info,
                "source_matches": []
            }
            
            # 1. 尝试查找精确的日志语句
            exact_matches = find_exact_log_statement(log_info, source_dir, use_cache)
            if exact_matches:
                for match in exact_matches:
                    # 获取代码上下文
                    if 'line_number' in match:
                        match['context'] = get_file_context(match['file'], match['line_number'])
                    log_entry["source_matches"].append({
                        "type": "日志语句匹配",
                        "matches": match,
                        "relevance": "高"
                    })
            
            # 2. 如果有API路径，查找API处理代码
            if 'api_path' in log_info:
                api_matches = find_source_by_api(log_info['api_path'], source_dir, use_cache, verbose)
                if api_matches:
                    top_matches = api_matches[:3]  # 只保留最相关的几个匹配
                    for match in top_matches:
                        if 'line_number' in match:
                            match['context'] = get_file_context(match['file'], match['line_number'])
                    log_entry["source_matches"].append({
                        "type": "API处理代码",
                        "matches": top_matches,
                        "relevance": "中" if not exact_matches else "低"
                    })
            
            # 3. 查找模块相关的代码
            module_matches = find_source_by_module(log_info['module'], source_dir, use_cache, verbose)
            if module_matches:
                top_matches = module_matches[:2]  # 只保留最相关的几个匹配
                log_entry["source_matches"].append({
                    "type": "模块相关代码",
                    "matches": top_matches,
                    "relevance": "低" if exact_matches or 'api_path' in log_info else "中"
                })
            
            # 如果有源码匹配，添加到结果中
            if log_entry["source_matches"]:
                results.append(log_entry)
        
        print("\n日志分析完成！")
        print(f"共找到 {len(results)} 条日志的源码映射")
        
    except Exception as e:
        print(f"\n处理日志时出错: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
        
    return results

def save_results(results, output_file="log_to_source_mapping.txt"):
    """保存日志到源码的映射结果"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, entry in enumerate(results, 1):
                f.write("=" * 80 + "\n")
                f.write(f"日志条目 #{i}:\n{entry['log_text']}\n\n")
                
                # 输出日志信息
                f.write("日志详情:\n")
                for key, value in entry['log_info'].items():
                    if key != 'full_text':  # 跳过完整文本以避免重复
                        f.write(f"  {key}: {value}\n")
                f.write("\n")
                
                # 输出源码匹配结果
                f.write("源码匹配结果:\n")
                for match_group in entry['source_matches']:
                    f.write(f"\n【{match_group['type']}】(相关性: {match_group['relevance']})\n")
                    
                    if isinstance(match_group['matches'], list):
                        for idx, match in enumerate(match_group['matches'], 1):
                            f.write(f"  匹配 #{idx}:\n")
                            f.write(f"    文件: {match['file']}\n")
                            if 'line_number' in match:
                                f.write(f"    行号: {match['line_number']}\n")
                            if 'match_type' in match:
                                f.write(f"    匹配类型: {match['match_type']}\n")
                            if 'content' in match:
                                f.write(f"    内容: {match['content']}\n")
                            if 'context' in match and match['context']:
                                f.write("    上下文:\n")
                                for ctx_line in match['context']:
                                    f.write(f"      {ctx_line}\n")
                            f.write("\n")
                    else:
                        # 单个匹配对象
                        match = match_group['matches']
                        f.write(f"    文件: {match['file']}\n")
                        if 'line_number' in match:
                            f.write(f"    行号: {match['line_number']}\n")
                        if 'match_type' in match:
                            f.write(f"    匹配类型: {match['match_type']}\n")
                        if 'log_statement' in match:
                            f.write(f"    日志语句: {match['log_statement']}\n")
                        if 'context' in match and match['context']:
                            f.write("    上下文:\n")
                            for ctx_line in match['context']:
                                f.write(f"      {ctx_line}\n")
                
                f.write("\n" + "=" * 80 + "\n\n")
        
        print(f"日志到源码的映射已完成。结果保存在 {output_file}")
        
    except Exception as e:
        print(f"保存结果时出错: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    args = parse_arguments()
    results = analyze_logs(args.log, args.source, args.cache, args.verbose)
    save_results(results, args.output)
