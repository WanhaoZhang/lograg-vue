import React from 'react';
import DateRangePicker from './components/DateRangePicker';
import 'antd/dist/antd.css'; // 导入 antd 的样式
import './styles/DateRangePicker.css'; // 导入我们自定义的样式

function App() {
  return (
    <div className="App">
      <DateRangePicker />
    </div>
  );
}

export default App; 