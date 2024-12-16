import React, { useState, useEffect, useRef } from 'react';
import { Input, Button, Card, List, Avatar, Space, Tag, Spin, message } from 'antd';
import { SendOutlined, RobotOutlined, UserOutlined } from '@ant-design/icons';

function LogChat() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const userMessage = {
      type: 'user',
      content: inputValue,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setLoading(true);

    try {
      const response = await fetch('/api/chat/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: inputValue,
          context: messages.slice(-5) // 发送最近5条消息作为上下文
        })
      });

      const data = await response.json();
      
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: data.response,
        analysis: data.analysis,
        timestamp: new Date().toISOString()
      }]);
    } catch (error) {
      message.error('分析请求失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const renderMessage = (msg) => {
    const isUser = msg.type === 'user';

    return (
      <List.Item>
        <Space align="start" style={{ width: '100%', justifyContent: isUser ? 'flex-end' : 'flex-start' }}>
          {!isUser && <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#1890ff' }} />}
          <div
            style={{
              maxWidth: '70%',
              padding: '12px 16px',
              backgroundColor: isUser ? '#1890ff' : '#f0f2f5',
              borderRadius: '8px',
              color: isUser ? 'white' : 'rgba(0, 0, 0, 0.85)'
            }}
          >
            <div>{msg.content}</div>
            {msg.analysis && (
              <div style={{ marginTop: 8 }}>
                <Tag color="blue">分析结果</Tag>
                <div style={{ marginTop: 4 }}>{msg.analysis}</div>
              </div>
            )}
          </div>
          {isUser && <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#1890ff' }} />}
        </Space>
      </List.Item>
    );
  };

  return (
    <Card style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ flex: 1, overflow: 'auto', marginBottom: 16 }}>
        <List
          dataSource={messages}
          renderItem={renderMessage}
          split={false}
        />
        <div ref={messagesEndRef} />
      </div>
      
      <div style={{ display: 'flex', gap: 8 }}>
        <Input.TextArea
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="请输入您的问题..."
          autoSize={{ minRows: 1, maxRows: 4 }}
          onPressEnter={(e) => {
            if (!e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleSend}
          loading={loading}
        >
          发送
        </Button>
      </div>
      
      {analyzing && (
        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <Spin /> 正在分析日志...
        </div>
      )}
    </Card>
  );
}

export default LogChat; 