import { Card, Row, Col, Typography, Space, Button } from 'antd'
import { UserOutlined, TeamOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import './RoleSelection.css'

const { Title, Paragraph } = Typography

const RoleSelection = () => {
  const navigate = useNavigate()

  return (
    <div className="role-selection-container">
      <div className="role-selection-content">
        <Space direction="vertical" size="large" style={{ width: '100%', textAlign: 'center' }}>
          <div>
            <Button 
              type="link" 
              onClick={() => navigate('/')} 
              style={{ position: 'absolute', top: 24, left: 24, color: 'white' }}
            >
              ← 返回首页
            </Button>
            <Title level={1}>智能教育学习系统</Title>
            <Paragraph style={{ fontSize: '16px', color: 'rgba(255, 255, 255, 0.9)' }}>
              基于认知诊断的大学计算机课程学习平台
            </Paragraph>
          </div>

          <Row gutter={[32, 32]} justify="center" style={{ marginTop: '40px' }}>
            <Col xs={24} sm={12} md={10} lg={8}>
              <Card
                hoverable
                className="role-card"
                onClick={() => navigate('/student')}
              >
                <div className="role-card-content">
                  <UserOutlined className="role-icon student-icon" />
                  <Title level={3}>学生端</Title>
                  <Paragraph>
                    课程学习、在线答题、认知诊断报告、学习进度追踪
                  </Paragraph>
                </div>
              </Card>
            </Col>

            <Col xs={24} sm={12} md={10} lg={8}>
              <Card
                hoverable
                className="role-card"
                onClick={() => navigate('/teacher')}
              >
                <div className="role-card-content">
                  <TeamOutlined className="role-icon teacher-icon" />
                  <Title level={3}>教师端</Title>
                  <Paragraph>
                    学生管理、认知诊断分析、智能题库、薄弱知识点分析
                  </Paragraph>
                </div>
              </Card>
            </Col>
          </Row>
        </Space>
      </div>
    </div>
  )
}

export default RoleSelection

