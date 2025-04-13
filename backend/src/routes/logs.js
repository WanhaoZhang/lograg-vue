const express = require('express');
const Log = require('../models/Log');

const router = express.Router();

/**
 * @route GET /api/logs
 * @desc 获取日志列表
 * @access Public
 */
router.get('/', async (req, res, next) => {
  try {
    const {
      service,
      level,
      startTime,
      endTime,
      page = 1,
      pageSize = 10
    } = req.query;

    // 构建查询条件
    const query = {};
    
    if (service) {
      if (service === 'openstack-service') {
        // 查询service为'openstack-service'的记录
        query.service = 'openstack-service';
      } else {
        query.service = service;
      }
    }
    
    if (level) {
      query.level = level;
    }
    
    if (startTime || endTime) {
      query.timestamp = {};
      if (startTime) {
        query.timestamp.$gte = new Date(startTime);
      }
      if (endTime) {
        query.timestamp.$lte = new Date(endTime);
      }
    }

    // 调试输出
    console.log('后端查询条件:', JSON.stringify(query));
    console.log('startTime:', startTime, '  endTime:', endTime);
    
    // 计算分页
    const skip = (parseInt(page) - 1) * parseInt(pageSize);
    
    // 执行查询
    const [logs, total] = await Promise.all([
      Log.find(query)
        .sort({ timestamp: -1 })
        .skip(skip)
        .limit(parseInt(pageSize))
        .lean(),
      Log.countDocuments(query)
    ]);

    // 格式化数据
    const formattedLogs = logs.map(log => ({
      id: log._id,
      timestamp: log.timestamp,
      service: log.service,
      level: log.level,
      message: log.message,
      stackTrace: log.stackTrace,
      summary: log.summary
    }));

    res.json({
      data: formattedLogs,
      total,
      page: parseInt(page),
      pageSize: parseInt(pageSize)
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route GET /api/logs/:id
 * @desc 获取日志详情
 * @access Public
 */
router.get('/:id', async (req, res, next) => {
  try {
    const log = await Log.findById(req.params.id).lean();
    
    if (!log) {
      return res.status(404).json({ message: '日志不存在' });
    }

    // 格式化响应数据
    const formattedLog = {
      id: log._id,
      timestamp: log.timestamp,
      service: log.service,
      level: log.level,
      message: log.message,
      stackTrace: log.stackTrace,
      summary: log.summary,
      metadata: log.metadata
    };

    res.json(formattedLog);
  } catch (error) {
    next(error);
  }
});

/**
 * @route GET /api/logs/:id/analysis
 * @desc 获取日志分析结果
 * @access Public
 */
router.get('/:id/analysis', async (req, res, next) => {
  try {
    const log = await Log.findById(req.params.id).lean();
    
    if (!log) {
      return res.status(404).json({ message: '日志不存在' });
    }

    // 如果没有分析结果，返回默认分析
    if (!log.analysis) {
      // 根据日志类型生成模拟分析结果
      const defaultAnalysis = generateDefaultAnalysis(log);
      return res.json(defaultAnalysis);
    }

    res.json(log.analysis);
  } catch (error) {
    next(error);
  }
});

/**
 * @route POST /api/logs
 * @desc 创建新日志
 * @access Public
 */
router.post('/', async (req, res, next) => {
  try {
    const {
      timestamp,
      service,
      level,
      message,
      stackTrace,
      summary,
      metadata
    } = req.body;

    const newLog = new Log({
      timestamp: timestamp || new Date(),
      service,
      level,
      message,
      stackTrace,
      summary,
      metadata
    });

    await newLog.save();
    
    res.status(201).json({
      id: newLog._id,
      message: '日志创建成功'
    });
  } catch (error) {
    next(error);
  }
});

// 生成默认分析结果的辅助函数
function generateDefaultAnalysis(log) {
  const causes = [];
  const solutions = [];
  
  // 根据服务和错误等级确定可能的原因和解决方案
  if (log.service === 'dns-service') {
    causes.push({
      title: 'DNS配置错误',
      description: 'DNS服务器配置不正确或域名解析失败'
    });
    solutions.push({
      type: 'shortTerm',
      description: '检查DNS服务器配置和网络连接'
    });
  } else if (log.service === 'http-service') {
    causes.push({
      title: 'HTTP请求问题',
      description: '服务器返回错误状态码或请求超时'
    });
    solutions.push({
      type: 'shortTerm',
      description: '检查服务器状态和网络连接'
    });
  } else if (log.service === 'openstack-service') {
    causes.push({
      title: '参数转换错误',
      description: 'flavor=abcde未映射到flavor_id'
    });
    causes.push({
      title: '测试数据缺陷',
      description: 'Mock返回空列表，但测试预期非空数据'
    });
    
    solutions.push({
      type: 'shortTerm',
      description: '检查compute_api.API.get_all中search_opts的过滤逻辑'
    });
    solutions.push({
      type: 'longTerm',
      description: '为pending task状态增加自动重试机制'
    });
  } else {
    // 默认分析
    causes.push({
      title: '未知错误',
      description: '系统无法自动分析此类型错误的具体原因'
    });
    solutions.push({
      type: 'shortTerm',
      description: '请检查相关日志和系统状态'
    });
  }

  return {
    summary: `${log.service}服务出现${log.level.toLowerCase()}级别的异常，可能影响系统正常运行。`,
    rootCauses: causes,
    solutions
  };
}

module.exports = {
  logsRouter: router
}; 