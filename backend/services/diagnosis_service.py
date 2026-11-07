"""
认知诊断服务
实现基于IRT（项目反应理论）的简化版认知诊断算法
"""
import json
from models import db, Knowledge, Question, QuestionRecord
from collections import defaultdict
import math
from services.recommendation_service import RecommendationService


class DiagnosisService:
    """认知诊断服务类"""
    
    def __init__(self):
        self.recommendation_service = RecommendationService()
    
    def diagnose_student(self, student_id, course_id):
        """
        对学生进行认知诊断（IRT算法）
        
        Args:
            student_id: 学生ID
            course_id: 课程ID
            
        Returns:
            dict: 诊断结果
        """
        # 获取课程的所有知识点
        knowledges = Knowledge.query.filter_by(course_id=course_id).all()
        
        # 计算每个知识点的掌握情况
        knowledge_mastery = []
        weak_knowledges = []
        strong_knowledges = []
        
        for knowledge in knowledges:
            mastery_info = self._calculate_knowledge_mastery(student_id, knowledge.id)
            mastery_info['knowledge_name'] = knowledge.name
            mastery_info['knowledge_id'] = knowledge.id
            
            knowledge_mastery.append(mastery_info)
            
            # 分类薄弱和优势知识点
            if mastery_info['mastery_level'] < 60:
                weak_knowledges.append(mastery_info)
            elif mastery_info['mastery_level'] >= 80:
                strong_knowledges.append(mastery_info)
        
        # 计算总体水平
        overall_mastery = self._calculate_overall_mastery(knowledge_mastery)
        
        # 生成学习建议
        suggestions = self._generate_suggestions(weak_knowledges, knowledge_mastery)
        
        # 使用智能推荐服务推荐题目
        knowledge_mastery_dict = {k['knowledge_id']: k['mastery_level'] for k in knowledge_mastery}
        recommended_questions = self.recommendation_service.recommend_questions(
            student_id, course_id, weak_knowledges, knowledge_mastery_dict
        )
        
        return {
            'algorithm': 'IRT',
            'overall_mastery': overall_mastery,
            'knowledge_mastery': knowledge_mastery,
            'weak_knowledges': weak_knowledges,
            'strong_knowledges': strong_knowledges,
            'suggestions': suggestions,
            'recommended_questions': recommended_questions
        }
    
    def _calculate_knowledge_mastery(self, student_id, knowledge_id):
        """
        计算学生对某个知识点的掌握程度
        
        Returns:
            dict: 包含掌握度、答题数量、正确率等信息
        """
        # 获取该知识点的所有题目
        questions = Question.query.filter_by(knowledge_id=knowledge_id).all()
        question_ids = [q.id for q in questions]
        
        # 获取学生的答题记录
        records = QuestionRecord.query.filter(
            QuestionRecord.student_id == student_id,
            QuestionRecord.question_id.in_(question_ids)
        ).all()
        
        if not records:
            return {
                'mastery_level': 0,
                'total_questions': len(questions),
                'attempted_questions': 0,
                'correct_questions': 0,
                'accuracy': 0,
                'avg_difficulty': 0,
                'status': 'not_started'
            }
        
        # 计算基本统计
        total_attempted = len(records)
        correct_count = sum(1 for r in records if r.is_correct)
        accuracy = (correct_count / total_attempted * 100) if total_attempted > 0 else 0
        
        # 考虑题目难度的加权计算
        weighted_score = 0
        total_weight = 0
        
        for record in records:
            question = Question.query.get(record.question_id)
            difficulty_weight = question.difficulty  # 难度作为权重
            
            if record.is_correct:
                weighted_score += difficulty_weight * 100
            
            total_weight += difficulty_weight
        
        # 掌握度 = 加权得分 / 总权重
        mastery_level = (weighted_score / total_weight) if total_weight > 0 else 0
        
        # 计算平均难度
        avg_difficulty = sum(Question.query.get(r.question_id).difficulty for r in records) / len(records)
        
        # 判断状态
        if mastery_level >= 80:
            status = 'mastered'
        elif mastery_level >= 60:
            status = 'learning'
        elif mastery_level >= 30:
            status = 'struggling'
        else:
            status = 'weak'
        
        return {
            'mastery_level': round(mastery_level, 1),
            'total_questions': len(questions),
            'attempted_questions': total_attempted,
            'correct_questions': correct_count,
            'accuracy': round(accuracy, 1),
            'avg_difficulty': round(avg_difficulty, 1),
            'status': status
        }
    
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
                    prerequisites = json.loads(k.prerequisites)
                    
                    if prerequisites:
                        suggestions.append({
                            'type': 'prerequisite',
                            'title': f'注意「{knowledge["knowledge_name"]}」的前置知识',
                            'content': '该知识点依赖其他基础知识，建议先巩固前置知识点后再深入学习。'
                        })
                        break
        
        return suggestions

