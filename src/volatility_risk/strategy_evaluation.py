"""Unchanged final decision-layer risk, cost and exposure attribution equations."""

import numpy as np
import pandas as pd
from numba import njit
from .strategy_account import mask_period
from .fhs import empirical


def drawdown_reference(r, m=None):
    n = len(r)
    m = np.ones(n, bool) if m is None else m
    best = 0.0
    longest = 0
    maxdur = 0
    censored = False
    starts = np.where(m & ~np.r_[False, m[:-1]])[0]
    ends = np.where(m & ~np.r_[m[1:], False])[0] + 1
    for start, end in zip(starts, ends):
        nav = np.r_[1.0, np.cumprod(1 + r[start:end])]
        peak = 1.0
        pi = 0
        segmentmax = 0.0
        for j in range(1, len(nav)):
            if nav[j] >= peak:
                longest = max(longest, j - pi if j - pi > 1 else 0)
                peak = nav[j]
                pi = j
            segmentmax = max(segmentmax, 1 - nav[j] / peak)
        dd = 1 - nav / np.maximum.accumulate(nav)
        ti = int(np.argmax(dd))
        p0 = int(np.argmax(nav[: ti + 1]))
        hits = np.where(nav[ti + 1 :] >= nav[p0])[0]
        dur = (ti + 1 + int(hits[0]) if len(hits) else len(nav) - 1) - p0
        if segmentmax > best:
            best = segmentmax
            maxdur = dur
            censored = not len(hits)
    return best, maxdur, censored, longest


@njit(cache=False)
def drawdown(r, m=None):
    n = len(r)
    keep = np.ones(n, np.bool_) if m is None else m
    best = 0.0
    bestpeak = 0
    besttrough = 0
    bestend = 0
    longest = 0
    bestrecovery = -1
    nav = 1.0
    peak = 1.0
    peakidx = 0
    segment = 0
    peakval = 1.0
    for i in range(n):
        if not keep[i]:
            nav = 1.0
            peak = 1.0
            peakidx = i + 1
            segment = i + 1
            continue
        nav *= 1 + r[i]
        if nav >= peak:
            if i + 1 - peakidx > 1:
                longest = max(longest, i + 1 - peakidx)
            peak = nav
            peakidx = i + 1
        dd = 1 - nav / peak
        if dd > best:
            best = dd
            bestpeak = peakidx
            besttrough = i + 1
            bestend = i + 1
            bestrecovery = -1
            peakval = peak
        if besttrough >= segment and best > 0:
            bestend = i + 1
            if bestrecovery < 0 and i + 1 > besttrough and nav >= peakval:
                bestrecovery = i + 1
    duration = (bestend if bestrecovery < 0 else bestrecovery) - bestpeak
    return best, duration, bestrecovery < 0, longest


def summarize(a, cyc, period="ALL"):
    m = mask_period(a.execution_session, a.end_session, period)
    z = a.loc[m]
    n = len(z)
    if n < 20:
        return None
    years = (
        (
            pd.to_datetime(z.end_session) - pd.to_datetime(z.execution_session)
        ).dt.total_seconds()
        / 86400
    ).sum() / 365.25
    r = z.net_return.to_numpy()
    cash = z.cash_return.to_numpy()
    market = z.market_return.to_numpy()
    excess = r - cash
    vol = np.std(r, ddof=1) * np.sqrt(252)
    arith = r.mean() * 252
    down = np.sqrt(np.mean(np.minimum(r, 0) ** 2) * 252)
    exdown = np.sqrt(np.mean(np.minimum(excess, 0) ** 2) * 252)
    mdd, dur, cens, longest = drawdown(a.net_return.to_numpy(), m)
    cagr = np.expm1(np.log1p(r).sum() / years)
    cm = mask_period(cyc.entry_session, cyc.exit_session, period)
    b = cyc.loc[cm]
    nn = len(b)
    q, e = empirical(b.net5.to_numpy()) if nn else (np.nan, np.nan)
    return dict(
        n=n,
        cycles=nn,
        years=years,
        CAGR=cagr,
        annual_return=arith,
        annual_vol=vol,
        downside_deviation=down,
        Sharpe=(
            excess.mean() * 252 / (np.std(excess, ddof=1) * np.sqrt(252))
            if np.std(excess) > 0
            else np.nan
        ),
        Sortino=excess.mean() * 252 / exdown if exdown > 0 else np.nan,
        Calmar=cagr / mdd if mdd > 0 else np.nan,
        MaxDD=mdd,
        recovery_sessions=dur,
        recovery_censored=bool(cens),
        longest_completed_recovery=longest,
        average_exposure=z.exposure.mean(),
        cash_share=1 - z.exposure.mean(),
        beta=np.cov(r, market, ddof=1)[0, 1] / np.var(market, ddof=1),
        annual_turnover=z.turnover.mean() * 252,
        annual_fee_drag=z.fee_fraction.mean() * 252,
        VaR95_5D=-q,
        ES95_5D=-e,
        loss2_frequency=(b.net5 < -0.02).mean(),
        loss5_frequency=(b.net5 < -0.05).mean(),
        mean_path_D=b.path_D.mean(),
        actual_5D_proxy_ann=np.sqrt(np.mean(b.realized_proxy_scale**2))
        * np.sqrt(252 / 5),
        vol_proxy_overshoot=(b.realized_proxy_scale > b.vol_budget).mean(),
        vol_prediction_rmse=np.sqrt(
            np.mean((b.realized_proxy_scale - b.predicted_vol_scale) ** 2)
        ),
        ES_budget_predicted_gross_breach=(b.ES_gross > b.ES_budget + 1e-12).mean(),
        ES_budget_predicted_net_breach=(b.ES_net > b.ES_budget + 1e-12).mean(),
        probability_budget_predicted_gross_breach=(b.prob_budget_gross > 0.05).mean(),
        probability_budget_predicted_net_breach=(b.prob_budget_net > 0.05).mean(),
        loss_budget_realized_frequency=(b.net5 < -b.loss_budget).mean(),
        VaR_hit=b.hit.mean(),
        ES_identification=b.ES_identification.mean(),
        expected_loss2=b.p_loss2.mean(),
        expected_loss5=b.p_loss5.mean(),
        path_projection_approx=b.projected_path_mean_first_order.mean(),
    )


def opportunities(c, period):
    m = mask_period(c.entry_session, c.exit_session, period)
    z = c.loc[m]
    high = z.p >= 0.8
    pos = z.R5_equity > 0
    neg = z.R5_equity < 0
    rebound = (z.R1_equity < 0) & pos

    def part(g):
        denom = z.loc[g, "R5_equity"].sum()
        return (
            (z.loc[g, "entry_weight"] * z.loc[g, "R5_equity"]).sum() / denom
            if denom
            else np.nan
        )

    missed = ((1 - z.entry_weight) * z.R5_equity).where(high & pos, 0).sum()
    avoided = (-(1 - z.entry_weight) * z.R5_equity).where(high & neg, 0).sum()
    return dict(
        cycles=len(z),
        high_positive_n=int((high & pos).sum()),
        high_negative_n=int((high & neg).sum()),
        high_positive_participation=part(high & pos),
        rebound_participation=part(high & rebound),
        rebound_n=int((high & rebound).sum()),
        high_missed_upside=missed,
        high_downside_avoided=avoided,
        missed_upside_per_downside_avoided=missed / avoided if avoided > 0 else np.nan,
        all_positive_participation=part(pos),
        all_negative_participation=part(neg),
    )


def attribute(a, b, matched, ca, cb, cs, period):
    m = mask_period(a.execution_session, a.end_session, period)
    ma = summarize(a, ca, period)
    mb = summarize(b, cb, period)
    ms = summarize(matched, cs, period)
    if ma is None:
        return None
    w = a.exposure.to_numpy()[m]
    f = a.fee_fraction.to_numpy()[m]
    fb = b.fee_fraction.to_numpy()[m]
    r = a.market_return.to_numpy()[m]
    cash = a.cash_return.to_numpy()[m]
    mean = w.mean()
    components = np.column_stack(
        [
            (mean - 1) * r,
            (w - mean) * r,
            (1 - w) * cash,
            fb - f,
            -f * (w * r + (1 - w) * cash) + fb * r,
        ]
    )
    gap = a.net_return.to_numpy()[m] - b.net_return.to_numpy()[m]
    err = np.max(abs(components.sum(axis=1) - gap))
    assert err < 1e-12
    ra = a.net_return.to_numpy()[m]
    rb = b.net_return.to_numpy()[m]
    factor = np.divide(
        np.log1p(ra) - np.log1p(rb), gap, out=1 / (1 + rb), where=abs(gap) > 1e-14
    )
    loggap = np.log1p(ma["CAGR"]) - np.log1p(mb["CAGR"])
    link = (ma["CAGR"] - mb["CAGR"]) / loggap if abs(loggap) > 1e-14 else 1 + mb["CAGR"]
    linked = (components * factor[:, None]).sum(axis=0) / ma["years"] * link
    result = dict(
        identity_error=err,
        CAGR_link_error=abs(linked.sum() - (ma["CAGR"] - mb["CAGR"])),
        CAGR_gap=ma["CAGR"] - mb["CAGR"],
        matched_target=float(matched.target.iloc[0]),
        dynamic_average=mean,
        static_average=matched.exposure.to_numpy()[m].mean(),
        matched_CAGR_gap=ma["CAGR"] - ms["CAGR"],
        Return_Retention=ma["CAGR"] / mb["CAGR"] if mb["CAGR"] > 0 else np.nan,
        annual_cost=ma["annual_fee_drag"],
    )
    for j, name in enumerate(
        ["exposure_opportunity", "dynamic_timing", "cash", "cost", "interaction"]
    ):
        result["annual_" + name] = components[:, j].mean() * 252
        result["CAGR_" + name] = linked[j]
    for k in ["annual_vol", "ES95_5D", "MaxDD"]:
        result[k + "_total_reduction"] = mb[k] - ma[k]
        result[k + "_lower_exposure_effect"] = mb[k] - ms[k]
        result[k + "_dynamic_effect"] = ms[k] - ma[k]
        result[k + "_dynamic_fraction"] = 1 - ma[k] / ms[k] if ms[k] > 0 else np.nan
        result[k + "_BH_reduction"] = 1 - ma[k] / mb[k] if mb[k] > 0 else np.nan
        assert abs((mb[k] - ms[k]) + (ms[k] - ma[k]) - (mb[k] - ma[k])) < 1e-12
    return result
