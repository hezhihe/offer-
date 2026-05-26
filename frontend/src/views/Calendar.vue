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
        @click="jobsStore.filterJobs(cat)"
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
        :class="{ active: currentEducation === edu.value }"
        @click="filterByEducation(edu.value)"
      >
        {{ edu.label }}
      </button>
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
          <span class="jli-date">📅 {{ job.date }}</span>
          <span class="badge badge-amber">💰 {{ job.capital }}</span>
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

      <div class="calendar-grid">
        <div class="cal-header" v-for="day in weekDays" :key="day">{{ day }}</div>
        <div
          v-for="day in calendarDays"
          :key="day.date"
          class="cal-day"
          :class="{
            'today': day.isToday,
            'other-month': !day.isCurrentMonth,
            'has-event': day.hasEvent
          }"
          @click="day.isCurrentMonth && selectDate(day)"
        >
          {{ day.day }}
        </div>
      </div>

      <div v-if="selectedDate" class="card" style="margin-top:16px">
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
            <span class="dr-label">注册资本</span>
            <span class="dr-value">{{ selectedJob.capital }}</span>
          </div>
          <div class="detail-row">
            <span class="dr-label">学历要求</span>
            <span class="dr-value">🎓 {{ selectedJob.education }}</span>
          </div>
          <div class="detail-row">
            <span class="dr-label">要求</span>
            <span class="dr-value">{{ selectedJob.requirements }}</span>
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
import { ref, computed, onMounted } from 'vue'
import { useJobsStore } from '../stores/jobs'
import { jobsApi } from '../api/jobs'
import { useToast } from '../composables/useToast'

const jobsStore = useJobsStore()
const toast = useToast()
const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth() + 1)
const selectedDate = ref(null)
const showDetail = ref(false)
const selectedJob = ref(null)
const currentEducation = ref('all')

const educationOptions = [
  { label: '全部', value: 'all' },
  { label: '本科及以上', value: '本科' },
  { label: '硕士及以上', value: '硕士' }
]

const weekDays = ['日', '一', '二', '三', '四', '五', '六']

const calendarDays = computed(() => {
  const days = []
  const firstDay = new Date(currentYear.value, currentMonth.value - 1, 1)
  const lastDay = new Date(currentYear.value, currentMonth.value, 0)
  const startDay = firstDay.getDay()
  const totalDays = lastDay.getDate()
  const today = new Date()

  const prevMonthLastDay = new Date(currentYear.value, currentMonth.value - 1, 0).getDate()
  for (let i = startDay - 1; i >= 0; i--) {
    days.push({
      day: prevMonthLastDay - i,
      date: `${currentYear.value}-${String(currentMonth.value - 1).padStart(2, '0')}-${String(prevMonthLastDay - i).padStart(2, '0')}`,
      isCurrentMonth: false,
      isToday: false,
      hasEvent: false
    })
  }

  for (let i = 1; i <= totalDays; i++) {
    const dateStr = `${currentYear.value}-${String(currentMonth.value).padStart(2, '0')}-${String(i).padStart(2, '0')}`
    const isToday = today.getFullYear() === currentYear.value &&
                    today.getMonth() + 1 === currentMonth.value &&
                    today.getDate() === i
    days.push({
      day: i,
      date: dateStr,
      isCurrentMonth: true,
      isToday,
      hasEvent: jobsStore.jobs.some(j => j.date === dateStr)
    })
  }

  const remaining = 42 - days.length
  for (let i = 1; i <= remaining; i++) {
    days.push({
      day: i,
      date: `${currentYear.value}-${String(currentMonth.value + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`,
      isCurrentMonth: false,
      isToday: false,
      hasEvent: false
    })
  }

  return days
})

const selectedJobs = computed(() => {
  if (!selectedDate.value) return []
  const dateStr = `${selectedDate.value.year}-${String(selectedDate.value.month).padStart(2, '0')}-${String(selectedDate.value.day).padStart(2, '0')}`
  return jobsStore.jobs.filter(j => j.date === dateStr)
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
  const [year, month, dayNum] = day.date.split('-').map(Number)
  selectedDate.value = { year, month, day: dayNum }
}

async function showJobDetail(job) {
  jobsStore.selectJob(job)
  selectedJob.value = job
  showDetail.value = true

  try {
    const response = await jobsApi.getById(job.id)
    selectedJob.value = response.data
  } catch (e) {
    toast.show('岗位详情加载失败，已显示列表缓存信息')
  }
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
  currentEducation.value = edu
  jobsStore.fetchJobs(jobsStore.currentFilter, edu)
}

onMounted(() => {
  jobsStore.fetchJobs()
})
</script>
