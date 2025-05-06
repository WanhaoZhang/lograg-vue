<template>
  <div class="log-analysis-container">
    <!-- 查询条件卡片 -->
    <el-card class="query-card">
      <div class="query-form">
        <el-form :model="queryForm" inline>
          <el-form-item label="服务选择">
            <el-select v-model="queryForm.service" placeholder="请选择服务">
              <el-option
                v-for="item in serviceOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
          
          <el-form-item label="时间范围">
            <el-radio-group v-model="queryForm.timeRange">
              <el-radio-button label="1">最近一天</el-radio-button>
              <el-radio-button label="7">最近一周</el-radio-button>
              <el-radio-button label="30">最近一月</el-radio-button>
            </el-radio-group>
          </el-form-item>
          
          <el-form-item>
            <el-button type="primary" @click="handleQuery">查询</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <!-- 日志列表卡片 -->
    <el-card class="log-list-card">
      <template #header>
        <div class="card-header">
          <span>异常日志列表</span>
        </div>
      </template>
      
      <el-table :data="logList" style="width: 100%">
        <el-table-column prop="timestamp" label="时间" width="180" />
        <el-table-column prop="service" label="服务" width="120" />
        <el-table-column prop="level" label="级别" width="100">
          <template #default="scope">
            <el-tag :type="getLogLevelType(scope.row.level)">
              {{ scope.row.level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="错误信息" />
        <el-table-column fixed="right" label="操作" width="120">
          <template #default="scope">
            <el-button link type="primary" @click="showDetails(scope.row)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailsVisible"
      title="日志详情"
      width="80%"
    >
      <el-tabs>
        <el-tab-pane label="分析摘要">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="AI分析摘要">
              {{ currentLog.aiSummary }}
            </el-descriptions-item>
            <el-descriptions-item label="调用链信息">
              <div class="call-stack">
                {{ currentLog.callStack }}
              </div>
            </el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>
        
        <el-tab-pane label="详细分析">
          <el-card class="analysis-card" v-if="currentLog.analysis">
            <h3>根本原因分析</h3>
            <el-timeline>
              <el-timeline-item
                v-for="(cause, index) in currentLog.analysis.rootCauses"
                :key="index"
                type="primary"
              >
                <h4>{{ cause.title || '原因 ' + (index + 1) }}</h4>
                <p>{{ cause.description }}</p>
              </el-timeline-item>
            </el-timeline>
            
            <h3>解决方案建议</h3>
            <el-collapse>
              <el-collapse-item 
                v-for="(solution, index) in currentLog.analysis.solutions" 
                :key="index" 
                :title="getSolutionTitle(solution)"
              >
                {{ solution.description }}
              </el-collapse-item>
            </el-collapse>
          </el-card>
          <el-empty v-else description="没有找到详细分析信息" />
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { logService } from '@/api/logService'

const queryForm = reactive({
  service: '',
  timeRange: '1'
})

const serviceOptions = ref([
  { label: '加载中...', value: '' }
])

const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const logList = ref([])
const detailsVisible = ref(false)
const currentLog = ref({})

// 获取服务列表
const fetchServices = async () => {
  try {
    const services = await logService.getServices()
    serviceOptions.value = services
    
    // 如果有'test'服务，默认选择它
    const testService = services.find(service => service.value === 'test')
    if (testService && !queryForm.service) {
      queryForm.service = 'test'
      handleQuery()
    }
  } catch (error) {
    ElMessage.error('获取服务列表失败：' + error.message)
  }
}

const handleQuery = async () => {
  try {
    // 计算时间范围
    const now = new Date();
    const days = parseInt(queryForm.timeRange);
    const startTime = new Date(now);
    startTime.setDate(now.getDate() - days);
    
    const params = {
      service: queryForm.service,
      timeRange: [startTime, now], // 使用时间范围对象
      page: currentPage.value,
      pageSize: pageSize.value
    }
    
    console.log('查询参数:', params); // 添加日志
    
    const result = await logService.queryLogs(params)
    logList.value = result.data
    total.value = result.total
  } catch (error) {
    ElMessage.error('查询失败：' + error.message)
  }
}

const handlePageChange = (page) => {
  currentPage.value = page
  handleQuery()
}

const showDetails = async (log) => {
  try {
    // 先获取日志详情
    const details = await logService.getLogDetails(log.id)
    
    // 初始化当前日志数据
    currentLog.value = {
      ...details,
      aiSummary: details.analysis?.summary || details.summary || '没有分析摘要',
      callStack: details.stackTrace || '没有调用堆栈信息'
    }
    
    // 如果没有analysis数据，尝试从专门的API获取
    if (!details.analysis && log.service === 'test') {
      const analysisData = await logService.getLogAnalysis(log.id)
      currentLog.value.analysis = analysisData
      currentLog.value.aiSummary = analysisData.summary || currentLog.value.aiSummary
    }
    
    console.log('当前日志详情:', currentLog.value);
    detailsVisible.value = true
  } catch (error) {
    console.error('获取详情失败:', error);
    ElMessage.error('获取详情失败：' + error.message)
  }
}

const getLogLevelType = (level) => {
  const types = {
    ERROR: 'danger',
    WARN: 'warning',
    INFO: 'info'
  }
  return types[level] || 'info'
}

const getSolutionTitle = (solution) => {
  const typeLabels = {
    'shortTerm': '短期解决方案',
    'longTerm': '长期优化策略',
    'general': '一般建议'
  }
  return typeLabels[solution.type] || '解决方案'
}

// 页面加载时获取服务列表和日志
onMounted(() => {
  fetchServices()
})
</script>

<style scoped>
.log-analysis-container {
  padding: 20px;
}

.query-card {
  margin-bottom: 20px;
}

.query-form {
  display: flex;
  justify-content: flex-start;
  align-items: center;
}

.log-list-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.call-stack {
  white-space: pre-wrap;
  font-family: monospace;
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
}

.analysis-card {
  margin-bottom: 20px;
}

.analysis-card h3 {
  margin-top: 20px;
  margin-bottom: 10px;
  font-weight: 600;
  color: #409EFF;
}

.el-timeline-item h4 {
  font-weight: 600;
  margin-bottom: 5px;
}

.el-collapse-item {
  margin-bottom: 5px;
}
</style> 