const mongoose = require('mongoose');

// 日志分析数据模型
const logAnalysisSchema = new mongoose.Schema({
  summary: String,
  rootCauses: [{
    title: String,
    description: String
  }],
  solutions: [{
    type: String,  // 'shortTerm' 或 'longTerm'
    description: String
  }]
});

// 日志数据模型
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
  analysis: logAnalysisSchema,
  metadata: {
    type: mongoose.Schema.Types.Mixed,
    default: {}
  }
}, {
  timestamps: true
});

// 添加索引以优化查询
logSchema.index({ timestamp: -1 });
logSchema.index({ service: 1, timestamp: -1 });
logSchema.index({ level: 1, timestamp: -1 });

const Log = mongoose.model('Log', logSchema);

module.exports = Log; 