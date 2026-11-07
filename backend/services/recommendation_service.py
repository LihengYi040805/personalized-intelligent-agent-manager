"""
智能题目推荐服务
结合多种推荐算法，为学生提供个性化的题目推荐
"""
import json
import math
from collections import defaultdict
from models import db, Knowledge, Question, QuestionRecord, Student
from sqlalchemy import func


class RecommendationService:
    """智能推荐服务类"""
    
    def __init__(self):
        self.max_recommendations = 10  # 最多推荐题目数
    
    def recommend_questions(self, student_id, course_id, weak_knowledges, knowledge_mastery_dict):
        """
        综合推荐算法，为学生推荐题目
        
        Args:
            student_id: 学生ID
            course_id: 课程ID
            weak_knowledges: 薄弱知识点列表
            knowledge_mastery_dict: 知识点掌握度字典 {knowledge_id: mastery_level}
            
        Returns:
            list: 推荐题目列表
        """
        if not weak_knowledges:
            # 如果没有薄弱知识点，推荐高难度题目用于巩固
            return self._recommend_challenge_questions(student_id, course_id, knowledge_mastery_dict)
        
        # 1. 基于知识图谱的路径推荐（考虑前置知识）
        graph_recommendations = self._recommend_by_knowledge_graph(
            student_id, course_id, weak_knowledges, knowledge_mastery_dict
        )
        
        # 2. 难度自适应推荐
        adaptive_recommendations = self._recommend_by_adaptive_difficulty(
            student_id, course_id, weak_knowledges, knowledge_mastery_dict
        )
        
        # 3. 协同过滤推荐（基于相似学生）
        collaborative_recommendations = self._recommend_by_collaborative_filtering(
            student_id, course_id, weak_knowledges
        )
        
        # 4. 多样性推荐（题型多样化）
        diversity_recommendations = self._recommend_by_diversity(
            student_id, course_id, weak_knowledges
        )
        
        # 合并推荐结果并去重
        all_recommendations = self._merge_recommendations([
            graph_recommendations,
            adaptive_recommendations,
            collaborative_recommendations,
            diversity_recommendations
        ])
        
        # 排序并返回Top N
        return self._rank_and_filter(all_recommendations, student_id)[:self.max_recommendations]
    
    def _recommend_by_knowledge_graph(self, student_id, course_id, weak_knowledges, knowledge_mastery_dict):
        """
        基于知识图谱的推荐
        优先推荐前置知识点未掌握的题目
        """
        recommendations = []
        
        for weak in weak_knowledges:
            knowledge_id = weak['knowledge_id']
            knowledge = Knowledge.query.get(knowledge_id)
            
            if not knowledge:
                continue
            
            # 检查前置知识点
            try:
                prerequisites = json.loads(knowledge.prerequisites) if knowledge.prerequisites else []
            except (json.JSONDecodeError, TypeError):
                prerequisites = []
            
            # 如果有前置知识点未掌握，优先推荐前置知识点的题目
            if prerequisites:
                for prereq_id in prerequisites:
                    prereq_mastery = knowledge_mastery_dict.get(prereq_id, 0)
                    if prereq_mastery < 60:  # 前置知识点未掌握
                        prereq_questions = self._get_unfinished_questions(
                            student_id, prereq_id, course_id
                        )
                        for q in prereq_questions[:3]:  # 每个前置知识点推荐3题
                            recommendations.append({
                                'question': q,
                                'reason': 'prerequisite',
                                'priority': 10,  # 最高优先级
                                'knowledge_name': Knowledge.query.get(prereq_id).name
                            })
            
            # 推荐当前薄弱知识点的题目
            current_questions = self._get_unfinished_questions(
                student_id, knowledge_id, course_id
            )
            for q in current_questions[:3]:
                recommendations.append({
                    'question': q,
                    'reason': 'weak_knowledge',
                    'priority': 8,
                    'knowledge_name': knowledge.name
                })
        
        return recommendations
    
    def _recommend_by_adaptive_difficulty(self, student_id, course_id, weak_knowledges, knowledge_mastery_dict):
        """
        难度自适应推荐
        根据学生当前掌握度推荐合适难度的题目
        """
        recommendations = []
        
        for weak in weak_knowledges:
            knowledge_id = weak['knowledge_id']
            mastery_level = weak['mastery_level']
            
            # 根据掌握度确定推荐难度
            if mastery_level < 30:
                # 掌握度很低，推荐简单题
                target_difficulty = 1
                priority = 9
            elif mastery_level < 60:
                # 掌握度中等，推荐中等难度题
                target_difficulty = 2
                priority = 7
            else:
                # 掌握度较高但仍需提升，推荐困难题
                target_difficulty = 3
                priority = 6
            
            # 获取指定难度的未完成题目
            questions = Question.query.filter_by(
                knowledge_id=knowledge_id,
                course_id=course_id,
                difficulty=target_difficulty
            ).all()
            
            for question in questions:
                # 检查是否已做对
                record = QuestionRecord.query.filter_by(
                    student_id=student_id,
                    question_id=question.id,
                    is_correct=True
                ).first()
                
                if not record:
                    recommendations.append({
                        'question': question,
                        'reason': 'adaptive_difficulty',
                        'priority': priority,
                        'knowledge_name': weak['knowledge_name']
                    })
        
        return recommendations
    
    def _recommend_by_collaborative_filtering(self, student_id, course_id, weak_knowledges):
        """
        协同过滤推荐
        基于相似学生的做题记录推荐
        """
        recommendations = []
        
        # 找到相似学生（在相同薄弱知识点上有相似表现的学生）
        similar_students = self._find_similar_students(student_id, course_id, weak_knowledges)
        
        if not similar_students:
            return recommendations
        
        # 获取相似学生做对的题目
        for similar_student_id in similar_students[:5]:  # 取前5个相似学生
            for weak in weak_knowledges[:2]:  # 针对最薄弱的2个知识点
                knowledge_id = weak['knowledge_id']
                
                # 获取相似学生在该知识点上做对的题目
                similar_correct_records = QuestionRecord.query.join(Question).filter(
                    QuestionRecord.student_id == similar_student_id,
                    QuestionRecord.is_correct == True,
                    Question.knowledge_id == knowledge_id,
                    Question.course_id == course_id
                ).all()
                
                for record in similar_correct_records:
                    question = Question.query.get(record.question_id)
                    
                    # 检查当前学生是否已做对
                    current_record = QuestionRecord.query.filter_by(
                        student_id=student_id,
                        question_id=question.id,
                        is_correct=True
                    ).first()
                    
                    if not current_record:
                        recommendations.append({
                            'question': question,
                            'reason': 'collaborative',
                            'priority': 6,
                            'knowledge_name': weak['knowledge_name']
                        })
        
        return recommendations
    
    def _recommend_by_diversity(self, student_id, course_id, weak_knowledges):
        """
        多样性推荐
        确保推荐的题目类型多样化（单选、多选、判断）
        """
        recommendations = []
        question_types = ['single', 'multiple', 'judge']
        
        for weak in weak_knowledges[:2]:
            knowledge_id = weak['knowledge_id']
            
            # 为每种题型推荐1-2题
            for qtype in question_types:
                questions = Question.query.filter_by(
                    knowledge_id=knowledge_id,
                    course_id=course_id,
                    question_type=qtype
                ).all()
                
                for question in questions[:2]:
                    # 检查是否已做对
                    record = QuestionRecord.query.filter_by(
                        student_id=student_id,
                        question_id=question.id,
                        is_correct=True
                    ).first()
                    
                    if not record:
                        recommendations.append({
                            'question': question,
                            'reason': 'diversity',
                            'priority': 5,
                            'knowledge_name': weak['knowledge_name']
                        })
        
        return recommendations
    
    def _recommend_challenge_questions(self, student_id, course_id, knowledge_mastery_dict):
        """
        推荐挑战题目（当学生没有明显薄弱知识点时）
        """
        recommendations = []
        
        # 找出掌握度最高的知识点
        if not knowledge_mastery_dict:
            return recommendations
        
        sorted_knowledges = sorted(
            knowledge_mastery_dict.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # 推荐掌握度高的知识点的困难题目
        for knowledge_id, mastery in sorted_knowledges[:3]:
            if mastery >= 80:
                questions = Question.query.filter_by(
                    knowledge_id=knowledge_id,
                    course_id=course_id,
                    difficulty=3  # 困难题
                ).all()
                
                for question in questions[:3]:
                    record = QuestionRecord.query.filter_by(
                        student_id=student_id,
                        question_id=question.id,
                        is_correct=True
                    ).first()
                    
                    if not record:
                        knowledge = Knowledge.query.get(knowledge_id)
                        recommendations.append({
                            'question': question,
                            'reason': 'challenge',
                            'priority': 4,
                            'knowledge_name': knowledge.name if knowledge else '未知'
                        })
        
        return recommendations
    
    def _find_similar_students(self, student_id, course_id, weak_knowledges):
        """
        找到相似学生
        基于在相同薄弱知识点上的答题表现
        """
        if not weak_knowledges:
            return []
        
        # 获取当前学生在薄弱知识点上的答题记录
        weak_knowledge_ids = [w['knowledge_id'] for w in weak_knowledges]
        
        current_student_records = QuestionRecord.query.join(Question).filter(
            QuestionRecord.student_id == student_id,
            Question.knowledge_id.in_(weak_knowledge_ids),
            Question.course_id == course_id
        ).all()
        
        if not current_student_records:
            return []
        
        # 计算当前学生的正确率
        current_accuracy = sum(1 for r in current_student_records if r.is_correct) / len(current_student_records)
        
        # 找到其他学生
        all_students = Student.query.filter(Student.id != student_id).all()
        similar_students = []
        
        for student in all_students:
            # 获取该学生在相同知识点上的答题记录
            student_records = QuestionRecord.query.join(Question).filter(
                QuestionRecord.student_id == student.id,
                Question.knowledge_id.in_(weak_knowledge_ids),
                Question.course_id == course_id
            ).all()
            
            if not student_records:
                continue
            
            # 计算该学生的正确率
            student_accuracy = sum(1 for r in student_records if r.is_correct) / len(student_records)
            
            # 如果正确率相似（差距在20%以内）且该学生表现更好，认为是相似学生
            if 0 < student_accuracy - current_accuracy <= 0.3:
                similarity_score = 1 - abs(student_accuracy - current_accuracy)
                similar_students.append((student.id, similarity_score))
        
        # 按相似度排序
        similar_students.sort(key=lambda x: x[1], reverse=True)
        
        return [s[0] for s in similar_students]
    
    def _get_unfinished_questions(self, student_id, knowledge_id, course_id):
        """获取未完成或做错的题目"""
        questions = Question.query.filter_by(
            knowledge_id=knowledge_id,
            course_id=course_id
        ).all()
        
        unfinished = []
        for question in questions:
            record = QuestionRecord.query.filter_by(
                student_id=student_id,
                question_id=question.id,
                is_correct=True
            ).first()
            
            if not record:
                unfinished.append(question)
        
        return unfinished
    
    def _merge_recommendations(self, recommendation_lists):
        """
        合并多个推荐列表并去重
        """
        merged = {}
        
        for rec_list in recommendation_lists:
            for rec in rec_list:
                question_id = rec['question'].id
                
                # 如果题目已存在，保留优先级更高的
                if question_id in merged:
                    if rec['priority'] > merged[question_id]['priority']:
                        merged[question_id] = rec
                else:
                    merged[question_id] = rec
        
        return list(merged.values())
    
    def _rank_and_filter(self, recommendations, student_id):
        """
        对推荐结果排序并格式化输出
        """
        # 按优先级排序
        recommendations.sort(key=lambda x: x['priority'], reverse=True)
        
        # 格式化输出
        result = []
        for rec in recommendations:
            question = rec['question']
            result.append({
                'question_id': question.id,
                'content': question.content,
                'difficulty': question.difficulty,
                'question_type': question.question_type,
                'knowledge_name': rec['knowledge_name'],
                'course_id': question.course_id,
                'reason': rec['reason'],
                'priority': rec['priority']
            })
        
        return result
