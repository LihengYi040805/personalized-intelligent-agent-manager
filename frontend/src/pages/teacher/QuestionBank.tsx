import { useEffect, useState } from 'react'
import { Card, Table, Tag, Space, Typography, Select, Button, Modal, Form, Input, InputNumber, Radio, message, Popconfirm } from 'antd'
import { FileTextOutlined, PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { courseApi } from '@/services/api'
import axios from 'axios'

const { Title, Text } = Typography
const { TextArea } = Input

const QuestionBank = () => {
  const [courses, setCourses] = useState<any[]>([])
  const [selectedCourse, setSelectedCourse] = useState<number | null>(null)  // null 表示"所有课程"
  const [questions, setQuestions] = useState<any[]>([])
  const [knowledges, setKnowledges] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [editingQuestion, setEditingQuestion] = useState<any>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    fetchCourses()
    fetchAllData()  // 首次加载所有数据
  }, [])

  useEffect(() => {
    if (selectedCourse !== null) {
      fetchData()
    } else {
      fetchAllData()  // 选择"所有课程"时加载所有数据
    }
  }, [selectedCourse])

  const fetchCourses = async () => {
    try {
      const data = await courseApi.getCourses()
      setCourses(data)
    } catch (error) {
      console.error('Failed to fetch courses:', error)
    }
  }

  const fetchAllData = async () => {
    try {
      setLoading(true)
      // 获取所有题目和知识点
      const apiBase = import.meta.env.VITE_API_BASE_URL || ''
      const response = await axios.get(`${apiBase}/api/questions`)
      const allQuestions = response.data
      
      const knowledgeResponse = await axios.get(`${apiBase}/api/knowledges`)
      const allKnowledges = knowledgeResponse.data
      
      setQuestions(allQuestions)
      setKnowledges(allKnowledges)
    } catch (error) {
      console.error('Failed to fetch all data:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchData = async () => {
    try {
      setLoading(true)
      const [questionsData, knowledgesData] = await Promise.all([
        courseApi.getQuestions(selectedCourse!),
        courseApi.getKnowledges(selectedCourse!),
      ])
      setQuestions(questionsData)
      setKnowledges(knowledgesData)
    } catch (error) {
      console.error('Failed to fetch data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getKnowledgeName = (knowledgeId: number) => {
    const knowledge = knowledges.find(k => k.id === knowledgeId)
    return knowledge ? knowledge.name : '未知'
  }

  const handleEdit = (record: any) => {
    setEditingQuestion(record)
    form.setFieldsValue({
      ...record,
      options: record.options.join('\n')  // 将选项数组转换为多行文本
    })
    setEditModalVisible(true)
  }

  const handleDelete = async (id: number) => {
    try {
      const apiBase = import.meta.env.VITE_API_BASE_URL || ''
      await axios.delete(`${apiBase}/api/questions/${id}`)
      message.success('删除成功')
      fetchData()  // 刷新列表
    } catch (error) {
      message.error('删除失败')
      console.error('Failed to delete question:', error)
    }
  }

  const handleEditSubmit = async () => {
    try {
      const values = await form.validateFields()
      
      // 处理选项：将多行文本转换为数组
      const optionsArray = values.options.split('\n').filter((opt: string) => opt.trim())
      
      const updateData = {
        ...values,
        options: optionsArray
      }

      const apiBase = import.meta.env.VITE_API_BASE_URL || ''
      await axios.put(`${apiBase}/api/questions/${editingQuestion.id}`, updateData)
      message.success('更新成功')
      setEditModalVisible(false)
      form.resetFields()
      setEditingQuestion(null)
      fetchData()  // 刷新列表
    } catch (error) {
      message.error('更新失败')
      console.error('Failed to update question:', error)
    }
  }

  // 为题目添加序号（按课程分组）
  const getQuestionNumber = (question: any) => {
    // 按ID排序后的题目列表
    const sortedQuestions = [...questions].sort((a, b) => a.id - b.id)
    
    if (selectedCourse === null) {
      // "所有课程"模式：按course_id分组编号
      const sameCourseQuestions = sortedQuestions.filter(q => q.course_id === question.course_id)
      const indexInCourse = sameCourseQuestions.findIndex(q => q.id === question.id)
      return indexInCourse + 1
    } else {
      // 特定课程模式：从1开始编号
      const indexInCourse = sortedQuestions.findIndex(q => q.id === question.id)
      return indexInCourse + 1
    }
  }

  const columns = [
    {
      title: '序号',
      key: 'number',
      width: 70,
      render: (_: any, record: any) => getQuestionNumber(record),
    },
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: '题目内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      render: (text: string) => <Text style={{ maxWidth: 400 }}>{text}</Text>,
    },
    {
      title: '知识点',
      dataIndex: 'knowledge_id',
      key: 'knowledge_id',
      render: (knowledgeId: number) => (
        <Tag color="blue">{getKnowledgeName(knowledgeId)}</Tag>
      ),
      filters: knowledges.map(k => ({ text: k.name, value: k.id })),
      onFilter: (value: any, record: any) => record.knowledge_id === value,
    },
    {
      title: '题型',
      dataIndex: 'question_type',
      key: 'question_type',
      render: (type: string) => (
        <Tag color={type === 'single' ? 'green' : type === 'multiple' ? 'orange' : 'purple'}>
          {type === 'single' ? '单选' : type === 'multiple' ? '多选' : '判断'}
        </Tag>
      ),
      filters: [
        { text: '单选', value: 'single' },
        { text: '多选', value: 'multiple' },
        { text: '判断', value: 'judge' },
      ],
      onFilter: (value: any, record: any) => record.question_type === value,
    },
    {
      title: '难度',
      dataIndex: 'difficulty',
      key: 'difficulty',
      render: (difficulty: number) => (
        <Tag color={difficulty === 1 ? 'green' : difficulty === 2 ? 'orange' : 'red'}>
          {difficulty === 1 ? '简单' : difficulty === 2 ? '中等' : '困难'}
        </Tag>
      ),
      filters: [
        { text: '简单', value: 1 },
        { text: '中等', value: 2 },
        { text: '困难', value: 3 },
      ],
      onFilter: (value: any, record: any) => record.difficulty === value,
      sorter: (a: any, b: any) => a.difficulty - b.difficulty,
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space>
          <Button 
            type="link" 
            size="small" 
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确认删除"
            description="确定要删除这道题目吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button 
              type="link" 
              size="small" 
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  // 统计数据
  const stats = {
    total: questions.length,
    single: questions.filter(q => q.question_type === 'single').length,
    multiple: questions.filter(q => q.question_type === 'multiple').length,
    easy: questions.filter(q => q.difficulty === 1).length,
    medium: questions.filter(q => q.difficulty === 2).length,
    hard: questions.filter(q => q.difficulty === 3).length,
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>题库管理</Title>
        <Space>
          <Select
            style={{ width: 300 }}
            value={selectedCourse}
            onChange={setSelectedCourse}
            placeholder="选择课程"
            options={[
              { label: '所有课程', value: null },
              ...courses.map(c => ({ label: c.name, value: c.id }))
            ]}
          />
          <Button type="primary" icon={<PlusOutlined />}>
            添加题目
          </Button>
        </Space>
      </div>

      <Card>
        <Space size="large">
          <div>
            <FileTextOutlined style={{ fontSize: 24, color: '#1890ff', marginRight: 8 }} />
            <span>总题数：<strong>{stats.total}</strong></span>
          </div>
          <div>单选题：<strong>{stats.single}</strong></div>
          <div>多选题：<strong>{stats.multiple}</strong></div>
          <div>|</div>
          <div><Tag color="green">简单 {stats.easy}</Tag></div>
          <div><Tag color="orange">中等 {stats.medium}</Tag></div>
          <div><Tag color="red">困难 {stats.hard}</Tag></div>
        </Space>
      </Card>

      <Card>
        <Table
          columns={columns}
          dataSource={[...questions].sort((a, b) => a.id - b.id)}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showTotal: (total) => `共 ${total} 道题目`,
          }}
        />
      </Card>

      {/* 编辑题目Modal */}
      <Modal
        title="编辑题目"
        open={editModalVisible}
        onOk={handleEditSubmit}
        onCancel={() => {
          setEditModalVisible(false)
          form.resetFields()
          setEditingQuestion(null)
        }}
        width={800}
        okText="保存"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            question_type: 'single',
            difficulty: 2
          }}
        >
          <Form.Item
            name="content"
            label="题目内容"
            rules={[{ required: true, message: '请输入题目内容' }]}
          >
            <TextArea rows={4} placeholder="请输入题目内容" />
          </Form.Item>

          <Form.Item
            name="question_type"
            label="题型"
            rules={[{ required: true }]}
          >
            <Radio.Group>
              <Radio value="single">单选题</Radio>
              <Radio value="multiple">多选题</Radio>
              <Radio value="judge">判断题</Radio>
            </Radio.Group>
          </Form.Item>

          <Form.Item
            name="options"
            label="选项（每行一个选项）"
            rules={[{ required: true, message: '请输入选项' }]}
            extra="每行输入一个选项，如：选项A的内容"
          >
            <TextArea 
              rows={6} 
              placeholder="选项A的内容&#10;选项B的内容&#10;选项C的内容&#10;选项D的内容"
            />
          </Form.Item>

          <Form.Item
            name="answer"
            label="正确答案"
            rules={[{ required: true, message: '请输入正确答案' }]}
            extra="单选题输入A/B/C/D，多选题输入ABC/ABD等"
          >
            <Input placeholder="如：A 或 ABC" />
          </Form.Item>

          <Form.Item
            name="difficulty"
            label="难度"
            rules={[{ required: true }]}
          >
            <Radio.Group>
              <Radio value={1}>简单</Radio>
              <Radio value={2}>中等</Radio>
              <Radio value={3}>困难</Radio>
            </Radio.Group>
          </Form.Item>

          <Form.Item
            name="knowledge_id"
            label="知识点"
            rules={[{ required: true, message: '请选择知识点' }]}
          >
            <Select
              placeholder="请选择知识点"
              options={knowledges.map(k => ({ label: k.name, value: k.id }))}
            />
          </Form.Item>
        </Form>
      </Modal>
    </Space>
  )
}

export default QuestionBank

