"""简单的导入测试"""
import sys
import os

# 清除缓存
if 'services.question_generation_agent' in sys.modules:
    del sys.modules['services.question_generation_agent']

# 重新导入
try:
    from services.question_generation_agent import QuestionGenerationAgent
    print("✅ 导入成功")
    
    # 尝试初始化
    agent = QuestionGenerationAgent()
    print("✅ 初始化成功")
    
except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback
    traceback.print_exc()
