<template>
  <div class="call-chain-graph">
    <v-chart class="chart" :option="option" autoresize />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import VChart from 'vue-echarts'
import * as echarts from 'echarts'

const props = defineProps({
  stackTrace: {
    type: String,
    required: true
  }
})

const chartInstance = ref(null)

const option = ref({
  tooltip: {
    trigger: 'item',
    triggerOn: 'mousemove',
    formatter: params => {
      return params.data.tooltip || params.name
    }
  },
  series: [{
    type: 'graph',
    layout: 'force',
    animation: true,
    label: {
      show: true,
      position: 'right',
      formatter: '{b}',
      fontSize: 12,
      color: '#333'
    },
    draggable: true,
    data: [],
    links: [],
    force: {
      repulsion: 200,
      gravity: 0.1,
      edgeLength: 100,
      layoutAnimation: true
    },
    lineStyle: {
      color: '#4A90E2',
      curveness: 0.3,
      width: 2,
      opacity: 0.6,
      type: 'solid'
    },
    itemStyle: {
      color: '#95D475',
      borderColor: '#fff',
      borderWidth: 2,
      shadowColor: 'rgba(0, 0, 0, 0.3)',
      shadowBlur: 10
    },
    emphasis: {
      focus: 'adjacency',
      lineStyle: {
        width: 4,
        opacity: 1
      },
      itemStyle: {
        color: '#FF9F43'
      },
      label: {
        fontSize: 14,
        fontWeight: 'bold'
      }
    },
    roam: true,
    zoom: 0.8,
    nodeSize: 30,
    edgeSymbol: ['circle', 'arrow'],
    edgeSymbolSize: [4, 10]
  }]
})

const setFullView = () => {
  if (chartInstance.value) {
    chartInstance.value.resize()
    chartInstance.value.dispatchAction({
      type: 'restore'
    })
  }
}

onMounted(() => {
  chartInstance.value = echarts.init(document.querySelector('.chart'))
  chartInstance.value.setOption(option.value)
  setFullView()
})

// 解析堆栈信息并生成图数据
const parseStackTrace = (stackTrace) => {
  if (!stackTrace) return { nodes: [], links: [] }
  
  const lines = stackTrace.split('\n').filter(line => line.includes('at'))
  const nodes = []
  const links = []
  
  lines.forEach((line, index) => {
    const match = line.match(/at\s+([^(]+)\(([^)]+)\)/)
    if (match) {
      const [_, method, location] = match
      nodes.push({
        id: index,
        name: method.trim(),
        value: 30,
        symbolSize: 50,
        category: 0,
        tooltip: {
          formatter: `<div style="font-weight:bold">${method.trim()}</div><div>${location}</div>`
        }
      })
      
      if (index > 0) {
        links.push({
          source: index - 1,
          target: index,
          value: 1
        })
      }
    }
  })
  
  return { nodes, links }
}

// 监听堆栈信息变化
watch(() => props.stackTrace, (newValue) => {
  if (newValue) {
    const { nodes, links } = parseStackTrace(newValue)
    option.value.series[0].data = nodes
    option.value.series[0].links = links
    setFullView()
  }
}, { immediate: true })
</script>

<style scoped>
.call-chain-graph {
  width: 100%;
  height: 500px;
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-sizing: border-box;
}

.chart {
  width: 100%;
  height: 100%;
}
</style> 