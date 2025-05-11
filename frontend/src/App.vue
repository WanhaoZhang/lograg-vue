<template>
  <div class="page-container">
    <div class="container">
      <div class="main-section">
        <div class="page-header">
          <h2>日志异常检测与分析平台</h2>
          <div v-if="showMessage" class="custom-message">
            {{ messageContent }}
          </div>
        </div>
        
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

        <div class="logs-section" style="overflow-y: auto; max-height: calc(100vh - 300px);">
          <el-table 
            :data="logs" 
            style="width: 100%" 
            v-loading="loading"
            :max-height="tableHeight"
            element-loading-text="加载中..."
            element-loading-background="rgba(255, 255, 255, 0.9)"
          >
            <el-table-column prop="timestamp" label="时间" width="200">
              <template #default="scope">
                {{ formatDateTime(scope.row.timestamp) }}
              </template>
            </el-table-column>
            <el-table-column prop="service" label="服务" width="180" />
            <el-table-column prop="level" label="级别" width="120" align="center">
              <template #default="scope">
                <el-tag :type="getTagType(scope.row.level)">{{ scope.row.level }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="message" label="错误信息" min-width="500" show-overflow-tooltip />
            <el-table-column prop="vm_id" label="VM ID" width="220" show-overflow-tooltip />
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
      </div>
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
        <!-- 只保留分析报告部分 -->
        <div class="section report-section" v-if="currentLog.analysis && currentLog.analysis.rawText">
          <div class="markdown-body enhanced" v-html="renderMarkdown(currentLog.analysis.rawText)"></div>
        </div>
        <!-- 如果没有分析报告则显示提示 -->
        <div class="empty-content" v-else>暂无分析报告数据</div>
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
            <span class="log-timestamp">{{ formatDateTime(currentLog.timestamp) }}</span>
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
                <div class="item-value markdown-body" v-html="renderMarkdown(currentLog && currentLog.service === 'openstack-service' ? 'AssertionError' : '服务异常')"></div>
              </div>
              <div class="detail-item">
                <div class="item-label">表现</div>
                <div class="item-value markdown-body" v-html="renderMarkdown(currentLog && currentLog.service === 'openstack-service' ? '预期返回1个服务器实例，实际len(servers)为0' : currentLog.message)"></div>
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
                  <li class="markdown-body" v-html="renderMarkdown(currentLog && currentLog.service === 'openstack-service' ? 'flavor=abcde未映射到flavor_id' : '服务参数配置错误')"></li>
                  <li class="markdown-body" v-html="renderMarkdown(currentLog && currentLog.service === 'openstack-service' ? 'status=resize未匹配实例真实状态' : '状态不匹配')"></li>
                </ul>
              </div>
              
              <div class="cause-section">
                <div class="cause-title">测试数据缺陷</div>
                <div class="cause-content markdown-body" v-html="renderMarkdown(currentLog && currentLog.service === 'openstack-service' ? 'Mock返回空列表，但测试预期非空数据' : '测试数据不完整')"></div>
              </div>
              
              <div class="cause-section">
                <div class="cause-title">状态同步异常</div>
                <div class="cause-content markdown-body" v-html="renderMarkdown(currentLog && currentLog.service === 'openstack-service' ? 'Nova日志显示实例因pending task跳过状态更新' : '服务状态同步失败')"></div>
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
                  <li class="markdown-body" v-html="renderMarkdown(currentLog && currentLog.service === 'openstack-service' ? '检查compute_api.API.get_all中search_opts的过滤逻辑' : '检查服务配置')"></li>
                  <li class="markdown-body" v-html="renderMarkdown(currentLog && currentLog.service === 'openstack-service' ? '添加断言验证参数：mock_get.assert_called_with(search_opts={\'status\':\'resize\'})' : '更新服务参数验证')"></li>
                </ul>
              </div>
              
              <div class="solution-section">
                <div class="solution-type">长期优化</div>
                <ul class="solution-list">
                  <li class="markdown-body" v-html="renderMarkdown(currentLog && currentLog.service === 'openstack-service' ? '在get_all中记录search_opts和返回结果数量' : '增强日志记录')"></li>
                  <li class="markdown-body" v-html="renderMarkdown(currentLog && currentLog.service === 'openstack-service' ? '为pending task状态增加自动重试机制' : '添加自动重试机制')"></li>
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
import { ChatDotRound, FullScreen, Warning, CircleClose, SetUp, Back, Document } from '@element-plus/icons-vue'
// 保留导入但注释掉使用
import AIChatBox from './components/AIChatBox.vue'
// 导入logService API，更新路径
import { logService } from './api/logService'
// 导入Markdown渲染相关库
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const searchForm = reactive({
  service: 'openstack-service',
  quickTime: '',
  timeRange: [new Date('2017-01-01'), new Date()]
})

const services = ref([])

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
  
  // 初始加载日志服务列表
  loadServices()
  
  // 自动执行一次查询
  handleSearch()
})

onUnmounted(() => {
  window.removeEventListener('resize', calculateTableHeight)
})

// 添加加载服务列表的函数
const loadServices = async () => {
  try {
    const serviceList = await logService.getServices()
    // 如果后端返回了服务列表，更新services数组
    if (serviceList && serviceList.length > 0) {
      services.value.length = 0 // 清空现有数组
      serviceList.forEach(service => services.value.push(service))
    }
  } catch (error) {
    console.error('加载服务列表失败:', error)
  }
}

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
  // 如果没有选择服务且服务列表不为空，自动选择第一个服务
  if (!searchForm.service && services.value.length > 0) {
    searchForm.service = services.value[0].value;
  }

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

  // 检查时间范围，如果未设置则使用默认值（2017年至今）
  if (!searchForm.timeRange) {
    searchForm.timeRange = [new Date('2017-01-01'), new Date()];
  }

  // 当切换服务时，重置当前页为第1页
  currentPage.value = 1;

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
  console.log('页面大小改变:', val)
  pageSize.value = val
  handleSearch()
}

const handleCurrentChange = (val) => {
  console.log('当前页改变:', val)
  currentPage.value = val
  
  // 构建查询参数
  const params = {
    service: searchForm.service,
    timeRange: searchForm.timeRange,
    page: currentPage.value,
    pageSize: pageSize.value
  }
  
  // 执行查询，但不重置页码
  loading.value = true
  
  logService.queryLogs(params)
    .then(result => {
      // 更新数据
      logs.value = result.data
      total.value = result.total
    })
    .catch(error => {
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
    })
    .finally(() => {
      loading.value = false
    })
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

// 在script部分添加formatDateTime方法
const formatDateTime = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  
  // 格式化日期和时间
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');
  
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

// 添加Markdown渲染函数
const renderMarkdown = (content) => {
  try {
    // 使用DOMPurify清理HTML，防止XSS攻击
    return DOMPurify.sanitize(marked(content))
  } catch (error) {
    console.error('Markdown渲染错误:', error)
    return content
  }
}

</script>
<style scoped>
/* 页面容器样式 */
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
  height: 100%; /* 确保主内容占满容器高度 */
  background-color: #fff;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.page-header {
  padding: 20px;
  background: linear-gradient(to right, #f8f9fa, #ffffff);
  border-bottom: 1px solid #ebeef5;
  text-align: center;
  position: sticky;
  top: 0;
  z-index: 10;
}

.page-header h2 {
  margin: 0;
  color: #303133;
  font-size: 24px;
  font-weight: 600;
  background: linear-gradient(45deg, #409EFF, #36D1DC);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.search-section {
  margin: 0;
  padding: 24px;
  background-color: #f8f9fa;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  display: flex;
  justify-content: center;
  box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.03);
  position: relative;
  z-index: 9;
}

.logs-section {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: #fff;
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

.analysis-dialog {
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

.analysis-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.analysis-text {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  height: calc(90vh - 200px); /* 设置固定高度 */
}

/* 添加Markdown样式 */
.markdown-body {
  font-size: 14px;
  line-height: 1.6;
  color: #333;
  padding: 16px;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4 {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
}

.markdown-body h1 { font-size: 1.7em; color: #24292e; }
.markdown-body h2 { font-size: 1.5em; color: #24292e; }
.markdown-body h3 { font-size: 1.3em; color: #24292e; }
.markdown-body h4 { font-size: 1.2em; color: #24292e; }

.markdown-body p {
  margin-top: 0;
  margin-bottom: 16px;
  line-height: 1.7;
}

.markdown-body code {
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 85%;
  background-color: rgba(27,31,35,0.05);
  border-radius: 3px;
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
}

.markdown-body pre {
  padding: 16px;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
  background-color: #f6f8fa;
  border-radius: 6px;
  margin-bottom: 16px;
  border: 1px solid #e1e4e8;
}

.markdown-body pre code {
  display: block;
  padding: 0;
  margin: 0;
  overflow: auto;
  line-height: inherit;
  word-wrap: normal;
  background-color: transparent;
  border: 0;
}

.markdown-body ul,
.markdown-body ol {
  padding-left: 2em;
  margin-top: 0;
  margin-bottom: 16px;
}

.markdown-body li {
  margin-bottom: 6px;
}

.markdown-body li + li {
  margin-top: 0.25em;
}

.markdown-body blockquote {
  margin: 0 0 16px 0;
  padding: 0 1em;
  color: #6a737d;
  border-left: 0.25em solid #dfe2e5;
  background-color: #f6f8fa;
  border-radius: 3px;
}

.markdown-body blockquote > :first-child {
  margin-top: 0;
}

.markdown-body blockquote > :last-child {
  margin-bottom: 0;
}

.markdown-body table {
  border-spacing: 0;
  border-collapse: collapse;
  margin-bottom: 16px;
  width: 100%;
  overflow: auto;
}

.markdown-body table th,
.markdown-body table td {
  padding: 8px 13px;
  border: 1px solid #dfe2e5;
}

.markdown-body table th {
  font-weight: 600;
  background-color: #f6f8fa;
}

.markdown-body table tr {
  background-color: #fff;
  border-top: 1px solid #c6cbd1;
}

.markdown-body table tr:nth-child(2n) {
  background-color: #f6f8fa;
}

.markdown-body a {
  color: #0366d6;
  text-decoration: none;
}

.markdown-body a:hover {
  text-decoration: underline;
}

.markdown-body img {
  max-width: 100%;
  box-sizing: content-box;
  background-color: #fff;
  border-radius: 3px;
}

.markdown-body hr {
  height: 0.25em;
  padding: 0;
  margin: 24px 0;
  background-color: #e1e4e8;
  border: 0;
}

/* 添加Markdown内部样式调整 */
.solution-desc.markdown-body {
  margin-top: 8px;
}

.cause-desc.markdown-body {
  margin-top: 6px;
}

.detail-item .markdown-body {
  padding: 8px 0;
}

.cause-list li.markdown-body, 
.solution-list li.markdown-body {
  padding: 4px 0;
}

.cause-content.markdown-body, 
.solution-content.markdown-body {
  padding: 8px;
  background-color: #f9fafb;
  border-radius: 4px;
}

/* 在详情卡片内的Markdown样式特别调整 */
.log-details .markdown-body {
  font-size: 14px;
  padding: 0;
  background: transparent;
}

.log-details .markdown-body p {
  margin-bottom: 10px;
}

.log-details .markdown-body code {
  background-color: #f6f8fa;
  padding: 2px 5px;
  border-radius: 3px;
}

.log-details .markdown-body pre {
  margin: 10px 0;
}

/* 增强版Markdown样式 */
.report-section {
  background-color: #fff;
  border-radius: 8px;
  padding: 0;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.markdown-body.enhanced {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  line-height: 1.6;
  color: #24292e;
  padding: 32px;
  background-color: #fff;
  border-radius: 8px;
  font-size: 15px;
}

.markdown-body.enhanced h1,
.markdown-body.enhanced h2,
.markdown-body.enhanced h3,
.markdown-body.enhanced h4 {
  margin-top: 32px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
  position: relative;
}

.markdown-body.enhanced h1 {
  font-size: 2em;
  color: #1a73e8;
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
}

.markdown-body.enhanced h2 {
  font-size: 1.6em;
  color: #1a73e8;
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
}

.markdown-body.enhanced h3 {
  font-size: 1.4em;
  color: #444;
}

.markdown-body.enhanced h4 {
  font-size: 1.2em;
  color: #444;
}

.markdown-body.enhanced h1::before,
.markdown-body.enhanced h2::before {
  content: "";
  position: absolute;
  left: -20px;
  top: 0.3em;
  height: 0.8em;
  width: 4px;
  background-color: #1a73e8;
  border-radius: 4px;
}

.markdown-body.enhanced p {
  margin-top: 0;
  margin-bottom: 20px;
  line-height: 1.8;
  color: #444;
}

.markdown-body.enhanced a {
  color: #1a73e8;
  text-decoration: none;
  border-bottom: 1px dotted #1a73e8;
  transition: all 0.3s ease;
}

.markdown-body.enhanced a:hover {
  color: #0d47a1;
  border-bottom: 1px solid #0d47a1;
}

.markdown-body.enhanced code {
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 90%;
  background-color: rgba(27, 31, 35, 0.05);
  border-radius: 4px;
  font-family: "SFMono-Regular", Consolas, Monaco, "Liberation Mono", "Courier New", monospace;
  color: #d14;
}

.markdown-body.enhanced pre {
  padding: 16px;
  overflow: auto;
  font-size: 90%;
  line-height: 1.45;
  background-color: #f6f8fa;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid #eaecef;
}

.markdown-body.enhanced pre code {
  display: block;
  padding: 0;
  margin: 0;
  overflow: auto;
  line-height: inherit;
  word-wrap: normal;
  background-color: transparent;
  border: 0;
  color: #24292e;
}

.markdown-body.enhanced ul,
.markdown-body.enhanced ol {
  padding-left: 2em;
  margin-top: 0;
  margin-bottom: 20px;
}

.markdown-body.enhanced ul {
  list-style-type: disc;
}

.markdown-body.enhanced ol {
  list-style-type: decimal;
}

.markdown-body.enhanced li {
  margin-bottom: 8px;
  line-height: 1.8;
}

.markdown-body.enhanced li + li {
  margin-top: 0.25em;
}

.markdown-body.enhanced blockquote {
  margin: 0 0 20px 0;
  padding: 12px 20px;
  color: #444;
  border-left: 4px solid #1a73e8;
  background-color: #f8f9fa;
  border-radius: 4px;
  font-style: italic;
}

.markdown-body.enhanced blockquote > :first-child {
  margin-top: 0;
}

.markdown-body.enhanced blockquote > :last-child {
  margin-bottom: 0;
}

.markdown-body.enhanced table {
  border-spacing: 0;
  border-collapse: collapse;
  margin-bottom: 20px;
  width: 100%;
  overflow: auto;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border-radius: 8px;
}

.markdown-body.enhanced table th,
.markdown-body.enhanced table td {
  padding: 10px 16px;
  border: 1px solid #eaecef;
}

.markdown-body.enhanced table th {
  font-weight: 600;
  background-color: #f8f9fa;
  color: #24292e;
  text-align: left;
}

.markdown-body.enhanced table tr {
  background-color: #fff;
  border-top: 1px solid #eaecef;
}

.markdown-body.enhanced table tr:nth-child(2n) {
  background-color: #f8f9fa;
}

.markdown-body.enhanced img {
  max-width: 100%;
  box-sizing: content-box;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  margin: 12px 0;
}

.markdown-body.enhanced hr {
  height: 2px;
  padding: 0;
  margin: 24px 0;
  background-color: #eaecef;
  border: 0;
  border-radius: 2px;
}

/* 优化代码块语法高亮部分的样式 */
.markdown-body.enhanced .hljs {
  display: block;
  overflow-x: auto;
  padding: 0.5em;
  color: #333;
  background: #f8f8f8;
}

/* 对话框样式优化 */
.details-dialog :deep(.el-dialog__body) {
  padding: 0;
  overflow: auto;
}

.details-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #1a73e8, #6c5ce7);
  padding: 16px 20px;
}

.details-dialog :deep(.el-dialog__title) {
  color: white;
  font-weight: 600;
  font-size: 18px;
}

.details-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: rgba(255, 255, 255, 0.9);
}

.details-dialog :deep(.el-dialog__headerbtn:hover .el-dialog__close) {
  color: white;
}

/* 空内容提示样式优化 */
.empty-content {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  font-size: 16px;
  color: #909399;
  background-color: #f5f7fa;
  border-radius: 8px;
  min-height: 200px;
}
</style>
