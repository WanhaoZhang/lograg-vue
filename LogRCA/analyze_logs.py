import os
import json
import time
import argparse
from openai import OpenAI
import yaml

# 读取配置文件
def load_config(config_path="config.yaml"):
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config

# 配置OpenAI客户端
class GPTAnalyzer:
    def __init__(self, api_base=None, api_key=None, model=None, config=None):
        if config is None:
            config = load_config()
        
        self.api_base = api_base or config['api']['openai']['api_base']
        self.api_key = api_key or config['api']['openai']['api_key']
        self.model = model or config['api']['openai']['default_model']
        self.client = OpenAI(
            base_url=self.api_base,
            api_key=self.api_key,
        )
    
    def ask_chatgpt(self, prompt_content):
        """
        使用ChatGPT分析异常日志
        """
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user", 
                        "content": prompt_content
                    }
                ],
                model=self.model,
                temperature=0,
            )
            content = chat_completion.choices[0].message.content
            return content
        except Exception as e:
            print(f"请求ChatGPT API时出错: {e}")
            return None

def generate_prompt(anomaly_data):
    """
    根据异常日志数据生成提示
    """
    anomaly_log = anomaly_data["anomaly_log"]
    
    # 准备异常日志文本
    log_text = anomaly_log["text"]
    
    # 准备上下文信息
    context_before = "\n".join([log["text"] for log in anomaly_data.get("context_before", [])])
    context_after = "\n".join([log["text"] for log in anomaly_data.get("context_after", [])])
    
    # 准备源码片段
    code_context = anomaly_log.get("code_context", {})
    source_code = ""
    if code_context and "context" in code_context:
        file_path = code_context.get("file", "未知文件")
        source_code = f"文件路径: {file_path}\n"
        source_code += "\n".join([f"{line['line_number']}: {line['content']}" for line in code_context["context"]])
    
    # 生成完整提示
    prompt = f"""指令：你是一名经验丰富的软件工程师。你的任务是分析异常日志、上下文
信息及源码，找出异常发生的原因，并生成格式化分析报告。输入：
•异常日志:
{log_text}

• 上下文信息:
--- 之前的日志 ---
{context_before}

--- 之后的日志 ---
{context_after}

•源码片段:
{source_code}

异常分析报告输出格式：
1.异常概述
- 异常类型：｛异常类型｝
- 异常信息：｛错误消息｝
2.详细分析
- 可能的异常原因：
-｛基于日志、上下文和源码的推断｝
- 影响范围：
-｛异常可能影响的系统组件｝
3. 解决方案建议
- 短期修复：｛快速缓解措施｝
- 长期优化：｛提升代码健壮性的方案｝
"""
    return prompt

def parse_args():
    """
    解析命令行参数
    """
    config = load_config()
    default_api_key = config['api']['openai']['api_key']
    default_api_base = config['api']['openai']['api_base']
    default_model = config['api']['openai']['default_model']
    
    parser = argparse.ArgumentParser(description='分析异常日志并生成报告')
    parser.add_argument('--api-key', type=str, 
                        default=default_api_key, 
                        help='OpenAI API密钥')
    parser.add_argument('--api-base', type=str, 
                        default=default_api_base, 
                        help='OpenAI API基础URL')
    parser.add_argument('--model', type=str, 
                        default=default_model, 
                        help='使用的模型名称')
    parser.add_argument('--input', type=str, 
                        help='输入JSON文件路径，默认为output/code_context.json')
    parser.add_argument('--output', type=str, 
                        help='输出JSON文件路径，默认为output/log_analysis_report.json')
    parser.add_argument('--config', type=str,
                        default='config.yaml',
                        help='配置文件路径')
    return parser.parse_args()

def main():
    # 解析命令行参数
    args = parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 配置
    api_base = args.api_base
    api_key = args.api_key
    model = args.model
    
    # 设置输入输出文件路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_config = config['output']
    input_file = args.input or os.path.join(current_dir, output_config['output_dir'], output_config['code_context_file'])
    output_file = args.output or os.path.join(current_dir, output_config['output_dir'], output_config['analysis_report_file'])
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    print(f"使用API基础URL: {api_base}")
    print(f"使用模型: {model}")
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    
    # 初始化GPT分析器
    analyzer = GPTAnalyzer(api_base, api_key, model, config)
    
    try:
        # 读取code_context.json
        print(f"正在读取文件: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            anomaly_data_list = json.load(f)
        
        print(f"共读取到 {len(anomaly_data_list)} 条异常记录")
        analysis_results = []
        
        # 获取最大处理的日志数量
        max_logs = config['log_analysis']['max_logs']
        
        # 处理每个异常日志
        for i, anomaly_data in enumerate(anomaly_data_list):
            print(f"处理第 {i+1}/{len(anomaly_data_list)} 条异常日志...")
            if i > max_logs:
                break
            
            try:
                # 生成提示
                prompt = generate_prompt(anomaly_data)
                
                # 发送到ChatGPT
                print(f"正在发送请求到ChatGPT...")
                analysis = analyzer.ask_chatgpt(prompt)
                
                if analysis:
                    # 保存分析结果
                    result = {
                        "vm_id": anomaly_data.get("vm_id", "unknown"),
                        "anomaly_log": anomaly_data["anomaly_log"]["text"],
                        "analysis": analysis
                    }
                    analysis_results.append(result)
                    
                    # 保存中间结果，以防程序中断
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(analysis_results, f, ensure_ascii=False, indent=2)
                    
                    print(f"已保存第 {i+1} 条分析结果")
                    
                    # 避免API限制
                    time.sleep(1)
                else:
                    print(f"无法获取第 {i+1} 条异常日志的分析结果")
            except Exception as e:
                print(f"处理第 {i+1} 条异常日志时出错: {e}")
                # 继续处理下一条
                continue
        
        print(f"分析完成！结果已保存到 {output_file}")
        
    except FileNotFoundError:
        print(f"错误: 找不到文件 {input_file}")
    except json.JSONDecodeError:
        print(f"错误: {input_file} 不是有效的JSON文件")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    main() 