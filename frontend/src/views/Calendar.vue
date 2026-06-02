<template>
  <div class="page active">
    <h1 class="section-title" style="margin-bottom:16px">
      <span class="icon" style="background:var(--blue-light)">📅</span>
      招聘日历
    </h1>

    <div class="calendar-header">
      <div class="view-toggle">
        <button :class="{ active: jobsStore.currentView === 'list' }" @click="jobsStore.switchView('list')">
          📋 列表
        </button>
        <button :class="{ active: jobsStore.currentView === 'grid' }" @click="jobsStore.switchView('grid')">
          📅 日历
        </button>
      </div>
    </div>

    <div class="filter-chips">
      <button
        v-for="cat in jobsStore.categories"
        :key="cat"
        class="chip"
        :class="{ active: jobsStore.currentFilter === cat }"
        @click="filterByCategory(cat)"
      >
        {{ jobsStore.categoryNames[cat] }}
      </button>
    </div>

    <div class="filter-chips" style="margin-top:8px">
      <span style="font-size:12px;color:var(--medium);margin-right:8px;line-height:28px">学历：</span>
      <button
        v-for="edu in educationOptions"
        :key="edu.value"
        class="chip"
        :class="{ active: jobsStore.currentEducation === edu.value }"
        @click="filterByEducation(edu.value)"
      >
        {{ edu.label }}
      </button>
      <label class="expired-toggle">
        <input
          type="checkbox"
          :checked="jobsStore.showExpiredJobs"
          @change="toggleExpiredJobs"
        >
        <span>查看已过期</span>
      </label>
    </div>

    <div v-if="jobsStore.currentView === 'list'">
      <div
        v-for="job in jobsStore.jobs"
        :key="job.id"
        class="job-list-item"
        @click="showJobDetail(job)"
      >
        <div class="jli-top">
          <div>
            <div class="jli-company">{{ job.company }}</div>
            <div class="jli-title">{{ job.title }}</div>
          </div>
          <span class="badge badge-blue">{{ job.salary }}</span>
        </div>
        <div class="jli-meta">
          <span v-if="deadlineLabel(job)" class="badge" :class="jobStatusClass(job)">
            {{ deadlineLabel(job) }}
          </span>
          <span class="jli-date">📅 {{ job.date }}</span>
          <span class="badge badge-amber">🏢 {{ job.capital }}</span>
          <span class="badge" style="background:var(--blue-light);color:var(--blue)">🎓 {{ job.education }}</span>
          <span v-if="job.womenFriendly" class="women-friendly">👩‍💼 女性友好</span>
        </div>
      </div>

      <div v-if="jobsStore.jobs.length === 0" class="empty-state">
        <div class="es-icon">📭</div>
        <p>暂无匹配的岗位</p>
      </div>
    </div>

    <div v-else>
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
        <button class="btn btn-secondary btn-sm" @click="prevMonth">◀</button>
        <h3 style="font-size:16px;font-weight:700">{{ currentYear }}年{{ currentMonth }}月</h3>
        <button class="btn btn-secondary btn-sm" @click="nextMonth">▶</button>
      </div>

      <div v-if="monthEventCount === 0" class="calendar-month-hint">
        本月暂无岗位截止日期，当前岗位数据主要集中在 {{ nextEventMonthText }}。
      </div>

      <div class="calendar-grid">
        <div class="cal-header" v-for="day in weekDays" :key="day">{{ day }}</div>
        <div
          v-for="day in calendarDays"
          :key="day.date"
          class="cal-day"
          :class="{
            'today': day.isToday,
            'selected': day.date === selectedDateKey,
            'other-month': !day.isCurrentMonth,
            'has-event': day.hasEvent
          }"
          @click="selectDate(day)"
        >
          <span class="cal-day-num">{{ day.day }}</span>
          <span v-if="day.eventCount" class="cal-day-count">{{ day.eventCount }}岗</span>
        </div>
      </div>

      <div v-if="selectedDate" ref="selectedJobsRef" class="card selected-jobs-card">
        <h3 style="font-size:15px;font-weight:700;margin-bottom:12px">
          {{ selectedDate.year }}年{{ selectedDate.month }}月{{ selectedDate.day }}日 招聘信息
        </h3>
        <div v-if="selectedJobs.length > 0">
          <div
            v-for="job in selectedJobs"
            :key="job.id"
            class="job-list-item"
            style="margin-bottom:8px"
            @click="showJobDetail(job)"
          >
            <div class="jli-top">
              <div>
                <div class="jli-company">{{ job.company }}</div>
                <div class="jli-title">{{ job.title }}</div>
              </div>
              <span class="badge badge-blue">{{ job.salary }}</span>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          <div class="es-icon">📭</div>
          <p>当日暂无招聘信息</p>
        </div>
      </div>
    </div>

    <div class="modal-overlay" :class="{ show: showDetail }" @click.self="closeDetail">
      <div class="modal-content">
        <div class="modal-handle"></div>
        <button class="modal-close" @click="closeDetail">×</button>
        <div v-if="selectedJob">
          <h3 style="font-size:18px;font-weight:700;margin-bottom:16px">{{ selectedJob.title }}</h3>
          <div class="detail-row">
            <span class="dr-label">公司</span>
            <span class="dr-value">{{ selectedJob.company }}</span>
          </div>
          <div class="detail-row">
            <span class="dr-label">薪资</span>
            <span class="dr-value">{{ selectedJob.salary }}</span>
          </div>
          <div class="detail-row">
            <span class="dr-label">日期</span>
            <span class="dr-value">{{ selectedJob.date }}</span>
          </div>
          <div class="detail-row">
            <span class="dr-label">企业规模</span>
            <span class="dr-value">{{ selectedJob.capital }}</span>
          </div>
          <div class="detail-row">
            <span class="dr-label">学历要求</span>
            <span class="dr-value">🎓 {{ selectedJob.education }}</span>
          </div>
          <div class="detail-row">
            <span class="dr-label">要求</span>
            <span class="dr-value requirement-value">{{ selectedJob.requirements }}</span>
          </div>
          <div v-if="selectedJob.womenFriendly" class="detail-row">
            <span class="women-friendly">👩‍💼 女性友好岗位</span>
          </div>
          <div v-if="selectedJob.url" class="detail-row">
            <span class="dr-label">详情链接</span>
            <a class="dr-value job-url" :href="selectedJob.url" target="_self">{{ selectedJob.url }}</a>
          </div>
          <button class="btn btn-primary btn-block" style="margin-top:20px" @click="openJobUrl">
            🔗 查看详情
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { useJobsStore } from '../stores/jobs'
import { useToast } from '../composables/useToast'

const jobsStore = useJobsStore()
const toast = useToast()
const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth() + 1)
const selectedDate = ref(null)
const selectedJobsRef = ref(null)
const showDetail = ref(false)
const selectedJob = ref(null)
const educationOptions = [
  { label: '全部', value: 'all' },
  { label: '专科可投', value: '专科' },
  { label: '本科可投', value: '本科' },
  { label: '硕士可投', value: '硕士' }
]

const weekDays = ['日', '一', '二', '三', '四', '五', '六']

const jobsByDate = computed(() => {
  const grouped = new Map()
  jobsStore.jobs.forEach(job => {
    const key = normalizeDateKey(job.date)
    if (!key) return
    const current = grouped.get(key) || []
    current.push(job)
    grouped.set(key, current)
  })
  return grouped
})

const selectedDateKey = computed(() => {
  if (!selectedDate.value) return ''
  return formatDateKey(selectedDate.value.year, selectedDate.value.month, selectedDate.value.day)
})

const monthEventCount = computed(() => {
  let count = 0
  jobsByDate.value.forEach((jobs, dateKey) => {
    const [year, month] = dateKey.split('-').map(Number)
    if (year === currentYear.value && month === currentMonth.value) {
      count += jobs.length
    }
  })
  return count
})

const nextEventMonthText = computed(() => {
  const dates = Array.from(jobsByDate.value.keys()).sort()
  const firstFutureDate = dates.find(date => date >= formatDateKey(currentYear.value, currentMonth.value, 1)) || dates[0]
  if (!firstFutureDate) return '后续月份'
  const [year, month] = firstFutureDate.split('-').map(Number)
  return `${year}年${month}月`
})

const calendarDays = computed(() => {
  const days = []
  const firstDay = new Date(currentYear.value, currentMonth.value - 1, 1)
  const lastDay = new Date(currentYear.value, currentMonth.value, 0)
  const startDay = firstDay.getDay()
  const totalDays = lastDay.getDate()
  const today = new Date()

  const prevMonthLastDay = new Date(currentYear.value, currentMonth.value - 1, 0).getDate()
  for (let i = startDay - 1; i >= 0; i--) {
    const date = new Date(currentYear.value, currentMonth.value - 2, prevMonthLastDay - i)
    const dateStr = formatDateKey(date.getFullYear(), date.getMonth() + 1, date.getDate())
    days.push({
      day: prevMonthLastDay - i,
      date: dateStr,
      year: date.getFullYear(),
      month: date.getMonth() + 1,
      isCurrentMonth: false,
      isToday: false,
      hasEvent: jobsByDate.value.has(dateStr),
      eventCount: jobsByDate.value.get(dateStr)?.length || 0
    })
  }

  for (let i = 1; i <= totalDays; i++) {
    const dateStr = formatDateKey(currentYear.value, currentMonth.value, i)
    const isToday = today.getFullYear() === currentYear.value &&
                    today.getMonth() + 1 === currentMonth.value &&
                    today.getDate() === i
    days.push({
      day: i,
      date: dateStr,
      year: currentYear.value,
      month: currentMonth.value,
      isCurrentMonth: true,
      isToday,
      hasEvent: jobsByDate.value.has(dateStr),
      eventCount: jobsByDate.value.get(dateStr)?.length || 0
    })
  }

  const remaining = 42 - days.length
  for (let i = 1; i <= remaining; i++) {
    const date = new Date(currentYear.value, currentMonth.value, i)
    const dateStr = formatDateKey(date.getFullYear(), date.getMonth() + 1, date.getDate())
    days.push({
      day: i,
      date: dateStr,
      year: date.getFullYear(),
      month: date.getMonth() + 1,
      isCurrentMonth: false,
      isToday: false,
      hasEvent: jobsByDate.value.has(dateStr),
      eventCount: jobsByDate.value.get(dateStr)?.length || 0
    })
  }

  return days
})

const selectedJobs = computed(() => {
  if (!selectedDate.value) return []
  return jobsByDate.value.get(selectedDateKey.value) || []
})

function prevMonth() {
  if (currentMonth.value === 1) {
    currentMonth.value = 12
    currentYear.value--
  } else {
    currentMonth.value--
  }
  selectedDate.value = null
}

function nextMonth() {
  if (currentMonth.value === 12) {
    currentMonth.value = 1
    currentYear.value++
  } else {
    currentMonth.value++
  }
  selectedDate.value = null
}

function selectDate(day) {
  selectedDate.value = { year: day.year, month: day.month, day: day.day }
  if (!day.isCurrentMonth) {
    currentYear.value = day.year
    currentMonth.value = day.month
  }
  nextTick(() => {
    selectedJobsRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
}

function formatDateKey(year, month, day) {
  return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
}

function normalizeDateKey(value) {
  if (!value) return ''
  if (typeof value === 'string') {
    const match = value.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/)
    if (match) return formatDateKey(Number(match[1]), Number(match[2]), Number(match[3]))
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return formatDateKey(date.getFullYear(), date.getMonth() + 1, date.getDate())
}

function showJobDetail(job) {
  jobsStore.selectJob(job)
  selectedJob.value = job
  showDetail.value = true
}

function closeDetail() {
  showDetail.value = false
  selectedJob.value = null
}

function openJobUrl() {
  const url = selectedJob.value?.url
  if (!url) {
    toast.show('No detail link for this job')
    return
  }

  window.location.href = url
}

function filterByEducation(edu) {
  jobsStore.filterByEducation(edu)
}

function filterByCategory(category) {
  jobsStore.filterJobs(category)
}

async function toggleExpiredJobs(event) {
  await jobsStore.setShowExpiredJobs(event.target.checked)
}

function deadlineLabel(job) {
  if (job?.status === 'closed') return '已下架'
  if (job?.status === 'expired' || job?.isExpired) return '已过期'
  if (typeof job?.daysUntilDeadline === 'number' && job.daysUntilDeadline >= 0 && job.daysUntilDeadline <= 7) {
    return job.daysUntilDeadline === 0 ? '今日截止' : `${job.daysUntilDeadline}天后截止`
  }
  return ''
}

function jobStatusClass(job) {
  if (job?.status === 'closed' || job?.status === 'expired' || job?.isExpired) {
    return 'badge-muted'
  }
  if (typeof job?.daysUntilDeadline === 'number' && job.daysUntilDeadline >= 0 && job.daysUntilDeadline <= 7) {
    return 'badge-urgent'
  }
  return 'badge-active'
}

onMounted(() => {
  jobsStore.fetchJobs()
})
</script>

<style scoped>
.calendar-month-hint {
  margin: -4px 0 14px;
  padding: 10px 12px;
  border-radius: 12px;
  background: #f8fafc;
  color: var(--medium);
  font-size: 13px;
  line-height: 1.5;
}

.expired-toggle {
  min-height: 34px;
  padding: 0 12px;
  border: 1px solid #dbe3ef;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--medium);
  font-size: 13px;
  font-weight: 700;
  background: #fff;
  cursor: pointer;
}

.expired-toggle input {
  width: 14px;
  height: 14px;
  accent-color: var(--blue);
}

.badge-muted {
  background: #eef2f7;
  color: #64748b;
}

.badge-urgent {
  background: #fff1f2;
  color: #e11d48;
}

.badge-active {
  background: #ecfdf5;
  color: #047857;
}

.selected-jobs-card {
  margin-top: 16px;
  scroll-margin-top: 18px;
}

.cal-day {
  gap: 3px;
}

.cal-day-num {
  line-height: 1;
}

.cal-day.selected {
  outline: 2px solid var(--blue);
  outline-offset: -2px;
  background: var(--blue-light);
  color: var(--blue);
  font-weight: 800;
}

.cal-day.today.selected {
  outline-color: var(--purple);
  background: var(--gradient);
  color: var(--white);
}

.cal-day-count {
  min-width: 28px;
  height: 16px;
  padding: 0 5px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: var(--blue);
  color: var(--white);
  font-size: 10px;
  font-weight: 800;
  line-height: 1;
}

.cal-day.has-event {
  background: #eff6ff;
  border: 1px solid rgba(37, 99, 235, .22);
  color: var(--blue);
  font-weight: 800;
}

.cal-day.today .cal-day-count {
  background: var(--white);
  color: var(--blue);
}

.cal-day.has-event::after {
  display: none;
}

.cal-day.other-month {
  cursor: pointer;
}

.requirement-value {
  line-height: 1.65;
  white-space: pre-line;
}
</style>
