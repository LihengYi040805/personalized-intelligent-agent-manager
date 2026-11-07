import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from 'antd'
import StudentLayout from './layouts/StudentLayout'
import TeacherLayout from './layouts/TeacherLayout'
import Landing from './pages/Landing'
import RoleSelection from './pages/RoleSelection'

const { Content } = Layout

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/role" element={<RoleSelection />} />
        <Route path="/student/*" element={<StudentLayout />} />
        <Route path="/teacher/*" element={<TeacherLayout />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App

