# LogRCA - 日志根因分析工具

LogRCA是一个用于分析异常日志、查找相关代码上下文并生成分析报告的工具。该工具专为OpenStack等大型系统设计，可以帮助开发人员和运维人员快速定位和解决问题。

## 功能特点

1. **异常日志提取**：从大量日志中提取相关的异常日志及其上下文
2. **代码映射**：将日志与相应的源代码关联起来
3. **智能分析**：使用GPT模型分析异常日志并生成根因分析报告

## 项目结构

- `extract_anomaly_context.py`: 从日志文件中提取异常日志及其上下文
- `find_code_context.py`: 查找与日志相关的代码上下文
- `analyze_logs.py`: 使用GPT模型分析日志并生成报告
- `config.yaml`: 集中管理所有配置信息
- `import_to_mongodb.js`: 将分析结果导入到MongoDB
- `OpenStack/`: 包含OpenStack日志数据
- `nova-13.0.0/`: 包含OpenStack Nova项目源代码
- `output/`: 存放处理结果

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

项目使用 `config.yaml` 作为主要配置文件，其中包含以下配置项：

### API配置

```yaml
api:
  # OpenAI API配置
  openai:
    api_key: "YOUR_API_KEY"  # API密钥
    api_base: "https://api.openai.com/v1"  # API基础URL
    default_model: "gpt-4o-mini"  # 默认模型
    alternative_models:  # 替代模型
      - "gpt-3.5-turbo"
      - "gpt-4"
      - "gpt-4o"
```

### 环境变量配置

除了配置文件，您还可以使用环境变量来覆盖配置文件中的设置。
创建一个 `.env` 文件（可以从 `env.example` 复制），包含以下内容：

```
# OpenAI API配置
OPENAI_API_KEY=your-api-key
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# MongoDB配置
MONGODB_URI=mongodb://mongodb:27017/loganalysis
```

## 使用方法

### 本地运行

完整的处理流程：

```bash
# 步骤1: 提取异常日志上下文
python extract_anomaly_context.py

# 步骤2: 查找代码上下文
python find_code_context.py

# 步骤3: 分析日志并生成报告
python analyze_logs.py

# 步骤4: 导入分析结果到MongoDB（可选）
node import_to_mongodb.js
```

### 使用Docker运行

#### 前提条件

- Docker和Docker Compose已安装
- OpenStack日志文件和源代码已准备就绪

#### 构建和运行

1. 克隆代码库：

```bash
git clone <repository-url>
cd LogRCA
```

2. 使用Docker Compose构建和运行：

```bash
docker-compose up --build
```

这将按顺序执行处理流程中的所有步骤。

#### 自定义运行参数

如果需要更改默认参数（如API密钥或模型），可以编辑`.env`文件或直接使用环境变量：

```bash
OPENAI_API_KEY=your-new-api-key docker-compose up logrca
```

### 命令行选项

`analyze_logs.py` 脚本支持以下命令行选项：

```
usage: analyze_logs.py [-h] [--api-key API_KEY] [--api-base API_BASE]
                       [--model MODEL] [--input INPUT] [--output OUTPUT]
                       [--config CONFIG]

分析异常日志并生成报告

options:
  -h, --help           显示帮助信息并退出
  --api-key API_KEY    OpenAI API密钥
  --api-base API_BASE  OpenAI API基础URL
  --model MODEL        使用的模型名称
  --input INPUT        输入JSON文件路径
  --output OUTPUT      输出JSON文件路径
  --config CONFIG      配置文件路径
```

其他脚本也支持类似的命令行参数。

## 处理结果

所有处理结果将保存在`output/`目录中：
- `anomaly_context.json`：包含异常日志及其上下文
- `code_context.json`：包含日志与代码的映射关系
- `log_analysis_report.json`：包含最终的分析报告

## 如何安全使用API密钥

1. **不要提交API密钥到版本控制系统**：
   - 我们已经在 `.gitignore` 中添加了 `.env` 文件，确保您的API密钥不会被意外提交。

2. **使用环境变量**：
   - 优先使用环境变量来传递API密钥，而不是硬编码在配置文件中。

3. **注意API密钥泄露**：
   - 如果您怀疑API密钥已泄露，请立即轮换它。

## 故障排除

1. **权限问题**：如果遇到权限错误，请确保output目录具有正确的读写权限：
   ```bash
   chmod -R 777 output
   ```

2. **找不到文件**：确保必要的日志文件和源代码文件已正确放置在相应目录中

3. **API错误**：检查是否正确设置了API密钥和基础URL 