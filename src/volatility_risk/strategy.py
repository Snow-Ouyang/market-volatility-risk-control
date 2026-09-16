"""Frozen Full VOL application; Core is secondary and matching is ex-post only."""

import hashlib
import numpy as np
import pandas as pd
from .io import save
from .fhs import empirical
from .strategy_account import account, timeline, cycles, match, PERIODS, mask_period
from .strategy_evaluation import summarize, attribute, opportunities


def run(symbol, panel, forecasts, features, vintages, out):
    d, z, x, histories, norm = prepare(
        symbol, panel, forecasts, features, vintages, out
    )
    rules = ["VOL", "CORE_VOL"]
    out.joinpath("ledgers").mkdir()
    out.joinpath("cycles").mkdir()
    metrics, attrs, controls, opps = [], [], [], []
    for cash in ["PROXY", "ZERO"]:
        weights = pd.DataFrame(index=z.index)
        weights["VOL"] = np.clip(norm[cash]["Bvol"] / z.scale.to_numpy(), 0, 1)
        weights["CORE_VOL"] = 0.5 + 0.5 * weights.VOL
        export = z[
            [
                "session",
                "scale",
                "information_cutoff",
                "forecast_timestamp",
                "next_open_timestamp",
            ]
        ].join(weights)
        export.reset_index().to_csv(out / f"DECISION_WEIGHTS_{cash}.csv", index=False)
        for phase in range(5):
            meta, prices, starts = timeline(z, x, phase, cash)
            ids = meta.decision_origin_index.to_numpy()
            for bp in [0, 1, 3]:
                prefix = f"{cash}_{phase}_{bp}"
                base = account(meta, prices, np.ones(len(meta)), bp, True)
                cb = cycles(base, z, histories, norm[cash], cash)
                base.to_parquet(
                    out / "ledgers" / f"{prefix}_BUYHOLD.parquet", index=False
                )
                cb.to_parquet(out / "cycles" / f"{prefix}_BUYHOLD.parquet", index=False)
                for period in PERIODS:
                    mb = summarize(base, cb, period)
                    if mb:
                        metrics.append(
                            dict(
                                cash_mode=cash,
                                offset=phase,
                                cost_bps=bp,
                                rule="BUYHOLD",
                                period=period,
                                Return_Retention=1.0,
                                **mb,
                            )
                        )
                for rule in rules:
                    a = account(meta, prices, weights.loc[ids, rule].to_numpy(), bp)
                    ca = cycles(a, z, histories, norm[cash], cash)
                    matched, q, err = match(meta, prices, a, bp)
                    cs = cycles(matched, z, histories, norm[cash], cash)
                    for name, la, cc in [(rule, a, ca), ("MATCH_" + rule, matched, cs)]:
                        la.to_parquet(
                            out / "ledgers" / f"{prefix}_{name}.parquet", index=False
                        )
                        cc.to_parquet(
                            out / "cycles" / f"{prefix}_{name}.parquet", index=False
                        )
                    for period in PERIODS:
                        ma = summarize(a, ca, period)
                        if ma is None:
                            continue
                        mb = summarize(base, cb, period)
                        if period == "ALL":
                            stat, sc, qq, ee = matched, cs, q, err
                        else:
                            mask = mask_period(
                                a.execution_session, a.end_session, period
                            )
                            stat, qq, ee = match(meta, prices, a, bp, mask)
                            sc = cycles(stat, z, histories, norm[cash], cash)
                        ms = summarize(stat, sc, period)
                        common = dict(
                            cash_mode=cash, offset=phase, cost_bps=bp, period=period
                        )
                        for name, mm in [(rule, ma), ("MATCH_" + rule, ms)]:
                            metrics.append(
                                dict(
                                    **common,
                                    rule=name,
                                    **mm,
                                    Return_Retention=(
                                        mm["CAGR"] / mb["CAGR"]
                                        if mb["CAGR"] > 0
                                        else np.nan
                                    ),
                                )
                            )
                        controls.append(
                            dict(
                                **common,
                                rule=rule,
                                target=qq,
                                exposure_error=ee,
                                dynamic_mean=ma["average_exposure"],
                                static_mean=ms["average_exposure"],
                            )
                        )
                        attrs.append(
                            dict(
                                **common,
                                rule=rule,
                                **attribute(a, base, stat, ca, cb, sc, period),
                            )
                        )
                        opps.append(
                            dict(**common, rule=rule, **opportunities(ca, period))
                        )
            print("CANONICAL_ACCOUNTS", symbol, cash, phase, flush=True)
    p = pd.DataFrame(metrics)
    zero = p[p.cost_bps == 0].set_index(["cash_mode", "offset", "rule", "period"]).CAGR
    p["CAGR_cost_drag"] = [
        zero.loc[(r.cash_mode, r.offset, r.rule, r.period)] - r.CAGR
        for r in p.itertuples()
    ]
    for name, a in [
        ("PORTFOLIO_RESULTS", p),
        ("RETURN_RISK_ATTRIBUTION", pd.DataFrame(attrs)),
        ("PERIOD_STATIC_CONTROLS", pd.DataFrame(controls)),
        ("OPPORTUNITY_COST", pd.DataFrame(opps)),
    ]:
        a.to_csv(out / f"{name}.csv", index=False)
    return p


def prepare(symbol, panel, tail_forecasts, features, vintages, out):
    d = panel.copy()
    f = tail_forecasts[tail_forecasts.model == "FHS"].copy()
    x = (
        features[features.symbol == symbol]
        .sort_values("session")
        .reset_index(drop=True)
    )
    z = d.set_index("origin_index").loc[f.origin_index].copy()
    z["q_fhs"] = f.q.to_numpy()
    z["e_fhs"] = f.e.to_numpy()
    z["dd_fhs"] = f.dd.to_numpy()
    missing_cash = z[z.cash5.isna()].copy()
    histories = {}
    logs = []
    original = vintages
    for log in original:
        cut = pd.Timestamp(log["cutoff"])
        tr = d[
            (d.session < pd.Timestamp(log["vintage"] + "-01"))
            & (d.target_end_timestamp <= cut)
        ]
        assert len(tr) == log["n"]
        assert (
            hashlib.sha256("|".join(tr.session.astype(str)).encode()).hexdigest()
            == log["train_hash"]
        )
        zz = np.sort(tr.Z.to_numpy())
        histories[log["vintage"]] = zz
        ix = z.session.dt.strftime("%Y-%m") == log["vintage"]
        q, e = empirical(zz)
        assert np.allclose(
            z.loc[ix, "q_fhs"], z.loc[ix, "scale"] * q, atol=1e-14, rtol=0
        )
        assert np.allclose(
            z.loc[ix, "e_fhs"], z.loc[ix, "scale"] * e, atol=1e-14, rtol=0
        )
        z.loc[ix, "prob_quantile"] = (
            zz[int(np.floor(0.05 * len(zz)))] * z.loc[ix, "scale"]
        )
        logs.append(
            dict(
                vintage=log["vintage"],
                n=len(tr),
                train_hash=log["train_hash"],
                cutoff=cut,
                q=q,
                e=e,
                prob_order_stat=float(zz[int(np.floor(0.05 * len(zz)))]),
            )
        )
    first = z.iloc[0]
    tr = d[
        (d.session < first.session)
        & (d.target_end_timestamp <= first.information_cutoff)
    ]
    zz = np.sort(tr.Z.to_numpy())
    s0 = float(tr.scale.median())
    E0 = -empirical(zz)[1]
    Q0 = -zz[int(np.floor(0.05 * len(zz)))]
    normal = {}
    for cash in ["PROXY", "ZERO"]:
        c0 = float(first.cash5) if cash == "PROXY" else 0.0
        normal[cash] = dict(
            anchor=0.8,
            core=0.5,
            probability_cap=0.05,
            s0=s0,
            E0=E0,
            Q0=Q0,
            C0=c0,
            Bvol=0.8 * s0,
            BES=0.8 * s0 * E0 - 0.2 * c0,
            L=0.8 * s0 * Q0 - 0.2 * c0,
            annualized_proxy_vol_budget=0.8 * s0 * np.sqrt(252 / 5),
        )
        assert normal[cash]["BES"] > 0 and normal[cash]["L"] > 0
    save(
        out / "NORMALIZATION.json",
        dict(
            symbol=symbol,
            cutoff=first.information_cutoff,
            training_origins=len(tr),
            train_first=tr.session.min(),
            train_last=tr.session.max(),
            latest_target_end=tr.target_end_timestamp.max(),
            budgets=normal,
            calibration="Once, training-only; same .80 appetite and .50 core for both assets",
            cash_vintage="PIT_VINTAGE_PARTIAL",
        ),
    )
    save(
        out / "FHS_REUSE_AUDIT.json",
        dict(
            status="PASS",
            n=len(z),
            vintages=logs,
            first=z.session.min(),
            last=z.session.max(),
            no_refitting=True,
        ),
    )
    original_n = len(z)
    if len(missing_cash):
        z = z.loc[z.index > missing_cash.index.max()].copy()
    assert z.cash5.notna().all() and np.all(np.diff(z.index) == 1)
    save(
        out / "DATA_COVERAGE_AUDIT.json",
        dict(
            original_fhs_origins=original_n,
            eligible_origins=len(z),
            excluded_prefix=original_n - len(z),
            first_eligible=z.session.min(),
            last_eligible=z.session.max(),
            normalization_unchanged=True,
            missing_cash=missing_cash[
                ["session", "cash_quote_date", "cash_age_days"]
            ].to_dict("records"),
            rule="Common contiguous eligible suffix; no imputation; original modulo-five offsets",
        ),
    )
    return d, z, x, histories, normal
