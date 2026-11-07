"""
基于LangChain的智能题库生成Agent
使用LangChain 0.1.x API，真正的Agent框架实现
"""
import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType, Tool
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()


class QuestionGenerationAgent:
    """智能题库生成Agent - 真正的LangChain Agent实现"""
    
    def __init__(self):
        """初始化Agent"""
        # 初始化LLM
        self.llm = ChatOpenAI(
            model=os.getenv('LLM_MODEL', 'qwen-max'),
            api_key=os.getenv('ALI_API_KEY'),
            base_url=os.getenv('API_BASE'),
            temperature=0.7,
            max_tokens=3000
        )
        
        # 创建工具
        self.tools = self._create_tools()
        
        # 创建记忆
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # 初始化Agent
        try:
            self.agent = initialize_agent(
                tools=self.tools,
                llm=self.llm,
                agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True,
                memory=self.memory,
                handle_parsing_errors=True,
                max_iterations=5
            )
            print("[INFO] ✅ LangChain Agent初始化成功")
            print(f"[INFO] Agent类型: STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION")
            print(f"[INFO] 工具数量: {len(self.tools)}")
            self.agent_available = True
        except Exception as e:
            print(f"[WARN] Agent初始化失败，将使用直接调用模式: {str(e)}")
            self.agent = None
            self.agent_available = False
        
        print("[INFO] QuestionGenerationAgent初始化完成")
    
    def _create_tools(self) -> List[Tool]:
        """创建Agent可用的工具"""
        
        tools = [
            Tool(
                name="analyze_document",
                func=self._tool_analyze_document,
                description="""
                分析文档的结构和内容，识别主要章节、主题和知识点。
                输入：文档内容（字符串）
                输出：JSON格式的文档结构分析结果
                使用场景：当需要了解文档整体结构时
                """
            ),
            Tool(
                name="extract_knowledge",
                func=self._tool_extract_knowledge,
                description="""
                从文档内容中提取核心知识点。
                输入：JSON格式字符串，包含course_name和content
                输出：JSON格式的知识点列表
                使用场景：提取课程的核心知识点
                示例：{"course_name": "C语言", "content": "..."}
                """
            ),
            Tool(
                name="generate_single_choice",
                func=self._tool_generate_single,
                description="""
                生成单选题。
                输入：JSON格式，包含knowledge_name、knowledge_description、content、count
                输出：JSON格式的单选题列表
                示例：{"knowledge_name": "变量", "knowledge_description": "...", "content": "...", "count": 3}
                """
            ),
            Tool(
                name="generate_multiple_choice",
                func=self._tool_generate_multiple,
                description="""
                生成多选题。
                输入：JSON格式，包含knowledge_name、knowledge_description、content、count
                输出：JSON格式的多选题列表
                """
            ),
            Tool(
                name="generate_judge",
                func=self._tool_generate_judge,
                description="""
                生成判断题。
                输入：JSON格式，包含knowledge_name、knowledge_description、content、count
                输出：JSON格式的判断题列表
                """
            ),
            Tool(
                name="evaluate_quality",
                func=self._tool_evaluate_quality,
                description="""
                评估题目质量。
                输入：JSON格式的题目数据
                输出：质量评估报告
                """
            )
        ]
        
        return tools
    
    # ==================== 工具包装器 ====================
    
    def _tool_analyze_document(self, content: str) -> str:
        """工具：分析文档"""
        try:
            result = self.analyze_document_structure(content)
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    def _tool_extract_knowledge(self, input_str: str) -> str:
        """工具：提取知识点"""
        try:
            data = json.loads(input_str)
            result = self.extract_knowledge_points(
                data.get('course_name', ''),
                data.get('content', '')
            )
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    def _tool_generate_single(self, input_str: str) -> str:
        """工具：生成单选题"""
        try:
            data = json.loads(input_str)
            result = self._generate_single_choice(
                data.get('knowledge_name', ''),
                data.get('knowledge_description', ''),
                data.get('content', ''),
                data.get('count', 3)
            )
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    def _tool_generate_multiple(self, input_str: str) -> str:
        """工具：生成多选题"""
        try:
            data = json.loads(input_str)
            result = self._generate_multiple_choice(
                data.get('knowledge_name', ''),
                data.get('knowledge_description', ''),
                data.get('content', ''),
                data.get('count', 2)
            )
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    def _tool_generate_judge(self, input_str: str) -> str:
        """工具：生成判断题"""
        try:
            data = json.loads(input_str)
            result = self._generate_judge(
                data.get('knowledge_name', ''),
                data.get('knowledge_description', ''),
                data.get('content', ''),
                data.get('count', 2)
            )
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    def _tool_evaluate_quality(self, input_str: str) -> str:
        """工具：评估质量"""
        try:
            data = json.loads(input_str)
            result = self.evaluate_question_quality(data)
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    # ==================== 核心功能实现 ====================
    
    def analyze_document_structure(self, content: str) -> Dict[str, Any]:
        """分析文档结构"""
        prompt = f"""请分析以下课程文档的结构。

文档内容：
{content[:4000]}

请按照以下JSON格式返回：
{{
    "course_name": "课程名称",
    "description": "课程简介",
    "total_chapters": 章节数量,
    "chapters": [
        {{
            "title": "章节标题",
            "topics": ["主题1", "主题2"]
        }}
    ]
}}

只返回JSON数据。"""

        try:
            messages = [
                SystemMessage(content="你是一位文档分析专家。"),
                HumanMessage(content=prompt)
            ]
            response = self.llm.invoke(messages)
            result_text = response.content.strip()
            
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            return json.loads(result_text)
        except Exception as e:
            return {"error": str(e)}
    
    def extract_knowledge_points(self, course_name: str, content: str) -> Dict[str, Any]:
        """提取知识点"""
        prompt = f"""从以下课程内容中提取核心知识点。

课程名称：{course_name}
课程内容：
{content[:3000]}

请按照以下JSON格式返回：
{{
    "knowledges": [
        {{
            "name": "知识点名称",
            "description": "知识点描述",
            "level": 1,
            "prerequisites": []
        }}
    ]
}}

只返回JSON数据。"""

        try:
            messages = [
                SystemMessage(content="你是一位课程设计专家。"),
                HumanMessage(content=prompt)
            ]
            response = self.llm.invoke(messages)
            result_text = response.content.strip()
            
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            return json.loads(result_text)
        except Exception as e:
            return {"error": str(e)}
    
    def _generate_single_choice(self, knowledge_name: str, knowledge_description: str,
                                content: str, count: int) -> Dict[str, Any]:
        """生成单选题"""
        prompt = f"""生成{count}道单选题。

知识点：{knowledge_name}
描述：{knowledge_description}
参考内容：{content[:2000]}

JSON格式：
{{
    "questions": [
        {{
            "content": "题目内容",
            "question_type": "single",
            "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
            "answer": "A",
            "difficulty": 2,
            "explanation": "解析"
        }}
    ]
}}

只返回JSON。"""

        try:
            messages = [
                SystemMessage(content="你是出题专家。"),
                HumanMessage(content=prompt)
            ]
            response = self.llm.invoke(messages)
            result_text = response.content.strip()
            
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            return json.loads(result_text)
        except Exception as e:
            return {"questions": []}
    
    def _generate_multiple_choice(self, knowledge_name: str, knowledge_description: str,
                                   content: str, count: int) -> Dict[str, Any]:
        """生成多选题"""
        prompt = f"""生成{count}道多选题。

知识点：{knowledge_name}
描述：{knowledge_description}
参考内容：{content[:2000]}

JSON格式：
{{
    "questions": [
        {{
            "content": "题目内容",
            "question_type": "multiple",
            "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
            "answer": "ABC",
            "difficulty": 2,
            "explanation": "解析"
        }}
    ]
}}

只返回JSON。"""

        try:
            messages = [
                SystemMessage(content="你是出题专家。"),
                HumanMessage(content=prompt)
            ]
            response = self.llm.invoke(messages)
            result_text = response.content.strip()
            
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            return json.loads(result_text)
        except Exception as e:
            return {"questions": []}
    
    def _generate_judge(self, knowledge_name: str, knowledge_description: str,
                        content: str, count: int) -> Dict[str, Any]:
        """生成判断题"""
        prompt = f"""生成{count}道判断题。

知识点：{knowledge_name}
描述：{knowledge_description}
参考内容：{content[:2000]}

JSON格式：
{{
    "questions": [
        {{
            "content": "判断题陈述",
            "question_type": "judge",
            "options": ["正确", "错误"],
            "answer": "正确",
            "difficulty": 1,
            "explanation": "解析"
        }}
    ]
}}

只返回JSON。"""

        try:
            messages = [
                SystemMessage(content="你是出题专家。"),
                HumanMessage(content=prompt)
            ]
            response = self.llm.invoke(messages)
            result_text = response.content.strip()
            
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            return json.loads(result_text)
        except Exception as e:
            return {"questions": []}
    
    def evaluate_question_quality(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """评估题目质量"""
        prompt = f"""评估题目质量。

题目：{json.dumps(question, ensure_ascii=False)}

返回JSON：
{{
    "overall_score": 85,
    "is_acceptable": true,
    "issues": [],
    "suggestions": []
}}

只返回JSON。"""

        try:
            messages = [
                SystemMessage(content="你是质量评估专家。"),
                HumanMessage(content=prompt)
            ]
            response = self.llm.invoke(messages)
            result_text = response.content.strip()
            
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            return json.loads(result_text)
        except Exception as e:
            return {"overall_score": 0, "is_acceptable": False}
    
    # ==================== Agent主要接口 ====================
    
    def generate_questions_for_knowledge(
        self,
        knowledge_name: str,
        knowledge_description: str,
        content: str,
        total_count: int = 5,
        existing_questions: List[Dict] = None,
        enable_quality_check: bool = False
    ) -> Dict[str, Any]:
        """使用Agent为指定知识点生成题目"""
        print(f"[INFO] 开始为知识点「{knowledge_name}」生成{total_count}道题目")
        
        # 如果Agent可用，使用Agent
        if self.agent_available and self.agent:
            try:
                print("[INFO] 🤖 使用Agent自主规划生成题目...")
                
                task = f"""请为知识点「{knowledge_name}」生成{total_count}道题目。

知识点描述：{knowledge_description}

要求：
1. 使用generate_single_choice工具生成{total_count//2}道单选题
2. 使用generate_multiple_choice工具生成{total_count//4}道多选题
3. 使用generate_judge工具生成{total_count//4}道判断题

每个工具的输入格式为JSON字符串，包含knowledge_name、knowledge_description、content、count字段。

最后返回所有生成的题目（JSON格式）。"""

                result = self.agent.run(task)
                
                print(f"[INFO] ✅ Agent执行完成")
                
                return {
                    "success": True,
                    "result": result
                }
                
            except Exception as e:
                print(f"[WARN] Agent执行失败，使用直接生成: {str(e)}")
        
        # 直接生成（回退方案）
        print("[INFO] 使用直接生成模式...")
        return self._direct_generate(knowledge_name, knowledge_description, content, total_count)
    
    def _direct_generate(self, knowledge_name: str, knowledge_description: str,
                        content: str, total_count: int) -> Dict[str, Any]:
        """直接生成题目（不使用Agent）"""
        all_questions = []
        
        # 单选题
        single_count = total_count // 2
        if single_count > 0:
            result = self._generate_single_choice(
                knowledge_name, knowledge_description, content, single_count
            )
            all_questions.extend(result.get('questions', []))
        
        # 多选题
        multiple_count = total_count // 4
        if multiple_count > 0:
            result = self._generate_multiple_choice(
                knowledge_name, knowledge_description, content, multiple_count
            )
            all_questions.extend(result.get('questions', []))
        
        # 判断题
        judge_count = total_count - single_count - multiple_count
        if judge_count > 0:
            result = self._generate_judge(
                knowledge_name, knowledge_description, content, judge_count
            )
            all_questions.extend(result.get('questions', []))
        
        return {
            "success": True,
            "result": json.dumps({"questions": all_questions}, ensure_ascii=False)
        }
    
    def extract_knowledge_from_document(
        self,
        content: str,
        course_name: str = None
    ) -> Dict[str, Any]:
        """使用Agent从文档中提取知识点"""
        print(f"[INFO] 开始分析文档并提取知识点")
        
        # 如果Agent可用，使用Agent
        if self.agent_available and self.agent:
            try:
                print("[INFO] 🤖 使用Agent自主规划提取知识点...")
                
                task = f"""请分析文档并提取知识点。

{"课程名称：" + course_name if course_name else ""}

文档内容：
{content[:5000]}

步骤：
1. 使用analyze_document工具分析文档结构
2. 使用extract_knowledge工具提取知识点（输入格式：{{"course_name": "...", "content": "..."}}）

返回知识点数据（JSON格式）。"""

                result = self.agent.run(task)
                
                print(f"[INFO] ✅ Agent执行完成")
                
                return {
                    "success": True,
                    "result": result
                }
                
            except Exception as e:
                print(f"[WARN] Agent执行失败，使用直接提取: {str(e)}")
        
        # 直接提取（回退方案）
        print("[INFO] 使用直接提取模式...")
        if not course_name:
            doc_structure = self.analyze_document_structure(content)
            course_name = doc_structure.get('course_name', '未命名课程')
        
        knowledge_data = self.extract_knowledge_points(course_name, content)
        knowledge_data['course_name'] = course_name
        
        return {
            "success": True,
            "result": json.dumps(knowledge_data, ensure_ascii=False)
        }
