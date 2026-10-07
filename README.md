# FitAgent

基于 LangGraph 的个人健身助手 Agent，自动生成个性化的训练和饮食计划。

---

## 一、项目简介

FitAgent 是一个 **AI Agent 应用**，用户填写个人档案（性别、年龄、体重、身高、目标、训练条件）后，系统自动生成：

- **饮食计划**：基于 BMR/TDEE 计算目标热量，分配宏量营养素，给出餐次建议
- **训练计划**：根据目标和经验水平，生成周结构、动作、组数次数

**核心特性**：

- **确定性计算**：BMR/TDEE/宏量营养素由工具计算，LLM 不自己心算，保证结果可复现
- **RAG 检索**：营养和动作建议来自知识库，带来源标注，可追溯
- **HITL 中断**：生成后暂停，用户确认或提反馈，支持多轮修改
- **四层架构**：API / Service / Agent / Data 分层，职责清晰，可维护

---

## 二、功能列表

| 功能 | 说明 |
|---|---|
| 用户注册/登录 | 手机号 + 密码，JWT 认证 |
| 个人档案管理 | 填写、更新身体数据和训练条件 |
| 计划生成 | 调用 LangGraph 生成营养 + 训练计划 |
| HITL 确认 | 用户确认或提交修改意见（最多 3 次） |
| 历史计划 | 查询已确认的计划列表和详情 |
| 简单对话 | 直接调模型（调试用） |

---

## 三、技术栈

| 类别 | 技术 |
|---|---|
| 语言 | Python 3.12 |
| Agent 框架 | LangChain 1.4 / LangGraph 1.2 |
| 模型 | 通义千问（qwen3.7-plus，DashScope OpenAI 兼容接口） |
| 嵌入模型 | text-embedding-v4 |
| 向量库 | ChromaDB |
| Web 框架 | FastAPI |
| 数据库 | MySQL 8（SQLAlchemy ORM） |
| 会话持久化 | SQLite（LangGraph checkpointer） |
| 认证 | JWT（python-jose）+ bcrypt |

---

## 四、架构设计

### 4.1 四层架构
```
┌──────────────────────────────────────────────────┐
│ API 层（app/api/） │
│ 接收 HTTP 请求、参数校验、返回响应 │
│ 只做"转接"，不写业务逻辑 │
├──────────────────────────────────────────────────┤
│ Service 层（app/services/） │
│ 编排业务逻辑，调用 Agent 和 Repository │
├──────────────────────────────────────────────────┤
│ Agent 层（app/agents/） │
│ 定义智能体、工具、提示词 │
│ 用 LangGraph 编排营养和训练两个 Agent │
├──────────────────────────────────────────────────┤
│ Data 层（app/repositories/ + app/models/） │
│ 数据库读写、向量库读写 │
└──────────────────────────────────────────────────┘
```

### 4.2 核心调用流
```
用户请求
↓
API 层 → Service 层 → LangGraph 编排
↓
nutrition_node → 营养 Agent
├── calculate_bmr / tdee / macros（计算工具）
└── search_nutrition（检索营养库）
↓
workout_node → 训练 Agent
└── search_workout（检索动作库）
↓
review_node → interrupt() 暂停，等用户确认
↓
用户确认 → 落库 → 返回
```


详细设计见 [`docs/02-architecture.md`](docs/02-architecture.md)。

---

## 五、快速开始

### 5.1 环境要求

- Python 3.12+
- MySQL 8
- DashScope API Key（[申请地址](https://dashscope.console.aliyun.com/)）

### 5.2 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/你的用户名/fitagent.git
cd fitagent

# 2. 创建虚拟环境
python3.12 -m venv .venv
source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 DASHSCOPE_API_KEY、DATABASE_URL、JWT_SECRET_KEY

# 5. 创建数据库
mysql -u root -p -e "CREATE DATABASE fitagent DEFAULT CHARSET utf8mb4;"

# 6. 建表
python -m scripts.init_db

# 7. 构建向量库（需要先准备两份 PDF 放到 data/knowledge/）
python -m scripts.build_vectorstore

# 8. 启动服务
uvicorn app.main:app --reload
启动后访问：http://127.0.0.1:8000/docs
```
### 5.3 环境变量说明

| 变量 | 说明 |
|---|---|
| `DASHSCOPE_API_KEY` | DashScope API Key |
| `DASHSCOPE_BASE_URL` | DashScope OpenAI 兼容端点 |
| `DATABASE_URL` | MySQL 连接串 |
| `JWT_SECRET_KEY` | JWT 签名密钥 |
| `JWT_EXPIRE_HOURS` | Token 过期时间（小时） |
| `CHROMA_PERSIST_DIR` | 向量库持久化目录 |

**生成 JWT_SECRET_KEY**：

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 六、接口示例

### 6.1 注册

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "13800138000",
    "password": "123456",
    "name": "张三"
  }'
```

**响应**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "user_id": 1,
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "name": "张三"
  }
}
```

### 6.2 更新档案

```bash
curl -X PUT http://127.0.0.1:8000/api/v1/users/me \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "name": "张三",
    "profile": {
      "gender": "male",
      "age": 28,
      "weight_kg": 80,
      "height_cm": 178,
      "activity": "moderate",
      "goal": "bulk",
      "experience": "intermediate",
      "injuries": "无",
      "days_per_week": 4
    }
  }'
```

### 6.3 生成计划

```bash
curl -X POST http://127.0.0.1:8000/api/v1/plans/generate \
  -H "Authorization: Bearer <token>"
```

**响应**（生成需要 30-60 秒）：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "plan_id": "user_1_plan_1760000000",
    "status": "pending_review",
    "nutrition_plan": "...",
    "workout_plan": "...",
    "question": "请确认计划。回复 'approve' 通过，或输入修改意见。"
  }
}
```

### 6.4 确认计划

```bash
curl -X POST http://127.0.0.1:8000/api/v1/plans/user_1_plan_1760000000/confirm \
  -H "Authorization: Bearer <token>"
```

完整的接口清单见 [`docs/03-api-spec.md`](docs/03-api-spec.md)。

## 七、项目结构
```
fitagent/
├── app/
│   ├── api/               # API 层
│   │   ├── deps.py        # 依赖注入
│   │   └── v1/            # 路由
│   ├── services/          # Service 层（业务编排）
│   ├── agents/            # Agent 层（LangGraph 编排）
│   ├── tools/             # 工具集（计算、检索）
│   ├── rag/               # RAG 链路（加载、嵌入、检索）
│   ├── models/            # ORM 模型
│   ├── repositories/      # 数据访问层
│   ├── schemas/           # Pydantic 模型
│   ├── core/              # 配置、异常、日志、安全
│   └── main.py            # FastAPI 入口
├── data/
│   └── knowledge/         # 知识库 PDF
├── docs/                  # 项目文档
│   ├── 01-requirements.md
│   ├── 02-architecture.md
│   ├── 03-api-spec.md
│   └── 04-data-model.md
├── scripts/               # 辅助脚本
│   ├── init_db.py
│   └── build_vectorstore.py
├── tests/                 # 测试
├── .env.example
├── requirements.txt
└── README.md
```
## 八、关键设计决策

| 决策 | 理由 |
|---|---|
| **BMR/TDEE 用工具算** | LLM 是概率模型，同样输入可能不同输出，健康类应用必须可复现 |
| **RAG 检索带来源** | 用户可以追溯依据，出错时能定位是知识库还是模型问题 |
| **营养和训练拆两个 Agent** | 领域知识差异大，各自的工具集和提示词不同 |
| **HITL 中断** | LLM 生成的计划不一定符合预期，给用户确认和修改的机会 |
| **短期会话用 SQLite** | HITL 中断可能跨小时甚至跨进程，必须持久化 |
| **Repository 只 flush 不 commit** | 事务边界由 Service 层控制，保证多个写入的原子性 |

---

## 九、后续优化方向

- **异步改造**：API/Service/Agent 全面异步，提升并发能力
- **Docker 部署**：一条命令启动 app + MySQL
- **流式输出**：SSE 或 WebSocket，让用户逐字看到计划生成
- **安全护栏**：热量下限、禁忌动作的中间件拦截
- **单元测试**：核心业务覆盖率 > 60%
- **Redis 会话**：从 SQLite checkpointer 迁移到 Redis，支持分布式部署