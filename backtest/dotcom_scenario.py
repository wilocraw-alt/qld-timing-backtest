#!/usr/bin/env python3
"""
가상 시나리오: 닷컴버블 '포 호스맨' ETF (1x) vs 3배 레버리지 (3x).

- 포 호스맨(데이터 가용): Microsoft, Intel, Cisco, Oracle 등가중 지수 (일간 리밸런싱).
  (원래 자주 거론된 Dell/Sun/EMC는 상장폐지·인수로 1999~2003 데이터 없음 → 제외.)
- 3x ETF: 지수 일간수익률 ×3 으로 매일 재설정되는 합성 레버리지(총비용 0 가정;
  실제는 연 ~1% 수수료+차입비용 추가 → 결과는 낙관적 상한).
- 기간: 나스닥 고점 2000-03-10 기준, 1년 전(1999-03-10) ~ 3년 후(2003-03-10).
- 초기자본 $10,000. 비교 전략: 일괄 B&H / 분할매수(DCA) / 추세추종(200일선) × {1x, 3x}.
- 신호는 전일 종가 기준(미래참조 없음), 체결은 당일 종가.
"""
import numpy as np
import pandas as pd
import yfinance as yf

HORSEMEN = ["MSFT", "INTC", "CSCO", "ORCL"]
PEAK = pd.Timestamp("2000-03-10")
WIN_START = pd.Timestamp("1999-03-10")
WIN_END = pd.Timestamp("2003-03-10")
CAP = 10000.0


def load_index():
    px = {}
    for t in HORSEMEN:
        h = yf.Ticker(t).history(start="1998-01-01", end="2003-03-20", auto_adjust=True)
        px[t] = h["Close"]
    df = pd.concat(px, axis=1).dropna()
    df.index = df.index.tz_localize(None)
    idx_ret = df.pct_change().mean(axis=1)          # equal-weight daily return
    idx = (1 + idx_ret.fillna(0)).cumprod()
    lev3 = (1 + 3 * idx_ret.fillna(0)).cumprod()    # synthetic daily 3x
    return idx.rename("1x"), pd.DataFrame({"1x": idx, "3x": lev3}), idx.rolling(200).mean()


def mdd(s):
    return float((1 - s / s.cummax()).max())


def run_all():
    idx, prices, ma200 = load_index()
    mask = (prices.index >= WIN_START) & (prices.index <= WIN_END)
    win_idx = prices.index[mask]
    sig = (idx.shift(1) > ma200.shift(1))           # lagged → no look-ahead

    def bh(level):
        p = prices[level][mask]
        return CAP / p.iloc[0] * p

    def dca(level):
        sub = prices[level][mask]
        firsts = set(sub.groupby(pd.Series(sub.index).dt.to_period("M").values).head(1).index)
        slice_amt = CAP / len(firsts)
        cash, units, vals = CAP, 0.0, []
        for d in sub.index:
            if d in firsts:
                buy = min(slice_amt, cash); units += buy / sub[d]; cash -= buy
            vals.append(cash + units * sub[d])
        return pd.Series(vals, index=sub.index)

    def trend(level):
        p = prices[level]
        invested, cash, units, vals = False, CAP, 0.0, []
        for d in p.index:
            s = bool(sig.get(d, False))
            if s and not invested:
                units = cash / p[d]; cash = 0.0; invested = True
            elif (not s) and invested:
                cash = units * p[d]; units = 0.0; invested = False
            if WIN_START <= d <= WIN_END:
                vals.append(cash + units * p[d])
        return pd.Series(vals, index=win_idx)

    strategies = [
        ("B&H 1x", bh, "1x"), ("B&H 3x", bh, "3x"),
        ("DCA 1x", dca, "1x"), ("DCA 3x", dca, "3x"),
        ("Trend200 1x", trend, "1x"), ("Trend200 3x", trend, "3x"),
    ]
    rows = []
    for name, fn, lev in strategies:
        v = fn(lev); fv = float(v.iloc[-1])
        rows.append({"strategy": name, "final": round(fv, 0),
                     "total_return": fv / CAP - 1, "MDD": mdd(v)})
    return idx, prices, mask, rows


if __name__ == "__main__":
    idx, prices, mask, rows = run_all()
    print(f"포 호스맨 등가중 지수 (MSFT/INTC/CSCO/ORCL)")
    print(f"창: {WIN_START.date()} ~ {WIN_END.date()} (고점 {PEAK.date()})")
    print(f"지수 1x — 창시작 {idx[mask].iloc[0]:.3f}  고점 {idx.asof(PEAK):.3f}  창끝 {idx[mask].iloc[-1]:.3f}")
    print(f"  고점대비 최종 1x: {idx[mask].iloc[-1]/idx.asof(PEAK)-1:+.1%}\n")
    print(f"{'전략':14s} {'최종$':>10s} {'총수익':>9s} {'MDD':>6s}")
    for r in rows:
        print(f"{r['strategy']:14s} {r['final']:>10,.0f} {r['total_return']:>+8.1%} {r['MDD']*100:>5.0f}%")
