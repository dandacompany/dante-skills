#!/usr/bin/env python3
"""magma-mart-seed — MAGMA 판매·프로모션 더미 데이터 마트 생성기.

교육 목적으로 '현실에서 만나는 지저분한 상태'를 의도적으로 주입한
관계형 마트 CSV 5종을 생성한다. 시드가 고정돼 있어 누가 언제 돌려도
완전히 동일한 데이터가 나온다 (결정론 보장).

사용법:
    python3 generate_mart.py [--out DIR] [--seed 42]

출력: customers.csv products.csv promotions.csv orders.csv order_items.csv
      + schema.sql (스테이징 테이블 DDL) + DIRT_REPORT.md (주입된 오염 요약)
"""
import argparse
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

SEED_DEFAULT = 42

FAMILY = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임"]
GIVEN = ["민준", "서준", "도윤", "예준", "시우", "지호", "준서", "건우", "현우", "우진",
         "지훈", "선우", "서진", "민재", "태윤", "은우", "수호", "정우", "승현", "준혁"]
REGIONS_CLEAN = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "경기", "강원", "충북",
                 "충남", "전북", "전남", "경북", "경남", "제주"]
REGION_DIRTY = {"서울": ["SEOUL", "seoul", "서울특별시", " 서울"], "부산": ["BUSAN", "부산광역시"],
                "경기": ["GYEONGGI", "경기도"], "대구": ["daegu"]}
CATEGORIES = ["셔츠", "티셔츠", "팬츠", "아우터", "니트", "액세서리"]
CHANNELS_CLEAN = ["online", "store", "pop-up"]
CHANNELS_DIRTY = ["ONLINE", "Online ", "온라인", "매장", "STORE"]
ADJ = ["릴렉스드", "클래식", "오버핏", "슬림", "베이직", "프리미엄", "시티", "에센셜"]
NOUN = ["옥스포드 셔츠", "린넨 셔츠", "카라 티셔츠", "치노 팬츠", "와이드 팬츠",
        "블루종", "트러커 자켓", "캐시미어 니트", "라운드 니트", "레더 벨트", "볼캡", "머플러"]

BASE_DATE = datetime(2025, 7, 1)
DAYS = 365


def pick_date(rng, spread=DAYS):
    return BASE_DATE + timedelta(days=rng.randrange(spread), hours=rng.randrange(24), minutes=rng.randrange(60))


def fmt_date_dirty(rng, dt):
    """날짜 포맷 혼재 오염: ISO, 슬래시, 점, 한국식이 뒤섞인다."""
    r = rng.random()
    if r < 0.70:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    if r < 0.82:
        return dt.strftime("%Y/%m/%d")
    if r < 0.92:
        return dt.strftime("%d.%m.%Y")
    return dt.strftime("%Y년 %m월 %d일")


def fmt_price_dirty(rng, price):
    """금액 표기 오염: 숫자, 원화기호, 콤마, '원' 접미가 뒤섞인다."""
    r = rng.random()
    if r < 0.75:
        return str(price)
    if r < 0.85:
        return f"₩{price:,}"
    if r < 0.95:
        return f"{price:,}원"
    return f"{price}.0"


def gen_customers(rng, n=1000):
    rows, dirt = [], {"dup": 0, "null_phone": 0, "dirty_region": 0, "bad_email": 0}
    for i in range(1, n + 1):
        name = rng.choice(FAMILY) + rng.choice(GIVEN)
        region = rng.choice(REGIONS_CLEAN)
        if region in REGION_DIRTY and rng.random() < 0.18:
            region = rng.choice(REGION_DIRTY[region]); dirt["dirty_region"] += 1
        phone = f"010-{rng.randrange(1000, 9999)}-{rng.randrange(1000, 9999)}"
        if rng.random() < 0.07:
            phone = ""; dirt["null_phone"] += 1
        email = f"user{i:04d}@example.com"
        if rng.random() < 0.03:
            email = email.replace("@", "(at)"); dirt["bad_email"] += 1
        rows.append([f"C{i:05d}", name, email, phone, region,
                     fmt_date_dirty(rng, pick_date(rng, 700)), rng.choice(["M", "F", "m", ""])])
    # 중복 고객 오염: 같은 사람이 살짝 다른 표기로 다시 등록
    for _ in range(30):
        src = rng.choice(rows[:n])
        dup = list(src)
        dup[0] = f"C{len(rows) + 1:05d}"
        dup[1] = src[1] + (" " if rng.random() < 0.5 else "")
        dup[3] = src[3].replace("-", "") if src[3] else ""
        rows.append(dup); dirt["dup"] += 1
    return rows, dirt


def gen_products(rng, n=200):
    rows, dirt = [], {"neg_price": 0, "outlier": 0, "null_cat": 0}
    for i in range(1, n + 1):
        cat = rng.choice(CATEGORIES)
        name = f"{rng.choice(ADJ)} {rng.choice(NOUN)}"
        cost = rng.randrange(8, 60) * 1000
        price = int(cost * rng.uniform(1.8, 3.2)) // 100 * 100
        if rng.random() < 0.02:
            price = -price; dirt["neg_price"] += 1
        elif rng.random() < 0.015:
            price = price * 100; dirt["outlier"] += 1
        if rng.random() < 0.04:
            cat = ""; dirt["null_cat"] += 1
        rows.append([f"P{i:04d}", name, cat, cost, price,
                     rng.choice(["active", "active", "active", "discontinued", "ACTIVE"])])
    return rows, dirt


def gen_promotions(rng, n=30):
    rows = []
    for i in range(1, n + 1):
        start = pick_date(rng)
        end = start + timedelta(days=rng.randrange(3, 21))
        rate = rng.choice([10, 15, 20, 25, 30, 40, 50])
        rows.append([f"PR{i:03d}", f"{start.month}월 {rng.choice(['시즌오프', '위크엔드', '멤버스', '신상런칭', '반짝'])} {rate}%",
                     rate, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"),
                     rng.choice(CATEGORIES + ["전체", "ALL"])])
    return rows


def gen_orders_items(rng, customers, products, promotions, n_orders=20000):
    orders, items = [], []
    dirt = {"orphan_fk": 0, "neg_qty": 0, "future_date": 0, "dup_order": 0, "dirty_channel": 0}
    pid_pool = [p[0] for p in products]
    cid_pool = [c[0] for c in customers]
    item_seq = 1
    for i in range(1, n_orders + 1):
        oid = f"O{i:06d}"
        cid = rng.choice(cid_pool)
        odt = pick_date(rng)
        if rng.random() < 0.005:
            odt = datetime(2027, rng.randrange(1, 13), rng.randrange(1, 28)); dirt["future_date"] += 1
        channel = rng.choice(CHANNELS_CLEAN)
        if rng.random() < 0.12:
            channel = rng.choice(CHANNELS_DIRTY); dirt["dirty_channel"] += 1
        promo = rng.choice(promotions)[0] if rng.random() < 0.25 else ""
        status = rng.choice(["paid"] * 8 + ["cancelled", "refunded"])
        orders.append([oid, cid, fmt_date_dirty(rng, odt), channel, promo, status])
        for _ in range(rng.choice([1, 1, 1, 2, 2, 3])):
            pid = rng.choice(pid_pool)
            if rng.random() < 0.008:
                pid = f"P{rng.randrange(900, 999):04d}X"; dirt["orphan_fk"] += 1
            qty = rng.choice([1, 1, 1, 2, 3])
            if rng.random() < 0.004:
                qty = -qty; dirt["neg_qty"] += 1
            unit = next((p[4] for p in products if p[0] == pid), rng.randrange(20, 200) * 1000)
            items.append([f"I{item_seq:07d}", oid, pid, qty, fmt_price_dirty(rng, abs(int(unit)))])
            item_seq += 1
    # 중복 주문행 오염
    for _ in range(60):
        orders.append(list(rng.choice(orders))); dirt["dup_order"] += 1
    return orders, items, dirt


SCHEMA_SQL = """-- magma-mart-seed 스테이징 테이블 (오염 데이터를 그대로 받기 위해 텍스트 중심)
create table if not exists stg_customers (customer_id text, name text, email text, phone text, region text, joined_at text, gender text);
create table if not exists stg_products (product_id text, name text, category text, cost int, price bigint, status text);
create table if not exists stg_promotions (promo_id text, name text, discount_rate int, starts_on date, ends_on date, target_category text);
create table if not exists stg_orders (order_id text, customer_id text, ordered_at text, channel text, promo_id text, status text);
create table if not exists stg_order_items (item_id text, order_id text, product_id text, qty int, unit_price text);
"""


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out")
    ap.add_argument("--seed", type=int, default=SEED_DEFAULT)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    customers, d_c = gen_customers(rng)
    products, d_p = gen_products(rng)
    promotions = gen_promotions(rng)
    orders, items, d_o = gen_orders_items(rng, customers, products, promotions)

    write_csv(out / "customers.csv", ["customer_id", "name", "email", "phone", "region", "joined_at", "gender"], customers)
    write_csv(out / "products.csv", ["product_id", "name", "category", "cost", "price", "status"], products)
    write_csv(out / "promotions.csv", ["promo_id", "name", "discount_rate", "starts_on", "ends_on", "target_category"], promotions)
    write_csv(out / "orders.csv", ["order_id", "customer_id", "ordered_at", "channel", "promo_id", "status"], orders)
    write_csv(out / "order_items.csv", ["item_id", "order_id", "product_id", "qty", "unit_price"], items)
    (out / "schema.sql").write_text(SCHEMA_SQL, encoding="utf-8")

    report = ["# DIRT_REPORT — 주입된 오염 요약 (seed=%d)" % args.seed, ""]
    report.append(f"- customers: {len(customers)}행 · 중복 등록 {d_c['dup']} · 전화 결측 {d_c['null_phone']} · 지역 표기 비정규 {d_c['dirty_region']} · 이메일 오염 {d_c['bad_email']}")
    report.append(f"- products: {len(products)}행 · 음수 가격 {d_p['neg_price']} · 가격 이상치 {d_p['outlier']} · 카테고리 결측 {d_p['null_cat']}")
    report.append(f"- promotions: {len(promotions)}행 · 타깃에 '전체'/'ALL' 혼재")
    report.append(f"- orders: {len(orders)}행 · 중복 주문행 {d_o['dup_order']} · 미래 날짜 {d_o['future_date']} · 채널 표기 비정규 {d_o['dirty_channel']} · 날짜 포맷 4종 혼재")
    report.append(f"- order_items: {len(items)}행 · 고아 상품 FK {d_o['orphan_fk']} · 음수 수량 {d_o['neg_qty']} · 금액 표기 4종 혼재")
    (out / "DIRT_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    print(f"\n생성 완료: {out.resolve()}")


if __name__ == "__main__":
    main()
