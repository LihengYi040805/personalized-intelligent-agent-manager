"""
大模型服务 - 基于通义千问的智能题库生成
"""
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class LLMService:
    """大模型服务类"""
    
    def __init__(self):
        self.api_key = os.getenv('ALI_API_KEY')
        self.api_base = os.getenv('API_BASE')
        self.model = os.getenv('LLM_MODEL', 'qwen-max')
        
        # 打印配置信息（调试用）
        print(f"[DEBUG] API_KEY: {self.api_key[:20]}..." if self.api_key else "[ERROR] API_KEY未设置")
        print(f"[DEBUG] API_BASE: {self.api_base}")
        print(f"[DEBUG] MODEL: {self.model}")
        
        # 初始化OpenAI客户端（兼容通义千问API）
        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.api_base,
                timeout=60.0,
                max_retries=2
            )
            print("[INFO] OpenAI客户端初始化成功")
        except Exception as e:
            print(f"[ERROR] OpenAI客户端初始化失败: {str(e)}")
            raise
    
    def extract_knowledge_points(self, content: str, course_name: str) -> dict:
        """
        从文档内容中提取知识点
        
        Args:
            content: 文档内容
            course_name: 课程名称
            
        Returns:
            dict: 包含知识点列表和关系的结构化数据
        """
        prompt = f"""你是一位专业的课程设计专家。请分析以下课程内容，提取出关键知识点。

课程名称：{course_name}

课程内容：
{content[:3000]}  # 限制内容长度

请按照以下JSON格式返回知识点信息：
{{
    "knowledges": [
        {{
            "name": "知识点名称",
            "description": "知识点详细描述",
            "level": 1,  // 知识点层级：1-基础，2-进阶，3-高级，4-专家
            "prerequisites": []  // 前置知识点的索引列表，例如[0, 1]表示依赖第0和第1个知识点
        }}
    ]
}}

要求：
1. 提取5-10个核心知识点
2. 知识点名称简洁明了（5-15字）
3. 描述清晰具体（20-50字）
4. 合理设置知识点层级和依赖关系
5. 确保返回的是有效的JSON格式

只返回JSON数据，不要包含其他内容。"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位专业的课程设计专家，擅长提取和组织知识点。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 清理可能的markdown代码块标记
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
            
            result = json.loads(result_text)
            return result
            
        except Exception as e:
            print(f"提取知识点失败: {str(e)}")
            raise
    
    def generate_questions(self, content: str, knowledge_name: str, knowledge_description: str, count: int = 5) -> dict:
        """
        基于知识点生成题目
        
        Args:
            content: 文档内容
            knowledge_name: 知识点名称
            knowledge_description: 知识点描述
            count: 生成题目数量
            
        Returns:
            dict: 包含题目列表的结构化数据
        """
        prompt = f"""你是一位专业的考试出题专家。请基于以下知识点生成{count}道高质量的练习题。

知识点：{knowledge_name}
知识点描述：{knowledge_description}

参考内容：
{content[:2000]}

请按照以下JSON格式返回题目：
{{
    "questions": [
        {{
            "content": "题目内容（清晰、具体、专业）",
            "question_type": "single",  // single-单选题, multiple-多选题
            "options": ["选项A", "选项B", "选项C", "选项D"],
            "answer": "A",  // 单选题答案为单个字母，多选题答案为字母组合如"ABC"
            "difficulty": 2,  // 1-简单, 2-中等, 3-困难
            "explanation": "答案解析（简要说明为什么这个答案正确）"
        }}
    ]
}}

出题要求：
1. 题目应该紧扣知识点，考查理解和应用能力
2. 单选题和多选题都要有，比例约为3:2
3. 难度分布：简单2题，中等2题，困难1题
4. 选项设计合理，干扰项有迷惑性但不能误导
5. 每道题都要有清晰的答案解析
6. 确保返回的是有效的JSON格式

只返回JSON数据，不要包含其他内容。"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位专业的考试出题专家，擅长设计高质量的考试题目。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=3000
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 清理可能的markdown代码块标记
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
            
            result = json.loads(result_text)
            return result
            
        except Exception as e:
            print(f"生成题目失败: {str(e)}")
            raise
    
    def analyze_document_structure(self, content: str) -> dict:
        """
        分析文档结构，识别章节和主题
        
        Args:
            content: 文档内容
            
        Returns:
            dict: 文档结构分析结果
        """
        prompt = f"""请分析以下教学文档的结构，识别主要章节和主题。

文档内容：
{content[:4000]}

请按照以下JSON格式返回：
{{
    "course_name": "课程名称",
    "description": "课程简介",
    "chapters": [
        {{
            "title": "章节标题",
            "topics": ["主题1", "主题2"]
        }}
    ]
}}

只返回JSON数据。"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位文档分析专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1500
            )
            
            result_text = response.choices[0].message.content.strip()
            
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
            
            result = json.loads(result_text)
            return result
            
        except Exception as e:
            print(f"分析文档结构失败: {str(e)}")
            raise

