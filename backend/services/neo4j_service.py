"""
Neo4j图数据库服务
用于查询和操作知识图谱
"""
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()


class Neo4jService:
    """Neo4j服务类"""
    
    def __init__(self):
        self.uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.user = os.getenv('NEO4J_USER', 'neo4j')
        self.password = os.getenv('NEO4J_PASSWORD', 'password')
        self.driver = None
    
    def connect(self):
        """连接到Neo4j"""
        if not self.driver:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        return self.driver
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
            self.driver = None
    
    def get_knowledge_graph(self, course_id):
        """
        获取课程的知识图谱
        
        Args:
            course_id: 课程ID
            
        Returns:
            dict: {'nodes': [...], 'edges': [...]}
        """
        driver = self.connect()
        
        with driver.session() as session:
            # 获取知识点节点
            nodes_query = """
            MATCH (k:Knowledge {course_id: $course_id})
            RETURN k.id as id, k.name as name, k.description as description, k.level as level
            ORDER BY k.level, k.id
            """
            nodes_result = session.run(nodes_query, course_id=course_id)
            nodes = []
            for record in nodes_result:
                nodes.append({
                    'id': str(record['id']),
                    'name': record['name'],
                    'description': record['description'],
                    'level': record['level']
                })
            
            # 获取前置关系
            edges_query = """
            MATCH (k1:Knowledge {course_id: $course_id})-[:PREREQUISITE_OF]->(k2:Knowledge {course_id: $course_id})
            RETURN k1.id as source, k2.id as target
            """
            edges_result = session.run(edges_query, course_id=course_id)
            edges = []
            for record in edges_result:
                edges.append({
                    'source': str(record['source']),
                    'target': str(record['target'])
                })
            
            return {'nodes': nodes, 'edges': edges}
    
    def get_knowledge_prerequisites(self, knowledge_id):
        """
        获取知识点的所有前置知识点
        
        Args:
            knowledge_id: 知识点ID
            
        Returns:
            list: 前置知识点列表
        """
        driver = self.connect()
        
        with driver.session() as session:
            query = """
            MATCH (k1:Knowledge)-[:PREREQUISITE_OF]->(k2:Knowledge {id: $knowledge_id})
            RETURN k1.id as id, k1.name as name, k1.level as level
            """
            result = session.run(query, knowledge_id=knowledge_id)
            prerequisites = []
            for record in result:
                prerequisites.append({
                    'id': record['id'],
                    'name': record['name'],
                    'level': record['level']
                })
            return prerequisites
    
    def get_knowledge_dependents(self, knowledge_id):
        """
        获取依赖某个知识点的所有后续知识点
        
        Args:
            knowledge_id: 知识点ID
            
        Returns:
            list: 后续知识点列表
        """
        driver = self.connect()
        
        with driver.session() as session:
            query = """
            MATCH (k1:Knowledge {id: $knowledge_id})-[:PREREQUISITE_OF]->(k2:Knowledge)
            RETURN k2.id as id, k2.name as name, k2.level as level
            """
            result = session.run(query, knowledge_id=knowledge_id)
            dependents = []
            for record in result:
                dependents.append({
                    'id': record['id'],
                    'name': record['name'],
                    'level': record['level']
                })
            return dependents
    
    def get_learning_path(self, course_id, target_knowledge_id):
        """
        获取学习路径：从基础知识点到目标知识点的最短路径
        
        Args:
            course_id: 课程ID
            target_knowledge_id: 目标知识点ID
            
        Returns:
            list: 学习路径（知识点列表）
        """
        driver = self.connect()
        
        with driver.session() as session:
            # 找到所有level=1的基础知识点
            base_query = """
            MATCH (k:Knowledge {course_id: $course_id, level: 1})
            RETURN k.id as id
            """
            base_result = session.run(base_query, course_id=course_id)
            base_ids = [record['id'] for record in base_result]
            
            if not base_ids:
                return []
            
            # 从基础知识点到目标知识点的最短路径
            path_query = """
            MATCH path = shortestPath(
                (start:Knowledge)-[:PREREQUISITE_OF*]->(target:Knowledge {id: $target_id})
            )
            WHERE start.id IN $base_ids
            RETURN [node in nodes(path) | {id: node.id, name: node.name, level: node.level}] as path
            ORDER BY length(path)
            LIMIT 1
            """
            path_result = session.run(path_query, target_id=target_knowledge_id, base_ids=base_ids)
            
            for record in path_result:
                return record['path']
            
            return []
    
    def get_knowledge_statistics(self, course_id):
        """
        获取课程知识图谱的统计信息
        
        Args:
            course_id: 课程ID
            
        Returns:
            dict: 统计信息
        """
        driver = self.connect()
        
        with driver.session() as session:
            # 知识点总数
            count_query = """
            MATCH (k:Knowledge {course_id: $course_id})
            RETURN count(k) as total
            """
            total = session.run(count_query, course_id=course_id).single()['total']
            
            # 各层级知识点数量
            level_query = """
            MATCH (k:Knowledge {course_id: $course_id})
            RETURN k.level as level, count(k) as count
            ORDER BY k.level
            """
            level_result = session.run(level_query, course_id=course_id)
            level_distribution = {record['level']: record['count'] for record in level_result}
            
            # 关系总数
            edge_query = """
            MATCH (k1:Knowledge {course_id: $course_id})-[:PREREQUISITE_OF]->(k2:Knowledge {course_id: $course_id})
            RETURN count(*) as total
            """
            edge_total = session.run(edge_query, course_id=course_id).single()['total']
            
            return {
                'total_knowledge': total,
                'level_distribution': level_distribution,
                'total_relationships': edge_total
            }


# 全局Neo4j服务实例
neo4j_service = Neo4jService()
