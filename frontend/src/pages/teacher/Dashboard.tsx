import { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, Space, Typography, Select } from 'antd'
import { UserOutlined, CheckCircleOutlined, ClockCircleOutlined, TrophyOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { teacherApi, courseApi } from '@/services/api'

const { Title } = Typography

const TeacherDashboard = () => {
  const [courses, setCourses] = useState<any[]>([])
  const [selectedCourse, setSelectedCourse] = useState<number>(1)
  const [studentsData, setStudentsData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchCourses()
  }, [])

  useEffect(() => {
    if (selectedCourse) {
      fetchStudentsOverview()
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

  const fetchStudentsOverview = async () => {
    try {
      setLoading(true)
      const data = await teacherApi.getStudentsOverview(selectedCourse)
      setStudentsData(data)
    } catch (error) {
      console.error('Failed to fetch students overview:', error)
    } finally {
      setLoading(false)
    }
  }

  const totalStudents = studentsData.length
  const totalQuestions = studentsData.reduce((sum, s) => sum + s.total_questions, 0)
  const avgAccuracy = studentsData.length > 0
    ? Math.round(studentsData.reduce((sum, s) => sum + s.accuracy, 0) / studentsData.length)
    : 0

  const getAccuracyDistributionOption = () => {
    const ranges = [
      { name: '0-60%', min: 0, max: 60, count: 0 },
      { name: '60-70%', min: 60, max: 70, count: 0 },
      { name: '70-80%', min: 70, max: 80, count: 0 },
      { name: '80-90%', min: 80, max: 90, count: 0 },
      { name: '90-100%', min: 90, max: 100, count: 0 },
    ]

    studentsData.forEach(student => {
      for (const range of ranges) {
        if (student.accuracy >= range.min && student.accuracy < range.max) {
          range.count++
          break
        }
        if (range.max === 100 && student.accuracy === 100) {
          range.count++
          break
        }
      }
    })

    return {
      title: {
        text: '学生正确率分布',
        left: 'center',
      },
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c}人 ({d}%)',
      },
      legend: {
        orient: 'vertical',
        left: 'left',
        top: 'middle',
      },
      series: [
        {
          type: 'pie',
          radius: '60%',
          data: ranges.map(range => ({
            name: range.name,
            value: range.count,
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

  const getStudentRankingOption = () => {
    const sortedStudents = [...studentsData]
      .sort((a, b) => b.accuracy - a.accuracy)
      .slice(0, 10)

    return {
      title: {
        text: '学生成绩排名（Top 10）',
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
      },
      yAxis: {
        type: 'category',
        data: sortedStudents.map(s => s.name),
      },
      series: [
        {
          type: 'bar',
          data: sortedStudents.map(s => ({
            value: s.accuracy,
            itemStyle: {
              color: s.accuracy >= 80 ? '#52c41a' : s.accuracy >= 60 ? '#1890ff' : '#ff4d4f',
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

  const getDepartmentStatOption = () => {
    const departmentMap = new Map()
    
    studentsData.forEach(student => {
      if (!departmentMap.has(student.department)) {
        departmentMap.set(student.department, {
          count: 0,
          totalAccuracy: 0,
        })
      }
      const dept = departmentMap.get(student.department)
      dept.count++
      dept.totalAccuracy += student.accuracy
    })

    const departments = Array.from(departmentMap.keys())
    const avgAccuracies = departments.map(dept => {
      const data = departmentMap.get(dept)
      return Math.round(data.totalAccuracy / data.count)
    })

    return {
      title: {
        text: '各专业平均正确率',
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
      },
      xAxis: {
        type: 'category',
        data: departments,
      },
      yAxis: {
        type: 'value',
        max: 100,
        axisLabel: {
          formatter: '{value}%',
        },
      },
      series: [
        {
          type: 'bar',
          data: avgAccuracies,
          itemStyle: {
            color: '#1890ff',
          },
          label: {
            show: true,
            position: 'top',
            formatter: '{c}%',
          },
        },
      ],
    }
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>数据看板</Title>
        <Select
          style={{ width: 300 }}
          value={selectedCourse}
          onChange={setSelectedCourse}
          options={courses.map(c => ({ label: c.name, value: c.id }))}
        />
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="学生总数"
              value={totalStudents}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总答题数"
              value={totalQuestions}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="平均正确率"
              value={avgAccuracy}
              suffix="%"
              prefix={<TrophyOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="平均答题数"
              value={Math.round(totalQuestions / (totalStudents || 1))}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card loading={loading}>
            <ReactECharts option={getAccuracyDistributionOption()} style={{ height: '350px' }} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card loading={loading}>
            <ReactECharts option={getDepartmentStatOption()} style={{ height: '350px' }} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24}>
          <Card loading={loading}>
            <ReactECharts option={getStudentRankingOption()} style={{ height: '500px' }} />
          </Card>
        </Col>
      </Row>
    </Space>
  )
}

export default TeacherDashboard

