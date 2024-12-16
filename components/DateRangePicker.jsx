import { DatePicker } from 'antd';
import moment from 'moment';
const { RangePicker } = DatePicker;

function DateRangePicker({ value, onChange }) {
  // 定义快捷选项
  const ranges = {
    '今天': [moment().startOf('day'), moment().endOf('day')],
    '本周': [moment().startOf('week'), moment().endOf('week')],
    '本月': [moment().startOf('month'), moment().endOf('month')],
    '过去7天': [moment().subtract(7, 'days'), moment()],
    '过去30天': [moment().subtract(30, 'days'), moment()],
    '过去一年': [moment().subtract(1, 'year'), moment()],
  };

  return (
    <RangePicker 
      ranges={ranges}
      value={value}
      onChange={onChange}
      style={{ marginRight: '16px' }}
    />
  );
}

export default DateRangePicker; 