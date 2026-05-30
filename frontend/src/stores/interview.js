import { defineStore } from 'pinia'
import { ref } from 'vue'
import { interviewApi } from '../api/interview'

export const useInterviewStore = defineStore('interview', () => {
  const jobType = ref('')
  const questions = ref([])
  const currentQuestionIndex = ref(0)
  const answers = ref([])
  const scores = ref([])
  const feedbacks = ref([])
  const interviewId = ref(null)
  const isStarting = ref(false)
  const isAnswering = ref(false)
  const isCompleted = ref(false)
  const report = ref(null)
  const history = ref([])
  const historyDetail = ref(null)
  const isLoadingDetail = ref(false)
  const answerError = ref('')
  let historyPromise = null
  let historyFetchedAt = 0

  const jobTypeNames = {
    robot: '机器人工程师',
    ai: 'AI算法工程师',
    lowAltitude: '低空经济运营',
    material: '新材料研发',
    pm: '产品经理'
  }

  async function start(jobTypeVal) {
    isStarting.value = true
    jobType.value = jobTypeVal
    isCompleted.value = false
    currentQuestionIndex.value = 0
    answers.value = []
    scores.value = []
    feedbacks.value = []
    report.value = null
    answerError.value = ''

    try {
      const response = await interviewApi.start(jobTypeVal)
      questions.value = response.data.questions
      interviewId.value = response.data.id
      return response.data
    } catch {
      questions.value = getModernMockQuestions(jobTypeVal)
      interviewId.value = 'mock-' + Date.now()
    } finally {
      isStarting.value = false
    }
  }

  async function answer(answerText) {
    if (!answerText.trim()) return
    isAnswering.value = true
    answerError.value = ''

    try {
      const response = await interviewApi.answer(interviewId.value, currentQuestionIndex.value, answerText)
      answers.value.push(answerText)
      scores.value.push(response.data.score)
      feedbacks.value.push(response.data.feedback)
      if (response.data.next_question) {
        questions.value.push(response.data.next_question)
      }
      currentQuestionIndex.value++
      return response.data
    } catch (error) {
      const detail = error.response?.data?.detail
      answerError.value = detail === 'Interview not found'
        ? '当前面试会话已失效，通常是后端重启或热更新导致，请退出后重新开始一轮。'
        : `AI 评分服务暂时不可用，请稍后重试。${detail ? `原因：${detail}` : ''}`
      throw error
    } finally {
      isAnswering.value = false
    }
  }

  async function complete() {
    try {
      const response = await interviewApi.complete(interviewId.value)
      report.value = response.data
    } catch {
      report.value = generateMockReport()
    }
    isCompleted.value = true
    return report.value
  }

  function reset() {
    jobType.value = ''
    questions.value = []
    currentQuestionIndex.value = 0
    answers.value = []
    scores.value = []
    feedbacks.value = []
    interviewId.value = null
    isCompleted.value = false
    report.value = null
    answerError.value = ''
  }

  async function fetchHistory() {
    const now = Date.now()
    if (historyPromise) return historyPromise
    if (history.value.length && now - historyFetchedAt < 30000) return

    historyPromise = interviewApi.getHistory()
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
      const response = await interviewApi.getById(id)
      historyDetail.value = response.data
      return response.data
    } finally {
      isLoadingDetail.value = false
    }
  }

  function clearHistoryDetail() {
    historyDetail.value = null
  }

  function getLocalFollowUp(type, answerText, turn) {
    if (answerText.trim().length < 50) {
      return '你的回答还比较概括。请补充一个真实项目：你负责什么、怎么做、结果如何验证？'
    }
    const followUps = {
      robot: ['你刚才提到项目落地，真实设备上最难复现的问题是什么？', '如果要上线，你会用哪些指标证明稳定性和安全边界？', '这部分工作里你个人贡献和团队协作边界分别是什么？'],
      ai: ['你刚才提到项目效果，评测集怎么构建，怎样确认优化真的有效？', '如果线上质量、时延和成本同时受压，你会先做哪两个取舍？', '这部分工作里你亲自负责的数据、模型和工程环节分别是什么？'],
      lowAltitude: ['你刚才提到运营方案，遇到现场异常时你会怎样做预案和复盘？', '这条航线试运营时，你会看哪些数据决定是否继续扩量？', '这里最关键的合规或跨部门协同点是什么？'],
      material: ['你刚才提到实验结论，怎样排除测试条件变化造成的假提升？', '如果从小试走向放大，你最担心哪类波动？', '这项工作里你亲自做了哪些实验设计和数据判断？'],
      pm: ['你刚才提到方案价值，请说出核心用户问题、关键指标和一次重要取舍。', '如果模型能力有波动，你会怎样设计兜底交互和上线门槛？', '你怎样验证这不是伪需求？']
    }
    const options = followUps[type] || followUps.ai
    return options[(turn - 2) % options.length]
  }

  function getModernMockQuestions(type) {
    const pools = {
      robot: [
        ['请用 60 秒介绍一个最能证明你适合机器人岗位的项目，并说清你负责的模块和结果。', '机器人项目跨算法、硬件和现场调试。你最近一次把问题定位到根因的过程是什么？'],
        ['在 ROS2 系统里，你会怎样拆分感知、定位、规划和控制节点，并处理时序与消息延迟？', '定位或感知结果抖动时，你会从传感器、标定、同步和算法四层怎样排查？'],
        ['讲一个你把算法从仿真或实验数据推进到真实设备的经历，性能落差出现在哪里？', '请选择一个项目说明你如何做成功率、精度、时延和安全边界评估。'],
        ['为校园配送机器人设计一条从感知到规划控制的最小可落地方案，你会先保哪些能力？', '算力和功耗预算被压缩后，你会怎样在效果、实时性和稳定性之间做取舍？'],
        ['具身智能热度很高。对校招候选人而言，哪些能力是真正能落到机器人系统里的？', '你如何判断一个机器人算法改动值得上线，而不是只在离线指标上变好？']
      ],
      ai: [
        ['请介绍一个你做过的 AI 项目，重点说数据、指标、迭代决策和最终效果。', '如果只能展示一个项目证明你的 AI 工程能力，你会选哪个，为什么？'],
        ['做 RAG 时召回质量、重排、上下文组织和答案评测会怎样互相影响？', '请比较 SFT、偏好对齐和推理阶段优化分别解决什么问题。'],
        ['讲一次你建立评测集或误差分析表的经历，它怎样改变了后续优化方向？', '模型离线分数提升但线上体验变差时，你会补看哪些质量、时延、成本和安全指标？'],
        ['为校招简历分析助手设计一套评测方案，怎样防止它只会写漂亮建议？', '业务要求响应更快但不能明显牺牲质量，你会从模型、缓存、提示词和链路哪里下手？'],
        ['Agent 很热。你会怎样判断一个任务需要 Agent，还是普通工作流更稳？', '请说一个你近期关注的大模型应用方向，并说明它的落地门槛。']
      ],
      lowAltitude: [
        ['请用一个具体场景说明你理解的低空经济运营，不要只讲行业概念。', '如果你加入低空运营团队，前三个月最想先摸清哪三类数据？'],
        ['规划一条低空物流航线时，你会先核对哪些空域、气象、起降点和安全约束？', '请说明运营岗位如何把合规、安全和用户体验放进同一套流程里。'],
        ['讲一次你把模糊目标拆成运营方案和执行清单的经历。', '如果要复盘一次试运营，你会设计哪些指标来判断航线是否值得继续投入？'],
        ['为文旅低空体验活动设计首周试运营方案，怎样安排流程、人员和风险兜底？', '一条航线准点率下降但需求上涨，你会怎样平衡扩量和服务稳定性？'],
        ['你如何判断一个低空应用是短期热点，还是能形成持续运营闭环？', '低空运营岗位最需要避免哪类只讲概念、不讲落地的判断？']
      ],
      material: [
        ['请介绍一个最能体现你材料研发思路的课题，说明假设、实验和结论。', '你做材料实验时遇到过哪次结果不稳定？后来如何确认原因？'],
        ['选择一种你熟悉的表征手段，说明它能回答什么问题，不能回答什么问题。', '材料性能提升后，你会怎样确认它不是由测试条件变化造成的假提升？'],
        ['讲一次你把实验结果整理成可复现实验记录或数据结论的过程。', '如果小试很好但放大后波动明显，你会先排查原料、工艺还是设备？'],
        ['为新能源材料候选方案设计从筛选到验证的最小研发路径，你会设哪些门槛？', '客户反馈批次差异影响应用，你会怎样组织验证并给出改进计划？'],
        ['请说一个你关注的材料方向，并解释它离规模化应用还差哪一步。', '材料研发越来越数据化。你认为数据工具最能先改善哪个环节？']
      ],
      pm: [
        ['请介绍一个你推动过的产品或项目，重点说目标、取舍和结果。', '哪段经历最能证明你做 AI 产品不是只会写需求文档？'],
        ['AI 产品上线前，你会怎样定义质量、时延、成本和安全的验收指标？', '当模型回答有波动时，PRD、评测样例和兜底交互分别要补什么？'],
        ['讲一次你通过用户反馈或数据复盘改变产品方案的经历。', '研发说方案能做但维护成本高，你会怎样拆 MVP 和后续版本？'],
        ['为大学生面试练习产品设计一次迭代，怎样证明题目更有参考价值而不是更花哨？', 'AI 功能点击率高但留存低，你会先排查内容质量、引导流程还是目标用户？'],
        ['你如何判断一个 AI 功能该做成自动执行、辅助建议，还是只做信息检索？', '请说一个你近期关注的 AI 产品案例，并解释它的关键体验取舍。']
      ]
    }
    const sections = pools[type] || pools.ai
    return sections.map(section => section[Math.floor(Math.random() * section.length)])
  }

  function getMockQuestions(type) {
    const questionSets = {
      robot: [
        '请介绍一下你对ROS机器人操作系统的理解，以及在项目中如何使用的？',
        '描述一个你参与过的机器人项目，你在其中负责什么？遇到了什么技术难点？',
        '如何设计一个室内服务机器人的导航避障方案？请从传感器选型到算法实现进行说明。',
        '谈谈你对人形机器人发展前景的看法，以及当前面临的主要技术瓶颈。',
        '如果让你设计一个工业协作机器人的安全策略，你会考虑哪些方面？'
      ],
      ai: [
        '请解释Transformer架构的核心思想，以及Self-Attention机制的工作原理。',
        '描述你做过的一个AI项目，从数据准备到模型部署的完整流程。',
        '如何解决深度学习模型训练中的过拟合问题？请列举至少三种方法。',
        '谈谈你对大模型（LLM）在垂直领域应用的理解，以及可能面临的挑战。',
        '如果让你设计一个简历筛选AI系统，你会如何定义评估指标和优化目标？'
      ],
      lowAltitude: [
        '请谈谈你对低空经济概念的理解，以及eVTOL行业的发展现状。',
        '低空经济运营需要关注哪些政策法规？如何确保合规运营？',
        '如果让你规划一条城市低空物流航线，你会考虑哪些因素？',
        '低空经济与智慧城市如何融合？请描述一个具体的应用场景。',
        '你认为低空经济运营面临的最大挑战是什么？如何应对？'
      ],
      material: [
        '请介绍你熟悉的一种新型材料，其特性和应用前景。',
        '描述你在材料研发或测试方面的项目经验，使用了哪些表征手段？',
        '碳纤维复合材料在航空航天领域有哪些应用？其优势是什么？',
        '如何设计一个新材料从实验室到量产的验证流程？',
        '谈谈你对新能源电池材料（如固态电解质）发展趋势的看法。'
      ],
      pm: [
        '请描述你从0到1做产品的完整流程，重点说明需求分析阶段的方法。',
        '如何判断一个产品需求是否值得做？你的优先级排序框架是什么？',
        '谈谈你对AI产品经理角色的理解，与传统产品经理有什么区别？',
        '描述一次你处理用户反馈并推动产品改进的经历。',
        '如果让你设计一个面向大学生的求职辅助产品，你会如何规划MVP？'
      ]
    }
    return questionSets[type] || questionSets.ai
  }

  function getStrictFallbackFeedback(answerText) {
    const text = answerText.trim()
    const normalized = text.replace(/\s/g, '')
    const directBadAnswers = ['不知道', '不会', '不懂', '随便', '无', '没有', '不知道了', '测试', 'test']
    const hasShortDirectBadAnswer = text.length <= 25 && ['我不知道', '我不会', '我不懂', '不知道怎么答', '没有想过', '随便答'].some(marker => normalized.includes(marker))
    const hasShortIrrelevantAnswer = text.length <= 40 && ['吃饭', '睡觉', '天气', '哈哈'].some(marker => normalized.includes(marker))
    const isInvalid = !text || text.length < 8 || directBadAnswers.includes(normalized) || hasShortDirectBadAnswer || hasShortIrrelevantAnswer || /(.)\1{6,}/.test(text)
    const zeroDimensions = [
      { label: '问题相关性', score: 0, comment: '回答没有有效回应题目' },
      { label: '内容准确性', score: 0, comment: '没有可判断的有效内容' },
      { label: '结构完整性', score: 0, comment: '缺少完整表达结构' },
      { label: '证据与细节', score: 0, comment: '没有项目、动作或结果证据' },
      { label: '岗位匹配度', score: 0, comment: '没有体现与岗位的匹配' }
    ]

    if (isInvalid) {
      return {
        score: 0,
        is_relevant: false,
        strict_reason: '回答无效或明显答非所问',
        dimensions: zeroDimensions,
        hit_points: [],
        missed_points: ['没有有效回应当前面试问题', '没有提供岗位相关证据', '没有说明个人动作和结果'],
        rewrite_advice: ['先正面回答问题', '补充一个真实场景', '说明你的动作、结果和复盘'],
        summary: '这版回答目前不能作为有效面试回答，需要先回到问题本身。',
        suggestion: '请重新围绕题目作答，至少说明具体场景、你的动作、结果和复盘。'
      }
    }

    return {
      score: 2,
      is_relevant: true,
      strict_reason: '评分服务异常，使用保守兜底评分',
      hit_points: ['回答有一定信息量，可以继续整理。'],
      missed_points: ['本地兜底无法完整判断岗位匹配', '还需要补充具体证据和结果'],
      rewrite_advice: ['用一句话先回答问题', '补一个真实项目或真实经历', '把经历扣回岗位要求'],
      summary: '当前为本地兜底分析，建议稍后重试 AI 复盘。',
      dimensions: [
        { label: '问题相关性', score: 2, comment: '本地兜底无法完整判断，只给低分' },
        { label: '内容准确性', score: 2, comment: '需要后端评分服务进一步判断' },
        { label: '结构完整性', score: 2, comment: '建议使用背景、行动、结果组织回答' },
        { label: '证据与细节', score: 1, comment: '需要补充可验证细节' },
        { label: '岗位匹配度', score: 2, comment: '需要明确对应岗位能力' }
      ],
      suggestion: '后端评分服务异常，本地只给保守低分，避免生成虚假高分。'
    }
  }

  function getMockFeedback() {
    const baseScore = Math.floor(Math.random() * 4) + 5
    const dims = [
      { label: '内容完整性', score: Math.floor(Math.random() * 5) + 5, comment: Math.random() > 0.3 ? '基本覆盖了问题的核心要点' : '可以补充更多关键细节' },
      { label: '逻辑清晰度', score: Math.floor(Math.random() * 5) + 5, comment: Math.random() > 0.3 ? '逻辑结构较清晰' : '可以用STAR法则让结构更清晰' },
      { label: '专业深度', score: Math.floor(Math.random() * 5) + 4, comment: Math.random() > 0.3 ? '展现了基础专业素养' : '可以深入展开技术细节' },
      { label: '表达结构化', score: Math.floor(Math.random() * 5) + 5, comment: Math.random() > 0.3 ? '表达较有条理' : '建议多用具体案例支撑观点' },
      { label: '岗位匹配度', score: Math.floor(Math.random() * 5) + 4, comment: Math.random() > 0.3 ? '能看出与岗位的基本匹配' : '可以更好地展示与岗位的契合点' }
    ]
    const suggestions = [
      '回答整体不错，建议在专业深度和具体案例上进一步加强。',
      '结构比较清晰，可以尝试用STAR法则组织回答，让面试官更容易抓住重点。',
      '基础内容覆盖了，建议补充更多行业理解和项目经验来增强竞争力。',
      '表达通顺，但可以在专业术语和深度上多下功夫，体现专业素养。',
      '思路清楚，建议将抽象观点落地到具体场景和案例中，更有说服力。',
      '回答有一定质量，可以从岗位需求出发更有针对性地展示自己的能力。'
    ]
    return {
      score: Math.min(10, baseScore),
      dimensions: dims,
      suggestion: suggestions[Math.floor(Math.random() * suggestions.length)]
    }
  }

  function generateMockReport() {
    const totalScore = scores.value.reduce((a, b) => a + b, 0)
    const avgScore = totalScore / questions.value.length
    let advice = ''
    if (avgScore >= 8) advice = '表现优秀！你的回答逻辑清晰、内容充实，具备较强的专业能力和表达能力。建议继续保持，在细节上精益求精。'
    else if (avgScore >= 6) advice = '表现良好！整体回答有一定深度，但在结构化表达和具体案例支撑上还有提升空间。建议使用STAR法则组织回答，多准备量化数据。'
    else advice = '还需加强！建议从以下方面提升：1）使用STAR法则结构化回答；2）增加具体项目案例和数据支撑；3）提前准备岗位核心知识点；4）练习控制语速和表达节奏。'

    return {
      total_score: totalScore,
      avg_score: avgScore,
      advice,
      details: questions.value.map((q, i) => ({
        question: q,
        answer: answers.value[i] || '',
        score: scores.value[i] || 0
      }))
    }
  }

  return {
    jobType,
    jobTypeNames,
    questions,
    currentQuestionIndex,
    answers,
    scores,
    feedbacks,
    interviewId,
    isStarting,
    isAnswering,
    isCompleted,
    report,
    history,
    historyDetail,
    isLoadingDetail,
    answerError,
    start,
    answer,
    complete,
    reset,
    fetchHistory,
    fetchHistoryDetail,
    clearHistoryDetail
  }
})
