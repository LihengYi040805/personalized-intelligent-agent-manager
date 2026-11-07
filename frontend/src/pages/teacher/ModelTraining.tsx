import { useState, useEffect } from 'react'
import { Card, Button, Space, Typography, message, Progress, Alert, Select, InputNumber, Tag, Statistic, Row, Col, Divider } from 'antd'
import { PlayCircleOutlined, CheckCircleOutlined, LoadingOutlined, ThunderboltOutlined } from '@ant-design/icons'
import { courseApi } from '@/services/api'

const { Title, Text, Paragraph } = Typography
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

const ModelTraining = () => {
  const [courses, setCourses] = useState<any[]>([])
  const [selectedCourse, setSelectedCourse] = useState<number | null>(null)
  const [training, setTraining] = useState(false)
  const [progress, setProgress] = useState(0)
  const [statusMessage, setStatusMessage] = useState('')
  const [currentEpoch, setCurrentEpoch] = useState(0)
  const [totalEpochs, setTotalEpochs] = useState(20)
  const [epochMetrics, setEpochMetrics] = useState<any>(null)
  const [trainingResult, setTrainingResult] = useState<any>(null)
  const [device, setDevice] = useState<string>('')

  useEffect(() => {
    fetchCourses()
  }, [])

  const fetchCourses = async () => {
    try {
      const data = await courseApi.getCourses()
      setCourses(data)
      if (data.length > 0 && !selectedCourse) {
        setSelectedCourse(data[0].id)
      }
    } catch (error) {
      console.error('Failed to fetch courses:', error)
    }
  }

  const handleTrain = async () => {
    if (!selectedCourse) {
      message.warning('请选择课程')
      return
    }

    setTraining(true)
    setProgress(0)
    setStatusMessage('准备开始训练...')
    setCurrentEpoch(0)
    setEpochMetrics(null)
    setTrainingResult(null)

    try {
      const response = await fetch(`${API_BASE_URL}/api/ncdm/train-stream/${selectedCourse}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          epochs: totalEpochs,
          batch_size: 32,
          lr: 0.002
        })
      })

      if (!response.ok) {
        throw new Error('训练请求失败')
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('无法读取响应流')
      }

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
                case 'info':
                  setStatusMessage(data.message)
                  if (data.message.includes('GPU')) {
                    setDevice('cuda')
                  } else if (data.message.includes('CPU')) {
                    setDevice('cpu')
                  }
                  break
                
                case 'start':
                  setStatusMessage(data.message)
                  setTotalEpochs(data.total_epochs)
                  setProgress(5)
                  break
                
                case 'epoch_start':
                  setCurrentEpoch(data.epoch)
                  setStatusMessage(data.message)
                  setProgress(Math.min(5 + (data.epoch - 1) * 90 / data.total_epochs, 90))
                  break
                
                case 'training':
                  setStatusMessage(data.message)
                  // 训练阶段的进度（在epoch内部）
                  const epochProgress = (data.epoch - 1) * 90 / data.total_epochs
                  const batchProgress = data.progress * 0.9 / data.total_epochs
                  setProgress(Math.min(5 + epochProgress + batchProgress, 90))
                  break
                
                case 'evaluating':
                  setStatusMessage(data.message)
                  break
                
                case 'epoch':
                  setCurrentEpoch(data.epoch)
                  setEpochMetrics({
                    epoch: data.epoch,
                    loss: data.loss,
                    auc: data.auc,
                    accuracy: data.accuracy,
                    rmse: data.rmse,
                    f1: data.f1,
                    best_epoch: data.best_epoch,
                    best_auc: data.best_auc
                  })
                  setStatusMessage(data.message)
                  setProgress(data.progress)
                  break
                
                case 'saving':
                  setStatusMessage(data.message)
                  setProgress(95)
                  break
                
                case 'complete':
                  setStatusMessage(data.message)
                  setProgress(100)
                  setTrainingResult({
                    best_epoch: data.best_epoch,
                    best_auc: data.best_auc,
                    best_acc: data.best_acc || 0,
                    best_rmse: data.best_rmse || 0,
                    model_path: data.model_path
                  })
                  message.success('模型训练完成！')
                  setTraining(false)
                  break
                
                case 'error':
                  message.error(data.message || '训练失败')
                  setTraining(false)
                  setStatusMessage('训练失败')
                  return
              }
            } catch (e) {
              console.error('解析SSE消息失败:', e)
            }
          }
        }
      }
    } catch (error: any) {
      console.error('训练失败:', error)
      message.error(error.message || '训练失败')
      setTraining(false)
    }
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>NCDM模型训练</Title>
      </div>

      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Text strong>选择课程</Text>
            <Select
              style={{ width: '100%', marginTop: 8 }}
              value={selectedCourse}
              onChange={setSelectedCourse}
              options={courses.map(c => ({ label: c.name, value: c.id }))}
              disabled={training}
              size="large"
            />
          </div>

          <Divider />

          <div>
            <Text strong>训练参数</Text>
            <Space style={{ marginTop: 8, width: '100%' }} size="middle">
              <div style={{ flex: 1 }}>
                <Text type="secondary">训练轮数 (Epochs)</Text>
                <InputNumber
                  style={{ width: '100%', marginTop: 4 }}
                  min={1}
                  max={100}
                  value={totalEpochs}
                  onChange={(val) => val && setTotalEpochs(val)}
                  disabled={training}
                />
              </div>
              <div style={{ flex: 1 }}>
                <Text type="secondary">批次大小 (Batch Size)</Text>
                <InputNumber
                  style={{ width: '100%', marginTop: 4 }}
                  min={8}
                  max={128}
                  defaultValue={32}
                  disabled={true}
                />
              </div>
              <div style={{ flex: 1 }}>
                <Text type="secondary">学习率 (Learning Rate)</Text>
                <InputNumber
                  style={{ width: '100%', marginTop: 4 }}
                  min={0.0001}
                  max={0.01}
                  step={0.001}
                  defaultValue={0.002}
                  disabled={true}
                />
              </div>
            </Space>
          </div>

          <Divider />

          <Button
            type="primary"
            size="large"
            icon={<PlayCircleOutlined />}
            onClick={handleTrain}
            loading={training}
            disabled={!selectedCourse || training}
            block
          >
            {training ? '训练中...' : '开始训练'}
          </Button>

          {device && (
            <Alert
              message={device === 'cuda' ? '✅ 使用GPU加速训练' : '⚠️ 使用CPU训练（速度较慢）'}
              type={device === 'cuda' ? 'success' : 'warning'}
              showIcon
            />
          )}

          {training && (
            <Card>
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <div>
                  <Progress 
                    percent={progress} 
                    status="active"
                    strokeColor={{
                      '0%': '#108ee9',
                      '100%': '#87d068',
                    }}
                  />
                  <Text type="secondary" style={{ marginTop: 8, display: 'block', textAlign: 'center' }}>
                    {statusMessage}
                  </Text>
                </div>

                {currentEpoch > 0 && (
                  <div>
                    <Text strong>当前进度：</Text>
                    <Text> 第 {currentEpoch} / {totalEpochs} 轮</Text>
                  </div>
                )}

                {epochMetrics && (
                  <Row gutter={16}>
                    <Col span={6}>
                      <Statistic
                        title="损失值 (Loss)"
                        value={epochMetrics.loss}
                        precision={4}
                        valueStyle={{ color: '#cf1322' }}
                      />
                    </Col>
                    <Col span={6}>
                      <Statistic
                        title="AUC"
                        value={epochMetrics.auc}
                        precision={4}
                        valueStyle={{ color: '#3f8600' }}
                      />
                    </Col>
                    <Col span={6}>
                      <Statistic
                        title="准确率"
                        value={epochMetrics.accuracy}
                        precision={2}
                        suffix="%"
                        valueStyle={{ color: '#1890ff' }}
                      />
                    </Col>
                    <Col span={6}>
                      <Statistic
                        title="F1分数"
                        value={epochMetrics.f1}
                        precision={4}
                        valueStyle={{ color: '#722ed1' }}
                      />
                    </Col>
                  </Row>
                )}

                {epochMetrics && epochMetrics.best_epoch === epochMetrics.epoch && (
                  <Alert
                    message={`🎉 当前为最佳模型 (Epoch ${epochMetrics.best_epoch}, AUC: ${epochMetrics.best_auc.toFixed(4)})`}
                    type="success"
                    showIcon
                  />
                )}
              </Space>
            </Card>
          )}

          {trainingResult && (
            <Card>
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <Alert
                  message="训练完成"
                  description={
                    <div>
                      <p>✅ 最佳轮次: Epoch {trainingResult.best_epoch}</p>
                      <p>✅ 最佳AUC: {trainingResult.best_auc?.toFixed(4) || 'N/A'}</p>
                      {trainingResult.best_acc !== undefined && (
                        <p>✅ 最佳准确率: {(trainingResult.best_acc * 100).toFixed(2)}%</p>
                      )}
                      {trainingResult.best_rmse !== undefined && (
                        <p>✅ 最佳RMSE: {trainingResult.best_rmse.toFixed(4)}</p>
                      )}
                      <p>✅ 模型已保存</p>
                    </div>
                  }
                  type="success"
                  showIcon
                  icon={<CheckCircleOutlined />}
                />
              </Space>
            </Card>
          )}

          <Card size="small" title="训练说明">
            <Paragraph>
              <ul>
                <li>训练需要至少10条答题记录</li>
                <li>建议数据量大于100条以获得更好的效果</li>
                <li>训练时间取决于数据量和设备性能（GPU会快很多）</li>
                <li>训练过程中可以实时查看进度和指标</li>
                <li>训练完成后模型会自动保存，可用于认知诊断</li>
              </ul>
            </Paragraph>
          </Card>
        </Space>
      </Card>
    </Space>
  )
}

export default ModelTraining

