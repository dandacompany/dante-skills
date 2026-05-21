---
name: nextjs-tremor-report
description: Brand Intelligence Lab 의 임원 보고용 시장조사 보고서를 Marp 정적 PDF 대신 Next.js + shadcn/ui + Tremor + ECharts 인터랙티브 웹앱으로 빌드해 Vercel 에 배포한다. 단테랩스 paper+ink+rust 디자인 토큰을 Tailwind config 로 강제하고, Vercel deploy hook 으로 단테가 즉시 URL 확인 가능.
---

# nextjs-tremor-report

브랜드 시장조사 보고서를 **인터랙티브 웹 보고서**로 빌드해 Vercel 에 배포한다.<br>
Marp 정적 PDF 대비 다음 가치를 추가한다.

- **인터랙티브 차트** — Tremor (간단한 KPI/면적/막대) + ECharts (복잡한 지리·네트워크·트리맵)
- **shadcn/ui 컴포넌트** — Card, Tabs, Sheet, Accordion 으로 슬라이드 흐름 → 임원 대시보드
- **반응형** — 모바일·태블릿·노트북에서 모두 잘 보임
- **고유 URL** — Vercel 배포 URL 로 단테가 슬랙·이메일에 바로 공유 가능
- **한글 폰트** — Tailwind config 에서 `font-serif: "Noto Serif KR"` 명시. □□ 함정 0건

## 언제 쓰나

- Brand Intelligence Lab 의 **슬라이드 제작자 (engineer)** 가 분석가 산출물 5종 (`insights.md`, `swot_matrix.json`, `chart_spec.json`, `fact_check.md`, `cleaned_data.parquet`) 을 받아서 임원용 인터랙티브 보고서로 빌드할 때.
- 시청자가 `paperclipai company import` 한 회사의 슬라이드 제작자 capabilities 에 들어가 있으면 자동 적용.

## 사전 조건

| 항목 | 확인 명령 | 비고 |
|------|---------|-----|
| Node.js ≥ 20 | `node --version` | hvps-paperclip 이미지 기본 만족 |
| Vercel CLI | `vercel --version` | `npm i -g vercel` (setup.sh 가 처리) |
| `VERCEL_API_TOKEN` | `echo ${VERCEL_API_TOKEN:0:8}***` | paperclip company secrets 에 등록 → 에이전트 런타임에 환경변수로 주입됨 |
| Vercel 계정 + 프로젝트 | 콘솔에서 1회 생성 | 첫 빌드 후 자동 생성도 가능 |

## 빌드 절차

### 1. 프로젝트 스캐폴딩

```bash
WS=/workspace/{BRAND}
cd $WS
mkdir -p report-app && cd report-app

# Next.js 15 + App Router + Tailwind + shadcn/ui 초기화
npx create-next-app@latest . --typescript --tailwind --app --no-src-dir --import-alias "@/*" --yes
npx shadcn@latest init --yes --base-color slate --css-variables true
npx shadcn@latest add card tabs accordion sheet button badge separator --yes

# Tremor + ECharts
npm i @tremor/react echarts echarts-for-react
```

### 2. Tailwind config — 단테랩스 디자인 토큰

```ts
// tailwind.config.ts 의 theme.extend
colors: {
  paper: "#F7F2E6",
  ink:   "#1a1a1a",
  rust:  "#A0522D",
},
fontFamily: {
  serif: ["Noto Serif KR", "Noto Serif CJK KR", "serif"],
  sans:  ["Noto Sans KR", "Noto Sans CJK KR", "system-ui", "sans-serif"],
},
```

`app/layout.tsx` 의 `<body className="font-serif bg-paper text-ink">` 로 본문 기본 serif. 좌측 4px rust accent stripe 는 `border-l-4 border-rust pl-4` 로 컴포넌트별 강조.

### 3. 페이지 구성 (분석가 산출물 → 컴포넌트 매핑)

| 분석가 산출물 | 페이지/컴포넌트 |
|--------------|----------------|
| `insights.md` 핵심 인사이트 5 | `app/page.tsx` 상단 Card 5개 (Tremor `<Metric>` + `<Text>`) |
| `swot_matrix.json` | `app/swot/page.tsx` — 2×2 Card grid (Strengths/Weaknesses/Opportunities/Threats) |
| `chart_spec.json` 차트 4~6개 | Tremor `<BarChart>`, `<LineChart>`, `<DonutChart>` 또는 ECharts `<ReactECharts>` (복잡 차트) |
| `fact_check.md` | `app/fact-check/page.tsx` — Accordion (각 인용 출처 + 재검증 결과) |
| `competitor_matrix_normalized.csv` | `app/competitors/page.tsx` — shadcn `<Table>` + 정렬·필터 |

### 4. Vercel 배포

```bash
# 빌드 검증 (로컬)
npm run build

# Vercel 배포 (production)
export VERCEL_TOKEN="$VERCEL_API_TOKEN"
vercel link --yes --token "$VERCEL_TOKEN" --project brand-intelligence-{BRAND}
vercel deploy --prod --yes --token "$VERCEL_TOKEN" 2>&1 | tee /tmp/vercel-deploy.log

# 배포 URL 추출
DEPLOY_URL=$(grep -oE 'https://[a-z0-9-]+\.vercel\.app' /tmp/vercel-deploy.log | tail -1)
echo "$DEPLOY_URL"
```

### 5. 자가 검증 + paperclip 코멘트

```bash
# HTTP 200 + 한글 정상 표시 확인
curl -sI "$DEPLOY_URL" | head -1                                       # HTTP/2 200
curl -s  "$DEPLOY_URL" | grep -oE "무신사|29CM|브랜드" | sort -u        # 한글 토큰 확인
```

paperclip 코멘트에 다음을 보고:

```
사용 도구: Next.js 15 + shadcn/ui + Tremor + ECharts + Vercel

| 항목 | 값 |
|---|---|
| 배포 URL | https://brand-intelligence-musinsa-xxxx.vercel.app |
| 페이지 수 | 5 (홈 / SWOT / 차트 / 팩트체크 / 경쟁사) |
| 차트 수 | 6 (Tremor 4 + ECharts 2) |
| 디자인 가드 위반 | 0건 (paper+ink+rust + Noto Serif KR) |
| Lighthouse | Performance ≥90, Accessibility ≥95 |
| 한글 표시 | ✓ (curl + 시각 점검) |
```

## 디자인 가드 (단테랩스)

| 토큰 | 값 |
|------|------|
| `paper` | `#F7F2E6` — 본문 배경 |
| `ink` | `#1a1a1a` — 본문 텍스트 |
| `rust` | `#A0522D` — 강조 (좌측 4px stripe, 링크, 차트 primary) |
| `font-serif` | Noto Serif KR (본문) |
| `font-sans` | Noto Sans KR (UI 컴포넌트) |
| corner radius | ≤ 8px |
| shadow | hard `shadow-[2px_2px_0_0_rgba(0,0,0,0.08)]` (컬러 드롭섀도 금지) |

**금지 패턴**: 글래스모피즘 · backdrop-filter · mesh gradient · 네온 · 이모지 · 사진 배경

## 절대 제약

- 데이터·문구 임의 가공 금지. 분석가 산출물 그대로 인용. 평가성 어휘 사용 금지 (`brand-research-glossary` + `report-evidence-citation` 스킬 참조).
- API 키 평문 노출 금지 (첫 8자 + ***). `VERCEL_API_TOKEN` 은 환경변수로만 사용, 코드/코멘트에 직접 적지 않는다.
- Vercel 프로젝트는 `brand-intelligence-{BRAND}` 명명 (BRAND=무신사·29CM 등).
- 배포 URL 은 코멘트에 반드시 명시. 단테가 즉시 검토 가능해야 한다.

## 시청자가 마주칠 가능성 있는 함정

| 함정 | 해결 |
|------|------|
| `vercel: not found` | `npm i -g vercel` (setup.sh 가 처리) |
| `VERCEL_API_TOKEN unset` | paperclip company → Settings → Secrets 에 등록. agent 런타임에서 자동 주입 |
| `Error: Project not found` | 첫 빌드 시 `vercel link --yes` 로 새 프로젝트 자동 생성 |
| 한글 □□ | Tailwind config 의 `font-serif: "Noto Serif KR"` 누락. 추가 후 재빌드 |
| Hydration mismatch | Tremor + ECharts 는 client component. 페이지 상단에 `"use client"` |
