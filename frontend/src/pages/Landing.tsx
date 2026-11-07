import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Card, Row, Col, Modal, Form, Input, message, Tabs, Radio } from 'antd'
import { UserOutlined, LockOutlined, MailOutlined, BookOutlined, LineChartOutlined, RobotOutlined } from '@ant-design/icons'
import { authApi } from '@/services/api'
import './Landing.css'

const Landing = () => {
  const navigate = useNavigate()
  const [loginModalVisible, setLoginModalVisible] = useState(false)
  const [loading, setLoading] = useState(false)
  const [loginForm] = Form.useForm()
  const [registerForm] = Form.useForm()

  const handleLogin = async (values: any) => {
    try {
      setLoading(true)
      const response = await authApi.login({
        username: values.username,
        password: values.password
      })
      
      message.success('登录成功！')
      setLoginModalVisible(false)
      
      // 保存用户信息到localStorage
      localStorage.setItem('user', JSON.stringify(response.user))
      
      // 根据角色跳转
      if (response.user.role === 'teacher') {
        navigate('/teacher')
      } else {
        navigate('/student')
      }
    } catch (error: any) {
      message.error(error?.response?.data?.error || '登录失败')
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (values: any) => {
    try {
      setLoading(true)
      await authApi.register({
        username: values.username,
        email: values.email,
        password: values.password,
        role: values.role || 'student'
      })
      
      message.success('注册成功！请登录')
      registerForm.resetFields()
    } catch (error: any) {
      message.error(error?.response?.data?.error || '注册失败')
    } finally {
      setLoading(false)
    }
  }

  const features = [
    {
      icon: <RobotOutlined style={{ fontSize: 48, color: '#1890ff' }} />,
      title: '智能认知诊断',
      description: '基于IRT和NCDM算法，精准分析学习者知识掌握情况，提供个性化学习建议'
    },
    {
      icon: <LineChartOutlined style={{ fontSize: 48, color: '#52c41a' }} />,
      title: '学习进度可视化',
      description: '实时追踪学习进度，通过知识图谱和数据分析，帮助学生了解学习状态'
    },
    {
      icon: <BookOutlined style={{ fontSize: 48, color: '#722ed1' }} />,
      title: '在线题库练习',
      description: '丰富的题库资源，支持在线答题、即时反馈，巩固知识点掌握'
    }
  ]

  const courses = [
    {
      title: 'C语言程序设计',
      description: '计算机专业基础课程，涵盖C语言语法、数据类型、控制结构、函数、指针等核心知识',
      image: 'https://images.unsplash.com/photo-1542831371-29b0f74f9713?w=400&h=250&fit=crop'
    },
    {
      title: '数据库原理与应用',
      description: '数据库系统基础课程，包含关系模型、SQL语言、数据库设计、事务处理等内容',
      image: 'https://images.unsplash.com/photo-1544383835-bda2bc66a55d?w=400&h=250&fit=crop'
    },
    {
      title: '数据结构与算法',
      description: '计算机核心课程，学习线性表、树、图等数据结构及常用算法设计与分析',
      image: 'https://images.unsplash.com/photo-1509228468518-180dd4864904?w=400&h=250&fit=crop'
    }
  ]

  return (
    <div className="landing-container">
      {/* 导航栏 */}
      <header className="landing-header">
        <div className="header-content">
          <div className="logo">
            <BookOutlined style={{ fontSize: 28, marginRight: 8 }} />
            <span>智能教育学习系统</span>
          </div>
          <nav className="nav-menu">
            <a href="#home">首页</a>
            <a href="#features">平台特色</a>
            <a href="#courses">热门课程</a>
            <a href="#about">关于我们</a>
          </nav>
          <div className="header-actions">
            <Button type="link" onClick={() => setLoginModalVisible(true)}>登录</Button>
            <Button type="primary" onClick={() => setLoginModalVisible(true)}>注册</Button>
          </div>
        </div>
      </header>

      {/* Hero区域 */}
      <section className="hero-section" id="home">
        <div className="hero-content">
          <div className="hero-text">
            <h1 className="hero-title">智能教育学习平台</h1>
            <p className="hero-subtitle">个性化学习引擎 + AI智能辅助功能</p>
            <div className="hero-features">
              <div className="hero-feature-item">
                <UserOutlined /> 个性化诊断 | 精准定位 | 智能推荐
              </div>
              <div className="hero-feature-item">
                <BookOutlined /> 实时跟踪 | 数据驱动 | 全面评估
              </div>
            </div>
            <div className="hero-buttons">
              <Button type="primary" size="large" onClick={() => setLoginModalVisible(true)}>
                立即加入
              </Button>
              <Button size="large" style={{ marginLeft: 16 }}>
                了解更多
              </Button>
            </div>
          </div>
          <div className="hero-image">
            <img src="https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=600&h=400&fit=crop" alt="学习场景" />
          </div>
        </div>
      </section>

      {/* 平台特色 */}
      <section className="features-section" id="features">
        <div className="section-content">
          <h2 className="section-title">平台特色</h2>
          <Row gutter={[32, 32]}>
            {features.map((feature, index) => (
              <Col xs={24} md={8} key={index}>
                <Card className="feature-card" hoverable>
                  <div className="feature-icon">{feature.icon}</div>
                  <h3>{feature.title}</h3>
                  <p>{feature.description}</p>
                </Card>
              </Col>
            ))}
          </Row>
        </div>
      </section>

      {/* 热门课程 */}
      <section className="courses-section" id="courses">
        <div className="section-content">
          <h2 className="section-title">热门课程</h2>
          <Row gutter={[24, 24]}>
            {courses.map((course, index) => (
              <Col xs={24} md={8} key={index}>
                <Card
                  hoverable
                  cover={<img alt={course.title} src={course.image} style={{ height: 200, objectFit: 'cover' }} />}
                  className="course-card"
                >
                  <Card.Meta
                    title={course.title}
                    description={course.description}
                  />
                  <Button type="link" style={{ marginTop: 16 }}>查看详情 →</Button>
                </Card>
              </Col>
            ))}
          </Row>
        </div>
      </section>

      {/* 页脚 */}
      <footer className="landing-footer">
        <div className="footer-content">
          <div className="footer-section">
            <h4>智能教育学习系统</h4>
            <p>基于认知诊断的大学计算机课程学习平台</p>
          </div>
          <div className="footer-section">
            <h4>快速链接</h4>
            <a href="#home">首页</a>
            <a href="#features">平台特色</a>
            <a href="#courses">热门课程</a>
          </div>
          <div className="footer-section">
            <h4>联系我们</h4>
            <p>邮箱: contact@aied.edu.cn</p>
            <p>地址: 某某大学</p>
          </div>
        </div>
        <div className="footer-bottom">
          <p>© 2025 智能教育学习系统. All rights reserved.</p>
        </div>
      </footer>

      {/* 登录/注册Modal */}
      <Modal
        title={null}
        open={loginModalVisible}
        onCancel={() => setLoginModalVisible(false)}
        footer={null}
        width={400}
      >
        <Tabs
          defaultActiveKey="login"
          centered
          items={[
            {
              key: 'login',
              label: '登录',
              children: (
                <Form form={loginForm} onFinish={handleLogin} layout="vertical">
                  <Form.Item
                    name="username"
                    rules={[{ required: true, message: '请输入用户名' }]}
                  >
                    <Input prefix={<UserOutlined />} placeholder="用户名/学号" size="large" />
                  </Form.Item>
                  <Form.Item
                    name="password"
                    rules={[{ required: true, message: '请输入密码' }]}
                  >
                    <Input.Password prefix={<LockOutlined />} placeholder="密码" size="large" />
                  </Form.Item>
                  <Form.Item>
                    <Button type="primary" htmlType="submit" block size="large" loading={loading}>
                      登录
                    </Button>
                  </Form.Item>
                </Form>
              )
            },
            {
              key: 'register',
              label: '注册',
              children: (
                <Form form={registerForm} onFinish={handleRegister} layout="vertical">
                  <Form.Item
                    name="role"
                    rules={[{ required: true, message: '请选择角色' }]}
                    initialValue="student"
                  >
                    <Radio.Group size="large" style={{ width: '100%' }}>
                      <Radio.Button value="student" style={{ width: '50%', textAlign: 'center' }}>
                        学生
                      </Radio.Button>
                      <Radio.Button value="teacher" style={{ width: '50%', textAlign: 'center' }}>
                        教师
                      </Radio.Button>
                    </Radio.Group>
                  </Form.Item>
                  <Form.Item
                    name="username"
                    rules={[{ required: true, message: '请输入用户名' }]}
                  >
                    <Input prefix={<UserOutlined />} placeholder="用户名" size="large" />
                  </Form.Item>
                  <Form.Item
                    name="email"
                    rules={[
                      { required: true, message: '请输入邮箱' },
                      { type: 'email', message: '请输入有效的邮箱地址' }
                    ]}
                  >
                    <Input prefix={<MailOutlined />} placeholder="邮箱" size="large" />
                  </Form.Item>
                  <Form.Item
                    name="password"
                    rules={[{ required: true, message: '请输入密码' }]}
                  >
                    <Input.Password prefix={<LockOutlined />} placeholder="密码" size="large" />
                  </Form.Item>
                  <Form.Item
                    name="confirm"
                    dependencies={['password']}
                    rules={[
                      { required: true, message: '请确认密码' },
                      ({ getFieldValue }) => ({
                        validator(_, value) {
                          if (!value || getFieldValue('password') === value) {
                            return Promise.resolve()
                          }
                          return Promise.reject(new Error('两次输入的密码不一致'))
                        },
                      }),
                    ]}
                  >
                    <Input.Password prefix={<LockOutlined />} placeholder="确认密码" size="large" />
                  </Form.Item>
                  <Form.Item>
                    <Button type="primary" htmlType="submit" block size="large" loading={loading}>
                      注册
                    </Button>
                  </Form.Item>
                </Form>
              )
            }
          ]}
        />
      </Modal>
    </div>
  )
}

export default Landing
