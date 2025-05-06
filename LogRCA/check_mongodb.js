/**
 * 检查MongoDB中是否有LogRCA导入的数据
 * 如果没有，则手动导入数据
 */
const mongoose = require('mongoose');
const fs = require('fs');
const path = require('path');

// 定义Log模型（与import_to_mongodb.js中的定义相同）
const logSchema = new mongoose.Schema({
  timestamp: {
    type: Date,
    required: true,
    default: Date.now
  },
  service: {
    type: String,
    required: true,
    index: true
  },
  level: {
    type: String,
    required: true,
    enum: ['ERROR', 'WARN', 'INFO', 'CRITICAL', 'DEBUG'],
    index: true
  },
  message: {
    type: String,
    required: true
  },
  stackTrace: String,
  summary: String,
  analysis: {
    summary: String,
    rootCauses: [{
      title: String,
      description: String
    }],
    solutions: [{
      type: String,
      description: String
    }]
  },
  metadata: {
    type: mongoose.Schema.Types.Mixed,
    default: {}
  }
}, {
  timestamps: true
});

// 添加索引
logSchema.index({ timestamp: -1 });
logSchema.index({ service: 1, timestamp: -1 });
logSchema.index({ level: 1, timestamp: -1 });

// 创建模型
const Log = mongoose.model('Log', logSchema);

async function checkAndImportData() {
  try {
    // 连接到MongoDB
    const mongoUri = process.env.MONGODB_URI || 'mongodb://localhost:27017/loganalysis';
    console.log(`正在连接到MongoDB: ${mongoUri}`);
    await mongoose.connect(mongoUri);
    console.log('已连接到MongoDB');
    
    // 检查是否有LogRCA导入的数据
    const count = await Log.countDocuments({ service: 'test' });
    console.log(`MongoDB中有 ${count} 条LogRCA数据`);
    
    if (count === 0) {
      console.log('未发现LogRCA数据，开始手动导入...');
      
      // 导入数据
      await require('./import_to_mongodb.js');
    } else {
      console.log('发现LogRCA数据，无需导入');
      
      // 列出所有服务
      const services = await Log.distinct('service');
      console.log('所有可用服务:', services);
      
      // 断开连接
      await mongoose.disconnect();
      console.log('已断开MongoDB连接');
    }
  } catch (error) {
    console.error('检查或导入数据失败:', error);
  }
}

// 执行检查
checkAndImportData(); 