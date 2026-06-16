# 네거티브 · 디자인 조건어 · 모델 약점 회피 · 벡터화

## 추천 네거티브 프롬프트 (항상 첨부)

```
no 3D mockup, no realistic photo, no complex background, no stock logo, no generic icon,
no excessive gradients, no tiny details, no unreadable text, no watermark, no shadow-heavy design,
no complicated illustration, no neon glow, no cool pure-white if brand uses warm tone
```

브랜드 `DESIGN.md`에 금지 항목이 있으면 거기에 더한다(예: MAGMA — 네온·요란한 그라데이션·차가운 순백·과장 금지).

## 디자인 조건어 사전 (추상어 대체)

| ❌ 추상어 | ✅ 디자인 조건어 |
|---|---|
| beautiful / cool / stylish | flat vector, clean, refined |
| simple | strong silhouette, minimal strokes, geometric |
| works everywhere | scalable, favicon-ready, app-icon-ready |
| not cluttered | balanced negative space, generous margins |
| professional | professional brand identity, editorial |
| modern | geometric, structured, node/grid motif |

## 모델 글자 약점 회피

- text-to-image 모델은 **글자 철자·자간**이 불안정하다. 워드마크는 컨셉 탐색용으로만.
- 안정 순위: **추상 마크 > 모노그램(글자 1) > 워드마크**. 시연·빠른 확정엔 글자 적은 쪽.
- 워드마크를 꼭 뽑아야 하면 단어를 짧게(브랜드명만), 그리고 철자를 **사람이 확인**한 뒤 깨졌으면 벡터에서 글자를 다시 친다.
- 프롬프트에 `no extra letters, no unreadable text`를 넣어 잡스러운 글자 생성을 줄인다.

## 생성 운영

- **방향당 2~4장**을 뽑는다(비결정성 인정). 한 장에 의존하지 않는다.
- 기본 정사각 1:1(워드마크는 가로형 1종 추가 가능).
- 배경은 단색(흰/투명/브랜드 bg). 사진·씬·목업 금지.
- 헤르메스: 빌트인 `image_generate`(프로필 config `image_gen.provider`, 예: gpt-image-2 via Codex OAuth). Claude 환경: `kie-image-generator` 등. 생성 도구는 환경에 맞게, 프롬프트 규율은 동일.

## 벡터화 인계 (확정 단계)

1. 평가 체크리스트 통과 안 2~3개 선별.
2. 래스터(PNG)를 Figma/Illustrator/Canva로 가져가 **벡터로 재제작**(트레이싱이 아니라 형태를 다시 그림).
3. 글자·폰트를 정식 폰트로 교체(워드마크), 컬러를 정확한 hex로 고정.
4. 파비콘·앱 아이콘·프로필 크기로 축소 테스트(16/32/512px).
5. 확정본·컬러·폰트 시스템을 브랜드 `DESIGN.md`에 반영(단일 진실원천 갱신).

> 원칙: AI 이미지는 **방향·심볼 탐색**에 쓰고, **확정 자산은 벡터**로 만든다. 이 분업이 품질과 일관성을 동시에 잡는다.
