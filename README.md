# Personal Agent - 个人AI助理

基于 LangGraph + FastAPI + Vue3 构建的个人AI助理智能体。

## 技术栈

### 后端
- **FastAPI** - 高性能异步API框架
- **LangGraph** - 强大的Agent编排框架
- **LangChain** - LLM工具链
- **SQLite/MemorySaver** - 会话持久化

### 前端
- **Vue 3** - 渐进式前端框架
- **Vite** - 快速构建工具
- **Axios** - HTTP客户端
- **Pinia** - 状态管理

## 快速开始

### 1. 配置环境变量

```bash
cd backend

# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的API密钥
# LLM_PROVIDER: openai 或 anthropic
# OPENAI_API_KEY: 你的OpenAI API密钥
# ANTHROPIC_API_KEY: 你的Anthropic API密钥
# MODEL_NAME: 模型名称（如 gpt-4o, claude-3-5-sonnet-20241022）
```

### 2. 安装依赖

**后端：**
```bash
cd backend
pip install -r requirements.txt
```

**前端：**
```bash
cd frontend
npm install
```

### 3. 启动服务

**启动后端：**
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**启动前端（新终端）：**
```bash
cd frontend
npm run dev
```

### 4. 访问应用

打开浏览器访问：http://localhost:5173

## 功能特性

- ✅ 实时对话
- ✅ 多会话管理
- ✅ 历史记录
- ✅ 流式输出（可扩展）
- ✅ 记忆持久化
- ✅ 现代化UI

## 项目结构

```
personal-agent/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py       # API路由
│   │   ├── core/
│   │   │   └── config.py       # 配置
│   │   ├── models/
│   │   │   └── schemas.py      # 数据模型
│   │   ├── services/
│   │   │   └── agent.py        # LangGraph Agent
│   │   └── main.py             # FastAPI入口
│   ├── logs/
│   ├── requirements.txt
│   └── .env
│
└── frontend/
    ├── src/
    │   ├── api/
    │   │   └── client.js        # API客户端
    │   ├── components/
    │   │   └── ChatView.vue     # 聊天界面
    │   ├── App.vue
    │   └── main.js
    ├── index.html
    ├── package.json
    └── vite.config.js
```

## 下一步计划

### 阶段 2：自动化能力
- [ ] 工具调用（日历、邮件、文件）
- [ ] 文件操作
- [ ] 网页自动化
- [ ] 智能提醒

### 阶段 3：多模态
- [ ] 语音输入（Whisper）
- [ ] 语音输出（TTS）
- [ ] 图像理解

### 阶段 4：本地化
- [ ] 切换到本地LLM（Ollama）
- [ ] 离线语音识别
- [ ] 完全本地运行

### 阶段 5：高级功能
- [ ] 长期记忆（向量数据库）
- [ ] 自主决策
- [ ] 多角色切换
- [ ] 端到端加密

## 开发指南

### 添加新的API端点

1. 在 `backend/app/models/schemas.py` 定义数据模型
2. 在 `backend/app/api/routes.py` 添加路由
3. 在 `frontend/src/api/client.js` 添加对应的API调用

### 扩展Agent能力

修改 `backend/app/services/agent.py`：

- 添加工具（Tools）
- 修改状态（State）
- 添加新的节点（Nodes）

## 常见问题

### Q: 如何切换LLM提供商？
A: 编辑 `backend/.env` 文件，设置 `LLM_PROVIDER` 为 `openai` 或 `anthropic`，并填入对应的API密钥。

### Q: 会话数据保存在哪里？
A: 目前使用内存存储（MemorySaver），重启后会丢失。后期可升级为SQLite或其他数据库。

### Q: 如何添加流式输出？
A: 在 FastAPI 路由中使用 `StreamingResponse`，前端使用 `EventSource` 或 `readableStream` 接收。

## License

MIT
