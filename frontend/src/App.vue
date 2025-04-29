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
                  <!-- 注释掉AI对话按钮
                  <el-button 
                    link 
                    type="success" 
                    @click="startAIChat(scope.row)"
                  >
                    <el-icon><ChatDotRound /></el-icon>
                    AI对话
                  </el-button>
                  -->
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
      
      <!-- 注释掉AIChatBox组件显示 
      <AIChatBox ref="aiChatRef" />
      -->
    </div>

    <el-dialog
      v-model="detailsVisible"
      title="异常日志详情"
      width="70%"
      center
      @open="handleDialogOpen"
      custom-class="details-dialog"
    >
      <div class="log-details">
        <!-- 日志基本信息 -->
        <div class="log-info">
          <div class="log-level">
            <el-tag size="large" :type="getTagType(currentLog.level)" effect="dark">
              {{ currentLog.level }}
            </el-tag>
          </div>
          <div class="log-time">{{ currentLog.timestamp }}</div>
          <div class="log-service">{{ currentLog.service }}</div>
        </div>

        <!-- 异常概述 -->
        <div class="section">
          <div class="section-title">
            <el-icon><Warning /></el-icon>
            <span>异常概述</span>
          </div>
          <div class="section-content">
            <div class="info-item">
              <div class="label">类型</div>
              <div class="value">{{ currentLog && currentLog.service === 'openstack-service' ? 'AssertionError' : '服务异常' }}</div>
            </div>
            <div class="info-item">
              <div class="label">表现</div>
              <div class="value">{{ currentLog && currentLog.service === 'openstack-service' ? '预期返回1个服务器实例，实际len(servers)为0' : currentLog.message }}</div>
            </div>
          </div>
        </div>

        <!-- 核心原因 -->
        <div class="section">
          <div class="section-title">
            <el-icon><CircleClose /></el-icon>
            <span>核心原因</span>
          </div>
          <div class="section-content">
            <div class="cause-item">
              <div class="cause-title">参数转换错误</div>
              <ul class="cause-list">
                <li>{{ currentLog && currentLog.service === 'openstack-service' ? 'flavor=abcde未映射到flavor_id' : '服务参数配置错误' }}</li>
                <li>{{ currentLog && currentLog.service === 'openstack-service' ? 'status=resize未匹配实例真实状态' : '状态不匹配' }}</li>
              </ul>
            </div>
            <div class="cause-item">
              <div class="cause-title">测试数据缺陷</div>
              <div class="cause-desc">
                {{ currentLog && currentLog.service === 'openstack-service' ? 'Mock返回空列表，但测试预期非空数据' : '测试数据不完整' }}
              </div>
            </div>
            <div class="cause-item">
              <div class="cause-title">状态同步异常</div>
              <div class="cause-desc">
                {{ currentLog && currentLog.service === 'openstack-service' ? 'Nova日志显示实例因pending task跳过状态更新' : '服务状态同步失败' }}
              </div>
            </div>
          </div>
        </div>

        <!-- 解决方案 -->
        <div class="section">
          <div class="section-title">
            <el-icon><SetUp /></el-icon>
            <span>解决方案</span>
          </div>
          <div class="section-content">
            <div class="solution-item">
              <div class="solution-title">短期措施</div>
              <ul class="solution-list">
                <li>{{ currentLog && currentLog.service === 'openstack-service' ? '检查compute_api.API.get_all中search_opts的过滤逻辑' : '检查服务配置' }}</li>
                <li>{{ currentLog && currentLog.service === 'openstack-service' ? '添加断言验证参数：mock_get.assert_called_with(search_opts={\'status\':\'resize\'})' : '更新服务参数验证' }}</li>
              </ul>
            </div>
            <div class="solution-item">
              <div class="solution-title">长期优化</div>
              <ul class="solution-list">
                <li>{{ currentLog && currentLog.service === 'openstack-service' ? '在get_all中记录search_opts和返回结果数量' : '增强日志记录' }}</li>
                <li>{{ currentLog && currentLog.service === 'openstack-service' ? '为pending task状态增加自动重试机制' : '添加自动重试机制' }}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

    <el-dialog
      v-model="fullScreenVisible"
      title="完整异常分析"
      width="90%"
      center
      fullscreen
      custom-class="fullscreen-dialog"
    >
      <div class="details-container">
        <div class="details-header">
          <div class="log-meta">
            <el-tag size="large" :type="getTagType(currentLog.level)" effect="dark">{{ currentLog.level }}</el-tag>
            <span class="log-timestamp">{{ currentLog.timestamp }}</span>
            <span class="log-service">{{ currentLog.service }}</span>
          </div>
          <div class="control-buttons">
            <el-button size="small" type="primary" @click="closeFullScreen" circle>
              <el-icon><Back /></el-icon>
            </el-button>
          </div>
        </div>
        
        <div class="details-content">
          <div class="detail-card">
            <div class="card-title">
              <el-icon><Warning /></el-icon>
              <span>异常概述</span>
            </div>
            <div class="card-content">
              <div class="detail-item">
                <div class="item-label">类型</div>
                <div class="item-value">{{ currentLog && currentLog.service === 'openstack-service' ? 'AssertionError' : '服务异常' }}</div>
              </div>
              <div class="detail-item">
                <div class="item-label">表现</div>
                <div class="item-value">{{ currentLog && currentLog.service === 'openstack-service' ? '预期返回1个服务器实例，实际len(servers)为0' : currentLog.message }}</div>
              </div>
            </div>
          </div>
          
          <div class="detail-card">
            <div class="card-title">
              <el-icon><CircleClose /></el-icon>
              <span>核心原因</span>
            </div>
            <div class="card-content">
              <div class="cause-section">
                <div class="cause-title">参数转换错误</div>
                <ul class="cause-list">
                  <li>{{ currentLog && currentLog.service === 'openstack-service' ? 'flavor=abcde未映射到flavor_id' : '服务参数配置错误' }}</li>
                  <li>{{ currentLog && currentLog.service === 'openstack-service' ? 'status=resize未匹配实例真实状态' : '状态不匹配' }}</li>
                </ul>
              </div>
              
              <div class="cause-section">
                <div class="cause-title">测试数据缺陷</div>
                <div class="cause-content">
                  {{ currentLog && currentLog.service === 'openstack-service' ? 'Mock返回空列表，但测试预期非空数据' : '测试数据不完整' }}
                </div>
              </div>
              
              <div class="cause-section">
                <div class="cause-title">状态同步异常</div>
                <div class="cause-content">
                  {{ currentLog && currentLog.service === 'openstack-service' ? 'Nova日志显示实例因pending task跳过状态更新' : '服务状态同步失败' }}
                </div>
              </div>
            </div>
          </div>
          
          <div class="detail-card">
            <div class="card-title">
              <el-icon><SetUp /></el-icon>
              <span>解决方案</span>
            </div>
            <div class="card-content">
              <div class="solution-section">
                <div class="solution-type">短期措施</div>
                <ul class="solution-list">
                  <li>{{ currentLog && currentLog.service === 'openstack-service' ? '检查compute_api.API.get_all中search_opts的过滤逻辑' : '检查服务配置' }}</li>
                  <li>{{ currentLog && currentLog.service === 'openstack-service' ? '添加断言验证参数：mock_get.assert_called_with(search_opts={\'status\':\'resize\'})' : '更新服务参数验证' }}</li>
                </ul>
              </div>
              
              <div class="solution-section">
                <div class="solution-type">长期优化</div>
                <ul class="solution-list">
                  <li>{{ currentLog && currentLog.service === 'openstack-service' ? '在get_all中记录search_opts和返回结果数量' : '增强日志记录' }}</li>
                  <li>{{ currentLog && currentLog.service === 'openstack-service' ? '为pending task状态增加自动重试机制' : '添加自动重试机制' }}</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ChatDotRound, FullScreen, Warning, CircleClose, SetUp, Back } from '@element-plus/icons-vue'
// 保留导入但注释掉使用
import AIChatBox from './components/AIChatBox.vue'
// 导入logService API，更新路径
import { logService } from './api/logService'

const searchForm = reactive({
  service: '',
  quickTime: '',
  timeRange: null
})

const services = [
  { value: 'dns-service', label: 'DNS服务' },
  { value: 'http-service', label: 'HTTP服务' },
  { value: 'ftp-service', label: 'FTP服务' },
  { value: 'smtp-service', label: 'SMTP服务' },
  { value: 'openstack-service', label: 'OpenStack服务' }
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

// 添加缺失的函数
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

// 将handleSearch函数替换为使用API服务的版本
const handleSearch = async () => {
  if (!searchForm.service) {
    ElMessage({
      message: '请选择服务',
      type: 'warning',
      duration: 3000,
      showClose: true,
      customClass: 'custom-message'
    })
    return
  }

  if (!searchForm.quickTime && !searchForm.timeRange) {
    ElMessage({
      message: '请选择时间或快捷时间',
      type: 'warning',
      duration: 3000,
      showClose: true,
      customClass: 'custom-message'
    })
    return
  }

  loading.value = true
  
  try {
    // 构建查询参数
    const params = {
      service: searchForm.service,
      timeRange: searchForm.timeRange,
      page: currentPage.value,
      pageSize: pageSize.value
    }

    // 调用API服务获取数据
    const result = await logService.queryLogs(params)
    
    // 更新数据
    logs.value = result.data
    total.value = result.total
  } catch (error) {
    console.error('查询日志失败:', error)
    
    ElMessage({
      message: '查询日志失败，请稍后再试',
      type: 'error',
      duration: 3000,
      showClose: true
    })
    
    // 清空数据
    logs.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

const handleSizeChange = (val) => {
  pageSize.value = val
  handleSearch()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  handleSearch()
}

// 更新详情查看函数，使用API获取详细信息
const showDetails = async (row) => {
  try {
    loading.value = true
    
    // 调用API获取详细信息
    const detailData = await logService.getLogDetails(row.id)
    
    // 更新当前日志数据
    currentLog.value = detailData
    
    // 显示详情对话框
    detailsVisible.value = true
  } catch (error) {
    console.error('获取日志详情失败:', error)
    
    ElMessage({
      message: '获取日志详情失败，请稍后再试',
      type: 'error',
      duration: 3000,
      showClose: true
    })
  } finally {
    loading.value = false
  }
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
1. 异常概述
   - 类型
   - 表现
2. 核心原因
   - 参数转换错误
   - 测试数据缺陷
   - 状态同步异常
3. 解决方案
   - 短期措施
   - 长期优化`

  aiChatRef.value?.startNewChat(analysisPrompt)
}

const toggleFullScreen = () => {
  fullScreenVisible.value = true
  detailsVisible.value = false
}

// 添加从全屏返回详情页的功能
const closeFullScreen = () => {
  fullScreenVisible.value = false
  detailsVisible.value = true
}

const handleDialogOpen = () => {
  // 移除对callChainGraph的操作
  // callChainGraphRef.value?.setFullView()
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
  display: flex;
  flex-direction: column;
  max-height: 90vh;
}

:deep(.el-dialog__body) {
  flex: 1;
  overflow: auto;
  padding: 0;
  max-height: calc(90vh - 120px);
}

.details-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-height: 80vh;
}

.details-header {
  padding: 16px 20px;
  background-color: #fff;
  border-bottom: 1px solid #ebeef5;
  position: sticky;
  top: 0;
  z-index: 1;
}

.details-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  height: calc(90vh - 200px); /* 设置固定高度 */
}

.details-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-height: 100%;
}

.detail-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
  overflow: hidden; /* 添加溢出处理 */
}

.card-title {
  padding: 15px 20px;
  border-bottom: 1px solid #ebeef5;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
}

.card-content {
  padding: 20px;
  background: #fff;
  overflow-y: auto;
  max-height: none;
  min-height: 200px; /* 设置最小高度 */
}

.detail-item {
  margin-bottom: 10px;
}

.item-label {
  font-weight: bold;
  color: #303133;
}

.item-value {
  color: #606266;
}

.cause-section {
  margin-bottom: 10px;
}

.cause-title {
  font-weight: bold;
  color: #303133;
  margin-bottom: 5px;
}

.cause-list {
  padding-left: 20px;
  list-style-type: disc;
}

.cause-content {
  color: #606266;
}

.solution-section {
  margin-bottom: 16px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 8px;
}

.solution-type {
  font-weight: 600;
  margin-bottom: 8px;
  color: #303133;
  font-size: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #ebeef5;
}

.solution-list {
  margin: 0;
  padding-left: 20px;
  list-style-type: disc;
}

.solution-list li {
  margin-bottom: 8px;
  line-height: 1.6;
  color: #606266;
}

.details-dialog {
  :deep(.el-dialog) {
    display: flex;
    flex-direction: column;
    margin: 0 !important;
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    max-height: 90vh;
    width: 80% !important;
    border-radius: 8px;
  }

  :deep(.el-dialog__header) {
    padding: 20px;
    margin: 0;
    border-bottom: 1px solid #ebeef5;
  }

  :deep(.el-dialog__body) {
    flex: 1;
    overflow: hidden;
    padding: 0;
  }
}

.details-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.details-header {
  padding: 20px;
  background-color: #fff;
  border-bottom: 1px solid #ebeef5;
  position: sticky;
  top: 0;
  z-index: 1;
}

.details-content {
  padding: 20px;
  flex: 1;
  overflow-y: auto;
}

.detail-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
  padding: 0;
}

.card-title {
  padding: 15px 20px;
  border-bottom: 1px solid #ebeef5;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
}

.card-title .el-icon {
  margin-right: 8px;
  font-size: 18px;
}

.card-content {
  padding: 20px;
  background: #fff;
}

.cause-section, .solution-section {
  margin-bottom: 16px;
}

.cause-title, .solution-type {
  font-weight: 600;
  margin-bottom: 8px;
  color: #303133;
}

.cause-list, .solution-list {
  margin: 0;
  padding-left: 20px;
}

.cause-list li, .solution-list li {
  margin-bottom: 8px;
  line-height: 1.6;
}

.log-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.log-timestamp {
  color: #606266;
}

.log-service {
  background: #f5f7fa;
  padding: 4px 8px;
  border-radius: 4px;
  color: #606266;
}

/* 移除之前的响应式布局代码 */
@media screen and (max-width: 768px) {
  .detail-card {
    width: 100%;
    margin-right: 0;
  }
  
  .log-meta {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .log-meta .el-tag {
    margin-bottom: 5px;
  }
  
  .log-timestamp, .log-service {
    margin-top: 5px;
  }
}

/* 美化卡片样式 */
.detail-card {
  transition: all 0.3s ease;
}

.detail-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  padding-bottom: 8px;
  border-bottom: 2px solid #ebeef5;
}

.card-content {
  padding: 15px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

/* 添加图标颜色 */
.card-title .el-icon {
  color: #409EFF;
}
</style>
