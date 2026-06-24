# Design Tokens — 단테랩스 v1.1 (Brand Intel Web Report 전용)

## 7 색 팔레트

| 토큰           | Hex       | 역할                      | 사용 위치                                   |
| -------------- | --------- | ------------------------- | ------------------------------------------- |
| `paper`        | `#F7F2E6` | 캔버스 배경               | body bg                                     |
| `paper.soft`   | `#EDE7D7` | 비네팅 끝                 | secondary section                           |
| `paper.strong` | `#FCF9F0` | 카드 surface              | `.dl-card` bg + self row                    |
| `ink`          | `#1a1a1a` | 본문 텍스트               | 헤드라인·본문                               |
| `ink.soft`     | `#3a3a3a` | 서브타이틀                | 부제·table data                             |
| `ink.muted`    | `#6a6a6a` | 메타                      | caption                                     |
| `rust`         | `#A0522D` | 메인 액센트               | KPI delta · self row stripe · primary chart |
| `rust.deep`    | `#7C3F22` | hover/active variant      | button hover                                |
| `slate2`       | `#435B6C` | cool dyad 액센트          | secondary chart · slate badge               |
| `slate2.deep`  | `#3E5E75` | hover/active variant      | link hover                                  |
| `sepia`        | `#8B6F47` | 메타 텍스트               | text-meta · footer                          |
| `amber2`       | `#C9A857` | success 배지              | factCheck verified                          |
| `mark2`        | `#EBC65B` | 형광펜 하이라이트         | `.dl-mark` 배경 그라데이션                  |
| `link`         | `#5B7F99` | 본문 링크 (≥24px or ≥700) | nav hover                                   |

## 절대 비율 60/30/10

- 60% paper (배경)
- 30% ink (텍스트)
- 10% **rust + slate + amber + mark 합쳐서** — 단일 액센트가 화면의 3% 초과 금지

## 타이포

| 토큰        | Family                         | Use                                            |
| ----------- | ------------------------------ | ---------------------------------------------- |
| `editorial` | Nanum Myeongjo + Noto Serif KR | 헤드라인 (type-display, type-hero, type-h1)    |
| `serif`     | Noto Serif KR                  | 본문 (type-body, type-h2, type-h3, type-small) |
| `sans`      | Pretendard Variable            | UI 라벨 (type-meta, num-tabular)               |
| `mono`      | JetBrains Mono / D2Coding      | 인라인 코드                                    |

## Spacing / Radius / Shadow

- spacing: 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 96 (xs~xl 별칭)
- radius: none / sm 2 / md 4 / lg 8 (8 초과 금지)
- shadow: ink-tint 만 (`rgba(26,26,26,...)`) — 컬러 드롭섀도 금지
- `emboss`: `inset 0 1px 0 rgba(255,255,255,0.5), 0 12px 32px -16px rgba(26,26,26,0.18)`
- `card`: `0 12px 32px -16px rgba(160,82,45,0.18)` (rust hover only)
