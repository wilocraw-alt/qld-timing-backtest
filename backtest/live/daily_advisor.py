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

import yaml
import yfinance as yf


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
    if os.path.exists(state_path):
        with open(state_path, encoding="utf-8") as f:
            st = json.load(f)
    else:
        # 최초 실행: 신호 초기화(밴드 위면 ON, 아래면 OFF)
        init_on = ratio == ratio and ratio > 1.0
        st = {"core_shares": 0, "sat_shares": 0,
              "core_reserve": 0.0, "sat_reserve": 0.0,
              "core_on": bool(init_on), "last_contrib_month": None,
              "history": []}

    now = dt.datetime.now()
    today = now.date()
    actions = []

    # ---- 1) 월 적립 ----
    ym = f"{today.year}-{today.month:02d}"
    is_weekday = today.weekday() < 5
    if st["last_contrib_month"] != ym and is_weekday:
        st["core_reserve"] += budget * wc
        st["sat_reserve"] += budget * (1 - wc)
        st["last_contrib_month"] = ym
        actions.append(f"💰 월 적립 {fmt(budget)} 유입 → 코어 {fmt(budget*wc)} / 위성 {fmt(budget*(1-wc))}")

    # ---- 2) 위성(QLD) 무규칙: 예약현금 전부 매수 ----
    if st["sat_reserve"] >= sat_px:
        q = int(st["sat_reserve"] // sat_px)
        cost = q * sat_px
        st["sat_shares"] += q
        st["sat_reserve"] = round(st["sat_reserve"] - cost, 2)
        actions.append(f"🟢 매수 {sat}  {q}주  (~{fmt(cost)}, 종가 {fmt(sat_px)})")

    # ---- 3) 코어(SOXL) 신호 buffer 히스테리시스 ----
    prev_on = st["core_on"]
    if ratio == ratio:
        if prev_on and ratio < 1 - buf:
            st["core_on"] = False
        elif (not prev_on) and ratio > 1 + buf:
            st["core_on"] = True
    flipped = st["core_on"] != prev_on

    if st["core_on"]:
        if flipped:
            actions.append(f"🔁 신호 OFF→ON (SOXX/120MA={ratio:.3f}) — {core} 재진입")
        if st["core_reserve"] >= core_px:
            q = int(st["core_reserve"] // core_px)
            cost = q * core_px
            st["core_shares"] += q
            st["core_reserve"] = round(st["core_reserve"] - cost, 2)
            actions.append(f"🟢 매수 {core}  {q}주  (~{fmt(cost)}, 종가 {fmt(core_px)})")
    else:
        if flipped and st["core_shares"] > 0:
            proceeds = st["core_shares"] * core_px
            actions.append(f"🔴 전량 매도 {core}  {st['core_shares']}주  (~{fmt(proceeds)}, 종가 {fmt(core_px)}) → 현금화")
            st["core_reserve"] = round(st["core_reserve"] + proceeds, 2)
            st["core_shares"] = 0
        elif st["core_reserve"] > 0:
            actions.append(f"⏸  {core} 신호 OFF (SOXX/120MA={ratio:.3f}) — 코어 현금 {fmt(st['core_reserve'])} 보관(매수 보류)")

    if not actions:
        actions.append("✅ 오늘 매매 없음 — 보유 유지")

    # ---- 평가 ----
    core_val = st["core_shares"] * core_px
    sat_val = st["sat_shares"] * sat_px
    cash = st["core_reserve"] + st["sat_reserve"]
    total = core_val + sat_val + cash

    lines = []
    lines.append("=" * 56)
    lines.append(f" 데일리 어드바이저  실행 {now:%Y-%m-%d %H:%M:%S} (KST)")
    lines.append(f" 기준 데이터: 전일 종가 {last_date.date()}")
    lines.append("=" * 56)
    lines.append(f"[신호] {sig_t} 종가 {fmt(sig_close)} / {win}일선 {fmt(ma)} = ratio {ratio:.3f}")
    on_txt = "ON(보유)" if st["core_on"] else "OFF(현금)"
    lines.append(f"       완충밴드 ±{buf*100:.0f}%  → 코어 {core} 신호: {on_txt}")
    lines.append("")
    lines.append("[오늘 할 일]")
    for a in actions:
        lines.append(f"  - {a}")
    lines.append("")
    lines.append("[현재 포트폴리오(추정)]")
    lines.append(f"  {core}: {st['core_shares']}주 ({fmt(core_val)})  |  {sat}: {st['sat_shares']}주 ({fmt(sat_val)})")
    lines.append(f"  현금: {fmt(cash)} (코어예약 {fmt(st['core_reserve'])}/위성예약 {fmt(st['sat_reserve'])})")
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
