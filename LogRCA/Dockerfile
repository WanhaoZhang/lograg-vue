FROM python:3.9-slim

WORKDIR /app

# 复制依赖文件并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制所有项目文件
COPY . .

# 创建输出目录
RUN mkdir -p output

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 创建启动脚本
RUN echo '#!/bin/bash\n\
echo "步骤1: 提取异常日志上下文"\n\
python extract_anomaly_context.py\n\
echo "步骤2: 查找代码上下文"\n\
python find_code_context.py\n\
echo "步骤3: 分析日志并生成报告"\n\
python analyze_logs.py "$@"\n\
echo "处理完成！"\n\
' > /app/run_pipeline.sh

# 为启动脚本添加执行权限
RUN chmod +x /app/run_pipeline.sh

# 设置入口点
ENTRYPOINT ["/app/run_pipeline.sh"] 