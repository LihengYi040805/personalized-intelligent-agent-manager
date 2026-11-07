import axios from 'axios'

// 优先使用环境变量，如果没有则使用空字符串（使用相对路径）
// 开发环境：使用相对路径，Vite proxy 会转发 /api/* 到 localhost:5000
// 生产环境：如果有 VITE_API_BASE_URL 则使用，否则使用相对路径
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 响应拦截器
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// ==================== 课程相关API ====================
export const courseApi = {
  // 获取所有课程
  getCourses: () => api.get('/api/courses'),
  
  // 获取课程详情
  getCourseDetail: (courseId: number) => api.get(`/api/courses/${courseId}`),
  
  // 获取课程知识点
  getKnowledges: (courseId: number) => api.get(`/api/courses/${courseId}/knowledges`),
  
  // 获取知识图谱
  getKnowledgeGraph: (courseId: number) => api.get(`/api/courses/${courseId}/knowledge-graph`),
  
  // 获取课程题目
  getQuestions: (courseId: number, params?: any) => 
    api.get(`/api/courses/${courseId}/questions`, { params }),
}

// ==================== 题目相关API ====================
export const questionApi = {
  // 获取题目详情
  getQuestionDetail: (questionId: number) => api.get(`/api/questions/${questionId}`),
  
  // 提交答案
  submitAnswer: (questionId: number, data: any) => 
    api.post(`/api/questions/${questionId}/submit`, data),
}

// ==================== 学生相关API ====================
export const studentApi = {
  // 获取所有学生
  getStudents: () => api.get('/api/students'),
  
  // 获取学生详情
  getStudentDetail: (studentId: number) => api.get(`/api/students/${studentId}`),
  
  // 生成认知诊断报告
  generateDiagnosis: (studentId: number, courseId: number, algorithm: string = 'IRT') => 
    api.post(`/api/students/${studentId}/diagnosis`, { course_id: courseId, algorithm }),
  
  // 获取最新诊断报告
  getLatestDiagnosis: (studentId: number, courseId: number) => 
    api.get(`/api/students/${studentId}/diagnosis/latest`, { params: { course_id: courseId } }),
  
  // 获取学习进度
  getLearningProgress: (studentId: number, courseId: number) => 
    api.get(`/api/students/${studentId}/learning-progress`, { params: { course_id: courseId } }),
  
  // 获取答题记录
  getQuestionRecords: (studentId: number, courseId?: number) => 
    api.get(`/api/students/${studentId}/question-records`, { params: courseId ? { course_id: courseId } : {} }),
}

// ==================== 教师端API ====================
export const teacherApi = {
  // 获取学生概况
  getStudentsOverview: (courseId: number) => 
    api.get('/api/teacher/students-overview', { params: { course_id: courseId } }),
  
  // 获取薄弱知识点分析
  getWeakKnowledges: (courseId: number) => 
    api.get('/api/teacher/weak-knowledges', { params: { course_id: courseId } }),
}

// ==================== 用户认证API ====================
export const authApi = {
  // 用户注册
  register: (data: { username: string; email: string; password: string; role?: string }) =>
    api.post('/api/auth/register', data),
  
  // 用户登录
  login: (data: { username: string; password: string }) =>
    api.post('/api/auth/login', data),
  
  // 检查登录状态
  checkAuth: (userId: number) =>
    api.get('/api/auth/check', { params: { user_id: userId } }),
}

export default api

