"""
自动配置Neo4j Browser的节点样式
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'password')


def configure_styles():
    """配置Neo4j样式"""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    print("=" * 60)
    print("🎨 配置Neo4j Browser样式")
    print("=" * 60)
    
    # Neo4j Browser的样式是存储在浏览器本地的，无法通过Cypher直接设置
    # 但我们可以提供样式配置代码
    
    print("\n请按照以下步骤配置样式：\n")
    print("1. 打开Neo4j Browser: http://localhost:7474")
    print("2. 点击左下角的 ⚙️ (设置) 图标")
    print("3. 找到 'Graph Stylesheet' 部分")
    print("4. 将以下样式代码粘贴进去：\n")
    
    styles = """
node {
  diameter: 50px;
  color: #A5ABB6;
  border-color: #9AA1AC;
  border-width: 2px;
  text-color-internal: #FFFFFF;
  font-size: 10px;
}

/* 课程节点 - 深蓝色 */
node.CourseNode {
  color: #2E5EAA;
  border-color: #1E3A8A;
  text-color-internal: #FFFFFF;
  caption: '{name}';
  diameter: 80px;
  font-size: 12px;
}

/* 层级1 - 基础知识 - 绿色 */
node.Level1 {
  color: #10B981;
  border-color: #059669;
  text-color-internal: #FFFFFF;
  caption: '{name}';
  diameter: 60px;
}

/* 层级2 - 进阶知识 - 蓝色 */
node.Level2 {
  color: #3B82F6;
  border-color: #2563EB;
  text-color-internal: #FFFFFF;
  caption: '{name}';
  diameter: 60px;
}

/* 层级3 - 高级知识 - 橙色 */
node.Level3 {
  color: #F59E0B;
  border-color: #D97706;
  text-color-internal: #FFFFFF;
  caption: '{name}';
  diameter: 60px;
}

/* 层级4 - 专家知识 - 红色 */
node.Level4 {
  color: #EF4444;
  border-color: #DC2626;
  text-color-internal: #FFFFFF;
  caption: '{name}';
  diameter: 60px;
}

relationship {
  color: #A5B4FC;
  shaft-width: 2px;
  font-size: 10px;
  padding: 3px;
  text-color-external: #6B7280;
  text-color-internal: #FFFFFF;
  caption: '{type}';
}

relationship.PREREQUISITE_OF {
  color: #818CF8;
  shaft-width: 3px;
  caption: '前置';
}

relationship.HAS_KNOWLEDGE {
  color: #60A5FA;
  shaft-width: 2px;
  caption: '包含';
}
"""
    
    print(styles)
    print("\n5. 点击 'Apply' 按钮")
    print("6. 运行查询查看效果：")
    print("\n   MATCH (n) RETURN n LIMIT 50")
    print("\n   或者：")
    print("\n   MATCH (c:Course)-[:HAS_KNOWLEDGE]->(k:Knowledge)")
    print("   RETURN c, k LIMIT 25")
    print("\n" + "=" * 60)
    print("\n颜色说明：")
    print("  🔵 深蓝色 - 课程节点")
    print("  🟢 绿色   - 层级1（基础知识）")
    print("  🔵 蓝色   - 层级2（进阶知识）")
    print("  🟠 橙色   - 层级3（高级知识）")
    print("  🔴 红色   - 层级4（专家知识）")
    print("=" * 60)
    
    # 保存样式到文件
    with open('neo4j_styles.grass', 'w', encoding='utf-8') as f:
        f.write(styles)
    
    print("\n✅ 样式配置已保存到 neo4j_styles.grass 文件")
    print("   你也可以在Neo4j Browser中导入这个文件")
    
    driver.close()


if __name__ == '__main__':
    configure_styles()
