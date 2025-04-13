import axios from 'axios'

const chatAPI = axios.create({
  baseURL: 'https://api.deepseek.com/v1',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer sk-a52406feb1684792a2ba399aa2472e7b'
  }
})

export const sendMessage = async (messages) => {
  try {
    const response = await chatAPI.post('/chat/completions', {
      model: 'deepseek-chat',
      messages: [
        { role: 'system', content: 'You are a helpful assistant.' },
        ...messages
      ],
      stream: false
    })
    return response.data.choices[0].message.content
  } catch (error) {
    console.error('Chat API Error:', error)
    throw new Error('无法连接到AI服务，请稍后重试')
  }
} 