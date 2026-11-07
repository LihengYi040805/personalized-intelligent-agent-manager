from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Course(db.Model):
    """课程模型"""
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    total_hours = db.Column(db.Integer)
    cover_image = db.Column(db.String(500))  # 课程封面图片URL
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    knowledges = db.relationship('Knowledge', backref='course', lazy=True)
    questions = db.relationship('Question', backref='course', lazy=True)


class Knowledge(db.Model):
    """知识点模型"""
    __tablename__ = 'knowledges'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    level = db.Column(db.Integer, default=1)  # 知识点层级
    prerequisites = db.Column(db.Text, default='[]')  # JSON格式的前置知识点ID列表
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    questions = db.relationship('Question', backref='knowledge', lazy=True)


class Question(db.Model):
    """题目模型"""
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    knowledge_id = db.Column(db.Integer, db.ForeignKey('knowledges.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text)  # JSON格式的选项列表
    answer = db.Column(db.String(200), nullable=False)
    difficulty = db.Column(db.Integer, default=1)  # 1-简单 2-中等 3-困难
    question_type = db.Column(db.String(50), default='single')  # single-单选 multiple-多选 judge-判断
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    records = db.relationship('QuestionRecord', backref='question', lazy=True)


class Student(db.Model):
    """学生（员工）模型"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)
    department = db.Column(db.String(100))
    position = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    question_records = db.relationship('QuestionRecord', backref='student', lazy=True)
    diagnosis_reports = db.relationship('DiagnosisReport', backref='student', lazy=True)


class QuestionRecord(db.Model):
    """答题记录模型"""
    __tablename__ = 'question_records'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    answer = db.Column(db.String(200))
    is_correct = db.Column(db.Boolean, default=False)
    time_spent = db.Column(db.Integer, default=0)  # 答题用时（秒）
    created_at = db.Column(db.DateTime, default=datetime.now)


class DiagnosisReport(db.Model):
    """认知诊断报告模型"""
    __tablename__ = 'diagnosis_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    diagnosis_result = db.Column(db.Text)  # JSON格式的诊断结果
    created_at = db.Column(db.DateTime, default=datetime.now)


class User(db.Model):
    """用户模型（用于登录认证）"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # 存储加密后的密码
    role = db.Column(db.String(20), default='student')  # student/teacher
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)  # 关联学生表
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    student = db.relationship('Student', backref='user', lazy=True)

