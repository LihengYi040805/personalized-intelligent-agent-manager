import { Layout, Menu, Dropdown, Avatar, Space, message } from 'antd'
import {
  DashboardOutlined,
  TeamOutlined,
  BookOutlined,
  BarChartOutlined,
  RobotOutlined,
  UserOutlined,
  LogoutOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import { useState } from 'react'
import TeacherDashboard from '@/pages/teacher/Dashboard'
import StudentsManagement from '@/pages/teacher/StudentsManagement'
import QuestionBank from '@/pages/teacher/QuestionBank'
import WeakAnalysis from '@/pages/teacher/WeakAnalysis'
import AIGeneration from '@/pages/teacher/AIGeneration'
import ModelTraining from '@/pages/teacher/ModelTraining'

const { Header, Content, Sider } = Layout

const TeacherLayout = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)
  
  // 从 localStorage 获取登录用户信息
  const getUserInfo = () => {
    const userStr = localStorage.getItem('user')
    if (userStr) {
      return JSON.parse(userStr)
    }
    return null
  }

  const handleMenuClick = ({ key }: { key: string }) => {
    if (key === 'profile') {
      const user = getUserInfo()
      if (user) {
        message.info({
          content: (
            <div>
              <p><strong>用户名：</strong>{user.username}</p>
              <p><strong>角色：</strong>教师</p>
              <p><strong>邮箱：</strong>{user.email}</p>
            </div>
          ),
          duration: 5,
        })
      }
    } else if (key === 'logout') {
      localStorage.removeItem('user')
      message.success('已退出登录')
      navigate('/')
    }
  }

  const user = getUserInfo()
  const displayName = user?.username || '教师'

  const menuItems = [
    {
      key: '/teacher',
      icon: <DashboardOutlined />,
      label: '数据看板',
    },
    {
      key: '/teacher/students',
      icon: <TeamOutlined />,
      label: '学生管理',
    },
    {
      key: '/teacher/ai-generation',
      icon: <RobotOutlined />,
      label: 'AI生成题库',
    },
    {
      key: '/teacher/model-training',
      icon: <ThunderboltOutlined />,
      label: '模型训练',
    },
    {
      key: '/teacher/question-bank',
      icon: <BookOutlined />,
      label: '题库管理',
    },
    {
      key: '/teacher/weak-analysis',
      icon: <BarChartOutlined />,
      label: '薄弱分析',
    },
  ]

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
          智能教育学习系统 - 教师端
        </div>
        <Dropdown menu={{ items: userMenuItems, onClick: handleMenuClick }}>
          <Space style={{ cursor: 'pointer' }}>
            <Avatar icon={<UserOutlined />} style={{ background: '#52c41a' }} />
            <span style={{ color: '#333' }}>{displayName}</span>
          </Space>
        </Dropdown>
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
              <Route path="/" element={<TeacherDashboard />} />
              <Route path="/students" element={<StudentsManagement />} />
              <Route path="/ai-generation" element={<AIGeneration />} />
              <Route path="/model-training" element={<ModelTraining />} />
              <Route path="/question-bank" element={<QuestionBank />} />
              <Route path="/weak-analysis" element={<WeakAnalysis />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </Layout>
  )
}

export default TeacherLayout

