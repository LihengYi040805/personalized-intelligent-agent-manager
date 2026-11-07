import { useEffect, useState } from 'react'
import { Card, Select, Space, Typography, Spin, Empty } from 'antd'
import ReactECharts from 'echarts-for-react'
import { courseApi } from '@/services/api'

const { Title } = Typography

const KnowledgeGraph = () => {
  const [courses, setCourses] = useState<any[]>([])
  const [selectedCourse, setSelectedCourse] = useState<number>(1)
  const [graphData, setGraphData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchCourses()
  }, [])

  useEffect(() => {
    if (selectedCourse) {
      fetchGraphData(selectedCourse)
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

  const fetchGraphData = async (courseId: number) => {
    try {
      setLoading(true)
      const data = await courseApi.getKnowledgeGraph(courseId)
      setGraphData(data)
    } catch (error) {
      console.error('Failed to fetch graph data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getChartOption = () => {
    if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
      return {}
    }

    // 根据level设置节点颜色和大小
    const colorMap: { [key: number]: string } = {
      1: '#1890ff',
      2: '#52c41a',
      3: '#faad14',
      4: '#f5222d',
    }

    return {
      title: {
        text: '知识点关系图谱',
        left: 'center',
        textStyle: {
          fontSize: 18,
          fontWeight: 'bold',
          color: '#333'
        }
      },
      tooltip: {
        formatter: (params: any) => {
          if (params.dataType === 'node') {
            return `
              <div style="padding: 8px;">
                <strong style="font-size: 14px;">${params.data.name}</strong><br/>
                <span style="color: #666; font-size: 12px;">层级: 第${params.data.level}级</span><br/>
                <span style="color: #888; font-size: 12px;">${params.data.description}</span>
              </div>
            `
          }
          return ''
        },
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#ddd',
        borderWidth: 1,
        textStyle: {
          color: '#333'
        }
      },
      animationDuration: 1000,
      animationEasingUpdate: 'quinticInOut',
      series: [
        {
          type: 'graph',
          layout: 'force',
          data: graphData.nodes.map((node: any) => ({
            id: node.id,
            name: node.name,
            level: node.level,
            description: node.description,
            symbolSize: 60 + (4 - node.level) * 8, // 基础知识更大
            itemStyle: {
              color: colorMap[node.level] || '#1890ff',
              borderColor: '#fff',
              borderWidth: 2,
              shadowBlur: 10,
              shadowColor: 'rgba(0, 0, 0, 0.2)'
            },
            label: {
              show: true,
              formatter: '{b}',
              fontSize: 11,
              fontWeight: 'bold',
              color: '#fff',
              textBorderColor: 'transparent'
            },
          })),
          links: graphData.edges.map((edge: any) => ({
            source: edge.source,
            target: edge.target,
            lineStyle: {
              color: '#aaa',
              width: 2,
              curveness: 0.3,
              opacity: 0.6
            },
            symbol: ['none', 'arrow'],
            symbolSize: 8
          })),
          roam: true,
          draggable: true,
          force: {
            repulsion: 2000,
            edgeLength: [100, 200],
            gravity: 0.1,
            friction: 0.3
          },
          emphasis: {
            focus: 'adjacency',
            lineStyle: {
              width: 4,
              opacity: 1
            },
            itemStyle: {
              shadowBlur: 20,
              shadowColor: 'rgba(0, 0, 0, 0.4)'
            }
          },
          lineStyle: {
            color: 'source',
            curveness: 0.3
          }
        },
      ],
    }
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>知识图谱</Title>
        <Select
          style={{ width: 300 }}
          value={selectedCourse}
          onChange={setSelectedCourse}
          options={courses.map(c => ({ label: c.name, value: c.id }))}
        />
      </div>

      <Card>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '100px 0' }}>
            <Spin size="large" />
          </div>
        ) : graphData && graphData.nodes && graphData.nodes.length > 0 ? (
          <ReactECharts
            option={getChartOption()}
            style={{ height: '700px', width: '100%' }}
            notMerge={true}
            lazyUpdate={true}
          />
        ) : (
          <Empty description="暂无知识图谱数据" style={{ padding: '100px 0' }} />
        )}
      </Card>

      <Card title="图例说明" style={{ marginTop: 16 }}>
        <Space size="large" wrap>
          <Space>
            <div style={{ width: 20, height: 20, background: '#1890ff', borderRadius: '50%', border: '2px solid #fff', boxShadow: '0 2px 4px rgba(0,0,0,0.2)' }} />
            <span style={{ fontSize: 14 }}>层级1 - 基础知识</span>
          </Space>
          <Space>
            <div style={{ width: 20, height: 20, background: '#52c41a', borderRadius: '50%', border: '2px solid #fff', boxShadow: '0 2px 4px rgba(0,0,0,0.2)' }} />
            <span style={{ fontSize: 14 }}>层级2 - 进阶知识</span>
          </Space>
          <Space>
            <div style={{ width: 20, height: 20, background: '#faad14', borderRadius: '50%', border: '2px solid #fff', boxShadow: '0 2px 4px rgba(0,0,0,0.2)' }} />
            <span style={{ fontSize: 14 }}>层级3 - 高级知识</span>
          </Space>
          <Space>
            <div style={{ width: 20, height: 20, background: '#f5222d', borderRadius: '50%', border: '2px solid #fff', boxShadow: '0 2px 4px rgba(0,0,0,0.2)' }} />
            <span style={{ fontSize: 14 }}>层级4 - 专家知识</span>
          </Space>
        </Space>
        <div style={{ marginTop: 12, color: '#666', fontSize: 13 }}>
          💡 提示：可以拖拽节点调整位置，滚轮缩放，点击节点查看详情
        </div>
      </Card>
    </Space>
  )
}

export default KnowledgeGraph

