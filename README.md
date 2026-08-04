# 삼성디스플레이 화질 용어 시멘틱 데이터

영어 → 한글로 번역된 IDMS 문서의 **한글 답변 품질 향상**을 목표로, 삼성디스플레이 **화질(Picture Quality) 용어**를 정제한 시멘틱 데이터(도메인 용어 지식베이스)를 구축하는 프로젝트입니다.

## 구성

| 경로 | 내용 |
|------|------|
| [`docs/업무계획.md`](docs/업무계획.md) | 업무 계획서 (목표·단계·스키마·일정·결정사항) |
| [`data/display-quality-terms.csv`](data/display-quality-terms.csv) | 화질 용어 시멘틱 데이터 (**104개 용어**: 일반 55 + IDMS 추출 49) |
| [`prompts/translation-qa-prompt.md`](prompts/translation-qa-prompt.md) | LLM 프롬프트 주입 템플릿 |
| [`scripts/build_glossary_prompt.py`](scripts/build_glossary_prompt.py) | 원문에서 용어 자동 탐지 → 프롬프트 블록 생성 |

## 시멘틱 데이터 스키마

`id, category, en_term, ko_term, ko_synonyms, abbr, definition_ko, translation_note, source`

- 범주(category): `휘도/명암`, `색`, `계조`, `결함·불량`, `시간응답`, `해상도·구조`, `규격·측정`
- 출처(source): `일반(seed)` 또는 실제 추출 챕터(예: `IDMS Ch01`, `IDMS Ch04`) — 용어 추적성 확보

## 데이터 출처 (IDMS)

용어는 **IDMS (Information Display Measurements Standard, SID/ICDM 2025)** 영문 원문에서 추출합니다.
구글 드라이브에 챕터별 PDF로 보관되어 있으며, 챕터를 처리할 때마다 용어집이 확장됩니다.
- 처리 완료: Ch01(Introduction), Ch04(Visual Assessment)
- 진행 예정: Ch05~Ch21 (Fundamental/Color Scale/Uniformity/Viewing Angle/Temporal/Motion/HDR 등)

## 활용 방향

이 용어집은 번역·질의응답 시 **도메인 근거(grounding)**로 주입되어, 전문 용어의 오역과 표기 불일치를 줄입니다. 예: `mura`→'무라(얼룩)', `image sticking`→'잔상' vs `burn-in`→'번인' 구분 등.

### 사용 예

```bash
# 영어 원문(idms_en.txt)에서 관련 용어만 탐지해 프롬프트 블록 생성
python3 scripts/build_glossary_prompt.py --source idms_en.txt

# system prompt 전체 생성
python3 scripts/build_glossary_prompt.py --source idms_en.txt --full-prompt
```

> 진행 현황과 다음 단계는 [`docs/업무계획.md`](docs/업무계획.md) §6을 참고하세요.
