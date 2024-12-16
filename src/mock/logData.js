export const mockLogs = [
  {
    id: 1,
    timestamp: '2023-12-01 10:00:00',
    service: 'user-service',
    level: 'ERROR',
    message: '用户认证失败',
    aiSummary: '检测到用户登录时的认证失败，可能是由于密码错误或账号被锁定导致。',
    callStack: 'at AuthService.authenticate (AuthService.js:25)\nat LoginController.login (LoginController.js:15)'
  },
  {
    id: 2,
    timestamp: '2023-12-01 09:45:23',
    service: 'order-service',
    level: 'WARN',
    message: '订单处理超时',
    aiSummary: '订单处理耗时超过预期阈值，建议检查数据库性能和网络连接状态。',
    callStack: 'at OrderProcessor.process (OrderProcessor.js:78)\nat OrderService.createOrder (OrderService.js:45)'
  },
  {
    id: 3,
    timestamp: '2023-12-01 09:30:15',
    service: 'payment-service',
    level: 'ERROR',
    message: '支付接口调用异常',
    aiSummary: '调用第三方支付接口时发生网络超时，需要检查网络连接和接口可用性。',
    callStack: 'at PaymentGateway.processPayment (PaymentGateway.js:156)\nat PaymentService.pay (PaymentService.js:89)'
  }
] 