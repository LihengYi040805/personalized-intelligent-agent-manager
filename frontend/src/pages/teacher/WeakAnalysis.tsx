import { useEffect, useState } from 'react'
import { Card, Space, Typography, Select, Table, Tag } from 'antd'
import ReactECharts from 'echarts-for-react'
import { teacherApi, courseApi } from '@/services/api'

const { Title } = Typography

const WeakAnalysis = () => {
  const [courses, setCourses] = useState<any[]>([])
  const [selectedCourse, setSelectedCourse] = useState<number>(1)
  const [weakData, setWeakData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)

  useEffect(() => {
    fetchCourses()
  }, [])

  useEffect(() => {
    if (selectedCourse) {
      fetchWeakAnalysis()
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

  const fetchWeakAnalysis = async () => {
    try {
      setLoading(true)
      const data = await teacherApi.getWeakKnowledges(selectedCourse)
      setWeakData(data)
    } catch (error) {
      console.error('Failed to fetch weak analysis:', error)
    } finally {
      setLoading(false)
    }
  }

  const columns = [
    {
      title: '排名',
      key: 'rank',
      width: 80,
      render: (_: any, __: any, index: number) => {
        // 计算全局排名：当前页索引 + (当前页码 - 1) * 每页大小
        const globalRank = index + 1 + (currentPage - 1) * pageSize
        return (
          <Tag color={globalRank <= 3 ? 'red' : 'default'}>{globalRank}</Tag>
        )
      },
    },
    {
      title: '知识点',
      dataIndex: 'knowledge_name',
      key: 'knowledge_name',
    },
    {
      title: '正确率',
      dataIndex: 'accuracy',
      key: 'accuracy',
      sorter: (a: any, b: any) => a.accuracy - b.accuracy,
      render: (accuracy: number) => (
        <Tag color={accuracy >= 80 ? 'success' : accuracy >= 60 ? 'warning' : 'error'}>
          {accuracy}%
        </Tag>
      ),
    },
    {
      title: '答题总数',
      dataIndex: 'total_attempts',
      key: 'total_attempts',
      sorter: (a: any, b: any) => a.total_attempts - b.total_attempts,
    },
    {
      title: '参与学生数',
      dataIndex: 'student_count',
      key: 'student_count',
      sorter: (a: any, b: any) => a.student_count - b.student_count,
    },
    {
      title: '状态',
      key: 'status',
      render: (_: any, record: any) => {
        if (record.accuracy < 60) {
          return <Tag color="error">需重点关注</Tag>
        } else if (record.accuracy < 70) {
          return <Tag color="warning">需加强</Tag>
        } else {
          return <Tag color="success">良好</Tag>
        }
      },
    },
  ]

  const getAccuracyChartOption = () => {
    const sortedData = [...weakData].sort((a, b) => a.accuracy - b.accuracy).slice(0, 10)

    return {
      title: {
        text: '知识点正确率排名（由低到高）',
        left: 'center',
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
        axisLabel: {
          formatter: '{value}%',
        },
      },
      yAxis: {
        type: 'category',
        data: sortedData.map(d => d.knowledge_name),
      },
      series: [
        {
          type: 'bar',
          data: sortedData.map(d => ({
            value: d.accuracy,
            itemStyle: {
              color: d.accuracy < 60 ? '#ff4d4f' : d.accuracy < 70 ? '#faad14' : '#52c41a',
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

  const getAttemptsChartOption = () => {
    return {
      title: {
        text: '各知识点答题量分布',
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
      },
      xAxis: {
        type: 'category',
        data: weakData.map(d => d.knowledge_name),
        axisLabel: {
          rotate: 45,
          interval: 0,
        },
      },
      yAxis: {
        type: 'value',
        name: '答题数',
      },
      series: [
        {
          type: 'bar',
          data: weakData.map(d => d.total_attempts),
          itemStyle: {
            color: '#1890ff',
          },
          label: {
            show: true,
            position: 'top',
          },
        },
      ],
      grid: {
        bottom: 100,
      },
    }
  }

  const getCoverageChartOption = () => {
    return {
      title: {
        text: '知识点学生覆盖率',
        left: 'center',
      },
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c}人',
      },
      series: [
        {
          type: 'pie',
          radius: ['40%', '70%'],
          data: weakData.map(d => ({
            name: d.knowledge_name,
            value: d.student_count,
          })),
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)',
            },
          },
        },
      ],
    }
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>薄弱知识点分析</Title>
        <Select
          style={{ width: 300 }}
          value={selectedCourse}
          onChange={setSelectedCourse}
          options={courses.map(c => ({ label: c.name, value: c.id }))}
        />
      </div>

      <Card loading={loading}>
        <ReactECharts option={getAccuracyChartOption()} style={{ height: '500px' }} />
      </Card>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '16px' }}>
        <Card loading={loading}>
          <ReactECharts option={getAttemptsChartOption()} style={{ height: '350px' }} />
        </Card>
        <Card loading={loading}>
          <ReactECharts option={getCoverageChartOption()} style={{ height: '350px' }} />
        </Card>
      </div>

      <Card title="知识点详细分析" loading={loading}>
        <Table
          columns={columns}
          dataSource={weakData}
          rowKey="knowledge_id"
          pagination={{
            pageSize: pageSize,
            showTotal: (total) => `共 ${total} 个知识点`,
            current: currentPage,
            onChange: (page, size) => {
              setCurrentPage(page)
              setPageSize(size || 10)
            },
            onShowSizeChange: (current, size) => {
              setCurrentPage(1) // 切换每页大小时重置到第一页
              setPageSize(size)
            },
          }}
        />
      </Card>
    </Space>
  )
}

export default WeakAnalysis

