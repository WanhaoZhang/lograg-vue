// 管理聊天历史记录
export class ChatHistory {
  constructor() {
    this.messages = []
  }

  // 添加用户消息
  addUserMessage(content) {
    this.messages.push({
      role: 'user',
      content: content
    })
  }

  // 添加助手消息
  addAssistantMessage(content) {
    this.messages.push({
      role: 'assistant',
      content: content
    })
  }

  // 获取所有消息历史
  getMessages() {
    return this.messages
  }

  // 清空聊天历史
  clear() {
    this.messages = []
  }
} 