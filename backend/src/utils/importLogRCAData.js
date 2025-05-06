const fs = require('fs');
const path = require('path');
const mongoose = require('mongoose');
const Log = require('../models/Log');

/**
 * 解析LogRCA的分析报告并转换为MongoDB数据格式
 * @param {Object} logEntry LogRCA的分析报告条目
 * @returns {Object} 符合MongoDB模型的数据对象
 */
function parseLogRCAEntry(logEntry) {
  // 解析异常日志信息
  const logParts = logEntry.anomaly_log.split(' ', 4);
  
  // 尝试从日志中提取日期和时间
  let timestamp;
  const timestampMatch = logEntry.anomaly_log.match(/\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/);
  if (timestampMatch) {
    timestamp = new Date(timestampMatch[0]);
  } else {
    timestamp = new Date(); // 如果无法从日志中提取，使用当前时间
  }
  
  // 提取日志级别
  let level = 'ERROR'; // 默认为ERROR
  if (logEntry.anomaly_log.includes(' INFO ')) {
    level = 'INFO';
  } else if (logEntry.anomaly_log.includes(' WARN ')) {
    level = 'WARN';
  } else if (logEntry.anomaly_log.includes(' DEBUG ')) {
    level = 'DEBUG';
  } else if (logEntry.anomaly_log.includes(' CRITICAL ')) {
    level = 'CRITICAL';
  }
  
  // 提取服务名称
  const serviceMatch = logEntry.anomaly_log.match(/nova-[a-zA-Z]+/);
  const service = serviceMatch ? serviceMatch[0] : 'test';
  
  // 提取日志消息 - 通常是日志行的剩余部分
  const messageStartIndex = logEntry.anomaly_log.indexOf('] ');
  const message = messageStartIndex !== -1 
    ? logEntry.anomaly_log.substring(messageStartIndex + 2) 
    : logEntry.anomaly_log;
  
  // 解析分析内容
  let analysis = null;
  if (logEntry.analysis) {
    const analysisLines = logEntry.analysis.split('\n');
    let summary = '';
    const rootCauses = [];
    const solutions = [];
    
    // 尝试提取概述、原因和解决方案
    let section = '';
    for (const line of analysisLines) {
      if (line.includes('异常概述')) {
        section = 'summary';
      } else if (line.includes('详细分析') || line.includes('可能的异常原因')) {
        section = 'causes';
      } else if (line.includes('解决方案建议')) {
        section = 'solutions';
      } else if (line.startsWith('- ') || line.startsWith('  -')) {
        if (section === 'summary' && !summary) {
          summary = line.replace(/^- |^  - /, '').replace(/^[\*\*](.+)[\*\*]：/, '$1:');
        } else if (section === 'causes') {
          const cause = line.replace(/^- |^  - /, '').replace(/^[\*\*](.+)[\*\*]：/, '$1:');
          if (cause.trim()) {
            rootCauses.push({
              title: '异常原因',
              description: cause
            });
          }
        } else if (section === 'solutions') {
          const solution = line.replace(/^- |^  - /, '').replace(/^[\*\*](.+)[\*\*]：/, '$1:');
          if (solution.trim()) {
            if (solution.includes('短期') || line.includes('短期')) {
              solutions.push({
                type: 'shortTerm',
                description: solution
              });
            } else if (solution.includes('长期') || line.includes('长期')) {
              solutions.push({
                type: 'longTerm',
                description: solution
              });
            } else {
              solutions.push({
                type: 'general',
                description: solution
              });
            }
          }
        }
      }
    }
    
    // 如果没有成功提取到概述，使用第一行作为概述
    if (!summary && analysisLines.length > 0) {
      summary = analysisLines[0].replace('# ', '');
    }
    
    analysis = {
      summary: summary,
      rootCauses: rootCauses,
      solutions: solutions
    };
  }
  
  return {
    timestamp,
    service,
    level,
    message,
    stackTrace: logEntry.anomaly_log,
    summary: analysis ? analysis.summary : null,
    analysis,
    metadata: {
      vm_id: logEntry.vm_id,
      source: 'LogRCA'
    }
  };
}

/**
 * 导入LogRCA分析结果到MongoDB
 * @param {string} filePath LogRCA分析结果文件路径
 */
async function importLogRCAData(filePath) {
  try {
    // 读取LogRCA分析结果文件
    const fileContent = fs.readFileSync(filePath, 'utf8');
    const logEntries = JSON.parse(fileContent);
    
    console.log(`读取到 ${logEntries.length} 条日志分析记录`);
    
    // 连接到MongoDB
    const mongoUri = process.env.MONGODB_URI || 'mongodb://localhost:27017/log-analysis';
    await mongoose.connect(mongoUri);
    console.log('已连接到MongoDB');
    
    // 转换并导入数据
    const formattedLogs = logEntries.map(parseLogRCAEntry);
    
    // 先删除之前导入的LogRCA数据
    await Log.deleteMany({ 'metadata.source': 'LogRCA' });
    console.log('已清除之前的LogRCA数据');
    
    // 导入新数据
    await Log.insertMany(formattedLogs);
    console.log(`成功导入 ${formattedLogs.length} 条日志分析记录`);
    
    // 断开连接
    await mongoose.disconnect();
    console.log('已断开MongoDB连接');
    
    return { success: true, count: formattedLogs.length };
  } catch (error) {
    console.error('导入LogRCA数据失败:', error);
    return { success: false, error: error.message };
  }
}

// 如果直接运行脚本，则执行导入操作
if (require.main === module) {
  const defaultPath = path.join(__dirname, '../../../LogRCA/output/log_analysis_report.json');
  
  // 检查文件是否存在
  if (!fs.existsSync(defaultPath)) {
    console.error(`错误: 文件不存在 ${defaultPath}`);
    process.exit(1);
  }
  
  importLogRCAData(defaultPath)
    .then(result => {
      if (result.success) {
        console.log('导入完成');
        process.exit(0);
      } else {
        console.error('导入失败:', result.error);
        process.exit(1);
      }
    })
    .catch(err => {
      console.error('发生错误:', err);
      process.exit(1);
    });
} else {
  // 作为模块导出
  module.exports = importLogRCAData;
} 