"""
NCDM (Neural Cognitive Diagnosis Model) 神经网络模型
适配本系统的NCDM实现

NCDM核心原理：
================

1. 模型目标：
   预测学生在某道题目上的答对概率 P(y=1|student, question)

2. 核心公式：
   input_x = e_difficulty * (stat_emb - k_difficulty) * input_knowledge_point
   P(y=1) = σ(MLP(input_x))
   
   其中：
   - stat_emb: 学生在各知识点上的掌握程度 (0~1)
   - k_difficulty: 题目在各知识点上的难度 (0~1)
   - e_difficulty: 题目整体难度系数 (0~2)
   - input_knowledge_point: Q矩阵，标记题目涉及哪些知识点 (0或1)
   - MLP: 多层感知机，学习知识点的区分度和交互
   - σ: sigmoid函数，输出概率

3. 计算逻辑：
   步骤1: stat_emb - k_difficulty
          → 学生能力与题目难度的差值
          → 正值表示学生能力高于题目难度
   
   步骤2: 乘以 input_knowledge_point
          → 只保留题目相关知识点的差值
   
   步骤3: 乘以 e_difficulty
          → 用题目整体难度系数加权
          → e_difficulty范围(0~2)，可以放大或缩小差值
   
   步骤4: 通过MLP网络
          → 学习知识点之间的交互和区分度
          → 输出最终的答对概率

4. 模型结构：
   输入层: e * (θ - d) ⊙ Q  [K维]
   隐藏层1: 512维 + Dropout(0.5) + Sigmoid
   隐藏层2: 256维 + Dropout(0.5) + Sigmoid  
   输出层: 1维 + Sigmoid → 答对概率

5. 关键特性：
   - 使用PosLinear确保权重为正（符合认知诊断的单调性假设）
   - Dropout防止过拟合
   - 学生掌握度和题目难度都通过Embedding学习
   - e_difficulty作为整体难度系数，范围(0~2)
   - MLP自动学习知识点之间的交互和区分度

6. 与IRT的区别：
   - IRT: 线性模型，假设知识点独立
   - NCDM: 神经网络，可以捕捉知识点之间的复杂交互
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PosLinear(nn.Linear):
    """正权重线性层（确保权重为正）"""
    
    def forward(self, input: torch.Tensor) -> torch.Tensor:
        weight = 2 * F.relu(1 * torch.neg(self.weight)) + self.weight
        return F.linear(input, weight, self.bias)


class NCDMNet(nn.Module):
    """NCDM神经网络模型"""
    
    def __init__(self, knowledge_n, exer_n, student_n):
        """
        初始化NCDM网络
        
        Args:
            knowledge_n: 知识点数量
            exer_n: 题目数量
            student_n: 学生数量
        """
        self.knowledge_dim = knowledge_n
        self.exer_n = exer_n
        self.emb_num = student_n
        self.stu_dim = self.knowledge_dim
        self.prednet_input_len = self.knowledge_dim
        self.prednet_len1, self.prednet_len2 = 512, 256  # 可调整的网络层大小
        
        super(NCDMNet, self).__init__()
        
        # 预测子网络
        # 学生嵌入层：将学生ID映射到知识点维度的向量
        self.student_emb = nn.Embedding(self.emb_num, self.stu_dim)
        
        # 知识点难度嵌入：每个题目对应每个知识点的难度
        self.k_difficulty = nn.Embedding(self.exer_n, self.knowledge_dim)
        
        # 题目整体难度嵌入
        self.e_difficulty = nn.Embedding(self.exer_n, 1)
        
        # 预测网络（使用正权重线性层）
        self.prednet_full1 = PosLinear(self.prednet_input_len, self.prednet_len1)
        self.drop_1 = nn.Dropout(p=0.5)
        self.prednet_full2 = PosLinear(self.prednet_len1, self.prednet_len2)
        self.drop_2 = nn.Dropout(p=0.5)
        self.prednet_full3 = PosLinear(self.prednet_len2, 1)
        
        # 初始化权重
        for name, param in self.named_parameters():
            if 'weight' in name:
                nn.init.xavier_normal_(param)
    
    def forward(self, stu_id, input_exercise, input_knowledge_point):
        """
        前向传播 - 实现NCDM核心公式
        
        NCDM正确公式：
        input_x = e_difficulty * (stat_emb - k_difficulty) * input_knowledge_point
        
        各变量含义：
        - stat_emb: 学生在各知识点上的掌握程度 (0~1)
        - k_difficulty: 题目在各知识点上的难度 (0~1)
        - e_difficulty: 题目整体难度系数 (0~2)
        - input_knowledge_point: Q矩阵，标记题目涉及哪些知识点 (0或1)
        
        计算逻辑：
        1. stat_emb - k_difficulty: 学生能力与题目难度的差值，正值表示学生能力高于题目难度
        2. 乘以 input_knowledge_point: 只保留题目相关知识点的差值
        3. 乘以 e_difficulty: 用题目整体难度加权
        4. 最后通过 MLP 网络输出最终的正确概率
        
        Args:
            stu_id: 学生ID张量 [batch_size]
            input_exercise: 题目ID张量 [batch_size]
            input_knowledge_point: 知识点向量 [batch_size, knowledge_dim] (one-hot或multi-hot)
            
        Returns:
            答对概率 [batch_size]
        """
        # 1. 获取学生掌握度向量 stat_emb (0~1)
        stu_emb = self.student_emb(stu_id)
        stat_emb = torch.sigmoid(stu_emb)  # [batch_size, knowledge_dim]
        
        # 2. 获取题目的知识点难度 k_difficulty (0~1)
        k_difficulty = torch.sigmoid(self.k_difficulty(input_exercise))  # [batch_size, knowledge_dim]
        
        # 3. 获取题目的整体难度系数 e_difficulty (0~2)
        e_difficulty = torch.sigmoid(self.e_difficulty(input_exercise)) * 2  # [batch_size, 1]
        
        # 4. 计算输入特征：e_difficulty * (stat_emb - k_difficulty) * input_knowledge_point
        # 这是NCDM的核心公式
        input_x = e_difficulty * (stat_emb - k_difficulty) * input_knowledge_point  # [batch_size, knowledge_dim]
        
        # 5. 通过多层感知机（MLP）进行非线性变换
        input_x = self.drop_1(torch.sigmoid(self.prednet_full1(input_x)))
        input_x = self.drop_2(torch.sigmoid(self.prednet_full2(input_x)))
        output_1 = torch.sigmoid(self.prednet_full3(input_x))
        
        return output_1.view(-1)
    
    def get_student_mastery(self, stu_id, device="cpu"):
        """
        获取学生的知识点掌握度向量
        
        Args:
            stu_id: 学生ID索引
            device: 设备
            
        Returns:
            掌握度向量 [knowledge_dim]
        """
        self.to(device)
        self.eval()
        with torch.no_grad():
            stu_emb = self.student_emb(torch.LongTensor([stu_id]).to(device))
            stat_emb = torch.sigmoid(stu_emb)
            return stat_emb.cpu().numpy()[0]
    
    def get_question_difficulty(self, exer_id, device="cpu"):
        """
        获取题目的知识点难度向量
        
        Args:
            exer_id: 题目ID索引
            device: 设备
            
        Returns:
            难度向量 [knowledge_dim]
        """
        self.to(device)
        self.eval()
        with torch.no_grad():
            k_difficulty = torch.sigmoid(self.k_difficulty(torch.LongTensor([exer_id]).to(device)))
            return k_difficulty.cpu().numpy()[0]

