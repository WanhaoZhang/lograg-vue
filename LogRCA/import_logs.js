const fs = require('fs');
const path = require('path');
const { MongoClient } = require('mongodb');

async function importLogRCAData() {
  const filePath = path.join(__dirname, 'output', 'log_analysis_report.json');
  
  try {
    // 检查文件是否存在
    if (!fs.existsSync(filePath)) {
      console.error(`错误: 文件不存在 ${filePath}`);
      process.exit(1);
    }
    
    // 读取LogRCA分析结果文件
    const fileContent = fs.readFileSync(filePath, 'utf8');
    const logEntries = JSON.parse(fileContent);
    
    console.log(`读取到 ${logEntries.length} 条日志分析记录`);
    
    // 连接到MongoDB
    const mongoUri = process.env.MONGODB_URI || 'mongodb://localhost:27017/loganalysis';
    console.log(`正在连接到MongoDB: ${mongoUri}`);
    
    const client = new MongoClient(mongoUri);
    await client.connect();
    console.log('已连接到MongoDB');
    
    const db = client.db();
    const logsCollection = db.collection('logs');
    
    // 先删除之前导入的LogRCA数据
    await logsCollection.deleteMany({ 'metadata.source': 'LogRCA' });
    console.log('已清除之前的LogRCA数据');
    
    // 转换并导入数据
    const formattedLogs = logEntries.map(logEntry => {
      // 解析日志信息
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
      const originalService = serviceMatch ? serviceMatch[0] : 'test';
      
      // 提取日志消息
      const messageStartIndex = logEntry.anomaly_log.indexOf('] ');
      const message = messageStartIndex !== -1 
        ? logEntry.anomaly_log.substring(messageStartIndex + 2) 
        : logEntry.anomaly_log;
      
      // 提取分析内容
      let summary = '';
      let rootCauses = [];
      let solutions = [];
      
      // 简单提取分析摘要（第一行）
      if (logEntry.analysis) {
        const lines = logEntry.analysis.split('\n');
        if (lines.length > 0) {
          summary = lines[0].replace('# ', '');
        }
        
        // 提取根本原因和解决方案
        let currentSection = '';
        for (const line of lines) {
          if (line.includes('异常概述')) {
            currentSection = 'summary';
          } else if (line.includes('详细分析') || line.includes('可能的异常原因')) {
            currentSection = 'causes';
          } else if (line.includes('解决方案建议')) {
            currentSection = 'solutions';
          } else if (line.startsWith('- ') || line.startsWith('  -')) {
            if (currentSection === 'causes') {
              rootCauses.push({
                title: '异常原因',
                description: line.replace(/^- |^  - /, '')
              });
            } else if (currentSection === 'solutions') {
              let type = 'general';
              if (line.includes('短期')) {
                type = 'shortTerm';
              } else if (line.includes('长期')) {
                type = 'longTerm';
              }
              
              solutions.push({
                type: type,
                description: line.replace(/^- |^  - /, '')
              });
            }
          }
        }
      }
      
      // 确保至少有一个解决方案
      if (solutions.length === 0) {
        solutions.push({
          type: 'general',
          description: '需要进一步分析'
        });
      }
      
      return {
        timestamp: timestamp,
        service: 'openstack-service',
        level: level,
        message: message,
        stackTrace: logEntry.anomaly_log,
        summary: summary,
        analysis: {
          summary: summary,
          rootCauses: rootCauses,
          solutions: solutions
        },
        metadata: {
          vm_id: logEntry.vm_id,
          source: 'LogRCA',
          originalService: originalService
        },
        createdAt: new Date(),
        updatedAt: new Date()
      };
    });
    
    // 导入数据
    const result = await logsCollection.insertMany(formattedLogs);
    console.log(`成功导入 ${result.insertedCount} 条日志分析记录`);
    
    // 断开连接
    await client.close();
    console.log('已断开MongoDB连接');
    
    console.log('导入成功!');
    process.exit(0);
  } catch (error) {
    console.error('导入LogRCA数据失败:', error);
    process.exit(1);
  }
}

// 执行导入操作
importLogRCAData(); 