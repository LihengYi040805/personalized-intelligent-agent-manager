import { useEffect, useState } from 'react'
import { Card, Table, Tag, Space, Typography, Select, Empty } from 'antd'
import { CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined } from '@ant-design/icons'
import { studentApi, courseApi } from '@/services/api'

const { Title, Text } = Typography

interface QuestionRecordsProps {
  studentId: number
}

const QuestionRecords = ({ studentId }: QuestionRecordsProps) => {
  const [courses, setCourses] = useState<any[]>([])
  const [selectedCourse, setSelectedCourse] = useState<number | null>(null)
  const [records, setRecords] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchCourses()
  }, [])

  useEffect(() => {
    if (selectedCourse !== null) {
      fetchRecords()
    }
  }, [selectedCourse, studentId])

  const fetchCourses = async () => {
    try {
      const data = await courseApi.getCourses()
      setCourses(data)
      if (data.length > 0) {
        setSelectedCourse(data[0].id)
      }
    } catch (error) {
      console.error('Failed to fetch courses:', error)
    }
  }

  const fetchRecords = async () => {
    try {
      setLoading(true)
      const data = await studentApi.getQuestionRecords(
        studentId, 
        selectedCourse || undefined
      )
      setRecords(data)
    } catch (error) {
      console.error('Failed to fetch records:', error)
      setRecords([])
    } finally {
      setLoading(false)
    }
  }

  const formatTime = (seconds: number) => {
    if (seconds < 60) {
      return `${seconds}秒`
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60)
      const secs = seconds % 60
      return `${minutes}分${secs}秒`
    } else {
      const hours = Math.floor(seconds / 3600)
      const minutes = Math.floor((seconds % 3600) / 60)
      return `${hours}小时${minutes}分`
    }
  }

  const getDifficultyTag = (difficulty: number) => {
    const config = {
      1: { color: 'success', text: '简单' },
      2: { color: 'warning', text: '中等' },
      3: { color: 'error', text: '困难' },
    }
    const { color, text } = config[difficulty as keyof typeof config] || { color: 'default', text: '未知' }
    return <Tag color={color}>{text}</Tag>
  }

  const getQuestionTypeTag = (type: string) => {
    const config: { [key: string]: { color: string; text: string } } = {
      single: { color: 'blue', text: '单选题' },
      multiple: { color: 'purple', text: '多选题' },
      judge: { color: 'cyan', text: '判断题' },
    }
    const { color, text } = config[type] || { color: 'default', text: '未知' }
    return <Tag color={color}>{text}</Tag>
  }

  const columns = [
    {
      title: '题目内容',
      dataIndex: 'question_content',
      key: 'question_content',
      width: 300,
      ellipsis: true,
      render: (text: string) => (
        <Text ellipsis={{ tooltip: text }} style={{ maxWidth: 300 }}>
          {text}
        </Text>
      ),
    },
    {
      title: '知识点',
      dataIndex: 'knowledge_name',
      key: 'knowledge_name',
      width: 150,
    },
    {
      title: '题目类型',
      dataIndex: 'question_type',
      key: 'question_type',
      width: 100,
      render: (type: string) => getQuestionTypeTag(type),
    },
    {
      title: '难度',
      dataIndex: 'difficulty',
      key: 'difficulty',
      width: 80,
      render: (difficulty: number) => getDifficultyTag(difficulty),
    },
    {
      title: '我的答案',
      dataIndex: 'student_answer',
      key: 'student_answer',
      width: 120,
      render: (answer: string, record: any) => (
        <Space>
          <Text>{answer || '未作答'}</Text>
          {record.is_correct ? (
            <CheckCircleOutlined style={{ color: '#52c41a' }} />
          ) : (
            <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
          )}
        </Space>
      ),
    },
    {
      title: '正确答案',
      dataIndex: 'correct_answer',
      key: 'correct_answer',
      width: 120,
    },
    {
      title: '结果',
      key: 'is_correct',
      width: 100,
      render: (_: any, record: any) => (
        <Tag color={record.is_correct ? 'success' : 'error'} icon={record.is_correct ? <CheckCircleOutlined /> : <CloseCircleOutlined />}>
          {record.is_correct ? '正确' : '错误'}
        </Tag>
      ),
    },
    {
      title: '答题时长',
      dataIndex: 'time_spent',
      key: 'time_spent',
      width: 120,
      render: (time: number) => (
        <Space>
          <ClockCircleOutlined />
          <Text>{formatTime(time)}</Text>
        </Space>
      ),
    },
    {
      title: '答题时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      sorter: (a: any, b: any) => {
        const dateA = new Date(a.created_at).getTime()
        const dateB = new Date(b.created_at).getTime()
        return dateA - dateB
      },
      defaultSortOrder: 'descend' as const,
    },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>我的答题记录</Title>
        <Select
          style={{ width: 300 }}
          value={selectedCourse}
          onChange={setSelectedCourse}
          options={[
            { label: '全部课程', value: null },
            ...courses.map(c => ({ label: c.name, value: c.id }))
          ]}
        />
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={records}
          rowKey="id"
          loading={loading}
          scroll={{ x: 'max-content' }}
          pagination={{
            pageSize: 10,
            showTotal: (total) => `共 ${total} 条记录`,
            showSizeChanger: true,
            showQuickJumper: true,
          }}
          locale={{
            emptyText: (
              <Empty
                description="暂无答题记录"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            ),
          }}
        />
      </Card>
    </Space>
  )
}

export default QuestionRecords

