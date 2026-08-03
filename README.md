# 삼성디스플레이 화질 용어 시멘틱 데이터

영어 → 한글로 번역된 IDMS 문서의 **한글 답변 품질 향상**을 목표로, 삼성디스플레이 **화질(Picture Quality) 용어**를 정제한 시멘틱 데이터(도메인 용어 지식베이스)를 구축하는 프로젝트입니다.

## 구성

| 경로 | 내용 |
|------|------|
| [`docs/업무계획.md`](docs/업무계획.md) | 업무 계획서 (목표·단계·스키마·일정·확인사항) |
| [`data/display-quality-terms.csv`](data/display-quality-terms.csv) | 화질 용어 시멘틱 데이터 (시드, 55개 용어) |

## 시멘틱 데이터 스키마

`id, category, en_term, ko_term, ko_synonyms, abbr, definition_ko, translation_note`

범주(category): `휘도/명암`, `색`, `계조`, `결함·불량`, `시간응답`, `해상도·구조`, `규격·측정`

## 활용 방향

이 용어집은 번역·질의응답 시 **도메인 근거(grounding)**로 주입되어, 전문 용어의 오역과 표기 불일치를 줄입니다. 예: `mura`→'무라(얼룩)', `image sticking`→'잔상' vs `burn-in`→'번인' 구분 등.

> 진행 현황과 다음 단계는 [`docs/업무계획.md`](docs/업무계획.md) §6을 참고하세요.
