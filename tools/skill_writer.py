#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from analyze_relationship_materials import analyze


RUNTIME_TEMPLATE = """---
name: dating_{slug}
description: {display_name}，{source_label}，恋爱模拟
user-invocable: true
---

# {display_name}

## 角色摘要

- 来源：{source_label}
- 当前阶段：{relationship_stage}
- 当前场景：{current_scene}
- 默认模式：{default_mode}
- 一句话人格：{core_persona}

## 关系卡

{relationship_card}

## 运行规则

你是这个关系对象本人，不是旁白，不是恋爱导师。

默认进入 `immersive` 模式：

1. 保持真人自然互动感
2. 不主动指导用户
3. 不主动切策略视角
4. 不进入复合路线

只有当用户主动输入以下命令时，才切策略视角：

- `/debrief`
- `/strategy`
- `/analyze`

也支持一个唯一的自然语言触发短语：

- “别演了直接教我拿下”

如果用户只是情绪化表达、普通追问，或说了别的相近句子，不要误判成切换视角。

策略视角输出：

- 当前阶段判断
- 当前场景判断
- 对方信号
- 推进风险
- 下一步建议

支持：

- `/reset`
  清空当前场景并重开
- `/stage {{相识|熟悉|升温|暧昧|表白|确定关系|恋爱}}`
  切换起始阶段
- `/scene {{日常|争吵}}`
  切换当前互动场景；`争吵` 是场景，不是关系阶段

## 硬边界

- 不支持复合
- 不做挽回前任
"""


STAGES = ["相识", "熟悉", "升温", "暧昧", "表白", "确定关系", "恋爱"]
SCENES = ["日常", "争吵"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify(text: str) -> str:
    text = text.strip()
    if not text:
        return "relationship"
    try:
        from pypinyin import lazy_pinyin
        pinyin = "-".join(lazy_pinyin(text))
        pinyin = re.sub(r"-+", "-", pinyin).strip("-")
        if pinyin:
            return pinyin.lower()
    except Exception:
        pass
    ascii_text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return ascii_text or f"relationship-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"


def source_label(meta: dict) -> str:
    return "真人复刻" if meta.get("source_type") == "real-person" else "关系原型"


def ensure_layout(skill_dir: Path) -> None:
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "versions").mkdir(exist_ok=True)
    for kind in ("docs", "messages", "images", "notes"):
        (skill_dir / "knowledge" / kind).mkdir(parents=True, exist_ok=True)
    corrections = skill_dir / "corrections.jsonl"
    if not corrections.exists():
        corrections.write_text("", encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def build_runtime(meta: dict, card_text: str) -> str:
    return RUNTIME_TEMPLATE.format(
        slug=meta["slug"],
        display_name=meta["display_name"],
        source_label=source_label(meta),
        relationship_stage=meta.get("relationship_stage", "相识"),
        current_scene=meta.get("current_scene", "日常"),
        default_mode=meta.get("default_mode", "immersive"),
        core_persona=meta.get("core_persona", "关系对象"),
        relationship_card=card_text,
    )


def snapshot_current(skill_dir: Path, version: str) -> None:
    version_dir = skill_dir / "versions" / version
    version_dir.mkdir(parents=True, exist_ok=True)
    for name in ("SKILL.md", "relationship-card.md", "meta.json", "corrections.jsonl"):
        src = skill_dir / name
        if src.exists():
            shutil.copy2(src, version_dir / name)


def next_version(version: str | None) -> str:
    if not version:
        return "v1"
    match = re.fullmatch(r"v(\d+)", version.strip())
    if not match:
        return "v2"
    return f"v{int(match.group(1)) + 1}"


def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", name).strip("-")
    return cleaned or "material.txt"


def append_note_section(card_text: str, section: str, line: str) -> str:
    if section in card_text:
        return card_text.rstrip() + "\n" + line + "\n"
    return card_text.rstrip() + f"\n\n{section}\n\n{line}\n"


def append_material_to_card(card_text: str, material_kind: str, stored_path: str) -> str:
    return append_note_section(card_text, "## source_updates", f"- [{material_kind}] 新增资料：`{stored_path}`")


def append_correction_to_card(card_text: str, correction: dict) -> str:
    line = (
        f"- [{correction.get('dimension', 'other')}] "
        f"不应该：{correction.get('wrong', '')}；应该：{correction.get('correct', '')}"
    ).strip()
    return append_note_section(card_text, "## corrections", line)


def apply_materials_to_card(card_text: str, materials: list[dict]) -> str:
    updated = card_text.rstrip()
    for material in materials:
        updated = append_material_to_card(updated, material.get("kind", "notes"), material.get("stored_path", "")).rstrip()
    return updated + "\n"


def apply_corrections_to_card(card_text: str, corrections: list[dict]) -> str:
    updated = card_text.rstrip()
    for correction in corrections:
        updated = append_correction_to_card(updated, correction).rstrip()
    return updated + "\n"


def read_text_if_possible(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def gather_material_texts(skill_dir: Path) -> str:
    chunks: list[str] = []
    for kind in ("messages", "docs", "notes"):
        target = skill_dir / "knowledge" / kind
        if not target.exists():
            continue
        for file_path in sorted(target.rglob("*")):
            if file_path.is_file():
                text = read_text_if_possible(file_path).strip()
                if text:
                    chunks.append(text)
    return "\n\n".join(chunks).strip()


def load_corrections(skill_dir: Path) -> list[dict]:
    path = skill_dir / "corrections.jsonl"
    if not path.exists():
        return []
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def merge_preserved_meta(existing_meta: dict, new_meta: dict) -> dict:
    merged = dict(new_meta)
    for key in ("slug", "created_at", "materials", "corrections_count"):
        if key in existing_meta:
            merged[key] = existing_meta[key]
    merged["display_name"] = existing_meta.get("display_name", new_meta.get("display_name"))
    merged["source_type"] = existing_meta.get("source_type", new_meta.get("source_type"))
    merged["relationship_stage"] = existing_meta.get("relationship_stage", new_meta.get("relationship_stage", "相识"))
    merged["current_scene"] = existing_meta.get("current_scene", new_meta.get("current_scene", "日常"))
    return merged


def write_skill(base_dir: Path, meta: dict, card_text: str, slug_override: str | None = None) -> Path:
    slug = slug_override or meta.get("slug") or slugify(meta.get("display_name", "relationship"))
    meta["slug"] = slug
    skill_dir = base_dir / slug
    ensure_layout(skill_dir)

    current_version = meta.get("version")
    if current_version and (skill_dir / "meta.json").exists():
        snapshot_current(skill_dir, current_version)

    now = utc_now()
    meta.setdefault("created_at", now)
    meta["updated_at"] = now
    meta.setdefault("version", "v1")
    meta.setdefault("default_mode", "immersive")
    meta.setdefault("relationship_stage", "相识")
    meta.setdefault("current_scene", "日常")

    (skill_dir / "relationship-card.md").write_text(card_text + "\n", encoding="utf-8")
    (skill_dir / "SKILL.md").write_text(build_runtime(meta, card_text), encoding="utf-8")
    (skill_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return skill_dir


def import_material(base_dir: Path, slug: str, material_file: Path, material_kind: str) -> Path:
    skill_dir = base_dir / slug
    if not skill_dir.exists():
        raise FileNotFoundError(f"relationship not found: {skill_dir}")
    if material_kind not in {"messages", "docs", "images", "notes"}:
        raise ValueError("material kind must be one of: messages, docs, images, notes")
    if not material_file.exists():
        raise FileNotFoundError(f"material not found: {material_file}")

    ensure_layout(skill_dir)
    meta = load_json(skill_dir / "meta.json")
    snapshot_current(skill_dir, meta.get("version", "v1"))

    target_dir = skill_dir / "knowledge" / material_kind
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    target_name = f"{timestamp}-{sanitize_filename(material_file.name)}"
    target_path = target_dir / target_name
    shutil.copy2(material_file, target_path)

    materials = meta.setdefault("materials", [])
    materials.append(
        {
            "added_at": utc_now(),
            "kind": material_kind,
            "original_name": material_file.name,
            "stored_path": str(target_path.relative_to(skill_dir)),
            "size_bytes": os.path.getsize(target_path),
        }
    )
    meta["updated_at"] = utc_now()
    (skill_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    refresh_skill(base_dir, slug)
    return target_path


def update_skill(base_dir: Path, slug: str, correction: dict) -> Path:
    skill_dir = base_dir / slug
    if not skill_dir.exists():
        raise FileNotFoundError(f"relationship not found: {skill_dir}")
    ensure_layout(skill_dir)
    meta = load_json(skill_dir / "meta.json")
    snapshot_current(skill_dir, meta.get("version", "v1"))

    correction_record = {
        "recorded_at": utc_now(),
        "dimension": correction.get("dimension", "other"),
        "wrong": correction.get("wrong", ""),
        "correct": correction.get("correct", ""),
        "reason": correction.get("reason", ""),
    }
    with (skill_dir / "corrections.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(correction_record, ensure_ascii=False) + "\n")

    meta["updated_at"] = utc_now()
    meta["corrections_count"] = int(meta.get("corrections_count", 0)) + 1
    (skill_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    refresh_skill(base_dir, slug)
    return skill_dir


def refresh_skill(base_dir: Path, slug: str) -> Path:
    skill_dir = base_dir / slug
    if not skill_dir.exists():
        raise FileNotFoundError(f"relationship not found: {skill_dir}")

    ensure_layout(skill_dir)
    existing_meta = load_json(skill_dir / "meta.json")
    current_version = existing_meta.get("version", "v1")
    material_text = gather_material_texts(skill_dir)
    new_meta, card_text = analyze(
        material_text,
        existing_meta.get("display_name", slug),
        existing_meta.get("source_type", "real-person"),
        existing_meta.get("relationship_stage", "相识"),
    )
    merged_meta = merge_preserved_meta(existing_meta, new_meta)
    merged_meta["updated_at"] = utc_now()
    merged_meta["version"] = next_version(current_version)
    corrections = load_corrections(skill_dir)
    final_card = apply_corrections_to_card(card_text, corrections).rstrip()
    final_card = apply_materials_to_card(final_card, merged_meta.get("materials", [])).rstrip()

    (skill_dir / "relationship-card.md").write_text(final_card + "\n", encoding="utf-8")
    (skill_dir / "SKILL.md").write_text(build_runtime(merged_meta, final_card), encoding="utf-8")
    (skill_dir / "meta.json").write_text(json.dumps(merged_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return skill_dir


def rollback_skill(base_dir: Path, slug: str, version: str) -> Path:
    skill_dir = base_dir / slug
    version_dir = skill_dir / "versions" / version
    if not version_dir.exists():
        raise FileNotFoundError(f"version not found: {version_dir}")
    for name in ("SKILL.md", "relationship-card.md", "meta.json", "corrections.jsonl"):
        src = version_dir / name
        if src.exists():
            shutil.copy2(src, skill_dir / name)
    return skill_dir


def delete_skill(base_dir: Path, slug: str) -> Path:
    skill_dir = base_dir / slug
    if not skill_dir.exists():
        raise FileNotFoundError(f"relationship not found: {skill_dir}")
    shutil.rmtree(skill_dir)
    return skill_dir


def list_skills(base_dir: Path) -> int:
    if not base_dir.exists():
        return 0
    count = 0
    for child in sorted(base_dir.iterdir()):
        meta_path = child / "meta.json"
        if not meta_path.exists():
            continue
        meta = load_json(meta_path)
        print(
            f"{meta.get('slug', child.name)}\t{meta.get('display_name', child.name)}\t"
            f"{meta.get('relationship_stage', '相识')}\t{meta.get('current_scene', '日常')}"
        )
        count += 1
    return count


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Create and manage generated relationship skills.")
    p.add_argument("--action", required=True, choices=["create", "list", "rollback", "delete", "update", "import-material", "refresh-card"])
    p.add_argument("--base-dir", default="./relationships")
    p.add_argument("--slug")
    p.add_argument("--version")
    p.add_argument("--meta-file")
    p.add_argument("--card-file")
    p.add_argument("--material-file")
    p.add_argument("--material-kind")
    p.add_argument("--update-kind")
    p.add_argument("--correction-file")
    return p


def main() -> int:
    args = parser().parse_args()
    base_dir = Path(args.base_dir).expanduser().resolve()
    try:
        if args.action == "create":
            if not args.meta_file or not args.card_file:
                raise ValueError("--meta-file and --card-file are required for create")
            meta = load_json(Path(args.meta_file))
            card_text = load_text(Path(args.card_file))
            skill_dir = write_skill(base_dir, meta, card_text, slug_override=args.slug)
            print(skill_dir)
            return 0
        if args.action == "list":
            list_skills(base_dir)
            return 0
        if args.action == "import-material":
            if not args.slug or not args.material_file or not args.material_kind:
                raise ValueError("--slug, --material-file, and --material-kind are required for import-material")
            path = import_material(base_dir, args.slug, Path(args.material_file), args.material_kind)
            print(path)
            return 0
        if args.action == "update":
            if not args.slug or args.update_kind != "correction" or not args.correction_file:
                raise ValueError("--slug, --update-kind correction, and --correction-file are required for update")
            skill_dir = update_skill(base_dir, args.slug, load_json(Path(args.correction_file)))
            print(skill_dir)
            return 0
        if args.action == "refresh-card":
            if not args.slug:
                raise ValueError("--slug is required for refresh-card")
            skill_dir = refresh_skill(base_dir, args.slug)
            print(skill_dir)
            return 0
        if args.action == "rollback":
            if not args.slug or not args.version:
                raise ValueError("--slug and --version are required for rollback")
            skill_dir = rollback_skill(base_dir, args.slug, args.version)
            print(skill_dir)
            return 0
        if args.action == "delete":
            if not args.slug:
                raise ValueError("--slug is required for delete")
            skill_dir = delete_skill(base_dir, args.slug)
            print(skill_dir)
            return 0
        raise ValueError(f"unknown action: {args.action}")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
