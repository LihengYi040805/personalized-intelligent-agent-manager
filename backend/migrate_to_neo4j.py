"""
将知识图谱从关系数据库迁移到Neo4j图数据库
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from dotenv import load_dotenv
from models import db, Course, Knowledge
from neo4j import GraphDatabase

load_dotenv()

app = Flask(__name__)

# 关系数据库配置
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME', 'aied_platform')
DB_PORT = os.getenv('DB_PORT', '3306')

if DB_HOST and DB_USER and DB_PASSWORD:
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///training.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Neo4j配置
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'password')


class Neo4jMigrator:
    """Neo4j迁移器"""
    
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def clear_database(self):
        """清空Neo4j数据库"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("✅ Neo4j数据库已清空")
    
    def get_existing_nodes(self):
        """获取Neo4j中已存在的节点ID"""
        with self.driver.session() as session:
            # 获取课程ID
            course_query = "MATCH (c:Course) RETURN c.id as id"
            course_result = session.run(course_query)
            course_ids = {record['id'] for record in course_result}
            
            # 获取知识点ID
            knowledge_query = "MATCH (k:Knowledge) RETURN k.id as id"
            knowledge_result = session.run(knowledge_query)
            knowledge_ids = {record['id'] for record in knowledge_result}
            
            return course_ids, knowledge_ids
    
    def upsert_course(self, course_id, course_name, description, total_hours):
        """创建或更新课程节点（MERGE操作）"""
        with self.driver.session() as session:
            query = """
            MERGE (c:Course:CourseNode {id: $course_id})
            SET c.name = $name,
                c.description = $description,
                c.total_hours = $total_hours,
                c.node_type = 'course',
                c.updated_at = datetime()
            RETURN c
            """
            session.run(query, 
                       course_id=course_id,
                       name=course_name,
                       description=description,
                       total_hours=total_hours)
    
    def upsert_knowledge(self, knowledge_id, course_id, name, description, level):
        """创建或更新知识点节点（MERGE操作）"""
        with self.driver.session() as session:
            # 根据层级添加不同的标签
            level_labels = {
                1: 'Level1:BasicKnowledge',
                2: 'Level2:IntermediateKnowledge',
                3: 'Level3:AdvancedKnowledge',
                4: 'Level4:ExpertKnowledge'
            }
            level_label = level_labels.get(level, 'Level1:BasicKnowledge')
            
            # 先删除旧的层级标签，再添加新标签
            query = f"""
            MERGE (k:Knowledge {{id: $knowledge_id}})
            REMOVE k:Level1:Level2:Level3:Level4:BasicKnowledge:IntermediateKnowledge:AdvancedKnowledge:ExpertKnowledge
            SET k:{level_label}
            SET k.course_id = $course_id,
                k.name = $name,
                k.description = $description,
                k.level = $level,
                k.node_type = 'knowledge',
                k.updated_at = datetime()
            RETURN k
            """
            session.run(query,
                       knowledge_id=knowledge_id,
                       course_id=course_id,
                       name=name,
                       description=description or '',
                       level=level)
    
    def delete_course(self, course_id):
        """删除课程节点及其所有关系"""
        with self.driver.session() as session:
            query = """
            MATCH (c:Course {id: $course_id})
            DETACH DELETE c
            """
            session.run(query, course_id=course_id)
    
    def delete_knowledge(self, knowledge_id):
        """删除知识点节点及其所有关系"""
        with self.driver.session() as session:
            query = """
            MATCH (k:Knowledge {id: $knowledge_id})
            DETACH DELETE k
            """
            session.run(query, knowledge_id=knowledge_id)
    
    def sync_course_knowledge_relationship(self, course_id, knowledge_ids):
        """同步课程-知识点关系"""
        with self.driver.session() as session:
            # 先删除该课程的所有HAS_KNOWLEDGE关系
            delete_query = """
            MATCH (c:Course {id: $course_id})-[r:HAS_KNOWLEDGE]->()
            DELETE r
            """
            session.run(delete_query, course_id=course_id)
            
            # 重新创建关系
            for knowledge_id in knowledge_ids:
                create_query = """
                MATCH (c:Course {id: $course_id})
                MATCH (k:Knowledge {id: $knowledge_id})
                MERGE (c)-[:HAS_KNOWLEDGE]->(k)
                """
                session.run(create_query, course_id=course_id, knowledge_id=knowledge_id)
    
    def sync_knowledge_prerequisites(self, knowledge_id, prerequisite_ids):
        """同步知识点的前置关系"""
        with self.driver.session() as session:
            # 先删除该知识点的所有前置关系（作为目标）
            delete_query = """
            MATCH ()-[r:PREREQUISITE_OF]->(k:Knowledge {id: $knowledge_id})
            DELETE r
            """
            session.run(delete_query, knowledge_id=knowledge_id)
            
            # 重新创建前置关系
            for pre_id in prerequisite_ids:
                create_query = """
                MATCH (k1:Knowledge {id: $pre_id})
                MATCH (k2:Knowledge {id: $knowledge_id})
                MERGE (k1)-[:PREREQUISITE_OF]->(k2)
                """
                session.run(create_query, pre_id=pre_id, knowledge_id=knowledge_id)
    
    def get_knowledge_graph(self, course_id):
        """获取课程的知识图谱"""
        with self.driver.session() as session:
            # 获取知识点节点
            nodes_query = """
            MATCH (k:Knowledge {course_id: $course_id})
            RETURN k.id as id, k.name as name, k.description as description, k.level as level
            """
            nodes_result = session.run(nodes_query, course_id=course_id)
            nodes = [dict(record) for record in nodes_result]
            
            # 获取关系
            edges_query = """
            MATCH (k1:Knowledge {course_id: $course_id})-[:PREREQUISITE_OF]->(k2:Knowledge {course_id: $course_id})
            RETURN k1.id as source, k2.id as target
            """
            edges_result = session.run(edges_query, course_id=course_id)
            edges = [dict(record) for record in edges_result]
            
            return {'nodes': nodes, 'edges': edges}


def migrate_to_neo4j(full_sync=False):
    """
    执行迁移/同步
    
    Args:
        full_sync: 是否完全同步（清空后重建），默认False为增量同步
    """
    print("\n" + "=" * 60)
    if full_sync:
        print("完全同步：清空Neo4j并重新导入所有数据")
    else:
        print("增量同步：只更新变化的数据")
    print("=" * 60 + "\n")
    
    # 连接Neo4j
    try:
        migrator = Neo4jMigrator(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        print(f"✅ 成功连接到Neo4j: {NEO4J_URI}\n")
    except Exception as e:
        print(f"❌ 无法连接到Neo4j: {e}")
        print("\n请确保：")
        print("1. Neo4j已安装并运行")
        print("2. 在.env文件中配置了正确的Neo4j连接信息：")
        print("   NEO4J_URI=bolt://localhost:7687")
        print("   NEO4J_USER=neo4j")
        print("   NEO4J_PASSWORD=your_password")
        return
    
    try:
        # 如果是完全同步，清空数据库
        if full_sync:
            print("清空Neo4j数据库...")
            migrator.clear_database()
            print()
            existing_course_ids = set()
            existing_knowledge_ids = set()
        else:
            # 获取Neo4j中已存在的节点
            print("📊 检查Neo4j中的现有数据...")
            existing_course_ids, existing_knowledge_ids = migrator.get_existing_nodes()
            print(f"   现有课程: {len(existing_course_ids)} 个")
            print(f"   现有知识点: {len(existing_knowledge_ids)} 个\n")
        
        with app.app_context():
            # 获取所有课程
            courses = Course.query.all()
            print(f"📚 关系数据库中有 {len(courses)} 个课程\n")
            
            current_course_ids = set()
            current_knowledge_ids = set()
            
            for course in courses:
                current_course_ids.add(course.id)
                
                print(f"📚 处理课程: {course.name}")
                print("-" * 60)
                
                # 创建或更新课程节点
                if course.id in existing_course_ids:
                    print(f"  🔄 更新课程节点")
                else:
                    print(f"  ➕ 创建课程节点")
                
                migrator.upsert_course(
                    course.id,
                    course.name,
                    course.description or '',
                    course.total_hours or 0
                )
                
                # 获取该课程的所有知识点
                knowledges = Knowledge.query.filter_by(course_id=course.id).all()
                print(f"  找到 {len(knowledges)} 个知识点")
                
                # 创建或更新知识点节点
                course_knowledge_ids = []
                for knowledge in knowledges:
                    current_knowledge_ids.add(knowledge.id)
                    course_knowledge_ids.append(knowledge.id)
                    
                    if knowledge.id in existing_knowledge_ids:
                        action = "🔄 更新"
                    else:
                        action = "➕ 新增"
                    
                    migrator.upsert_knowledge(
                        knowledge.id,
                        knowledge.course_id,
                        knowledge.name,
                        knowledge.description,
                        knowledge.level
                    )
                    print(f"    {action}: {knowledge.name} (Level {knowledge.level})")
                
                # 同步课程-知识点关系
                migrator.sync_course_knowledge_relationship(course.id, course_knowledge_ids)
                
                # 同步知识点之间的前置关系
                relationship_count = 0
                for knowledge in knowledges:
                    if knowledge.prerequisites:
                        try:
                            prerequisites = json.loads(knowledge.prerequisites)
                            if isinstance(prerequisites, list):
                                prerequisite_ids = [int(p) for p in prerequisites if int(p) in current_knowledge_ids]
                                migrator.sync_knowledge_prerequisites(knowledge.id, prerequisite_ids)
                                relationship_count += len(prerequisite_ids)
                        except (json.JSONDecodeError, ValueError) as e:
                            print(f"    ⚠️  解析前置关系失败: {knowledge.name}")
                
                print(f"  ✅ 同步了 {relationship_count} 个前置关系")
                print()
            
            # 删除已不存在的节点（仅增量同步时）
            if not full_sync:
                deleted_courses = existing_course_ids - current_course_ids
                deleted_knowledges = existing_knowledge_ids - current_knowledge_ids
                
                if deleted_courses:
                    print("🗑️  删除已不存在的课程:")
                    for course_id in deleted_courses:
                        migrator.delete_course(course_id)
                        print(f"  ➖ 删除课程 ID={course_id}")
                
                if deleted_knowledges:
                    print("\n🗑️  删除已不存在的知识点:")
                    for knowledge_id in deleted_knowledges:
                        migrator.delete_knowledge(knowledge_id)
                        print(f"  ➖ 删除知识点 ID={knowledge_id}")
                
                if deleted_courses or deleted_knowledges:
                    print()
            
            print("=" * 60)
            print("✅ 同步完成！")
            print("=" * 60)
            print("\n📊 同步统计：")
            print(f"   课程: {len(current_course_ids)} 个")
            print(f"   知识点: {len(current_knowledge_ids)} 个")
            
            if not full_sync:
                print(f"   删除课程: {len(existing_course_ids - current_course_ids)} 个")
                print(f"   删除知识点: {len(existing_knowledge_ids - current_knowledge_ids)} 个")
            
            print("\n" + "=" * 60)
            print("🎨 Neo4j Browser 样式配置")
            print("=" * 60)
            print("\n在Neo4j Browser中，点击左下角的 ⚙️ 图标，然后粘贴以下样式配置：\n")
            print("""
// 课程节点 - 深蓝色
node.CourseNode {
  color: #2E5EAA;
  border-color: #1E3A8A;
  text-color-internal: #FFFFFF;
  caption: '{name}';
  diameter: 80px;
}

// 层级1 - 基础知识 - 绿色
node.Level1 {
  color: #10B981;
  border-color: #059669;
  text-color-internal: #FFFFFF;
  caption: '{name}';
  diameter: 60px;
}

// 层级2 - 进阶知识 - 蓝色
node.Level2 {
  color: #3B82F6;
  border-color: #2563EB;
  text-color-internal: #FFFFFF;
  caption: '{name}';
  diameter: 60px;
}

// 层级3 - 高级知识 - 橙色
node.Level3 {
  color: #F59E0B;
  border-color: #D97706;
  text-color-internal: #FFFFFF;
  caption: '{name}';
  diameter: 60px;
}

// 层级4 - 专家知识 - 红色
node.Level4 {
  color: #EF4444;
  border-color: #DC2626;
  text-color-internal: #FFFFFF;
  caption: '{name}';
  diameter: 60px;
}

// 关系样式
relationship {
  color: #A5B4FC;
  shaft-width: 2px;
  font-size: 10px;
  padding: 3px;
  text-color-external: #6B7280;
  text-color-internal: #FFFFFF;
  caption: '{type}';
}
            """)
            print("\n或者运行以下Cypher查询来查看彩色图谱：")
            print("\nMATCH (n) RETURN n LIMIT 50")
            print("=" * 60)
    
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        migrator.close()


if __name__ == '__main__':
    import sys
    
    # 检查命令行参数
    full_sync = '--full' in sys.argv or '-f' in sys.argv
    
    if full_sync:
        print("\n⚠️  警告：将清空Neo4j数据库并重新导入所有数据")
        confirm = input("确认继续？(yes/no): ")
        if confirm.lower() != 'yes':
            print("已取消操作")
            sys.exit(0)
    
    migrate_to_neo4j(full_sync=full_sync)
