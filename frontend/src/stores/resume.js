import { defineStore } from 'pinia'
import { ref } from 'vue'
import { resumeApi } from '../api/resume'

export const useResumeStore = defineStore('resume', () => {
  const jdContent = ref('')
  const experience = ref('')
  const result = ref(null)
  const isAnalyzing = ref(false)
  const history = ref([])
  const historyDetail = ref(null)
  const isLoadingDetail = ref(false)
  let historyPromise = null
  let historyFetchedAt = 0

  async function analyze() {
    if (!jdContent.value || !experience.value) return
    isAnalyzing.value = true
    try {
      const response = await resumeApi.analyze(jdContent.value, experience.value)
      result.value = response.data
      return response.data
    } finally {
      isAnalyzing.value = false
    }
  }

  async function fetchHistory() {
    const now = Date.now()
    if (historyPromise) return historyPromise
    if (history.value.length && now - historyFetchedAt < 30000) return

    historyPromise = resumeApi.getHistory()
      .then(response => {
        history.value = response.data
        historyFetchedAt = Date.now()
      })
      .catch(() => {
        history.value = []
      })
      .finally(() => {
        historyPromise = null
      })
    return historyPromise
  }

  async function fetchHistoryDetail(id) {
    if (!id) return null
    historyDetail.value = null
    isLoadingDetail.value = true
    try {
      const response = await resumeApi.getById(id)
      historyDetail.value = response.data
      return response.data
    } finally {
      isLoadingDetail.value = false
    }
  }

  function clearHistoryDetail() {
    historyDetail.value = null
  }

  function fillSampleData() {
    jdContent.value = `【机器人算法工程师】

岗位职责：
1. 负责移动机器人导航算法的研发与优化，包括SLAM、路径规划等
2. 参与机器人感知系统的开发，包括视觉识别、激光雷达数据处理
3. 优化机器人运动控制算法，提升运动精度和稳定性
4. 编写技术文档，与硬件团队协作完成系统集成

任职要求：
1. 硕士及以上学历，机器人/自动化/计算机相关专业
2. 熟悉ROS/ROS2框架，有实际项目经验
3. 掌握C++/Python，具备良好的编程能力
4. 了解SLAM、运动规划、计算机视觉等至少一个方向
5. 有机器人竞赛或实习经验优先`

    experience.value = `张三 | 2026届硕士 | 控制科学与工程

教育背景：
- XX大学 控制科学与工程 硕士（2023-2026）
- XX大学 自动化 本科（2019-2023）

项目经验：
1. 校园导览机器人项目（2024.03-2024.12）
   - 使用ROS框架搭建机器人软件系统
   - 实现基于激光雷达的SLAM建图功能
   - 开发A*路径规划算法，导航精度达5cm

2. 智能小车视觉追踪系统（2023.09-2024.02）
   - 基于OpenCV实现目标检测与追踪
   - 使用Python开发控制逻辑
   - 获校级创新创业大赛二等奖

技能：
- 编程：C++、Python、MATLAB
- 工具：ROS、OpenCV、Git
- 英语：CET-6 520分`
  }

  function clear() {
    jdContent.value = ''
    experience.value = ''
    result.value = null
  }

  return { jdContent, experience, result, isAnalyzing, history, historyDetail, isLoadingDetail, analyze, fetchHistory, fetchHistoryDetail, clearHistoryDetail, fillSampleData, clear }
})
