#!/usr/bin/env python3
"""
데일리 어드바이저 — 추천 전략 ①(SOXL60 buffer±3% + QLD40 무규칙, 월 $300 DCA)을
전일까지의 실제 종가로 점검하여 '오늘(미국장) 수행할 매매'를 알려준다.

전략 규칙:
  - 코어 60% SOXL: 신호용 SOXX의 120일선 ±3% 완충밴드(buffer).
      SOXX 종가 > 120MA×1.03 → SOXL 보유(ON) / < ×0.97 → 현금(OFF) / 사이 → 직전상태 유지.
  - 위성 40% QLD: 무규칙 항상 보유.
  - 매월 첫 (스크립트가 본) 영업일에 예산 $300 유입, 60:40 배분.
  - 신호는 전일 종가로 판정(미래참조 없음), 체결은 당일 미국장.

상태(state.json)에 보유주·예약현금·신호상태·마지막 적립월을 저장(주문 실행 가정).
--dry-run: 상태를 저장하지 않고 미리보기만.

주의: 본 스크립트는 정보 제공용이며 투자 조언이 아님. 실제 체결가는 당일 종가와 다를 수 있음.
"""
import os, sys, json, argparse, datetime as dt

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root
os.chdir(BASE)

import pandas as pd
import yaml
import yfinance as yf
from pandas.tseries.holiday import (AbstractHolidayCalendar, Holiday, nearest_workday,
                                    USMartinLutherKingJr, USPresidentsDay, USMemorialDay,
                                    USLaborDay, USThanksgivingDay, GoodFriday)


class _NYSEHolidays(AbstractHolidayCalendar):
    """NYSE 휴장일 규칙(날짜 하드코딩 없이 규칙 기반). 콜럼버스/재향군인의날 제외, 굿프라이데이 포함."""
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
    """미국장(NYSE) 개장 여부 판정 → (is_open: bool, reason: str|None). 조기폐장·특별휴장 제외."""
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


def fmt(x):
    return f"${x:,.2f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="backtest/live/advisor_config.yaml")
    ap.add_argument("--dry-run", action="store_true", help="상태 저장 안 함(미리보기)")
    args = ap.parse_args()

    cfg = load_cfg(args.config)
    core, sig_t, sat = cfg["core_ticker"], cfg["core_signal"], cfg["satellite_ticker"]
    budget, wc = float(cfg["monthly_budget"]), float(cfg["w_core"])
    win, buf = int(cfg["ma_window"]), float(cfg["buffer"])
    state_path, action_path = cfg["state_path"], cfg["action_path"]

    px = fetch([core, sig_t, sat])
    last_date = min(px[t].index[-1] for t in px)        # 공통 최신 영업일(=전일 종가)
    core_px = float(px[core].asof(last_date))
    sat_px = float(px[sat].asof(last_date))
    sig_close = float(px[sig_t].asof(last_date))
    ma = float(px[sig_t].loc[:last_date].tail(win).mean()) if len(px[sig_t].loc[:last_date]) >= win else float("nan")
    ratio = sig_close / ma if ma == ma and ma > 0 else float("nan")

    # ---- state load ----
    st = None
    if os.path.exists(state_path):
        with open(state_path, encoding="utf-8") as f:
            st = json.load(f)
        if "cash" not in st:          # 구(舊) 정수주 포맷 → 소수점 포맷으로 재초기화
            st = None
    if st is None:
        # 최초 실행: 신호 초기화(밴드 위면 ON, 아래면 OFF)
        init_on = ratio == ratio and ratio > 1.0
        st = {"core_shares": 0.0, "sat_shares": 0.0, "cash": 0.0,
              "core_on": bool(init_on), "last_contrib_month": None,
              "history": []}

    now = dt.datetime.now()
    today = now.date()
    actions = []

    is_open, reason = market_status(today)
    if not is_open:
        # 미국장 휴장일: 매매·적립·리밸런싱 모두 보류(상태 변경 없음)
        actions.append(f"🛌 오늘 미국장 휴장 ({reason}) — 매매 없음 (다음 개장일에 처리)")
    else:
        # ---- 1) 월 적립 (현금 유입) — 그 달 첫 '개장일'에 ----
        ym = f"{today.year}-{today.month:02d}"
        new_month = st["last_contrib_month"] != ym
        if new_month:
            st["cash"] += budget
            st["last_contrib_month"] = ym
            actions.append(f"💰 월 적립 {fmt(budget)} 유입")

        # ---- 2) 코어(SOXL) 신호 buffer 히스테리시스 ----
        prev_on = st["core_on"]
        if ratio == ratio:
            if prev_on and ratio < 1 - buf:
                st["core_on"] = False
            elif (not prev_on) and ratio > 1 + buf:
                st["core_on"] = True
        flipped = st["core_on"] != prev_on
        if flipped:
            actions.append(f"🔁 신호 전환 {'OFF→ON' if st['core_on'] else 'ON→OFF'} (SOXX/120MA={ratio:.3f})")

        # ---- 3) 소수점 목표비중 리밸런싱 (매월 적립일 또는 신호전환시) ----
        do_rebal = new_month or flipped
        if do_rebal:
            total_eq = st["cash"] + st["core_shares"] * core_px + st["sat_shares"] * sat_px
            w_core_eff = wc if st["core_on"] else 0.0     # SOXL OFF면 코어 0% → 현금
            tgt_core_v = w_core_eff * total_eq
            tgt_sat_v = (1 - wc) * total_eq
            for nm, px_now, cur_sh, tgt_v in [
                    (core, core_px, st["core_shares"], tgt_core_v),
                    (sat, sat_px, st["sat_shares"], tgt_sat_v)]:
                d_sh = tgt_v / px_now - cur_sh
                amt = abs(d_sh) * px_now
                if amt < 1.0:                              # $1 미만 변화는 무시
                    continue
                mark, verb = ("🟢", "매수") if d_sh > 0 else ("🔴", "매도")
                actions.append(f"{mark} {verb} {nm}  {abs(d_sh):.4f}주  (~{fmt(amt)}, 종가 {fmt(px_now)}) → 목표 {fmt(tgt_v)}")
            st["core_shares"] = tgt_core_v / core_px
            st["sat_shares"] = tgt_sat_v / sat_px
            st["cash"] = round(total_eq - tgt_core_v - tgt_sat_v, 2)

        if not actions:
            actions.append("✅ 오늘 매매 없음 — 보유 유지 (리밸런싱은 매월 적립일·신호전환시에만)")

    # ---- 평가 ----
    core_val = st["core_shares"] * core_px
    sat_val = st["sat_shares"] * sat_px
    cash = st["cash"]
    total = core_val + sat_val + cash
    cw = core_val / total * 100 if total > 0 else 0
    sw = sat_val / total * 100 if total > 0 else 0
    kw = cash / total * 100 if total > 0 else 0

    lines = []
    lines.append("=" * 56)
    lines.append(f" 데일리 어드바이저  실행 {now:%Y-%m-%d %H:%M:%S} (KST)")
    lines.append(f" 기준 데이터: 전일 종가 {last_date.date()}")
    lines.append(f" 오늘 미국장: {'개장' if is_open else '휴장 — ' + str(reason)}")
    lines.append("=" * 56)
    lines.append(f"[신호] {sig_t} 종가 {fmt(sig_close)} / {win}일선 {fmt(ma)} = ratio {ratio:.3f}")
    on_txt = "ON(보유)" if st["core_on"] else "OFF(현금)"
    lines.append(f"       완충밴드 ±{buf*100:.0f}%  → 코어 {core} 신호: {on_txt}")
    lines.append("")
    lines.append("[오늘 할 일]")
    for a in actions:
        lines.append(f"  - {a}")
    lines.append("")
    lines.append("[현재 포트폴리오(추정, 소수점)]")
    lines.append(f"  {core}: {st['core_shares']:.4f}주 ({fmt(core_val)}, {cw:.0f}%)  |  {sat}: {st['sat_shares']:.4f}주 ({fmt(sat_val)}, {sw:.0f}%)")
    lines.append(f"  현금: {fmt(cash)} ({kw:.0f}%)")
    lines.append(f"  목표비중: {core} {wc*100:.0f}% / {sat} {(1-wc)*100:.0f}%  (SOXL 신호 OFF시 코어→현금)")
    lines.append(f"  총평가: {fmt(total)}")
    lines.append("-" * 56)
    lines.append("※ 정보 제공용, 투자조언 아님. 체결가는 당일 종가와 다를 수 있음.")
    report = "\n".join(lines)
    print(report)

    # ---- persist ----
    if not args.dry_run:
        st.setdefault("history", []).append({"run_at": now.isoformat(timespec="seconds"),
                                             "date": str(today), "ref_close": str(last_date.date()),
                                             "actions": actions, "total": round(total, 2)})
        st["history"] = st["history"][-400:]
        os.makedirs(os.path.dirname(state_path), exist_ok=True)
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(st, f, ensure_ascii=False, indent=2)
        with open(action_path, "w", encoding="utf-8") as f:
            f.write(report + "\n")


if __name__ == "__main__":
    main()
