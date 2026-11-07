"""
AI生成服务 - 整合文档解析和大模型生成
"""
import os
import json
from models import db, Course, Knowledge, Question
from services.document_parser import DocumentParser
from services.llm_service import LLMService


class AIGenerationService:
    """AI自动生成题库服务"""
    
    def __init__(self):
        self.parser = DocumentParser()
        self.llm = LLMService()
    
    def process_document(self, file_path: str, course_name: str = None, stream_callback=None) -> dict:
        """
        处理上传的文档，自动生成课程、知识点和题目
        
        Args:
            file_path: 文档文件路径
            course_name: 课程名称（可选，如果不提供则由AI生成）
            
        Returns:
            dict: 生成结果统计
        """
        # 1. 解析文档
        print("📄 正在解析文档...")
        content = self.parser.parse_document(file_path)
        
        if len(content) < 100:
            raise Exception("文档内容过少，无法生成有效的题库")
        
        # 2. 分析文档结构（如果没有提供课程名）
        if not course_name:
            print("🔍 正在分析文档结构...")
            doc_structure = self.llm.analyze_document_structure(content)
            course_name = doc_structure.get('course_name', '未命名课程')
            course_description = doc_structure.get('description', '')
        else:
            course_description = '基于文档自动生成的课程'
        
        # 3. 检查或创建课程
        course = Course.query.filter_by(name=course_name).first()
        if course:
            print(f"📚 找到已有课程: {course_name}，将在该课程中添加内容")
            if stream_callback:
                stream_callback({'type': 'status', 'message': f'找到已有课程: {course_name}，将在该课程中添加内容'})
            # 更新课程描述（如果提供了新的描述）
            if course_description and course_description != '基于文档自动生成的课程':
                course.description = course_description
                db.session.flush()  # 立即保存更新
        else:
            print(f"📚 正在创建新课程: {course_name}")
            if stream_callback:
                stream_callback({'type': 'status', 'message': f'正在创建新课程: {course_name}'})
            course = Course(
                name=course_name,
                description=course_description,
                total_hours=40  # 默认值
            )
            db.session.add(course)
            db.session.flush()
        
        # 4. 提取知识点
        print("🧠 正在提取知识点...")
        if stream_callback:
            stream_callback({'type': 'status', 'message': '正在提取知识点...'})
        
        knowledge_data = self.llm.extract_knowledge_points(content, course_name)
        
        knowledges = []
        for idx, kn_data in enumerate(knowledge_data.get('knowledges', [])):
            # 检查该课程下是否已有同名知识点
            existing_knowledge = Knowledge.query.filter_by(
                course_id=course.id,
                name=kn_data['name']
            ).first()
            
            if existing_knowledge:
                # 使用已有知识点
                knowledge = existing_knowledge
                print(f"   ✅ 使用已有知识点: {knowledge.name}")
            else:
                # 创建新知识点（先不设置prerequisites，等所有知识点创建后再转换）
                knowledge = Knowledge(
                    course_id=course.id,
                    name=kn_data['name'],
                    description=kn_data['description'],
                    level=kn_data.get('level', 1),
                    prerequisites=json.dumps([])  # 先设为空，后续转换
                )
                db.session.add(knowledge)
                db.session.flush()
            
            knowledges.append(knowledge)
            
            if stream_callback:
                stream_callback({
                    'type': 'knowledge',
                    'data': {
                        'name': kn_data['name'],
                        'description': kn_data['description']
                    }
                })
        
        db.session.flush()
        
        # 转换prerequisites：将索引转换为实际的知识点ID
        print("🔗 正在构建知识点关系...")
        if stream_callback:
            stream_callback({'type': 'status', 'message': '正在构建知识点关系...'})
        
        for idx, kn_data in enumerate(knowledge_data.get('knowledges', [])):
            if idx < len(knowledges):
                knowledge = knowledges[idx]
                prerequisite_indices = kn_data.get('prerequisites', [])
                
                # 将索引转换为实际的知识点ID
                prerequisite_ids = []
                for pre_idx in prerequisite_indices:
                    if isinstance(pre_idx, int) and 0 <= pre_idx < len(knowledges):
                        prerequisite_ids.append(knowledges[pre_idx].id)
                    elif isinstance(pre_idx, str):
                        # 如果已经是ID字符串，尝试转换
                        try:
                            pre_id = int(pre_idx)
                            if 0 <= pre_id < len(knowledges):
                                prerequisite_ids.append(knowledges[pre_id].id)
                        except ValueError:
                            pass
                
                # 更新知识点的prerequisites
                knowledge.prerequisites = json.dumps(prerequisite_ids)
                if prerequisite_ids:
                    pre_names = [knowledges[i].name for i in prerequisite_indices if isinstance(i, int) and 0 <= i < len(knowledges)]
                    print(f"   🔗 {knowledge.name} 依赖: {', '.join(pre_names)}")
        
        db.session.flush()
        
        # 5. 为每个知识点生成题目
        print("✍️ 正在生成题目...")
        if stream_callback:
            stream_callback({'type': 'status', 'message': '正在生成题目...'})
        
        total_questions = 0
        
        import random
        
        for knowledge in knowledges:
            # 随机生成1-5道题目
            question_count = random.randint(1, 5)
            print(f"   生成知识点「{knowledge.name}」的题目（{question_count}道）...")
            if stream_callback:
                stream_callback({
                    'type': 'status', 
                    'message': f'正在为「{knowledge.name}」生成{question_count}道题目...'
                })
            
            try:
                questions_data = self.llm.generate_questions(
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
                    db.session.flush()  # 立即刷新，获取ID
                    total_questions += 1
                    
                    # 流式发送每道题目
                    if stream_callback:
                        stream_callback({
                            'type': 'question',
                            'data': {
                                'id': question.id,
                                'content': q_data['content'],
                                'knowledge_name': knowledge.name,
                                'difficulty': q_data.get('difficulty', 2),
                                'question_type': q_data.get('question_type', 'single')
                            }
                        })
                    
            except Exception as e:
                print(f"   ⚠️  生成题目失败: {str(e)}")
                if stream_callback:
                    stream_callback({
                        'type': 'error',
                        'message': f'生成「{knowledge.name}」题目失败: {str(e)}'
                    })
                continue
        
        # 6. 提交到数据库
        db.session.commit()
        
        print("✅ 课程生成完成！")
        
        return {
            'success': True,
            'course_id': course.id,
            'course_name': course.name,
            'knowledge_count': len(knowledges),
            'question_count': total_questions
        }
    
    def generate_additional_questions(self, knowledge_id: int, count: int = 5) -> dict:
        """
        为已有知识点生成额外的题目
        
        Args:
            knowledge_id: 知识点ID
            count: 生成数量
            
        Returns:
            dict: 生成结果
        """
        knowledge = Knowledge.query.get(knowledge_id)
        if not knowledge:
            raise Exception("知识点不存在")
        
        course = Course.query.get(knowledge.course_id)
        
        # 获取课程的相关内容（这里简化处理，实际应该从原始文档获取）
        content = f"{course.description}\n{knowledge.description}"
        
        questions_data = self.llm.generate_questions(
            content=content,
            knowledge_name=knowledge.name,
            knowledge_description=knowledge.description,
            count=count
        )
        
        generated_count = 0
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
            generated_count += 1
        
        db.session.commit()
        
        return {
            'success': True,
            'knowledge_name': knowledge.name,
            'generated_count': generated_count
        }

