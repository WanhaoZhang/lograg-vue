import { mockLogs } from '@/mock/logData'

// 临时使用模拟数据
export const logService = {
  async queryLogs(params) {
    // 模拟API调用延迟
    await new Promise(resolve => setTimeout(resolve, 500))
    return {
      data: mockLogs,
      total: mockLogs.length
    }
  },
  
  async getLogDetails(logId) {
    await new Promise(resolve => setTimeout(resolve, 500))
    return mockLogs.find(log => log.id === logId)
  }
} 