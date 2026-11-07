import { useEffect, useState } from 'react'
import { Card, Select, Space, Typography, Button, Radio, Checkbox, message, Tag, Divider, Alert, Spin } from 'antd'
import { CheckCircleOutlined, CloseCircleOutlined, LeftOutlined, RightOutlined } from '@ant-design/icons'
import { useSearchParams } from 'react-router-dom'
import { courseApi, questionApi } from '@/services/api'

const { Title, Text, Paragraph } = Typography

interface PracticeProps {
  studentId: number
}

const Practice = ({ studentId }: PracticeProps) => {
  const [searchParams] = useSearchParams()
  const [courses, setCourses] = useState<any[]>([])
  const [selectedCourse, setSelectedCourse] = useState<number | null>(null)
  const [questions, setQuestions] = useState<any[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answer, setAnswer] = useState<string>('')
  const [submitted, setSubmitted] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [coursesLoading, setCoursesLoading] = useState(true)
  const [startTime, setStartTime] = useState(Date.now())
  // 记录每道题的答案和提交状态
  const [questionAnswers, setQuestionAnswers] = useState<Record<number, { answer: string; result: any; submitted: boolean }>>({})

  useEffect(() => {
    fetchCourses()
  }, [])

  // 监听URL参数变化，当courseId变化时更新selectedCourse
  useEffect(() => {
    const courseIdFromUrl = searchParams.get('courseId')
    if (courseIdFromUrl && courses.length > 0) {
      const courseId = parseInt(courseIdFromUrl, 10)
      if (!isNaN(courseId)) {
        // 验证课程ID是否存在于课程列表中
        const courseExists = courses.some(c => c.id === courseId)
        if (courseExists) {
          // 只有当当前选中的课程与URL中的课程不同时才更新
          setSelectedCourse(prev => prev !== courseId ? courseId : prev)
        }
      }
    } else if (courses.length > 0) {
      // 如果没有URL参数，使用第一个课程（但只在selectedCourse为null时设置）
      setSelectedCourse(prev => prev === null ? courses[0].id : prev)
    }
  }, [searchParams, courses])

  useEffect(() => {
    if (selectedCourse) {
      fetchQuestions(selectedCourse)
      // 切换学生或课程时，重置答案记录（但保留URL参数中的questionId定位）
      setQuestionAnswers({})
      setAnswer('')
      setSubmitted(false)
      setResult(null)
    }
  }, [selectedCourse, studentId])

  // 当切换题目时，自动加载该题目的答案（如果有）
  useEffect(() => {
    if (questions.length > 0 && currentIndex >= 0 && currentIndex < questions.length) {
      const currentQ = questions[currentIndex]
      const savedAnswer = questionAnswers[currentQ?.id]
      if (savedAnswer) {
        setAnswer(savedAnswer.answer)
        setResult(savedAnswer.result)
        setSubmitted(savedAnswer.submitted)
      } else {
        setAnswer('')
        setSubmitted(false)
        setResult(null)
      }
      setStartTime(Date.now())
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentIndex, questions.length])

  const fetchCourses = async () => {
    try {
      setCoursesLoading(true)
      const data = await courseApi.getCourses()
      setCourses(data)
      // 注意：不在这里设置selectedCourse，而是在useEffect中根据URL参数设置
    } catch (error) {
      console.error('Failed to fetch courses:', error)
    } finally {
      setCoursesLoading(false)
    }
  }

  const fetchQuestions = async (courseId: number) => {
    try {
      setLoading(true)
      const data = await courseApi.getQuestions(courseId)
      setQuestions(data)
      
      // 检查URL参数中是否有questionId，如果有则定位到该题目
      const questionIdFromUrl = searchParams.get('questionId')
      if (questionIdFromUrl && data.length > 0) {
        const questionId = parseInt(questionIdFromUrl, 10)
        if (!isNaN(questionId)) {
          const questionIndex = data.findIndex((q: any) => q.id === questionId)
          if (questionIndex >= 0) {
            setCurrentIndex(questionIndex)
            // 清除URL参数中的questionId，避免刷新时重复定位
            const newSearchParams = new URLSearchParams(searchParams)
            newSearchParams.delete('questionId')
            window.history.replaceState({}, '', `${window.location.pathname}?${newSearchParams.toString()}`)
          } else {
            setCurrentIndex(0)
          }
        } else {
          setCurrentIndex(0)
        }
      } else {
        setCurrentIndex(0)
      }
      
      setQuestionAnswers({}) // 清空答案记录
      setAnswer('')
      setSubmitted(false)
      setResult(null)
      setStartTime(Date.now())
    } catch (error) {
      console.error('Failed to fetch questions:', error)
      message.error('获取题目失败')
      setQuestions([]) // 确保在错误时清空题目列表
      setCurrentIndex(0)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async () => {
    if (!answer) {
      message.warning('请选择答案')
      return
    }

    if (questions.length === 0 || currentIndex < 0 || currentIndex >= questions.length) {
      message.error('题目信息错误')
      return
    }

    // 防止重复提交
    if (submitted || loading) {
      return
    }

    const currentQ = questions[currentIndex]
    const timeSpent = Math.floor((Date.now() - startTime) / 1000)

    try {
      setLoading(true)
      const response = await questionApi.submitAnswer(currentQ.id, {
        student_id: studentId,
        answer,
        time_spent: timeSpent,
      })
      setResult(response)
      setSubmitted(true)
      
      // 保存答案记录
      setQuestionAnswers(prev => ({
        ...prev,
        [currentQ.id]: {
          answer,
          result: response,
          submitted: true
        }
      }))
    } catch (error) {
      console.error('Failed to submit answer:', error)
      message.error('提交失败')
    } finally {
      setLoading(false)
    }
  }

  // 保存当前题目的答案
  const saveCurrentAnswer = () => {
    if (questions.length > 0 && currentIndex >= 0 && currentIndex < questions.length) {
      const currentQ = questions[currentIndex]
      if (currentQ) {
        setQuestionAnswers(prev => ({
          ...prev,
          [currentQ.id]: {
            answer,
            result,
            submitted
          }
        }))
      }
    }
  }

  const handlePrevious = () => {
    if (currentIndex > 0) {
      saveCurrentAnswer()
      setCurrentIndex(currentIndex - 1)
    }
  }

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      saveCurrentAnswer()
      setCurrentIndex(currentIndex + 1)
    } else {
      saveCurrentAnswer()
      message.success('已完成所有题目！')
    }
  }

  const handleJumpToQuestion = (index: number) => {
    saveCurrentAnswer()
    setCurrentIndex(index)
  }

  // 如果课程列表还在加载，显示加载状态
  if (coursesLoading) {
    return (
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Title level={2}>在线答题</Title>
        <Card>
          <div style={{ textAlign: 'center', padding: '50px 0' }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>
              <Text type="secondary">正在加载课程列表...</Text>
            </div>
          </div>
        </Card>
      </Space>
    )
  }

  // 如果没有选中课程或没有题目（且不在加载中），显示选择界面
  if (!selectedCourse || (questions.length === 0 && !loading)) {
    return (
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={2}>在线答题</Title>
          <Select
            style={{ width: 300 }}
            value={selectedCourse || undefined}
            onChange={(value) => {
              setSelectedCourse(value)
              // 更新URL参数，但不触发页面刷新
              const newSearchParams = new URLSearchParams(searchParams)
              newSearchParams.set('courseId', value.toString())
              window.history.replaceState({}, '', `${window.location.pathname}?${newSearchParams.toString()}`)
            }}
            options={courses.map(c => ({ label: c.name, value: c.id }))}
            placeholder="请选择课程"
          />
        </div>
        <Card>
          <div style={{ textAlign: 'center', padding: '50px 0' }}>
            <Text type="secondary">
              {!selectedCourse ? '请先选择课程' : loading ? '正在加载题目...' : '暂无题目'}
            </Text>
          </div>
        </Card>
      </Space>
    )
  }

  // 确保有题目才渲染题目内容
  if (questions.length === 0 || currentIndex < 0 || currentIndex >= questions.length) {
    return (
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={2}>在线答题</Title>
          <Select
            style={{ width: 300 }}
            value={selectedCourse || undefined}
            onChange={(value) => {
              setSelectedCourse(value)
              // 更新URL参数，但不触发页面刷新
              const newSearchParams = new URLSearchParams(searchParams)
              newSearchParams.set('courseId', value.toString())
              window.history.replaceState({}, '', `${window.location.pathname}?${newSearchParams.toString()}`)
            }}
            options={courses.map(c => ({ label: c.name, value: c.id }))}
            placeholder="请选择课程"
          />
        </div>
        <Card>
          <div style={{ textAlign: 'center', padding: '50px 0' }}>
            <Text type="secondary">
              {loading ? '正在加载题目...' : '暂无题目'}
            </Text>
          </div>
        </Card>
      </Space>
    )
  }

  const currentQuestion = questions[currentIndex]
  const optionLabels = ['A', 'B', 'C', 'D', 'E', 'F']

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>在线答题</Title>
        <Select
          style={{ width: 300 }}
          value={selectedCourse || undefined}
          onChange={(value) => {
            setSelectedCourse(value)
            // 更新URL参数，但不触发页面刷新
            const newSearchParams = new URLSearchParams(searchParams)
            newSearchParams.set('courseId', value.toString())
            window.history.replaceState({}, '', `${window.location.pathname}?${newSearchParams.toString()}`)
          }}
          options={courses.map(c => ({ label: c.name, value: c.id }))}
          placeholder="请选择课程"
        />
      </div>

      <Card>
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Space>
              <Text strong>第 {currentIndex + 1} 题 / 共 {questions.length} 题</Text>
              {currentQuestion.knowledge_name && (
                <Tag color="purple">知识点: {currentQuestion.knowledge_name}</Tag>
              )}
              <Tag color={currentQuestion.difficulty === 1 ? 'green' : currentQuestion.difficulty === 2 ? 'orange' : 'red'}>
                {currentQuestion.difficulty === 1 ? '简单' : currentQuestion.difficulty === 2 ? '中等' : '困难'}
              </Tag>
              <Tag color="blue">
                {currentQuestion.question_type === 'single' ? '单选题' : currentQuestion.question_type === 'multiple' ? '多选题' : '判断题'}
              </Tag>
            </Space>
          </div>

          {/* 题目导航 */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
            {questions.map((q, index) => (
              <Button
                key={q.id}
                type={index === currentIndex ? 'primary' : questionAnswers[q.id]?.submitted ? 'default' : 'dashed'}
                size="small"
                onClick={() => handleJumpToQuestion(index)}
                style={{
                  minWidth: '40px',
                  backgroundColor: index === currentIndex 
                    ? undefined 
                    : questionAnswers[q.id]?.submitted 
                      ? (questionAnswers[q.id]?.result?.is_correct ? '#f6ffed' : '#fff1f0')
                      : undefined,
                  borderColor: questionAnswers[q.id]?.submitted
                    ? (questionAnswers[q.id]?.result?.is_correct ? '#b7eb8f' : '#ffccc7')
                    : undefined
                }}
              >
                {index + 1}
              </Button>
            ))}
          </div>

          <Divider />

          <div style={{ fontSize: '16px', lineHeight: '1.8' }}>
            <Text strong>{currentQuestion.content}</Text>
          </div>

          <div style={{ marginTop: 24 }}>
            {currentQuestion.question_type === 'multiple' ? (
              <Checkbox.Group
                value={answer ? answer.split('') : []}
                onChange={(values) => setAnswer(values.sort().join(''))}
                disabled={submitted}
              >
                <Space direction="vertical" size="middle">
                  {currentQuestion.options.map((option: string, index: number) => (
                    <Checkbox key={index} value={optionLabels[index]}>
                      <span style={{ fontSize: '15px' }}>
                        {optionLabels[index]}. {option}
                      </span>
                    </Checkbox>
                  ))}
                </Space>
              </Checkbox.Group>
            ) : (
              <Radio.Group
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                disabled={submitted}
              >
                <Space direction="vertical" size="middle">
                  {currentQuestion.options.map((option: string, index: number) => (
                    <Radio key={index} value={optionLabels[index]}>
                      <span style={{ fontSize: '15px' }}>
                        {optionLabels[index]}. {option}
                      </span>
                    </Radio>
                  ))}
                </Space>
              </Radio.Group>
            )}
          </div>

          {submitted && result && (
            <Alert
              message={result.is_correct ? '回答正确！' : '回答错误'}
              description={
                <Space direction="vertical">
                  <Text>正确答案：{result.correct_answer}</Text>
                  <Text>{result.explanation}</Text>
                </Space>
              }
              type={result.is_correct ? 'success' : 'error'}
              icon={result.is_correct ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
              showIcon
            />
          )}

          <div style={{ marginTop: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Button 
              icon={<LeftOutlined />} 
              disabled={currentIndex === 0}
              onClick={handlePrevious}
            >
              上一题
            </Button>
            <Space>
              {!submitted && (
                <Button 
                  type="primary" 
                  size="large" 
                  onClick={handleSubmit}
                  disabled={!answer || loading}
                  loading={loading}
                >
                  提交答案
                </Button>
              )}
            </Space>
            <Button 
              type="primary"
              icon={<RightOutlined />} 
              disabled={currentIndex === questions.length - 1}
              onClick={handleNext}
            >
              {currentIndex < questions.length - 1 ? '下一题' : '完成'}
            </Button>
          </div>
        </Space>
      </Card>
    </Space>
  )
}

export default Practice

