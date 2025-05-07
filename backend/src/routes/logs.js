const express = require('express');
const Log = require('../models/Log');

const router = express.Router();

/**
 * @route GET /api/logs/services
 * @desc 获取所有可用服务列表
 * @access Public
 */
router.get('/services', async (req, res, next) => {
  try {
    // 从数据库中查询去重后的服务列表
    const services = await Log.distinct('service');
    console.log('可用服务列表:', services);
    
    // 确保服务列表中包含openstack-service
    if (!services.includes('openstack-service') && services.length > 0) {
      services.push('openstack-service');
    }
    
    // 构建响应数据
    const serviceOptions = services.map(service => ({
      value: service,
      label: service === 'test' ? 'LogRCA异常分析' 
           : service === 'openstack-service' ? 'OpenStack服务' 
           : `${service}服务`
    }));
    
    res.json(serviceOptions);
  } catch (error) {
    console.error('获取服务列表失败:', error);
    next(error);
  }
});

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
      vm_id,
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
    
    if (vm_id) {
      query.vm_id = vm_id;
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
    console.log('vm_id:', vm_id);
    
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
      vm_id: log.vm_id,
      stackTrace: log.stackTrace,
      summary: log.summary || (log.analysis ? log.analysis.summary : ''),
      hasAnalysis: !!log.analysis
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
      vm_id: log.vm_id,
      stackTrace: log.stackTrace,
      summary: log.summary || (log.analysis ? log.analysis.summary : ''),
      metadata: log.metadata,
      analysis: log.analysis // 确保包含完整的分析信息
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
 * @route GET /api/logs/vm/:vm_id
 * @desc 获取指定VM_ID的所有日志
 * @access Public
 */
router.get('/vm/:vm_id', async (req, res, next) => {
  try {
    const { vm_id } = req.params;
    const { page = 1, pageSize = 10 } = req.query;

    // 计算分页
    const skip = (parseInt(page) - 1) * parseInt(pageSize);
    
    // 执行查询
    const [logs, total] = await Promise.all([
      Log.find({ vm_id })
        .sort({ timestamp: -1 })
        .skip(skip)
        .limit(parseInt(pageSize))
        .lean(),
      Log.countDocuments({ vm_id })
    ]);

    // 格式化数据
    const formattedLogs = logs.map(log => ({
      id: log._id,
      timestamp: log.timestamp,
      service: log.service,
      level: log.level,
      message: log.message,
      vm_id: log.vm_id,
      stackTrace: log.stackTrace,
      summary: log.summary || (log.analysis ? log.analysis.summary : ''),
      hasAnalysis: !!log.analysis
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
      vm_id,
      metadata
    } = req.body;

    const newLog = new Log({
      timestamp: timestamp || new Date(),
      service,
      level,
      message,
      stackTrace,
      summary,
      vm_id,
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

/**
 * 生成默认的分析结果
 * @param {Object} log 日志对象
 * @returns {Object} 分析结果
 */
function generateDefaultAnalysis(log) {
  // 根据日志类型和级别生成分析结果
  let summary = '';
  let rootCauses = [];
  let solutions = [];
  
  switch (log.level) {
    case 'ERROR':
      summary = `系统错误: ${log.message.substring(0, 50)}`;
      rootCauses = [{
        title: '可能的原因',
        description: '系统组件运行异常或配置错误'
      }];
      solutions = [{
      type: 'shortTerm',
        description: '检查系统日志以获取更多详细信息并重启相关服务'
      }];
      break;
      
    case 'WARN':
      summary = `警告信息: ${log.message.substring(0, 50)}`;
      rootCauses = [{
        title: '可能的原因',
        description: '系统检测到潜在的问题，但未导致严重故障'
      }];
      solutions = [{
      type: 'shortTerm',
        description: '监控系统状态，确保问题未扩大'
      }];
      break;
      
    default:
      summary = `信息日志: ${log.message.substring(0, 50)}`;
      rootCauses = [{
        title: '说明',
        description: '这是一条正常的系统操作日志'
      }];
      solutions = [];
      break;
  }

  return {
    summary,
    rootCauses,
    solutions
  };
}

module.exports = {
  logsRouter: router
}; 