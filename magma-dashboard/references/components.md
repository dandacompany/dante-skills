# Evidence 컴포넌트 사용법 — 판매 대시보드 8종

> 실측 기준: Evidence 40.1.8 · core-components 5.4.2 (2026-08-01).
> 페이지는 `pages/*.md` 하나가 곧 화면이다. ```sql 블록으로 질의를 정의하고, 컴포넌트가 `data={질의명}`으로 읽는다.

## 질의 블록 기본형

````markdown
```sql kpi
select
  sum(revenue) as revenue,
  count(distinct order_id) as orders,
  count(distinct customer_id) as customers,
  sum(revenue) / count(distinct order_id) as aov
from magma.sales
```
````

- 테이블명은 `소스명.정의명` (`magma.sales` = `sources/magma/sales.sql`).
- 질의는 브라우저 안 DuckDB에서 돈다. Postgres 문법과 대부분 같지만 방언 차이가 있으면 DuckDB 기준.

## 1. KPI (BigValue + Grid)

```html
<Grid cols=4>
  <BigValue data={kpi} value=revenue title="총매출" fmt=num0/>
  <BigValue data={kpi} value=orders title="주문 수" fmt=num0/>
  <BigValue data={kpi} value=customers title="구매 고객 수" fmt=num0/>
  <BigValue data={kpi} value=aov title="평균 주문금액" fmt=num0/>
</Grid>
```

## 2. 라인 차트 (시간 추이)

```html
<LineChart data={monthly} x=month y=revenue yFmt=num0 title="월별 매출 추이"/>
```

질의에서 `date_trunc('month', ordered_at)::date as month`로 월을 만들어 두는 쪽이 안전하다.

## 3. 스택 막대 (구성 추이)

```html
<BarChart data={monthly_channel} x=month y=revenue series=channel type=stacked yFmt=num0 title="월별 채널 구성"/>
```

## 4. 도넛 — 내장 컴포넌트 없음, ECharts로 만든다

Evidence에는 파이·도넛 컴포넌트가 없다(설계 철학). 필요하면 ECharts 직결:

```html
<ECharts config={{
  tooltip: { trigger: 'item' },
  legend: { bottom: 0 },
  series: [{
    type: 'pie',
    radius: ['45%','70%'],
    data: [...channel_mix].map(d => ({ name: d.channel, value: d.revenue }))
  }]
}} title="채널별 매출 비중"/>
```

## 5. 가로 막대 (순위)

```html
<BarChart data={by_category} x=category y=revenue swapXY=true yFmt=num0 title="카테고리별 매출"/>
```

⚠️ 원화 금액이 크면 세로형에서 x축 라벨이 겹친다. 순위류는 `swapXY=true` 가로형 + 필요하면 질의에서 `revenue/100000000.0 as revenue_eok`로 억 단위 변환.

## 6. 히트맵 (요일과 시간대)

```html
<Heatmap data={dow_hour} x=hour y=dow value=orders title="요일과 시간대별 주문 분포"/>
```

y 정렬이 필요하면 질의에 `dow_num`(0~6)을 함께 뽑아 `order by dow_num`.

## 7. 버블 (두 측정값 관계)

```html
<BubbleChart data={cost_price} x=avg_cost y=avg_price size=qty series=category xFmt=num0 yFmt=num0 title="원가 대비 판매가"/>
```

⚠️ 이상치 하나가 축을 늘려 나머지가 바닥에 뭉친다. 이상치가 보이면 차트를 늘리려 하지 말고 데이터 문제로 보고.

## 8. 표 (상세·검산용)

```html
<DataTable data={top_products} rows=15>
  <Column id=product_name title="상품명"/>
  <Column id=category title="카테고리"/>
  <Column id=revenue title="매출" fmt=num0 contentType=colorscale/>
  <Column id=qty title="수량" fmt=num0/>
  <Column id=margin_rate title="마진율" fmt=pct1/>
</DataTable>
```

마진율 컬럼은 검산 포인트다 — 특정 행만 100%에 붙어 있으면 원가나 단가에 이상치가 있다는 신호.

## 필터 (Dropdown)

```html
<Dropdown data={channels} name=channel value=channel title="판매 채널">
  <DropdownOption value="__all__" valueLabel="전체"/>
</Dropdown>
```

⚠️ **전체 선택을 `like '%'`로 구현하지 않는다** — NULL 행이 조용히 빠진다. 안전한 패턴:

```sql
where ('${inputs.channel.value}' = '__all__' or channel = '${inputs.channel.value}')
```

## 자주 쓰는 fmt

| fmt | 예 |
| --- | --- |
| `num0` | 10,828,045,500 |
| `pct1` | 84.0% |
| `#,##0,,"백만"` 류 커스텀 | 축 축약이 필요할 때 |
