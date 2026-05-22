---
name: nextjs-tremor-report
description: Brand Intelligence Lab 의 임원 보고용 시장조사 보고서를 Marp 정적 PDF 대신 Next.js 15 + Tailwind + ECharts 인터랙티브 웹앱으로 빌드해 Vercel 에 배포한다. 단테랩스 paper+ink+rust+slate 디자인 토큰을 Tailwind config 로 강제하고, 5 페이지(홈/SWOT/차트/팩트체크/경쟁사) 표준 구조 · 더미 데이터 컨벤션 · 메타 disclaimer 금지 · ECharts 4종(SerpChart/PriceDistChart/RevenueChart/SocialChart) 패턴을 모두 강제한다. 슬라이드 제작자 에이전트가 깨어날 때마다 이 스킬을 켜고, 분석가 산출물 5종을 받아 동일한 완성도의 보고서를 빌드한다.
---

# nextjs-tremor-report

브랜드 시장조사 보고서를 **단테랩스 디자인 토큰을 적용한 인터랙티브 웹 보고서**로 빌드해 Vercel 에 배포한다. 본 스킬을 그대로 따르면 무신사 / 29CM / 임의 브랜드 모두 동일한 시각 완성도가 나오는 것이 목표다.

## 절대 규칙 (Hard Contract)

1. **빌드는 로컬 SSD (`/tmp/{brand}-report-app`) 에서** 한다. SMB/NAS 마운트된 워크스페이스에서 `npm install` 을 돌리면 17분+ 걸리고 멈춘 것처럼 보인다. 빌드 산출물만 다시 워크스페이스로 복사.
2. **VERCEL_API_TOKEN 은 컨테이너 `.env` 또는 docker-compose `environment:` 블록에서만 주입**한다. paperclip 콘솔의 Secrets 패널은 `codex_local` 어댑터 heartbeat 프로세스 env 로 전파되지 않는다 (2026-05 기준). spawn-time 검증: `printenv | grep VERCEL_API_TOKEN` 가 비어있지 않아야 빌드 시작.
3. **메타 disclaimer 금지**. "데이터가 아직 분석되지 않았습니다", "원문 페이지 재확인 전까지", "LinkedIn dead page", "Trustpilot noise", "0 corrections needed with 0.86 confidence" 같은 메타 정보는 어떤 페이지에도 나오지 않는다. 사실 기반 더미 데이터로 모든 슬롯을 가득 채운 완성된 보고서로 보이게 한다.
4. **5 페이지 정확 구조**. 홈 / SWOT / 차트 / 팩트체크 / 경쟁사 — 그 외 페이지 추가 금지. 부족한 데이터는 dummy 로 채우되 위 §3 규칙을 따른다.
5. **단테랩스 토큰만**. paper #F7F2E6 / ink #1a1a1a / rust #A0522D / slate #435B6C / sepia #8B6F47 / amber #C9A857 / mark #EBC65B. 그 외 색 (회색, 코발트, 인디고 등 임의 색) 금지. 강조는 rust 또는 yellow `dl-mark` 형광 하이라이트만.
6. **본문은 Noto Serif KR, 헤드라인은 Nanum Myeongjo, UI 라벨은 Pretendard Variable**. 본문에 sans-serif 금지. 이모지 금지.
7. **챕터 배지 금지**. 좌하단/우상단의 "CHAPTER 23 · BRAND INTEL" 같은 시그니처 마크 추가 금지 (요청 시 예외).
8. **빌드 검증 통과 후에만 deploy**. `npm run build` 성공 → production deploy.

## 언제 쓰나

- Brand Intelligence Lab 의 **슬라이드 제작자 (agent-3)** 가 분석가 산출물 5종 (`analysis/insights.md`, `analysis/swot_matrix.json`, `analysis/chart_spec.json`, `analysis/fact_check.md`, `analysis/cleaned_data.parquet`) 을 받아서 임원용 인터랙티브 보고서로 빌드할 때.
- 시청자가 `paperclipai company import https://github.com/dandacompany/brand-intelligence-lab` 한 회사의 슬라이드 제작자 capabilities 에 들어가 있으면 자동 적용.

## 사전 조건 검증 (스킵 금지)

```bash
node --version                                              # ≥ 20
which vercel || npm i -g vercel                             # CLI 존재
printenv | grep -E 'VERCEL_API_TOKEN'                       # 비어있지 않아야 함
[ -n "$VERCEL_API_TOKEN" ] || { echo "BLOCK: token missing — .env injection 필요"; exit 1; }
```

검증 실패 시 paperclip 코멘트로 `BLOCK: VERCEL_API_TOKEN missing in heartbeat env — 호스팅어 hPanel Docker Manager → paperclip-{slug} → .env 편집 후 컨테이너 재시작` 보고하고 즉시 정지.

## 빌드 절차

### 1. 로컬 SSD 스캐폴딩

```bash
BRAND={brand}                                               # musinsa | 29cm
APP=/tmp/${BRAND}-report-app
rm -rf "$APP" && mkdir -p "$APP" && cd "$APP"
```

`package.json` (수동 작성 — `create-next-app` 의 대화형/네트워크 회피로 ~2분 단축):

```json
{
  "name": "brand-intel-${BRAND}",
  "version": "0.1.0",
  "private": true,
  "scripts": { "dev": "next dev", "build": "next build", "start": "next start" },
  "dependencies": {
    "next": "^15.0.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "echarts": "^5.5.0",
    "echarts-for-react": "^3.0.2"
  },
  "devDependencies": {
    "@types/node": "^22",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "typescript": "^5",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0"
  }
}
```

추가 파일 4종: `tsconfig.json`, `next.config.ts` (env NEXT_PUBLIC_BRAND 분기 포함), `postcss.config.mjs`, `tailwind.config.ts`. 정확한 본문은 `references/scaffold-files.md` 참조 — 그대로 복사.

### 2. 단테랩스 디자인 토큰 — `tailwind.config.ts`

`references/design-tokens.md` 의 token 표를 Tailwind theme 에 등록한다. 핵심:

- `colors`: paper {DEFAULT/soft/strong}, ink {DEFAULT/soft/muted}, rust {DEFAULT/deep}, slate2 {DEFAULT/deep}, sepia, amber2, mark2, link
- `fontFamily`: editorial (Nanum Myeongjo + Noto Serif KR), serif (Noto Serif KR), sans (Pretendard Variable), mono (JetBrains Mono)
- `borderRadius`: none / sm 2px / md 4px / lg 8px (8 초과 금지)
- `boxShadow`: emboss (헤어라인 inset + soft drop, ink-tint 만), card (rust hover 셰도)

### 3. `app/globals.css` — 타이포 클래스 + 시그니처 컴포넌트

`references/globals-css.md` 그대로 사용. 포함되는 클래스:
- `.type-display` / `.type-hero` / `.type-h1~h3` / `.type-body` / `.type-small` / `.type-meta` / `.num-tabular`
- `.ledger-hairline` — top/bottom 1px border (헤더·푸터 시그니처)
- `.edge-mark` — 절대 위치 메타 라벨 (좌상단 SESSION · 우상단 BRAND CODE)
- `.rust-stripe` — 좌측 4px rust accent stripe
- `.dl-card` — 카드 surface + hover 셰도
- `.dl-badge` / `.dl-badge-rust` / `.dl-badge-slate` / `.dl-badge-amber`
- `.dl-mark` — 노란 형광펜 하이라이트 (배경 그래디언트, 절대 underline 사용 금지)

### 4. 5 페이지 정확 구조

`references/page-blueprints.md` 의 5 페이지 spec 그대로. 각 페이지 헤더는 `<div className="type-meta">PAGE · {LABEL}</div>` + `<h1 className="type-hero">{브랜드명} · {타이틀}</h1>` 패턴 유지.

| 페이지 | 컴포넌트 | 데이터 소스 |
|---|---|---|
| `app/page.tsx` (홈) | KPI 4 card (rust-stripe) + Key Insights 5 (ledger-hairline grid 12) | `kpis[]`, `insights[]` |
| `app/swot/page.tsx` | 2×2 quadrant Card grid (S/W/O/T), 각 카드 좌측에 거대 글자 마크 (rust/slate 교차) | `swot.{strengths,weaknesses,opportunities,threats}[]` |
| `app/charts/page.tsx` | 2×2 chart grid — SerpChart / PriceDistChart / RevenueChart / SocialChart | `trends.{serp,priceDist,revenue,social}[]` |
| `app/fact-check/page.tsx` | 헤더 callout (검증 N건 `dl-mark` 강조) + 4열 table (주장/출처/상태 badge/비고) | `factCheck[]` |
| `app/competitors/page.tsx` | 5열 table — self 행은 rust-stripe + bg-paper-strong + "SELF" 메타 | `competitors[]` |

### 5. ECharts 4종 차트 컴포넌트 — `components/Charts.tsx`

`references/charts-component.md` 그대로. SVG 렌더러 사용 (`opts={{ renderer: 'svg' }}`). 색 팔레트는 rust/slate 2색만, 배경은 paper. 4종 모두 baseGrid (left 56, right 24, top 24, bottom 36) + baseAxis (border dashed splitLine, Pretendard 라벨 11px muted) 동일 적용.

### 6. 더미 데이터 — `lib/data/{brand}.ts`

`references/dummy-data-rules.md` 의 룰을 따른다. 핵심:

- **메타 disclaimer 절대 금지** — "데이터가 아직 분석 안 됨", "원문 페이지 재확인 전까지", "추정치 / 부분 데이터" 같은 표기 없음
- **모든 슬롯을 채운다** — KPI 4, Insight 5, SWOT 각 사분면 3 (총 12), 차트 serp 12점 / priceDist 5 / revenue 6 / social 4, competitors 4, factCheck 8
- **사실 기반 더미** — 공식 IR, 보도자료, Bright Data 데이터셋에서 실제 확인 가능한 수치만. 시청자가 검증해도 실제 값 ±10% 이내.
- **factCheck status 분포** — verified 5~6 · estimated 2~3 · flagged 0. status badge 는 dl-badge-rust / dl-badge-amber / dl-badge-slate 순.

### 7. 빌드 → Vercel deploy

```bash
cd /tmp/${BRAND}-report-app
npm install --no-audit --no-fund --legacy-peer-deps          # ~10초 (SSD)
NEXT_PUBLIC_BRAND=$BRAND npx next build                       # 5 페이지 정적 생성

export VERCEL_TOKEN="$VERCEL_API_TOKEN"
# 기존 프로젝트 연결 (대화형 회피 — project.json 직접 작성)
mkdir -p .vercel
curl -sS "https://api.vercel.com/v9/projects/brand-intelligence-${BRAND}" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  | python3 -c "import json,sys;d=json.load(sys.stdin);open('.vercel/project.json','w').write(json.dumps({'projectId':d['id'],'orgId':d['accountId']}))"

vercel deploy --prod --yes --token "$VERCEL_TOKEN" \
  --build-env NEXT_PUBLIC_BRAND=$BRAND \
  --env NEXT_PUBLIC_BRAND=$BRAND 2>&1 | tee /tmp/vercel-deploy.log

DEPLOY_URL=$(grep -oE 'https://[a-z0-9-]+\.vercel\.app' /tmp/vercel-deploy.log | tail -1)
```

### 8. 자가 검증 후 보고

```bash
curl -sI "$DEPLOY_URL" | head -1                             # HTTP/2 200
curl -s  "$DEPLOY_URL" | grep -oE "무신사|29CM|브랜드|SWOT" | sort -u
```

paperclip 코멘트에 다음 형식으로 보고:

```
배포 완료 — {BRAND}
URL: $DEPLOY_URL
페이지 5종: 홈 / SWOT / 차트 / 팩트체크 / 경쟁사
디자인 토큰: paper+ink+rust+slate (단테랩스 v1.1)
메타 disclaimer 0건 · 차트 4종 · KPI 4 · Insight 5 · factCheck 8
다음 owner: 단테 (URL 시청 후 코멘트로 OK/수정 요청)
```

## 자가 검증 체크리스트 (deploy 전)

| 검증 | Pass 기준 |
|---|---|
| `npm run build` 통과 | 5 페이지 모두 `○ (Static)` 표시 |
| `printenv \| grep VERCEL_API_TOKEN` | 비어있지 않음 |
| 임의 페이지 텍스트 검색 | "TODO" "placeholder" "lorem" "데이터 없음" "추정 전까지" 0건 |
| 색 팔레트 | tailwind.config.ts 의 7색만 등장 (rg "#[0-9A-Fa-f]{6}" app/ components/ lib/) |
| 폰트 | 본문 globals.css 가 `font-family: 'Noto Serif KR'` 로 시작 |
| 이모지 | `rg "[\U0001F300-\U0001F9FF]" app/ components/` 0건 |
| 챕터 배지 | `rg -i "chapter\|episode\|session ·" app/` 0건 (요청 시 예외) |

체크 실패 시 deploy 중단 → 항목 수정 후 재실행.

## 트러블슈팅

| 증상 | 원인 | 조치 |
|---|---|---|
| `next: command not found` | install 실패 또는 PATH 누락 | `npx next build` 로 직접 호출 |
| `npm install` 17분+ 진행 | SMB 마운트 (`/Volumes/...` 또는 `/paperclip/...`) 에서 small file IO 병목 | `/tmp/{brand}-report-app` 로 옮겨서 install |
| Vercel `Not Authorized` (401) | token 만료 또는 invalid | 새 토큰 발급 → 컨테이너 `.env` 갱신 → 컨테이너 재시작 |
| 한글 □□ 깨짐 | tailwind config 의 font-serif 미설정 또는 폰트 import 누락 | `globals.css` 에 `@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR...')` 확인 |
| 차트 SSR 에러 | echarts 가 window 참조 | `next/dynamic` 으로 `ReactECharts` 를 `ssr: false` 로 감싸기 |

## References

- `references/design-tokens.md` — 7색 + 타이포 + spacing/radius/shadow 토큰 표 (그대로 복사 가능)
- `references/scaffold-files.md` — package.json / tsconfig / next.config / postcss / tailwind.config 전체 본문
- `references/globals-css.md` — 타이포 클래스 + dl-card / dl-badge / ledger-hairline / rust-stripe 전체 CSS
- `references/page-blueprints.md` — 5 페이지 각 tsx 본문 템플릿
- `references/charts-component.md` — ECharts 4종 컴포넌트 본문
- `references/dummy-data-rules.md` — 메타 disclaimer 금지 룰 + 슬롯 채우기 표 + factCheck status 분포

## Source of truth

- 캐노니컬 구현: https://github.com/dandacompany/dante-skills/tree/main/nextjs-tremor-report
- 미러: https://github.com/dandacompany/brand-intelligence-lab/tree/main/skills/dandacompany/dante-skills/nextjs-tremor-report
- 검증된 배포: https://brand-intelligence-musinsa.vercel.app · https://brand-intelligence-29cm.vercel.app
