"""
NCDM模型训练器
负责数据加载、模型训练和评估
"""
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import os
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score
import logging
from models import db, Student, Question, QuestionRecord, Knowledge
from services.ncdm_model import NCDMNet

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NCDMDataset(Dataset):
    """NCDM数据集"""
    
    def __init__(self, records, student_id_map, question_id_map, knowledge_id_map, knowledge_dim):
        """
        初始化数据集
        
        Args:
            records: 答题记录列表 [(student_id, question_id, knowledge_id, is_correct), ...]
            student_id_map: 学生ID到索引的映射
            question_id_map: 题目ID到索引的映射
            knowledge_id_map: 知识点ID到索引的映射
            knowledge_dim: 知识点维度
        """
        self.records = records
        self.student_id_map = student_id_map
        self.question_id_map = question_id_map
        self.knowledge_id_map = knowledge_id_map
        self.knowledge_dim = knowledge_dim
    
    def __len__(self):
        return len(self.records)
    
    def __getitem__(self, idx):
        student_id, question_id, knowledge_id, is_correct = self.records[idx]
        
        # 转换为索引
        student_idx = self.student_id_map[student_id]
        question_idx = self.question_id_map[question_id]
        knowledge_idx = self.knowledge_id_map[knowledge_id]
        
        # 构建知识点向量（one-hot，因为一个题目只对应一个知识点）
        knowledge_vector = np.zeros(self.knowledge_dim)
        knowledge_vector[knowledge_idx] = 1.0
        
        return (
            torch.LongTensor([student_idx]),
            torch.LongTensor([question_idx]),
            torch.FloatTensor(knowledge_vector),
            torch.FloatTensor([float(is_correct)])
        )


class NCDMTrainer:
    """NCDM模型训练器"""
    
    def __init__(self, course_id, device="cpu"):
        """
        初始化训练器
        
        Args:
            course_id: 课程ID
            device: 计算设备（cpu/cuda）
        """
        self.course_id = course_id
        self.device = device
        self.model = None
        self.student_id_map = {}
        self.question_id_map = {}
        self.knowledge_id_map = {}
        self.reverse_student_map = {}
        self.reverse_question_map = {}
        self.reverse_knowledge_map = {}
    
    def prepare_data(self):
        """从数据库准备训练数据"""
        # 注意：需要在Flask应用上下文中调用
        # 获取课程的所有学生、题目、知识点
        records = QuestionRecord.query.join(Question).filter(
            Question.course_id == self.course_id
        ).all()
        
        if len(records) < 10:
            raise ValueError(f"数据量太少（{len(records)}条），至少需要10条记录才能训练")
        
        # 收集所有唯一的学生、题目、知识点ID
        student_ids = set()
        question_ids = set()
        knowledge_ids = set()
        
        data_records = []
        for record in records:
            question = Question.query.get(record.question_id)
            if question:
                student_ids.add(record.student_id)
                question_ids.add(record.question_id)
                knowledge_ids.add(question.knowledge_id)
                data_records.append((
                    record.student_id,
                    record.question_id,
                    question.knowledge_id,
                    record.is_correct
                ))
        
        # 创建ID到索引的映射
        self.student_id_map = {sid: idx for idx, sid in enumerate(sorted(student_ids))}
        self.question_id_map = {qid: idx for idx, qid in enumerate(sorted(question_ids))}
        self.knowledge_id_map = {kid: idx for idx, kid in enumerate(sorted(knowledge_ids))}
        
        # 反向映射（索引到ID）
        self.reverse_student_map = {v: k for k, v in self.student_id_map.items()}
        self.reverse_question_map = {v: k for k, v in self.question_id_map.items()}
        self.reverse_knowledge_map = {v: k for k, v in self.knowledge_id_map.items()}
        
        logger.info(f"数据准备完成：{len(student_ids)}个学生，{len(question_ids)}道题目，{len(knowledge_ids)}个知识点，{len(data_records)}条记录")
        
        return data_records
    
    def create_model(self):
        """创建NCDM模型"""
        knowledge_n = len(self.knowledge_id_map)
        exer_n = len(self.question_id_map)
        student_n = len(self.student_id_map)
        
        self.model = NCDMNet(knowledge_n, exer_n, student_n)
        self.model.to(self.device)
        
        logger.info(f"模型创建完成：知识点={knowledge_n}, 题目={exer_n}, 学生={student_n}")
        
        return self.model
    
    def train(self, epochs=20, batch_size=32, lr=0.002, train_ratio=0.8, progress_callback=None):
        """
        训练模型
        
        Args:
            epochs: 训练轮数
            batch_size: 批次大小
            lr: 学习率
            train_ratio: 训练集比例
            progress_callback: 进度回调函数，接收(epoch, total_epochs, loss, metrics)参数
        """
        from app import app
        with app.app_context():
            # 准备数据
            data_records = self.prepare_data()
        
        # 创建模型
        if self.model is None:
            self.create_model()
        
        # 划分训练集和测试集
        train_records, test_records = train_test_split(
            data_records, 
            test_size=1-train_ratio, 
            random_state=42
        )
        
        # 创建数据集和数据加载器
        knowledge_dim = len(self.knowledge_id_map)
        train_dataset = NCDMDataset(
            train_records, 
            self.student_id_map, 
            self.question_id_map, 
            self.knowledge_id_map,
            knowledge_dim
        )
        test_dataset = NCDMDataset(
            test_records,
            self.student_id_map,
            self.question_id_map,
            self.knowledge_id_map,
            knowledge_dim
        )
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
        
        # 训练设置
        self.model.train()
        criterion = nn.BCELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=lr)
        
        best_auc = 0.0
        best_epoch = 0
        
        logger.info(f"开始训练，训练集：{len(train_records)}条，测试集：{len(test_records)}条")
        
        # 发送训练开始消息
        if progress_callback:
            progress_callback({
                'type': 'start',
                'message': '开始训练模型',
                'total_epochs': epochs,
                'train_size': len(train_records),
                'test_size': len(test_records)
            })
        
        for epoch in range(epochs):
            # 训练阶段
            epoch_losses = []
            total_batches = len(train_loader)
            
            for batch_idx, batch in enumerate(train_loader):
                user_id, item_id, knowledge_emb, y = batch
                user_id = user_id.squeeze(1).to(self.device)  # [batch, 1] -> [batch]
                item_id = item_id.squeeze(1).to(self.device)  # [batch, 1] -> [batch]
                knowledge_emb = knowledge_emb.to(self.device)  # [batch, knowledge_dim]
                y = y.squeeze(1).to(self.device)  # [batch, 1] -> [batch]
                
                pred = self.model(user_id, item_id, knowledge_emb)
                loss = criterion(pred, y)
                
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                epoch_losses.append(loss.item())
                
                # 每10个batch发送一次进度
                if progress_callback and batch_idx % 10 == 0:
                    progress_callback({
                        'type': 'training',
                        'epoch': epoch + 1,
                        'total_epochs': epochs,
                        'batch': batch_idx + 1,
                        'total_batches': total_batches,
                        'progress': int((batch_idx + 1) / total_batches * 100)
                    })
            
            avg_loss = np.mean(epoch_losses)
            logger.info(f"[Epoch {epoch+1}/{epochs}] 平均损失: {avg_loss:.6f}")
            
            # 评估阶段
            if test_loader:
                auc, accuracy, rmse, f1 = self.evaluate(test_loader)
                logger.info(f"[Epoch {epoch+1}/{epochs}] AUC: {auc:.6f}, 准确率: {accuracy:.6f}, RMSE: {rmse:.6f}, F1: {f1:.6f}")
                
                if auc > best_auc:
                    best_auc = auc
                    best_acc = accuracy
                    best_rmse = rmse
                    best_epoch = epoch + 1
                
                # 发送epoch完成消息
                if progress_callback:
                    progress_callback({
                        'type': 'epoch',
                        'epoch': epoch + 1,
                        'total_epochs': epochs,
                        'loss': float(avg_loss),
                        'auc': float(auc),
                        'accuracy': float(accuracy),
                        'rmse': float(rmse),
                        'f1': float(f1),
                        'best_epoch': best_epoch,
                        'best_auc': float(best_auc),
                        'best_acc': float(best_acc),
                        'best_rmse': float(best_rmse),
                        'progress': int((epoch + 1) / epochs * 100)
                    })
        
        logger.info(f"训练完成！最佳Epoch: {best_epoch}, 最佳AUC: {best_auc:.6f}, 最佳ACC: {best_acc:.6f}, 最佳RMSE: {best_rmse:.6f}")
        
        # 发送保存模型消息
        if progress_callback:
            progress_callback({
                'type': 'saving',
                'message': '正在保存模型...'
            })
        
        # 保存模型（使用绝对路径，基于backend目录）
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        models_dir = os.path.join(base_dir, "models")
        os.makedirs(models_dir, exist_ok=True)
        model_path = os.path.join(models_dir, f"ncdm_course_{self.course_id}.pth")
        self.save_model(model_path)
        
        # 发送训练完成消息
        if progress_callback:
            progress_callback({
                'type': 'complete',
                'message': '模型训练完成',
                'best_epoch': best_epoch,
                'best_auc': float(best_auc),
                'best_acc': float(best_acc),
                'best_rmse': float(best_rmse),
                'model_path': model_path
            })
        
        return best_epoch, best_auc, best_acc, best_rmse
    
    def train_stream(self, epochs=20, batch_size=32, lr=0.002, train_ratio=0.8):
        """
        训练模型（流式版本，返回生成器）
        
        Args:
            epochs: 训练轮数
            batch_size: 批次大小
            lr: 学习率
            train_ratio: 训练集比例
            
        Yields:
            SSE格式的消息字符串
        """
        from app import app
        import json
        
        with app.app_context():
            # 准备数据
            data_records = self.prepare_data()
        
        # 创建模型
        if self.model is None:
            self.create_model()
        
        # 划分训练集和测试集
        train_records, test_records = train_test_split(
            data_records, 
            test_size=1-train_ratio, 
            random_state=42
        )
        
        # 创建数据集和数据加载器
        knowledge_dim = len(self.knowledge_id_map)
        train_dataset = NCDMDataset(
            train_records, 
            self.student_id_map, 
            self.question_id_map, 
            self.knowledge_id_map,
            knowledge_dim
        )
        test_dataset = NCDMDataset(
            test_records,
            self.student_id_map,
            self.question_id_map,
            self.knowledge_id_map,
            knowledge_dim
        )
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
        
        # 发送训练开始消息
        yield f"data: {json.dumps({'type': 'start', 'message': '🚀 开始训练模型', 'total_epochs': epochs, 'train_size': len(train_records), 'test_size': len(test_records)}, ensure_ascii=False)}\n\n"
        
        # 训练设置
        self.model.train()
        criterion = nn.BCELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=lr)
        
        best_auc = 0.0
        best_acc = 0.0
        best_rmse = float('inf')
        best_epoch = 0
        
        logger.info(f"开始训练，训练集：{len(train_records)}条，测试集：{len(test_records)}条")
        
        for epoch in range(epochs):
            # 训练阶段
            epoch_losses = []
            total_batches = len(train_loader)
            
            yield f"data: {json.dumps({'type': 'epoch_start', 'epoch': epoch + 1, 'total_epochs': epochs, 'message': f'📊 开始第 {epoch + 1}/{epochs} 轮训练'}, ensure_ascii=False)}\n\n"
            
            for batch_idx, batch in enumerate(train_loader):
                user_id, item_id, knowledge_emb, y = batch
                user_id = user_id.squeeze(1).to(self.device)  # [batch, 1] -> [batch]
                item_id = item_id.squeeze(1).to(self.device)  # [batch, 1] -> [batch]
                knowledge_emb = knowledge_emb.to(self.device)  # [batch, knowledge_dim]
                y = y.squeeze(1).to(self.device)  # [batch, 1] -> [batch]
                
                pred = self.model(user_id, item_id, knowledge_emb)
                loss = criterion(pred, y)
                
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                epoch_losses.append(loss.item())
                
                # 每10个batch发送一次进度
                if batch_idx % 10 == 0 or batch_idx == total_batches - 1:
                    batch_progress = int((batch_idx + 1) / total_batches * 100)
                    yield f"data: {json.dumps({'type': 'training', 'epoch': epoch + 1, 'total_epochs': epochs, 'batch': batch_idx + 1, 'total_batches': total_batches, 'progress': batch_progress, 'message': f'训练中... ({batch_idx + 1}/{total_batches})'}, ensure_ascii=False)}\n\n"
            
            avg_loss = np.mean(epoch_losses)
            logger.info(f"[Epoch {epoch+1}/{epochs}] 平均损失: {avg_loss:.6f}")
            
            # 评估阶段
            if test_loader:
                yield f"data: {json.dumps({'type': 'evaluating', 'epoch': epoch + 1, 'message': '📈 正在评估模型...'}, ensure_ascii=False)}\n\n"
                
                auc, accuracy, rmse, f1 = self.evaluate(test_loader)
                logger.info(f"[Epoch {epoch+1}/{epochs}] AUC: {auc:.6f}, 准确率: {accuracy:.6f}, RMSE: {rmse:.6f}, F1: {f1:.6f}")
                
                if auc > best_auc:
                    best_auc = auc
                    best_acc = accuracy
                    best_rmse = rmse
                    best_epoch = epoch + 1
                
                # 发送epoch完成消息
                epoch_progress = int((epoch + 1) / epochs * 100)
                yield f"data: {json.dumps({'type': 'epoch', 'epoch': epoch + 1, 'total_epochs': epochs, 'loss': float(avg_loss), 'auc': float(auc), 'accuracy': float(accuracy), 'rmse': float(rmse), 'f1': float(f1), 'best_epoch': best_epoch, 'best_auc': float(best_auc), 'best_acc': float(best_acc), 'best_rmse': float(best_rmse), 'progress': epoch_progress, 'message': f'✅ 第 {epoch + 1} 轮完成 - AUC: {auc:.4f}, 准确率: {accuracy:.2%}'}, ensure_ascii=False)}\n\n"
        
        logger.info(f"训练完成！最佳Epoch: {best_epoch}, 最佳AUC: {best_auc:.6f}, 最佳ACC: {best_acc:.6f}, 最佳RMSE: {best_rmse:.6f}")
        
        # 发送保存模型消息
        yield f"data: {json.dumps({'type': 'saving', 'message': '💾 正在保存模型...'}, ensure_ascii=False)}\n\n"
        
        # 保存模型
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        models_dir = os.path.join(base_dir, "models")
        os.makedirs(models_dir, exist_ok=True)
        model_path = os.path.join(models_dir, f"ncdm_course_{self.course_id}.pth")
        self.save_model(model_path)
        
        # 发送训练完成消息
        yield f"data: {json.dumps({'type': 'complete', 'message': '🎉 模型训练完成！', 'best_epoch': best_epoch, 'best_auc': float(best_auc), 'best_acc': float(best_acc), 'best_rmse': float(best_rmse), 'model_path': model_path, 'success': True}, ensure_ascii=False)}\n\n"
    
    def evaluate(self, test_loader):
        """评估模型"""
        self.model.eval()
        y_true, y_pred = [], []
        
        with torch.no_grad():
            for batch in test_loader:
                user_id, item_id, knowledge_emb, y = batch
                user_id = user_id.squeeze(1).to(self.device)  # [batch, 1] -> [batch]
                item_id = item_id.squeeze(1).to(self.device)  # [batch, 1] -> [batch]
                knowledge_emb = knowledge_emb.to(self.device)  # [batch, knowledge_dim]
                y = y.squeeze(1).to(self.device)  # [batch, 1] -> [batch]
                
                pred = self.model(user_id, item_id, knowledge_emb)
                y_pred.extend(pred.cpu().tolist())
                y_true.extend(y.cpu().tolist())
        
        y_true = np.array(y_true)
        y_pred = np.array(y_pred)
        
        # 计算指标
        auc = roc_auc_score(y_true, y_pred) if len(np.unique(y_true)) > 1 else 0.0
        accuracy = accuracy_score(y_true, y_pred >= 0.5)
        rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
        f1 = f1_score(y_true, y_pred >= 0.5)
        
        return auc, accuracy, rmse, f1
    
    def predict_student_mastery(self, student_id):
        """
        预测学生的知识点掌握度
        
        Args:
            student_id: 学生ID（数据库ID）
            
        Returns:
            dict: {knowledge_id: mastery_level, ...}
        """
        if self.model is None:
            raise ValueError("模型未训练，请先调用train()方法")
        
        self.model.eval()
        
        if student_id not in self.student_id_map:
            # 如果学生不在训练数据中，返回默认值
            from app import app
            with app.app_context():
                knowledges = Knowledge.query.filter_by(course_id=self.course_id).all()
                return {k.id: 0.0 for k in knowledges}
        
        student_idx = self.student_id_map[student_id]
        mastery_vector = self.model.get_student_mastery(student_idx, self.device)
        
        # 转换为知识点ID到掌握度的映射
        mastery_dict = {}
        for idx, mastery in enumerate(mastery_vector):
            if idx in self.reverse_knowledge_map:
                knowledge_id = self.reverse_knowledge_map[idx]
                mastery_dict[knowledge_id] = float(mastery * 100)  # 转换为百分比
        
        return mastery_dict
    
    def save_model(self, filepath):
        """保存模型和映射"""
        if self.model is None:
            raise ValueError("模型未训练")
        
        save_data = {
            'model_state_dict': self.model.state_dict(),
            'student_id_map': self.student_id_map,
            'question_id_map': self.question_id_map,
            'knowledge_id_map': self.knowledge_id_map,
            'reverse_student_map': self.reverse_student_map,
            'reverse_question_map': self.reverse_question_map,
            'reverse_knowledge_map': self.reverse_knowledge_map,
            'course_id': self.course_id
        }
        
        torch.save(save_data, filepath)
        logger.info(f"模型已保存到: {filepath}")
    
    def load_model(self, filepath):
        """加载模型和映射"""
        save_data = torch.load(filepath, map_location=self.device)
        
        self.student_id_map = save_data['student_id_map']
        self.question_id_map = save_data['question_id_map']
        self.knowledge_id_map = save_data['knowledge_id_map']
        self.reverse_student_map = save_data['reverse_student_map']
        self.reverse_question_map = save_data['reverse_question_map']
        self.reverse_knowledge_map = save_data['reverse_knowledge_map']
        self.course_id = save_data['course_id']
        
        # 创建模型
        knowledge_n = len(self.knowledge_id_map)
        exer_n = len(self.question_id_map)
        student_n = len(self.student_id_map)
        
        self.model = NCDMNet(knowledge_n, exer_n, student_n)
        self.model.load_state_dict(save_data['model_state_dict'])
        self.model.to(self.device)
        self.model.eval()
        
        logger.info(f"模型已从 {filepath} 加载")

