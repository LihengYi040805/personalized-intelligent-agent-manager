[README.md](https://github.com/user-attachments/files/34518937/README.md)
# personalized-intelligent-agent-manager
这是一个面向计算机课程的 AI 学习与认知诊断平台，结合在线练习、知识图谱、学习分析与大语言模型辅助出题

<p align="center">
  <strong>面向计算机课程的 AI 学习与认知诊断平台</strong><br>
  结合在线练习、知识图谱、学习分析与大语言模型辅助出题
</p>

<p align="center">
  <img alt="React" src="https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white">
  <img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white">
  <img alt="Flask" src="https://img.shields.io/badge/Flask-3-000000?logo=flask&logoColor=white">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white">
</p>

---

## 🎓 项目简介

智能教育学习系统是一个面向大学计算机课程的学习平台。学生可以浏览课程、完成练习并查看知识掌握情况；教师可以管理课程与题库、分析学习数据，并借助大语言模型从教材内容生成知识点和题目。

系统提供 IRT 与 NCDM 两种认知诊断方案，并通过知识图谱呈现知识点之间的关系，帮助学生识别薄弱环节、规划学习路径。

## ✨ 功能特色

- 📚 **课程与练习**：浏览课程和知识点，完成单选题、多选题练习并查看答题记录。
- 🧠 **认知诊断**：根据答题数据评估知识点掌握情况，支持 IRT 和 NCDM。
- 🕸️ **知识图谱**：可视化展示课程知识点及其前置关系。
- 🎯 **个性化推荐**：结合薄弱知识点推荐相关练习。
- 👩‍🏫 **教师工作台**：提供题库、学生、班级学情和薄弱知识点分析功能。
- 🤖 **AI 辅助出题**：解析上传的教材文档，调用配置的大语言模型生成知识点与题目。

## 🧰 技术栈

| 部分 | 技术 |
| --- | --- |
| 前端 | React 18、TypeScript、Vite、Ant Design、ECharts、Axios |
| 后端 | Python、Flask、Flask-SQLAlchemy |
| 关系数据库 | SQLite（默认）或 MySQL |
| 图数据库 | Neo4j（知识图谱相关功能） |
| 诊断模型 | IRT、PyTorch NCDM |
| 大语言模型 | OpenAI 兼容接口（项目文档示例为通义千问） |

## 🏗️ 项目结构

```text
AiedPlatform-main/
├── backend/
│   ├── app.py                 # Flask API 入口
│   ├── models.py              # 数据模型
│   ├── routes/                # 路由模块
│   ├── services/              # AI、诊断、推荐、知识图谱等服务
│   ├── models/                # NCDM 模型文件
│   └── requirements.txt       # Python 依赖
├── frontend/
│   ├── src/
│   │   ├── pages/             # 学生端与教师端页面
│   │   ├── services/api.ts    # 前端 API 调用
│   │   └── layouts/           # 页面布局
│   ├── package.json
│   └── vite.config.ts
├── 示例文档-数据结构.md
└── 项目技术讲解文档.md
```

## 🚀 本地运行

### 环境要求

- Python 3.10 或更高版本
- Node.js 和 npm
- 可选：MySQL、Neo4j，以及兼容 OpenAI API 的大语言模型服务

### 1. 启动后端

```bash
cd backend
python -m venv .venv
```

Windows PowerShell：

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

后端默认监听 `http://localhost:5000`。未配置 MySQL 时，项目使用 SQLite。

### 2. 启动前端

另开一个终端：

```bash
cd frontend
npm install
npm run dev
```

## ⚙️ 配置说明

后端通过环境变量读取数据库、Neo4j 和模型服务配置。可在 `backend` 目录下创建本地 `.env` 文件，例如：

ALI_API_KEY=your_api_key
API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
```



