# 프롬프트 공식 · 템플릿 · 예시

## 프롬프트 공식

> 브랜드 정체성 + 업종 + 고객층 + 키워드 + 심볼 방향 + 형태 스타일 + 색상(정확한 hex) + 금지 요소 + 출력 조건

추상어("beautiful·cool")는 빼고, 디자인 조건어(flat vector·strong silhouette·scalable·negative space)로 채운다. 색상은 "브랜드 색"이 아니라 정확한 hex로 "X ink on Y background". 네거티브는 항상 첨부(`negative-and-craft.md`).

---

## 1. 영문 템플릿 (이미지 모델 직접 입력용 · 권장)

대괄호를 채워 그대로 쓴다. 정사각 1:1, 방향당 2~4장.

```
Professional brand logo concept. [logo type: symbol mark / abstract mark / lettermark monogram / emblem].
Brand: [brand name], [industry]. Audience: [target]. Personality: [3 adjectives].
Concept metaphor: [one metaphor]. Visual direction: [clean geometric / premium minimal / friendly modern / bold tech].
Colors: [main hex] ink on [bg hex] background, one [accent hex] accent only.
Style: flat vector, strong silhouette, balanced negative space, scalable, favicon-ready, professional brand identity.
Composition: centered single mark, generous margins, high contrast, [white / transparent / parchment] background.
Negative: no 3D, no mockup, no photo, no gradient, no glow, no shadow, no stock-logo feeling,
no generic icon, no tiny details, no unreadable text, no watermark, no complex background.
— square 1:1
```

## 2. 한국어 지시 템플릿 (에이전트에게 시킬 때)

```
너는 시니어 브랜드 아이덴티티 디자이너이자 로고 아트디렉터다.
바로 이미지를 만들지 말고, 먼저 브리프(brief-and-eval.md 10항목)를 정리한 뒤 아래 정보로 최종 프롬프트 3~5개를 영문으로 써라.

브랜드명: [브랜드명]
업종/서비스: [업종]
타깃 고객: [타깃]
브랜드 성격: [지적·신뢰·미니멀·미래·친근·프리미엄 중]
핵심 키워드: [3~7개]
로고 유형: [심볼형/추상/레터마크/엠블럼/앱 아이콘]
시각 방향성: [깔끔한 기하 심볼/모던 테크/프리미엄 미니멀/친근 모던]
선호 색상: [정확한 hex — DESIGN.md 있으면 그 토큰]
피하고 싶은 색상: [hex]
반드시 반영할 은유/형태: [상징]
피해야 할 요소: 흔한 아이콘, 클리셰, 복잡한 디테일, 3D 목업, 과한 그림자/그라데이션, 스톡 로고 느낌, 읽기 어려운 글자

디자인 조건: 단순·확장성(파비콘·앱 아이콘·프로필) · 강한 실루엣 · 플랫 벡터 · 균형 잡힌 여백 · 흰/투명/단색 배경 · 목업·사진·3D 금지
```

## 3. 4방향 변형 (한 브랜드를 여러 각도로)

같은 브랜드를 서로 다른 4방향으로 뽑아 비교한다.

1. **미니멀 기하** — minimal geometric symbol, clean straight strokes, mathematical balance.
2. **프리미엄 추상** — premium abstract mark, refined editorial, restrained luxury feel.
3. **친근 모던** — friendly modern, soft rounded geometry, approachable.
4. **강한 테크** — bold tech-oriented, structured, node/grid motif, confident.

## 4. 유형별 안정성 메모

- **추상 심볼(글자 0)** — 가장 안정적. 시연·빠른 확정에 적합.
- **모노그램(글자 1)** — 안정적. 브랜드 이니셜 한 글자를 기하 형태로.
- **워드마크(전체 글자)** — 철자 깨짐 위험. 컨셉 탐색용으로만 쓰고 확정은 벡터 후처리.

## 5. 예시 — AI/교육/자동화 브랜드(단테랩스류)

키워드: intelligent · modular · agentic · automation · learning system · data flow · human-AI collaboration · node-based symbol · minimal tech identity.

```
A minimal geometric logo symbol for an AI automation education brand, representing human-AI
collaboration, modular agents, data flow, and structured knowledge. Clean node-based symbol,
modern Korean tech brand identity, flat vector, strong silhouette, favicon-ready, premium but
approachable, white background. Negative: no text, no 3D, no mockup, no gradient, no shadow.
— square 1:1
```

## 6. 예시 — MAGMA(3040 남성 패션 · DESIGN.md 토큰 고정)

`~/.hermes/profiles/mia/DESIGN.md`: primary 딥틸 `#0F595E`, accent 테라코타 `#C05621`, bg 파치먼트 `#F4F1EA`, 로고타입 Noto Serif KR(넓은 자간), 60/30/10, 금지(네온·요란한 그라데이션·차가운 순백·과장).

- **추상 심볼(권장)**: 마그마가 식어 굳은 지층 모티프.
```
Minimal abstract brand symbol: a calm horizontal strata / layered earth motif evoking "magma"
cooled into solid ground, geometric, deep teal (#0F595E) with one terracotta (#C05621) layer,
on warm parchment (#F4F1EA). Flat vector icon, centered, generous negative space, mature and
restrained, Korean editorial mood for men in their 30s-40s. Negative: no gradient, no neon,
no 3D, no photo, no letters, no shadow. — square 1:1
```
- **모노그램 'M'**:
```
Minimal geometric lettermark of capital "M" built from clean straight strokes suggesting a calm
mountain/strata silhouette, deep teal (#0F595E), single terracotta (#C05621) accent edge, on
parchment (#F4F1EA). Flat vector emblem, centered, lots of negative space, scalable. Negative:
no gradient, no 3D, no neon, no photo, no text, no shadow. — square 1:1
```
- **워드마크(탐색용, 확정은 벡터)**:
```
Minimal editorial wordmark "MAGMA" in a refined serif with wide letter-spacing, deep teal
(#0F595E) ink on warm parchment (#F4F1EA), one small terracotta (#C05621) accent mark. Flat
vector, centered, high contrast. Negative: no gradient, no 3D, no glow, no photo, no extra
letters, no shadow. — square 1:1
```
