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
- `OpenStack/`: 包含OpenStack日志数据
- `nova-13.0.0/`: 包含OpenStack Nova项目源代码
- `output/`: 存放处理结果

## 使用Docker运行

### 前提条件

- Docker和Docker Compose已安装
- OpenStack日志文件和源代码已准备就绪

### 构建和运行

1. 克隆代码库：

```bash
git clone <repository-url>
cd LogRCA
```

2. 使用Docker Compose构建和运行：

```bash
docker-compose up --build
```

这将按顺序执行以下步骤：
- 提取异常日志上下文（`extract_anomaly_context.py`）
- 查找代码上下文（`find_code_context.py`）
- 分析日志并生成报告（`analyze_logs.py`）

### 处理结果

所有处理结果将保存在`output/`目录中：
- `anomaly_context.json`：包含异常日志及其上下文
- `code_context.json`：包含日志与代码的映射关系
- `log_analysis_report.json`：包含最终的分析报告

## 自定义配置

如需自定义API密钥或其他参数，可以编辑`docker-compose.yml`文件中的`command`部分。

## 注意事项

- 确保`OpenStack/`目录中包含必要的日志文件（`openstack_abnormal.log`和`anomaly_labels.txt`）
- 确保`nova-13.0.0/`目录包含完整的OpenStack Nova源代码 