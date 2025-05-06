FROM python:3.9-slim

WORKDIR /app

# 安装node.js和npm以支持导入脚本
RUN apt-get update && apt-get install -y nodejs npm \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 安装cnpm
RUN npm install -g cnpm --registry=https://registry.npmmirror.com

# 复制依赖文件并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制所有项目文件
COPY . .

# 创建输出目录
RUN mkdir -p output

# 安装导入脚本所需的npm包
RUN cnpm init -y && cnpm install mongodb

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV MONGODB_URI=mongodb://mongodb:27017/loganalysis

# 创建启动脚本
RUN echo '#!/bin/bash\n\
echo "步骤1: 提取异常日志上下文"\n\
python extract_anomaly_context.py\n\
echo "步骤2: 查找代码上下文"\n\
python find_code_context.py\n\
echo "步骤3: 分析日志并生成报告"\n\
python analyze_logs.py "$@"\n\
echo "步骤4: 导入分析结果到MongoDB"\n\
node import_logs.js\n\
echo "处理完成！"\n\
' > /app/run_pipeline.sh

# 为启动脚本添加执行权限
RUN chmod +x /app/run_pipeline.sh

# 设置入口点
ENTRYPOINT ["/app/run_pipeline.sh"] 