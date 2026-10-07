# FitAgent 数据模型

> 版本：v1.0
> 作者：Young
> 日期：2026-10-05

---

## 1. 数据模型总览

### 1.1 表关系图

```text
┌─────────────┐          ┌─────────────┐
│   users     │ 1      1 │  profiles   │
│  认证信息   │ ──────── │  档案信息   │
│             │          │             │
│ id (PK)     │          │ id (PK)     │
│ phone       │          │ user_id FK  │
│ password    │          │ gender      │
│ name        │          │ age         │
│ status      │          │ weight_kg   │
│ last_login  │          │ ...         │
└──────┬──────┘          └─────────────┘
       │
       │ 1
       │
       │ N
┌──────┴──────┐
│   plans     │
│  历史计划   │
│             │
│ id (PK)     │
│ user_id FK  │
│ nutrition   │
│ workout     │
│ feedback    │
│ goal        │
│ status      │
└─────────────┘
```

**关系说明**：

- 一个 user 对应一个 profile（1:1）
- 一个 user 对应多个 plans（1:N）

### 1.2 表职责

| 表 | 职责 | 变更频率 |
| --- | --- | --- |
| users | 认证信息（手机号、密码、状态） | 低 |
| profiles | 身体数据（年龄、体重、目标） | 中 |
| plans | 历史计划 | 高（每次生成写一条） |

---

## 2. users 表

### 2.1 字段定义

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | INT | PK, AUTO_INCREMENT | 主键 |
| phone | VARCHAR(11) | UNIQUE, NOT NULL, INDEX | 手机号 |
| password_hash | VARCHAR(255) | NOT NULL | 密码哈希（bcrypt） |
| name | VARCHAR(50) | NOT NULL | 姓名 |
| status | TINYINT | NOT NULL, DEFAULT 1 | 1=正常，0=禁用 |
| last_login_at | DATETIME | NULL | 最后登录时间 |
| created_at | DATETIME | NOT NULL, DEFAULT NOW | 创建时间 |

### 2.2 设计决策

**为什么 name 放在 users 而不是 profiles**：

- 注册时必须填 name，放 users 表方便
- name 变更频率低，和认证信息一起管理更简单
- profiles 表保持"纯粹的档案数据"

**为什么用 status 而不是 deleted_at**：

- 用户禁用和用户删除是两个概念
- status=0 表示禁用（可恢复），不是物理删除
- v1.0 不做物理删除，防止误删

**为什么 password_hash 长度 255**：

- bcrypt 哈希固定 60 字符，但预留空间给未来的算法（如 argon2）
- VARCHAR(255) 是通用做法

---

## 3. profiles 表

### 3.1 字段定义

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | INT | PK, AUTO_INCREMENT | 主键 |
| user_id | INT | FK → users.id, UNIQUE, NOT NULL | 外键，一个用户一份 |
| gender | VARCHAR(10) | NOT NULL | male / female |
| age | INT | NOT NULL | 年龄 |
| weight_kg | FLOAT | NOT NULL | 体重（公斤） |
| height_cm | FLOAT | NOT NULL | 身高（厘米） |
| activity | VARCHAR(20) | NOT NULL | sedentary / light / moderate / active / very_active |
| goal | VARCHAR(20) | NOT NULL | cut / bulk / maintain |
| experience | VARCHAR(20) | NOT NULL | beginner / intermediate / advanced |
| injuries | TEXT | NULL | 伤病史 |
| days_per_week | INT | NOT NULL | 每周训练天数 |
| created_at | DATETIME | NOT NULL, DEFAULT NOW | 创建时间 |
| updated_at | DATETIME | NOT NULL, DEFAULT NOW ON UPDATE | 更新时间 |

### 3.2 设计决策

**为什么 user_id 加 UNIQUE**：

- v1.0 一个用户只有一份档案
- 未来如果要支持多档案（给自己、给家人），去掉 UNIQUE 即可

**为什么 injuries 用 TEXT**：

- 伤病史可能较长（"左膝半月板损伤，2023 年手术，避免深蹲和箭步蹲"）
- TEXT 不限长度，适合这种自由文本
- 代价：TEXT 不能设默认值，不能直接建索引（v1.0 不需要对 injuries 建索引）

**为什么用 FLOAT 而不是 DECIMAL**：

- 体重、身高不需要精确到小数点后很多位
- FLOAT 足够（80.5 kg 这种精度够用）
- DECIMAL 适合金额，不适合物理量

**为什么 activity / goal / experience 用 VARCHAR 而不是 ENUM**：

- VARCHAR + 应用层校验更灵活（加新枚举值不用改表）
- MySQL 的 ENUM 修改成本高
- 代价：数据库层不做枚举校验，靠应用层

---

## 4. plans 表

### 4.1 字段定义

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | INT | PK, AUTO_INCREMENT | 主键 |
| user_id | INT | FK → users.id, NOT NULL, INDEX | 外键 |
| goal | VARCHAR(20) | NOT NULL | 生成时的目标（cut/bulk/maintain） |
| nutrition_plan | TEXT | NOT NULL | 营养计划全文 |
| workout_plan | TEXT | NOT NULL | 训练计划全文 |
| feedback | TEXT | NULL | 用户的修改意见（最后一次） |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'completed' | pending / completed |
| created_at | DATETIME | NOT NULL, DEFAULT NOW | 创建时间 |

### 4.2 索引设计

| 索引名 | 字段 | 类型 | 用途 |
| --- | --- | --- | --- |
| idx_plans_user_id | user_id | 普通索引 | 按用户查历史 |
| idx_plans_user_created | (user_id, created_at DESC) | 复合索引 | 按用户查历史并按时间倒序 |

**为什么要复合索引**：

- 最常见查询是"查某用户的所有计划，按时间倒序"
- 复合索引 `(user_id, created_at DESC)` 可以直接覆盖这个查询，不用回表排序

### 4.3 设计决策

**为什么加 goal 字段**：

- 用户的 `goal` 会变（先减脂后增肌）
- 历史计划应该记录"当时的目标是什么"
- 如果从 `profiles` 表读 `goal`，用户改了目标后，历史计划的语义就错了

**为什么 feedback 只存最后一次**：

- v1.0 简化设计，只记录最终反馈
- 未来如果需要完整反馈历史，可以单独建 `plan_feedback` 表

**为什么 status 默认 'completed'**：

- 只有确认后的计划才写入 plans 表
- 生成中/待确认的计划不在 plans 表里（在 LangGraph checkpointer 里）
- 所以写入时状态一定是 completed
- 保留 status 字段是为了未来扩展（如支持"作废"）

**为什么 nutrition_plan 和 workout_plan 用 TEXT**：

- 计划是长文本（含 Markdown 格式），可能几百到几千字
- TEXT 上限 65535 字节，足够
- 不需要对计划内容做索引

---

## 5. SQLAlchemy 模型定义

以下是 `app/models/` 下的模型定义（S5 写代码时按此实现）：

### 5.1 base.py

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
```

### 5.2 user.py

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, SmallInteger
from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(11), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(50), nullable=False)
    status = Column(SmallInteger, nullable=False, default=1)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
```

### 5.3 profile.py

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from app.models.base import Base


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    gender = Column(String(10), nullable=False)
    age = Column(Integer, nullable=False)
    weight_kg = Column(Float, nullable=False)
    height_cm = Column(Float, nullable=False)
    activity = Column(String(20), nullable=False)
    goal = Column(String(20), nullable=False)
    experience = Column(String(20), nullable=False)
    injuries = Column(Text, nullable=True)
    days_per_week = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 5.4 plan.py

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from app.models.base import Base


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    goal = Column(String(20), nullable=False)
    nutrition_plan = Column(Text, nullable=False)
    workout_plan = Column(Text, nullable=False)
    feedback = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="completed")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_plans_user_created", "user_id", created_at.desc()),
    )
```

---

## 6. 建表 SQL（参考）

虽然 v1.0 用 SQLAlchemy 自动建表，但保留 SQL 作为参考：

```sql
-- users 表
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    phone VARCHAR(11) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(50) NOT NULL,
    status TINYINT NOT NULL DEFAULT 1,
    last_login_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_users_phone (phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- profiles 表
CREATE TABLE profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    gender VARCHAR(10) NOT NULL,
    age INT NOT NULL,
    weight_kg FLOAT NOT NULL,
    height_cm FLOAT NOT NULL,
    activity VARCHAR(20) NOT NULL,
    goal VARCHAR(20) NOT NULL,
    experience VARCHAR(20) NOT NULL,
    injuries TEXT NULL,
    days_per_week INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- plans 表
CREATE TABLE plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    goal VARCHAR(20) NOT NULL,
    nutrition_plan TEXT NOT NULL,
    workout_plan TEXT NOT NULL,
    feedback TEXT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'completed',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_plans_user_id (user_id),
    INDEX idx_plans_user_created (user_id, created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 7. 数据流示例

### 7.1 用户注册时

1. 插入 users 表：phone, password_hash, name
2. 不插入 profiles 表（等用户填档案时再插）

### 7.2 用户填写档案时

1. 检查 profiles 表中是否存在该 user_id
2. 不存在 → INSERT
3. 已存在 → UPDATE

### 7.3 用户确认计划时

1. 从 LangGraph checkpointer 读取计划内容
2. 插入 plans 表：user_id, goal, nutrition_plan, workout_plan, feedback

### 7.4 用户查询历史

```sql
SELECT * FROM plans WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?
```

---

## 8. 待确认问题

- 是否需要软删除（deleted_at 字段）？
- 是否需要记录计划的版本（同一计划的多次修改）？
- 是否需要记录每次 LLM 调用的 token 消耗（用于成本统计）？

以上问题 v1.0 不做。
