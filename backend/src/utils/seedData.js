const mongoose = require('mongoose');
const Log = require('../models/Log');

// 初始化示例日志数据
const seedLogs = async () => {
  try {
    // 检查是否已有数据
    const count = await Log.countDocuments();
    
    if (count > 0) {
      console.log('已有日志数据，跳过种子数据生成');
      return;
    }
    
    console.log('正在生成示例日志数据...');
    
    // 准备日志数据
    const logs = generateSampleLogs();
    
    // 插入数据
    await Log.insertMany(logs);
    
    console.log(`成功生成 ${logs.length} 条示例日志数据`);
  } catch (error) {
    console.error('生成示例数据失败:', error);
  }
};

// 生成示例日志数据
function generateSampleLogs() {
  const services = ['dns-service', 'http-service', 'ftp-service', 'smtp-service', 'openstack-service'];
  const levels = ['ERROR', 'WARN', 'INFO', 'CRITICAL', 'DEBUG'];
  
  const logs = [];
  
  // 为每个服务生成一些日志
  services.forEach(service => {
    // 生成20条记录
    for (let i = 0; i < 20; i++) {
      const level = levels[Math.floor(Math.random() * 3)]; // 主要使用前三种级别
      const timestamp = new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000); // 过去7天内的随机时间
      
      // 根据服务类型生成不同的日志内容
      const logData = generateLogByService(service, level);
      
      logs.push({
        timestamp,
        service,
        level,
        message: logData.message,
        stackTrace: logData.stackTrace,
        summary: logData.summary,
        metadata: logData.metadata || {}
      });
    }
  });
  
  return logs;
}

// 根据服务类型生成日志内容
function generateLogByService(service, level) {
  const messages = {
    'dns-service': {
      'ERROR': 'DNS解析失败',
      'WARN': 'DNS服务器超时',
      'CRITICAL': '无效的DNS响应'
    },
    'http-service': {
      'ERROR': 'HTTP 404错误',
      'WARN': 'HTTP 500内部服务器错误',
      'CRITICAL': 'HTTP请求超时'
    },
    'ftp-service': {
      'ERROR': 'FTP连接失败',
      'WARN': 'FTP权限被拒绝',
      'CRITICAL': 'FTP传输中断'
    },
    'smtp-service': {
      'ERROR': 'SMTP身份验证失败',
      'WARN': 'SMTP连接超时',
      'CRITICAL': 'SMTP邮件发送失败'
    },
    'openstack-service': {
      'ERROR': 'AssertionError: 预期返回1个服务器实例，实际为0',
      'WARN': 'Nova实例状态同步失败',
      'CRITICAL': 'Flavor参数转换错误'
    }
  };

  const stackTraces = {
    'dns-service': 'at DNSResolver.resolve (DNSResolver.java:45)\nat NetworkManager.handleRequest (NetworkManager.java:78)\nat ApiGateway.route (ApiGateway.java:65)',
    'http-service': 'at HttpRequestHandler.process (HttpRequestHandler.java:120)\nat WebServer.handleRequest (WebServer.java:89)\nat ApiGateway.route (ApiGateway.java:65)',
    'ftp-service': 'at FTPClient.connect (FTPClient.java:32)\nat FileTransferManager.upload (FileTransferManager.java:56)\nat ApiGateway.route (ApiGateway.java:65)',
    'smtp-service': 'at SMTPClient.send (SMTPClient.java:90)\nat EmailService.sendEmail (EmailService.java:45)\nat ApiGateway.route (ApiGateway.java:65)',
    'openstack-service': 'at ServerList.get_all (ServerList.py:85)\nat compute_api.API.get_all (compute_api.py:120)\nat test_servers.py:245'
  };

  const message = messages[service][level] || `${service} ${level.toLowerCase()} message`;
  const stackTrace = `Error: ${message}\n${stackTraces[service]}`;
  
  let summary = '';
  if (service === 'openstack-service') {
    summary = `测试失败，${message}。核心问题在于compute_api.API.get_all。异常是由于参数转换错误和状态同步异常导致`;
  } else {
    summary = `在处理请求时，${message}。可能的问题阶段是NetworkManager或API网关。总体异常是由于网络配置错误或服务不可用导致`;
  }
  
  return {
    message,
    stackTrace,
    summary,
    metadata: {
      requestId: Math.random().toString(36).substring(2, 15),
      hostname: `server-${Math.floor(Math.random() * 10)}`,
      environment: Math.random() > 0.5 ? 'production' : 'staging'
    }
  };
}

module.exports = seedLogs;