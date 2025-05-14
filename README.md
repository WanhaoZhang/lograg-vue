[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/WanhaoZhang/lograg-vue)
# 日志异常检测与分析平台

一个用于检测和分析系统日志异常的综合平台，集成了多种先进的日志分析技术，包括日志根因分析(LogRCA)和基于检索增强生成的日志异常检测(LogRAG)。本平台提供直观的前端可视化界面和强大的后端API服务，帮助开发人员和运维人员快速定位和解决系统问题。

## 项目概述

本平台主要面向大规模系统（如OpenStack）的日志分析，具有以下特点：

- **多技术集成**：结合传统分析方法与先进的人工智能技术
- **全流程支持**：从日志收集、异常检测到根因分析的完整解决方案
- **可视化展示**：直观呈现分析结果，提升用户体验
- **可扩展架构**：模块化设计，便于扩展和定制

## 系统架构

该项目由以下主要模块组成：

```
.
├── frontend/              # 前端Vue项目
│   ├── src/               # 源代码
│   │   ├── api/           # API接口
│   │   ├── components/    # Vue组件
│   │   ├── mock/          # 模拟数据
│   │   ├── utils/         # 工具函数
│   │   ├── views/         # 页面视图
│   │   ├── App.vue        # 主应用组件
│   │   └── main.js        # 入口文件
│   ├── public/            # 静态资源
│   ├── index.html         # HTML模板
│   ├── package.json       # 依赖配置
│   └── vite.config.js     # Vite配置
│
├── backend/               # 后端Node.js项目
│   ├── src/               # 源代码
│   │   ├── models/        # 数据模型
│   │   ├── routes/        # API路由
│   │   ├── utils/         # 工具函数
│   │   └── index.js       # 入口文件
│   └── package.json       # 依赖配置
│
├── LogRCA/                # 日志根因分析模块
│   ├── extract_anomaly_context.py    # 异常日志提取
│   ├── find_code_context.py          # 代码上下文查找
│   ├── analyze_logs.py               # 日志分析与报告生成
│   ├── OpenStack/                    # OpenStack日志数据
│   ├── nova-13.0.0/                  # OpenStack Nova源码
│   └── output/                       # 分析结果输出
│
├── LogRAG/                # 基于RAG的日志异常检测模块
│   ├── main.py            # 主程序入口
│   ├── config.yaml        # 配置文件
│   ├── prelogad/          # 异常检测预处理
│   ├── postprocess/       # RAG后处理
│   ├── pretrained/        # 预训练模型
│   ├── dataset/           # 训练和测试数据集
│   └── output/            # 结果输出
│
├── docker-compose.yml或compose.yaml     # Docker Compose配置
├── Dockerfile             # Docker配置
└── import_*.js            # 数据导入工具
```

## 核心技术栈

- **前端**：
  - Vue 3：现代化的响应式前端框架
  - Element Plus：美观的UI组件库
  - Axios：HTTP客户端
  - Vite：高效的构建工具

- **后端**：
  - Node.js：高性能JavaScript运行时
  - Express：Web应用框架
  - MongoDB：NoSQL数据库
  - Mongoose：MongoDB对象模型工具

- **分析引擎**：
  - Python：主要分析脚本语言
  - 大型语言模型(LLM)：用于智能分析
  - RAG (检索增强生成)：增强异常检测准确率
  - DeepSVDD：半监督异常检测算法

## 功能特性

### 1. 日志处理与存储

- 多源日志采集与统一规范化处理
- 高效存储与索引方案
- 日志数据流水线处理

### 2. 异常检测

- 基于DeepSVDD的半监督学习异常检测
- 日志序列与模板双阶段检测
- RAG增强的异常检测准确率提升

### 3. 根因分析

- 异常日志上下文提取
- 源码与日志映射关联
- 基于LLM的智能根因分析

### 4. 可视化与交互

- 日志数据多维度可视化展示
- 复杂条件过滤与智能搜索
- 异常聚类与趋势分析
- 可交互的根因分析报告

## 快速开始

### 环境要求

- Docker 和 Docker Compose（推荐使用容器化部署）
- 或满足以下条件的本地环境：
  - Node.js >= 14
  - Python >= 3.8
  - MongoDB >= 4.0
  - NVIDIA GPU + CUDA（用于加速模型推理，可选）

### 使用Docker运行（推荐）

1. 克隆仓库
   ```bash
   git clone <仓库URL>
   cd <项目目录>
   ```

2. 使用Docker Compose启动所有服务
   ```bash
   # 构建项目
   docker build
   # 构建并启动所有服务（前台运行，可以看到日志输出）
   docker compose up
   
   # 或者在后台运行
   docker compose up -d
   ```

   > **注意**: 以上命令将一次性启动所有服务，包括前端、后端、MongoDB数据库、LogRCA和LogRAG模块。

3. 查看服务状态
   ```bash
   # 查看所有运行中的容器
   docker compose ps
   
   # 查看特定服务的日志
   docker compose logs -f frontend
   docker compose logs -f backend
   docker compose logs -f logrca
   docker compose logs -f lograg
   ```

4. 访问应用
   - 前端界面：http://localhost:8080
   - 后端API：http://localhost:3000/api
   - LogRAG API（如适用）：http://localhost:8000

5. 数据导入（首次启动时需要）
   ```bash
   # 进入后端容器
   docker compose exec backend sh
   
   # 运行数据导入脚本
   node import_logs.js
   ```

6. 停止服务
   ```bash
   # 停止所有服务但保留数据
   docker compose down
   
   # 停止所有服务并删除数据卷（会清除数据库数据）
   docker compose down -v
   ```

7. 常见问题解决
   - **服务启动失败**：检查各个服务的日志 `docker compose logs -f <服务名>`
   - **端口冲突**：如果8080、3000或27017端口已被占用，可以在compose.yaml中修改相应端口映射
   - **LogRCA模块连接MongoDB失败**：确保在启动前MongoDB服务已正常运行
   - **API密钥配置**：LogRCA模块需要配置API密钥，可在compose.yaml中修改相应环境变量
   - **修改配置后重新构建**：
     ```bash
     docker compose build
     docker compose up -d
     ```

8. 高级配置
   - **调整LogRAG配置**：修改`LogRAG/config.yaml`文件后重新构建并启动LogRAG容器
   - **修改API地址**：前端服务默认连接到`http://backend:3000`，如需修改，可在compose.yaml中调整`VITE_API_BASE_URL`环境变量
   - **持久化数据**：MongoDB数据存储在名为`mongodb_data`的Docker卷中，分析结果输出存储在各个服务的挂载卷中

### 本地运行

1. 安装后端依赖并启动
   ```bash
   cd backend
   npm install
   npm run dev
   ```

2. 安装前端依赖并启动
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. 设置分析模块（LogRCA & LogRAG）
   
   LogRCA:
   ```bash
   cd LogRCA
   pip install -r requirements.txt
   python analyze_logs.py
   ```
   
   LogRAG:
   ```bash
   cd LogRAG
   pip install -r requirements.txt
   python main.py
   ```

### 数据导入

使用提供的脚本导入示例日志数据：

```bash
node import_logs.js
# 或导入OpenStack日志
python import_openstack_logs.py
```

## 配置说明

### LogRAG配置（config.yaml）

主要配置项：
- `is_train`: 是否训练DeepOC模块
- `is_rag`: 是否启用RAG后处理
- `window_size`: 窗口大小
- `window_time`: 时间窗口（秒）
- `llm_name`: 使用的语言模型（如gpt-3.5-turbo或本地Mistral模型）

### API密钥配置

在使用GPT等云端模型时，需要在相应配置文件中设置API密钥：
- LogRAG: 在`config.yaml`中设置`api_key`字段
- LogRCA: 在脚本参数或环境变量中配置

## API文档

### 日志数据API

```
GET /api/logs                # 获取日志列表
GET /api/logs/:id            # 获取日志详情
GET /api/logs/:id/analysis   # 获取日志分析
POST /api/logs               # 创建日志
```

### 分析结果API

```
GET /api/analysis            # 获取分析结果列表
GET /api/analysis/:id        # 获取特定分析详情
GET /api/anomalies           # 获取异常列表
GET /api/stats               # 获取统计数据
```

## 高级用法

### 自定义模型

本平台支持替换或集成自定义模型：

1. 在LogRAG中替换预训练模型
2. 添加新的分析算法到LogRCA
3. 扩展后端API以支持新的分析方法

### 集成外部系统

提供多种集成方式：

- REST API接口
- 数据导入/导出工具
- 消息队列连接（计划中）

## 故障排除

- **Docker相关问题**：查看容器日志 `docker compose logs -f [服务名]`
- **模型加载错误**：检查预训练模型路径和权限
- **API连接问题**：验证网络设置和防火墙配置

## 贡献指南

欢迎贡献代码或提出建议：

1. Fork本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## 许可证

MIT

## 致谢

- [LogHub](https://github.com/logpai/loghub)提供的开源日志数据集
- [BigLog](https://github.com/LogAIBox/BigLog)提供的预训练模型
- OpenStack社区提供的系统和日志示例 
