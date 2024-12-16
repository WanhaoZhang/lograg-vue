export class DeepSeekService {
  private apiKey: string;
  private baseUrl: string;

  constructor() {
    this.apiKey = 'sk-78d748f832f2466b9c4caf5383ebc981';
    this.baseUrl = 'https://api.deepseek.com';
  }

  async chat(messages: Array<{ role: string; content: string }>) {
    try {
      console.log('发送请求到DeepSeek API:', {
        url: `${this.baseUrl}/v1/chat/completions`,
        messages
      });

      const response = await fetch(`${this.baseUrl}/v1/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`
        },
        body: JSON.stringify({
          model: 'deepseek-chat',
          messages: [
            { role: "system", content: "You are a helpful assistant" },
            ...messages
          ],
          stream: false
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error('API响应错误:', errorData);
        throw new Error(`API 错误: ${JSON.stringify(errorData)}`);
      }

      const data = await response.json();
      console.log('API响应数据:', data);
      
      if (!data.choices?.[0]?.message?.content) {
        throw new Error('API返回数据格式错误');
      }

      return data.choices[0].message.content;
    } catch (error) {
      console.error('DeepSeek API 调用失败:', error);
      if (error instanceof Error) {
        throw new Error(`调用AI服务失败: ${error.message}`);
      }
      throw error;
    }
  }
} 