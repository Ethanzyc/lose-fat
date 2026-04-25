# 减脂微信机器人 — 产品设计文档

## 背景

现有一个 Claude Code 减脂健康管理 skill（[lose-fat](https://github.com/Ethanzyc/lose-fat)），包含 16 个专业知识文件（3300+ 行）、7 步交互流程、食物评分系统、用户档案管理。目标是将核心能力转化为微信聊天机器人，让甘油三酯偏高且有减脂需求的人群无需安装任何工具即可使用。

## 产品定位

- **目标用户**：身边朋友 / 社群成员（几十到几百人）
- **核心场景**：用户在微信里跟机器人私聊，完成健康建档、获取减脂方案、日常记录体重和饮食、获得正向鼓励
- **规模阶段**：MVP，验证核心流程可用
- **不考虑盈利**

## 产品形态

**微信个人号机器人**：用户扫码添加机器人为微信好友，直接通过聊天完成所有交互。

### 为什么选这个形态

| 对比 | 微信个人号机器人 | 微信公众号 | 低代码平台（Coze/Dify） |
|------|----------------|-----------|----------------------|
| 用户门槛 | 零（加好友即可） | 需关注，交互受限 | 零 |
| 对话体验 | 最自然（私聊） | 5 秒响应限制，体验差 | 中等 |
| 流程复杂度支持 | 任意多步流程 | 受限 | 受限，7 步流程难以实现 |
| 合规风险 | 个人号小规模极低 | 零 | 零 |
| 自定义程度 | 完全可控 | 中等 | 有限 |
| 开发成本 | 中等 | 中等 | 低 |

## 核心功能（MVP）

### 1. 新用户建档

用户发送 `/start` 或首次私聊时触发：

1. 机器人分步收集：姓名、年龄、性别、身高、体重、甘油三酯（必填）、其他体检指标（选填）
2. 自动计算 BMI，给出健康评估
3. 收集运动偏好（每周几天、每次多久、经验、偏好类型）
4. 收集目标体重
5. 生成并展示个人档案摘要

### 2. 减脂方案生成

建档完成后自动触发，或在任意时刻发送 `/plan`：

1. 基于用户数据计算 TDEE、每日热量目标、食物评分分配
2. 输出：饮食方案（食物评分表 + 搭配建议）、运动方案（根据 BMI 分层）、生活习惯目标
3. 以文本形式分段发送（微信单条消息不宜过长）

### 3. 日常记录

用户随时发送：

- **体重**：`75.2` / `今天 75.2kg` → 自动记录到体重历史，回复趋势分析
- **饮食**：`中午吃了碗牛肉面` / `晚上吃了火锅` → 给出评分和建议
- **运动**：`今天快走了 30 分钟` → 记录并鼓励

### 4. 进度回访

发送 `/progress` 触发：

1. 收集：当前体重、饮食执行度、运动完成度、主观感受
2. 分析体重趋势（区分水重/脂重/平台期）
3. 给出正向鼓励 + 计划调整建议

### 5. 知识问答

用户随时提问：

- `火锅怎么吃比较好？`
- `西瓜能吃吗？`
- `平台期了怎么办？`

机器人基于知识库回答。

## 技术架构

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│   微信用户   │ ←→  │  微信机器人框架   │ ←→  │  后端服务     │
│   (私聊)     │     │  (WeChatFerry)   │     │  (FastAPI)   │
└─────────────┘     └──────────────────┘     └──────┬───────┘
                                                     │
                                              ┌──────┴───────┐
                                              │              │
                                        ┌─────┴─────┐ ┌─────┴─────┐
                                        │ 大模型 API │ │  数据存储   │
                                        │ (DeepSeek) │ │  (MySQL)   │
                                        └───────────┘ └───────────┘
```

### 组件说明

#### 1. 微信机器人框架（WeChatFerry）

- 监听微信消息，转发给后端服务
- 支持文本、图片消息收发
- 运行在一台 Windows 或 Linux 机器上（需要登录微信）

**备选方案：**
- [WeChatFerry](https://github.com/nickyam/pull/blob/main/README.md)（推荐，Python SDK，活跃维护）
- [itchat](https://github.com/littlecodersh/ItChat)（较老，不推荐）
- [gewechat](https://github.com/Devo919/Gewechat)（基于 iPad 协议，Linux 部署友好）

#### 2. 后端服务（Python FastAPI）

**核心职责：**
- 接收机器人转发的消息
- 管理多用户会话和上下文
- 调用大模型 API
- 管理用户数据和知识库

**关键模块：**

| 模块 | 职责 |
|------|------|
| `message_handler` | 消息路由：识别指令（`/start`、`/plan`、`/progress`）、体重记录、饮食记录、自由问答 |
| `user_service` | 用户档案 CRUD、体重历史、进度记录 |
| `llm_service` | 大模型 API 调用、system prompt 管理、知识库注入 |
| `knowledge_service` | 知识文件管理、按需加载 |
| `plan_service` | 方案生成逻辑（TDEE 计算、食物评分分配、运动方案） |

#### 3. 大模型（DeepSeek）

- **模型**：DeepSeek-V3 或 DeepSeek-Chat
- **成本**：约 ¥1-2 / 百万 token，几十用户月费 ¥30-50
- **调用方式**：OpenAI 兼容 API
- **知识注入**：将现有 16 个知识文件作为 system prompt 或 RAG 检索结果注入

**知识库注入策略：**

知识文件总计 3300+ 行，不适合全量塞入 system prompt（token 开销大）。建议采用分层策略：

| 场景 | 策略 | 加载的知识文件 |
|------|------|--------------|
| 新用户建档 | 固定 prompt | 无（建档不需要知识库） |
| 健康评估 | 固定 prompt | triglycerides.md, fatty-liver.md, blood-sugar.md, metabolic-syndrome.md |
| 方案生成 | 固定 prompt | nutrition-guide.md, exercise-guide.md, food-scoring.md, lifestyle.md |
| 进度回访 | 固定 prompt | plateau.md, behavioral-support.md, body-composition.md |
| 自由问答 | RAG 检索 top-3 | 根据问题语义匹配相关文件 |
| 日常记录（体重/饮食/运动） | 轻量 prompt | 无或极少 |

> **MVP 阶段可以先用固定 prompt**（按场景加载对应知识文件），RAG 作为后续优化。

#### 4. 数据存储（MySQL）

已有现成的 MySQL 实例，直接复用，无需额外部署。

**核心表：**

```sql
-- 用户档案
users (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50),
  age INT,
  gender ENUM('male', 'female'),
  height_cm DECIMAL(5,1),
  weight_kg DECIMAL(5,1),
  bmi DECIMAL(4,1),
  target_weight_kg DECIMAL(5,1),
  health_data JSON,      -- tg, tc, hdl, ldl, alt, ast, liver_ultrasound, fasting_glucose
  exercise_prefs JSON,   -- weekly_days, session_duration, experience, preferred_types
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)

-- 体重历史
weight_records (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  weight_kg DECIMAL(5,1) NOT NULL,
  recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_user_time (user_id, recorded_at)
)

-- 体检历史
checkup_records (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  data JSON,              -- 各项指标
  recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
)

-- 会话状态（跟踪用户处于哪个流程步骤）
session_states (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL UNIQUE,
  state VARCHAR(50),      -- e.g. 'awaiting_age', 'awaiting_weight', 'idle'
  context JSON,            -- 当前步骤的临时数据
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)

-- 饮食记录（用户提到饮食时自动存储，不展示给用户，用于分析和诊断）
diet_records (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  meal_type ENUM('breakfast', 'lunch', 'dinner', 'snack'),
  raw_text TEXT NOT NULL,   -- 用户原始描述
  tags JSON,                -- 结构化标签，如 ["high_carb", "eating_out", "no_vegetable"]
  score INT,                -- 基于食物评分系统估算（null 表示无法评估）
  recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_user_time (user_id, recorded_at),
  INDEX idx_user_tags ((CAST(tags AS CHAR(255))))  -- 用于按标签聚合分析
)

-- 生成的方案
plans (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  cycle_number INT,
  content TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_user_cycle (user_id, cycle_number)
)
```

## 从现有 skill 迁移的内容

| 现有内容 | 迁移方式 |
|---------|---------|
| 16 个知识文件 | 原样复制到新项目的 `knowledge/` 目录 |
| SKILL.md 中的流程逻辑 | 转化为后端服务的 Python 代码 |
| TDEE/BMI 计算公式 | 提取为独立工具函数 |
| 食物评分系统 | 保留在 food-scoring.md，由大模型读取并执行 |
| 用户档案 JSON 结构 | 转化为 MySQL 表结构 |
| Dashboard 可视化 | MVP 不迁移，后续可选 |

## Prompt 设计要点

现有 skill 的 prompt 散布在 SKILL.md 中，需要重新组织为适合 API 调用的格式：

```
System Prompt 结构：
├── 角色定义（你是减脂健康管理顾问）
├── 核心规则（免责声明、回答语言、不要编造数据）
├── 按场景加载的知识文件内容
└── 当前用户的档案摘要

User Prompt：
└── 用户的原始消息
```

**关键差异：** Claude Code skill 是一次性读取知识文件后由 Claude 自主决策，API 调用需要代码主动管理"什么时候读什么文件"。这就是后端服务 `message_handler` 的核心职责——根据消息内容判断场景，加载对应知识，构建 prompt。

## 部署方案

### MVP 推荐：单机部署

```
一台轻量云服务器（或你的电脑）
├── 微信客户端（登录机器人微信号）
├── WeChatFerry（Python 进程）
├── 后端服务（FastAPI 进程）
└── MySQL（已有实例，新建库即可）
```

| 方案 | 配置 | 月费 |
|------|------|------|
| 腾讯云轻量服务器 | 2C2G，60GB SSD | ~¥50-70 |
| 本地电脑运行 | 无额外费用 | ¥0 |
| 阿里云 ECS | 2C2G | ~¥50-80 |

## 项目结构建议

```
lose-fat-bot/
├── README.md
├── requirements.txt
├── config/
│   ├── settings.py          # 配置（API key、数据库连接、端口等）
│   └── prompts/             # system prompt 模板
│       ├── assessment.md
│       ├── plan.md
│       ├── followup.md
│       └── qa.md
├── knowledge/               # 从现有 skill 复制，原样保留
│   ├── triglycerides.md
│   ├── fatty-liver.md
│   ├── food-scoring.md
│   └── ...（16 个文件）
├── src/
│   ├── main.py              # FastAPI 入口
│   ├── bot/
│   │   ├── wechat.py        # WeChatFerry 集成
│   │   └── message_handler.py  # 消息路由
│   ├── services/
│   │   ├── user_service.py
│   │   ├── llm_service.py
│   │   ├── knowledge_service.py
│   │   └── plan_service.py
│   ├── models/
│   │   └── database.py      # MySQL 表定义和操作
│   └── utils/
│       ├── calculator.py    # BMI、TDEE 等计算
│       └── formatter.py     # 消息格式化（分段、表情等）
└── tests/
```

## MVP 功能优先级

### P0（必须）
- [ ] 微信消息收发
- [ ] 新用户建档（分步引导）
- [ ] 健康评估 + 减脂方案生成
- [ ] 体重记录和趋势回复
- [ ] 知识问答（基于知识库）

### P1（应该有）
- [ ] 饮食记录和评分反馈
- [ ] 运动记录
- [ ] 进度回访和计划调整
- [ ] 多用户隔离

### P2（后续优化）
- [ ] RAG 检索替代固定 prompt
- [ ] 定时提醒（称重、运动）
- [ ] 数据可视化（复用现有 dashboard）
- [ ] 知识库更新机制

## 成本估算

| 项目 | 月费 |
|------|------|
| DeepSeek API（50 用户，每人每天 10-20 条消息） | ¥30-60 |
| 云服务器（可选） | ¥50-70 |
| **合计** | **¥30-130/月** |

## 风险和注意事项

| 风险 | 影响 | 应对 |
|------|------|------|
| 微信封号 | 机器人微信号被封 | 使用小号；小规模私聊风险极低；不群发不营销 |
| 大模型幻觉 | 给出错误的医学建议 | system prompt 中强调"仅供参考，不构成医疗建议"；关键数字（TG 范围、BMI 标准）硬编码验证 |
| 知识库过期 | 指南更新后知识文件未同步 | 定期复查；在回答中标注参考指南版本 |
| 用户隐私 | 体检数据敏感 | 数据加密存储；不外传；隐私声明 |

## 与现有 skill 项目的关系

- **现有项目（lose-fat）**：保持纯 Claude Code skill 定位，继续独立迭代
- **新项目（lose-fat-bot）**：独立仓库，复制 `knowledge/` 目录作为初始知识库
- **知识库同步**：skill 项目更新知识文件后，手动或通过脚本同步到 bot 项目
