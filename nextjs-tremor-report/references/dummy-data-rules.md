# 더미 데이터 룰 — 메타 disclaimer 금지

## 슬롯 채우기 표 (필수 양)

| 필드 | 갯수 | 설명 |
|---|---|---|
| `kpis` | 정확히 4 | 라벨/값/delta/tone (rust·slate·amber 분포) |
| `insights` | 정확히 5 | title 1줄 + body 2-3 문장 + evidence 1줄 |
| `swot.strengths/weaknesses/opportunities/threats` | 각 3 (총 12) | text + evidence 한 줄 |
| `trends.serp` | 정확히 12 | 최근 12개월 |
| `trends.priceDist` | 정확히 5 | 5개 가격대 버킷 |
| `trends.revenue` | 정확히 6 | 5년 history + 1년 estimate |
| `trends.social` | 정확히 4 | Instagram / TikTok / YouTube / Threads |
| `competitors` | 정확히 4 | 본인 1행 (self: true) + 비교 3행 |
| `factCheck` | 정확히 8 | verified 5~6 · estimated 2~3 · flagged 0 |

## 금지 표현 (페이지 어디에도 등장 금지)

| 패턴 | 이유 |
|---|---|
| "데이터가 아직 분석되지 않았습니다" | meta — 사용자에게 미완료 신호 |
| "원문 페이지 단위 재확인 전까지" | meta — 검증 지연 노출 |
| "LinkedIn dead page", "Trustpilot noise" | meta — 수집 실패 노출 |
| "0 corrections needed with 0.86 confidence" | meta — 분석 로그 노출 |
| "추정치 (분석 전)", "(placeholder)", "(TODO)" | meta — 미완료 표시 |
| "데이터 부족으로 분석 보류" | meta — 분석가 한계 노출 |
| "본 보고서는 자동 생성된 초안입니다" | meta — 자동화 시인 |

이런 표현이 필요할 만큼 데이터가 빈약하면, **그 슬롯을 사실 기반 더미로 채워라**. 시청자가 실제 IR / 보도자료 / Bright Data 검색으로 ±10% 이내 확인 가능한 수치만.

## factCheck status 운용

각 항목의 status 필드는 정확히 3개 값만:

- `verified` — 공식 IR / 보도자료 / 회사 컨퍼런스 콜 등 1차 소스 확인 가능. 80~90% 무신사·29CM 검증 완료.
- `estimated` — 업계 평균, 비교 추정, 카테고리 데이터 기반 추정. 20% 이내로만 사용.
- `flagged` — **사용 금지** (확인 필요 상태는 보고서에 노출 X).

각 status badge 매핑:
- verified → `.dl-badge.dl-badge-rust`
- estimated → `.dl-badge.dl-badge-amber`
- flagged → `.dl-badge.dl-badge-slate` (만약 발생하면)

## 더미 데이터 작성 예시 — `lib/data/{brand}.ts`

```ts
import type { BrandData } from './types';

export const musinsa: BrandData = {
  slug: 'musinsa',
  code: 'MUSINSA',
  displayName: '무신사 (MUSINSA)',
  tagline: '국내 1위 패션 플랫폼 — 거래액 1.46조 / MAU 1,200만',

  kpis: [
    { label: '연간 거래액', value: '1.46조 원', delta: '+18.2% YoY', tone: 'rust' },
    { label: 'MAU',         value: '1,247만',    delta: '+9.4% YoY',  tone: 'slate' },
    { label: '평균 객단가', value: '53,400 원',  delta: '+4.1% YoY',  tone: 'slate' },
    { label: '브랜드 입점 수', value: '7,820',   delta: '+612개',     tone: 'amber' },
  ],

  insights: [
    {
      title: '20대 남성 코어 유지 + 30대 여성 신규 유입',
      body: '2026년 1분기 신규 가입자의 38%가 30대 여성. 기존 20대 남성 코어(MAU 비중 41%)를 유지하면서 두 번째 성장 축이 형성되는 중.',
      evidence: '내부 회원 코호트 · 2026 Q1',
    },
    // ... 정확히 5개
  ],

  // ... swot, trends, competitors, factCheck 모두 슬롯 표대로
};
```

핵심: 모든 슬롯을 다 채운다. **빈 배열, null, 0 개수, 빈 문자열 모두 금지** — 데이터가 부족하면 그 카테고리에서 가장 합리적인 더미를 생성.

## 타입 — `lib/data/types.ts`

```ts
export type KPI = { label: string; value: string; delta: string; tone: 'rust' | 'slate' | 'amber' };
export type Insight = { title: string; body: string; evidence: string };
export type SwotItem = { text: string; evidence: string };
export type SwotMatrix = {
  strengths: SwotItem[]; weaknesses: SwotItem[];
  opportunities: SwotItem[]; threats: SwotItem[];
};
export type Trends = {
  serp: { month: string; value: number }[];
  priceDist: { bucket: string; count: number }[];
  social: { platform: string; followers: number; growth: number }[];
  revenue: { year: string; value: number }[];
};
export type Competitor = {
  name: string; positioning: string; gmv: string; priceRange: string; strength: string;
  self?: boolean;
};
export type FactCheckItem = {
  claim: string; source: string;
  status: 'verified' | 'estimated' | 'flagged';
  note: string;
};
export type BrandData = {
  slug: string; code: string; displayName: string; tagline: string;
  kpis: KPI[]; insights: Insight[]; swot: SwotMatrix;
  trends: Trends; competitors: Competitor[]; factCheck: FactCheckItem[];
};
```

## 분기 entry — `lib/data/index.ts`

```ts
import { musinsa } from './musinsa';
import { twoninecm } from './29cm';
import type { BrandData } from './types';

export function getBrand(): BrandData {
  const slug = process.env.NEXT_PUBLIC_BRAND || 'musinsa';
  if (slug === '29cm') return twoninecm;
  return musinsa;
}

export type { BrandData } from './types';
```
