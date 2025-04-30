# LogRCA Docker 使用指南

本指南说明如何使用Docker容器运行LogRCA日志分析工具。

## 前提条件

- 安装 [Docker](https://www.docker.com/get-started)
- 安装 [Docker Compose](https://docs.docker.com/compose/install/) (通常随Docker一起安装)

## 使用方法

### 1. 准备数据

将您的`code_context.json`文件放入`output`目录：

```bash
cp 您的code_context.json文件路径 output/code_context.json
```

### 2. 使用Docker Compose构建并运行

```bash
# 构建并启动容器
docker-compose up --build
```

这将自动执行以下操作：
- 构建Docker镜像
- 运行分析脚本
- 分析结果将保存在`output/log_analysis_report.json`

### 3. 只构建镜像

```bash
docker-compose build
```

### 4. 自定义运行参数

如果需要更改默认参数（如API密钥或模型），可以编辑`docker-compose.yml`文件或直接运行容器：

```bash
docker run --rm -v $(pwd)/output:/app/output logrca_logrca --api-key YOUR_API_KEY --model MODEL_NAME
```

## 目录挂载

默认设置下，容器将挂载以下目录：
- `./output:/app/output`：分析输入和输出文件的目录

## 故障排除

1. **权限问题**：如果遇到权限错误，请确保output目录具有正确的读写权限：
   ```bash
   chmod -R 777 output
   ```

2. **找不到文件**：确保`code_context.json`文件已正确放置在output目录中

3. **API错误**：检查是否正确设置了API密钥和基础URL

## 其他命令

查看日志：
```bash
docker-compose logs
```

停止容器：
```bash
docker-compose down
``` 