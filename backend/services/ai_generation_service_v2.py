"""
AI生成服务 V2 - 基于LangChain Agent的智能题库生成
相比V1版本，具有更强的推理、规划和质量控制能力
"""
import os
import json
from typing import Dict, Any, Optional, Callable
from models import db, Course, Knowledge, Question
from services.document_parser import DocumentParser
from services.question_generation_agent import QuestionGenerationAgent


class AIGenerationServiceV2:
    """AI智能题库生成服务 V2"""
    
    def __init__(self):
        self.parser = DocumentParser()
        self.agent = QuestionGenerationAgent()
    
    def process_document(
        self,
        file_path: str,
        course_name: str = None,
        stream_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        处理上传的文档，使用Agent智能生成课程、知识点和题目
        
        Args:
            file_path: 文档文件路径
            course_name: 课程名称（可选）
            stream_callback: 流式回调函数
            
        Returns:
            生成结果统计
        """
        # 1. 解析文档
        print("📄 正在解析文档...")
        if stream_callback:
            stream_callback({'type': 'status', 'message': '正在解析文档...'})
        
        content = self.parser.parse_document(file_path)
        
        if len(content) < 100:
            raise Exception("文档内容过少，无法生成有效的题库")
        
        print(f"✅ 文档解析完成，共 {len(content)} 字符")
        
        # 2. 使用Agent分析文档并提取知识点
        print("🤖 启动智能Agent分析文档...")
        if stream_callback:
            stream_callback({'type': 'status', 'message': '智能Agent正在分析文档结构...'})
        
        extraction_result = self.agent.extract_knowledge_from_document(
            content=content,
            course_name=course_name
        )
        
        if not extraction_result.get('success'):
            raise Exception(f"Agent分析失败: {extraction_result.get('error')}")
        
        # 解析Agent返回的结果
        agent_output = extraction_result.get('result', '')
        knowledge_data = self._parse_agent_output(agent_output)
        
        # 3. 创建或更新课程
        if not course_name:
            course_name = knowledge_data.get('course_name', '未命名课程')
        
        course = Course.query.filter_by(name=course_name).first()
        if course:
            print(f"📚 找到已有课程: {course_name}")
            if stream_callback:
                stream_callback({'type': 'status', 'message': f'找到已有课程: {course_name}'})
        else:
            print(f"📚 创建新课程: {course_name}")
            if stream_callback:
                stream_callback({'type': 'status', 'message': f'创建新课程: {course_name}'})
            
            course = Course(
                name=course_name,
                description=knowledge_data.get('description', '基于文档自动生成的课程'),
                total_hours=40
            )
            db.session.add(course)
            db.session.flush()
        
        # 4. 创建知识点
        print("🧠 正在创建知识点...")
        if stream_callback:
            stream_callback({'type': 'status', 'message': '正在创建知识点...'})
        
        knowledges = []
        knowledge_list = knowledge_data.get('knowledges', [])
        
        for idx, kn_data in enumerate(knowledge_list):
            # 检查是否已存在
            existing_knowledge = Knowledge.query.filter_by(
                course_id=course.id,
                name=kn_data['name']
            ).first()
            
            if existing_knowledge:
                knowledge = existing_knowledge
                print(f"   ✅ 使用已有知识点: {knowledge.name}")
            else:
                knowledge = Knowledge(
                    course_id=course.id,
                    name=kn_data['name'],
                    description=kn_data.get('description', ''),
                    level=kn_data.get('level', 1),
                    prerequisites=json.dumps([])  # 先设为空
                )
                db.session.add(knowledge)
                db.session.flush()
                print(f"   ✅ 创建知识点: {knowledge.name}")
            
            knowledges.append(knowledge)
            
            if stream_callback:
                stream_callback({
                    'type': 'knowledge',
                    'data': {
                        'name': kn_data['name'],
                        'description': kn_data.get('description', '')
                    }
                })
        
        # 5. 建立知识点依赖关系
        print("🔗 正在建立知识点依赖关系...")
        if stream_callback:
            stream_callback({'type': 'status', 'message': '正在建立知识点依赖关系...'})
        
        for idx, kn_data in enumerate(knowledge_list):
            if idx < len(knowledges):
                knowledge = knowledges[idx]
                prerequisite_indices = kn_data.get('prerequisites', [])
                
                prerequisite_ids = []
                for pre_idx in prerequisite_indices:
                    if isinstance(pre_idx, int) and 0 <= pre_idx < len(knowledges):
                        prerequisite_ids.append(knowledges[pre_idx].id)
                
                knowledge.prerequisites = json.dumps(prerequisite_ids)
                
                if prerequisite_ids:
                    pre_names = [knowledges[i].name for i in prerequisite_indices 
                                if isinstance(i, int) and 0 <= i < len(knowledges)]
                    print(f"   🔗 {knowledge.name} 依赖: {', '.join(pre_names)}")
        
        db.session.flush()
        
        # 6. 使用Agent为每个知识点生成题目
        print("✍️ 正在使用Agent生成题目...")
        if stream_callback:
            stream_callback({'type': 'status', 'message': 'Agent正在智能生成题目...'})
        
        total_questions = 0
        
        for knowledge in knowledges:
            # 获取该知识点已有的题目（用于去重）
            existing_questions = Question.query.filter_by(
                knowledge_id=knowledge.id
            ).all()
            
            existing_questions_data = [
                {
                    'content': q.content,
                    'question_type': q.question_type
                }
                for q in existing_questions
            ]
            
            # 使用Agent生成题目
            question_count = 5  # 每个知识点生成5道题
            print(f"   🤖 Agent正在为「{knowledge.name}」生成{question_count}道题目...")
            if stream_callback:
                stream_callback({
                    'type': 'status',
                    'message': f'Agent正在为「{knowledge.name}」生成{question_count}道题目...'
                })
            
            try:
                generation_result = self.agent.generate_questions_for_knowledge(
                    knowledge_name=knowledge.name,
                    knowledge_description=knowledge.description,
                    content=content,
                    total_count=question_count,
                    existing_questions=existing_questions_data
                )
                
                if not generation_result.get('success'):
                    print(f"   ⚠️  Agent生成失败: {generation_result.get('error')}")
                    continue
                
                # 解析Agent生成的题目
                questions_data = self._parse_questions_from_agent(
                    generation_result.get('result', '')
                )
                
                # 保存题目到数据库
                for q_data in questions_data:
                    question = Question(
                        course_id=course.id,
                        knowledge_id=knowledge.id,
                        content=q_data['content'],
                        options=json.dumps(q_data.get('options', []), ensure_ascii=False),
                        answer=q_data['answer'],
                        difficulty=q_data.get('difficulty', 2),
                        question_type=q_data.get('question_type', 'single')
                    )
                    db.session.add(question)
                    db.session.flush()
                    total_questions += 1
                    
                    print(f"   ✅ 生成题目: {q_data['content'][:30]}...")
                    
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
        
        # 7. 提交到数据库
        db.session.commit()
        
        print("✅ 课程生成完成！")
        if stream_callback:
            stream_callback({
                'type': 'complete',
                'message': '课程生成完成！'
            })
        
        return {
            'success': True,
            'course_id': course.id,
            'course_name': course.name,
            'knowledge_count': len(knowledges),
            'question_count': total_questions
        }
    
    def _parse_agent_output(self, output: str) -> Dict[str, Any]:
        """解析Agent的输出结果"""
        try:
            # 尝试从输出中提取JSON
            # Agent的输出可能包含思考过程，需要提取最终的JSON结果
            
            # 查找JSON代码块
            if '```json' in output:
                json_start = output.find('```json') + 7
                json_end = output.find('```', json_start)
                json_str = output[json_start:json_end].strip()
            elif '```' in output:
                json_start = output.find('```') + 3
                json_end = output.find('```', json_start)
                json_str = output[json_start:json_end].strip()
            elif '{' in output and '}' in output:
                # 尝试提取JSON对象
                json_start = output.find('{')
                json_end = output.rfind('}') + 1
                json_str = output[json_start:json_end]
            else:
                json_str = output
            
            result = json.loads(json_str)
            return result
            
        except Exception as e:
            print(f"⚠️  解析Agent输出失败: {str(e)}")
            print(f"原始输出: {output[:500]}...")
            # 返回默认结构
            return {
                'course_name': '未命名课程',
                'description': '',
                'knowledges': []
            }
    
    def _parse_questions_from_agent(self, output: str) -> list:
        """从Agent输出中解析题目列表"""
        try:
            data = self._parse_agent_output(output)
            
            # Agent可能返回不同的结构
            if 'questions' in data:
                return data['questions']
            elif isinstance(data, list):
                return data
            else:
                return []
                
        except Exception as e:
            print(f"⚠️  解析题目失败: {str(e)}")
            return []
    
    def generate_additional_questions(
        self,
        knowledge_id: int,
        count: int = 5
    ) -> Dict[str, Any]:
        """
        为已有知识点生成额外的题目（使用Agent）
        
        Args:
            knowledge_id: 知识点ID
            count: 生成数量
            
        Returns:
            生成结果
        """
        knowledge = Knowledge.query.get(knowledge_id)
        if not knowledge:
            raise Exception("知识点不存在")
        
        course = Course.query.get(knowledge.course_id)
        
        # 获取已有题目
        existing_questions = Question.query.filter_by(
            knowledge_id=knowledge_id
        ).all()
        
        existing_questions_data = [
            {
                'content': q.content,
                'question_type': q.question_type
            }
            for q in existing_questions
        ]
        
        # 使用Agent生成题目
        content = f"{course.description}\n{knowledge.description}"
        
        generation_result = self.agent.generate_questions_for_knowledge(
            knowledge_name=knowledge.name,
            knowledge_description=knowledge.description,
            content=content,
            total_count=count,
            existing_questions=existing_questions_data
        )
        
        if not generation_result.get('success'):
            raise Exception(f"Agent生成失败: {generation_result.get('error')}")
        
        # 解析并保存题目
        questions_data = self._parse_questions_from_agent(
            generation_result.get('result', '')
        )
        
        generated_count = 0
        for q_data in questions_data:
            question = Question(
                course_id=course.id,
                knowledge_id=knowledge.id,
                content=q_data['content'],
                options=json.dumps(q_data.get('options', []), ensure_ascii=False),
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
