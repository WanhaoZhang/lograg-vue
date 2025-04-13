import React, { useState, useEffect } from 'react';
import { DatePicker, Table, Card, Space, Button, Tag, message } from 'antd';
import { SearchOutlined, DownloadOutlined, AlertOutlined } from '@ant-design/icons';

const { RangePicker } = DatePicker;

function LogAnalysis() {
  const [timeRange, setTimeRange] = useState({
    startTime: new Date(Date.now() - 24 * 60 * 60 * 1000),
    endTime: new Date()
  });
  const [loading, setLoading] = useState(false);
  const [logData, setLogData] = useState([]);
  const [alertRules, setAlertRules] = useState([]);

  const columns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
      sorter: (a, b) => new Date(a.timestamp) - new Date(b.timestamp)
    },
    {
      title: '日志级别',
      dataIndex: 'level',
      key: 'level',
      width: 100,
      render: (level) => (
        <Tag color={level === 'ERROR' ? 'red' : level === 'WARN' ? 'orange' : 'green'}>
          {level}
        </Tag>
      )
    },
    {
      title: '服务名称',
      dataIndex: 'serviceName',
      key: 'serviceName',
      width: 150
    },
    {
      title: '日志内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space>
          <Button type="link" onClick={() => showLogDetail(record)}>
            详情
          </Button>
          <Button type="link" onClick={() => addToAnalysis(record)}>
            分析
          </Button>
        </Space>
      )
    }
  ];

  const fetchLogData = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/logs/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          startTime: timeRange.startTime.toISOString(),
          endTime: timeRange.endTime.toISOString()
        })
      });
      const data = await response.json();
      setLogData(data);
    } catch (error) {
      message.error('获取日志数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    fetchLogData();
  };

  const handleExport = async () => {
    try {
      const response = await fetch('/api/logs/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          startTime: timeRange.startTime.toISOString(),
          endTime: timeRange.endTime.toISOString()
        })
      });
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `logs-${new Date().toISOString()}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      message.error('导出日志失败');
    }
  };

  return (
    <Card>
      <Space direction="vertical" style={{ width: '100%' }}>
        <Space>
          <RangePicker
            showTime
            value={[timeRange.startTime, timeRange.endTime]}
            onChange={(dates) => {
              if (dates) {
                setTimeRange({
                  startTime: dates[0],
                  endTime: dates[1]
                });
              }
            }}
            shortcuts={[
              {
                text: '最近24小时',
                value: () => [new Date(Date.now() - 24 * 60 * 60 * 1000), new Date()]
              },
              {
                text: '最近7天',
                value: () => [new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), new Date()]
              }
            ]}
          />
          <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
            搜索
          </Button>
          <Button icon={<DownloadOutlined />} onClick={handleExport}>
            导出
          </Button>
          <Button icon={<AlertOutlined />} onClick={() => setShowRuleModal(true)}>
            告警规则
          </Button>
        </Space>

        <Table
          columns={columns}
          dataSource={logData}
          loading={loading}
          rowKey="id"
          scroll={{ x: 1200, y: 600 }}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`
          }}
        />
      </Space>
    </Card>
  );
}

export default LogAnalysis; 