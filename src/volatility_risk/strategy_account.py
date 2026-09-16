"""Frozen five-session scalar equity/cash accountant, extracted without numerical edits."""

import numpy as np
import pandas as pd
from numba import njit
from .fhs import empirical
from .io import save

COLS = [
    "pre_NAV",
    "post_NAV",
    "end_NAV",
    "units",
    "cash",
    "drift",
    "exposure",
    "fee",
    "fee_fraction",
    "signed_notional",
    "turnover",
    "net_return",
    "cash_next",
    "old_units",
    "old_cash",
    "target",
]
PERIODS = {
    "ALL": None,
    "DOTCOM": ("2000-01-01", "2002-12-31"),
    "GFC": ("2007-01-01", "2009-12-31"),
    "2011": ("2011-01-01", "2011-12-31"),
    "2015_2016": ("2015-01-01", "2016-12-31"),
    "2018Q4": ("2018-10-01", "2018-12-31"),
    "COVID": ("2020-02-19", "2020-06-30"),
    "2022": ("2022-01-01", "2022-12-31"),
    "2023_PLUS": ("2023-01-01", "2100-01-01"),
    "2024_PLUS": ("2024-01-01", "2100-01-01"),
    "EX_MAJOR_SHOCKS": None,
}
NAMED = [
    "GFC",
    "2011",
    "2015_2016",
    "2018Q4",
    "COVID",
    "2022",
    "2023_PLUS",
    "2024_PLUS",
]


def mask_period(start, end, name):
    start = np.asarray(start, dtype="datetime64[ns]")
    end = np.asarray(end, dtype="datetime64[ns]")
    if name == "EX_MAJOR_SHOCKS":
        m = np.ones(len(start), bool)
        for k in ["GFC", "COVID", "2022"]:
            lo, hi = map(np.datetime64, PERIODS[k])
            m &= ~((start <= hi) & (end >= lo))
        return m
    if PERIODS[name] is None:
        return np.ones(len(start), bool)
    lo, hi = map(np.datetime64, PERIODS[name])
    return (start >= lo) & (end <= hi)


def probability(z, s, c, w, loss):
    if w <= 0:
        return float(c < -loss)
    return np.searchsorted(z, (-loss - (1 - w) * c) / (w * s), side="left") / len(z)


def timeline(z, x, phase, cash, daily=False):
    selected = z if daily else z[z.index.to_numpy() % 5 == phase]
    start = int(selected.index.min())
    last = int(selected.index.max())
    end = last + (1 if daily else 5)
    origins = np.arange(start, end)
    price = x.Open.to_numpy()[np.arange(start + 1, end + 2)]
    starts = np.arange(0, len(origins), 1 if daily else 5)
    decision = origins[starts]
    assert np.isin(decision, z.index).all()
    meta = pd.DataFrame(
        dict(
            origin_index=origins,
            execution_session=x.session.iloc[origins + 1].to_numpy(),
            end_session=x.session.iloc[origins + 2].to_numpy(),
            execution_timestamp=x.open_ts.iloc[origins + 1].to_numpy(),
            end_timestamp=x.open_ts.iloc[origins + 2].to_numpy(),
            price=price[:-1],
            next_price=price[1:],
            market_return=price[1:] / price[:-1] - 1,
            HOLD=x.HOLD.iloc[origins + 1].to_numpy(),
        )
    )
    rc = np.zeros(len(origins))
    decpos = np.zeros(len(origins), int)
    for startpos, orig in zip(starts, decision):
        n = 1 if daily else 5
        quote = z.loc[orig, "cash_quote_yield"] / 100 if cash == "PROXY" else 0.0
        entry = pd.Timestamp(meta.execution_session.iloc[startpos])
        day = np.array(
            [
                (pd.Timestamp(t) - entry).days
                for t in meta.execution_session.iloc[startpos : startpos + n]
            ]
        )
        nextday = np.array(
            [
                (pd.Timestamp(t) - entry).days
                for t in meta.end_session.iloc[startpos : startpos + n]
            ]
        )
        rc[startpos : startpos + n] = (1 + quote * nextday / 365) / (
            1 + quote * day / 365
        ) - 1
        decpos[startpos : startpos + n] = orig
    meta["cash_return"] = rc
    meta["decision_origin_index"] = decpos
    er = np.ones(len(origins))
    cr = np.ones(len(origins))
    for startpos in starts:
        n = 1 if daily else 5
        er[startpos : startpos + n] = price[startpos : startpos + n] / price[startpos]
        cr[startpos : startpos + n] = np.r_[
            1.0, np.cumprod(1 + rc[startpos : startpos + n - 1])
        ]
    meta["equity_drift_factor"] = er
    meta["cash_drift_factor"] = cr
    meta["decision_time"] = [z.loc[o, "forecast_timestamp"] for o in decpos]
    meta["rebalance"] = False
    meta.loc[starts, "rebalance"] = True
    assert np.all(
        pd.to_datetime(meta.decision_time, utc=True)
        < pd.to_datetime(meta.execution_timestamp, utc=True)
    )
    return meta, price, starts


@njit(cache=False)
def simulate(price, rc, target, rebalance, fee, hold=False):
    n = len(rc)
    a = np.zeros((n, 16))
    cash = 1.0
    units = 0.0
    for i in range(n):
        N = cash + units * price[i]
        old = units * price[i]
        drift = old / N
        oc = cash
        ou = units
        f = 0.0
        delta = 0.0
        w = drift
        if rebalance[i] and (not hold or i == 0):
            w = target[i]
            new = (
                w * (N + fee * old) / (1 + fee * w)
                if w >= drift
                else w * (N - fee * old) / (1 - fee * w)
            )
            delta = new - old
            f = fee * abs(delta)
            cash -= delta + f
            units = new / price[i]
        post = cash + units * price[i]
        weight = units * price[i] / post
        cn = cash * (1 + rc[i])
        end = cn + units * price[i + 1]
        a[i, :] = np.array(
            [
                N,
                post,
                end,
                units,
                cash,
                drift,
                weight,
                f,
                f / N,
                delta,
                abs(delta) / N,
                end / N - 1,
                cn,
                ou,
                oc,
                w,
            ]
        )
        cash = cn
    return a


def account(meta, price, target, bp, hold=False):
    a = simulate(
        price,
        meta.cash_return.to_numpy(),
        target,
        meta.rebalance.to_numpy(),
        bp / 10000,
        hold,
    )
    z = pd.DataFrame(a, columns=COLS)
    z = pd.concat([meta.reset_index(drop=True), z], axis=1)
    assert (
        z.cash.min() > -1e-11
        and z.exposure.min() > -1e-12
        and z.exposure.max() < 1 + 1e-12
    )
    assert np.max(abs(z.post_NAV - z.pre_NAV + z.fee)) < 1e-10
    return z


def match(meta, price, dynamic, bp, mask=None):
    m = np.ones(len(meta), bool) if mask is None else mask
    goal = dynamic.exposure.to_numpy()[m].mean()
    lo = 0.0
    hi = 1.0
    er = meta.equity_drift_factor.to_numpy()[m]
    cr = meta.cash_drift_factor.to_numpy()[m]
    for _ in range(36):
        q = (lo + hi) / 2
        mean = np.mean(q * er / (q * er + (1 - q) * cr))
        if mean < goal:
            lo = q
        else:
            hi = q
    q = (lo + hi) / 2
    out = account(meta, price, np.full(len(meta), q), bp)
    error = abs(out.exposure.to_numpy()[m].mean() - goal)
    assert error < 1e-8, error
    return out, q, error


def cycles_slow(ledger, z, histories, budget, cash):
    rec = []
    n = len(ledger)
    for k in range(0, n, 5):
        a = ledger.iloc[k : k + 5]
        if len(a) != 5:
            continue
        orig = int(a.decision_origin_index.iloc[0])
        f = z.loc[orig]
        month = f.session.strftime("%Y-%m")
        zz = histories[month]
        w = a.target.iloc[0]
        actual_w = a.exposure.iloc[0]
        fee = a.fee_fraction.iloc[0]
        C = f.cash5 if cash == "PROXY" else 0.0
        net = a.end_NAV.iloc[-1] / a.pre_NAV.iloc[0] - 1
        gross = a.end_NAV.iloc[-1] / a.post_NAV.iloc[0] - 1
        nav = np.r_[a.pre_NAV.iloc[0], a.post_NAV.iloc[0], a.end_NAV.to_numpy()]
        D = np.max(1 - nav / np.maximum.accumulate(nav))
        q = (1 - w) * C + w * f.q_fhs
        e = (1 - w) * C + w * f.e_fhs
        qn = (1 - fee) * (1 + q) - 1
        en = (1 - fee) * (1 + e) - 1
        probgross = probability(zz, f.scale, C, w, budget["L"])
        effective = (1 - budget["L"]) / (1 - fee) - 1
        probnet = probability(zz, f.scale, C, w, -effective)
        varscale = np.sqrt(np.sum(a.exposure.to_numpy() ** 2 * a.HOLD.to_numpy()))
        rec.append(
            dict(
                origin_index=orig,
                signal_session=f.session,
                entry_session=a.execution_session.iloc[0],
                exit_session=a.end_session.iloc[-1],
                p=f.p,
                R5_equity=f.R5,
                R1_equity=f.R1,
                entry_weight=actual_w,
                entry_target=w,
                target_roundoff=actual_w - w,
                prob_budget_gross_float_holdings=probability(
                    zz, f.scale, C, actual_w, budget["L"]
                ),
                fee_fraction=fee,
                cash5=C,
                net5=net,
                gross5=gross,
                path_D=D,
                q_pred=qn,
                e_pred=en,
                p_loss2=probability(zz, f.scale, C, w, -((1 - 0.02) / (1 - fee) - 1)),
                p_loss5=probability(zz, f.scale, C, w, -((1 - 0.05) / (1 - fee) - 1)),
                predicted_vol_scale=w * f.scale,
                realized_proxy_scale=varscale,
                vol_budget=budget["Bvol"],
                ES_budget=budget["BES"],
                loss_budget=budget["L"],
                ES_gross=-e,
                ES_net=-en,
                prob_budget_gross=probgross,
                prob_budget_net=probnet,
                projected_path_mean_first_order=w * f.dd_fhs,
                hit=float(net <= qn),
                ES_identification=(qn - en - (net <= qn) * (qn - net) / 0.05)
                / max(abs(en), 1e-12),
                held_days=(
                    pd.Timestamp(a.end_session.iloc[-1])
                    - pd.Timestamp(a.execution_session.iloc[0])
                ).days,
            )
        )
    return pd.DataFrame(rec)


def cycles(ledger, z, histories, budget, cash):
    n = len(ledger) // 5 * 5
    a = ledger.iloc[:n]
    first = a.iloc[::5]
    last = a.iloc[4::5]
    f = z.loc[first.decision_origin_index.to_numpy()].reset_index(drop=True)
    w = first.target.to_numpy()
    actual_w = first.exposure.to_numpy()
    fee = first.fee_fraction.to_numpy()
    C = f.cash5.to_numpy() if cash == "PROXY" else np.zeros(len(f))
    net = last.end_NAV.to_numpy() / first.pre_NAV.to_numpy() - 1
    gross = last.end_NAV.to_numpy() / first.post_NAV.to_numpy() - 1
    nav = np.column_stack(
        [first.pre_NAV, first.post_NAV, a.end_NAV.to_numpy().reshape(-1, 5)]
    )
    D = np.max(1 - nav / np.maximum.accumulate(nav, axis=1), axis=1)
    q = (1 - w) * C + w * f.q_fhs.to_numpy()
    e = (1 - w) * C + w * f.e_fhs.to_numpy()
    qn = (1 - fee) * (1 + q) - 1
    en = (1 - fee) * (1 + e) - 1

    def probs(loss, weights=None):
        ww = w if weights is None else weights
        loss = np.broadcast_to(loss, len(f))
        answer = np.zeros(len(f))
        month = f.session.dt.strftime("%Y-%m").to_numpy()
        s = f.scale.to_numpy()
        for key in np.unique(month):
            m = (month == key) & (ww > 0)
            zz = histories[key]
            threshold = (-loss[m] - (1 - ww[m]) * C[m]) / (ww[m] * s[m])
            answer[m] = np.searchsorted(zz, threshold, side="left") / len(zz)
        m = ww <= 0
        answer[m] = (C[m] < -loss[m]).astype(float)
        return answer

    return pd.DataFrame(
        dict(
            origin_index=first.decision_origin_index.to_numpy(),
            signal_session=f.session.to_numpy(),
            entry_session=first.execution_session.to_numpy(),
            exit_session=last.end_session.to_numpy(),
            p=f.p.to_numpy(),
            R5_equity=f.R5.to_numpy(),
            R1_equity=f.R1.to_numpy(),
            entry_weight=actual_w,
            entry_target=w,
            target_roundoff=actual_w - w,
            prob_budget_gross_float_holdings=probs(budget["L"], actual_w),
            fee_fraction=fee,
            cash5=C,
            net5=net,
            gross5=gross,
            path_D=D,
            q_pred=qn,
            e_pred=en,
            p_loss2=probs(1 - (1 - 0.02) / (1 - fee)),
            p_loss5=probs(1 - (1 - 0.05) / (1 - fee)),
            predicted_vol_scale=w * f.scale.to_numpy(),
            realized_proxy_scale=np.sqrt(
                np.sum(
                    (a.exposure.to_numpy() ** 2 * a.HOLD.to_numpy()).reshape(-1, 5),
                    axis=1,
                )
            ),
            vol_budget=budget["Bvol"],
            ES_budget=budget["BES"],
            loss_budget=budget["L"],
            ES_gross=-e,
            ES_net=-en,
            prob_budget_gross=probs(budget["L"]),
            prob_budget_net=probs(1 - (1 - budget["L"]) / (1 - fee)),
            projected_path_mean_first_order=w * f.dd_fhs.to_numpy(),
            hit=(net <= qn).astype(float),
            ES_identification=(qn - en - (net <= qn) * (qn - net) / 0.05)
            / np.maximum(abs(en), 1e-12),
            held_days=(
                pd.to_datetime(last.end_session.to_numpy())
                - pd.to_datetime(first.execution_session.to_numpy())
            ).days,
        )
    )
