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
  }],
  // 添加原始分析文本，用于显示完整的分析结果
  rawText: String
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
  // 添加vm_id字段，用于关联LogRCA分析结果
  vm_id: {
    type: String,
    index: true
  },
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
logSchema.index({ vm_id: 1 });

const Log = mongoose.model('Log', logSchema);

module.exports = Log; 