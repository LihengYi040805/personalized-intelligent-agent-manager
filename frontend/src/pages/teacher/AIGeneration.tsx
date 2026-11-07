import { useState } from 'react'
import { Card, Upload, Button, Space, Typography, message, Progress, Alert, Input, Divider, Steps, Tag, Tooltip } from 'antd'
import { InboxOutlined, RobotOutlined, CheckCircleOutlined, LoadingOutlined, UnorderedListOutlined, EyeOutlined, FileImageOutlined } from '@ant-design/icons'
import type { UploadProps } from 'antd'
import { useNavigate } from 'react-router-dom'

const { Title, Text, Paragraph } = Typography
const { Dragger } = Upload

const AIGeneration = () => {
  const navigate = useNavigate()
  const [uploading, setUploading] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [courseName, setCourseName] = useState('')
  const [result, setResult] = useState<any>(null)
  const [progress, setProgress] = useState(0)
  const [generatedQuestions, setGeneratedQuestions] = useState<any[]>([])
  const [generatedKnowledges, setGeneratedKnowledges] = useState<any[]>([])
  const [statusMessage, setStatusMessage] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    accept: '.txt,.md,.markdown,.pdf,.doc,.docx',
    beforeUpload: (file) => {
      setSelectedFile(file)
      return false  // 阻止自动上传
    },
    onRemove: () => {
      setSelectedFile(null)
    },
    showUploadList: true,
    maxCount: 1,
  }

  const handleUpload = async (file: File) => {
    setUploading(true)
    setCurrentStep(1)
    setProgress(5)
    setResult(null)
    setGeneratedQuestions([])
    setGeneratedKnowledges([])
    setStatusMessage('准备上传文档...')

    const formData = new FormData()
    formData.append('file', file)
    if (courseName) {
      formData.append('course_name', courseName)
    }

    try {
      // 使用fetch进行流式上传
      const apiBase = import.meta.env.VITE_API_BASE_URL || ''
      const response = await fetch(`${apiBase}/api/ai/upload-document-stream`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('上传失败')
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('无法读取响应流')
      }

      let progressValue = 10

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6))
              
              switch (data.type) {
                case 'start':
                  setStatusMessage(data.message)
                  setProgress(10)
                  break
                
                case 'status':
                  setStatusMessage(data.message)
                  progressValue = Math.min(progressValue + 5, 85)
                  setProgress(progressValue)
                  break
                
                case 'course':
                  setStatusMessage(`课程创建成功: ${data.data.name}`)
                  setProgress(20)
                  break
                
                case 'knowledge':
                  setGeneratedKnowledges(prev => [...prev, data.data])
                  setStatusMessage(`提取知识点: ${data.data.name}`)
                  setProgress(30)
                  break
                
                case 'question':
                  setGeneratedQuestions(prev => [...prev, data.data])
                  progressValue = Math.min(progressValue + 2, 90)
                  setProgress(progressValue)
                  break
                
                case 'complete':
                  setProgress(100)
                  setCurrentStep(2)
                  setResult(data.data)
                  setStatusMessage('生成完成！')
                  message.success('课程生成成功！')
                  break
                
                case 'error':
                  message.error(data.message || '生成失败')
                  setCurrentStep(0)
                  setUploading(false)
                  return
              }
            } catch (e) {
              console.error('解析SSE数据失败:', e)
            }
          }
        }
      }
      
    } catch (error: any) {
      message.error(error.message || '上传失败')
      setCurrentStep(0)
    } finally {
      setUploading(false)
    }
  }

  const steps = [
    {
      title: '上传文档',
      icon: currentStep > 0 ? <CheckCircleOutlined /> : undefined,
    },
    {
      title: 'AI分析生成',
      icon: currentStep === 1 ? <LoadingOutlined /> : currentStep > 1 ? <CheckCircleOutlined /> : undefined,
    },
    {
      title: '完成',
      icon: currentStep === 2 ? <CheckCircleOutlined /> : undefined,
    },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <RobotOutlined style={{ fontSize: 32, color: '#1890ff' }} />
        <Title level={2} style={{ margin: 0 }}>AI智能题库生成</Title>
      </div>

      <Alert
        message="功能说明"
        description={
          <div>
            <Paragraph>
              上传课程相关的教学文档（支持 TXT、PDF、Word 格式），AI 将自动：
            </Paragraph>
            <ul style={{ marginBottom: 0 }}>
              <li>🧠 提取并组织知识点（含知识点层级和依赖关系）</li>
              <li>✍️ 自动生成高质量练习题（单选题、多选题）</li>
              <li>🎯 标注题目难度和知识点考察关系</li>
              <li>📊 建立完整的知识图谱结构</li>
            </ul>
          </div>
        }
        type="info"
        showIcon
      />

      {/* Deepseek-OCR 技术亮点 */}
      <Card 
        size="small" 
        style={{ 
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
          border: 'none',
          borderRadius: 12
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ 
            background: 'rgba(255,255,255,0.2)', 
            borderRadius: 12, 
            padding: 12,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <EyeOutlined style={{ fontSize: 32, color: '#fff' }} />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
              <Text strong style={{ color: '#fff', fontSize: 16 }}>
                🔍 Deepseek-OCR 智能文档解析
              </Text>
              <Tag color="#52c41a" style={{ margin: 0 }}>AI驱动</Tag>
            </div>
            <Text style={{ color: 'rgba(255,255,255,0.85)', fontSize: 13 }}>
              采用 <Text strong style={{ color: '#fff' }}>Deepseek 多模态大模型</Text> 进行 OCR 识别，
              支持<Text strong style={{ color: '#ffd666' }}>扫描版 PDF</Text>、
              <Text strong style={{ color: '#ffd666' }}>图片型文档</Text>，
              精准提取文字、表格、公式，识别准确率高达 <Text strong style={{ color: '#95de64' }}>99%+</Text>
            </Text>
          </div>
          <Tooltip title="支持扫描件、截图、拍照文档等图片型PDF的智能识别">
            <div style={{ 
              background: 'rgba(255,255,255,0.15)', 
              borderRadius: 8, 
              padding: '8px 16px',
              cursor: 'pointer'
            }}>
              <FileImageOutlined style={{ color: '#fff', marginRight: 6 }} />
              <Text style={{ color: '#fff', fontSize: 12 }}>支持扫描件</Text>
            </div>
          </Tooltip>
        </div>
      </Card>

      <Steps current={currentStep} items={steps} />

      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Text strong>课程名称（可选）</Text>
            <Input
              placeholder="留空则由AI自动识别课程名称"
              value={courseName}
              onChange={(e) => setCourseName(e.target.value)}
              disabled={uploading}
              style={{ marginTop: 8 }}
              size="large"
            />
          </div>

          <Divider />

          <Dragger {...uploadProps} disabled={uploading}>
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p className="ant-upload-hint">
              支持的格式：.txt, .md, .markdown, .pdf, .doc, .docx<br />
              <Text type="success">✨ PDF 文档将使用 Deepseek-OCR 智能解析（支持扫描件）</Text><br />
              文件大小限制：16MB
            </p>
          </Dragger>

          <Button
            type="primary"
            size="large"
            block
            onClick={() => {
              if (selectedFile) {
                handleUpload(selectedFile)
              } else {
                message.warning('请先选择文件')
              }
            }}
            loading={uploading}
            disabled={uploading || !selectedFile}
          >
            {uploading ? 'AI正在生成中...' : '开始生成'}
          </Button>

          {uploading && (
            <div>
              <Progress percent={progress} status="active" />
              <Text type="secondary" style={{ marginTop: 8, display: 'block', textAlign: 'center' }}>
                {statusMessage}
              </Text>
            </div>
          )}

          {/* 实时显示生成的知识点 */}
          {generatedKnowledges.length > 0 && (
            <Card size="small" title={`已提取 ${generatedKnowledges.length} 个知识点`} style={{ marginTop: 16 }}>
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                {generatedKnowledges.map((k, idx) => (
                  <div key={idx}>
                    <Text strong>{k.name}</Text>
                    <Text type="secondary" style={{ fontSize: 12, display: 'block' }}>{k.description}</Text>
                  </div>
                ))}
              </Space>
            </Card>
          )}

          {/* 实时显示生成的题目 */}
          {generatedQuestions.length > 0 && (
            <Card size="small" title={`已生成 ${generatedQuestions.length} 道题目`} style={{ marginTop: 16 }}>
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                {generatedQuestions.slice(-5).map((q, idx) => (
                  <div key={idx} style={{ padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}>
                    <Text ellipsis style={{ width: '100%', display: 'block' }}>
                      <Tag color="blue">{q.knowledge_name}</Tag>
                      <Tag color={q.difficulty === 1 ? 'green' : q.difficulty === 2 ? 'orange' : 'red'}>
                        {q.difficulty === 1 ? '简单' : q.difficulty === 2 ? '中等' : '困难'}
                      </Tag>
                      {q.content}
                    </Text>
                  </div>
                ))}
                {generatedQuestions.length > 5 && (
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    （显示最新5条，共{generatedQuestions.length}条）
                  </Text>
                )}
              </Space>
            </Card>
          )}
        </Space>
      </Card>

      {result && (
        <Card title="生成结果" style={{ borderColor: '#52c41a' }}>
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <Alert
              message="课程生成成功！"
              description={
                <div>
                  <p><strong>课程名称：</strong>{result.course_name}</p>
                  <p><strong>课程ID：</strong>{result.course_id}</p>
                  <p><strong>知识点数量：</strong>{result.knowledge_count} 个</p>
                  <p><strong>题目数量：</strong>{result.question_count} 道</p>
                </div>
              }
              type="success"
              showIcon
            />

            <Space>
              <Button 
                type="primary"
                icon={<UnorderedListOutlined />}
                onClick={() => navigate('/teacher/question-bank')}
              >
                查看题库
              </Button>
              <Button onClick={() => {
                setCurrentStep(0)
                setResult(null)
                setProgress(0)
                setCourseName('')
                setSelectedFile(null)
                setGeneratedQuestions([])
                setGeneratedKnowledges([])
                setStatusMessage('')
              }}>
                继续生成
              </Button>
            </Space>
          </Space>
        </Card>
      )}

      <Card title="💡 使用建议">
        <Space direction="vertical">
          <Text>1. 文档内容应清晰、结构化，包含完整的知识点说明</Text>
          <Text>2. 建议文档字数在 1000-10000 字之间，效果最佳</Text>
          <Text>3. 文档应包含具体的知识点、概念、操作步骤等信息</Text>
          <Text>4. PDF 文档请确保文字可以被正常提取（非扫描版）</Text>
          <Text>5. Markdown 文件可以保留格式，AI 能够理解标题和列表结构</Text>
          <Text>6. 生成后可在题库管理中查看和编辑题目</Text>
        </Space>
      </Card>
    </Space>
  )
}

export default AIGeneration

