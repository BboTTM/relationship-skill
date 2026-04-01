#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ARCHETYPE_KEYWORDS = {
    "高冷型": ["嗯", "哦", "再说", "看情况", "不一定", "随缘"],
    "慢热型": ["慢慢来", "再了解一下", "不着急", "先熟一点"],
    "主动型": ["我来", "要不要", "一起", "下次", "那我找你"],
    "边界感强型": ["不太方便", "先这样", "不要误会", "保持距离"],
    "暧昧拉扯型": ["你猜", "再说吧", "看你表现", "也不是不行"],
}

MBTI_HINTS = {
    "INTJ": ["冷静", "理性", "克制"],
    "INFP": ["敏感", "慢热", "情绪细"],
    "ENFP": ["热情", "会接话", "主动"],
    "ISFJ": ["稳", "照顾人", "保守"],
}

ZODIAC_ELEMENTS = {
    "火象": ["白羊", "狮子", "射手"],
    "土象": ["金牛", "处女", "摩羯"],
    "风象": ["双子", "天秤", "水瓶"],
    "水象": ["巨蟹", "天蝎", "双鱼"],
}

STAGES = ["相识", "熟悉", "升温", "暧昧", "表白", "确定关系", "恋爱"]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def normalize_lines(text: str) -> list[str]:
    return [line.strip() for line in re.split(r"[\r\n]+", text) if line.strip()]


def keyword_hits(text: str, keywords: list[str]) -> int:
    return sum(text.count(keyword) for keyword in keywords)


def pick_archetype(text: str) -> tuple[str, dict[str, int]]:
    scores = {name: keyword_hits(text, words) for name, words in ARCHETYPE_KEYWORDS.items()}
    best = max(scores, key=scores.get) if scores else "慢热型"
    if scores.get(best, 0) == 0:
        best = "慢热型"
    return best, scores


def detect_mbti(text: str) -> str | None:
    text_upper = text.upper()
    for mbti in MBTI_HINTS:
        if mbti in text_upper:
            return mbti
    return None


def detect_zodiac(text: str) -> str | None:
    for element, signs in ZODIAC_ELEMENTS.items():
        if element in text:
            return element
        for sign in signs:
            if sign in text:
                return sign
    return None


def infer_bullets(text: str, keywords: list[str], fallback: list[str]) -> list[str]:
    bullets: list[str] = []
    for line in normalize_lines(text):
        if any(keyword in line for keyword in keywords):
            cleaned = re.sub(r"\s+", " ", line)
            if cleaned not in bullets:
                bullets.append(cleaned[:90])
        if len(bullets) >= 4:
            break
    return bullets or fallback


def extract_sample_lines(text: str) -> list[str]:
    found: list[str] = []
    for sentence in re.split(r"[。！？\n]", text):
        sentence = sentence.strip()
        if len(sentence) < 4:
            continue
        if any(token in sentence for token in ["一起", "改天", "看情况", "慢慢来", "别急", "你猜"]):
            if sentence not in found:
                found.append(sentence)
        if len(found) >= 4:
            break
    return found or ["嗯，先慢慢来吧。", "改天有机会可以一起。"]


def build_card(meta: dict, text: str) -> str:
    interaction = infer_bullets(
        text,
        ["回复", "聊天", "主动", "慢慢来", "不一定", "一起", "下次"],
        ["聊天节奏偏自然，不会一下给很多信号", "会根据你的节奏决定回应力度"],
    )
    affection = infer_bullets(
        text,
        ["好感", "喜欢", "在意", "想见", "想你", "主动找"],
        ["好感表达偏克制，需要通过互动密度判断", "不会很快直接说破"],
    )
    boundaries = infer_bullets(
        text,
        ["不要", "不方便", "误会", "边界", "先这样", "不太合适"],
        ["对推进过快比较敏感", "需要尊重边界才会继续升温"],
    )
    signals = infer_bullets(
        text,
        ["主动", "回应", "冷淡", "没兴趣", "会不会", "要不要"],
        ["有好感时会给持续回应", "没兴趣时会明显降频或收口"],
    )
    progress = infer_bullets(
        text,
        ["一起", "下次", "见面", "单独", "主动找", "分享"],
        ["共同记忆增加", "线下轻邀约被积极接住"],
    )
    risks = infer_bullets(
        text,
        ["太快", "压迫", "冒犯", "尴尬", "误会", "失控"],
        ["推进过快会让关系降温", "过度解释或过度试探会破坏自然感"],
    )
    samples = extract_sample_lines(text)
    card = [
        "## 核心人格",
        "",
        meta["core_persona"],
        "",
        "## 当前阶段",
        "",
        meta["relationship_stage"],
        "",
        "## 当前场景",
        "",
        meta.get("current_scene", "日常"),
        "",
        "## interaction_style",
        "",
        *[f"- {item}" for item in interaction[:4]],
        "",
        "## affection_style",
        "",
        *[f"- {item}" for item in affection[:4]],
        "",
        "## boundaries",
        "",
        *[f"- {item}" for item in boundaries[:4]],
        "",
        "## signal_patterns",
        "",
        *[f"- {item}" for item in signals[:4]],
        "",
        "## progress_triggers",
        "",
        *[f"- {item}" for item in progress[:4]],
        "",
        "## risk_triggers",
        "",
        *[f"- {item}" for item in risks[:4]],
        "",
        "## sample_lines",
        "",
        *[f"- {item}" for item in samples[:4]],
        "",
        "## debrief_rules",
        "",
        meta["debrief_rules"],
    ]
    return "\n".join(card).strip() + "\n"


def analyze(text: str, display_name: str, source_type: str, stage: str, user_notes: str = "") -> tuple[dict, str]:
    combined = f"{user_notes}\n{text}".strip()
    archetype, scores = pick_archetype(combined)
    mbti = detect_mbti(combined)
    zodiac = detect_zodiac(combined)
    confidence = "high" if len(combined) > 800 else "medium" if len(combined) > 200 else "low"
    if source_type == "real-person":
        core_persona = f"{archetype}互动风格对象，在 {stage} 阶段会通过回应节奏和边界感释放信号。"
    else:
        mix = " + ".join(part for part in [archetype, zodiac, mbti] if part) or archetype
        core_persona = f"{mix} 混合生成对象，当前处于 {stage} 阶段。"
    if confidence == "low":
        core_persona += " 当前判断基于有限资料。"

    meta = {
        "display_name": display_name,
        "source_type": source_type,
        "relationship_stage": stage if stage in STAGES else "相识",
        "current_scene": "日常",
        "core_persona": core_persona,
        "default_mode": "immersive",
        "strategy_mode": "manual-only",
        "archetype_mix": {
            "relationship_style": archetype,
            "zodiac": zodiac or "",
            "mbti": mbti or "",
        },
        "debrief_rules": "只有在用户主动触发 `/debrief`、`/strategy`、`/analyze`，或明确输入“别演了直接教我拿下”时，才分析当前阶段、场景、信号、风险和下一步建议。",
        "analysis": {
            "archetype_guess": archetype,
            "archetype_scores": scores,
            "confidence": confidence,
            "source_excerpt_length": len(combined),
        },
    }
    return meta, build_card(meta, combined)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Analyze relationship materials and draft a relationship card.")
    p.add_argument("--input", action="append", dest="inputs", default=[], help="Material text file path. Repeatable.")
    p.add_argument("--display-name", required=True)
    p.add_argument("--source-type", choices=["archetype", "real-person"], required=True)
    p.add_argument("--stage", default="相识")
    p.add_argument("--notes-file")
    p.add_argument("--meta-out", required=True)
    p.add_argument("--card-out", required=True)
    return p


def main() -> int:
    args = parser().parse_args()
    material_texts = [read_text(Path(path)) for path in args.inputs]
    notes = read_text(Path(args.notes_file)) if args.notes_file else ""
    combined = "\n\n".join(material_texts).strip()
    meta, card = analyze(combined, args.display_name, args.source_type, args.stage, user_notes=notes)
    Path(args.meta_out).write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    Path(args.card_out).write_text(card, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
