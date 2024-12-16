<template>
  <div class="page-container">
    <div class="container">
      <div class="main-section">
        <el-card class="main-card">
          <template #header>
            <div class="card-header">
              <h2>日志异常检测与分析平台</h2>
              <div v-if="showMessage" class="custom-message">
                {{ messageContent }}
              </div>
            </div>
          </template>
          
          <div class="search-section">
            <el-form :model="searchForm" inline class="search-form">
              <el-form-item label="服务选择">
                <el-select v-model="searchForm.service" placeholder="请选择服务" style="width: 240px">
                  <el-option
                    v-for="item in services"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  />
                </el-select>
              </el-form-item>
              
              <el-form-item label="时间选择">
                <el-date-picker
                  v-model="searchForm.timeRange"
                  type="datetimerange"
                  range-separator="至"
                  start-placeholder="开始时间"
                  end-placeholder="结束时间"
                  style="width: 460px"
                />
              </el-form-item>

              <el-form-item label="快捷时间">
                <el-select v-model="searchForm.quickTime" placeholder="请选择快捷时间" style="width: 240px" @change="handleQuickTimeChange">
                  <el-option label="最近一天" value="1" />
                  <el-option label="最近一周" value="7" />
                  <el-option label="最近一月" value="30" />
                </el-select>
              </el-form-item>
              
              <el-form-item>
                <el-button type="primary" size="default" @click="handleSearch">查询</el-button>
              </el-form-item>
            </el-form>
          </div>

          <div class="logs-section" style="overflow-y: auto; max-height: calc(100vh - 400px);">
            <el-table 
              :data="logs" 
              style="width: 100%" 
              v-loading="loading"
              :max-height="tableHeight"
              element-loading-text="加载中..."
              element-loading-background="rgba(255, 255, 255, 0.9)"
            >
              <el-table-column prop="timestamp" label="时间" width="200" />
              <el-table-column prop="service" label="服务" width="180" />
              <el-table-column prop="level" label="级别" width="120" align="center">
                <template #default="scope">
                  <el-tag :type="getTagType(scope.row.level)">{{ scope.row.level }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="message" label="错误信息" min-width="500" show-overflow-tooltip />
              <el-table-column fixed="right" label="操作" width="180" align="center">
                <template #default="scope">
                  <el-button link type="primary" @click="showDetails(scope.row)">
                    查看详情
                  </el-button>
                  <el-button 
                    link 
                    type="success" 
                    @click="startAIChat(scope.row)"
                  >
                    <el-icon><ChatDotRound /></el-icon>
                    AI对话
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
            
            <div v-if="!loading && logs.length === 0" class="empty-state">
              <el-empty 
                description="暂无数据，请点击查询按钮获取日志信息"
                :image-size="200"
              >
                <el-button type="primary" @click="handleSearch">
                  立即查询
                </el-button>
              </el-empty>
            </div>

            <div class="pagination" v-if="logs.length > 0">
              <el-pagination
                v-model:current-page="currentPage"
                v-model:page-size="pageSize"
                :total="total"
                :page-sizes="[10, 20, 50, 100]"
                layout="total, sizes, prev, pager, next"
                @size-change="handleSizeChange"
                @current-change="handleCurrentChange"
              />
            </div>
          </div>
        </el-card>
      </div>
      
      <AIChatBox ref="aiChatRef" />
    </div>

    <el-dialog
      v-model="detailsVisible"
      title="异常日志详情"
      width="60%"
      :style="{ maxHeight: '80vh' }"
      center
      @open="handleDialogOpen"
    >
      <el-descriptions :column="1" border>
        <el-descriptions-item label="函数调用链">
          <div class="call-chain-container">
            <CallChainGraph ref="callChainGraph" :stack-trace="currentLog.stackTrace" />
            <el-button type="text" @click="toggleFullScreen">全屏查看</el-button>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="异常日志分析">
          <span v-html="currentLog.summary"></span>
        </el-descriptions-item>
        <el-descriptions-item label="修复建议">
          <ul>
            <li>检查网络配置，确保服务可用。</li>
            <li>查看系统日志以获取更多信息。</li>
            <li>联系技术支持以获得进一步帮助。</li>
          </ul>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <el-dialog
      v-model="fullScreenVisible"
      title="完整函数调用链"
      width="90%"
      center
    >
      <CallChainGraph :stack-trace="currentLog.stackTrace" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ChatDotRound } from '@element-plus/icons-vue'
import AIChatBox from './components/AIChatBox.vue'
import CallChainGraph from './components/CallChainGraph.vue'

const searchForm = reactive({
  service: '',
  quickTime: '',
  timeRange: null
})

const services = [
  { value: 'dns-service', label: 'DNS服务' },
  { value: 'http-service', label: 'HTTP服务' },
  { value: 'ftp-service', label: 'FTP服务' },
  { value: 'smtp-service', label: 'SMTP服务' }
]

const loading = ref(false)
const logs = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const detailsVisible = ref(false)
const currentLog = ref({})
const fullScreenVisible = ref(false)
const showMessage = ref(false)
const messageContent = ref('')

// 动态计算表格高度
const tableHeight = ref(500)  // 默认高度

const calculateTableHeight = () => {
  const windowHeight = window.innerHeight
  const offset = 400  // 预留空间（头部+搜索区域+分页+边距）
  tableHeight.value = windowHeight - offset
}

// 添加偏移量计算
const containerOffset = ref(120)

const calculateOffset = () => {
  const windowWidth = window.innerWidth
  // 根据窗口宽度动态计算偏移量
  if (windowWidth > 1920) {
    containerOffset.value = 120
  } else if (windowWidth > 1600) {
    containerOffset.value = 100
  } else if (windowWidth > 1366) {
    containerOffset.value = 80
  } else if (windowWidth > 1024) {
    containerOffset.value = 60
  } else {
    containerOffset.value = 20
  }
}

// 修改 onMounted，添加窗口大小变化监听
onMounted(() => {
  calculateTableHeight()
  calculateOffset()  // 初始计算
  window.addEventListener('resize', () => {
    calculateTableHeight()
    calculateOffset()  // 窗口大小变化时重新计算
  })
})

onUnmounted(() => {
  window.removeEventListener('resize', calculateTableHeight)
})

// 模拟数据生成函数
const generateMockLogs = (serviceType) => {
  const mockLogs = []
  const levels = ['ERROR', 'WARN', 'CRITICAL']
  const messages = {
    'dns-service': [
      'DNS解析失败',
      'DNS服务器超时',
      '无效的DNS响应'
    ],
    'http-service': [
      'HTTP 404错误',
      'HTTP 500内部服务器错误',
      'HTTP请求超时'
    ],
    'ftp-service': [
      'FTP连接失败',
      'FTP权限被拒绝',
      'FTP传输中断'
    ],
    'smtp-service': [
      'SMTP身份验证失败',
      'SMTP连接超时',
      'SMTP邮件发送失败'
    ]
  }

  const stackTraces = {
    'dns-service': [
      'at DNSResolver.resolve(DNSResolver.java:45)',
      'at NetworkManager.handleRequest(NetworkManager.java:78)',
      'at ApiGateway.route(ApiGateway.java:65)'
    ],
    'http-service': [
      'at HttpRequestHandler.process(HttpRequestHandler.java:120)',
      'at WebServer.handleRequest(WebServer.java:89)',
      'at ApiGateway.route(ApiGateway.java:65)'
    ],
    'ftp-service': [
      'at FTPClient.connect(FTPClient.java:32)',
      'at FileTransferManager.upload(FileTransferManager.java:56)',
      'at ApiGateway.route(ApiGateway.java:65)'
    ],
    'smtp-service': [
      'at SMTPClient.send(SMTPClient.java:90)',
      'at EmailService.sendEmail(EmailService.java:45)',
      'at ApiGateway.route(ApiGateway.java:65)'
    ]
  }

  for (let i = 0; i < 20; i++) {
    const level = levels[Math.floor(Math.random() * levels.length)]
    const message = messages[serviceType][Math.floor(Math.random() * messages[serviceType].length)]
    const problemStage = stackTraces[serviceType][1]
    const stackTrace = stackTraces[serviceType].join('\n    ')

    mockLogs.push({
      id: `${serviceType}-${i + 1}`,
      timestamp: new Date(Date.now() - Math.random() * 86400000 * 7).toLocaleString(),
      service: serviceType,
      level,
      message,
      summary: `在处理请求时，${message}。<strong>可能的问题阶段是：${problemStage}</strong>。总体异常是由于网络配置错误或服务不可用导致`,
      stackTrace: `Error: ${message}\n    ${stackTrace}`
    })
  }

  return mockLogs
}

const getTagType = (level) => {
  const types = {
    'ERROR': 'danger',
    'WARN': 'warning',
    'CRITICAL': 'error'
  }
  return types[level] || 'info'
}

const handleQuickTimeChange = (value) => {
  if (value !== 'custom') {
    const now = new Date()
    let startDate = new Date()
    if (value === '1') {
      startDate.setDate(now.getDate() - 1)
    } else if (value === '7') {
      startDate.setDate(now.getDate() - 7)
    } else if (value === '30') {
      startDate.setMonth(now.getMonth() - 1)
    }
    searchForm.timeRange = [startDate, now]
  }
}

const handleSearch = () => {
  if (!searchForm.service) {
    ElMessage({
      message: '请选择服务',
      type: 'warning',
      duration: 3000, // 提示持续时间，单位为毫秒
      showClose: true, // 显示关闭按钮
      customClass: 'custom-message' // 自定义样式类
    })
    return
  }

  if (!searchForm.quickTime && !searchForm.timeRange) {
    ElMessage({
      message: '请选择时间或快捷时间',
      type: 'warning',
      duration: 3000, // 提示持续时间，单位为毫秒
      showClose: true, // 显示关闭按钮
      customClass: 'custom-message' // 自定义样式类
    })
    return
  }

  loading.value = true
  // 模拟API请求延迟
  setTimeout(() => {
    const selectedService = searchForm.service
    const allLogs = generateMockLogs(selectedService)

    // 根据快捷时间或时间范围进行过滤
    let filteredLogs = allLogs
    if (searchForm.quickTime !== 'custom' && searchForm.quickTime) {
      const now = new Date()
      let startDate = new Date()
      if (searchForm.quickTime === '1') {
        startDate.setDate(now.getDate() - 1)
      } else if (searchForm.quickTime === '7') {
        startDate.setDate(now.getDate() - 7)
      } else if (searchForm.quickTime === '30') {
        startDate.setMonth(now.getMonth() - 1)
      }
      filteredLogs = allLogs.filter(log => {
        const logDate = new Date(log.timestamp)
        return logDate >= startDate && logDate <= now
      })
    } else if (searchForm.timeRange) {
      const [start, end] = searchForm.timeRange
      filteredLogs = allLogs.filter(log => {
        const logDate = new Date(log.timestamp)
        return logDate >= start && logDate <= end
      })
    }

    total.value = filteredLogs.length // 设置总数据量
    // 根据当前页和每页大小进行分页
    const start = (currentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    logs.value = filteredLogs.slice(start, end)
    loading.value = false
  }, 500)
}

const handleSizeChange = (val) => {
  pageSize.value = val
  handleSearch()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  handleSearch()
}

const showDetails = (row) => {
  currentLog.value = row
  detailsVisible.value = true
}

// 添加与AI对话的方法
const aiChatRef = ref(null)  // 添加ref以调用子组件方法

const startAIChat = (row) => {
  const analysisPrompt = `服务：${row.service}
时间：${row.timestamp}
级别：${row.level}
错误信息：${row.message}
堆栈信息：${row.stackTrace}

请从以下几个方面进行分析：
1. 错误原因分析
2. 可能的影响
3. 解决建议
4. 预防措施`

  aiChatRef.value?.startNewChat(analysisPrompt)
}

const toggleFullScreen = () => {
  fullScreenVisible.value = !fullScreenVisible.value
}

const callChainGraphRef = ref(null)

const handleDialogOpen = () => {
  callChainGraphRef.value?.setFullView()
}
</script>

<style scoped>
.page-container {
  min-height: 100vh;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  background-color: #f5f7fa;
  padding: 20px;
  box-sizing: border-box;
  position: fixed; /* 定页面位置 */
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden; /* 确保页面不滚动 */
}

.container {
  width: 95%;
  max-width: 2000px;
  display: flex;
  gap: 20px;
  margin: 0 auto;
  justify-content: center;
  transform: translateX(0);
  height: 100%; /* 确保容器占页面高度 */
}

.main-section {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  height: 100%; /* 确保主卡片占满容器高度 */
}

.main-card, .chat-card {
  width: 100%;
  margin: 0;
  flex-grow: 0;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  height: 100%; /* 确保卡片占满主卡片高度 */
  overflow: hidden;
  border-radius: 16px;
  transition: all 0.3s ease;
  border: none;
}

.main-card:hover, .chat-card:hover {
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.search-section {
  margin: 0 20px 20px;
  padding: 24px;
  background-color: #f8f9fa;
  border-radius: 12px;
  display: flex;
  justify-content: center;
  box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.03);
  position: relative;
  z-index: 10;
}

.card-header {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 16px 0;
  background: linear-gradient(to right, #f8f9fa, #ffffff);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  position: relative; /* 确保子元素可以绝对定位 */
}

.card-header h2 {
  margin: 0;
  color: #303133;
  font-size: 24px;
  font-weight: 600;
  background: linear-gradient(45deg, #409EFF, #36D1DC);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

:deep(.el-table) {
  --el-table-header-bg-color: #f8f9fa;
  border-radius: 8px;
  overflow: hidden;
}

:deep(.el-table th) {
  background: linear-gradient(to right, #f8f9fa, #ffffff);
  font-weight: 600;
  color: #303133;
}

:deep(.el-table td) {
  padding: 12px 0;
}

:deep(.el-tag) {
  border-radius: 6px;
  padding: 4px 8px;
}

:deep(.el-button) {
  border-radius: 8px;
  transition: all 0.3s ease;
}

:deep(.el-button:not(.is-text):hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
}

:deep(.el-select__wrapper) {
  border-radius: 8px;
}

.pagination {
  margin-top: 20px;
  width: 100%;
  display: flex;
  justify-content: center;
  padding: 16px 0;
}

/* 优化加载状态的显示 */
:deep(.el-loading-mask) {
  background-color: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(4px);
  border-radius: 16px;
}

:deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.15);
}

:deep(.el-dialog__header) {
  margin: 0;
  padding: 20px 24px;
  background: linear-gradient(to right, #f8f9fa, #ffffff);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

:deep(.el-descriptions) {
  padding: 24px;
  border-radius: 12px;
  background-color: #f8f9fa;
}

:deep(.el-descriptions__cell) {
  padding: 16px 24px;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

:deep(.el-descriptions-item__label) {
  font-weight: bold;
  color: #303133;
}

:deep(.el-descriptions-item__content) {
  color: #606266;
}

:deep(ul) {
  padding-left: 20px;
  list-style-type: disc;
}

:deep(li) {
  margin-bottom: 8px;
}

/* 确保日期选择器弹窗在最上层 */
:deep(.el-picker__popper) {
  z-index: 2000 !important;
}

/* 响应式布局调整 */
@media screen and (max-width: 1200px) {
  .container {
    width: 98%;
    transform: translateX(0);
  }
}

.call-chain-container {
  max-height: 200px; /* 限制最大高度 */
  overflow-y: auto; /* 启���垂直滚动 */
  padding: 10px;
  background-color: #f8f9fa;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  position: relative;
}

.call-chain-container .el-button {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 1;
}

.custom-message {
  font-size: 20px; /* 增大字体 */
  font-weight: bold; /* 加粗字体 */
  padding: 10px 20px; /* 增加内边距 */
  background-color: #f0f9ff; /* 设置背景颜色 */
  border: 1px solid #b3d8ff; /* 设置边框颜色 */
  border-radius: 8px; /* 圆角 */
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); /* 添加阴影 */
  position: fixed;
  top: 50%; /* 垂直居中 */
  left: 50%; /* 水平居中 */
  transform: translate(-50%, -50%); /* 确保居中 */
  z-index: 1000; /* 确保在其他元素之上 */
}
</style>
