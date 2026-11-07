import { Layout, Menu, Dropdown, Avatar, Space, message } from 'antd'
import {
  BookOutlined,
  EditOutlined,
  BarChartOutlined,
  HomeOutlined,
  UserOutlined,
  LogoutOutlined,
  HistoryOutlined,
} from '@ant-design/icons'
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import StudentHome from '@/pages/student/Home'
import CourseList from '@/pages/student/CourseList'
import KnowledgeGraph from '@/pages/student/KnowledgeGraph'
import Practice from '@/pages/student/Practice'
import Diagnosis from '@/pages/student/Diagnosis'
import QuestionRecords from '@/pages/student/QuestionRecords'
import { studentApi } from '@/services/api'

const { Header, Content, Sider } = Layout

const StudentLayout = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)
  const [currentStudent, setCurrentStudent] = useState<any>(null)
  const [selectedStudentId, setSelectedStudentId] = useState<number>(1)

  // 从 localStorage 获取登录用户信息
  useEffect(() => {
    const userStr = localStorage.getItem('user')
    if (!userStr) {
      message.warning('请先登录')
      navigate('/')
      return
    }

    const user = JSON.parse(userStr)
    if (user.role !== 'student') {
      message.error('权限不足')
      navigate('/')
      return
    }

    // 获取学生详细信息
    if (user.student_id) {
      setSelectedStudentId(user.student_id)
      fetchStudentInfo(user.student_id)
    }
  }, [navigate])

  const fetchStudentInfo = async (studentId: number) => {
    try {
      const data = await studentApi.getStudentDetail(studentId)
      setCurrentStudent(data)
    } catch (error) {
      console.error('Failed to fetch student info:', error)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('user')
    message.success('已退出登录')
    navigate('/')
  }

  const menuItems = [
    {
      key: '/student',
      icon: <HomeOutlined />,
      label: '首页',
    },
    {
      key: '/student/courses',
      icon: <BookOutlined />,
      label: '课程学习',
    },
    {
      key: '/student/knowledge-graph',
      icon: <BarChartOutlined />,
      label: '知识图谱',
    },
    {
      key: '/student/practice',
      icon: <EditOutlined />,
      label: '在线答题',
    },
    {
      key: '/student/diagnosis',
      icon: <BarChartOutlined />,
      label: '认知诊断',
    },
    {
      key: '/student/records',
      icon: <HistoryOutlined />,
      label: '我的答题记录',
    },
  ]

  const handleMenuClick = ({ key }: { key: string }) => {
    if (key === 'profile') {
      // 显示个人信息
      const userStr = localStorage.getItem('user')
      if (userStr) {
        const user = JSON.parse(userStr)
        message.info({
          content: (
            <div>
              <p><strong>用户名：</strong>{user.username}</p>
              <p><strong>姓名：</strong>{currentStudent?.name || '加载中...'}</p>
              <p><strong>学号：</strong>{currentStudent?.employee_id || '加载中...'}</p>
              <p><strong>院系：</strong>{currentStudent?.department || '加载中...'}</p>
              <p><strong>邮箱：</strong>{user.email}</p>
            </div>
          ),
          duration: 5,
        })
      }
    } else if (key === 'logout') {
      handleLogout()
    }
  }

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人信息',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
    },
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ 
        background: '#fff', 
        padding: '0 24px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
      }}>
        <div style={{ color: '#1890ff', fontSize: '20px', fontWeight: 'bold' }}>
          智能教育学习系统 - 学生端
        </div>
        <Space>
          <Dropdown menu={{ items: userMenuItems, onClick: handleMenuClick }}>
            <Space style={{ cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#1890ff' }} />
              <span style={{ color: '#333' }}>{currentStudent?.name || '加载中...'}</span>
            </Space>
          </Dropdown>
        </Space>
      </Header>
      
      <Layout>
        <Sider 
          collapsible 
          collapsed={collapsed} 
          onCollapse={setCollapsed}
          theme="light"
        >
          <Menu
            mode="inline"
            selectedKeys={[location.pathname]}
            items={menuItems}
            onClick={({ key }) => navigate(key)}
            style={{ height: '100%', borderRight: 0 }}
          />
        </Sider>
        
        <Layout style={{ padding: '24px', background: '#f5f7fa' }}>
          <Content style={{ 
            background: '#fff',
            padding: 24,
            margin: 0,
            minHeight: 280,
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
          }}>
            <Routes>
              <Route path="/" element={<StudentHome key={selectedStudentId} studentId={selectedStudentId} />} />
              <Route path="/courses" element={<CourseList />} />
              <Route path="/knowledge-graph" element={<KnowledgeGraph />} />
              <Route path="/practice" element={<Practice key={selectedStudentId} studentId={selectedStudentId} />} />
              <Route path="/diagnosis" element={<Diagnosis key={selectedStudentId} studentId={selectedStudentId} />} />
              <Route path="/records" element={<QuestionRecords key={selectedStudentId} studentId={selectedStudentId} />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </Layout>
  )
}

export default StudentLayout

