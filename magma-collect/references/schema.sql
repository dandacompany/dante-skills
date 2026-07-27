-- magma-collect 수집 테이블 (섹션 7.1에서 Ada가 설계하는 스키마의 참조 정답지)
create table if not exists collected_products (
  id bigint generated always as identity primary key,
  source text not null check (source in ('musinsa', 'naver', 'coupang')),
  keyword text not null,
  rank integer,
  brand text,
  name text not null,
  price integer,
  discount_rate integer,
  rating numeric(2,1),           -- 쿠팡은 목록에 평점이 없어 null 허용 (소스별 필드 차이)
  review_count integer,
  purchase_count integer,        -- 네이버만 제공
  is_ad boolean default false,   -- 광고 상품 구분 (정제 단계 재료)
  product_url text,
  collected_at timestamptz not null default now()
);

create index if not exists idx_collected_products_source_kw
  on collected_products (source, keyword, collected_at);
