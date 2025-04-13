const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
const mongoose = require('mongoose');
const { logsRouter } = require('./routes/logs');
const seedLogs = require('./utils/seedData');

// 创建Express应用
const app = express();
const PORT = process.env.PORT || 3000;

// 中间件
app.use(cors());
app.use(express.json());
app.use(morgan('dev'));

// 连接数据库
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/log-analysis')
  .then(async () => {
    console.log('MongoDB连接成功');
    
    // 初始化种子数据
    await seedLogs();
  })
  .catch(err => {
    console.error('MongoDB连接失败:', err);
  });

// 路由
app.use('/api/logs', logsRouter);

// 错误处理中间件
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({
    message: '服务器内部错误',
    error: process.env.NODE_ENV === 'development' ? err.message : undefined
  });
});

// 启动服务器
app.listen(PORT, () => {
  console.log(`服务器运行在端口 ${PORT}`);
}); 