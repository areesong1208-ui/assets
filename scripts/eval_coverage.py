#!/usr/bin/env python3
"""프롬프트 주입 품질 평가 (reference-free).

영어 원문에서 용어집 용어를 얼마나 탐지하는지(커버리지)와,
그중 오역 위험(번역 주의사항 보유) 용어가 몇 개인지 측정한다.

사용:
    python3 scripts/eval_coverage.py --source eval/sample_idms_en.txt
"""
import argparse
import csv
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = ROOT / "data" / "display-quality-terms.csv"


def load(csv_path):
    return list(csv.DictReader(csv_path.open(encoding="utf-8")))


def match_keys(row):
    keys = []
    for field in ("en_term", "abbr"):
        for part in re.split(r"\s*/\s*", (row.get(field) or "").strip()):
            part = part.strip()
            if part and not re.fullmatch(r"[xy,]{1,3}", part):  # 'x,y' 같은 잡음 제외
                keys.append(part)
    return keys


def detect(terms, text):
    low = text.lower()
    hits = []
    for row in terms:
        for k in match_keys(row):
            if re.search(r"\b" + re.escape(k.lower()) + r"\b", low):
                hits.append(row)
                break
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    args = ap.parse_args()

    terms = load(args.csv)
    text = args.source.read_text(encoding="utf-8")
    words = len(text.split())
    hits = detect(terms, text)

    with_note = [h for h in hits if (h.get("translation_note") or "").strip()]
    by_cat = Counter(h["category"] for h in hits)
    by_src = Counter(h["source"] for h in hits)

    print(f"■ 원문: {words} 단어")
    print(f"■ 탐지 용어: {len(hits)} / 용어집 {len(terms)}")
    print(f"■ 오역위험(주의사항 보유) 탐지: {len(with_note)} "
          f"({round(100*len(with_note)/max(len(hits),1))}%)")
    print(f"■ 밀도: 100단어당 {round(100*len(hits)/max(words,1),1)}개 용어 주입")
    print("\n[범주별 탐지]")
    for c, n in by_cat.most_common():
        print(f"  - {c}: {n}")
    print("\n[출처별 탐지]")
    for s, n in by_src.most_common():
        print(f"  - {s}: {n}")
    print("\n[오역위험 상위 예시]")
    for h in with_note[:8]:
        print(f"  · {h['en_term']} → {h['ko_term']}  | 주의: {h['translation_note']}")


if __name__ == "__main__":
    main()
