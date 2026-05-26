import { defineStore } from 'pinia'
import { ref } from 'vue'
import { jobsApi } from '../api/jobs'

export const useJobsStore = defineStore('jobs', () => {
  const jobs = ref([])
  const categories = ref(['all', 'robot', 'material', 'lowAltitude', 'ai', 'energy'])
  const categoryNames = {
    robot: '🤖 机器人',
    material: '🔬 新材料',
    lowAltitude: '🛸 低空经济',
    ai: '🧠 AI',
    energy: '⚡ 新能源',
    all: '全部'
  }
  const currentFilter = ref('all')
  const currentView = ref('list')
  const selectedJob = ref(null)
  const todayTip = ref('')
  const stats = ref({ resume: 0, interview: 0, browse: 0 })

  async function fetchJobs(category, education) {
    try {
      const cat = category || currentFilter.value
      const edu = education || 'all'
      const response = await jobsApi.getList(cat, edu)
      jobs.value = response.data
    } catch {
      jobs.value = getMockJobs()
    }
  }

  async function fetchTodayTip() {
    try {
      const response = await jobsApi.getTodayTip()
      todayTip.value = response.data.content
    } catch {
      todayTip.value = getMockTip()
    }
  }

  async function fetchStats() {
    try {
      const response = await jobsApi.getStats()
      const serverData = response.data
      // 后端返回 resume/interview 真实数据，browse 由前端 localStorage 管理
      const localData = JSON.parse(localStorage.getItem('offer_compass_stats') || '{}')
      stats.value = {
        resume: serverData.resume || 0,
        interview: serverData.interview || 0,
        browse: localData.browse || stats.value.browse || 0
      }
    } catch {
      stats.value = JSON.parse(localStorage.getItem('offer_compass_stats') || '{"resume":0,"interview":0,"browse":0}')
    }
  }

  function filterJobs(category) {
    currentFilter.value = category
    fetchJobs()
  }

  function switchView(view) {
    currentView.value = view
  }

  function selectJob(job) {
    selectedJob.value = job
    if (job) {
      stats.value.browse++
      saveStats()
    }
  }

  function saveStats() {
    localStorage.setItem('offer_compass_stats', JSON.stringify(stats.value))
  }

  function getMockJobs() {
    return [
      { id: 1, company: '优必选科技', title: '机器人算法工程师', date: '2026-06-15', salary: '15K-25K', category: 'robot', capital: '5亿+', requirements: '硕士及以上，机器人/自动化相关专业，熟悉ROS、运动控制算法', womenFriendly: false, url: 'https://www.ubtrobot.com' },
      { id: 2, company: '大疆创新', title: '低空经济运营专员', date: '2026-06-20', salary: '12K-20K', category: 'lowAltitude', capital: '10亿+', requirements: '本科及以上，航空管理/交通运输相关专业，了解低空政策法规', womenFriendly: true, url: 'https://we.dji.com' },
      { id: 3, company: '宁德时代', title: '新材料研发工程师', date: '2026-07-01', salary: '18K-30K', category: 'material', capital: '100亿+', requirements: '硕士及以上，材料科学/化学工程，有电池材料研究经验优先', womenFriendly: true, url: 'https://www.catl.com' },
      { id: 4, company: '商汤科技', title: 'AI算法工程师', date: '2026-06-10', salary: '20K-35K', category: 'ai', capital: '50亿+', requirements: '硕士及以上，计算机/AI相关专业，熟悉PyTorch、深度学习框架', womenFriendly: false, url: 'https://www.sensetime.com' },
      { id: 5, company: '比亚迪', title: '新能源系统工程师', date: '2026-07-15', salary: '15K-25K', category: 'energy', capital: '200亿+', requirements: '本科及以上，电气工程/自动化，了解BMS系统开发', womenFriendly: true, url: 'https://www.byd.com' },
      { id: 6, company: '云从科技', title: 'AI产品经理', date: '2026-06-25', salary: '15K-22K', category: 'ai', capital: '10亿+', requirements: '本科及以上，有AI产品0-1经验，了解大模型应用场景', womenFriendly: true, url: 'https://www.cloudwalk.cn' },
      { id: 7, company: '埃斯顿自动化', title: '机器人控制工程师', date: '2026-07-10', salary: '12K-20K', category: 'robot', capital: '20亿+', requirements: '本科及以上，自动化/控制工程，熟悉PLC、伺服控制', womenFriendly: false, url: 'https://www.estun.com' },
      { id: 8, company: '亿航智能', title: '低空经济产品经理', date: '2026-06-30', salary: '15K-25K', category: 'lowAltitude', capital: '5亿+', requirements: '本科及以上，有出行/航空产品经验，了解eVTOL行业', womenFriendly: false, url: 'https://www.ehang.com' },
      { id: 9, company: '光威复材', title: '新材料测试工程师', date: '2026-07-20', salary: '10K-18K', category: 'material', capital: '15亿+', requirements: '本科及以上，材料/化工专业，熟悉碳纤维复合材料测试标准', womenFriendly: true, url: 'https://www.gwcomposites.com' },
      { id: 10, company: '科大讯飞', title: 'AI语音算法工程师', date: '2026-06-18', salary: '18K-30K', category: 'ai', capital: '30亿+', requirements: '硕士及以上，语音信号处理/自然语言处理，有语音合成经验优先', womenFriendly: false, url: 'https://www.iflytek.com' },
      { id: 11, company: '小鹏汇天', title: '低空飞行器工程师', date: '2026-07-05', salary: '20K-35K', category: 'lowAltitude', capital: '10亿+', requirements: '硕士及以上，航空航天/飞行器设计，了解eVTOL适航标准', womenFriendly: false, url: 'https://www.xpeng.com' },
      { id: 12, company: '天合光能', title: '新能源光伏工程师', date: '2026-06-28', salary: '12K-22K', category: 'energy', capital: '50亿+', requirements: '本科及以上，光伏/半导体相关专业，了解HJT电池技术', womenFriendly: true, url: 'https://www.trinasolar.com' }
    ]
  }

  function getMockTip() {
    const tips = [
      '🔰 面试开场：「请做个自我介绍」→ 用「我是谁 + 我为什么适合 + 我为什么想来」三段式，60秒搞定。',
      '💬 遇到不会的问题：别硬编！先说「这个问题我目前经验有限」，然后展示你的学习思路。',
      '⚡ 面试中大脑空白？停下来喝口水，说「让我想一想」，3秒的停顿能让你重新组织语言。',
      '🎮 把面试当成游戏副本：你是主角，面试官是NPC，任务是解锁对话、收集情报。',
      '😌 面试前紧张？试试「4-7-8呼吸法」：吸气4秒 → 屏息7秒 → 缓呼8秒，重复3次。',
    ]
    return tips[new Date().getDate() % tips.length]
}
  return {
    jobs,
    categories,
    categoryNames,
    currentFilter,
    currentView,
    selectedJob,
    todayTip,
    stats,
    fetchJobs,
    fetchTodayTip,
    fetchStats,
    filterJobs,
    switchView,
    selectJob,
    saveStats
  }
})