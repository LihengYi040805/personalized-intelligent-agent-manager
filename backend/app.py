from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import json
import os
import random
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import torch  # 导入PyTorch用于NCDM模型训练
from dotenv import load_dotenv
from models import db, Course, Knowledge, Question, Student, QuestionRecord, DiagnosisReport, User
from services.diagnosis_service import DiagnosisService
from services.ncdm_service import NCDMService
from services.ai_generation_service import AIGenerationService
from services.ai_generation_service_v2 import AIGenerationServiceV2

# 加载环境变量
load_dotenv()

app = Flask(__name__)

# 数据库配置：优先使用MySQL，如果没配置则使用SQLite
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME', 'aied_platform')
DB_PORT = os.getenv('DB_PORT', '3306')

if DB_HOST and DB_USER and DB_PASSWORD:
    # 使用MySQL
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
    }
    print(f"📦 使用 MySQL 数据库: {DB_HOST}:{DB_PORT}/{DB_NAME}")
else:
    # 使用SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///training.db'
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'connect_args': {
            'check_same_thread': False,
            'timeout': 20
        },
        'pool_pre_ping': True,
        'pool_recycle': 3600,
    }
    print("📦 使用 SQLite 数据库: training.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'md', 'markdown'}

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 配置 CORS，允许所有来源（包括内网穿透域名）
CORS(app, resources={r"/api/*": {"origins": "*"}})

db.init_app(app)

def init_sample_data():
    """初始化示例数据"""
    # 检查是否已有数据
    if Course.query.first() is not None:
        return
    
    # 创建课程1：C语言程序设计
    course1 = Course(
        name='C语言程序设计',
        description='计算机专业基础课程，涵盖C语言语法、数据类型、控制结构、函数、指针、数组、结构体等核心知识',
        total_hours=64,
        cover_image='https://images.unsplash.com/photo-1542831371-29b0f74f9713?w=800&h=400&fit=crop'
    )
    db.session.add(course1)
    db.session.flush()
    
    # 创建课程2：数据库原理
    course2 = Course(
        name='数据库原理与应用',
        description='数据库系统基础课程，包含关系模型、SQL语言、数据库设计、事务处理、索引优化等内容',
        total_hours=48,
        cover_image='https://images.unsplash.com/photo-1544383835-bda2bc66a55d?w=800&h=400&fit=crop'
    )
    db.session.add(course2)
    db.session.flush()
    
    # 创建C语言知识点
    c_knowledges = [
        Knowledge(
            course_id=course1.id,
            name='C语言基础语法',
            description='变量定义、数据类型、运算符、输入输出函数等基础语法',
            level=1,
            prerequisites='[]'
        ),
        Knowledge(
            course_id=course1.id,
            name='控制结构',
            description='条件语句(if-else)、循环语句(for/while/do-while)、分支语句(switch)',
            level=2,
            prerequisites='[1]'
        ),
        Knowledge(
            course_id=course1.id,
            name='函数',
            description='函数定义与调用、参数传递、递归函数、作用域',
            level=2,
            prerequisites='[1]'
        ),
        Knowledge(
            course_id=course1.id,
            name='数组与字符串',
            description='一维数组、二维数组、字符数组、字符串处理函数',
            level=2,
            prerequisites='[1,2]'
        ),
        Knowledge(
            course_id=course1.id,
            name='指针',
            description='指针概念、指针运算、指针与数组、指针与函数',
            level=3,
            prerequisites='[1,2,3,4]'
        ),
    ]
    
    for k in c_knowledges:
        db.session.add(k)
    db.session.flush()
    
    # 创建数据库知识点
    db_knowledges = [
        Knowledge(
            course_id=course2.id,
            name='数据库基础概念',
            description='数据库系统概述、数据模型、关系模型基础',
            level=1,
            prerequisites='[]'
        ),
        Knowledge(
            course_id=course2.id,
            name='SQL基础查询',
            description='SELECT语句、WHERE条件、ORDER BY排序、聚合函数',
            level=2,
            prerequisites='[6]'
        ),
        Knowledge(
            course_id=course2.id,
            name='多表查询与连接',
            description='内连接、外连接、子查询、集合运算',
            level=2,
            prerequisites='[6,7]'
        ),
        Knowledge(
            course_id=course2.id,
            name='数据库设计',
            description='ER模型、范式理论、数据库规范化设计',
            level=3,
            prerequisites='[6,7]'
        ),
        Knowledge(
            course_id=course2.id,
            name='事务与并发控制',
            description='事务ACID特性、并发问题、锁机制、隔离级别',
            level=3,
            prerequisites='[6,7,8]'
        ),
    ]
    
    for k in db_knowledges:
        db.session.add(k)
    db.session.flush()
    
    # 创建C语言题目
    c_questions = [
        # C语言基础语法
        Question(
            course_id=course1.id,
            knowledge_id=1,
            content='在C语言中，以下哪个是合法的变量名？',
            options=json.dumps(['2name', '_count', 'int', 'my-var']),
            answer='B',
            difficulty=1,
            question_type='single'
        ),
        Question(
            course_id=course1.id,
            knowledge_id=1,
            content='C语言中int类型在32位系统上通常占用多少字节？',
            options=json.dumps(['1字节', '2字节', '4字节', '8字节']),
            answer='C',
            difficulty=1,
            question_type='single'
        ),
        Question(
            course_id=course1.id,
            knowledge_id=1,
            content='以下哪些是C语言的基本数据类型？（多选）',
            options=json.dumps(['int', 'float', 'string', 'char', 'boolean']),
            answer='ABD',
            difficulty=2,
            question_type='multiple'
        ),
        
        # 控制结构
        Question(
            course_id=course1.id,
            knowledge_id=2,
            content='以下代码的输出结果是什么？\nint i = 0;\nwhile(i < 3) { printf("%d ", i); i++; }',
            options=json.dumps(['0 1 2', '1 2 3', '0 1 2 3', '1 2']),
            answer='A',
            difficulty=2,
            question_type='single'
        ),
        Question(
            course_id=course1.id,
            knowledge_id=2,
            content='switch语句中，如果没有break，会发生什么？',
            options=json.dumps(['编译错误', '运行时错误', '继续执行下一个case（穿透）', '直接跳出switch']),
            answer='C',
            difficulty=2,
            question_type='single'
        ),
        Question(
            course_id=course1.id,
            knowledge_id=2,
            content='以下哪些是C语言的循环结构？（多选）',
            options=json.dumps(['for', 'while', 'do-while', 'foreach', 'repeat-until']),
            answer='ABC',
            difficulty=1,
            question_type='multiple'
        ),
        
        # 函数
        Question(
            course_id=course1.id,
            knowledge_id=3,
            content='C语言中函数参数的默认传递方式是？',
            options=json.dumps(['值传递', '引用传递', '指针传递', '地址传递']),
            answer='A',
            difficulty=2,
            question_type='single'
        ),
        Question(
            course_id=course1.id,
            knowledge_id=3,
            content='递归函数必须具备的条件包括哪些？（多选）',
            options=json.dumps(['有递归调用', '有终止条件', '必须返回值', '参数必须递减', '必须是void类型']),
            answer='AB',
            difficulty=3,
            question_type='multiple'
        ),
        
        # 数组与字符串
        Question(
            course_id=course1.id,
            knowledge_id=4,
            content='定义数组int arr[5]，则arr[5]的访问会导致什么问题？',
            options=json.dumps(['正常访问', '数组越界', '编译错误', '返回0']),
            answer='B',
            difficulty=2,
            question_type='single'
        ),
        Question(
            course_id=course1.id,
            knowledge_id=4,
            content='C语言中字符串以什么字符结尾？',
            options=json.dumps(['\\n', '\\0', '\\t', 'EOF']),
            answer='B',
            difficulty=1,
            question_type='single'
        ),
        
        # 指针
        Question(
            course_id=course1.id,
            knowledge_id=5,
            content='int *p; 中，*p表示什么？',
            options=json.dumps(['指针变量p的地址', '指针p指向的值', '指针p本身', '一个整数']),
            answer='B',
            difficulty=2,
            question_type='single'
        ),
        Question(
            course_id=course1.id,
            knowledge_id=5,
            content='以下关于指针的说法正确的是？（多选）',
            options=json.dumps(['指针存储的是内存地址', '指针可以进行算术运算', '所有指针占用相同大小的内存', '空指针可以被解引用', '指针可以指向函数']),
            answer='ABE',
            difficulty=3,
            question_type='multiple'
        ),
    ]
    
    for q in c_questions:
        db.session.add(q)
    
    # 创建数据库题目
    db_questions = [
        # 数据库基础概念
        Question(
            course_id=course2.id,
            knowledge_id=6,
            content='关系数据库中，一个关系对应一个？',
            options=json.dumps(['数据库', '表', '记录', '字段']),
            answer='B',
            difficulty=1,
            question_type='single'
        ),
        Question(
            course_id=course2.id,
            knowledge_id=6,
            content='以下哪些是关系数据库的特点？（多选）',
            options=json.dumps(['数据以表格形式存储', '支持SQL查询', '数据之间无关联', '支持事务处理', '必须有主键']),
            answer='ABD',
            difficulty=2,
            question_type='multiple'
        ),
        
        # SQL基础查询
        Question(
            course_id=course2.id,
            knowledge_id=7,
            content='SQL中用于去除重复记录的关键字是？',
            options=json.dumps(['UNIQUE', 'DISTINCT', 'DIFFERENT', 'SINGLE']),
            answer='B',
            difficulty=1,
            question_type='single'
        ),
        Question(
            course_id=course2.id,
            knowledge_id=7,
            content='以下哪个SQL语句用于统计记录数？',
            options=json.dumps(['SUM()', 'COUNT()', 'TOTAL()', 'NUM()']),
            answer='B',
            difficulty=1,
            question_type='single'
        ),
        Question(
            course_id=course2.id,
            knowledge_id=7,
            content='WHERE子句中可以使用的运算符包括？（多选）',
            options=json.dumps(['=', 'LIKE', 'BETWEEN', 'IN', 'HAVING']),
            answer='ABCD',
            difficulty=2,
            question_type='multiple'
        ),
        
        # 多表查询与连接
        Question(
            course_id=course2.id,
            knowledge_id=8,
            content='LEFT JOIN会返回？',
            options=json.dumps(['只返回匹配的记录', '左表全部记录和右表匹配的记录', '右表全部记录和左表匹配的记录', '两表的笛卡尔积']),
            answer='B',
            difficulty=2,
            question_type='single'
        ),
        Question(
            course_id=course2.id,
            knowledge_id=8,
            content='子查询可以出现在SQL语句的哪些位置？（多选）',
            options=json.dumps(['SELECT子句', 'FROM子句', 'WHERE子句', 'ORDER BY子句', 'GROUP BY子句']),
            answer='ABC',
            difficulty=3,
            question_type='multiple'
        ),
        
        # 数据库设计
        Question(
            course_id=course2.id,
            knowledge_id=9,
            content='第三范式(3NF)要求消除？',
            options=json.dumps(['部分函数依赖', '传递函数依赖', '多值依赖', '连接依赖']),
            answer='B',
            difficulty=3,
            question_type='single'
        ),
        Question(
            course_id=course2.id,
            knowledge_id=9,
            content='ER图中，矩形表示？',
            options=json.dumps(['实体', '属性', '关系', '主键']),
            answer='A',
            difficulty=2,
            question_type='single'
        ),
        
        # 事务与并发控制
        Question(
            course_id=course2.id,
            knowledge_id=10,
            content='事务的ACID特性不包括？',
            options=json.dumps(['原子性', '一致性', '独立性', '持久性']),
            answer='C',
            difficulty=2,
            question_type='single'
        ),
        Question(
            course_id=course2.id,
            knowledge_id=10,
            content='以下哪些是数据库并发可能导致的问题？（多选）',
            options=json.dumps(['脏读', '不可重复读', '幻读', '死锁', '数据丢失']),
            answer='ABCDE',
            difficulty=3,
            question_type='multiple'
        ),
    ]
    
    for q in db_questions:
        db.session.add(q)
    
    # 创建示例学生
    students = [
        Student(name='张明', employee_id='2021001', department='计算机科学与技术', position='大三学生'),
        Student(name='李华', employee_id='2021002', department='软件工程', position='大三学生'),
        Student(name='王芳', employee_id='2021003', department='计算机科学与技术', position='大三学生'),
        Student(name='刘洋', employee_id='2021004', department='信息安全', position='大三学生'),
        Student(name='陈晨', employee_id='2021005', department='软件工程', position='大三学生'),
        Student(name='赵雪', employee_id='2022001', department='计算机科学与技术', position='大二学生'),
        Student(name='孙磊', employee_id='2022002', department='数据科学', position='大二学生'),
        Student(name='周婷', employee_id='2022003', department='软件工程', position='大二学生'),
        Student(name='吴凯', employee_id='2022004', department='人工智能', position='大二学生'),
        Student(name='郑欣', employee_id='2022005', department='计算机科学与技术', position='大二学生'),
    ]
    
    for s in students:
        db.session.add(s)
    
    db.session.commit()
    
    # 为所有学生创建默认登录账号，密码统一为123456
    default_password = generate_password_hash('123456')
    
    for student in students:
        # 检查是否已有账号
        existing_user = User.query.filter_by(student_id=student.id).first()
        if not existing_user:
            user = User(
                username=student.employee_id,  # 使用学号作为用户名
                email=f'{student.employee_id}@student.edu.cn',  # 生成默认邮箱
                password=default_password,
                role='student',
                student_id=student.id
            )
            db.session.add(user)
    
    # 创建一个默认教师账号
    teacher_user = User.query.filter_by(username='teacher').first()
    if not teacher_user:
        teacher_user = User(
            username='teacher',
            email='teacher@edu.cn',
            password=default_password,
            role='teacher'
        )
        db.session.add(teacher_user)
    
    db.session.commit()
    print("示例数据初始化完成！")
    print("默认学生账号：学号作为用户名，密码：123456")
    print("默认教师账号：teacher，密码：123456")


# 初始化数据库和示例数据
with app.app_context():
    db.create_all()
    init_sample_data()


# ==================== 用户认证相关API ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'student')
    
    # 验证必填字段
    if not username or not email or not password:
        return jsonify({'error': '用户名、邮箱和密码不能为空'}), 400
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({'error': '用户名已存在'}), 400
    
    # 检查邮箱是否已存在
    if User.query.filter_by(email=email).first():
        return jsonify({'error': '邮箱已被注册'}), 400
    
    # 创建新用户
    hashed_password = generate_password_hash(password)
    user = User(
        username=username,
        email=email,
        password=hashed_password,
        role=role
    )
    
    # 如果是学生角色，自动创建对应的学生记录
    if role == 'student':
        student = Student(
            name=username,
            employee_id=f'STU{User.query.count() + 1:05d}',
            department='未分配',
            position='学生'
        )
        db.session.add(student)
        db.session.flush()
        user.student_id = student.id
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '注册成功',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'student_id': user.student_id
        }
    })


@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    # 查找用户
    user = User.query.filter_by(username=username).first()
    
    if not user or not check_password_hash(user.password, password):
        return jsonify({'error': '用户名或密码错误'}), 401
    
    return jsonify({
        'success': True,
        'message': '登录成功',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'student_id': user.student_id
        }
    })


@app.route('/api/auth/check', methods=['GET'])
def check_auth():
    """检查用户登录状态（简化版，实际应使用JWT或Session）"""
    user_id = request.args.get('user_id', type=int)
    
    if not user_id:
        return jsonify({'error': '未登录'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'student_id': user.student_id
        }
    })


# ==================== 课程相关API ====================

@app.route('/api/courses', methods=['GET'])
def get_courses():
    """获取所有课程"""
    courses = Course.query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'description': c.description,
        'total_hours': c.total_hours,
        'cover_image': c.cover_image
    } for c in courses])


@app.route('/api/courses/<int:course_id>', methods=['GET'])
def get_course_detail(course_id):
    """获取课程详情"""
    course = Course.query.get_or_404(course_id)
    knowledges = Knowledge.query.filter_by(course_id=course_id).all()
    
    return jsonify({
        'id': course.id,
        'name': course.name,
        'description': course.description,
        'total_hours': course.total_hours,
        'knowledge_count': len(knowledges),
        'question_count': Question.query.filter_by(course_id=course_id).count()
    })


# ==================== 知识点相关API ====================

@app.route('/api/courses/<int:course_id>/knowledges', methods=['GET'])
def get_knowledges(course_id):
    """获取课程的知识点列表"""
    knowledges = Knowledge.query.filter_by(course_id=course_id).all()
    result = []
    for k in knowledges:
        try:
            prerequisites = json.loads(k.prerequisites) if k.prerequisites else []
            if not isinstance(prerequisites, list):
                prerequisites = []
        except (json.JSONDecodeError, TypeError):
            prerequisites = []
        
        result.append({
            'id': k.id,
            'name': k.name,
            'description': k.description or '',
            'level': k.level,
            'prerequisites': prerequisites
        })
    return jsonify(result)


@app.route('/api/courses/<int:course_id>/knowledge-graph', methods=['GET'])
def get_knowledge_graph(course_id):
    """获取知识图谱数据（用于可视化）"""
    knowledges = Knowledge.query.filter_by(course_id=course_id).all()
    
    # 构建知识点ID映射，用于验证prerequisites中的ID是否存在
    knowledge_id_set = {k.id for k in knowledges}
    
    # 构建节点
    nodes = [{
        'id': str(k.id),
        'name': k.name,
        'level': k.level,
        'description': k.description or ''
    } for k in knowledges]
    
    # 构建边（依赖关系）
    edges = []
    for k in knowledges:
        try:
            # 解析prerequisites JSON
            if k.prerequisites:
                prerequisites = json.loads(k.prerequisites)
                if isinstance(prerequisites, list):
                    for pre_id in prerequisites:
                        # 确保pre_id是整数，且在有效范围内
                        pre_id_int = int(pre_id) if isinstance(pre_id, (int, str)) else None
                        if pre_id_int and pre_id_int in knowledge_id_set:
                            edges.append({
                                'source': str(pre_id_int),
                                'target': str(k.id)
                            })
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            # 如果prerequisites格式错误，跳过该知识点的关系
            print(f"警告：知识点 {k.id} ({k.name}) 的prerequisites格式错误: {e}")
            continue
    
    return jsonify({
        'nodes': nodes,
        'edges': edges
    })


# ==================== 题目相关API ====================

@app.route('/api/questions', methods=['GET'])
def get_all_questions():
    """获取所有题目列表"""
    try:
        questions = Question.query.order_by(Question.id.desc()).all()
        return jsonify([{
            'id': q.id,
            'course_id': q.course_id,
            'knowledge_id': q.knowledge_id,
            'content': q.content,
            'options': json.loads(q.options),
            'answer': q.answer,
            'difficulty': q.difficulty,
            'question_type': q.question_type
        } for q in questions])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledges', methods=['GET'])
def get_all_knowledges():
    """获取所有知识点列表"""
    try:
        knowledges = Knowledge.query.order_by(Knowledge.id.desc()).all()
        return jsonify([{
            'id': k.id,
            'course_id': k.course_id,
            'name': k.name,
            'description': k.description,
            'level': k.level
        } for k in knowledges])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/courses/<int:course_id>/questions', methods=['GET'])
def get_questions(course_id):
    """获取课程的题目列表"""
    knowledge_id = request.args.get('knowledge_id', type=int)
    difficulty = request.args.get('difficulty', type=int)
    
    query = Question.query.filter_by(course_id=course_id)
    
    if knowledge_id:
        query = query.filter_by(knowledge_id=knowledge_id)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    
    questions = query.all()
    
    result = []
    for q in questions:
        knowledge = None
        if q.knowledge_id:
            knowledge = db.session.get(Knowledge, q.knowledge_id)
        
        result.append({
            'id': q.id,
            'content': q.content,
            'options': json.loads(q.options),
            'knowledge_id': q.knowledge_id,
            'knowledge_name': knowledge.name if knowledge else None,
            'difficulty': q.difficulty,
            'question_type': q.question_type
        })
    
    return jsonify(result)


@app.route('/api/questions/<int:question_id>', methods=['GET'])
def get_question_detail(question_id):
    """获取题目详情"""
    question = Question.query.get_or_404(question_id)
    knowledge = db.session.get(Knowledge, question.knowledge_id) if question.knowledge_id else None
    
    return jsonify({
        'id': question.id,
        'content': question.content,
        'options': json.loads(question.options),
        'difficulty': question.difficulty,
        'question_type': question.question_type,
        'knowledge': {
            'id': knowledge.id if knowledge else None,
            'name': knowledge.name if knowledge else '未知'
        } if knowledge else None
    })


@app.route('/api/questions/<int:question_id>/submit', methods=['POST'])
def submit_answer(question_id):
    """提交答案"""
    data = request.json
    student_id = data.get('student_id')
    answer = data.get('answer')
    time_spent = data.get('time_spent', 0)
    
    question = Question.query.get_or_404(question_id)
    is_correct = (answer == question.answer)
    
    # 记录答题记录
    record = QuestionRecord(
        student_id=student_id,
        question_id=question_id,
        answer=answer,
        is_correct=is_correct,
        time_spent=time_spent
    )
    db.session.add(record)
    db.session.commit()
    
    knowledge = db.session.get(Knowledge, question.knowledge_id) if question.knowledge_id else None
    return jsonify({
        'is_correct': is_correct,
        'correct_answer': question.answer,
        'explanation': f'本题考察知识点：{knowledge.name if knowledge else "未知"}'
    })


@app.route('/api/questions/<int:question_id>', methods=['PUT'])
def update_question(question_id):
    """更新题目"""
    question = Question.query.get_or_404(question_id)
    data = request.json
    
    try:
        # 更新字段
        if 'content' in data:
            question.content = data['content']
        if 'options' in data:
            question.options = json.dumps(data['options'], ensure_ascii=False)
        if 'answer' in data:
            question.answer = data['answer']
        if 'difficulty' in data:
            question.difficulty = data['difficulty']
        if 'question_type' in data:
            question.question_type = data['question_type']
        if 'knowledge_id' in data:
            question.knowledge_id = data['knowledge_id']
        
        db.session.commit()
        return jsonify({'success': True, 'message': '更新成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'更新失败: {str(e)}'}), 500


@app.route('/api/questions/<int:question_id>', methods=['DELETE'])
def delete_question(question_id):
    """删除题目"""
    question = Question.query.get_or_404(question_id)
    
    try:
        # 先删除相关的答题记录
        QuestionRecord.query.filter_by(question_id=question_id).delete()
        # 删除题目
        db.session.delete(question)
        db.session.commit()
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除失败: {str(e)}'}), 500


# ==================== 学生相关API ====================

@app.route('/api/students', methods=['GET'])
def get_students():
    """获取所有学生"""
    students = Student.query.all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'employee_id': s.employee_id,
        'department': s.department,
        'position': s.position
    } for s in students])


@app.route('/api/students/<int:student_id>', methods=['GET'])
def get_student_detail(student_id):
    """获取学生详情"""
    student = Student.query.get_or_404(student_id)
    total_questions = QuestionRecord.query.filter_by(student_id=student_id).count()
    correct_questions = QuestionRecord.query.filter_by(student_id=student_id, is_correct=True).count()
    
    return jsonify({
        'id': student.id,
        'name': student.name,
        'employee_id': student.employee_id,
        'department': student.department,
        'position': student.position,
        'total_questions': total_questions,
        'correct_questions': correct_questions,
        'accuracy': round(correct_questions / total_questions * 100, 1) if total_questions > 0 else 0
    })


# ==================== 认知诊断相关API ====================

@app.route('/api/students/<int:student_id>/diagnosis', methods=['POST'])
def generate_diagnosis(student_id):
    """生成学生的认知诊断报告"""
    data = request.json
    course_id = data.get('course_id')
    algorithm = data.get('algorithm', 'IRT')  # 默认使用IRT算法
    
    # 检查学生是否有答题记录
    records_count = QuestionRecord.query.filter_by(student_id=student_id).join(Question).filter(
        Question.course_id == course_id
    ).count()
    
    if records_count == 0:
        return jsonify({
            'error': '该学生还没有答题记录，请先完成一些练习题后再进行诊断'
        }), 400
    
    # 根据算法类型选择服务
    if algorithm == 'NCDM':
        diagnosis_service = NCDMService()
    else:  # 默认使用IRT
        diagnosis_service = DiagnosisService()
    
    try:
        report_data = diagnosis_service.diagnose_student(student_id, course_id)
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'诊断失败: {str(e)}'}), 500
    
    # 保存诊断报告
    report = DiagnosisReport(
        student_id=student_id,
        course_id=course_id,
        diagnosis_result=json.dumps(report_data, ensure_ascii=False)
    )
    db.session.add(report)
    db.session.commit()
    
    return jsonify(report_data)


@app.route('/api/ncdm/train/<int:course_id>', methods=['POST'])
def train_ncdm_model(course_id):
    """训练NCDM模型（同步版本，保持兼容）"""
    from services.ncdm_trainer import NCDMTrainer
    
    data = request.json or {}
    epochs = data.get('epochs', 20)
    batch_size = data.get('batch_size', 32)
    lr = data.get('lr', 0.002)
    
    try:
        # 检测GPU
        if torch.cuda.is_available():
            device = "cuda"
            gpu_name = torch.cuda.get_device_name(0)
            print(f"✅ 检测到GPU: {gpu_name}，使用设备: {device}")
        else:
            device = "cpu"
            print(f"⚠️ 未检测到GPU，使用设备: {device}")
            print(f"   提示：如需使用GPU，请安装CUDA版本的PyTorch")
        
        trainer = NCDMTrainer(course_id, device)
        best_epoch, best_auc, best_acc, best_rmse = trainer.train(epochs=epochs, batch_size=batch_size, lr=lr)
        
        return jsonify({
            'success': True,
            'message': '模型训练完成',
            'best_epoch': best_epoch,
            'best_auc': float(best_auc),
            'best_acc': float(best_acc),
            'best_rmse': float(best_rmse),
            'model_path': f'models/ncdm_course_{course_id}.pth'
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        import traceback
        print(f"训练失败: {traceback.format_exc()}")
        return jsonify({'error': f'训练失败: {str(e)}'}), 500


@app.route('/api/ncdm/check-model/<int:course_id>', methods=['GET'])
def check_ncdm_model(course_id):
    """检查NCDM模型是否存在"""
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_dir, "models", f"ncdm_course_{course_id}.pth")
    
    exists = os.path.exists(model_path)
    return jsonify({
        'exists': exists,
        'course_id': course_id,
        'model_path': model_path if exists else None
    })


@app.route('/api/ncdm/train-stream/<int:course_id>', methods=['POST'])
def train_ncdm_model_stream(course_id):
    """训练NCDM模型（流式版本，实时显示进度）"""
    from services.ncdm_trainer import NCDMTrainer
    
    data = request.json or {}
    epochs = data.get('epochs', 20)
    batch_size = data.get('batch_size', 32)
    lr = data.get('lr', 0.002)
    
    def generate():
        """生成器函数，用于SSE流式输出"""
        try:
            # 检测GPU
            if torch.cuda.is_available():
                device = "cuda"
                gpu_name = torch.cuda.get_device_name(0)
                yield f"data: {json.dumps({'type': 'info', 'message': f'✅ 检测到GPU: {gpu_name}，使用设备: {device}'}, ensure_ascii=False)}\n\n"
            else:
                device = "cpu"
                yield f"data: {json.dumps({'type': 'info', 'message': f'⚠️ 未检测到GPU，使用设备: {device}'}, ensure_ascii=False)}\n\n"
            
            # 创建训练器
            trainer = NCDMTrainer(course_id, device)
            
            # 开始训练（使用生成器模式）
            for message in trainer.train_stream(epochs=epochs, batch_size=batch_size, lr=lr):
                yield message
                
        except ValueError as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            print(f"训练失败: {error_msg}")
            yield f"data: {json.dumps({'type': 'error', 'message': f'训练失败: {str(e)}'}, ensure_ascii=False)}\n\n"
    
    return app.response_class(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


@app.route('/api/students/<int:student_id>/diagnosis/latest', methods=['GET'])
def get_latest_diagnosis(student_id):
    """获取学生最新的诊断报告"""
    course_id = request.args.get('course_id', type=int)
    
    query = DiagnosisReport.query.filter_by(student_id=student_id)
    if course_id:
        query = query.filter_by(course_id=course_id)
    
    report = query.order_by(DiagnosisReport.created_at.desc()).first()
    
    if not report:
        return jsonify({'error': '暂无诊断报告'}), 404
    
    return jsonify({
        'id': report.id,
        'created_at': report.created_at.isoformat(),
        'result': json.loads(report.diagnosis_result)
    })


@app.route('/api/students/<int:student_id>/learning-progress', methods=['GET'])
def get_learning_progress(student_id):
    """获取学生的学习进度"""
    course_id = request.args.get('course_id', type=int)
    
    # 获取所有知识点
    knowledges = Knowledge.query.filter_by(course_id=course_id).all()
    
    progress = []
    for k in knowledges:
        # 获取该知识点的所有题目
        questions = Question.query.filter_by(knowledge_id=k.id).all()
        question_ids = [q.id for q in questions]
        
        # 获取学生在这些题目上的答题记录
        records = QuestionRecord.query.filter(
            QuestionRecord.student_id == student_id,
            QuestionRecord.question_id.in_(question_ids)
        ).all()
        
        total = len(records)
        correct = sum(1 for r in records if r.is_correct)
        accuracy = round(correct / total * 100, 1) if total > 0 else 0
        
        progress.append({
            'knowledge_id': k.id,
            'knowledge_name': k.name,
            'total_questions': len(question_ids),
            'attempted_questions': total,
            'correct_questions': correct,
            'accuracy': accuracy,
            'mastery_level': accuracy  # mastery_level 和 accuracy 使用相同的值
        })
    
    return jsonify(progress)


@app.route('/api/students/<int:student_id>/question-records', methods=['GET'])
def get_student_question_records(student_id):
    """获取学生的答题记录"""
    course_id = request.args.get('course_id', type=int)
    
    # 构建查询
    query = QuestionRecord.query.filter_by(student_id=student_id)
    
    # 如果指定了课程，则只查询该课程的题目记录
    if course_id:
        query = query.join(Question).filter(Question.course_id == course_id)
    
    # 按时间倒序排列
    records = query.order_by(QuestionRecord.created_at.desc()).all()
    
    result = []
    for record in records:
        question = db.session.get(Question, record.question_id)
        if question:
            knowledge = db.session.get(Knowledge, question.knowledge_id)
            result.append({
                'id': record.id,
                'question_id': record.question_id,
                'question_content': question.content,
                'knowledge_name': knowledge.name if knowledge else '未知',
                'question_type': question.question_type,
                'difficulty': question.difficulty,
                'student_answer': record.answer,
                'correct_answer': question.answer,
                'is_correct': record.is_correct,
                'time_spent': record.time_spent,
                'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
    
    return jsonify(result)


# ==================== 教师端API ====================

@app.route('/api/teacher/students-overview', methods=['GET'])
def get_students_overview():
    """获取所有学生的学习概况"""
    course_id = request.args.get('course_id', type=int)
    students = Student.query.all()
    
    overview = []
    for student in students:
        records = QuestionRecord.query.join(Question).filter(
            QuestionRecord.student_id == student.id,
            Question.course_id == course_id
        ).all()
        
        total = len(records)
        correct = sum(1 for r in records if r.is_correct)
        
        overview.append({
            'id': student.id,
            'name': student.name,
            'employee_id': student.employee_id,
            'department': student.department,
            'total_questions': total,
            'correct_questions': correct,
            'accuracy': round(correct / total * 100, 1) if total > 0 else 0
        })
    
    return jsonify(overview)


@app.route('/api/teacher/weak-knowledges', methods=['GET'])
def get_weak_knowledges():
    """获取学生们的薄弱知识点分析"""
    course_id = request.args.get('course_id', type=int, default=1)
    
    knowledges = Knowledge.query.filter_by(course_id=course_id).all()
    
    weak_analysis = []
    for k in knowledges:
        questions = Question.query.filter_by(knowledge_id=k.id).all()
        question_ids = [q.id for q in questions]
        
        records = QuestionRecord.query.filter(
            QuestionRecord.question_id.in_(question_ids)
        ).all()
        
        total = len(records)
        correct = sum(1 for r in records if r.is_correct)
        accuracy = round(correct / total * 100, 1) if total > 0 else 0
        
        weak_analysis.append({
            'knowledge_id': k.id,
            'knowledge_name': k.name,
            'total_attempts': total,
            'accuracy': accuracy,
            'student_count': len(set(r.student_id for r in records))
        })
    
    # 按正确率排序，找出薄弱知识点
    weak_analysis.sort(key=lambda x: x['accuracy'])
    
    return jsonify(weak_analysis)


# ==================== AI生成相关API ====================

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/ai/upload-document', methods=['POST'])
def upload_document():
    """上传文档并自动生成课程和题目（流式）"""
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['file']
    course_name = request.form.get('course_name', '')
    
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file and allowed_file(file.filename):
        # 先提取原始扩展名，避免secure_filename处理中文文件名时丢失扩展名
        original_filename = file.filename
        _, original_ext = os.path.splitext(original_filename)
        original_ext = original_ext.lower()
        
        # 使用secure_filename处理文件名，但保留原始扩展名
        safe_name = secure_filename(original_filename)
        # 如果secure_filename处理后没有扩展名，手动添加
        if not safe_name.endswith(original_ext):
            # 如果safe_name为空（全中文文件名），使用时间戳作为文件名
            if not safe_name or safe_name == '':
                import time
                safe_name = f"upload_{int(time.time())}{original_ext}"
            else:
                safe_name = safe_name + original_ext
        
        filename = safe_name
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        def generate():
            """生成器函数，用于SSE流式输出"""
            try:
                print(f"[INFO] 开始处理文档: {filename}")
                
                def stream_callback(data):
                    """回调函数，发送SSE消息"""
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                
                # 根据配置选择使用V1还是V2
                use_agent_v2 = os.getenv('USE_AGENT_V2', 'true').lower() == 'true'
                
                if use_agent_v2:
                    print("[INFO] 使用Agent V2（LangChain智能Agent）")
                    ai_service = AIGenerationServiceV2()
                else:
                    print("[INFO] 使用V1（简单LLM调用）")
                    ai_service = AIGenerationService()
                
                result = ai_service.process_document(
                    file_path=filepath,
                    course_name=course_name if course_name else None,
                    stream_callback=lambda data: None  # 先不用回调，直接返回结果
                )
                
                # 发送完成消息
                yield f"data: {json.dumps({'type': 'complete', 'data': result}, ensure_ascii=False)}\n\n"
                
                # 删除上传的文件
                if os.path.exists(filepath):
                    os.remove(filepath)
                    
            except Exception as e:
                import traceback
                print(f"[ERROR] 处理文档失败:")
                print(traceback.format_exc())
                
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
                
                if os.path.exists(filepath):
                    os.remove(filepath)
        
        return app.response_class(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
    
    return jsonify({'error': '不支持的文件格式'}), 400


@app.route('/api/ai/upload-document-stream', methods=['POST'])
def upload_document_stream():
    """上传文档并自动生成课程和题目（真正的流式）"""
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['file']
    course_name = request.form.get('course_name', '')
    
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file and allowed_file(file.filename):
        # 先提取原始扩展名，避免secure_filename处理中文文件名时丢失扩展名
        original_filename = file.filename
        _, original_ext = os.path.splitext(original_filename)
        original_ext = original_ext.lower()
        
        # 使用secure_filename处理文件名，但保留原始扩展名
        safe_name = secure_filename(original_filename)
        # 如果secure_filename处理后没有扩展名，手动添加
        if not safe_name.endswith(original_ext):
            # 如果safe_name为空（全中文文件名），使用时间戳作为文件名
            if not safe_name or safe_name == '':
                import time
                safe_name = f"upload_{int(time.time())}{original_ext}"
            else:
                safe_name = safe_name + original_ext
        
        filename = safe_name
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        def generate():
            """生成器函数，用于SSE流式输出"""
            try:
                print(f"[INFO] 开始流式处理文档: {filename}")
                yield f"data: {json.dumps({'type': 'start', 'message': '开始处理文档'}, ensure_ascii=False)}\n\n"
                
                def stream_callback(data):
                    """回调函数，发送SSE消息"""
                    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                
                # 根据配置选择使用V1还是V2
                use_agent_v2 = os.getenv('USE_AGENT_V2', 'true').lower() == 'true'
                
                if use_agent_v2:
                    print("[INFO] 使用Agent V2（LangChain智能Agent）")
                    ai_service = AIGenerationServiceV2()
                else:
                    print("[INFO] 使用V1（简单LLM调用）")
                    ai_service = AIGenerationService()
                
                # 使用生成器模式
                for message in ai_service_stream(ai_service, filepath, course_name):
                    yield message
                
                # 删除上传的文件
                if os.path.exists(filepath):
                    os.remove(filepath)
                    
            except Exception as e:
                import traceback
                print(f"[ERROR] 处理文档失败:")
                print(traceback.format_exc())
                
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
                
                if os.path.exists(filepath):
                    os.remove(filepath)
        
        return app.response_class(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )
    
    return jsonify({'error': '不支持的文件格式'}), 400


def ai_service_stream(ai_service, filepath, course_name):
    """AI服务流式生成器"""
    from services.document_parser import DocumentParser
    from models import Course, Knowledge, Question
    
    # 创建应用上下文
    with app.app_context():
        # 1. 解析文档
        yield f"data: {json.dumps({'type': 'status', 'message': '📄 正在解析文档...'}, ensure_ascii=False)}\n\n"
        content = DocumentParser.parse_document(filepath)
        
        # 2. 分析文档结构
        if not course_name:
            yield f"data: {json.dumps({'type': 'status', 'message': '🔍 正在分析文档结构...'}, ensure_ascii=False)}\n\n"
            doc_structure = ai_service.llm.analyze_document_structure(content)
            course_name = doc_structure.get('course_name', '未命名课程')
            course_description = doc_structure.get('description', '')
        else:
            course_description = '基于文档自动生成的课程'
        
        # 3. 检查或创建课程
        existing_course = Course.query.filter_by(name=course_name).first()
        if existing_course:
            course = existing_course
            yield f"data: {json.dumps({'type': 'status', 'message': f'📚 找到已有课程: {course_name}，将在该课程中添加内容'}, ensure_ascii=False)}\n\n"
            # 更新课程描述（如果提供了新的描述）
            if course_description and course_description != '基于文档自动生成的课程':
                course.description = course_description
                db.session.flush()  # 立即保存更新
        else:
            yield f"data: {json.dumps({'type': 'status', 'message': f'📚 正在创建新课程: {course_name}'}, ensure_ascii=False)}\n\n"
            course = Course(
                name=course_name,
                description=course_description,
                total_hours=40
            )
            db.session.add(course)
            db.session.flush()
        
        yield f"data: {json.dumps({'type': 'course', 'data': {'id': course.id, 'name': course.name, 'is_new': not bool(existing_course)}}, ensure_ascii=False)}\n\n"
        
        # 4. 提取知识点
        yield f"data: {json.dumps({'type': 'status', 'message': '🧠 正在提取知识点...'}, ensure_ascii=False)}\n\n"
        knowledge_data = ai_service.llm.extract_knowledge_points(content, course_name)
        
        knowledges = []
        for kn_data in knowledge_data.get('knowledges', []):
            # 检查该课程下是否已有同名知识点
            existing_knowledge = Knowledge.query.filter_by(
                course_id=course.id,
                name=kn_data['name']
            ).first()
            
            if existing_knowledge:
                # 使用已有知识点
                knowledge = existing_knowledge
                yield f"data: {json.dumps({'type': 'status', 'message': f'✅ 使用已有知识点: {knowledge.name}'}, ensure_ascii=False)}\n\n"
            else:
                # 创建新知识点
                knowledge = Knowledge(
                    course_id=course.id,
                    name=kn_data['name'],
                    description=kn_data['description'],
                    level=kn_data.get('level', 1),
                    prerequisites=json.dumps(kn_data.get('prerequisites', []))
                )
                db.session.add(knowledge)
                db.session.flush()
                yield f"data: {json.dumps({'type': 'knowledge', 'data': {'name': kn_data['name'], 'description': kn_data['description']}}, ensure_ascii=False)}\n\n"
            
            knowledges.append(knowledge)
        
        # 5. 为每个知识点生成题目
        yield f"data: {json.dumps({'type': 'status', 'message': '✍️ 正在生成题目...'}, ensure_ascii=False)}\n\n"
        
        total_questions = 0
        for knowledge in knowledges:
            # 随机生成1-5道题目
            question_count = random.randint(1, 5)
            yield f"data: {json.dumps({'type': 'status', 'message': f'正在为「{knowledge.name}」生成{question_count}道题目...'}, ensure_ascii=False)}\n\n"
            
            try:
                questions_data = ai_service.llm.generate_questions(
                    content=content,
                    knowledge_name=knowledge.name,
                    knowledge_description=knowledge.description,
                    count=question_count
                )
                
                for q_data in questions_data.get('questions', []):
                    question = Question(
                        course_id=course.id,
                        knowledge_id=knowledge.id,
                        content=q_data['content'],
                        options=json.dumps(q_data['options'], ensure_ascii=False),
                        answer=q_data['answer'],
                        difficulty=q_data.get('difficulty', 2),
                        question_type=q_data.get('question_type', 'single')
                    )
                    db.session.add(question)
                    db.session.flush()
                    total_questions += 1
                    
                    # 实时发送每道题目
                    yield f"data: {json.dumps({'type': 'question', 'data': {'id': question.id, 'content': q_data['content'], 'knowledge_name': knowledge.name, 'difficulty': q_data.get('difficulty', 2), 'question_type': q_data.get('question_type', 'single')}}, ensure_ascii=False)}\n\n"
                    
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': f'生成「{knowledge.name}」题目失败'}, ensure_ascii=False)}\n\n"
        
        # 6. 提交到数据库
        db.session.commit()
        
        # 7. 发送完成消息
        result = {
            'success': True,
            'course_id': course.id,
            'course_name': course.name,
            'knowledge_count': len(knowledges),
            'question_count': total_questions
        }
        yield f"data: {json.dumps({'type': 'complete', 'data': result}, ensure_ascii=False)}\n\n"


@app.route('/api/ai/generate-questions/<int:knowledge_id>', methods=['POST'])
def generate_additional_questions(knowledge_id):
    """为指定知识点生成额外的题目"""
    data = request.json
    count = data.get('count', 5)
    
    try:
        # 根据配置选择使用V1还是V2
        use_agent_v2 = os.getenv('USE_AGENT_V2', 'true').lower() == 'true'
        
        if use_agent_v2:
            print("[INFO] 使用Agent V2生成额外题目")
            ai_service = AIGenerationServiceV2()
        else:
            print("[INFO] 使用V1生成额外题目")
            ai_service = AIGenerationService()
        
        result = ai_service.generate_additional_questions(knowledge_id, count)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'生成题目失败: {str(e)}'}), 500


@app.route('/api/ai/test-connection', methods=['GET'])
def test_ai_connection():
    """测试AI服务连接"""
    try:
        from services.llm_service import LLMService
        llm = LLMService()
        
        # 简单测试
        response = llm.client.chat.completions.create(
            model=llm.model,
            messages=[{"role": "user", "content": "你好"}],
            max_tokens=50
        )
        
        # 检查当前使用的版本
        use_agent_v2 = os.getenv('USE_AGENT_V2', 'true').lower() == 'true'
        version = 'V2 (LangChain Agent)' if use_agent_v2 else 'V1 (Simple LLM)'
        
        return jsonify({
            'success': True,
            'message': 'AI服务连接正常',
            'model': llm.model,
            'generation_version': version
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'AI服务连接失败: {str(e)}'
        }), 500


@app.route('/api/ai/version', methods=['GET'])
def get_ai_version():
    """获取当前AI生成服务版本"""
    use_agent_v2 = os.getenv('USE_AGENT_V2', 'true').lower() == 'true'
    
    return jsonify({
        'version': 'V2' if use_agent_v2 else 'V1',
        'description': 'LangChain智能Agent（具备推理、规划、质量控制能力）' if use_agent_v2 else '简单LLM调用',
        'features': {
            'reasoning': use_agent_v2,
            'quality_control': use_agent_v2,
            'auto_optimization': use_agent_v2,
            'duplicate_check': use_agent_v2,
            'multi_step_planning': use_agent_v2
        }
    })


if __name__ == '__main__':
    print("🚀 智能教育学习系统后端启动中...")
    print("📡 API服务地址: http://localhost:5000")
    # 启用多线程支持（开发环境）
    # 注意：生产环境建议使用 Gunicorn 或 uWSGI
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)

