"""Training-only BIC selection and close-to-next-open aligned GARCH risk forecasts."""

from concurrent.futures import ProcessPoolExecutor
import hashlib, warnings
import numpy as np
import pandas as pd
from arch import arch_model
from .io import csv, save

FAMILY = [(p, q, dist) for p, q in [(1, 1), (1, 2), (2, 1)] for dist in ["normal", "t"]]


def variance_path(parameters, squared_shocks, variances, p, q, horizon=6):
    """Conditional expectations of future squared innovations equal future variance."""
    shocks = list(np.asarray(squared_shocks, float)[-p:])
    state = list(np.asarray(variances, float)[-q:])
    out = []
    for step in range(horizon):
        value = (
            parameters["omega"]
            + sum(parameters[f"alpha[{j+1}]"] * shocks[-j - 1] for j in range(p))
            + sum(parameters[f"beta[{j+1}]"] * state[-j - 1] for j in range(q))
        )
        if not np.isfinite(value) or value <= 0:
            raise ArithmeticError("Invalid variance recursion")
        out.append(value)
        shocks.append(value)
        state.append(value)
    return np.array(out)


def fit_vintage(task):
    symbol, month, dates, returns, rth, gap, current_dates, current_returns = task
    candidates = []
    fits = {}
    attempts = []
    for order, (p, q, dist) in enumerate(FAMILY):
        model = arch_model(
            returns, mean="Zero", vol="GARCH", p=p, q=q, dist=dist, rescale=False
        )
        for limit in [500, 2000]:
            try:
                with warnings.catch_warnings(record=True) as caught:
                    result = model.fit(
                        disp="off",
                        show_warning=False,
                        options={"maxiter": limit, "ftol": 1e-8},
                    )
                pars = result.params.to_dict()
                valid = (
                    result.convergence_flag == 0
                    and np.isfinite(result.bic)
                    and all(np.isfinite(list(pars.values())))
                )
                attempts.append(
                    dict(
                        symbol=symbol,
                        vintage=month,
                        p=p,
                        q=q,
                        distribution=dist,
                        maxiter=limit,
                        convergence_flag=int(result.convergence_flag),
                        valid=bool(valid),
                        warnings="; ".join(str(w.message) for w in caught),
                    )
                )
                if valid:
                    break
            except Exception as error:
                valid = False
                attempts.append(
                    dict(
                        symbol=symbol,
                        vintage=month,
                        p=p,
                        q=q,
                        distribution=dist,
                        maxiter=limit,
                        convergence_flag=-999,
                        valid=False,
                        warnings=type(error).__name__ + ": " + str(error),
                    )
                )
        if not valid:
            candidates.append(
                dict(
                    symbol=symbol,
                    vintage=month,
                    p=p,
                    q=q,
                    distribution=dist,
                    valid=False,
                    order=order,
                )
            )
            continue
        fits[order] = result
        candidates.append(
            dict(
                symbol=symbol,
                vintage=month,
                p=p,
                q=q,
                distribution=dist,
                valid=True,
                order=order,
                n_train=len(returns),
                loglikelihood=result.loglikelihood,
                n_parameters=result.num_params,
                BIC=result.bic,
                AIC=result.aic,
                persistence=sum(
                    v for k, v in pars.items() if k.startswith(("alpha", "beta"))
                ),
            )
        )
    valid_rows = sorted(
        [r for r in candidates if r["valid"]], key=lambda r: (r["BIC"], r["order"])
    )
    if not valid_rows:
        raise RuntimeError(f"All GARCH candidates failed: {symbol} {month}")
    selected = valid_rows[0]
    result = fits[selected["order"]]
    p, q = selected["p"], selected["q"]
    pars = result.params.to_dict()
    for r in candidates:
        r["selected"] = r["order"] == selected["order"]
    shocks = list(returns**2)
    variances = list(np.asarray(result.conditional_volatility) ** 2)
    native = variance_path(pars, shocks, variances, p, q)
    library = result.forecast(
        horizon=6, method="analytic", reindex=False
    ).variance.to_numpy()[-1]
    check = float(np.max(abs(native / library - 1)))
    if check > 1e-10:
        raise AssertionError("Library/manual GARCH horizon mismatch")
    denom = np.sum((returns / 100) ** 2)
    a_rth = float(np.sum(rth) / denom)
    a_gap = float(np.sum(gap) / denom)
    output = []
    for date, ret in zip(current_dates, current_returns):
        today = variance_path(pars, shocks, variances, p, q, horizon=1)[0]
        shocks.append(ret**2)
        variances.append(today)
        h = variance_path(pars, shocks, variances, p, q) / 10000
        risk = (a_rth * h[:5].sum() + a_gap * h[1:6].sum()) / 5
        output.append(
            dict(
                symbol=symbol,
                session=date,
                vintage=month,
                forecast=risk,
                native_close_to_close5=float(h[:5].mean()),
                filtered_variance=today / 10000,
                **{f"h{j+1}": x for j, x in enumerate(h)},
            )
        )
    audit = dict(
        **selected,
        train_first=dates[0],
        train_last=dates[-1],
        training_row_hash=hashlib.sha256("|".join(dates).encode()).hexdigest(),
        parameters=pars,
        a_RTH=a_rth,
        a_GAP=a_gap,
        return_squared_sum=float(denom),
        rth_sum=float(np.sum(rth)),
        gap_sum=float(np.sum(gap)),
        BIC_margin=(
            valid_rows[1]["BIC"] - selected["BIC"] if len(valid_rows) > 1 else None
        ),
        manual_library_relative_error=check,
        backcast=float(result.model.volatility.backcast(returns)),
        last_training_shocks=shocks[: len(returns)][-p:],
        last_training_variances=variances[: len(returns)][-q:],
    )
    return output, candidates, attempts, audit


def run(data, existing_forecasts, out, workers=4):
    har = existing_forecasts[existing_forecasts.model.eq("HAR")]
    tasks = []
    for symbol, z in data.groupby("symbol"):
        z = z.sort_values("session").copy()
        z["cc_return"] = 100 * np.log(z.Close / z.Close.shift(1))
        for month, f in har[har.symbol.eq(symbol)].groupby("vintage"):
            first = f.session.min()
            tr = z[z.session < first].dropna(subset=["cc_return", "GK_RTH", "OVN2"])
            cur = z.set_index("session").loc[f.session]
            tasks.append(
                (
                    symbol,
                    month,
                    tr.session.dt.strftime("%Y-%m-%d").tolist(),
                    tr.cc_return.to_numpy(),
                    tr.GK_RTH.to_numpy(),
                    tr.OVN2.to_numpy(),
                    cur.index.strftime("%Y-%m-%d").tolist(),
                    cur.cc_return.to_numpy(),
                )
            )
    rows = []
    candidates = []
    attempts = []
    vintages = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for i, (r, c, a, v) in enumerate(pool.map(fit_vintage, tasks), 1):
            rows.extend(r)
            candidates.extend(c)
            attempts.extend(a)
            vintages.append(v)
            if i % 24 == 0 or i == len(tasks):
                print("GARCH_VINTAGES", i, "/", len(tasks), flush=True)
    raw = pd.DataFrame(rows)
    raw["session"] = pd.to_datetime(raw.session)
    raw.to_parquet(out / "GARCH_DAILY_STATE.parquet", index=False)
    gf = har.drop(
        columns=["forecast", "model", "forecast_q90", "forecast_percentile"]
    ).merge(
        raw[["symbol", "session", "forecast"]],
        on=["symbol", "session"],
        validate="one_to_one",
    )
    gf["model"] = "GARCH"
    parts = []
    for symbol, g in gf.groupby("symbol"):
        g = g.sort_values("session").copy()
        p = g.forecast.to_numpy()
        g["forecast_q90"] = g.forecast.shift().expanding(252).quantile(0.9)
        rank = np.full(len(g), np.nan)
        for i in range(252, len(g)):
            rank[i] = ((p[:i] < p[i]).sum() + 0.5 * (p[:i] == p[i]).sum()) / i
        g["forecast_percentile"] = rank
        parts.append(g)
    result = pd.concat(
        [existing_forecasts, pd.concat(parts, ignore_index=True)], ignore_index=True
    )
    result.to_parquet(out / "FORECASTS_WITH_GARCH.parquet", index=False)
    csv(out / "GARCH_MODEL_SELECTION.csv", candidates)
    csv(out / "GARCH_FIT_ATTEMPTS.csv", attempts)
    save(out / "GARCH_VINTAGES.json", vintages)
    return result
