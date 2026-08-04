# 프롬프트 주입 품질 검증 — 번역 전/후 비교

영어 IDMS 문체 지문을 **① 용어집 없이(generic)** 와 **② 용어집 주입 후** 로 각각 한글 번역하여
용어 표기 정확도·일관성이 어떻게 개선되는지 비교한다. (병렬 정답 없이 reference-free 검증)

- 원문: [`eval/sample_idms_en.txt`](sample_idms_en.txt) (198단어)
- 커버리지: 40개 용어 탐지 / 오역위험 용어 100% 포착 (`scripts/eval_coverage.py`)

---

## 원문 발췌 (1문단)

> The peak luminance reached 1000 cd/m2 at low APL, but the auto brightness limiter (ABL)
> reduced the sustained luminance to about 250 cd/m2 at 100% APL. ... We observed mura in the
> upper region and slight image sticking after a two-hour static pattern; no permanent burn-in
> was detected. ... the gamma curve followed the target EOTF closely, although black crush
> appeared in the near-black region. ... Gray-to-gray (GtG) response time was 1 ms ... but
> overdrive caused visible overshoot. ... Viewing angle showed measurable color shift off-axis
> ... no backlight bleeding was present.

## ① 용어집 없이 (generic MT — 오역/불일치 발생) ❌

> 낮은 APL에서 **최고 밝기**는 1000 cd/m2에 도달했지만, **자동 밝기 제한기(ABL)**가 100% APL에서
> **지속 밝기**를 약 250 cd/m2로 낮췄다. ... 상단 영역에서 **얼룩(불균일)**과 2시간 정지 패턴 후
> 약간의 **이미지 고착**이 관찰되었고, 영구적인 **화면 번짐**은 없었다. ... **감마 커브**가 목표
> EOTF를 잘 따랐으나 니어블랙 영역에서 **검은색 뭉개짐**이 나타났다. ... **회색 대 회색(GtG)**
> 응답시간은 1 ms였으나 오버드라이브가 **과도 현상**을 유발했다. ... 시야각에서 축을 벗어나면
> **색 이동**이 측정되었고 ... **백라이트 출혈**은 없었다.

**문제점**: 밝기/휘도 혼동, "이미지 고착"·"화면 번짐"(잔상↔번인 혼동), "검은색 뭉개짐"·"과도 현상"·
"색 이동"·"백라이트 출혈" 등 비표준·직역 오류. 같은 개념을 문서마다 다르게 표기.

## ② 용어집 주입 후 (표준 표기 강제) ✅

> 낮은 APL에서 **최대휘도**는 1000 cd/m²에 도달했지만, **자동 밝기 제한(ABL)**이 100% APL에서
> **지속 휘도**를 약 250 cd/m²로 낮췄다. ... 상단 영역에서 **무라(얼룩)**와 2시간 정지 패턴 후
> 약간의 **잔상(image sticking)**이 관찰되었고, 영구적인 **번인(burn-in)**은 없었다. ... **감마 곡선**이
> 목표 EOTF를 잘 따랐으나 니어블랙 영역에서 **블랙 크러시(암부 뭉개짐)**가 나타났다. ...
> **그레이 투 그레이(GtG)** 응답속도는 1 ms였으나 오버드라이브가 **오버슈트(역잔상)**를 유발했다. ...
> 시야각에서 축을 벗어나면 **색편이(color shift)**가 측정되었고 ... **빛샘(backlight bleeding)**은 없었다.

---

## 개선 요약 (교정된 용어)

| 원어 | ① generic (오역) | ② 주입 후 (표준) | 근거(용어집) |
|------|------------------|------------------|--------------|
| Peak luminance | 최고 밝기 | **최대휘도** | PQ-005 |
| Sustained luminance | 지속 밝기 | **지속 휘도** | PQ-126 |
| Auto brightness limiter | 자동 밝기 제한기 | **자동 밝기 제한(ABL)** | PQ-125 |
| Mura | 얼룩(불균일) | **무라(얼룩)** | PQ-026 |
| Image sticking | 이미지 고착 | **잔상** | PQ-027 |
| Burn-in | 화면 번짐 | **번인** | PQ-028 |
| Gamma curve | 감마 커브 | **감마 곡선** | PQ-086 |
| Black crush | 검은색 뭉개짐 | **블랙 크러시(암부 뭉개짐)** | PQ-130 |
| Gray-to-gray | 회색 대 회색 | **그레이 투 그레이** | PQ-036 |
| Overshoot | 과도 현상 | **오버슈트(역잔상)** | PQ-135 |
| Color shift | 색 이동 | **색편이** | PQ-015 |
| Backlight bleeding | 백라이트 출혈 | **빛샘** | PQ-148 |

**결과**: 12개 핵심 용어에서 오역·비표준·직역을 표준 표기로 교정. 잔상↔번인처럼 의미가 다른 용어의
혼동을 방지하고, 문서 전체에서 표기 일관성을 확보.

## 재현 방법

```bash
# 1) 원문에서 관련 용어 탐지 → system prompt 생성
python3 scripts/build_glossary_prompt.py --source eval/sample_idms_en.txt --full-prompt

# 2) 커버리지·오역위험 지표 측정
python3 scripts/eval_coverage.py --source eval/sample_idms_en.txt
```
생성된 system prompt를 LLM에 주입하고 원문을 함께 전달하면 위 ②와 같은 표준 표기 번역을 얻는다.
