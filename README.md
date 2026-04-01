<div align="center">

# 恋爱.skill

<hr>

> “我这么发出去，不能变小丑吧🤡🤡🤡”

让 AI 完美模拟真实人格，陪你完成从相识到热恋的完整推演。<br>
根据聊天记录将互动风格、边界感、好感信号，蒸馏成可调用的 AI Skill。

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)
![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet.svg)
![AgentSkills](https://img.shields.io/badge/AgentSkills-Standard-green.svg)

<br>

[安装](#安装) · [使用说明](#使用) · [阶段模型](#阶段模型) · [效果示例](#效果示例) · [English](README_EN.md)

</div>

## 核心理念

拧巴人有福了！HeartFlow 不做烂大街的 AI 陪伴，而是你的专属情感导师。通过 Skill 把 Agent 作为特定的关系对象，你可以在高拟真的模拟互动中，学会如何推进关系。

### 两种角色构建模式

- **Archetype 定制生成**：自由组合关系风格（如慢热型、主动型、边界感强型、暧昧拉扯型），叠加星座象限、具体星座与 MBTI，快速生成标准练习对象。
- **1:1 真人深度复刻**：支持喂入聊天截图、文档、社交软件导出记录以及你的主观文字描述，高度还原那个真实的 Ta。

### 覆盖完整恋爱生命周期

支持全链路场景模拟。你可以顺着真实时间线练习：**相识、熟悉、升温、暧昧、表白、确定关系、恋爱**。也可以随时切入 **争吵** 等高难度特殊场景进行定向单练。

### 持续进化的感情对象

告别生硬的 Prompt。生成后的角色不再是一成不变的，Ta 会随着你的资料追加和当场对话纠正而持续进化。（老师，我最擅长把天聊死了怎么办？同学同学没关系，咱支持 **版本回滚**。）

### 沉浸与策略视角无缝切换

- **沉浸式对线**：生成角色后，直接使用 `/{slug}` 开练，进入默认的第一视角真实互动。
- **上帝视角复盘**：遇到卡壳或不知如何回复时，既可以输入 `/debrief`，也可以直接说“别演了直接教我拿下”这句自然语言，切换到策略视角，让 AI 为你拆解当前局势、分析好感信号并提供推进建议。

## 安装

这个目录本身就是一个独立 skill。

Claude Code:

```bash
mkdir -p .claude/skills
cp -R /path/to/heartflow .claude/skills/create-heartflow
```

或全局安装：

```bash
cp -R /path/to/heartflow ~/.claude/skills/create-heartflow
```

可选依赖：

```bash
pip3 install -r requirements.txt
```

## 使用

### 1. 创建关系对象

```text
/create-heartflow
```

创建时支持两条路径：

- `archetype`
  通过关系风格 + 星座 + MBTI 混合生成对象
- `real-person`
  根据聊天记录、截图、文档、社交软件聊天导出和主观描述复刻某个人

创建时会问：

- 这个人怎么称呼
- 你们现在是什么阶段
- 是否从当前阶段直接开始

如果用户跳过阶段，默认从 `相识` 开始。

如果你们已经认识、也聊过一阵，通常从 `升温` 开始更合适。

### 2. 继续养成和纠正

```text
/update-heartflow lin
```

可以做两类更新：

- 追加资料
- 对话纠正

原始资料会归档到：

```text
relationships/{slug}/knowledge/
```

纠正记录会归档到：

```text
relationships/{slug}/corrections.jsonl
```

### 3. 直接互动

```text
/lin
```

默认始终保持沉浸式，不会主动跳出剧情给建议。
只有用户主动输入 `/debrief`、`/strategy`、`/analyze`，
或者明确输入“别演了直接教我拿下”时，才切换到策略视角。

也支持场景切换：

```text
/scene 争吵
```

这里的 `争吵` 是互动场景，不是关系阶段。

### 4. 回滚对象

```text
/heartflow-rollback lin v2
```

## 阶段模型

固定主线：

`相识 -> 熟悉 -> 升温 -> 暧昧 -> 表白 -> 确定关系 -> 恋爱`

但用户可以在创建时直接指定当前阶段。

多数实战演练里，如果双方已经不陌生，从 `升温` 开始通常更自然。

场景层：

- `日常`
- `争吵`

其中 `争吵` 是任意阶段都可能进入的互动场景，不属于主线阶段。

明确限制：

- 不支持复合分支
- 不做挽回前任路线

## 效果示例

场景一：从熟悉阶段开始

```text
用户              ❯ /lin

恋爱.skill         ❯ 今天怎么突然找我？
用户              ❯ 想起你之前说过那家店，我刚好路过。
恋爱.skill         ❯ 你这开场还挺自然的。你去了吗？
```

场景二：切策略视角

```text
用户              ❯ /strategy

恋爱.skill         ❯ 当前阶段判断：熟悉 -> 升温边缘
                    对方信号：回应稳定，愿意接你的话题，但还没有明显情绪投入
                    风险点：过早表露推进意图会破坏自然感
                    下一步建议：围绕共同记忆或线下轻邀约，测试主动性
```

## 社交聊天记录导入

支持把常见日常社交软件导出的聊天文件统一导入进来，例如：

- 微信/QQ 导出的文本整理稿
- Telegram 导出的 JSON
- WhatsApp 导出的 TXT
- 其他平台整理成 `txt / json / jsonl / csv` 的聊天记录

导入聊天记录：

```bash
python3 tools/social_chat_import.py \
  --input ./exports/chat.json \
  --platform telegram \
  --output ./relationships/lin/knowledge/messages/social-chat.txt
```

然后刷新对象卡：

```bash
python3 tools/skill_writer.py --action refresh-card --slug lin --base-dir ./relationships
```

## 验证

```bash
python3 -m unittest discover -s tests -v
```

---

MIT License © [BboTTM](https://github.com/BboTTM)

这个 skill 的 meta-skill 结构与 README 组织方式参考了
[titanwings/colleague-skill](https://github.com/titanwings/colleague-skill)。
