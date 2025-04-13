import axios from 'axios'
import { mockLogs } from '../mock/logData'

// 创建axios实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 日志服务API
export const logService = {
  /**
   * 查询日志数据
   * @param {Object} params 查询参数
   * @param {string} params.service 服务名称
   * @param {Array} params.timeRange 时间范围 [开始时间, 结束时间]
   * @param {number} params.page 当前页码
   * @param {number} params.pageSize 每页数量
   * @returns {Promise<Object>} 查询结果
   */
  async queryLogs(params) {
    try {
      // 构建查询参数
      const queryParams = {
        service: params.service,
        startTime: params.timeRange ? params.timeRange[0].toISOString() : undefined,
        endTime: params.timeRange ? params.timeRange[1].toISOString() : undefined,
        page: params.page || 1,
        pageSize: params.pageSize || 10
      }
      
      // 调试输出
      console.log('查询参数:', JSON.stringify(queryParams));
      
      // 发送API请求
      const response = await api.get('/logs', { params: queryParams })
      return response.data
    } catch (error) {
      console.error('获取日志数据失败:', error)
      
      // 如果API请求失败，回退到模拟数据
      console.warn('使用模拟数据进行回退')
      await new Promise(resolve => setTimeout(resolve, 500))
      
      // 过滤模拟数据以匹配查询参数
      let filteredLogs = [...mockLogs]
      
      if (params.service) {
        filteredLogs = filteredLogs.filter(log => log.service === params.service)
      }
      
      if (params.timeRange) {
        const [startTime, endTime] = params.timeRange
        filteredLogs = filteredLogs.filter(log => {
          const logDate = new Date(log.timestamp)
          return logDate >= startTime && logDate <= endTime
        })
      }
      
      // 分页处理
      const start = ((params.page || 1) - 1) * (params.pageSize || 10)
      const end = start + (params.pageSize || 10)
      
      return {
        data: filteredLogs.slice(start, end),
        total: filteredLogs.length
      }
    }
  },
  
  /**
   * 获取日志详情
   * @param {string} logId 日志ID
   * @returns {Promise<Object>} 日志详情
   */
  async getLogDetails(logId) {
    try {
      const response = await api.get(`/logs/${logId}`)
      return response.data
    } catch (error) {
      console.error('获取日志详情失败:', error)
      
      // 如果API请求失败，回退到模拟数据
      console.warn('使用模拟数据进行回退')
      await new Promise(resolve => setTimeout(resolve, 500))
      return mockLogs.find(log => log.id === logId)
    }
  },
  
  /**
   * 获取日志分析结果
   * @param {string} logId 日志ID
   * @returns {Promise<Object>} 分析结果
   */
  async getLogAnalysis(logId) {
    try {
      const response = await api.get(`/logs/${logId}/analysis`)
      return response.data
    } catch (error) {
      console.error('获取日志分析结果失败:', error)
      
      // 如果API请求失败，返回简单的回退数据
      await new Promise(resolve => setTimeout(resolve, 500))
      return {
        summary: '无法获取分析结果，请稍后再试',
        rootCauses: [],
        solutions: []
      }
    }
  }
} 