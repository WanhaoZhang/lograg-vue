# 使用官方的 Python 3.8 slim 镜像作为基础镜像
FROM python:3.8-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    pkg-config \
    libhdf5-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制 LogRAG 项目文件
COPY LogRAG/ /app/LogRAG/

# 安装项目依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r LogRAG/requirements.txt

# 设置工作目录
WORKDIR /app/LogRAG

# 设置默认命令
CMD ["python", "main.py"]
