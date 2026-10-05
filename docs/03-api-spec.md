# FitAgent 接口规范

版本：v1.0
作者：Young
日期：2026-10-05

---

## 1. 通用约定

### 1.1 基础 URL
http://localhost:8000/api/v1

text

开发环境用 `localhost`，生产环境替换为实际域名。

### 1.2 请求格式

- **Content-Type**：`application/json`
- **字符集**：UTF-8
- **认证**：需要认证的接口，请求头必须带 `Authorization: Bearer <token>`

### 1.3 响应格式

**所有接口**统一返回以下结构：

```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
字段	类型	说明
code	int	0 表示成功，非 0 表示错误
message	string	成功时为 "success"，失败时为错误描述
data	object / array / null	业务数据，失败时为 null
1.4 错误码表
code	HTTP 状态码	含义
0	200	成功
1001	400	参数校验失败
1002	401	未登录或 token 无效
1003	403	无权访问该资源
1004	404	资源不存在
1005	409	资源冲突（如手机号已注册）
2001	400	用户档案不完整
2002	400	热量低于安全阈值
2003	400	计划包含禁忌动作
5000	500	服务器内部错误
HTTP 状态码和 code 同步返回，前端优先看 code。

1.5 时间格式
所有时间字段用 ISO 8601 格式：

text
2026-10-05T14:30:00Z
2. 认证接口
2.1 注册
接口：POST /api/v1/auth/register

认证：不需要

请求体：

json
{
  "phone": "13800138000",
  "password": "123456",
  "name": "张三"
}
字段	类型	必填	约束
phone	string	是	11 位纯数字
password	string	是	长度 ≥ 6
name	string	是	长度 1-50
成功响应：

json
{
  "code": 0,
  "message": "success",
  "data": {
    "user_id": 1,
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "name": "张三"
  }
}
失败响应示例：

json
{
  "code": 1005,
  "message": "手机号已注册",
  "data": null
}
说明：注册只创建 users 表和 profiles 表的基础记录，档案字段（性别、年龄等）默认为空，用户首次调用 GET /users/me 时再补全。

2.2 登录
接口：POST /api/v1/auth/login

认证：不需要

请求体：

json
{
  "phone": "13800138000",
  "password": "123456"
}
成功响应：

json
{
  "code": 0,
  "message": "success",
  "data": {
    "user_id": 1,
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "name": "张三"
  }
}
失败响应：

json
{
  "code": 1002,
  "message": "手机号或密码错误",
  "data": null
}
说明：登录时更新 users.last_login_at。

3. 用户接口
3.1 获取当前用户档案
接口：GET /api/v1/users/me

认证：需要

成功响应：

json
{
  "code": 0,
  "message": "success",
  "data": {
    "user_id": 1,
    "phone": "13800138000",
    "name": "张三",
    "profile": {
      "gender": "male",
      "age": 28,
      "weight_kg": 80.0,
      "height_cm": 178.0,
      "activity": "moderate",
      "goal": "bulk",
      "experience": "intermediate",
      "injuries": "无",
      "days_per_week": 4
    }
  }
}
说明：profile 字段可能为 null（用户还没填档案）。

3.2 更新当前用户档案
接口：PUT /api/v1/users/me

认证：需要

请求体：

json
{
  "name": "张三",
  "profile": {
    "gender": "male",
    "age": 28,
    "weight_kg": 80.0,
    "height_cm": 178.0,
    "activity": "moderate",
    "goal": "bulk",
    "experience": "intermediate",
    "injuries": "无",
    "days_per_week": 4
  }
}
成功响应：

json
{
  "code": 0,
  "message": "success",
  "data": {
    "user_id": 1,
    "name": "张三",
    "profile": { ... }
  }
}
说明：PUT 是整体覆盖，不是部分更新。如果只想改一个字段，前端要先 GET 再 PUT。

4. 计划接口
4.1 生成计划
接口：POST /api/v1/plans/generate

认证：需要

请求体：

json
{}
说明：不需要请求参数。系统从当前用户的档案里读取所有信息。

成功响应：

json
{
  "code": 0,
  "message": "success",
  "data": {
    "plan_id": "tmp_001",
    "status": "pending_review",
    "nutrition_plan": "营养计划内容...",
    "workout_plan": "训练计划内容...",
    "question": "请确认计划。回复 'approve' 通过，或输入修改意见。"
  }
}
字段	说明
plan_id	临时 ID，用于后续 confirm 或 revise
status	pending_review（待确认）
nutrition_plan	营养计划全文
workout_plan	训练计划全文
question	给用户的提示语
失败响应示例：

json
{
  "code": 2001,
  "message": "用户档案不完整，缺少：weight_kg, height_cm",
  "data": null
}
说明：

生成过程会调用 LangGraph 的 invoke()，在 review 节点中断

plan_id 临时生成，不是数据库 ID

若热量低于 1200 kcal，返回 2002 错误

4.2 确认计划
接口：POST /api/v1/plans/{plan_id}/confirm

认证：需要

路径参数：

plan_id：生成时返回的临时 ID

请求体：

json
{}
成功响应：

json
{
  "code": 0,
  "message": "success",
  "data": {
    "plan_id": 1,
    "status": "completed",
    "nutrition_plan": "营养计划内容...",
    "workout_plan": "训练计划内容...",
    "created_at": "2026-10-05T14:30:00Z"
  }
}
说明：确认后计划写入 plans 表，plan_id 变为数据库真实 ID。

4.3 提交修改意见
接口：POST /api/v1/plans/{plan_id}/revise

认证：需要

路径参数：

plan_id：生成时返回的临时 ID

请求体：

json
{
  "feedback": "蛋白质太少，请增加"
}
成功响应（又触发中断）：

json
{
  "code": 0,
  "message": "success",
  "data": {
    "plan_id": "tmp_001",
    "status": "pending_review",
    "nutrition_plan": "更新后的营养计划...",
    "workout_plan": "训练计划...",
    "question": "请确认计划。",
    "retry_count": 1
  }
}
说明：

最多重试 3 次（retry_count 达到 3 时返回 429 错误）

每次 revise 会触发图重跑，生成新的计划

4.4 查询历史计划列表
接口：GET /api/v1/plans

认证：需要

查询参数：

参数	类型	必填	默认	说明
page	int	否	1	页码
page_size	int	否	10	每页数量（最大 50）
成功响应：

json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 5,
    "page": 1,
    "page_size": 10,
    "items": [
      {
        "plan_id": 5,
        "nutrition_plan": "营养计划...",
        "workout_plan": "训练计划...",
        "created_at": "2026-10-05T14:30:00Z"
      },
      {
        "plan_id": 4,
        "nutrition_plan": "营养计划...",
        "workout_plan": "训练计划...",
        "created_at": "2026-10-04T10:00:00Z"
      }
    ]
  }
}
4.5 查询单个计划详情
接口：GET /api/v1/plans/{plan_id}

认证：需要

成功响应：

json
{
  "code": 0,
  "message": "success",
  "data": {
    "plan_id": 1,
    "nutrition_plan": "营养计划...",
    "workout_plan": "训练计划...",
    "feedback": null,
    "status": "completed",
    "created_at": "2026-10-05T14:30:00Z"
  }
}
失败响应：

json
{
  "code": 1004,
  "message": "计划不存在",
  "data": null
}
5. 调试接口
5.1 简单对话
接口：POST /api/v1/chat/simple

认证：不需要（调试用）

请求体：

json
{
  "message": "你好"
}
成功响应：

json
{
  "code": 0,
  "message": "success",
  "data": {
    "reply": "你好！我是 FitAgent..."
  }
}
说明：

直接调模型，不走 Agent、不走 RAG、不查数据库

用于验证模型是否连通

生产环境应移除或加认证

6. 状态码汇总
状态	含义	出现场景
pending_review	待用户确认	生成计划后、修改后
completed	已完成	用户确认后
rejected	已拒绝	（预留，v1.0 未使用）
7. 完整接口清单
序号	方法	路径	认证	说明
1	POST	/api/v1/auth/register	否	注册
2	POST	/api/v1/auth/login	否	登录
3	GET	/api/v1/users/me	是	获取档案
4	PUT	/api/v1/users/me	是	更新档案
5	POST	/api/v1/plans/generate	是	生成计划
6	POST	/api/v1/plans/{plan_id}/confirm	是	确认计划
7	POST	/api/v1/plans/{plan_id}/revise	是	提交修改
8	GET	/api/v1/plans	是	历史列表
9	GET	/api/v1/plans/{plan_id}	是	计划详情
10	POST	/api/v1/chat/simple	否	调试对话
