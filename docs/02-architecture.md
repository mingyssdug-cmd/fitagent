# FitAgent 架构设计文档

版本：v1.0
作者：Young
日期：2026-10-05

---

## 1. 架构总览

### 1.1 四层架构
┌──────────────────────────────────────────────────┐
│ API 层（app/api/） │
│ 职责：接收 HTTP 请求、参数校验、返回响应 │
│ 只做"转接"，不写业务逻辑 │
├──────────────────────────────────────────────────┤
│ Service 层（app/services/） │
│ 职责：编排业务逻辑 │
│ 调用 Agent、Repository，组装结果 │
├──────────────────────────────────────────────────┤
│ Agent 层（app/agents/） │
│ 职责：定义智能体、工具、提示词 │
│ 只关心"怎么让模型干活" │
├──────────────────────────────────────────────────┤
│ Data 层（app/repositories/ + app/models/） │
│ 职责：数据库读写、向量库读写 │
│ 只关心"数据怎么存取" │
└──────────────────────────────────────────────────┘

text

### 1.2 每层职责的边界

| 层 | 该做什么 | 不该做什么 |
|---|---|---|
| **API** | 解析请求、校验参数、调 Service、返回响应 | 直接查数据库、直接调 Agent、写业务判断 |
| **Service** | 编排流程、组合多个 Agent/Repository 调用 | 直接写 SQL、直接处理 HTTP 细节 |
| **Agent** | 定义 Agent、工具、提示词、中间件 | 直接访问数据库、直接处理 HTTP |
| **Data** | 封装数据库操作、向量库操作 | 写业务逻辑、做 HTTP 处理 |

---

## 2. 分层调用规则

### 2.1 允许的调用
API 层 → Service 层 → Agent 层
→ Data 层（通过 Repository）

text

- API 可以调 Service
- Service 可以调 Agent
- Service 可以调 Repository
- Agent 可以调 Tool（工具层）
- Agent 可以调 RAG（检索层）

### 2.2 禁止的调用

| 禁止 | 原因 |
|---|---|
| API 直接调 Repository | 绕过 Service 的业务逻辑 |
| API 直接调 Agent | 同上 |
| Agent 直接调 Repository | Agent 不应关心数据怎么存 |
| Repository 调 Service | 依赖反向，形成循环 |
| 任何层直接调 `model.invoke()` | 必须通过 Agent 层封装的接口 |

### 2.3 依赖方向图
┌──────────┐
│ API 层 │
└────┬─────┘
│
▼
┌──────────┐
│ Service │
└────┬─────┘
│
┌─────┴─────┐
▼ ▼
┌────────┐ ┌──────────┐
│ Agent │ │Repository│
└───┬────┘ └────┬─────┘
│ │
▼ ▼
┌────────┐ ┌──────────┐
│ Tools │ │ MySQL │
│ RAG │ │ ChromaDB │
└────────┘ └──────────┘

text

**箭头方向 = 允许的调用方向。反向调用一律禁止。**

---

## 3. 模块清单

### 3.1 API 层（`app/api/`）

| 文件 | 职责 |
|---|---|
| `deps.py` | 依赖注入：`get_db()`、`get_current_user()`、`get_settings()` |
| `v1/auth.py` | 认证路由：`/auth/register`、`/auth/login` |
| `v1/users.py` | 用户路由：`/users/me`（GET、PUT） |
| `v1/plans.py` | 计划路由：`/plans/generate`、`/plans/{id}/confirm`、`/plans/{id}/revise`、`/plans`、`/plans/{id}` |
| `v1/chat.py` | 聊天路由：`/chat/simple`（调试用） |

### 3.2 Service 层（`app/services/`）

| 文件 | 职责 |
|---|---|
| `auth_service.py` | 注册、登录、密码校验、token 生成 |
| `user_service.py` | 用户档案的读写、字段校验 |
| `plan_service.py` | 计划生成编排、确认、修改、查询 |
| `chat_service.py` | 简单对话（调试用） |

### 3.3 Agent 层（`app/agents/`）

| 文件 | 职责 |
|---|---|
| `nutrition.py` | 营养 Agent 定义（工具、提示词） |
| `workout.py` | 训练 Agent 定义 |
| `graph.py` | LangGraph 编排：营养节点 → 训练节点 → review 节点 |
| `middleware/guardrail.py` | 安全护栏中间件（热量下限、禁忌动作） |

### 3.4 工具层（`app/tools/`）

| 文件 | 职责 |
|---|---|
| `calculator.py` | BMR、TDEE、宏量营养素计算（纯函数） |
| `nutrition_search.py` | 营养库检索工具 |
| `workout_search.py` | 动作库检索工具 |

### 3.5 RAG 层（`app/rag/`）

| 文件 | 职责 |
|---|---|
| `loader.py` | PDF 加载和切分 |
| `embedder.py` | 向量化（封装 OpenAIEmbeddings） |
| `retriever.py` | 向量库构建和检索 |

### 3.6 Data 层

**`app/models/`（ORM 模型）**：

| 文件 | 职责 |
|---|---|
| `base.py` | SQLAlchemy Base 定义、引擎、Session |
| `user.py` | User 模型（认证信息） |
| `profile.py` | Profile 模型（档案信息） |
| `profile.py` | Plan 模型（历史计划） |

**`app/repositories/`（数据访问）**：

| 文件 | 职责 |
|---|---|
| `user_repo.py` | 用户表 CRUD |
| `profile_repo.py` | 档案表 CRUD |
| `plan_repo.py` | 计划表 CRUD |

### 3.7 Schema 层（`app/schemas/`）

| 文件 | 职责 |
|---|---|
| `auth.py` | 注册、登录的请求/响应模型 |
| `user.py` | 用户档案的请求/响应模型 |
| `profile.py` | 计划相关的请求/响应模型 |
| `common.py` | 通用响应格式（如 `{"code": 0, "data": ...}`） |

### 3.8 核心层（`app/core/`）

| 文件 | 职责 |
|---|---|
| `config.py` | 配置加载（从 `.env` 读） |
| `security.py` | 密码哈希、JWT 生成与解析 |
| `logging.py` | 日志配置 |
| `exceptions.py` | 自定义异常类 |

### 3.9 入口（`app/main.py`）

只做三件事：
1. 创建 FastAPI 实例
2. 注册路由（从 `api/v1/` 引入）
3. 注册中间件（CORS、日志）

**不写任何业务逻辑。**

---

## 4. 数据流

### 4.1 用户注册流程
POST /auth/register
│
▼
API 层：auth.py 接收请求
│
▼
Service 层：auth_service.register()
├── 校验手机号、密码格式
├── 检查手机号是否已注册
├── 密码哈希
└── 调用 user_repo.create()
│
▼
Data 层：user_repo 写入 users 表
│
▼
API 层：返回 token 和 member_id

text

### 4.2 生成计划流程
POST /plans/generate
│
▼
API 层：plans.py 接收请求
├── 从 token 解析 user_id（依赖注入）
├── 校验用户档案完整性
└── 调用 plan_service.generate()
│
▼
Service 层：plan_service.generate()
├── 从 profile_repo 读用户档案
├── 调用 graph_app.invoke() 启动 Agent 流程
└── 返回中断信息
│
▼
Agent 层：graph_app 执行
├── nutrition_node → 营养 Agent
│ ├── 调 calculator（BMR/TDEE/宏量）
│ └── 调 nutrition_search（检索营养库）
├── workout_node → 训练 Agent
│ └── 调 workout_search（检索动作库）
└── review_node → interrupt() 暂停
│
▼
API 层：返回 pending_review + 两份计划

text

### 4.3 确认计划流程
POST /plans/{plan_id}/confirm
│
▼
API 层：plans.py 接收请求
│
▼
Service 层：plan_service.confirm()
├── 调用 graph_app.invoke(Command(resume="approve"))
├── 从 graph 返回结果
└── 调用 plan_repo.create() 保存到 plans 表
│
▼
Data 层：plan_repo 写入 plans 表
│
▼
API 层：返回最终计划

text

---

## 5. 技术选型

| 技术 | 用途 | 选型理由 |
|---|---|---|
| **FastAPI** | Web 框架 | 异步、自动生成 OpenAPI 文档、Pydantic 校验 |
| **SQLAlchemy 2.x** | ORM | 成熟、支持类型注解、可迁移 |
| **MySQL 8** | 主数据库 | 通用、支持事务、性能足够 |
| **ChromaDB** | 向量库 | 本地持久化、零部署成本、LangChain 原生集成 |
| **LangChain 1.4** | Agent 框架 | 工具调用、中间件、模型抽象 |
| **LangGraph 1.2** | 编排框架 | 状态图、中断恢复、checkpointer |
| **JWT** | 认证 | 无状态、适合 API |
| **bcrypt** | 密码哈希 | 加盐、慢哈希、抗彩虹表 |
| **SQLite** | LangGraph checkpointer | 零部署、持久化、Python 标准库 |

---

## 6. 横切关注点

### 6.1 配置管理

**所有配置从 `.env` 读取**，通过 `app/core/config.py` 统一管理。

```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    dashscope_api_key: str
    dashscope_base_url: str
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    
    class Config:
        env_file = ".env"

settings = Settings()
其他模块通过 from app.core.config import settings 读取，不直接调 os.getenv()。

6.2 异常处理
所有自定义异常继承 AppException：

python
class AppException(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
全局异常处理器（在 main.py 注册）：

python
@app.exception_handler(AppException)
async def app_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.code,
        content={"code": exc.code, "message": exc.message},
    )
Service 层抛 AppException，API 层不用写 try/except。

6.3 日志
统一用 app/core/logging.py 配置的 logger，不用 print。

日志级别：

DEBUG：开发调试

INFO：正常请求、关键操作

WARNING：可恢复的异常

ERROR：需要关注的错误

6.4 认证
JWT 流程：

登录成功 → security.create_token(user_id) 生成 token

客户端带 Authorization: Bearer <token>

deps.get_current_user() 解析 token → 查数据库 → 返回 User 对象

需要认证的路由参数写 current_user: User = Depends(get_current_user)

6.5 依赖注入
FastAPI 的 Depends 机制：

python
# app/api/deps.py
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    # 解析 token，返回 User
    ...

def get_settings():
    return settings
路由里用：

python
@router.get("/users/me")
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ...
7. 目录结构
text
fitagent/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI 入口
│   │
│   ├── api/                        # API 层
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── plans.py
│   │       └── chat.py
│   │
│   ├── services/                   # Service 层
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── plan_service.py
│   │   └── chat_service.py
│   │
│   ├── agents/                     # Agent 层
│   │   ├── __init__.py
│   │   ├── nutrition.py
│   │   ├── workout.py
│   │   ├── graph.py
│   │   └── middleware/
│   │       ├── __init__.py
│   │       └── guardrail.py
│   │
│   ├── tools/                      # 工具层
│   │   ├── __init__.py
│   │   ├── calculator.py
│   │   ├── nutrition_search.py
│   │   └── workout_search.py
│   │
│   ├── rag/                        # RAG 层
│   │   ├── __init__.py
│   │   ├── loader.py
│   │   ├── embedder.py
│   │   └── retriever.py
│   │
│   ├── models/                     # ORM 模型
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── profile.py
│   │   └── plan.py
│   │
│   ├── repositories/               # 数据访问层
│   │   ├── __init__.py
│   │   ├── user_repo.py
│   │   ├── profile_repo.py
│   │   └── plan_repo.py
│   │
│   ├── schemas/                    # Pydantic 模型
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── plan.py
│   │   └── common.py
│   │
│   └── core/                       # 核心配置
│       ├── __init__.py
│       ├── config.py
│       ├── security.py
│       ├── logging.py
│       └── exceptions.py
│
├── data/
│   └── knowledge/                  # 知识库 PDF
│
├── docs/                           # 项目文档
│   ├── 01-requirements.md
│   ├── 02-architecture.md
│   ├── 03-api-spec.md
│   ├── 04-data-model.md
│   └── 05-deployment.md
│
├── tests/                          # 测试
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   └── test_plans.py
│
├── scripts/                        # 辅助脚本
│   ├── init_db.py
│   └── build_vectorstore.py
│
├── .env
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
└── pyproject.toml
8. 架构决策记录（ADR）
ADR-1：为什么用四层架构
背景：上一版 main.py 单文件臃肿。

决策：分 API / Service / Agent / Data 四层。

收益：职责清晰、可独立测试、可替换实现。

ADR-2：为什么数据库拆分 users 和 profiles
背景：认证信息和档案信息的变更频率不同，字段性质不同。

决策：拆成 users（认证）+ profiles（档案）。

收益：未来加微信登录、邮箱登录，只改 users 表。

ADR-3：为什么短期对话和长期对话分开存储
背景：LangGraph 的 checkpointer 和业务数据是两种不同性质的数据。

决策：

短期对话（会话状态、中断点）→ SQLite checkpointer

长期对话（历史计划、反馈）→ MySQL plans 表

收益：职责分离，checkpointer 可重建，业务数据永久保存。

ADR-4：为什么用 JWT 而不是 Session
背景：API 服务需要无状态认证。

决策：JWT。

收益：服务端不存 session，方便水平扩展。

## 10. 后续优化方向

以下内容 v1.0 不做，记录为 v1.1+ 的迭代方向：

### 10.1 异步改造

**背景**：当前所有层用同步实现（`def` + `Session`）。当并发用户增多时，一个请求等 LLM 响应会阻塞其他请求。

**方案**：
- API 层路由改用 `async def`
- Service 层改用 `async def`
- Agent 层用 `ainvoke` 替代 `invoke`
- Data 层用 `AsyncSession` 替代 `Session`
- 数据库驱动从 `pymysql` 换成 `aiomysql`

**收益**：单机并发能力提升数倍，为后续水平扩展打基础。

### 10.2 Redis 会话缓存

**背景**：当前用 `MemorySaver`（进程内存），uvicorn 重启后中断状态丢失。

**方案**：迁移到 Redis checkpointer 或 SQLite checkpointer。

### 10.3 Docker 一键部署

**背景**：当前需要手动起 MySQL、装依赖、跑 uvicorn。

**方案**：写 `Dockerfile` + `docker-compose.yml`，一条命令启动 app + MySQL。

### 10.4 流式输出

**背景**：当前 `/chat/simple` 是同步返回，用户等 5-10 秒才能看到回复。

**方案**：用 SSE 或 WebSocket 实现流式输出。微信小程序端用 `enableChunked` 接收。

### 10.5 安全护栏中间件

**背景**：当前需求文档定义了护栏（热量下限、禁忌动作），但代码还没实现。

**方案**：用 LangChain 的 `@after_model` 中间件实现。

### 10.6 单元测试

**背景**：当前没有测试，无法保证修改不破坏已有功能。

**方案**：用 `pytest` 写核心业务的测试，覆盖率 > 60%。
EOF