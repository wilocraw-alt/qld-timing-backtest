#!/usr/bin/env python3
"""
정적 사이트 빌더 — 추천 전략 ①(SOXL60 buffer±3% + QLD40)의
데일리 신호·목표배분을 보여주는 모바일 PWA 사이트 생성.
"""
import os, sys, json, argparse, datetime as dt, shutil

import pandas as pd
import yaml
import yfinance as yf
from PIL import Image, ImageDraw, ImageFont
from pandas.tseries.holiday import (AbstractHolidayCalendar, Holiday, nearest_workday,
                                    USMartinLutherKingJr, USPresidentsDay, USMemorialDay,
                                    USLaborDay, USThanksgivingDay, GoodFriday)

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)

DISCLAIMER = "본 정보는 정보 제공 용도이며 투자 조언이 아닙니다. 과거 데이터 기반 백테스트로 실제 성과와 다를 수 있습니다."
CONCLUSION = "강세장 타이밍은 buy&hold에 패배, 폭락장 무방비3x는 전멸 → 추세규칙 SOXL60+QLD40로 '틀려도 생존' 설계"


class _NYSEHolidays(AbstractHolidayCalendar):
    rules = [
        Holiday("New Year's Day", month=1, day=1, observance=nearest_workday),
        USMartinLutherKingJr,
        USPresidentsDay,
        GoodFriday,
        USMemorialDay,
        Holiday("Juneteenth", month=6, day=19, observance=nearest_workday, start_date="2022-06-19"),
        Holiday("Independence Day", month=7, day=4, observance=nearest_workday),
        USLaborDay,
        USThanksgivingDay,
        Holiday("Christmas", month=12, day=25, observance=nearest_workday),
    ]

_NYSE_CAL = _NYSEHolidays()


def market_status(d):
    if d.weekday() >= 5:
        return False, "주말"
    hol = _NYSE_CAL.holidays(start=pd.Timestamp(d.year, 1, 1),
                             end=pd.Timestamp(d.year, 12, 31), return_name=True)
    ts = pd.Timestamp(d)
    if ts in hol.index:
        return False, str(hol[ts])
    return True, None


def load_cfg(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def fetch(tickers):
    out = {}
    for t in tickers:
        h = yf.Ticker(t).history(period="2y", auto_adjust=True)["Close"]
        h.index = h.index.tz_localize(None)
        out[t] = h
    return out


def read_conclusion(path):
    if not os.path.exists(path):
        return CONCLUSION
    with open(path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("최종 추천"):
                return stripped.replace("**", "")
    return CONCLUSION


def make_icon(size, path, maskable=False):
    img = Image.new("RGBA", (size, size), (17, 24, 39, 255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size // 3)
    except (IOError, OSError):
        font = ImageFont.load_default()

    text = "SQ"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) / 2
    y = (size - th) / 2 - size * 0.05

    if maskable:
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse([size * 0.1, size * 0.1, size * 0.9, size * 0.9], fill=255)
        img.putalpha(mask)

    draw.text((x, y), text, fill=(232, 234, 237, 255), font=font)
    img.save(path, "PNG")
    print(f"  → 생성됨 {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="site", help="출력 디렉터리 (기본값: site)")
    ap.add_argument("--config", default=os.path.join("backtest", "live", "advisor_config.yaml"),
                    help="설정 파일 경로")
    args = ap.parse_args()

    cfg_path = os.path.join(BASE, args.config) if not os.path.isabs(args.config) else args.config
    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)

    cfg = load_cfg(cfg_path)
    core_t = cfg["core_ticker"]
    sig_t = cfg["core_signal"]
    sat_t = cfg["satellite_ticker"]
    w_core = float(cfg["w_core"])
    ma_win = int(cfg["ma_window"])
    buffer = float(cfg["buffer"])

    print(f"[빌더] 설정 로드: {cfg_path}")
    print(f"[빌더] 전략: {core_t} ({w_core*100:.0f}%) + {sat_t} ({(1-w_core)*100:.0f}%)")
    print(f"[빌더] 신호: {sig_t} {ma_win}MA ±{buffer*100:.0f}%")

    # ---- 데이터 수집 ----
    print("[빌더] yfinance 데이터 수집 중...")
    px = fetch([core_t, sig_t, sat_t])
    last_date = min(px[t].index[-1] for t in px)
    core_close = float(px[core_t].asof(last_date))
    sat_close = float(px[sat_t].asof(last_date))
    sig_close = float(px[sig_t].asof(last_date))
    ma = float(px[sig_t].loc[:last_date].tail(ma_win).mean()) if len(px[sig_t].loc[:last_date]) >= ma_win else float("nan")
    ratio = sig_close / ma if ma == ma and ma > 0 else float("nan")

    upper = 1 + buffer
    lower = 1 - buffer

    # ---- 신호 판정 (무상태, buffer 기반) ----
    if ratio != ratio:
        state = "NEUTRAL"
    elif ratio > upper:
        state = "ON"
    elif ratio < lower:
        state = "OFF"
    else:
        state = "NEUTRAL"

    print(f"[빌더] {sig_t} 종가={sig_close:.2f} / {ma_win}MA={ma:.2f} / ratio={ratio:.4f}")
    print(f"[빌더] 신호 상태: {state} (밴드 {lower:.4f}–{upper:.4f})")

    # ---- 차트 시계열 (series.json) ----
    data_dir = os.path.join(out_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    sig_series = px[sig_t]  # daily close series, ~2y
    ma_series = sig_series.rolling(ma_win).mean()
    cutoff = sig_series.index[-1] - pd.DateOffset(months=3)
    mask = sig_series.index >= cutoff
    filtered_dates = sig_series.index[mask]
    series_pts = []
    for idx in filtered_dates:
        ma_val = float(ma_series.loc[idx]) if pd.notna(ma_series.loc[idx]) else None
        series_pts.append({
            "d": str(idx.date()),
            "soxx": float(round(sig_series.loc[idx], 2)),
            "ma": round(ma_val, 2) if ma_val is not None else None,
        })
    series_data = {
        "window": ma_win,
        "buffer": buffer,
        "points": series_pts,
    }
    with open(os.path.join(data_dir, "series.json"), "w", encoding="utf-8") as f:
        json.dump(series_data, f, ensure_ascii=False)
    print(f"  → 생성됨 {os.path.join(data_dir, 'series.json')} ({len(series_pts)} points)")

    # ---- 시장 상태 ----
    today = dt.datetime.now().date()
    is_open, reason = market_status(today)

    # ---- 타임스탬프 (KST) ----
    kst_now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    updated_at = kst_now.isoformat(timespec="seconds")

    # ---- 결론 ----
    research_path = os.path.join(BASE, "RESEARCH.md")
    conclusion = read_conclusion(research_path)

    # ---- latest.json 구성 ----
    data = {
        "updated_at": updated_at,
        "tz": "Asia/Seoul",
        "ref_close": str(last_date.date()),
        "market": {"open": is_open, "reason": reason},
        "signal": {
            "soxx_close": round(sig_close, 2),
            "ma120": round(ma, 2),
            "ratio": round(ratio, 4),
            "upper": round(upper, 4),
            "lower": round(lower, 4),
            "state": state,
        },
        "prices": {
            core_t: round(core_close, 2),
            sig_t: round(sig_close, 2),
            sat_t: round(sat_close, 2),
        },
        "target": {
            "core_pct": int(w_core * 100),
            "satellite_pct": int((1 - w_core) * 100),
            "core_ticker": core_t,
            "satellite_ticker": sat_t,
        },
        "conclusion": conclusion,
        "disclaimer": DISCLAIMER,
    }

    # ---- 출력 ----
    with open(os.path.join(data_dir, "latest.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  → 생성됨 {os.path.join(data_dir, 'latest.json')}")

    # ---- 템플릿 복사 ----
    build_id = updated_at.replace(":", "").replace("+", "").replace("-", "").replace("T", "")
    for fname in ["index.html", "manifest.webmanifest", "sw.js"]:
        src = os.path.join(HERE, f"template_{fname}")
        dst = os.path.join(out_dir, fname)
        if fname == "sw.js":
            with open(src, encoding="utf-8") as f:
                content = f.read()
            content = content.replace("__BUILD_ID__", build_id)
            with open(dst, "w", encoding="utf-8") as f:
                f.write(content)
        else:
            shutil.copy2(src, dst)
        print(f"  → 생성됨 {dst}")

    # ---- 아이콘 ----
    icons_dir = os.path.join(out_dir, "icons")
    os.makedirs(icons_dir, exist_ok=True)
    make_icon(192, os.path.join(icons_dir, "icon-192.png"), maskable=False)
    make_icon(512, os.path.join(icons_dir, "icon-512.png"), maskable=False)
    make_icon(512, os.path.join(icons_dir, "maskable-512.png"), maskable=True)

    print(f"\n[완료] 사이트 생성됨 → {out_dir}/")
    print(f"  data/latest.json  ({len(json.dumps(data, ensure_ascii=False))} bytes)")
    print(f"  data/series.json  ({len(series_pts)} points)")
    print(f"  index.html / manifest.webmanifest / sw.js")
    print(f"  icons/ (icon-192, icon-512, maskable-512)")


if __name__ == "__main__":
    main()
