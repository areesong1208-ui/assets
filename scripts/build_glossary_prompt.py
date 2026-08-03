#!/usr/bin/env python3
"""
build_glossary_prompt.py

영어 IDMS 원문에서 화질 용어집(data/display-quality-terms.csv)에 등록된 용어를
자동 탐지하여, LLM 프롬프트에 주입할 '표준 표기 강제' 블록을 생성한다.

사용 예:
    # 원문 파일에서 관련 용어만 추출해 프롬프트 블록 생성
    python3 scripts/build_glossary_prompt.py --source path/to/idms_en.txt

    # 전체 용어를 블록으로 출력 (원문 없이)
    python3 scripts/build_glossary_prompt.py --all

    # 완성된 system prompt까지 생성 (템플릿 결합)
    python3 scripts/build_glossary_prompt.py --source idms_en.txt --full-prompt
"""
import argparse
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = ROOT / "data" / "display-quality-terms.csv"


def load_terms(csv_path: Path):
    with csv_path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _match_keys(row):
    """원문 매칭에 사용할 키(영문 용어 + 약어)들을 반환."""
    keys = []
    en = (row.get("en_term") or "").strip()
    if en:
        # 'Bright dot / Dark dot' 같이 슬래시로 묶인 경우 분리
        for part in re.split(r"\s*/\s*", en):
            part = part.strip()
            if part:
                keys.append(part)
    abbr = (row.get("abbr") or "").strip()
    for a in re.split(r"\s*/\s*", abbr):
        a = a.strip()
        if a:
            keys.append(a)
    return keys


def find_relevant(terms, source_text: str):
    """원문에 등장하는 용어 행만 필터링."""
    text = source_text.lower()
    hits = []
    for row in terms:
        for key in _match_keys(row):
            # 단어 경계 기반 매칭(약어는 대소문자 구분 없이).
            pattern = r"\b" + re.escape(key.lower()) + r"\b"
            if re.search(pattern, text):
                hits.append(row)
                break
    return hits


def render_block(rows) -> str:
    """LLM에 주입할 용어 블록(마크다운 표 형태) 생성."""
    if not rows:
        return "[용어 사전] (원문에서 등록된 화질 용어가 탐지되지 않았습니다.)"
    lines = ["[용어 사전 — 한글 표준 표기]"]
    for r in rows:
        en = r["en_term"]
        ko = r["ko_term"]
        abbr = (r.get("abbr") or "").strip()
        note = (r.get("translation_note") or "").strip()
        head = f"- {en}"
        if abbr:
            head += f" ({abbr})"
        head += f" → {ko}"
        syn = (r.get("ko_synonyms") or "").strip()
        if syn:
            head += f"  [동의어: {syn}]"
        lines.append(head)
        if note:
            lines.append(f"    · 주의: {note}")
    return "\n".join(lines)


TEMPLATE = """당신은 삼성디스플레이 화질(Picture Quality) 도메인 전문 번역·질의응답 assistant입니다.
영어 IDMS 문서를 근거로 한국어 답변을 생성합니다.

[용어 표기 규칙 — 반드시 준수]
아래 용어 사전의 한글 표준 표기를 그대로 사용하십시오. 사전에 없는 용어만 자유롭게 번역합니다.
- 표준 표기가 지정된 용어는 임의로 다른 표현으로 바꾸지 마십시오.
- 번역 주의사항(오역 경고)이 있으면 반드시 반영하십시오.
- 약어(abbr)는 원문 약어를 유지하십시오.

{block}

[답변 규칙]
- 문서에 근거가 없는 내용은 추측하지 말고 "문서에 근거 없음"으로 표시하십시오.
- 용어 표기는 문서 전체에서 일관되게 유지하십시오."""


def main():
    ap = argparse.ArgumentParser(description="화질 용어집 → LLM 프롬프트 주입 블록 생성")
    ap.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="용어집 CSV 경로")
    ap.add_argument("--source", type=Path, help="영어 원문 파일 경로")
    ap.add_argument("--all", action="store_true", help="전체 용어를 블록으로 출력")
    ap.add_argument("--full-prompt", action="store_true", help="system prompt 전체 생성")
    args = ap.parse_args()

    terms = load_terms(args.csv)

    if args.all:
        rows = terms
    elif args.source:
        source_text = args.source.read_text(encoding="utf-8")
        rows = find_relevant(terms, source_text)
    else:
        ap.error("--source 또는 --all 중 하나가 필요합니다.")
        return

    block = render_block(rows)

    if args.full_prompt:
        print(TEMPLATE.format(block=block))
    else:
        print(block)
    print(f"\n# 매칭 용어 수: {len(rows)} / 전체 {len(terms)}", file=sys.stderr)


if __name__ == "__main__":
    main()
