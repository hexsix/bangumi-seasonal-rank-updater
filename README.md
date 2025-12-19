# bangumi-seasonal-rank-updater

Bangumi 季度排名更新器 - 从 Bangumi TV API 获取动画数据并提供排名查询服务。

---

## 目录

- [开发文档](#开发文档)
  - [安装依赖](#安装依赖)
  - [运行应用](#运行应用)
  - [数据库迁移](#数据库迁移)
- [运营文档](#运营文档)
  - [新增季度](#新增季度)
  - [API 接口说明](#api-接口说明)
  - [定时任务](#定时任务)

---

## 开发文档

### 安装依赖

install uv and init uv venv

```bash
uv venv .venv
```

activate venv

```bash
source .venv/bin/activate
```

安装项目依赖

```bash
# dev
uv pip install ".[dev]"

# product
uv sync --no-cache
```

配置环境变量

创建 `.env` 文件，配置必需的环境变量：

```env
BGMTV_TOKEN=your_bangumi_token
APP_API_PASSWORD=your_secure_password
DB_URL=postgresql://postgres:postgres@localhost:5432/rank
CF_PAGES_HOOKS=https://api.cloudflare.com/client/v4/pages/webhooks/deploy_hooks/xxxxx
```

### 运行应用

开发模式运行

```bash
fastapi run app/main.py --port 8000 --reload
```

生产模式运行

```bash
fastapi run app/main.py --port 8000 --worker 4
```

### 数据库迁移

```bash
# check current
alembic current
# upgrade
alembic upgrade head
# downgrade
alembic downgrade
# drop alembic_version
docker exec postgres psql -U postgres -d rank -c "DROP TABLE IF EXISTS alembic_version;"
# check tables
docker exec postgres psql -U postgres -d rank -c "\dt"
```

---

## 运营文档

### 新增季度

每个季度开始时（1月、4月、7月、10月），需要手动添加新季度数据。以 **2026年1月** 为例：

#### 步骤 1: 更新季度映射数据

编辑 `app/api/v0/update/data.py` 文件，在 `DATA` 字典中添加新季度：

```python
DATA = {
    202601: 12345,  # 新增这一行，12345 是 Bangumi 上该季度的索引 ID
    202510: 81501,
    202507: 78937,
    # ... 其他季度
}
```

**如何获取索引 ID**：

1. 访问 Bangumi 网站，找到对应季度的索引页面
2. 例如：`https://bgm.tv/index/12345`，其中 `12345` 就是索引 ID
3. 季度 ID 格式：`YYYYMM`（如 `202601` 表示 2026年1月）

#### 步骤 2: 更新索引数据

调用更新索引接口，将新季度的条目 ID 列表同步到数据库：

```bash
curl -X POST "http://localhost:8000/api/v0/update/index" \
  -u ":your_password" \
  -H "Content-Type: application/json" \
  -d "{}"
```

**响应示例**：

```json
{
  "success": [202601, 202510, 202507],
  "failed": []
}
```

#### 步骤 3: 更新条目详情

调用更新条目接口，获取所有条目的详细信息（评分、排名等）：

```bash
curl -X POST "http://localhost:8000/api/v0/update/subjects" \
  -u ":your_password" \
  -H "Content-Type: application/json" \
  -d "{}"
```

**注意**：此接口会在后台执行，立即返回空结果。查看日志了解执行进度：

```bash
tail -f app/logs/app.log
```

#### 步骤 4: 验证数据

查询可用季度列表，确认新季度已添加：

```bash
curl -X GET "http://localhost:8000/api/v0/season/available"
```

**响应示例**：

```json
{
  "current_season_id": 202601,
  "available_seasons": [202601, 202510, 202507, ...]
}
```

查询新季度的条目列表：

```bash
curl -X GET "http://localhost:8000/api/v0/season/202601"
```

### API 接口说明

#### 认证方式

需要认证的接口使用 **HTTP Basic Auth**：

- 用户名：任意（可为空）
- 密码：环境变量 `APP_API_PASSWORD` 的值

#### 接口列表

| 接口 | 方法 | 路径 | 认证 | 说明 |
| ------ | ------ | ------ | ------ | ------ |
| 更新索引 | POST | `/api/v0/update/index` | ✅ | 从 Bangumi API 获取所有季度的条目 ID 列表 |
| 更新条目 | POST | `/api/v0/update/subjects` | ✅ | 更新所有条目的详细信息（后台执行） |
| 获取可用季度 | GET | `/api/v0/season/available` | ❌ | 获取所有已有数据的季度列表 |
| 获取季度条目 | GET | `/api/v0/season/{season_id}` | ❌ | 获取指定季度的所有条目详情 |
| 获取单个条目 | GET | `/api/v0/subject/{subject_id}` | ✅ | 获取单个条目的详细信息 |

#### 接口详情

##### 1. 更新索引

```bash
POST /api/v0/update/index
```

**请求体**：

```json
{}
```

**响应**：

```json
{
  "success": [202601, 202510],  // 更新成功的季度 ID 列表
  "failed": []                  // 更新失败的季度 ID 列表
}
```

**说明**：遍历 `data.py` 中的所有季度，从 Bangumi API 获取条目 ID 列表并存入数据库。

---

##### 2. 更新条目

```bash
POST /api/v0/update/subjects
```

**请求体**：

```json
{}
```

**响应**：

```json
{
  "success": [],  // 立即返回空列表（后台执行）
  "failed": []
}
```

**说明**：

- 在后台异步执行，更新所有条目的详细信息
- 包括：评分、排名、收藏数、平均评论数、弃番率等
- 更新完成后会自动触发 Cloudflare Pages 部署钩子

---

##### 3. 获取可用季度

```bash
GET /api/v0/season/available
```

**响应**：

```json
{
  "current_season_id": 202601,           // 当前季度
  "available_seasons": [202601, 202510]  // 所有可用季度（降序）
}
```

---

##### 4. 获取季度条目

```bash
GET /api/v0/season/202601
```

**响应**：

```json
{
  "season_id": 202601,
  "subjects": [
    {
      "id": 123456,
      "name": "动画名称",
      "name_cn": "中文名称",
      "rank": 100,
      "score": 8.5,
      "collection_total": 5000,
      "average_comment": 120.5,
      "drop_rate": 0.15,
      "air_weekday": "星期五",
      "meta_tags": ["原创", "2026年1月"],
      "images_grid": "https://...",
      "images_large": "https://...",
      "updated_at": "2026-01-15T10:30:00"
    }
  ],
  "updated_at": "2026-01-15T10:30:00"  // 最后更新时间
}
```

---

##### 5. 获取单个条目

```bash
GET /api/v0/subject/123456
```

**响应**：与季度条目中的单个对象格式相同。

### 定时任务

系统配置了自动更新任务，无需手动干预：

**执行时间**：每天 0、4、8、12、16、20 点（每 4 小时一次）

**执行内容**：

1. 调用 `update_all()` 函数，更新所有条目的详细信息
2. 更新完成后触发 Cloudflare Pages 部署钩子

**查看任务日志**：

```bash
tail -f app/logs/app.log | grep "全量更新"
```

**手动触发定时任务**：

```bash
# 调用更新条目接口即可
curl -X POST "http://localhost:8000/api/v0/update/subjects" \
  -u ":your_password" \
  -H "Content-Type: application/json" \
  -d "{}"
```

### 常见问题

#### Q: 如何判断新季度数据更新完成？

A: 查看日志文件，搜索 "全量更新任务完成" 关键词：

```bash
grep "全量更新任务完成" app/logs/app.log
```

#### Q: 更新失败怎么办？

A:

1. 查看日志了解失败原因：`tail -f app/logs/app.log`
2. 常见原因：
   - Bangumi API 限流：等待一段时间后重试
   - 索引 ID 错误：检查 `data.py` 中的映射是否正确
   - 数据库连接失败：检查数据库服务和连接配置

#### Q: 如何只更新特定季度？

A: 目前没有直接接口，需要：

1. 临时修改 `data.py`，只保留需要更新的季度
2. 调用更新接口
3. 恢复 `data.py` 的完整内容

或者直接修改代码添加单季度更新接口。
