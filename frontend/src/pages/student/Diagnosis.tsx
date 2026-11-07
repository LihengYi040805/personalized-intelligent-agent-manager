import { useEffect, useState } from 'react'
import { Card, Select, Space, Typography, Button, Spin, Empty, Row, Col, Progress, Tag, List, Alert, Radio, message, Tooltip } from 'antd'
import { TrophyOutlined, RocketOutlined, BulbOutlined, InfoCircleOutlined, ExclamationCircleOutlined, EditOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import ReactECharts from 'echarts-for-react'
import { courseApi, studentApi } from '@/services/api'

const { Title, Text, Paragraph } = Typography

interface DiagnosisProps {
  studentId: number
}

const Diagnosis = ({ studentId }: DiagnosisProps) => {
  const navigate = useNavigate()
  const [courses, setCourses] = useState<any[]>([])
  const [selectedCourse, setSelectedCourse] = useState<number>(1)
  const [selectedAlgorithm, setSelectedAlgorithm] = useState<string>('IRT')
  const [diagnosis, setDiagnosis] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [modelStatus, setModelStatus] = useState<{ [key: number]: boolean }>({})

  useEffect(() => {
    fetchCourses()
  }, [])

  // 当 studentId 变化时，重置状态
  useEffect(() => {
    setDiagnosis(null)
    setError(null)
    setModelStatus({})
  }, [studentId])

  useEffect(() => {
    if (selectedCourse && studentId) {
      fetchLatestDiagnosis()
      checkModelStatus(selectedCourse)
    }
  }, [selectedCourse, studentId])

  useEffect(() => {
    // 当切换算法时，清除错误信息
    if (selectedAlgorithm === 'IRT') {
      setError(null)
    } else if (selectedAlgorithm === 'NCDM') {
      // 检查NCDM模型状态
      if (selectedCourse) {
        checkModelStatus(selectedCourse)
      }
    }
  }, [selectedAlgorithm, selectedCourse])

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

  const fetchLatestDiagnosis = async () => {
    try {
      setLoading(true)
      const data = await studentApi.getLatestDiagnosis(studentId, selectedCourse)
      setDiagnosis(data.result)
    } catch (error) {
      console.error('No diagnosis report found')
      setDiagnosis(null)
    } finally {
      setLoading(false)
    }
  }

  const checkModelStatus = async (courseId: number) => {
    try {
      // 检查NCDM模型是否存在
      const apiBase = import.meta.env.VITE_API_BASE_URL || ''
      const response = await fetch(`${apiBase}/api/ncdm/check-model/${courseId}`)
      if (response.ok) {
        const data = await response.json()
        setModelStatus(prev => ({ ...prev, [courseId]: data.exists }))
        if (!data.exists && selectedAlgorithm === 'NCDM') {
          setError('NCDM模型尚未训练，请先联系教师训练模型，或使用IRT算法进行诊断')
        } else {
          setError(null)
        }
      }
    } catch (error) {
      console.error('检查模型状态失败:', error)
    }
  }

  const handleGenerate = async () => {
    // 如果选择NCDM但模型不存在，显示提示
    if (selectedAlgorithm === 'NCDM' && !modelStatus[selectedCourse]) {
      message.warning('NCDM模型尚未训练，请先联系教师训练模型，或使用IRT算法进行诊断')
      return
    }

    try {
      setGenerating(true)
      setError(null)
      const data = await studentApi.generateDiagnosis(studentId, selectedCourse, selectedAlgorithm)
      setDiagnosis(data)
      message.success('诊断报告生成成功！')
    } catch (error: any) {
      console.error('Failed to generate diagnosis:', error)
      setDiagnosis(null)
      
      // 显示错误提示
      if (error?.response?.data?.error) {
        const errorMsg = error.response.data.error
        setError(errorMsg)
        message.error(errorMsg)
        
        // 如果是模型未训练的错误，更新模型状态
        if (errorMsg.includes('模型文件不存在') || errorMsg.includes('模型未训练')) {
          setModelStatus(prev => ({ ...prev, [selectedCourse]: false }))
        }
      } else {
        const defaultError = '生成诊断报告失败，请稍后重试'
        setError(defaultError)
        message.error(defaultError)
      }
    } finally {
      setGenerating(false)
    }
  }

  const getRadarOption = () => {
    if (!diagnosis || !diagnosis.knowledge_mastery) {
      return {}
    }

    const knowledgeData = diagnosis.knowledge_mastery

    return {
      title: {
        text: '知识点掌握雷达图',
      },
      tooltip: {},
      radar: {
        indicator: knowledgeData.map((k: any) => ({
          name: k.knowledge_name,
          max: 100,
        })),
      },
      series: [
        {
          type: 'radar',
          data: [
            {
              value: knowledgeData.map((k: any) => k.mastery_level),
              name: '掌握度',
              areaStyle: {
                color: 'rgba(24, 144, 255, 0.2)',
              },
              lineStyle: {
                color: '#1890ff',
                width: 2,
              },
            },
          ],
        },
      ],
    }
  }

  const getBarOption = () => {
    if (!diagnosis || !diagnosis.knowledge_mastery) {
      return {}
    }

    const knowledgeData = diagnosis.knowledge_mastery.sort(
      (a: any, b: any) => a.mastery_level - b.mastery_level
    )

    return {
      title: {
        text: '各知识点掌握情况',
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow',
        },
      },
      xAxis: {
        type: 'value',
        max: 100,
      },
      yAxis: {
        type: 'category',
        data: knowledgeData.map((k: any) => k.knowledge_name),
      },
      series: [
        {
          type: 'bar',
          data: knowledgeData.map((k: any) => ({
            value: k.mastery_level,
            itemStyle: {
              color: k.mastery_level >= 80 ? '#52c41a' : k.mastery_level >= 60 ? '#1890ff' : '#ff4d4f',
            },
          })),
          label: {
            show: true,
            position: 'right',
            formatter: '{c}%',
          },
        },
      ],
    }
  }

  const getStatusTag = (status: string) => {
    const statusMap: { [key: string]: { color: string; text: string } } = {
      mastered: { color: 'success', text: '已掌握' },
      learning: { color: 'processing', text: '学习中' },
      struggling: { color: 'warning', text: '需加强' },
      weak: { color: 'error', text: '薄弱' },
      not_started: { color: 'default', text: '未开始' },
    }
    const statusInfo = statusMap[status] || statusMap.not_started
    return <Tag color={statusInfo.color}>{statusInfo.text}</Tag>
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>认知诊断</Title>
        <Space>
          <Select
            style={{ width: 300 }}
            value={selectedCourse}
            onChange={setSelectedCourse}
            options={courses.map(c => ({ label: c.name, value: c.id }))}
          />
          <Radio.Group 
            value={selectedAlgorithm} 
            onChange={(e) => setSelectedAlgorithm(e.target.value)}
            buttonStyle="solid"
          >
            <Radio.Button value="IRT">
              <Space>
                <span>IRT算法</span>
                <Tooltip title="项目反应理论，基于统计模型的认知诊断方法">
                  <InfoCircleOutlined style={{ fontSize: 12 }} />
                </Tooltip>
              </Space>
            </Radio.Button>
            <Radio.Button value="NCDM">
              <Space>
                <span>NCDM算法</span>
                {selectedAlgorithm === 'NCDM' && !modelStatus[selectedCourse] && (
                  <Tooltip title="NCDM模型尚未训练，请先联系教师训练模型">
                    <ExclamationCircleOutlined style={{ fontSize: 12, color: '#ff4d4f' }} />
                  </Tooltip>
                )}
                <Tooltip title="神经网络认知诊断模型，基于深度学习的认知诊断方法">
                  <InfoCircleOutlined style={{ fontSize: 12 }} />
                </Tooltip>
              </Space>
            </Radio.Button>
          </Radio.Group>
          <Button 
            type="primary" 
            onClick={handleGenerate} 
            loading={generating}
            disabled={selectedAlgorithm === 'NCDM' && !modelStatus[selectedCourse]}
          >
            生成诊断报告
          </Button>
        </Space>
      </div>

      {/* 错误提示 */}
      {error && (
        <Alert
          message="诊断失败"
          description={error}
          type="error"
          showIcon
          closable
          onClose={() => setError(null)}
          style={{ marginBottom: 16 }}
        />
      )}

      {/* NCDM模型未训练提示 */}
      {selectedAlgorithm === 'NCDM' && !modelStatus[selectedCourse] && !error && (
        <Alert
          message="NCDM模型尚未训练"
          description={
            <div>
              <p>当前课程尚未训练NCDM模型，无法使用NCDM算法进行诊断。</p>
              <p>您可以：</p>
              <ul style={{ margin: '8px 0', paddingLeft: 20 }}>
                <li>使用IRT算法进行诊断（无需训练，可直接使用）</li>
                <li>联系教师为当前课程训练NCDM模型</li>
              </ul>
            </div>
          }
          type="warning"
          showIcon
          icon={<ExclamationCircleOutlined />}
          style={{ marginBottom: 16 }}
        />
      )}

      {loading ? (
        <Card>
          <div style={{ textAlign: 'center', padding: '100px 0' }}>
            <Spin size="large" />
          </div>
        </Card>
      ) : diagnosis ? (
        <>
          {/* 总体掌握情况 */}
          <Card>
            <Row gutter={[24, 24]} align="middle">
              <Col xs={24} md={8} style={{ textAlign: 'center' }}>
                <Progress
                  type="circle"
                  percent={diagnosis.overall_mastery}
                  width={180}
                  strokeColor={{
                    '0%': '#108ee9',
                    '100%': '#87d068',
                  }}
                  format={(percent) => (
                    <div>
                      <div style={{ fontSize: '32px', fontWeight: 'bold' }}>{percent}%</div>
                      <div style={{ fontSize: '14px', color: '#999' }}>总体掌握度</div>
                    </div>
                  )}
                />
              </Col>
              <Col xs={24} md={16}>
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text strong style={{ fontSize: '16px' }}>诊断总结</Text>
                    {diagnosis.algorithm && (
                      <Tag color="blue" style={{ fontSize: '14px' }}>
                        使用算法: {diagnosis.algorithm === 'IRT' ? 'IRT（项目反应理论）' : 'NCDM（神经网络认知诊断）'}
                      </Tag>
                    )}
                  </div>
                  <Row gutter={[16, 16]}>
                    <Col span={8}>
                      <Card size="small">
                        <div style={{ textAlign: 'center' }}>
                          <TrophyOutlined style={{ fontSize: 24, color: '#52c41a' }} />
                          <div style={{ marginTop: 8 }}>优势知识点</div>
                          <div style={{ fontSize: 24, fontWeight: 'bold', color: '#52c41a' }}>
                            {diagnosis.strong_knowledges?.length || 0}
                          </div>
                        </div>
                      </Card>
                    </Col>
                    <Col span={8}>
                      <Card size="small">
                        <div style={{ textAlign: 'center' }}>
                          <RocketOutlined style={{ fontSize: 24, color: '#1890ff' }} />
                          <div style={{ marginTop: 8 }}>学习中</div>
                          <div style={{ fontSize: 24, fontWeight: 'bold', color: '#1890ff' }}>
                            {diagnosis.knowledge_mastery?.filter((k: any) => k.mastery_level >= 60 && k.mastery_level < 80).length || 0}
                          </div>
                        </div>
                      </Card>
                    </Col>
                    <Col span={8}>
                      <Card size="small">
                        <div style={{ textAlign: 'center' }}>
                          <BulbOutlined style={{ fontSize: 24, color: '#ff4d4f' }} />
                          <div style={{ marginTop: 8 }}>薄弱知识点</div>
                          <div style={{ fontSize: 24, fontWeight: 'bold', color: '#ff4d4f' }}>
                            {diagnosis.weak_knowledges?.length || 0}
                          </div>
                        </div>
                      </Card>
                    </Col>
                  </Row>
                </Space>
              </Col>
            </Row>
          </Card>

          {/* 知识点详细分析 */}
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card>
                <ReactECharts option={getRadarOption()} style={{ height: '400px' }} />
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card>
                <ReactECharts option={getBarOption()} style={{ height: '400px' }} />
              </Card>
            </Col>
          </Row>

          {/* 知识点列表 */}
          <Card title="知识点掌握详情">
            <List
              dataSource={diagnosis.knowledge_mastery}
              renderItem={(item: any) => (
                <List.Item>
                  <List.Item.Meta
                    title={
                      <Space>
                        <Text strong>{item.knowledge_name}</Text>
                        {getStatusTag(item.status)}
                      </Space>
                    }
                    description={
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <Progress percent={item.mastery_level} size="small" />
                        <Text type="secondary">
                          已练习 {item.attempted_questions}/{item.total_questions} 题 | 
                          正确率 {item.accuracy}% | 
                          平均难度 {item.avg_difficulty.toFixed(1)}
                        </Text>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>

          {/* 学习建议 */}
          {diagnosis.suggestions && diagnosis.suggestions.length > 0 && (
            <Card title="学习建议">
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                {diagnosis.suggestions.map((suggestion: any, index: number) => (
                  <Alert
                    key={index}
                    message={suggestion.title}
                    description={suggestion.content}
                    type={suggestion.type === 'congratulation' ? 'success' : suggestion.type === 'prerequisite' ? 'warning' : 'info'}
                    showIcon
                  />
                ))}
              </Space>
            </Card>
          )}

          {/* 推荐题目 */}
          {diagnosis.recommended_questions && diagnosis.recommended_questions.length > 0 && (
            <Card title="推荐练习题目">
              <List
                dataSource={diagnosis.recommended_questions}
                renderItem={(question: any) => (
                  <List.Item
                    style={{ 
                      cursor: 'pointer',
                      padding: '12px',
                      borderRadius: '4px',
                      transition: 'background-color 0.3s'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = '#f5f5f5'
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent'
                    }}
                    onClick={() => {
                      // 跳转到在线答题页面，并传递课程ID和题目ID
                      navigate(`/student/practice?courseId=${question.course_id || selectedCourse}&questionId=${question.question_id}`)
                    }}
                    actions={[
                      <Button 
                        type="link" 
                        icon={<EditOutlined />}
                        onClick={(e) => {
                          e.stopPropagation()
                          navigate(`/student/practice?courseId=${question.course_id || selectedCourse}&questionId=${question.question_id}`)
                        }}
                      >
                        开始答题
                      </Button>
                    ]}
                  >
                    <List.Item.Meta
                      title={
                        <Text 
                          style={{ 
                            fontSize: '15px',
                            color: '#1890ff',
                            textDecoration: 'underline'
                          }}
                        >
                          {question.content}
                        </Text>
                      }
                      description={
                        <Space>
                          <Tag color="blue">{question.knowledge_name}</Tag>
                          <Tag color={question.difficulty === 1 ? 'green' : question.difficulty === 2 ? 'orange' : 'red'}>
                            难度 {question.difficulty}
                          </Tag>
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            </Card>
          )}
        </>
      ) : (
        <Card>
          <Empty
            description='暂无诊断报告，请先完成一些练习题，然后点击"生成诊断报告"按钮'
            style={{ padding: '50px 0' }}
          />
        </Card>
      )}
    </Space>
  )
}

export default Diagnosis

