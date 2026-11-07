"""
NCDM (Neural Cognitive Diagnosis Model) 认知诊断服务
基于神经网络的认知诊断模型（仅支持神经网络模式）
"""
import json
import os
import torch
from flask import current_app
from models import db, Knowledge, Question, QuestionRecord
from services.ncdm_trainer import NCDMTrainer
from services.recommendation_service import RecommendationService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NCDMService:
    """NCDM认知诊断服务类"""
    
    def __init__(self):
        """
        初始化NCDM服务（仅支持神经网络模式）
        """
        self.trainer = None
        self.recommendation_service = RecommendationService()
        # 检测GPU
        if torch.cuda.is_available():
            self.device = "cuda"
            gpu_name = torch.cuda.get_device_name(0)
            logger.info(f"✅ 检测到GPU: {gpu_name}，使用设备: {self.device}")
        else:
            self.device = "cpu"
            logger.warning(f"⚠️ 未检测到GPU，使用设备: {self.device}")
            logger.warning(f"   提示：如需使用GPU，请安装CUDA版本的PyTorch")
    
    def diagnose_student(self, student_id, course_id):
        """
        使用NCDM神经网络算法对学生进行认知诊断
        
        Args:
            student_id: 学生ID
            course_id: 课程ID
            
        Returns:
            dict: 诊断结果
            
        Raises:
            FileNotFoundError: 如果模型文件不存在
            Exception: 如果模型加载或诊断失败
        """
        # 检查模型文件是否存在（使用绝对路径，基于backend目录）
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(base_dir, "models", f"ncdm_course_{course_id}.pth")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"NCDM模型文件不存在: {model_path}\n"
                f"请先训练模型：POST /api/ncdm/train/{course_id}"
            )
        
        try:
            return self._diagnose_with_neural_network(student_id, course_id, model_path)
        except Exception as e:
            logger.error(f"神经网络模型诊断失败: {str(e)}")
            raise Exception(f"NCDM模型诊断失败: {str(e)}")
    
    def _diagnose_with_neural_network(self, student_id, course_id, model_path):
        """使用神经网络模型进行诊断"""
        # 使用current_app或延迟导入app，避免循环导入
        from app import app
        with app.app_context():
            # 加载模型
            trainer = NCDMTrainer(course_id, self.device)
            trainer.load_model(model_path)
            
            # 获取课程的所有知识点
            knowledges = Knowledge.query.filter_by(course_id=course_id).all()
            
            # 预测学生掌握度
            mastery_dict = trainer.predict_student_mastery(student_id)
            
            # 获取学生的答题记录用于统计
            all_records = QuestionRecord.query.filter_by(student_id=student_id).all()
            student_question_matrix = self._build_interaction_matrix(student_id, course_id, all_records)
            
            # 构建知识点掌握情况
            knowledge_mastery = []
            weak_knowledges = []
            strong_knowledges = []
            
            for knowledge in knowledges:
                # 从神经网络获取掌握度
                neural_mastery = mastery_dict.get(knowledge.id, 0.0)
                
                # 获取统计信息
                questions = Question.query.filter_by(knowledge_id=knowledge.id).all()
                question_ids = [q.id for q in questions]
                knowledge_records = [
                    student_question_matrix.get(qid) 
                    for qid in question_ids 
                    if qid in student_question_matrix
                ]
                
                total_attempted = len(knowledge_records)
                correct_count = sum(1 for r in knowledge_records if r['correct']) if knowledge_records else 0
                accuracy = (correct_count / total_attempted * 100) if total_attempted > 0 else 0
                avg_difficulty = sum(r['difficulty'] for r in knowledge_records) / len(knowledge_records) if knowledge_records else 0
                
                mastery_level = neural_mastery  # 使用神经网络预测的掌握度
                
                # 判断状态
                if mastery_level >= 80:
                    status = 'mastered'
                elif mastery_level >= 60:
                    status = 'learning'
                elif mastery_level >= 30:
                    status = 'struggling'
                else:
                    status = 'weak'
                
                mastery_info = {
                    'knowledge_id': knowledge.id,
                    'knowledge_name': knowledge.name,
                    'mastery_level': round(mastery_level, 1),
                    'total_questions': len(questions),
                    'attempted_questions': total_attempted,
                    'correct_questions': correct_count,
                    'accuracy': round(accuracy, 1),
                    'avg_difficulty': round(avg_difficulty, 1),
                    'status': status
                }
                
                knowledge_mastery.append(mastery_info)
                
                if mastery_level < 60:
                    weak_knowledges.append(mastery_info)
                elif mastery_level >= 80:
                    strong_knowledges.append(mastery_info)
            
            overall_mastery = self._calculate_overall_mastery(knowledge_mastery)
            suggestions = self._generate_suggestions(weak_knowledges, knowledge_mastery)
            
            # 使用智能推荐服务推荐题目
            knowledge_mastery_dict = {k['knowledge_id']: k['mastery_level'] for k in knowledge_mastery}
            recommended_questions = self.recommendation_service.recommend_questions(
                student_id, course_id, weak_knowledges, knowledge_mastery_dict
            )
            
            return {
                'algorithm': 'NCDM',
                'overall_mastery': overall_mastery,
                'knowledge_mastery': knowledge_mastery,
                'weak_knowledges': weak_knowledges,
                'strong_knowledges': strong_knowledges,
                'suggestions': suggestions,
                'recommended_questions': recommended_questions
            }
    
    def _build_interaction_matrix(self, student_id, course_id, records):
        """
        构建学生-题目交互矩阵
        
        Returns:
            dict: {question_id: {'correct': bool, 'difficulty': int, 'knowledge_id': int}}
        """
        matrix = {}
        
        for record in records:
            question = Question.query.get(record.question_id)
            if question and question.course_id == course_id:
                matrix[record.question_id] = {
                    'correct': record.is_correct,
                    'difficulty': question.difficulty,
                    'knowledge_id': question.knowledge_id,
                    'time_spent': record.time_spent
                }
        
        return matrix
    
    def _calculate_overall_mastery(self, knowledge_mastery):
        """计算总体掌握水平"""
        if not knowledge_mastery:
            return 0
        
        total_mastery = sum(k['mastery_level'] for k in knowledge_mastery)
        avg_mastery = total_mastery / len(knowledge_mastery)
        
        return round(avg_mastery, 1)
    
    def _generate_suggestions(self, weak_knowledges, all_knowledges):
        """生成学习建议"""
        suggestions = []
        
        if not weak_knowledges:
            suggestions.append({
                'type': 'congratulation',
                'title': '表现优秀',
                'content': '你已经很好地掌握了课程的各个知识点，继续保持！建议尝试更高难度的题目来巩固知识。'
            })
        else:
            # 按掌握度排序薄弱知识点
            weak_knowledges_sorted = sorted(weak_knowledges, key=lambda x: x['mastery_level'])
            
            for weak in weak_knowledges_sorted[:3]:  # 取最薄弱的3个
                suggestions.append({
                    'type': 'improvement',
                    'title': f'加强「{weak["knowledge_name"]}」的学习',
                    'content': f'该知识点掌握度为{weak["mastery_level"]}%，建议多做相关练习题，尤其是中等难度的题目。',
                    'knowledge_id': weak['knowledge_id']
                })
            
            # 检查是否有前置知识点没掌握
            for knowledge in all_knowledges:
                if knowledge['mastery_level'] < 60:
                    k = Knowledge.query.get(knowledge['knowledge_id'])
                    if k and k.prerequisites:
                        try:
                            prerequisites = json.loads(k.prerequisites) if k.prerequisites else []
                            if prerequisites:
                                suggestions.append({
                                    'type': 'prerequisite',
                                    'title': f'注意「{knowledge["knowledge_name"]}」的前置知识',
                                    'content': '该知识点依赖其他基础知识，建议先巩固前置知识点后再深入学习。'
                                })
                                break
                        except (json.JSONDecodeError, TypeError):
                            # 如果prerequisites不是有效的JSON，跳过
                            pass
        
        return suggestions

