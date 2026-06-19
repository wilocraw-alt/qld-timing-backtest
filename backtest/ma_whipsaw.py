#!/usr/bin/env python3
"""
이동평균 기준선(120일 vs 200일) + 휩쏘 완화 변형 비교.
- 신호: SOXL은 1x 반도체지수(SOXX), QLD는 QQQ의 N일 이동평균(미래참조 방지 위해 전일 데이터로 판정).
- 휩쏘 완화: plain / buffer(±b%) / confirm(k일 연속) / monthly(월1회 판정).
- 전략: 무규칙 보유(hold), 규칙(rule), 바벨(60% hold + 40% rule).
- 기간: 강세장 2011~2026 월 $300 DCA / 실제 폭락(2022, COVID).
- 지표: 최종액, MWRR(강세), MDD, 매매전환 횟수(휩쏘 프록시).
"""
import numpy as np, pandas as pd, yfinance as yf

def load(t, start="2009-06-01"):
    s = yf.Ticker(t).history(start=start, end="2026-06-19", auto_adjust=True)["Close"]
    s.index = s.index.tz_localize(None); return s

PX = {t: load(t) for t in ["SOXL", "SOXX", "QLD", "QQQ"]}
DF = pd.concat(PX, axis=1).dropna()


def invested_series(sig_px, win, mode="plain", buffer=0.03, confirm=5, monthly=False):
    """전일 데이터로 판정한 '투자 상태' bool Series (미래참조 없음)."""
    ma = sig_px.rolling(win).mean()
    idx = sig_px.index
    month_first = set()
    if monthly:
        per = pd.Series(idx).dt.to_period("M").values
        seen = set()
        for i, m in enumerate(per):
            if m not in seen:
                seen.add(m); month_first.add(idx[i])
    inv = []
    state = False
    cnt = 0  # 연속 반대신호 카운트 (confirm용)
    for i in range(len(idx)):
        if i == 0 or np.isnan(ma.iloc[i-1]):
            inv.append(False); continue
        px_p, ma_p = sig_px.iloc[i-1], ma.iloc[i-1]
        if mode == "buffer":
            target = state
            if px_p > ma_p * (1 + buffer): target = True
            elif px_p < ma_p * (1 - buffer): target = False
        elif mode == "confirm":
            above = bool(px_p > ma_p)
            if above != state:        # signal disagrees with current position
                cnt += 1
                if cnt >= confirm:    # enough consecutive days → flip
                    state = above; cnt = 0
            else:                     # signal agrees → reset counter
                cnt = 0
            target = state
        else:  # plain
            target = bool(px_p > ma_p)
        if monthly and idx[i] not in month_first:
            target = state
        state = target
        inv.append(state)
    return pd.Series(inv, index=idx)


def mdd(s): return float((1 - s / s.cummax()).max())
def irr(cfs):
    lo, hi = -0.95, 5.0; f = lambda r: sum(c/((1+r)**k) for k, c in enumerate(cfs))
    for _ in range(200):
        m = (lo+hi)/2; lo, hi = (m, hi) if f(m) > 0 else (lo, m)
    return (1+(lo+hi)/2)**12 - 1


def lump(asset, inv, window):
    sub = DF.loc[window[0]:window[1]]; p = sub[asset]; iv = inv.reindex(sub.index).fillna(False)
    cash, units, on, vals, flips = 10000.0, 0.0, False, [], 0
    for d in sub.index:
        want = bool(iv[d])
        if want and not on: units = cash/p[d]; cash = 0; on = True; flips += 1
        elif (not want) and on: cash = units*p[d]; units = 0; on = False; flips += 1
        vals.append(cash + units*p[d])
    return pd.Series(vals, index=sub.index), flips


def dca(asset, inv, window):
    sub = DF.loc[window[0]:window[1]]; p = sub[asset]; iv = inv.reindex(sub.index).fillna(False)
    firsts = set(sub.groupby(pd.Series(sub.index).dt.to_period("M").values).head(1).index)
    cash, units, vals, contribs, flips, on = 0.0, 0.0, [], [], 0, True
    for d in sub.index:
        if d in firsts: cash += 300; contribs.append(-300)
        want = bool(iv[d])
        if want:
            if cash > 0: units += cash/p[d]; cash = 0
            if not on: on = True; flips += 1
        else:
            if units > 0: cash += units*p[d]; units = 0
            if on: on = False; flips += 1
    # value path for MDD
        vals.append(cash + units*p[d])
    return pd.Series(vals, index=sub.index), contribs, flips


def hold_inv(window_asset):  # always invested
    return pd.Series(True, index=DF.index)


BULL = ("2011-01-01", "2026-06-19")
CRASH22 = ("2022-01-03", "2023-12-29")
COVID = ("2020-02-03", "2020-12-31")


def run_asset(asset, sigtkr):
    print("\n" + "#"*72); print(f"### {asset}  (신호: {sigtkr})"); print("#"*72)
    for win in [120, 200]:
        plain = invested_series(DF[sigtkr], win, "plain")
        buf = invested_series(DF[sigtkr], win, "buffer", buffer=0.03)
        conf = invested_series(DF[sigtkr], win, "confirm", confirm=5)
        mon = invested_series(DF[sigtkr], win, "plain", monthly=True)
        variants = [("규칙-plain", plain), ("규칙-buffer3%", buf),
                    ("규칙-confirm5d", conf), ("규칙-monthly", mon)]
        print(f"\n=== {win}일선 — 강세장 2011~2026 (월$300) ===")
        v, c, _ = dca(asset, hold_inv(asset), BULL)
        print(f"  {'무규칙 보유':16s} 최종 ${v.iloc[-1]:>11,.0f}  MWRR {irr(c+[v.iloc[-1]])*100:>5.1f}%  MDD {mdd(v)*100:>3.0f}%  flips   0")
        for nm, inv in variants:
            v, c, fl = dca(asset, inv, BULL)
            barb = 0.6*dca(asset, hold_inv(asset), BULL)[0] + 0.4*v
            print(f"  B {nm:14s} 최종 ${v.iloc[-1]:>11,.0f}  MWRR {irr(c+[v.iloc[-1]])*100:>5.1f}%  MDD {mdd(v)*100:>3.0f}%  flips {fl:>3d}")
        print(f"  --- {win}일선 — 2022 폭락 (일괄$10k) ---")
        vh, _ = lump(asset, hold_inv(asset), CRASH22)
        print(f"  {'무규칙 보유':16s} 최종 ${vh.iloc[-1]:>8,.0f}  총수익 {vh.iloc[-1]/1e4-1:>+5.0%}  MDD {mdd(vh)*100:>3.0f}%")
        for nm, inv in variants:
            vr, fl = lump(asset, inv, CRASH22)
            print(f"  B {nm:14s} 최종 ${vr.iloc[-1]:>8,.0f}  총수익 {vr.iloc[-1]/1e4-1:>+5.0%}  MDD {mdd(vr)*100:>3.0f}%  flips {fl}")


if __name__ == "__main__":
    run_asset("SOXL", "SOXX")
    run_asset("QLD", "QQQ")
