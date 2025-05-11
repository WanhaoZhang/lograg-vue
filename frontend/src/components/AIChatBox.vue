<template>
  <div class="chat-box" ref="chatBox">
    <div class="chat-header">
      <h2>日志对话</h2>
    </div>
    
    <!-- 固定高度的聊天记录区域 -->
    <div class="chat-history" ref="chatHistory">
      <div 
        v-for="(message, index) in chatMessages" 
        :key="index" 
        :class="['message', message.type]"
      >
        <div class="message-content">
          <el-avatar 
            :size="32" 
            :src="message.type === 'user' ? userAvatar : aiAvatar"
          />
          <div class="message-text">
            <div v-if="message.type === 'user'">{{ message.content }}</div>
            <div 
              v-else 
              class="markdown-body"
              v-html="renderMarkdown(message.content)"
            ></div>
          </div>
        </div>
        <div class="message-time">{{ message.time }}</div>
      </div>
    </div>
    
    <!-- 输入区域 -->
    <div class="chat-input">
      <el-input
        v-model="inputMessage"
        type="textarea"
        :rows="3"
        placeholder="请输入您的问题..."
        resize="none"
        @keyup.enter.exact.prevent="sendMessage"
      />
      <el-button 
        type="primary" 
        :loading="loading"
        @click="sendMessage"
      >
        发送
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { chatWithDeepSeek } from '../main'
import { marked } from 'marked'
import DOMPurify from 'dompurify' // 用于防止XSS攻击

const inputMessage = ref('')
const loading = ref(false)
const chatHistory = ref(null)

// 模拟用户AI头像
const userAvatar = 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png'
const aiAvatar = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'

// 聊天记录
const chatMessages = ref([
  {
    type: 'ai',
    content: '你好！我是AI助手，请问有什么可以帮助您？',
    time: new Date().toLocaleTimeString()
  }
])

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim()) return
  
  const userContent = inputMessage.value
  
  // 添加用户消息
  chatMessages.value.push({
    type: 'user',
    content: userContent,
    time: new Date().toLocaleTimeString()
  })
  
  loading.value = true
  inputMessage.value = ''
  await scrollToBottom()
  
  try {
    // 构造消息历史
    const messages = chatMessages.value.map(msg => ({
      role: msg.type === 'user' ? 'user' : 'assistant',
      content: msg.content
    }))
    
    // 调用 DeepSeek API
    const response = await chatWithDeepSeek(messages)
    
    if (response.choices && response.choices[0]?.message) {
      chatMessages.value.push({
        type: 'ai',
        content: response.choices[0].message.content,
        time: new Date().toLocaleTimeString()
      })
    }
  } catch (error) {
    console.error('AI对话出错:', error)
    chatMessages.value.push({
      type: 'ai',
      content: '抱歉，处理您的请求时出现错误，请稍后重试。',
      time: new Date().toLocaleTimeString()
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (chatHistory.value) {
    chatHistory.value.scrollTop = chatHistory.value.scrollHeight
  }
}

// 修改开始新对话的方法
const startNewChat = async (question) => {
  // 添加用户消息
  chatMessages.value.push({
    type: 'user',
    content: question,
    time: new Date().toLocaleTimeString()
  })
  
  loading.value = true
  await scrollToBottom()
  
  try {
    const messages = [{
      role: 'user',
      content: question
    }]
    
    const response = await chatWithDeepSeek(messages)
    
    if (response.choices && response.choices[0]?.message) {
      chatMessages.value.push({
        type: 'ai',
        content: response.choices[0].message.content,
        time: new Date().toLocaleTimeString()
      })
    }
  } catch (error) {
    console.error('AI对话出错:', error)
    chatMessages.value.push({
      type: 'ai',
      content: '抱歉，处理您的请求时出现错误，请稍后重试。',
      time: new Date().toLocaleTimeString()
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

// 添加markdown渲染函数
const renderMarkdown = (content) => {
  try {
    // 使用DOMPurify清理HTML，防止XSS攻击
    return DOMPurify.sanitize(marked(content))
  } catch (error) {
    console.error('Markdown渲染错误:', error)
    return content
  }
}

// 暴露方法供父组件调用
defineExpose({
  startNewChat
})

onMounted(() => {
  scrollToBottom()
})
</script>

<style scoped>
.chat-box {
  width: 400px;
  height: calc(100vh - 100px);
  background: white;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  margin-left: 20px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.chat-box:hover {
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.chat-header {
  padding: 16px;
  border-bottom: 1px solid #eee;
  text-align: center;
  background: linear-gradient(to right, #f8f9fa, #ffffff);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  border-top-left-radius: 16px;
  border-top-right-radius: 16px;
}

.chat-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  background: linear-gradient(45deg, #409EFF, #36D1DC);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background-color: #f9fafb;
}

.message {
  margin-bottom: 16px;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-content {
  display: flex;
  gap: 12px;
  margin-bottom: 4px;
}

.message-text {
  padding: 12px;
  border-radius: 12px;
  max-width: 80%;
  word-break: break-word;
}

.user .message-text {
  background-color: #e6f4ff;
  color: #1677ff;
}

.ai .message-text {
  background-color: #f5f5f5;
  color: #333;
  padding: 16px;
}

.message-time {
  font-size: 12px;
  color: #999;
  text-align: center;
}

.chat-input {
  padding: 16px;
  border-top: 1px solid #eee;
  background: white;
  border-bottom-left-radius: 16px;
  border-bottom-right-radius: 16px;
}

.chat-input .el-button {
  width: 100%;
  margin-top: 12px;
}

/* 自定义滚动条样式 */
.chat-history::-webkit-scrollbar {
  width: 6px;
}

.chat-history::-webkit-scrollbar-thumb {
  background-color: #ddd;
  border-radius: 3px;
}

.chat-history::-webkit-scrollbar-track {
  background-color: #f5f5f5;
}

/* 输入框样式优化 */
:deep(.el-textarea__inner) {
  border-radius: 8px;
  resize: none;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.3s ease;
}

:deep(.el-textarea__inner:focus) {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

:deep(.el-button--primary) {
  border-radius: 8px;
}

/* 添加Markdown样式 */
.markdown-body {
  font-size: 14px;
  line-height: 1.6;
  color: #333;
  padding: 5px 0;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4 {
  margin-top: 20px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
}

.markdown-body h1 { font-size: 1.7em; color: #24292e; }
.markdown-body h2 { font-size: 1.5em; color: #24292e; }
.markdown-body h3 { font-size: 1.3em; color: #24292e; }
.markdown-body h4 { font-size: 1.2em; color: #24292e; }

.markdown-body p {
  margin-top: 0;
  margin-bottom: 16px;
  line-height: 1.7;
}

.markdown-body code {
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 85%;
  background-color: rgba(27,31,35,0.05);
  border-radius: 3px;
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
}

.markdown-body pre {
  padding: 16px;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
  background-color: #f6f8fa;
  border-radius: 6px;
  margin-bottom: 16px;
  border: 1px solid #e1e4e8;
}

.markdown-body pre code {
  display: block;
  padding: 0;
  margin: 0;
  overflow: auto;
  line-height: inherit;
  word-wrap: normal;
  background-color: transparent;
  border: 0;
}

.markdown-body ul,
.markdown-body ol {
  padding-left: 2em;
  margin-top: 0;
  margin-bottom: 16px;
}

.markdown-body li {
  margin-bottom: 6px;
}

.markdown-body li + li {
  margin-top: 0.25em;
}

.markdown-body blockquote {
  margin: 0 0 16px 0;
  padding: 0 1em;
  color: #6a737d;
  border-left: 0.25em solid #dfe2e5;
  background-color: #f6f8fa;
  border-radius: 3px;
}

.markdown-body blockquote > :first-child {
  margin-top: 0;
}

.markdown-body blockquote > :last-child {
  margin-bottom: 0;
}

.markdown-body table {
  border-spacing: 0;
  border-collapse: collapse;
  margin-bottom: 16px;
  width: 100%;
  overflow: auto;
}

.markdown-body table th,
.markdown-body table td {
  padding: 8px 13px;
  border: 1px solid #dfe2e5;
}

.markdown-body table th {
  font-weight: 600;
  background-color: #f6f8fa;
}

.markdown-body table tr {
  background-color: #fff;
  border-top: 1px solid #c6cbd1;
}

.markdown-body table tr:nth-child(2n) {
  background-color: #f6f8fa;
}

.markdown-body a {
  color: #0366d6;
  text-decoration: none;
}

.markdown-body a:hover {
  text-decoration: underline;
}

.markdown-body img {
  max-width: 100%;
  box-sizing: content-box;
  background-color: #fff;
  border-radius: 3px;
}

.markdown-body hr {
  height: 0.25em;
  padding: 0;
  margin: 24px 0;
  background-color: #e1e4e8;
  border: 0;
}
</style> 