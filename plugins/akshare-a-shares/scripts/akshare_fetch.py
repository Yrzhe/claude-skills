#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fetch A-share data via local akshare sources.

Assumptions:
- Local akshare source exists at <CWD>/Recents/akshare
- Python3 with pandas and requests installed; py_mini_racer required for some Sina endpoints

Usage examples:
  spot (EM):
    python3 scripts/akshare_fetch.py spot --source em --format csv
  hist (EM, qfq):
    python3 scripts/akshare_fetch.py hist --symbol 600519 --period daily --start 20150101 --end 20251231 --adjust qfq --format csv
  minute (EM, 5m):
    python3 scripts/akshare_fetch.py min --symbol 000001 --period 5 --start "2024-12-01 09:30:00" --end "2024-12-02 15:00:00" --format csv
  gdhs latest:
    python3 scripts/akshare_fetch.py gdhs --when 最新 --format csv
  cninfo annual reports:
    python3 scripts/akshare_fetch.py cninfo --symbol 000001 --market 沪深京 --category 年报 --start 20230101 --end 20241231 --format csv
"""

import argparse
import sys
import json as _json
from pathlib import Path

import pandas as pd


AK_PATH = Path.cwd() / "Recents" / "akshare"


def _ensure_akshare_on_path():
    if not AK_PATH.exists():
        sys.stderr.write(f"[error] akshare source not found at: {AK_PATH}\n")
        sys.exit(1)
    if str(AK_PATH) not in sys.path:
        sys.path.insert(0, str(AK_PATH))


def _print_df(df: pd.DataFrame, fmt: str):
    if df is None:
        sys.stderr.write("[warn] got None dataframe\n")
        return
    if df.empty:
        sys.stderr.write("[warn] empty dataframe\n")
    if fmt == "csv":
        df.to_csv(sys.stdout, index=False)
    elif fmt == "json":
        sys.stdout.write(df.to_json(orient="records", force_ascii=False))
    else:
        sys.stderr.write(f"[error] unsupported format: {fmt}\n")
        sys.exit(2)


def _normalize_symbol_for_sina(symbol: str) -> str:
    # If already prefixed, return as-is
    if symbol.startswith(("sh", "sz")):
        return symbol
    if symbol.startswith("6"):
        return f"sh{symbol}"
    if symbol.startswith(("0", "3")):
        return f"sz{symbol}"
    return symbol


def cmd_spot(args):
    if args.source == "em":
        from akshare.stock_feature.stock_hist_em import stock_zh_a_spot_em

        df = stock_zh_a_spot_em()
        _print_df(df, args.format)
    elif args.source == "sina":
        try:
            from akshare.stock.stock_zh_a_sina import stock_zh_a_spot
        except Exception as e:
            sys.stderr.write("[error] importing sina spot requires deps (py_mini_racer, demjson).\n")
            raise e
        df = stock_zh_a_spot()
        _print_df(df, args.format)
    else:
        sys.stderr.write("[error] unknown source; use em|sina\n")
        sys.exit(2)


def cmd_hist(args):
    if args.source == "em":
        from akshare.stock_feature.stock_hist_em import stock_zh_a_hist

        df = stock_zh_a_hist(
            symbol=args.symbol,
            period=args.period,
            start_date=args.start,
            end_date=args.end,
            adjust=args.adjust,
        )
        _print_df(df, args.format)
    elif args.source == "sina":
        try:
            from akshare.stock.stock_zh_a_sina import stock_zh_a_daily
        except Exception as e:
            sys.stderr.write("[error] importing sina daily requires deps (py_mini_racer).\n")
            raise e
        sym = _normalize_symbol_for_sina(args.symbol)
        df = stock_zh_a_daily(
            symbol=sym, start_date=args.start, end_date=args.end, adjust=args.adjust
        )
        _print_df(df, args.format)
    else:
        sys.stderr.write("[error] unknown source; use em|sina\n")
        sys.exit(2)


def cmd_min(args):
    if args.source == "em":
        from akshare.stock_feature.stock_hist_em import stock_zh_a_hist_min_em

        df = stock_zh_a_hist_min_em(
            symbol=args.symbol,
            start_date=args.start,
            end_date=args.end,
            period=args.period,
            adjust=args.adjust,
        )
        _print_df(df, args.format)
    elif args.source == "sina":
        try:
            from akshare.stock.stock_zh_a_sina import stock_zh_a_minute
        except Exception as e:
            sys.stderr.write("[error] importing sina minute requires deps (py_mini_racer).\n")
            raise e
        sym = _normalize_symbol_for_sina(args.symbol)
        df = stock_zh_a_minute(symbol=sym, period=args.period, adjust=args.adjust)
        _print_df(df, args.format)
    else:
        sys.stderr.write("[error] unknown source; use em|sina\n")
        sys.exit(2)


def cmd_gdhs(args):
    from akshare.stock_feature.stock_gdhs import stock_zh_a_gdhs

    df = stock_zh_a_gdhs(symbol=args.when)
    _print_df(df, args.format)


def cmd_gdhs_detail(args):
    from akshare.stock_feature.stock_gdhs import stock_zh_a_gdhs_detail_em

    df = stock_zh_a_gdhs_detail_em(symbol=args.symbol)
    _print_df(df, args.format)


def cmd_cninfo(args):
    from akshare.stock_feature.stock_disclosure_cninfo import (
        stock_zh_a_disclosure_report_cninfo,
    )

    df = stock_zh_a_disclosure_report_cninfo(
        symbol=args.symbol,
        market=args.market,
        keyword=args.keyword,
        category=args.category,
        start_date=args.start,
        end_date=args.end,
    )
    _print_df(df, args.format)


def build_parser():
    p = argparse.ArgumentParser(description="Fetch A-share data via local akshare")
    sub = p.add_subparsers(dest="cmd", required=True)

    # spot
    sp = sub.add_parser("spot", help="Realtime A-share quotes")
    sp.add_argument("--source", choices=["em", "sina"], default="em")
    sp.add_argument("--format", choices=["csv", "json"], default="csv")
    sp.set_defaults(func=cmd_spot)

    # hist
    hp = sub.add_parser("hist", help="Daily/Weekly/Monthly kline")
    hp.add_argument("--source", choices=["em", "sina"], default="em")
    hp.add_argument("--symbol", required=True)
    hp.add_argument("--period", choices=["daily", "weekly", "monthly"], default="daily")
    hp.add_argument("--start", required=True, help="YYYYMMDD")
    hp.add_argument("--end", required=True, help="YYYYMMDD")
    hp.add_argument("--adjust", choices=["", "qfq", "hfq", "qfq-factor", "hfq-factor"], default="")
    hp.add_argument("--format", choices=["csv", "json"], default="csv")
    hp.set_defaults(func=cmd_hist)

    # minute
    mp = sub.add_parser("min", help="Minute kline (1/5/15/30/60)")
    mp.add_argument("--source", choices=["em", "sina"], default="em")
    mp.add_argument("--symbol", required=True)
    mp.add_argument("--period", choices=["1", "5", "15", "30", "60"], default="5")
    mp.add_argument("--start", required=False, help="YYYY-MM-DD HH:MM:SS")
    mp.add_argument("--end", required=False, help="YYYY-MM-DD HH:MM:SS")
    mp.add_argument("--adjust", choices=["", "qfq", "hfq"], default="")
    mp.add_argument("--format", choices=["csv", "json"], default="csv")
    mp.set_defaults(func=cmd_min)

    # gdhs
    gp = sub.add_parser("gdhs", help="Shareholder accounts summary")
    gp.add_argument("--when", required=True, help="最新 或 YYYYMMDD")
    gp.add_argument("--format", choices=["csv", "json"], default="csv")
    gp.set_defaults(func=cmd_gdhs)

    # gdhs detail
    gdp = sub.add_parser("gdhs-detail", help="Shareholder accounts detail for symbol")
    gdp.add_argument("--symbol", required=True)
    gdp.add_argument("--format", choices=["csv", "json"], default="csv")
    gdp.set_defaults(func=cmd_gdhs_detail)

    # cninfo
    cp = sub.add_parser("cninfo", help="Disclosure search via cninfo")
    cp.add_argument("--symbol", required=True)
    cp.add_argument("--market", default="沪深京")
    cp.add_argument("--keyword", default="")
    cp.add_argument("--category", default="")
    cp.add_argument("--start", required=True, help="YYYYMMDD")
    cp.add_argument("--end", required=True, help="YYYYMMDD")
    cp.add_argument("--format", choices=["csv", "json"], default="csv")
    cp.set_defaults(func=cmd_cninfo)

    return p


def main():
    _ensure_akshare_on_path()
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

