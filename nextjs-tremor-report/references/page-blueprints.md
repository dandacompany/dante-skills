# 5 페이지 본문 블루프린트

각 페이지 파일을 그대로 복사. 변수는 `getBrand()` 한 곳에서만 분기.

## `app/layout.tsx`

```tsx
import './globals.css';
import type { Metadata } from 'next';
import Nav from '@/components/Nav';
import Footer from '@/components/Footer';
import { getBrand } from '@/lib/data';

const brand = getBrand();

export const metadata: Metadata = {
  title: `${brand.displayName} — Brand Intelligence Report`,
  description: `${brand.displayName} 시장조사·SWOT·경쟁사 분석 보고서. 단테랩스 Brand Intelligence Lab.`,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-paper text-ink">
        <div className="relative mx-auto max-w-[1280px] px-6 py-12">
          <span className="edge-mark" style={{ top: 16, left: 24 }}>SESSION · 2026 Q2</span>
          <span className="edge-mark" style={{ top: 16, right: 24 }}>{brand.code} · BRAND INTEL</span>
          <Nav />
          <main className="mt-10">{children}</main>
          <Footer />
        </div>
      </body>
    </html>
  );
}
```

## `components/Nav.tsx`

```tsx
import Link from 'next/link';
import { getBrand } from '@/lib/data';

const items = [
  { href: '/',            label: '홈',        meta: 'OVERVIEW' },
  { href: '/swot',        label: 'SWOT',      meta: 'STRATEGY' },
  { href: '/charts',      label: '차트',      meta: 'METRICS'  },
  { href: '/fact-check',  label: '팩트 체크', meta: 'EVIDENCE' },
  { href: '/competitors', label: '경쟁사',    meta: 'PEERS'    },
];

export default function Nav() {
  const brand = getBrand();
  return (
    <header className="ledger-hairline flex items-center justify-between">
      <Link href="/" className="flex items-baseline gap-3">
        <span className="type-meta">DANTE LABS · BRAND INTEL</span>
        <span className="type-h2">{brand.displayName}</span>
      </Link>
      <nav className="flex items-center gap-6">
        {items.map((i) => (
          <Link key={i.href} href={i.href} className="group flex flex-col items-end">
            <span className="type-meta opacity-60 group-hover:text-rust">{i.meta}</span>
            <span className="font-serif text-[15px] text-ink group-hover:text-rust transition-colors">{i.label}</span>
          </Link>
        ))}
      </nav>
    </header>
  );
}
```

## `components/Footer.tsx`

```tsx
import { getBrand } from '@/lib/data';

export default function Footer() {
  const brand = getBrand();
  return (
    <footer className="ledger-hairline mt-24 flex items-center justify-between text-meta">
      <div className="type-meta">DANTE LABS · BRAND INTELLIGENCE LAB</div>
      <div className="type-meta">{brand.displayName} · 2026 Q2 REPORT</div>
      <div className="type-meta">EDITION 01</div>
    </footer>
  );
}
```

## `app/page.tsx` (홈)

```tsx
import { getBrand } from '@/lib/data';

export default function Home() {
  const brand = getBrand();
  return (
    <div className="space-y-16">
      <section>
        <div className="type-meta mb-4">SECTION · 01 OVERVIEW</div>
        <h1 className="type-display">{brand.displayName}</h1>
        <p className="type-h2 mt-3 text-ink-soft font-normal max-w-[820px]">{brand.tagline}</p>
      </section>

      <section className="grid grid-cols-4 gap-6">
        {brand.kpis.map((k) => (
          <div key={k.label} className="dl-card rust-stripe pl-6">
            <div className="type-meta">{k.label}</div>
            <div className="num-tabular font-editorial text-[40px] font-bold mt-2 leading-none">{k.value}</div>
            <div className={`type-small mt-3 ${k.tone === 'rust' ? 'text-rust' : 'text-slate2'}`}>{k.delta}</div>
          </div>
        ))}
      </section>

      <section>
        <div className="type-meta mb-4">SECTION · 02 KEY INSIGHTS</div>
        <h2 className="type-h1">관찰된 다섯 가지 시장 신호</h2>
        <div className="mt-8 space-y-6">
          {brand.insights.map((ins, i) => (
            <article key={i} className="grid grid-cols-12 gap-6 ledger-hairline pt-6">
              <div className="col-span-1 type-meta pt-2">{String(i + 1).padStart(2, '0')}</div>
              <div className="col-span-8">
                <h3 className="type-h3">{ins.title}</h3>
                <p className="type-body mt-2 text-ink-soft">{ins.body}</p>
              </div>
              <div className="col-span-3 type-small text-meta self-start pt-2">
                <span className="type-meta block">EVIDENCE</span>
                {ins.evidence}
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
```

## `app/swot/page.tsx`

```tsx
import { getBrand } from '@/lib/data';

const quadrants = [
  { key: 'strengths',     label: '강점 — Strengths',      badge: 'S', tone: 'rust'  },
  { key: 'weaknesses',    label: '약점 — Weaknesses',     badge: 'W', tone: 'slate' },
  { key: 'opportunities', label: '기회 — Opportunities',  badge: 'O', tone: 'rust'  },
  { key: 'threats',       label: '위협 — Threats',        badge: 'T', tone: 'slate' },
] as const;

export default function SwotPage() {
  const brand = getBrand();
  return (
    <div className="space-y-12">
      <header>
        <div className="type-meta mb-4">PAGE · SWOT MATRIX</div>
        <h1 className="type-hero">{brand.displayName} · 전략 매트릭스</h1>
        <p className="type-body text-ink-soft max-w-[820px] mt-3">
          각 사분면 3개 항목, 근거 한 줄. 사실 기반의 관찰 신호로만 구성합니다.
        </p>
      </header>

      <div className="grid grid-cols-2 gap-8">
        {quadrants.map((q) => {
          const items = brand.swot[q.key];
          return (
            <section key={q.key} className="dl-card">
              <div className="flex items-baseline gap-3 mb-6">
                <span className={`type-display !text-[64px] leading-none ${q.tone === 'rust' ? 'text-rust' : 'text-slate2'}`}>
                  {q.badge}
                </span>
                <h2 className="type-h2">{q.label}</h2>
              </div>
              <ul className="space-y-5">
                {items.map((it, i) => (
                  <li key={i} className="border-l-2 border-border pl-4">
                    <div className="type-body text-ink">{it.text}</div>
                    <div className="type-small text-meta mt-1">{it.evidence}</div>
                  </li>
                ))}
              </ul>
            </section>
          );
        })}
      </div>
    </div>
  );
}
```

## `app/charts/page.tsx`

```tsx
import { getBrand } from '@/lib/data';
import { SerpChart, PriceDistChart, RevenueChart, SocialChart } from '@/components/Charts';

export default function ChartsPage() {
  const brand = getBrand();
  return (
    <div className="space-y-12">
      <header>
        <div className="type-meta mb-4">PAGE · CHARTS</div>
        <h1 className="type-hero">{brand.displayName} · 정량 신호</h1>
        <p className="type-body text-ink-soft mt-3 max-w-[820px]">
          검색 트렌드 · 가격 분포 · 매출 추이 · SNS 채널별 영향력. paper + ink + rust 2색 차트.
        </p>
      </header>

      <section className="grid grid-cols-2 gap-8">
        <div className="dl-card">
          <div className="type-meta mb-1">CHART · 01 SERP TREND</div>
          <h2 className="type-h2 mb-4">검색량 추이 (12개월)</h2>
          <SerpChart data={brand.trends.serp} />
        </div>
        <div className="dl-card">
          <div className="type-meta mb-1">CHART · 02 PRICE DISTRIBUTION</div>
          <h2 className="type-h2 mb-4">가격대별 상품 분포</h2>
          <PriceDistChart data={brand.trends.priceDist} />
        </div>
        <div className="dl-card">
          <div className="type-meta mb-1">CHART · 03 REVENUE</div>
          <h2 className="type-h2 mb-4">연도별 거래액 (억 원)</h2>
          <RevenueChart data={brand.trends.revenue} />
        </div>
        <div className="dl-card">
          <div className="type-meta mb-1">CHART · 04 SOCIAL</div>
          <h2 className="type-h2 mb-4">SNS 채널 — 팔로워 · 월간 성장률</h2>
          <SocialChart data={brand.trends.social} />
        </div>
      </section>
    </div>
  );
}
```

## `app/fact-check/page.tsx`

```tsx
import { getBrand } from '@/lib/data';

const STATUS_STYLE: Record<string, { label: string; cls: string }> = {
  verified:  { label: '검증',      cls: 'dl-badge dl-badge-rust' },
  estimated: { label: '추정',      cls: 'dl-badge dl-badge-amber' },
  flagged:   { label: '확인 필요', cls: 'dl-badge dl-badge-slate' },
};

export default function FactCheckPage() {
  const brand = getBrand();
  const verified = brand.factCheck.filter((f) => f.status === 'verified').length;
  return (
    <div className="space-y-12">
      <header>
        <div className="type-meta mb-4">PAGE · FACT CHECK</div>
        <h1 className="type-hero">{brand.displayName} · 팩트 체크</h1>
        <p className="type-body text-ink-soft mt-3 max-w-[820px]">
          본 보고서의 핵심 주장 {brand.factCheck.length}건 중 <span className="dl-mark">{verified}건이 공식 출처로 검증</span>되었습니다.
          나머지는 업계 평균치 기반 추정이며 별도로 표기합니다.
        </p>
      </header>

      <section className="dl-card !p-0 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="ledger-hairline">
              <th className="text-left type-meta px-6 py-4 w-[55%]">주장</th>
              <th className="text-left type-meta px-6 py-4 w-[20%]">출처</th>
              <th className="text-left type-meta px-6 py-4 w-[10%]">상태</th>
              <th className="text-left type-meta px-6 py-4 w-[15%]">비고</th>
            </tr>
          </thead>
          <tbody>
            {brand.factCheck.map((f, i) => {
              const s = STATUS_STYLE[f.status];
              return (
                <tr key={i} className="border-t border-border">
                  <td className="px-6 py-5 type-body">{f.claim}</td>
                  <td className="px-6 py-5 type-small text-meta">{f.source}</td>
                  <td className="px-6 py-5"><span className={s.cls}>{s.label}</span></td>
                  <td className="px-6 py-5 type-small text-ink-soft">{f.note}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>
    </div>
  );
}
```

## `app/competitors/page.tsx`

```tsx
import { getBrand } from '@/lib/data';

export default function CompetitorsPage() {
  const brand = getBrand();
  return (
    <div className="space-y-12">
      <header>
        <div className="type-meta mb-4">PAGE · COMPETITORS</div>
        <h1 className="type-hero">{brand.displayName} · 경쟁사 매트릭스</h1>
        <p className="type-body text-ink-soft mt-3 max-w-[820px]">
          포지셔닝 · 거래액 · 가격대 · 핵심 강점을 한 표로 정리. {brand.displayName} 행은 rust 강조.
        </p>
      </header>

      <section className="dl-card !p-0 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="ledger-hairline">
              <th className="text-left type-meta px-6 py-4 w-[14%]">브랜드</th>
              <th className="text-left type-meta px-6 py-4 w-[34%]">포지셔닝</th>
              <th className="text-left type-meta px-6 py-4 w-[12%]">연 거래액</th>
              <th className="text-left type-meta px-6 py-4 w-[14%]">가격대</th>
              <th className="text-left type-meta px-6 py-4 w-[26%]">핵심 강점</th>
            </tr>
          </thead>
          <tbody>
            {brand.competitors.map((c, i) => (
              <tr key={i} className={`border-t border-border ${c.self ? 'rust-stripe bg-paper-strong' : ''}`}>
                <td className="px-6 py-5">
                  <div className={`type-h3 ${c.self ? 'text-rust' : 'text-ink'}`}>{c.name}</div>
                  {c.self && <div className="type-meta mt-1 text-rust">SELF</div>}
                </td>
                <td className="px-6 py-5 type-body text-ink-soft">{c.positioning}</td>
                <td className="px-6 py-5 num-tabular text-ink">{c.gmv}</td>
                <td className="px-6 py-5 num-tabular text-ink-soft">{c.priceRange}</td>
                <td className="px-6 py-5 type-body text-ink-soft">{c.strength}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
```
