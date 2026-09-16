"""Fixed HS/FHS evaluation and calibration; no retired tail candidates."""

import numpy as np
import pandas as pd
from scipy.stats import rankdata, chi2
from scipy.special import xlogy
from .fhs import empirical, masks, ALPHA, SCORES


def clusters(d, event):
    ix = d.origin_index.to_numpy()[np.asarray(event, bool)]
    return int(0 if len(ix) == 0 else 1 + (np.diff(ix) > 5).sum())


def auc(y, p):
    y = np.asarray(y, bool)
    n1 = y.sum()
    n0 = len(y) - n1
    return (
        float((rankdata(p)[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))
        if n0 and n1
        else np.nan
    )


def lr_tests(a):
    y = a.hit.to_numpy().astype(int)
    ix = a.origin_index.to_numpy()
    n = len(y)
    hits = int(y.sum())

    def bern(success, total, p):
        return xlogy(success, p) + xlogy(total - success, 1 - p)

    uc = 2 * (bern(hits, n, hits / n) - bern(hits, n, ALPHA)) if n else np.nan
    adj = np.diff(ix) == 5
    c = np.array(
        [[np.sum(adj & (y[:-1] == i) & (y[1:] == j)) for j in [0, 1]] for i in [0, 1]]
    )
    pooled = c[:, 1].sum() / max(1, c.sum())
    ind = 0
    for row in c:
        if row.sum():
            ind += 2 * (
                bern(row[1], row.sum(), row[1] / row.sum())
                - bern(row[1], row.sum(), pooled)
            )
    return dict(
        n=n,
        hits=hits,
        n00=int(c[0, 0]),
        n01=int(c[0, 1]),
        n10=int(c[1, 0]),
        n11=int(c[1, 1]),
        LRuc=uc,
        LRind=ind,
        LRcc=uc + ind,
        p_uc=chi2.sf(uc, 1),
        p_ind=chi2.sf(ind, 1),
        p_cc=chi2.sf(uc + ind, 2),
    )


def evaluate(d, f, out):
    rows = []
    cal = []
    coverage = []
    events = []
    contrib = []
    for period, m in masks(d).items():
        ids = set(d.loc[m, "origin_index"])
        for model, b in f.groupby("model", sort=False):
            a = b[b.origin_index.isin(ids)]
            n = len(a)
            if not n:
                continue
            y = a.R5.to_numpy()
            rec = dict(
                period=period,
                model=model,
                n=n,
                first=a.session.min(),
                last=a.session.max(),
                **{
                    k: (np.nan if model == "T_SCALE" and k == "DD_MSE" else a[k].mean())
                    for k in SCORES
                },
                DD_MAE=np.nan if model == "T_SCALE" else a.DD_MAE.mean(),
                var_hit_rate=a.hit.mean(),
                ES_moment=a.ES_moment.mean(),
                actual_p2=(y < -0.02).mean(),
                pred_p2=a.p2.mean(),
                actual_p5=(y < -0.05).mean(),
                pred_p5=a.p5.mean(),
                auc2=auc(y < -0.02, a.p2),
                auc5=auc(y < -0.05, a.p5),
                actual_D=a.D.mean(),
                pred_D=a.dd.mean(),
                fallback_fraction=a.fallback.mean(),
                max_impossible_mass=a.impossible_mass.max(),
                q_below_minus1=int((a.q < -1).sum()),
                e_below_minus1=int((a.e < -1).sum()),
            )
            rows.append(rec)
            events.append(
                dict(
                    period=period,
                    model=model,
                    n=n,
                    var_hits=int(a.hit.sum()),
                    var_episodes=clusters(a, a.hit == 1),
                    loss2_events=int((y < -0.02).sum()),
                    loss2_episodes=clusters(a, y < -0.02),
                    loss5_events=int((y < -0.05).sum()),
                    loss5_episodes=clusters(a, y < -0.05),
                )
            )
            if period.startswith("NONOVERLAP5"):
                coverage.append(dict(period=period, model=model, **lr_tests(a)))
            for state, mm in [
                ("LOW", a.p < 0.4),
                ("MID", (a.p >= 0.4) & (a.p < 0.8)),
                ("HIGH", a.p >= 0.8),
            ]:
                z = a.loc[mm]
                cal.append(
                    dict(
                        period=period,
                        model=model,
                        bucket_type="RISK",
                        bucket=state,
                        n=len(z),
                        var_hit=z.hit.mean(),
                        ES_moment=z.ES_moment.mean(),
                        actual_p2=(z.R5 < -0.02).mean(),
                        pred_p2=z.p2.mean(),
                        actual_p5=(z.R5 < -0.05).mean(),
                        pred_p5=z.p5.mean(),
                        actual_D=z.D.mean(),
                        pred_D=z.dd.mean(),
                    )
                )
            for prob, threshold in [("p2", -0.02), ("p5", -0.05)]:
                edges = [0, 0.01, 0.05, 0.1, 0.2, 1.000001]
                for lo, hi in zip(edges[:-1], edges[1:]):
                    z = a[(a[prob] >= lo) & (a[prob] < hi)]
                    cal.append(
                        dict(
                            period=period,
                            model=model,
                            bucket_type=prob,
                            bucket=f"{lo}_{hi}",
                            n=len(z),
                            actual_probability=(z.R5 < threshold).mean(),
                            predicted_probability=z[prob].mean(),
                        )
                    )
    pd.DataFrame(rows).to_csv(out / "FORECAST_METRICS.csv", index=False)
    pd.DataFrame(cal).to_csv(out / "CALIBRATION.csv", index=False)
    pd.DataFrame(events).to_csv(out / "FORECAST_EVENT_COUNTS.csv", index=False)
    pd.DataFrame(coverage).to_csv(out / "NONOVERLAP_COVERAGE.csv", index=False)
    # Loss concentration is additive for nonnegative scores and shortfall amounts, not FZ0 levels.
    pm = masks(d)
    shock_union = ~pm["EX_MAJOR_SHOCKS"]
    for model, a in f.groupby("model", sort=False):
        loss = np.maximum(-a.R5, 0)
        short = np.maximum(a.q - a.R5, 0)
        for period, mm in [(x, pm[x]) for x in ["GFC", "COVID", "2022"]] + [
            ("SHOCK_UNION", shock_union)
        ]:
            g = a.origin_index.isin(set(d.loc[mm, "origin_index"])).to_numpy()
            rec = dict(
                model=model,
                period=period,
                n=int(g.sum()),
                origin_share=float(g.mean()),
                negative_return_amount_share=loss[g].sum() / loss.sum(),
                VaR_shortfall_amount_share=short[g].sum() / short.sum(),
            )
            for k in ["PINBALL", "BRIER2", "BRIER5", "DD_MSE"]:
                rec[k + "_loss_share"] = a.loc[g, k].sum() / a[k].sum()
            contrib.append(rec)
    pd.DataFrame(contrib).to_csv(out / "SHOCK_CONTRIBUTIONS.csv", index=False)
