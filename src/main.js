import './assets/main.css'

import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import ECharts from 'vue-echarts'
import { use } from "echarts/core"

// 配置DeepSeek API
const DEEPSEEK_API_KEY = 'sk-78d748f832f2466b9c4caf5383ebc981'
const DEEPSEEK_API_URL = 'https://api.deepseek.com/chat/completions'

// 创建API调用函数
export const chatWithDeepSeek = async (messages) => {
  try {
    const response = await fetch(DEEPSEEK_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${DEEPSEEK_API_KEY}`
      },
      body: JSON.stringify({
        model: 'deepseek-chat',
        messages: messages,
        stream: false
      })
    })
    
    if (!response.ok) {
      throw new Error(`API请求失败: ${response.status}`)
    }
    
    return await response.json()
  } catch (error) {
    console.error('DeepSeek API调用错误:', error)
    throw error
  }
}

// 手动引入 ECharts 模块来减小打包体积
import {
  CanvasRenderer
} from 'echarts/renderers'
import {
  GraphChart
} from 'echarts/charts'
import {
  TooltipComponent,
  LegendComponent
} from 'echarts/components'

use([
  CanvasRenderer,
  GraphChart,
  TooltipComponent,
  LegendComponent
])

const app = createApp(App)

// 全局注册组件（也可以使用局部注册）
app.component('v-chart', ECharts)

app.use(ElementPlus)
app.mount('#app')
