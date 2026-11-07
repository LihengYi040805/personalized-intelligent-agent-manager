import { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, Typography, Space, Progress, List, Select, Tag, Empty } from 'antd'
import { BookOutlined, EditOutlined, CheckCircleOutlined, TrophyOutlined } from '@ant-design/icons'
import { studentApi, courseApi } from '@/services/api'

const { Title, Text } = Typography

interface HomeProps {
  studentId: number
}

const StudentHome = ({ studentId }: HomeProps) => {
  const [studentInfo, setStudentInfo] = useState<any>(null)
  const [courses, setCourses] = useState<any[]>([])
  const [selectedCourse, setSelectedCourse] = useState<number | null>(null)
  const [progress, setProgress] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [studentId])

  const fetchData = async () => {
    try {
      setLoading(true)
      const [studentData, coursesData] = await Promise.all([
        studentApi.getStudentDetail(studentId),
        courseApi.getCourses(),
      ])
      
      setStudentInfo(studentData)
      setCourses(coursesData)
      
      // 设置默认选中第一门课程
      if (coursesData.length > 0 && !selectedCourse) {
        setSelectedCourse(coursesData[0].id)
      }
    } catch (error) {
      console.error('Failed to fetch data:', error)
    } finally {
      setLoading(false)
    }
  }

  // 当选择课程变化时，获取该课程的学习进度
  useEffect(() => {
    if (selectedCourse) {
      fetchProgress(selectedCourse)
    }
  }, [selectedCourse, studentId])

  const fetchProgress = async (courseId: number) => {
    try {
      setLoading(true)
      const progressData = await studentApi.getLearningProgress(studentId, courseId)
      setProgress(progressData)
    } catch (error) {
      console.error('Failed to fetch progress:', error)
      setProgress([])
    } finally {
      setLoading(false)
    }
  }

  const overallProgress = progress.length > 0
    ? Math.round(progress.reduce((sum, p) => sum + p.mastery_level, 0) / progress.length)
    : 0

  // 获取状态标签
  const getStatusTag = (masteryLevel: number) => {
    if (masteryLevel >= 80) {
      return <Tag color="success">已掌握</Tag>
    } else if (masteryLevel >= 60) {
      return <Tag color="processing">学习中</Tag>
    } else if (masteryLevel > 0) {
      return <Tag color="warning">需加强</Tag>
    } else {
      return <Tag color="default">未开始</Tag>
    }
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Title level={2}>学习概况</Title>
      
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总答题数"
              value={studentInfo?.total_questions || 0}
              prefix={<EditOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="答对题数"
              value={studentInfo?.correct_questions || 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="正确率"
              value={studentInfo?.accuracy || 0}
              suffix="%"
              prefix={<TrophyOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="课程数量"
              value={courses.length}
              prefix={<BookOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card 
            title={
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>学习进度</span>
                {courses.length > 0 && (
                  <Select
                    style={{ width: 250 }}
                    value={selectedCourse}
                    onChange={setSelectedCourse}
                    options={courses.map(c => ({ label: c.name, value: c.id }))}
                  />
                )}
              </div>
            }
            loading={loading}
          >
            {progress.length > 0 ? (
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <div>
                  <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text strong>整体进度</Text>
                    <Text strong style={{ fontSize: '16px', color: '#1890ff' }}>{overallProgress}%</Text>
                  </div>
                  <Progress 
                    percent={overallProgress} 
                    status={overallProgress >= 80 ? 'success' : overallProgress >= 60 ? 'normal' : 'active'}
                    strokeColor={{
                      '0%': '#108ee9',
                      '100%': '#87d068',
                    }}
                  />
                </div>
                
                <div style={{ maxHeight: '500px', overflowY: 'auto', paddingRight: '8px' }}>
                  <List
                    dataSource={progress}
                    renderItem={(item: any) => (
                      <List.Item style={{ padding: '12px 0', borderBottom: '1px solid #f0f0f0' }}>
                        <div style={{ width: '100%' }}>
                          <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Text strong style={{ fontSize: '15px' }}>{item.knowledge_name}</Text>
                            {getStatusTag(item.mastery_level)}
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <Progress 
                              percent={item.mastery_level} 
                              size="small"
                              style={{ flex: 1 }}
                              status={item.mastery_level >= 80 ? 'success' : item.mastery_level >= 60 ? 'normal' : item.mastery_level > 0 ? 'active' : 'exception'}
                            />
                            <Text type="secondary" style={{ minWidth: '50px', textAlign: 'right' }}>
                              {item.mastery_level.toFixed(0)}%
                            </Text>
                          </div>
                          {item.attempted_questions !== undefined && (
                            <Text type="secondary" style={{ fontSize: '12px', marginTop: '4px', display: 'block' }}>
                              已练习 {item.attempted_questions || 0} 题 | 正确率 {item.accuracy || 0}%
                            </Text>
                          )}
                        </div>
                      </List.Item>
                    )}
                  />
                </div>
              </Space>
            ) : (
              <Empty 
                description="暂无学习进度数据" 
                style={{ padding: '40px 0' }}
              />
            )}
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card title="我的课程" loading={loading}>
            {courses.length > 0 ? (
              <List
                dataSource={courses}
                renderItem={(course: any) => (
                  <List.Item
                    style={{ 
                      cursor: 'pointer',
                      backgroundColor: selectedCourse === course.id ? '#e6f7ff' : 'transparent',
                      borderRadius: '4px',
                      padding: '12px',
                      marginBottom: '8px'
                    }}
                    onClick={() => setSelectedCourse(course.id)}
                  >
                    <List.Item.Meta
                      avatar={<BookOutlined style={{ fontSize: 24, color: '#1890ff' }} />}
                      title={course.name}
                      description={
                        <Text type="secondary" ellipsis style={{ fontSize: '12px' }}>
                          {course.description || '暂无描述'}
                        </Text>
                      }
                    />
                  </List.Item>
                )}
              />
            ) : (
              <Empty description="暂无课程" style={{ padding: '40px 0' }} />
            )}
          </Card>
        </Col>
      </Row>
    </Space>
  )
}

export default StudentHome

