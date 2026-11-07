import { useEffect, useState } from 'react'
import { Card, Table, Tag, Space, Typography, Button, Select, message, Modal, Empty } from 'antd'
import { EyeOutlined, BarChartOutlined, HistoryOutlined, CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined } from '@ant-design/icons'
import { teacherApi, studentApi, courseApi } from '@/services/api'

const { Title } = Typography

const StudentsManagement = () => {
  const [courses, setCourses] = useState<any[]>([])
  const [selectedCourse, setSelectedCourse] = useState<number>(1)
  const [studentsData, setStudentsData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [diagnosisVisible, setDiagnosisVisible] = useState(false)
  const [recordsVisible, setRecordsVisible] = useState(false)
  const [selectedStudent, setSelectedStudent] = useState<any>(null)
  const [diagnosisData, setDiagnosisData] = useState<any>(null)
  const [recordsData, setRecordsData] = useState<any[]>([])
  const [recordsLoading, setRecordsLoading] = useState(false)

  useEffect(() => {
    fetchCourses()
  }, [])

  useEffect(() => {
    if (selectedCourse) {
      fetchStudentsData()
    }
  }, [selectedCourse])

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

  const fetchStudentsData = async () => {
    try {
      setLoading(true)
      const data = await teacherApi.getStudentsOverview(selectedCourse)
      setStudentsData(data)
    } catch (error) {
      console.error('Failed to fetch students data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleViewDiagnosis = async (student: any) => {
    setSelectedStudent(student)
    setDiagnosisVisible(true)
    
    try {
      const data = await studentApi.getLatestDiagnosis(student.id, selectedCourse)
      setDiagnosisData(data.result)
    } catch (error) {
      console.error('Failed to fetch diagnosis:', error)
      message.warning('该学生暂无诊断报告')
    }
  }

  const handleViewRecords = async (student: any) => {
    setSelectedStudent(student)
    setRecordsVisible(true)
    setRecordsData([])
    
    try {
      setRecordsLoading(true)
      const data = await studentApi.getQuestionRecords(student.id, selectedCourse)
      setRecordsData(data)
    } catch (error) {
      console.error('Failed to fetch records:', error)
      message.error('获取答题记录失败')
      setRecordsData([])
    } finally {
      setRecordsLoading(false)
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
      title: '姓名',
      dataIndex: 'name',
      key: 'name',
      fixed: 'left' as const,
    },
    {
      title: '工号',
      dataIndex: 'employee_id',
      key: 'employee_id',
    },
    {
      title: '部门',
      dataIndex: 'department',
      key: 'department',
    },
    {
      title: '总答题数',
      dataIndex: 'total_questions',
      key: 'total_questions',
      sorter: (a: any, b: any) => a.total_questions - b.total_questions,
    },
    {
      title: '答对题数',
      dataIndex: 'correct_questions',
      key: 'correct_questions',
      sorter: (a: any, b: any) => a.correct_questions - b.correct_questions,
    },
    {
      title: '正确率',
      dataIndex: 'accuracy',
      key: 'accuracy',
      sorter: (a: any, b: any) => a.accuracy - b.accuracy,
      render: (accuracy: number) => (
        <Tag color={accuracy >= 80 ? 'success' : accuracy >= 60 ? 'processing' : 'error'}>
          {accuracy}%
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right' as const,
      render: (_: any, record: any) => (
        <Space>
          <Button
            type="link"
            icon={<BarChartOutlined />}
            onClick={() => handleViewDiagnosis(record)}
          >
            诊断报告
          </Button>
          <Button
            type="link"
            icon={<HistoryOutlined />}
            onClick={() => handleViewRecords(record)}
          >
            答题记录
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>学生管理</Title>
        <Select
          style={{ width: 300 }}
          value={selectedCourse}
          onChange={setSelectedCourse}
          options={courses.map(c => ({ label: c.name, value: c.id }))}
        />
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={studentsData}
          rowKey="id"
          loading={loading}
          scroll={{ x: 'max-content' }}
          pagination={{
            pageSize: 10,
            showTotal: (total) => `共 ${total} 名学生`,
          }}
        />
      </Card>

      <Modal
        title={
          <Space>
            <BarChartOutlined />
            <span>{selectedStudent?.name} 的认知诊断报告</span>
          </Space>
        }
        open={diagnosisVisible}
        onCancel={() => {
          setDiagnosisVisible(false)
          setDiagnosisData(null)
        }}
        footer={null}
        width={800}
      >
        {diagnosisData ? (
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <Card size="small">
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
                  <strong>总体掌握度：</strong>
                  <Tag color={diagnosisData.overall_mastery >= 80 ? 'success' : diagnosisData.overall_mastery >= 60 ? 'processing' : 'error'}>
                    {diagnosisData.overall_mastery}%
                  </Tag>
                </div>
                <div>
                  <strong>优势知识点：</strong>{diagnosisData.strong_knowledges?.length || 0} 个
                </div>
                <div>
                  <strong>薄弱知识点：</strong>{diagnosisData.weak_knowledges?.length || 0} 个
                </div>
              </Space>
            </Card>

            {diagnosisData.weak_knowledges && diagnosisData.weak_knowledges.length > 0 && (
              <Card size="small" title="薄弱知识点">
                <Space direction="vertical" style={{ width: '100%' }}>
                  {diagnosisData.weak_knowledges.map((weak: any, index: number) => (
                    <div key={index}>
                      <Tag color="error">{weak.knowledge_name}</Tag>
                      <span>掌握度：{weak.mastery_level}%</span>
                    </div>
                  ))}
                </Space>
              </Card>
            )}

            {diagnosisData.suggestions && diagnosisData.suggestions.length > 0 && (
              <Card size="small" title="学习建议">
                <Space direction="vertical" style={{ width: '100%' }}>
                  {diagnosisData.suggestions.map((suggestion: any, index: number) => (
                    <div key={index}>
                      <div><strong>{suggestion.title}</strong></div>
                      <div style={{ color: '#666' }}>{suggestion.content}</div>
                    </div>
                  ))}
                </Space>
              </Card>
            )}
          </Space>
        ) : (
          <div style={{ textAlign: 'center', padding: '50px 0' }}>
            该学生暂无诊断报告
          </div>
        )}
      </Modal>

      <Modal
        title={
          <Space>
            <HistoryOutlined />
            <span>{selectedStudent?.name} 的答题记录</span>
          </Space>
        }
        open={recordsVisible}
        onCancel={() => {
          setRecordsVisible(false)
          setRecordsData([])
        }}
        footer={null}
        width={1200}
      >
        {recordsLoading ? (
          <div style={{ textAlign: 'center', padding: '50px 0' }}>
            加载中...
          </div>
        ) : recordsData.length > 0 ? (
          <Table
            columns={[
              {
                title: '题目内容',
                dataIndex: 'question_content',
                key: 'question_content',
                width: 300,
                ellipsis: true,
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
                title: '学生答案',
                dataIndex: 'student_answer',
                key: 'student_answer',
                width: 120,
                render: (answer: string, record: any) => (
                  <Space>
                    <Typography.Text>{answer || '未作答'}</Typography.Text>
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
                    <Typography.Text>{formatTime(time)}</Typography.Text>
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
            ]}
            dataSource={recordsData}
            rowKey="id"
            scroll={{ x: 'max-content', y: 500 }}
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
        ) : (
          <Empty
            description="该学生暂无答题记录"
            style={{ padding: '50px 0' }}
          />
        )}
      </Modal>
    </Space>
  )
}

export default StudentsManagement

