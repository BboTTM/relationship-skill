---
name: create-heartflow
description: "Create and evolve a HeartFlow skill. Supports archetype-based characters and real-person reconstruction from chats, screenshots, docs, exported social chat logs, and notes. | 创建并进化一个恋爱 skill。"
argument-hint: "[person-name-or-slug]"
version: "0.1.0"
user-invocable: true
allowed-tools: Read, Write, Edit, Bash
---

# 恋爱.skill 创建器

这个 skill 用来做两件事：

1. 创建一个新的关系对象
2. 调用一个已有对象做沉浸式恋爱互动

## 触发方式

- `/create-heartflow`
- “帮我做一个恋爱 skill”
- “我想蒸馏一个暧昧对象”
- “创建一个恋爱对象”

运行和管理流程：

- `/update-heartflow {slug}`
- `/heartflow-rollback {slug} {version}`
- `/{slug}`

## 使用目标

这个 skill 不是普通聊天器，而是“模拟恋爱进程，但可以蒸馏人格”的恋爱模拟器。

它服务的阶段是：

- 相识
- 熟悉
- 升温
- 暧昧
- 表白
- 确定关系
- 恋爱

它还支持场景层：

- 日常
- 争吵

其中 `争吵` 是互动场景，不属于关系主线阶段。

明确不支持：

- 复合
- 挽回前任

## 创建流程

### Step 1: 先问来源类型

一次只问一个问题：

“这次你要创建哪种关系对象？
`[A] archetype`
`[B] real-person`”

### Step 2: 再问当前阶段

“你们现在是什么阶段？”

可选：

- 相识
- 熟悉
- 升温
- 暧昧
- 表白
- 确定关系
- 恋爱

如果用户跳过，默认 `相识`。

如果用户表示双方已经认识、已经聊过一阵，可以提醒：多数实战演练从 `升温` 开始更合适。

### Step 3A: archetype 路径

按 `prompts/intake.md` 的顺序收集：

1. 这个人怎么称呼
2. 关系风格 archetype
3. 星座象限 / 星座
4. MBTI
5. 当前阶段

### Step 3B: real-person 路径

按 `prompts/intake.md` 的顺序收集：

1. 这个人怎么称呼
2. 你们现在是什么阶段
3. 你准备提供什么资料
4. 你主观觉得对方是什么互动风格

资料支持：

- 聊天记录
- 聊天截图
- 文档
- 社交软件导出的聊天文件
- 主观描述

如果用户给的是社交软件导出的聊天文件：

```bash
python3 ${CLAUDE_SKILL_DIR}/tools/social_chat_import.py \
  --input "{chat_export_file}" \
  --platform "{wechat|qq|telegram|whatsapp|other}" \
  --output "./relationships/{slug}/knowledge/messages/social-chat.txt"
```

### Step 4: 生成对象

先分析资料：

```bash
python3 ${CLAUDE_SKILL_DIR}/tools/analyze_relationship_materials.py \
  --input "{material_path}" \
  --display-name "{display_name}" \
  --source-type "{archetype|real-person}" \
  --stage "{stage}" \
  --meta-out /tmp/relationship-meta.json \
  --card-out /tmp/relationship-card.md
```

再写入对象：

```bash
python3 ${CLAUDE_SKILL_DIR}/tools/skill_writer.py \
  --action create \
  --slug "{slug}" \
  --meta-file /tmp/relationship-meta.json \
  --card-file /tmp/relationship-card.md \
  --base-dir ./relationships
```

## 运行流程

`/{slug}` 直接进入沉浸式互动。

默认规则：

1. 保持沉浸感
2. 不主动切策略视角
3. 不主动指导用户

只有用户主动输入这些命令，才切视角：

- `/debrief`
- `/strategy`
- `/analyze`

也支持一个唯一的自然语言触发短语：

- “别演了直接教我拿下”

除这句以外，不要因为“帮我分析一下”“我下一步该怎么推进”这类普通提问自动切换，避免误触发和破坏沉浸感。

策略视角输出：

- 当前阶段判断
- 当前场景判断
- 对方信号
- 关系推进风险
- 下一步建议

## 进化流程

`/update-heartflow {slug}` 只做两件事：

1. 追加资料
2. 对话纠正

追加资料：

```bash
python3 ${CLAUDE_SKILL_DIR}/tools/skill_writer.py \
  --action import-material \
  --slug "{slug}" \
  --material-file "{path}" \
  --material-kind "{messages|docs|images|notes}" \
  --base-dir ./relationships
```

刷新对象卡：

```bash
python3 ${CLAUDE_SKILL_DIR}/tools/skill_writer.py --action refresh-card --slug "{slug}" --base-dir ./relationships
```

对话纠正：

```bash
python3 ${CLAUDE_SKILL_DIR}/tools/skill_writer.py \
  --action update \
  --slug "{slug}" \
  --update-kind correction \
  --correction-file "{correction_json}" \
  --base-dir ./relationships
```
