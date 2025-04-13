import { useState } from 'react';
import { DeepSeekService } from '../services/DeepSeekService';

export default function Chat() {
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([]);
  const [inputMessage, setInputMessage] = useState('');
  const deepSeekService = new DeepSeekService();

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    const newMessages = [...messages, { role: 'user', content: inputMessage }];
    setMessages(newMessages);
    setInputMessage('');
    
    try {
      const response = await deepSeekService.chat(newMessages);
      setMessages([...newMessages, { role: 'assistant', content: response }]);
    } catch (error) {
      console.error('发送消息失败:', error);
      // 可以添加一个错误提示UI
    }
  };

  return (
    <div className="flex flex-col h-screen">
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map((message, index) => (
          <div key={index} className={`mb-4 ${message.role === 'user' ? 'text-right' : 'text-left'}`}>
            <div className={`inline-block p-2 rounded-lg ${
              message.role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-200'
            }`}>
              {message.content}
            </div>
          </div>
        ))}
      </div>
      
      <form onSubmit={handleSendMessage} className="p-4 border-t">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            className="flex-1 p-2 border rounded"
            placeholder="输入消息..."
          />
          <button 
            type="submit"
            className="px-4 py-2 bg-blue-500 text-white rounded"
          >
            发送
          </button>
        </div>
      </form>
    </div>
  );
} 