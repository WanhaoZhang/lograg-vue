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
      width="60%"
    >
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

const serviceOptions = [
  { label: 'OpenStack服务', value: 'openstack-service' },
  { label: '用户服务', value: 'user-service' },
  { label: '订单服务', value: 'order-service' },
  { label: '支付服务', value: 'payment-service' }
]

const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const logList = ref([])
const detailsVisible = ref(false)
const currentLog = ref({})

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
    const details = await logService.getLogDetails(log.id)
    currentLog.value = {
      ...log,
      aiSummary: details.aiSummary,
      callStack: details.callStack
    }
    detailsVisible.value = true
  } catch (error) {
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

// 页面加载时自动查询
onMounted(() => {
  handleQuery()
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
</style> 