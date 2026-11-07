import { useEffect, useState } from 'react'
import { Card, List, Tag, Space, Typography, Spin, Button } from 'antd'
import { 
  BookOutlined, 
  ClockCircleOutlined, 
  EditOutlined, 
  CodeOutlined, 
  DatabaseOutlined,
  LaptopOutlined 
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { courseApi } from '@/services/api'
import './CourseList.css'

const { Title, Paragraph } = Typography

// 默认课程图片配置（当数据库中没有图片时使用）
const defaultCourseImages: { [key: string]: string } = {
  'C语言': 'https://images.unsplash.com/photo-1542831371-29b0f74f9713?w=800&h=400&fit=crop',
  '数据库': 'https://images.unsplash.com/photo-1544383835-bda2bc66a55d?w=800&h=400&fit=crop',
  '编程': 'https://images.unsplash.com/photo-1515879218367-8466d910aaa4?w=800&h=400&fit=crop',
  'default': 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=800&h=400&fit=crop'
}

// 获取课程图片：优先使用数据库中的图片，否则根据课程名称匹配默认图片
const getCourseImage = (course: any) => {
  // 如果数据库中有图片，直接使用
  if (course.cover_image) {
    return course.cover_image
  }
  
  // 否则根据课程名称匹配默认图片
  for (const key in defaultCourseImages) {
    if (course.name.includes(key)) {
      return defaultCourseImages[key]
    }
  }
  return defaultCourseImages['default']
}

const CourseList = () => {
  const navigate = useNavigate()
  const [courses, setCourses] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchCourses()
  }, [])

  const fetchCourses = async () => {
    try {
      const data = await courseApi.getCourses()
      setCourses(data)
    } catch (error) {
      console.error('Failed to fetch courses:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleStartPractice = (courseId: number) => {
    navigate(`/student/practice?courseId=${courseId}`)
  }

  if (loading) {
    return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Title level={2}>课程学习</Title>
      
      <List
        grid={{ gutter: 16, xs: 1, sm: 1, md: 2, lg: 2, xl: 3, xxl: 3 }}
        dataSource={courses}
        renderItem={(course, index) => {
          const courseImage = getCourseImage(course)
          
          return (
          <List.Item>
            <Card
              hoverable
              cover={
                <div style={{ 
                  height: 180, 
                  width: '100%',
                  overflow: 'hidden',
                  position: 'relative',
                  background: '#f0f0f0'
                }}>
                  <img 
                    src={courseImage}
                    alt={course.name}
                    style={{
                      width: '100%',
                      height: '100%',
                      objectFit: 'cover',
                      display: 'block'
                    }}
                    onError={(e) => {
                      // 图片加载失败时显示渐变背景
                      const target = e.target as HTMLImageElement
                      target.style.display = 'none'
                      if (target.parentElement) {
                        target.parentElement.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                      }
                    }}
                  />
                </div>
              }
              actions={[
                <Button
                  type="primary"
                  icon={<EditOutlined />}
                  onClick={() => handleStartPractice(course.id)}
                  style={{ width: '100%' }}
                >
                  开始答题
                </Button>
              ]}
            >
              <Card.Meta
                title={<Title level={4} style={{ marginBottom: 12 }}>{course.name}</Title>}
                description={
                  <Space direction="vertical" size="small" style={{ width: '100%', minHeight: '80px' }}>
                    <Paragraph 
                      ellipsis={{ rows: 2 }}
                      style={{ 
                        marginBottom: 12,
                        minHeight: '48px',
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden'
                      }}
                    >
                      {course.description}
                    </Paragraph>
                    <Space>
                      <Tag icon={<ClockCircleOutlined />} color="blue">
                        {course.total_hours}学时
                      </Tag>
                    </Space>
                  </Space>
                }
              />
            </Card>
          </List.Item>
        )}}
      />
    </Space>
  )
}

export default CourseList

