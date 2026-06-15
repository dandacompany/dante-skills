#!/usr/bin/env python3
"""price-positioning — deterministic pricing-landscape analyzer.

Reads a normalized table of price observations (CSV or JSON) and emits a
deterministic positioning report: per-band statistics, pricing whitespace
(empty / under-served price intervals), outliers, value-metric mix, data
gaps, and flags. Same input always yields the same output — results are
fully sorted and contain no time-, network-, or randomness-dependent values.

Standard library only. No network calls, no environment access, no shell
execution. Collection of the observations is out of scope on purpose: bring
your own data from any tool (web scraper, manual entry, exported sheet).

Usage:
    python3 positioning.py OBSERVATIONS.csv --market "3040 men fashion (KR)"
    python3 positioning.py OBSERVATIONS.json --bands "low:-50000,mid:50000-150000,premium:150000-"
    python3 positioning.py data.csv --quantiles 4 --format md --out pricing-landscape.md

Input columns / JSON keys (see references/input-schema.md):
    brand, item, price, currency, source_url, observed_at
    (optional) category, tier_hint, value_metric
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from datetime import date
from pathlib import Path

SCHEMA_VERSION = "1.0"
REQUIRED_FIELDS = ("brand", "item", "price", "currency", "source_url", "observed_at")


# --- loading -----------------------------------------------------------------

def _coerce_price(raw):
    """Parse a price into a float, tolerating thousands separators and spaces.

    Returns None when the value is not a clean number. Currency symbols are
    not guessed — strip them in collection, keep the currency in its own field.
    """
    if raw is None:
        return None
    text = str(raw).strip().replace(",", "").replace(" ", "")
    if not text:
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    if value < 0:
        return None
    return value


def load_observations(path: Path):
    """Load observations from .csv or .json into a list of dicts."""
    suffix = path.suffix.lower()
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        rows = data if isinstance(data, list) else data.get("observations", [])
    elif suffix == ".csv":
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    else:
        raise SystemExit(f"unsupported input type: {suffix} (use .csv or .json)")
    return rows


def normalize(rows):
    """Split raw rows into clean observations and excluded rows (with reasons)."""
    clean, excluded = [], []
    for index, row in enumerate(rows):
        missing = [f for f in ("brand", "item", "currency") if not str(row.get(f, "")).strip()]
        price = _coerce_price(row.get("price"))
        if price is None:
            excluded.append({"row": index, "reason": "missing or non-numeric price"})
            continue
        if missing:
            excluded.append({"row": index, "reason": "missing " + ", ".join(missing)})
            continue
        clean.append({
            "brand": str(row.get("brand", "")).strip(),
            "item": str(row.get("item", "")).strip(),
            "category": str(row.get("category", "")).strip(),
            "price": price,
            "currency": str(row.get("currency", "")).strip().upper(),
            "tier_hint": str(row.get("tier_hint", "")).strip(),
            "value_metric": str(row.get("value_metric", "")).strip().lower(),
            "source_url": str(row.get("source_url", "")).strip(),
            "observed_at": str(row.get("observed_at", "")).strip(),
        })
    return clean, excluded


def pick_currency(observations, forced):
    """Choose the working currency deterministically.

    If forced, keep only that currency. Otherwise pick the most frequent
    currency; ties resolve alphabetically. Everything else is set aside and
    reported as a data gap so mixed-currency input never silently averages.
    """
    counts = {}
    for obs in observations:
        counts[obs["currency"]] = counts.get(obs["currency"], 0) + 1
    if forced:
        chosen = forced.upper()
    elif counts:
        chosen = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    else:
        chosen = ""
    kept = [o for o in observations if o["currency"] == chosen]
    dropped = [o for o in observations if o["currency"] != chosen]
    return chosen, kept, dropped, counts


# --- banding -----------------------------------------------------------------

def parse_band_spec(spec):
    """Parse 'low:-50000,mid:50000-150000,premium:150000-' into ordered bands.

    A missing low bound means open-below; a missing high bound means
    open-above. Bounds use None for open ends.
    """
    bands = []
    for part in spec.split(","):
        part = part.strip()
        if not part or ":" not in part:
            continue
        label, _, rng = part.partition(":")
        lo_text, _, hi_text = rng.partition("-")
        lo = float(lo_text) if lo_text.strip() else None
        hi = float(hi_text) if hi_text.strip() else None
        bands.append({"label": label.strip(), "min": lo, "max": hi})
    bands.sort(key=lambda b: (b["min"] is not None, b["min"] if b["min"] is not None else 0.0))
    return bands


def quantile_bands(prices, n):
    """Build n bands from quantile cut points over the observed prices."""
    ordered = sorted(prices)
    usable = min(n, len(set(ordered))) or 1
    if usable == 1:
        return [{"label": "all", "min": None, "max": None}], 1
    cuts = statistics.quantiles(ordered, n=usable, method="inclusive")
    bounds = [None] + [round(c, 4) for c in cuts] + [None]
    bands = []
    for i in range(usable):
        bands.append({"label": f"band_{i + 1}", "min": bounds[i], "max": bounds[i + 1]})
    return bands, usable


def assign_band(price, bands):
    """Return the label of the first band whose interval contains price.

    Intervals are (min, max]; the lowest band is open-below and the highest
    open-above. Returns None if no band matches (should not happen for
    quantile bands, can happen for sparse user bands).
    """
    for band in bands:
        lo, hi = band["min"], band["max"]
        above_lo = lo is None or price > lo
        within_hi = hi is None or price <= hi
        if above_lo and within_hi:
            return band["label"]
    return None


# --- statistics --------------------------------------------------------------

def _pct(values, fraction):
    ordered = sorted(values)
    if not ordered:
        return None
    if len(ordered) == 1:
        return round(ordered[0], 4)
    rank = fraction * (len(ordered) - 1)
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    interp = ordered[low] + (ordered[high] - ordered[low]) * (rank - low)
    return round(interp, 4)


def band_stats(label, members, total):
    prices = [m["price"] for m in members]
    ordered = sorted(members, key=lambda m: (m["price"], m["brand"], m["item"]))
    examples = []
    if ordered:
        picks = [ordered[0], ordered[len(ordered) // 2], ordered[-1]]
        seen = set()
        for pick in picks:
            key = (pick["brand"], pick["item"], pick["price"])
            if key in seen:
                continue
            seen.add(key)
            examples.append({
                "brand": pick["brand"], "item": pick["item"],
                "price": pick["price"], "source_url": pick["source_url"],
            })
    return {
        "label": label,
        "count": len(members),
        "share": round(len(members) / total, 4) if total else 0.0,
        "min": round(min(prices), 4) if prices else None,
        "p25": _pct(prices, 0.25),
        "median": round(statistics.median(prices), 4) if prices else None,
        "p75": _pct(prices, 0.75),
        "max": round(max(prices), 4) if prices else None,
        "mean": round(statistics.fmean(prices), 4) if prices else None,
        "stdev": round(statistics.pstdev(prices), 4) if len(prices) > 1 else 0.0,
        "examples": examples,
    }


def find_outliers(members, label):
    """Flag members outside [p25 - 1.5*IQR, p75 + 1.5*IQR] for the band."""
    prices = [m["price"] for m in members]
    if len(prices) < 4:
        return []
    p25, p75 = _pct(prices, 0.25), _pct(prices, 0.75)
    iqr = p75 - p25
    lo, hi = p25 - 1.5 * iqr, p75 + 1.5 * iqr
    flagged = [m for m in members if m["price"] < lo or m["price"] > hi]
    flagged.sort(key=lambda m: (m["price"], m["brand"]))
    return [{
        "brand": m["brand"], "item": m["item"], "price": m["price"],
        "band": label,
        "reason": f"outside band IQR fence [{round(lo, 4)}, {round(hi, 4)}]",
    } for m in flagged]


def detect_whitespace(observations, bands, band_members):
    """Empty user bands plus the largest gap between adjacent observed prices."""
    whitespace = []
    prices = sorted({o["price"] for o in observations})
    price_range = (prices[-1] - prices[0]) if len(prices) >= 2 else 0.0

    for band in bands:
        members = band_members.get(band["label"], [])
        if not members and (band["min"] is not None or band["max"] is not None):
            neighbors = sum(1 for b in bands if band_members.get(b["label"]))
            whitespace.append({
                "type": "empty_band",
                "interval": [band["min"], band["max"]],
                "width": None,
                "width_pct_of_range": None,
                "confidence": "high" if neighbors >= 2 else "medium",
                "evidence": f"band '{band['label']}' defined but holds 0 observations",
            })

    if len(prices) >= 3 and price_range > 0:
        gaps = []
        for i in range(len(prices) - 1):
            lo, hi = prices[i], prices[i + 1]
            width = hi - lo
            below = sum(1 for o in observations if o["price"] <= lo)
            above = sum(1 for o in observations if o["price"] >= hi)
            pct = round(width / price_range, 4)
            if pct >= 0.15 and below >= 2 and above >= 2:
                conf = "high"
            elif pct >= 0.08:
                conf = "medium"
            else:
                conf = "low"
            gaps.append((width, lo, hi, pct, conf, below, above))
        widest = max(gaps, key=lambda g: g[0])
        whitespace.append({
            "type": "largest_gap",
            "interval": [round(widest[1], 4), round(widest[2], 4)],
            "width": round(widest[0], 4),
            "width_pct_of_range": widest[3],
            "confidence": widest[4],
            "evidence": (f"{widest[5]} obs at/below {round(widest[1], 4)}, "
                         f"{widest[6]} obs at/above {round(widest[2], 4)}"),
        })

    whitespace.sort(key=lambda w: (-(w["width"] or 0.0), w["interval"][0] or 0.0))
    return whitespace


def _max_date(observations):
    best = ""
    for obs in observations:
        stamp = obs["observed_at"]
        if len(stamp) >= 10 and stamp[:10] > best:
            best = stamp[:10]
    return best[:10] if best else ""


def _date_span_days(observations):
    stamps = []
    for obs in observations:
        try:
            stamps.append(date.fromisoformat(obs["observed_at"][:10]))
        except ValueError:
            continue
    if len(stamps) < 2:
        return None
    return (max(stamps) - min(stamps)).days


def build_flags(observations, dropped, currency_counts):
    red, yellow = [], []
    n = len(observations)
    if n < 5:
        red.append(f"only {n} usable observation(s) — too thin to position; collect more")
    elif n < 12:
        yellow.append(f"{n} observations is a small sample; treat bands as indicative")

    brand_counts = {}
    for obs in observations:
        brand_counts[obs["brand"]] = brand_counts.get(obs["brand"], 0) + 1
    if n and brand_counts:
        top_brand, top_count = sorted(brand_counts.items(), key=lambda kv: (-kv[1], kv[0]))[0]
        if top_count / n > 0.6:
            yellow.append(f"brand '{top_brand}' is {round(100 * top_count / n)}% of observations (skew)")

    span = _date_span_days(observations)
    if span is not None and span > 365:
        yellow.append(f"observations span {span} days — prices may not be comparable in time")

    no_source = sum(1 for o in observations if not o["source_url"])
    if no_source:
        yellow.append(f"{no_source} observation(s) have no source_url (weak provenance)")

    if len([c for c in currency_counts if c]) > 1:
        yellow.append("multiple currencies present; only the dominant currency was analyzed")

    return {"red": red, "yellow": yellow}


# --- orchestration -----------------------------------------------------------

def analyze(observations, bands, as_of, market, currency, dropped, currency_counts, mode):
    band_members = {b["label"]: [] for b in bands}
    unbanded = []
    for obs in observations:
        label = assign_band(obs["price"], bands)
        if label is None:
            unbanded.append(obs)
        else:
            band_members[label].append(obs)

    stats = [band_stats(b["label"], band_members[b["label"]], len(observations)) for b in bands]
    stats.sort(key=lambda s: (s["min"] is None, s["min"] if s["min"] is not None else 0.0))

    outliers = []
    for b in bands:
        outliers.extend(find_outliers(band_members[b["label"]], b["label"]))

    metrics = {}
    for obs in observations:
        if obs["value_metric"]:
            metrics[obs["value_metric"]] = metrics.get(obs["value_metric"], 0) + 1

    gaps = []
    if dropped:
        gaps.append(f"{len(dropped)} observation(s) dropped for non-dominant currency")
    if unbanded:
        gaps.append(f"{len(unbanded)} observation(s) fell outside all defined bands")
    if not as_of:
        gaps.append("no valid observed_at dates — as_of could not be determined")

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_for": market,
        "as_of": as_of,
        "currency": currency,
        "observation_count": len(observations),
        "excluded_observation_count": len(dropped),
        "banding": {"mode": mode,
                     "bands": [{"label": b["label"], "min": b["min"], "max": b["max"]} for b in bands]},
        "bands": stats,
        "whitespace": detect_whitespace(observations, bands, band_members),
        "outliers": outliers,
        "value_metrics": dict(sorted(metrics.items())),
        "data_gaps": gaps,
        "flags": build_flags(observations, dropped, currency_counts),
    }


def render_markdown(report):
    lines = [f"# Pricing Landscape: {report['generated_for'] or 'unnamed market'}",
             f"*Skill: price-positioning | as of {report['as_of'] or 'unknown'} | currency {report['currency'] or 'n/a'}*",
             "",
             f"Observations analyzed: {report['observation_count']} "
             f"(excluded: {report['excluded_observation_count']})",
             "",
             "## Bands",
             "| Band | Count | Share | Min | Median | Max | Mean | Stdev |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for b in report["bands"]:
        lines.append(f"| {b['label']} | {b['count']} | {b['share']} | {b['min']} | "
                     f"{b['median']} | {b['max']} | {b['mean']} | {b['stdev']} |")
    lines += ["", "## Pricing Whitespace"]
    if report["whitespace"]:
        for w in report["whitespace"]:
            lines.append(f"- **{w['type']}** interval {w['interval']} "
                         f"(confidence: {w['confidence']}) — {w['evidence']}")
    else:
        lines.append("- none detected with the current data")
    lines += ["", "## Data Gaps"]
    lines += [f"- {g}" for g in report["data_gaps"]] or ["- none"]
    lines += ["", "## Flags",
              "**Red**"] + ([f"- {x}" for x in report["flags"]["red"]] or ["- none"])
    lines += ["", "**Yellow**"] + ([f"- {x}" for x in report["flags"]["yellow"]] or ["- none"])
    lines += ["", "_Interpretation (price vs. value depth, recommendations) is the "
              "analyst's job — see references/methodology.md. Numbers above are computed "
              "deterministically; claims you add must carry evidence labels._"]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Deterministic pricing-landscape analyzer.")
    parser.add_argument("observations", help="path to a .csv or .json observation file")
    parser.add_argument("--bands", help="user band spec, e.g. low:-50000,mid:50000-150000,premium:150000-")
    parser.add_argument("--quantiles", type=int, default=3, help="band count when --bands is omitted (default 3)")
    parser.add_argument("--market", default="", help="market label for the report header")
    parser.add_argument("--as-of", dest="as_of", default="", help="report date; default = latest observed_at")
    parser.add_argument("--currency", default="", help="force a single currency (default: dominant)")
    parser.add_argument("--format", choices=("json", "md"), default="json")
    parser.add_argument("--out", help="write output to this path instead of stdout")
    args = parser.parse_args(argv)

    path = Path(args.observations)
    if not path.is_file():
        raise SystemExit(f"observation file not found: {path}")

    rows = load_observations(path)
    observations, excluded = normalize(rows)
    if not observations:
        raise SystemExit("no usable observations after normalization (check required columns)")

    currency, kept, dropped, currency_counts = pick_currency(observations, args.currency)
    as_of = args.as_of or _max_date(kept)

    if args.bands:
        bands = parse_band_spec(args.bands)
        mode = "user"
    else:
        bands, _ = quantile_bands([o["price"] for o in kept], max(1, args.quantiles))
        mode = "quantile"

    report = analyze(kept, bands, as_of, args.market, currency, dropped, currency_counts, mode)

    rendered = render_markdown(report) if args.format == "md" else json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(rendered + "\n", encoding="utf-8")
        print(f"wrote {args.format} report to {args.out}")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
