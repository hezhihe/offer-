import { defineStore } from 'pinia'
import { ref } from 'vue'
import { jobsApi } from '../api/jobs'

export const useJobsStore = defineStore('jobs', () => {
  const jobs = ref([])
  const allJobs = ref([])
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
  const tips = ref([])
  const currentTipIndex = ref(0)
  const stats = ref({ resume: 0, interview: 0, browse: 0 })
  const browseHistory = ref(JSON.parse(localStorage.getItem('offer_compass_job_browse_history') || '[]'))
  const currentEducation = ref('all')
  const showExpiredJobs = ref(false)
  let jobsPromise = null
  let tipsPromise = null
  let statsPromise = null
  let statsFetchedAt = 0

  async function fetchJobs(category, education) {
    currentFilter.value = category || currentFilter.value
    currentEducation.value = education || currentEducation.value

    if (allJobs.value.length > 0) {
      applyJobFilters()
      return
    }

    if (!jobsPromise) {
      jobsPromise = jobsApi.getList('all', 'all', showExpiredJobs.value)
        .then(response => {
          allJobs.value = response.data
        })
        .catch(() => {
          allJobs.value = getMockJobs()
        })
        .finally(() => {
          jobsPromise = null
        })
    }
    await jobsPromise
    applyJobFilters()
  }

  async function fetchTodayTip() {
    if (tips.value.length) {
      todayTip.value = tips.value[currentTipIndex.value] || ''
      return
    }
    if (!tipsPromise) {
      tipsPromise = jobsApi.getTips()
        .then(response => {
          tips.value = response.data.tips || []
        })
        .catch(() => {
          tips.value = getMockTips()
        })
        .finally(() => {
          currentTipIndex.value = getInitialTipIndex()
          todayTip.value = tips.value[currentTipIndex.value] || ''
          tipsPromise = null
        })
    }
    await tipsPromise
  }

  function getInitialTipIndex() {
    const listLength = tips.value.length || 1
    return new Date().getDate() % listLength
  }

  function switchTip(step = 1) {
    if (tips.value.length <= 1) {
      tips.value = getMockTips()
      const currentIndex = tips.value.findIndex(item => item === todayTip.value)
      currentTipIndex.value = currentIndex >= 0 ? currentIndex : getInitialTipIndex()
    }
    if (tips.value.length === 0) return
    currentTipIndex.value = (currentTipIndex.value + step + tips.value.length) % tips.value.length
    todayTip.value = tips.value[currentTipIndex.value]
  }

  async function fetchStats() {
    const now = Date.now()
    if (statsPromise) return statsPromise
    if (now - statsFetchedAt < 30000) return

    statsPromise = jobsApi.getStats()
      .then(response => {
        const serverData = response.data
        const localData = JSON.parse(localStorage.getItem('offer_compass_stats') || '{}')
        stats.value = {
          resume: serverData.resume || 0,
          interview: serverData.interview || 0,
          browse: localData.browse || stats.value.browse || 0
        }
        statsFetchedAt = Date.now()
      })
      .catch(() => {
        stats.value = JSON.parse(localStorage.getItem('offer_compass_stats') || '{"resume":0,"interview":0,"browse":0}')
      })
      .finally(() => {
        statsPromise = null
      })
    return statsPromise
  /*
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
  */
  }

  function filterJobs(category) {
    currentFilter.value = category
    applyJobFilters()
  }

  function filterByEducation(education) {
    currentEducation.value = education || 'all'
    applyJobFilters()
  }

  function applyJobFilters() {
    jobs.value = allJobs.value.filter(job => {
      const categoryMatched = currentFilter.value === 'all' || job.category === currentFilter.value
      const educationMatched = canApplyByEducation(job.education, currentEducation.value)
      const statusMatched = showExpiredJobs.value || !isInactiveJob(job)
      return categoryMatched && educationMatched && statusMatched
    })
  }

  async function setShowExpiredJobs(value) {
    showExpiredJobs.value = Boolean(value)
    allJobs.value = []
    await fetchJobs(currentFilter.value, currentEducation.value)
  }

  function isInactiveJob(job) {
    return job?.status === 'expired' || job?.status === 'closed' || job?.isExpired
  }

  function canApplyByEducation(jobEducation = '不限', userEducation = 'all') {
    if (userEducation === 'all') return true

    const rankMap = {
      不限: 0,
      专科及以上: 1,
      大专及以上: 1,
      本科及以上: 2,
      硕士及以上: 3,
      博士及以上: 4
    }
    const userRankMap = {
      专科: 1,
      本科: 2,
      硕士: 3,
      博士: 4
    }
    const requiredRank = rankMap[jobEducation] ?? 0
    const userRank = userRankMap[userEducation] ?? 0
    return requiredRank <= userRank
  }

  function switchView(view) {
    currentView.value = view
  }

  function selectJob(job) {
    selectedJob.value = job
    if (job) {
      stats.value.browse++
      addBrowseHistory(job)
      saveStats()
    }
  }

  function addBrowseHistory(job) {
    const record = {
      id: job.id,
      company: job.company || '',
      title: job.title || '',
      date: job.date || '',
      salary: job.salary || '',
      category: job.category || '',
      capital: job.capital || '',
      education: job.education || '',
      requirements: job.requirements || '',
      womenFriendly: Boolean(job.womenFriendly),
      url: job.url || '',
      viewedAt: new Date().toISOString()
    }
    browseHistory.value = [
      record,
      ...browseHistory.value.filter(item => item.id !== job.id)
    ].slice(0, 20)
    localStorage.setItem('offer_compass_job_browse_history', JSON.stringify(browseHistory.value))
  }

  function saveStats() {
    localStorage.setItem('offer_compass_stats', JSON.stringify(stats.value))
  }

  function getMockJobs() {
    return [
      { id: 1, company: '优必选科技', title: '机器人算法工程师', date: '2026-06-15', salary: '15K-25K', category: 'robot', capital: '上市机器人企业', education: '硕士及以上', requirements: '硕士及以上，机器人/自动化相关专业，熟悉ROS、运动控制算法', womenFriendly: false, url: 'https://www.ubtrobot.com' },
      { id: 2, company: '大疆创新', title: '低空经济运营专员', date: '2026-06-20', salary: '12K-20K', category: 'lowAltitude', capital: '大型科技企业', education: '本科及以上', requirements: '本科及以上，航空管理/交通运输相关专业，了解低空政策法规', womenFriendly: true, url: 'https://we.dji.com' },
      { id: 3, company: '宁德时代', title: '新材料研发工程师', date: '2026-07-01', salary: '18K-30K', category: 'material', capital: '头部新能源企业', education: '硕士及以上', requirements: '硕士及以上，材料科学/化学工程，有电池材料研究经验优先', womenFriendly: true, url: 'https://www.catl.com' },
      { id: 4, company: '商汤科技', title: 'AI算法工程师', date: '2026-06-10', salary: '20K-35K', category: 'ai', capital: '上市AI企业', education: '硕士及以上', requirements: '硕士及以上，计算机/AI相关专业，熟悉PyTorch、深度学习框架', womenFriendly: false, url: 'https://www.sensetime.com' },
      { id: 5, company: '比亚迪', title: '新能源系统工程师', date: '2026-07-15', salary: '15K-25K', category: 'energy', capital: '头部车企', education: '本科及以上', requirements: '本科及以上，电气工程/自动化，了解BMS系统开发', womenFriendly: true, url: 'https://www.byd.com' },
      { id: 6, company: '云从科技', title: 'AI产品经理', date: '2026-06-25', salary: '15K-22K', category: 'ai', capital: '上市AI企业', education: '本科及以上', requirements: '本科及以上，有AI产品0-1经验，了解大模型应用场景', womenFriendly: true, url: 'https://www.cloudwalk.cn' },
      { id: 7, company: '埃斯顿自动化', title: '机器人控制工程师', date: '2026-07-10', salary: '12K-20K', category: 'robot', capital: '上市自动化企业', education: '本科及以上', requirements: '本科及以上，自动化/控制工程，熟悉PLC、伺服控制', womenFriendly: false, url: 'https://www.estun.com' },
      { id: 8, company: '亿航智能', title: '低空经济产品经理', date: '2026-06-30', salary: '15K-25K', category: 'lowAltitude', capital: '上市eVTOL企业', education: '本科及以上', requirements: '本科及以上，有出行/航空产品经验，了解eVTOL行业', womenFriendly: false, url: 'https://www.ehang.com' },
      { id: 9, company: '光威复材', title: '新材料测试工程师', date: '2026-07-20', salary: '10K-18K', category: 'material', capital: '上市新材料企业', education: '本科及以上', requirements: '本科及以上，材料/化工专业，熟悉碳纤维复合材料测试标准', womenFriendly: true, url: 'https://www.gwcomposites.com' },
      { id: 10, company: '科大讯飞', title: 'AI语音算法工程师', date: '2026-06-18', salary: '18K-30K', category: 'ai', capital: '上市AI企业', education: '硕士及以上', requirements: '硕士及以上，语音信号处理/自然语言处理，有语音合成经验优先', womenFriendly: false, url: 'https://www.iflytek.com' },
      { id: 11, company: '小鹏汇天', title: '低空飞行器工程师', date: '2026-07-05', salary: '20K-35K', category: 'lowAltitude', capital: '成长型飞行汽车企业', education: '硕士及以上', requirements: '硕士及以上，航空航天/飞行器设计，了解eVTOL适航标准', womenFriendly: false, url: 'https://www.xpeng.com' },
      { id: 12, company: '天合光能', title: '新能源光伏工程师', date: '2026-06-28', salary: '12K-22K', category: 'energy', capital: '上市新能源企业', education: '本科及以上', requirements: '本科及以上，光伏/半导体相关专业，了解HJT电池技术', womenFriendly: true, url: 'https://www.trinasolar.com' },
      { id: 13, company: '顺丰无人机', title: '低空运维助理', date: '2026-07-08', salary: '7K-12K', category: 'lowAltitude', capital: '大型物流集团业务', education: '专科及以上', requirements: '专科及以上，机电/航空服务/物流相关专业，能配合现场巡检和飞行任务记录', womenFriendly: true, url: 'https://www.sf-express.com' },
      { id: 14, company: '新松机器人', title: '机器人装调技术员', date: '2026-07-18', salary: '8K-13K', category: 'robot', capital: '上市机器人企业', education: '专科及以上', requirements: '专科及以上，机电一体化/自动化相关专业，熟悉基础电气装配和设备调试', womenFriendly: false, url: 'https://www.siasun.com' }
    ]
  }

  function getMockTips() {
    return [
      '🔰 面试开场：「请做个自我介绍」→ 用「我是谁 + 我为什么适合 + 我为什么想来」三段式，60秒搞定。',
      '💬 遇到不会的问题：别硬编！先说「这个问题我目前经验有限」，然后展示你的学习思路。',
      '⚡ 面试中大脑空白？停下来喝口水，说「让我想一想」，3秒的停顿能让你重新组织语言。',
      '🎮 把面试当成游戏副本：你是主角，面试官是NPC，任务是解锁对话、收集情报。',
      '😌 面试前紧张？试试「4-7-8呼吸法」：吸气4秒 → 屏息7秒 → 缓呼8秒，重复3次。',
    ]
}
  return {
    jobs,
    allJobs,
    categories,
    categoryNames,
    currentFilter,
    currentEducation,
    currentView,
    selectedJob,
    todayTip,
    tips,
    currentTipIndex,
    stats,
    browseHistory,
    showExpiredJobs,
    fetchJobs,
    setShowExpiredJobs,
    filterByEducation,
    fetchTodayTip,
    switchTip,
    fetchStats,
    filterJobs,
    switchView,
    selectJob,
    saveStats
  }
})
