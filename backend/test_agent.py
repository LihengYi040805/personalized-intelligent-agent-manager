"""
测试LangChain Agent是否正常工作
"""
import os
from dotenv import load_dotenv

load_dotenv()

def test_agent_import():
    """测试Agent导入"""
    print("=" * 60)
    print("测试1：导入Agent模块")
    print("=" * 60)
    
    try:
        from services.question_generation_agent import QuestionGenerationAgent
        print("✅ Agent模块导入成功")
        return True
    except Exception as e:
        print(f"❌ Agent模块导入失败: {str(e)}")
        return False


def test_agent_initialization():
    """测试Agent初始化"""
    print("\n" + "=" * 60)
    print("测试2：初始化Agent")
    print("=" * 60)
    
    try:
        from services.question_generation_agent import QuestionGenerationAgent
        agent = QuestionGenerationAgent()
        print("✅ Agent初始化成功")
        print(f"   - LLM模型: {agent.llm.model_name}")
        print(f"   - 可用方法:")
        methods = [m for m in dir(agent) if not m.startswith('_') and callable(getattr(agent, m))]
        for method in methods[:5]:  # 只显示前5个
            print(f"     • {method}")
        return True
    except Exception as e:
        print(f"❌ Agent初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_simple_task():
    """测试简单任务"""
    print("\n" + "=" * 60)
    print("测试3：执行简单任务")
    print("=" * 60)
    
    try:
        from services.question_generation_agent import QuestionGenerationAgent
        agent = QuestionGenerationAgent()
        
        # 测试文档结构分析
        test_content = """
        C语言程序设计课程
        
        第一章：C语言基础
        1.1 变量与数据类型
        C语言支持多种数据类型，包括整型、浮点型、字符型等。
        
        1.2 运算符与表达式
        C语言提供了丰富的运算符，包括算术运算符、关系运算符等。
        """
        
        print("正在分析文档结构...")
        result = agent.analyze_document_structure(test_content)
        
        if 'error' in result:
            print(f"⚠️  分析返回错误: {result['error']}")
            return False
        
        print("✅ 文档结构分析成功")
        print(f"   课程名称: {result.get('course_name', '未知')}")
        print(f"   章节数量: {result.get('total_chapters', 0)}")
        return True
        
    except Exception as e:
        print(f"❌ 任务执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_v2_service():
    """测试V2服务"""
    print("\n" + "=" * 60)
    print("测试4：V2服务导入")
    print("=" * 60)
    
    try:
        from services.ai_generation_service_v2 import AIGenerationServiceV2
        service = AIGenerationServiceV2()
        print("✅ V2服务初始化成功")
        return True
    except Exception as e:
        print(f"❌ V2服务初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("LangChain Agent 测试")
    print("=" * 60)
    
    # 检查环境变量
    print("\n环境配置:")
    print(f"  ALI_API_KEY: {'已设置' if os.getenv('ALI_API_KEY') else '未设置'}")
    print(f"  API_BASE: {os.getenv('API_BASE', '未设置')}")
    print(f"  LLM_MODEL: {os.getenv('LLM_MODEL', '未设置')}")
    print(f"  USE_AGENT_V2: {os.getenv('USE_AGENT_V2', 'true')}")
    
    results = []
    
    # 运行测试
    results.append(("Agent导入", test_agent_import()))
    results.append(("Agent初始化", test_agent_initialization()))
    results.append(("简单任务执行", test_simple_task()))
    results.append(("V2服务", test_v2_service()))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！Agent系统可以正常使用。")
    else:
        print("\n⚠️  部分测试失败，请检查配置和依赖。")
        print("\n安装依赖命令:")
        print("  pip install langchain langchain-openai langchain-community")


if __name__ == '__main__':
    main()
