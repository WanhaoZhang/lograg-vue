# 日志异常检测与分析平台

一个用于检测和分析系统日志异常的平台，包括前端可视化界面和后端API服务。

## 项目结构

```
.
├── frontend/            # 前端Vue项目
│   ├── src/             # 源代码
│   │   ├── api/         # API接口
│   │   ├── components/  # Vue组件
│   │   ├── mock/        # 模拟数据
│   │   ├── utils/       # 工具函数
│   │   ├── views/       # 页面视图
│   │   ├── App.vue      # 主应用组件
│   │   └── main.js      # 入口文件
│   ├── public/          # 静态资源
│   ├── index.html       # HTML模板
│   ├── package.json     # 依赖配置
│   └── vite.config.js   # Vite配置
│
├── backend/             # 后端Node.js项目
│   ├── src/             # 源代码
│   │   ├── models/      # 数据模型
│   │   ├── routes/      # API路由
│   │   ├── utils/       # 工具函数
│   │   └── index.js     # 入口文件
│   └── package.json     # 依赖配置
│
└── start.sh             # 启动脚本
```

## 技术栈

- 前端：Vue 3、Element Plus、Axios、Vite
- 后端：Node.js、Express、MongoDB、Mongoose

## 功能特性

- 日志数据可视化展示
- 多维度日志过滤和搜索
- 异常日志智能分析
- RESTful API接口
- 响应式设计，适应不同屏幕尺寸

## 快速开始

### 前提条件

- Node.js >= 14
- MongoDB >= 4.0
- npm 或 yarn

### 安装与运行

1. 克隆仓库
   ```bash
   git clone <仓库URL>
   cd <项目目录>
   ```

2. 使用启动脚本运行项目
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

   或者分别启动前后端：

   后端：
   ```bash
   cd backend
   npm install
   npm run dev
   ```

   前端：
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. 在浏览器中访问：
   - 前端：http://localhost:8080
   - 后端API：http://localhost:3000/api

## API文档

### 获取日志列表

```
GET /api/logs
```

参数：
- `service`: 服务名称
- `level`: 日志级别
- `startTime`: 开始时间
- `endTime`: 结束时间
- `page`: 页码
- `pageSize`: 每页数量

### 获取日志详情

```
GET /api/logs/:id
```

### 获取日志分析

```
GET /api/logs/:id/analysis
```

### 创建日志

```
POST /api/logs
```

请求体：
```json
{
  "timestamp": "2023-12-01T10:00:00Z",
  "service": "service-name",
  "level": "ERROR",
  "message": "错误信息",
  "stackTrace": "堆栈信息"
}
```

## 许可证

MIT 