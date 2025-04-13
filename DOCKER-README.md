# Docker 使用说明

本项目已配置为使用 Docker 容器化运行，包括前端、后端和 MongoDB 数据库。

## 前提条件

- 安装 [Docker](https://www.docker.com/get-started)
- 安装 [Docker Compose](https://docs.docker.com/compose/install/)

## 运行项目

1. 在项目根目录下运行以下命令启动所有服务:

```bash
docker-compose up
```

2. 如需在后台运行:

```bash
docker-compose up -d
```

3. 访问应用:
   - 前端: http://localhost:8080
   - 后端 API: http://localhost:3000/api

## 停止项目

```bash
docker-compose down
```

如需同时删除卷(包括数据库数据):

```bash
docker-compose down -v
```

## 服务说明

- **frontend**: 前端 Vue 应用，运行在 8080 端口
- **backend**: 后端 Node.js API，运行在 3000 端口
- **mongodb**: MongoDB 数据库，运行在 27017 端口

## 重新构建

如果修改了代码，需要重新构建:

```bash
docker-compose build
docker-compose up
```

## 故障排除

- 检查日志: `docker-compose logs -f [服务名]`
- 进入容器: `docker-compose exec [服务名] sh` 