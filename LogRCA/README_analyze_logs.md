# 异常日志分析工具

这个工具用于分析异常日志，基于GPT模型生成详细的分析报告。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 用法

基本用法：

```bash
python3 analyze_logs.py
```

脚本默认使用以下配置：
- API基础URL: https://api.openai-proxy.org/v1
- API密钥: sk-IXv5inyh4jRh9ae8bRFbuZ1NDpQVXcTgjnUJW024Mn93JTsx
- 模型: gpt-4o-mini

所有可用选项：

```
usage: analyze_logs.py [-h] [--api-key API_KEY] [--api-base API_BASE]
                       [--model MODEL] [--input INPUT] [--output OUTPUT]

分析异常日志并生成报告

options:
  -h, --help           显示帮助信息并退出
  --api-key API_KEY    OpenAI API密钥，默认已设置
  --api-base API_BASE  OpenAI API基础URL，默认为 https://api.openai-proxy.org/v1
  --model MODEL        使用的模型名称，默认为 gpt-4o-mini
  --input INPUT        输入JSON文件路径，默认为 output/code_context.json
  --output OUTPUT      输出JSON文件路径，默认为 output/log_analysis_report.json
```

## 自定义设置

如果需要使用不同的API密钥或基础URL，可以通过命令行参数指定：

```bash
python3 analyze_logs.py --api-key YOUR_API_KEY --api-base YOUR_API_BASE --model MODEL_NAME
```

## 模型支持

默认使用gpt-4o-mini模型，但可以支持其他兼容模型，例如：
- gpt-3.5-turbo
- gpt-4
- deepseek-reasoner
- 其他兼容的模型

## 输出结果

脚本会生成一个JSON文件，包含每个异常日志的分析结果。分析结果包括：

1. 异常概述
   - 异常类型
   - 异常信息
2. 详细分析
   - 可能的异常原因
   - 影响范围
3. 解决方案建议
   - 短期修复
   - 长期优化 