#!/usr/bin/env python3
"""magma-collect CSV 검증기 — 적재 전 게이트.

사용법: python3 validate_csv.py collected_products.csv
컬럼 순서·타입·범위를 검사하고, 통과/실패 행 수와 실패 사유를 출력한다.
실패가 하나라도 있으면 exit code 1 (적재 금지 신호).
"""
import csv
import sys
from datetime import datetime

COLUMNS = ["source", "keyword", "rank", "brand", "name", "price", "discount_rate",
           "rating", "review_count", "purchase_count", "is_ad", "product_url", "collected_at"]
SOURCES = {"musinsa", "naver", "coupang"}


def err(row_no, msg, errors):
    errors.append(f"  행 {row_no}: {msg}")


def check_int(v, lo, hi):
    if v == "":
        return True
    try:
        return lo <= int(v) <= hi
    except ValueError:
        return False


def main(path):
    errors, n = [], 0
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header != COLUMNS:
            print("실패: 헤더가 정규 스키마와 다릅니다.")
            print(f"  기대: {COLUMNS}\n  실제: {header}")
            sys.exit(1)
        for i, row in enumerate(reader, start=2):
            n += 1
            if len(row) != len(COLUMNS):
                err(i, f"컬럼 수 {len(row)} (기대 {len(COLUMNS)})", errors); continue
            r = dict(zip(COLUMNS, row))
            if r["source"] not in SOURCES:
                err(i, f"source 비정규: {r['source']!r}", errors)
            if not r["name"].strip():
                err(i, "name 비어 있음", errors)
            if not check_int(r["rank"], 1, 10000):
                err(i, f"rank 비정상: {r['rank']!r}", errors)
            if not check_int(r["price"], 100, 100_000_000):
                err(i, f"price 비정상: {r['price']!r}", errors)
            if not check_int(r["discount_rate"], 0, 99):
                err(i, f"discount_rate 비정상: {r['discount_rate']!r}", errors)
            if r["rating"] != "":
                try:
                    if not (0.0 <= float(r["rating"]) <= 5.0):
                        err(i, f"rating 범위 밖: {r['rating']}", errors)
                except ValueError:
                    err(i, f"rating 숫자 아님: {r['rating']!r}", errors)
            if r["source"] == "coupang" and r["rating"] != "":
                err(i, "쿠팡 행에 rating 존재 — 목록에 평점이 없는 소스 (추출 오류 의심)", errors)
            if not check_int(r["review_count"], 0, 10_000_000):
                err(i, f"review_count 비정상: {r['review_count']!r}", errors)
            if not check_int(r["purchase_count"], 0, 100_000_000):
                err(i, f"purchase_count 비정상: {r['purchase_count']!r}", errors)
            if r["purchase_count"] != "" and r["source"] != "naver":
                err(i, "purchase_count는 네이버만 제공", errors)
            if r["is_ad"] not in ("true", "false"):
                err(i, f"is_ad는 true/false: {r['is_ad']!r}", errors)
            try:
                datetime.fromisoformat(r["collected_at"].replace("Z", "+00:00"))
            except ValueError:
                err(i, f"collected_at ISO 8601 아님: {r['collected_at']!r}", errors)

    print(f"검사 행: {n} · 실패: {len(errors)}")
    if errors:
        print("\n".join(errors[:30]))
        if len(errors) > 30:
            print(f"  ... 외 {len(errors) - 30}건")
        sys.exit(1)
    print("검증 통과 — 적재 가능")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1])
