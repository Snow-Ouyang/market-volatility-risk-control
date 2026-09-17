"""Presentation only: frozen tables and ledgers become figures and README.

No forecast fitting, account simulation, score calculation or bucket reassignment.
"""

import json
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import PercentFormatter, FuncFormatter
from .io import sha

NAVY = "#273E58"
TEAL = "#087F8C"
GRAY = "#7D8794"
INK = "#243447"
SHADE = "#E9EDF1"
EPISODES = {
    "GFC": ("2007-01-01", "2009-12-31"),
    "COVID": ("2020-02-19", "2020-06-30"),
    "2022": ("2022-01-01", "2022-12-31"),
}


def style():
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.labelsize": 10,
            "axes.titlesize": 12,
            "text.color": INK,
            "axes.labelcolor": INK,
            "xtick.color": INK,
            "ytick.color": INK,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.edgecolor": "#CCD3DA",
            "axes.linewidth": 0.7,
            "legend.frameon": False,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "pdf.fonttype": 42,
            "axes.axisbelow": True,
        }
    )


def title(fig, headline, subtitle):
    height = fig.get_size_inches()[1]
    fig.suptitle(
        headline,
        x=0.09,
        y=1 - 0.12 / height,
        ha="left",
        va="top",
        fontsize=16,
        fontweight="bold",
    )
    fig.text(
        0.09, 1 - 0.51 / height, subtitle, fontsize=9, color=GRAY, ha="left", va="top"
    )


def export(fig, folder, name, footnote):
    fig.text(0.09, 0.019, footnote, fontsize=8.2, color=GRAY, va="bottom")
    fig.savefig(folder / f"{name}.png", dpi=220)
    fig.savefig(
        folder / f"{name}.pdf", metadata={"CreationDate": None, "ModDate": None}
    )
    plt.close(fig)


def date_span(frame):
    return f"{pd.Timestamp(frame.start.iloc[0]):%Y-%m-%d} to {pd.Timestamp(frame.end.iloc[0]):%Y-%m-%d}"


def forecast_figures(out, folder, gains, sources):
    metrics = pd.read_csv(out / "forecast/BENCHMARK_METRICS.csv")
    bucket_path = out / "forecast/BENCHMARK_RISK_BUCKETS.csv"
    buckets = pd.read_csv(bucket_path)
    sources.append(bucket_path)
    forecast_path = out / "forecast/FORECASTS.parquet"
    forecasts = pd.read_parquet(forecast_path)
    sources.append(forecast_path)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    fig.subplots_adjust(left=0.14, right=0.97, bottom=0.2, top=0.71, wspace=0.43)
    title(
        fig,
        "HAR lowers average forecast error",
        "Frozen walk-forward forecasts | common model dates per asset | EXPOSED_HISTORY",
    )
    for ax, symbol in zip(axes, ["SPY", "QQQ"]):
        g = gains.set_index(["symbol", "baseline"])
        for j, (metric, color) in enumerate([("MSE", NAVY), ("QLIKE", TEAL)]):
            values = (
                np.array([g.loc[(symbol, b), metric] for b in ["GARCH", "ROLLING22"]])
                * 100
            )
            y = np.array([1.0, 0.0]) + (0.17 if j == 0 else -0.17)
            ax.barh(y, values, height=0.27, color=color, label=metric)
            for yi, val in zip(y, values):
                ax.text(
                    val + 0.5,
                    yi,
                    f"{val:.1f}%",
                    va="center",
                    fontsize=10,
                    fontweight="bold",
                    color=color,
                )
        m = metrics[
            (metrics.symbol == symbol)
            & (metrics.model == "HAR")
            & (metrics.period == "ALL")
        ]
        ax.set_title(f"{symbol}\n{date_span(m)}", loc="left", fontsize=11, pad=15)
        ax.set(
            yticks=[1, 0],
            yticklabels=["vs GARCH", "vs Rolling22"],
            xlim=(0, 32),
            ylim=(-0.55, 1.55),
            xlabel="Loss reduction (%)",
        )
        ax.set_xticks([0, 10, 20, 30])
        ax.grid(axis="x", color=SHADE)
    fig.legend(
        *axes[0].get_legend_handles_labels(),
        loc="lower left",
        bbox_to_anchor=(0.09, 0.075),
        ncol=2,
        fontsize=9,
    )
    export(
        fig,
        folder,
        "FORECAST_ACCURACY",
        "Positive values favor HAR. Average gains are descriptive; the joint HAR-over-GARCH inference verdict remains WEAK.",
    )

    fig, axes = plt.subplots(2, 1, figsize=(15, 7.2))
    fig.subplots_adjust(left=0.075, right=0.98, bottom=0.15, top=0.86, hspace=0.32)
    title(
        fig,
        "Predicted and realized five-day risk through time",
        "Frozen HAR forecast at each origin versus the subsequent five-session holding-risk target | EXPOSED_HISTORY",
    )
    har = forecasts[forecasts.model == "HAR"].copy()
    har["realized_risk"] = np.sqrt(252 * har.actual) * 100
    har["predicted_risk"] = np.sqrt(252 * har.forecast) * 100
    for ax, symbol in zip(axes, ["SPY", "QQQ"]):
        z = har[har.symbol == symbol].sort_values("session")
        ax.plot(
            z.session,
            z.realized_risk,
            color="#AAB4BE",
            lw=0.75,
            alpha=0.78,
            label="Realized future 5D risk",
        )
        ax.plot(
            z.session,
            z.predicted_risk,
            color=NAVY,
            lw=1.05,
            label="HAR predicted 5D risk",
        )
        ax.set_title(
            f"{symbol} | {pd.Timestamp(z.session.iloc[0]):%Y-%m-%d} to {pd.Timestamp(z.session.iloc[-1]):%Y-%m-%d}",
            loc="left",
            fontsize=10.5,
            pad=8,
        )
        ax.set_ylabel("Annualized risk (%)")
        ax.set_ylim(0, max(z.realized_risk.max(), z.predicted_risk.max()) * 1.06)
        ax.set_xlim(z.session.min(), z.session.max())
        ax.xaxis.set_major_locator(mdates.YearLocator(3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.grid(axis="y", color=SHADE, lw=0.6)
        for _, (lo, hi) in EPISODES.items():
            ax.axvspan(
                pd.Timestamp(lo), pd.Timestamp(hi), color=SHADE, alpha=0.45, zorder=0
            )
    fig.legend(
        *axes[0].get_legend_handles_labels(),
        loc="lower left",
        bbox_to_anchor=(0.075, 0.06),
        ncol=2,
        fontsize=9,
    )
    export(
        fig,
        folder,
        "FORECAST_TIMESERIES",
        "Each origin pairs its after-close forecast with realized HOLD risk over t+1 through t+5; scale = 100 x sqrt(252 x mean daily variance proxy).\nOverlapping five-session targets aid visual comparison; formal inference uses paired block intervals.",
    )

    fig, axes = plt.subplots(1, 2, figsize=(11, 5.2), sharey=True)
    fig.subplots_adjust(left=0.09, right=0.97, bottom=0.25, top=0.78, wspace=0.16)
    title(
        fig,
        "Higher forecast risk identifies higher future realized risk",
        "Existing past-only percentile buckets | no new grouping or smoothing | EXPOSED_HISTORY",
    )
    for ax, symbol in zip(axes, ["SPY", "QQQ"]):
        z = buckets[
            (buckets.symbol == symbol)
            & (buckets.model == "HAR")
            & (buckets.period == "ALL")
        ].sort_values("bin")
        for col, label, color, marker in [
            ("mean_forecast", "HAR forecast", NAVY, "o"),
            ("future_risk", "Realized future 5D risk", TEAL, "s"),
        ]:
            ax.plot(
                z.bin,
                np.sqrt(252 * z[col]) * 100,
                marker=marker,
                color=color,
                lw=1.8,
                markersize=5,
                label=label,
            )
        ax.set(
            xticks=range(1, 11),
            xlabel="Past-only forecast percentile bucket",
            ylim=(0, None),
        )
        m = metrics[
            (metrics.symbol == symbol)
            & (metrics.model == "HAR")
            & (metrics.period == "ALL")
        ]
        ax.set_title(
            f"{symbol} | {date_span(m)}\n{int(z.n.sum()):,} eligible origins; bucket counts differ",
            loc="left",
            fontsize=10,
            pad=12,
        )
        ax.grid(axis="y", color=SHADE)
    axes[0].set_ylabel("Annualized quadratic-risk scale (%)")
    high = (
        buckets[(buckets.model == "HAR") & (buckets.period == "ALL")][
            ["future_risk", "mean_forecast"]
        ]
        .to_numpy()
        .max()
    )
    axes[0].set_ylim(0, np.sqrt(252 * high) * 100 * 1.12)
    fig.legend(
        *axes[0].get_legend_handles_labels(),
        loc="lower left",
        bbox_to_anchor=(0.09, 0.09),
        ncol=2,
        fontsize=9,
    )
    export(
        fig,
        folder,
        "FORECAST_VS_REALIZED",
        "Scale = 100 x sqrt(252 x bucket mean daily variance proxy); not mean volatility or 5D endpoint-return volatility.\nBuckets 1-10 span successive past-forecast percentile bands. Aggregated means describe risk ranking, not conditional coverage.",
    )


def account_figure(out, folder, symbol, accounts, sources):
    fig, axes = plt.subplots(
        3,
        1,
        figsize=(11, 8.7),
        sharex=True,
        gridspec_kw={"height_ratios": [1.35, 1.2, 0.8]},
    )
    fig.subplots_adjust(left=0.09, right=0.97, bottom=0.10, top=0.86, hspace=0.15)
    frames = {}
    for rule, label, color in [
        ("BUYHOLD", "Buy & Hold", GRAY),
        ("VOL", "Full VOL", TEAL),
    ]:
        path = out / "strategy" / symbol / "ledgers" / f"PROXY_0_1_{rule}.parquet"
        sources.append(path)
        a = pd.read_parquet(path)
        frames[rule] = a
        dates = pd.DatetimeIndex(
            [pd.Timestamp(a.execution_session.iloc[0]), *pd.to_datetime(a.end_session)]
        )
        nav = np.r_[1.0, a.end_NAV.to_numpy()]
        dd = nav / np.maximum.accumulate(nav) - 1
        axes[0].plot(dates, nav, color=color, lw=1.5, label=label)
        axes[1].fill_between(dates, dd * 100, 0, color=color, alpha=0.12)
        axes[1].plot(dates, dd * 100, color=color, lw=1.0)
    a = frames["VOL"]
    axes[2].plot(a.execution_session, a.exposure * 100, color=TEAL, lw=0.85)
    axes[2].fill_between(
        a.execution_session, a.exposure * 100, 0, color=TEAL, alpha=0.09
    )
    axes[0].set(yscale="log", ylabel="Growth of $1\n(log scale)")
    axes[0].yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"${x:g}"))
    axes[1].set_ylabel("Drawdown (%)")
    axes[2].set(ylabel="Equity exposure (%)", ylim=(0, 105), yticks=[0, 50, 100])
    fig.legend(
        *axes[0].get_legend_handles_labels(),
        loc="lower left",
        bbox_to_anchor=(0.085, 0.865),
        ncol=2,
        fontsize=10,
    )
    for ax in axes:
        ax.grid(axis="y", color=SHADE, lw=0.6)
        for _, (lo, hi) in EPISODES.items():
            ax.axvspan(
                pd.Timestamp(lo), pd.Timestamp(hi), color=SHADE, alpha=0.55, zorder=0
            )
    for label, (lo, hi) in EPISODES.items():
        center = pd.Timestamp(lo) + (pd.Timestamp(hi) - pd.Timestamp(lo)) / 2
        axes[0].text(
            center,
            0.98,
            label,
            transform=axes[0].get_xaxis_transform(),
            ha="center",
            va="top",
            fontsize=8,
            color=GRAY,
        )
    axes[2].xaxis.set_major_locator(mdates.YearLocator(3))
    axes[2].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    axes[2].set_xlim(
        pd.Timestamp(a.execution_session.iloc[0]), pd.Timestamp(a.end_session.iloc[-1])
    )
    h = accounts.set_index(["asset", "rule"])
    bh, vol = h.loc[(symbol, "BUYHOLD")], h.loc[(symbol, "VOL")]
    reduction = 100 * (1 - vol.MaxDD / bh.MaxDD)
    title(
        fig,
        f"{symbol}: Full VOL reduces maximum drawdown by {reduction:.0f}%",
        f"{pd.Timestamp(a.execution_session.iloc[0]):%Y-%m-%d} to {pd.Timestamp(a.end_session.iloc[-1]):%Y-%m-%d} | 5-session next-open rebalance | 1bp per side | EXPOSED_HISTORY",
    )
    export(
        fig,
        folder,
        f"{symbol}_RISK_CONTROL",
        "Primary original offset 0; frozen 3M Treasury cash-carry proxy. Daily account marks; exposure includes natural weight drift.\nInitial funding fee included; no terminal liquidation. Shading uses existing GFC / COVID / 2022 windows.",
    )


def tradeoff(folder, accounts):
    fig, axes = plt.subplots(1, 4, figsize=(11, 4.7))
    fig.subplots_adjust(left=0.10, right=0.97, bottom=0.25, top=0.75, wspace=0.35)
    title(
        fig,
        "Less equity participation buys substantial risk reduction",
        "SPY and QQQ | original offset 0, 1bp, cash proxy | asset-specific application samples | EXPOSED_HISTORY",
    )
    h = accounts.set_index(["asset", "rule"])
    for ax, (metric, label) in zip(
        axes,
        [
            ("CAGR", "CAGR"),
            ("annual_vol", "Annual volatility"),
            ("MaxDD", "Maximum drawdown"),
            ("ES95_5D", "5D ES95"),
        ],
    ):
        for y, symbol in [(1, "SPY"), (0, "QQQ")]:
            b, v = (h.loc[(symbol, rule), metric] * 100 for rule in ["BUYHOLD", "VOL"])
            ax.plot([v, b], [y, y], color="#C2CAD2", lw=3)
            ax.scatter(
                [b],
                [y],
                color=GRAY,
                s=45,
                label="Buy & Hold" if y == 1 else None,
                zorder=3,
            )
            ax.scatter(
                [v],
                [y],
                color=TEAL,
                s=45,
                label="Full VOL" if y == 1 else None,
                zorder=3,
            )
            ax.text(b, y + 0.17, f"{b:.2f}", ha="center", color=GRAY, fontsize=9)
            ax.text(
                v,
                y - 0.23,
                f"{v:.2f}",
                ha="center",
                color=TEAL,
                fontsize=9,
                fontweight="bold",
            )
        ax.set(
            yticks=[1, 0],
            yticklabels=["SPY", "QQQ"] if ax == axes[0] else [],
            ylim=(-0.5, 1.5),
            xlabel="Percent (%)",
        )
        ax.set_xlim(0, h[metric].max() * 100 * 1.28)
        ax.set_title(label, fontsize=10, pad=16)
        ax.grid(axis="x", color=SHADE)
    fig.legend(
        *axes[0].get_legend_handles_labels(),
        loc="lower left",
        bbox_to_anchor=(0.09, 0.07),
        ncol=2,
        fontsize=9,
    )
    export(
        fig,
        folder,
        "RISK_RETURN_TRADEOFF",
        "Each panel uses its own percent axis. Full VOL retains part, not all, of Buy & Hold CAGR. No parameter or Sharpe ranking.",
    )


def timing_figure(folder):
    fig, ax = plt.subplots(figsize=(11, 3.7))
    ax.set_axis_off()
    title(
        fig,
        "The risk state and the holding interval use different gaps",
        "Frozen definition schematic | close-t information determines the next-open position",
    )
    x = [0.08, 0.35, 0.65, 0.93]
    y = 0.54
    ax.set_position([0.04, 0.15, 0.92, 0.65])
    ax.set(xlim=(0, 1), ylim=(0, 1))
    for p, label in zip(x, ["Close[t-1]", "Open[t]", "Close[t]", "Open[t+1]"]):
        ax.plot(p, y, "o", color=NAVY, markersize=6)
        ax.text(p, y + 0.12, label, ha="center", fontsize=11, fontweight="bold")
    for lo, hi, label, color in [
        (x[0], x[1], "Gap[t] squared", GRAY),
        (x[1], x[2], "Session GK[t]\nfrom daily OHLC", TEAL),
        (x[2], x[3], "Gap[t+1] squared", GRAY),
    ]:
        ax.annotate(
            "",
            xy=(hi - 0.01, y),
            xytext=(lo + 0.01, y),
            arrowprops={"arrowstyle": "->", "color": color, "lw": 2},
        )
        ax.text(
            (lo + hi) / 2,
            y - 0.12,
            label,
            ha="center",
            va="top",
            color=color,
            fontsize=10,
        )
    ax.plot([x[0], x[2]], [0.15, 0.15], color=NAVY, lw=3)
    ax.text(
        (x[0] + x[2]) / 2, 0.19, "STATE[t]", ha="center", color=NAVY, fontweight="bold"
    )
    ax.plot([x[1], x[3]], [-0.015, -0.015], color=TEAL, lw=3, clip_on=False)
    ax.text(
        (x[1] + x[3]) / 2, 0.025, "HOLD[t]", ha="center", color=TEAL, fontweight="bold"
    )
    export(
        fig,
        folder,
        "SESSION_HOLDING_TIMELINE",
        "A squared overnight gap captures the net overnight shock, not the full intranight price path.",
    )


def matched_exposure(public):
    """Read the existing primary-case attribution; never refit the static control."""
    a = pd.read_csv(public / "results/strategy/HEADLINE_ATTRIBUTION.csv")
    a = (
        a[
            (a.rule == "VOL")
            & (a.cash_mode == "PROXY")
            & (a.offset == 0)
            & (a.cost_bps == 1)
            & (a.period == "ALL")
        ]
        .set_index("asset")
        .loc[["SPY", "QQQ"]]
        .reset_index()
    )
    assert len(a) == 2
    assert np.allclose(a.dynamic_average, a.static_average, atol=1e-10, rtol=0)
    return a


def matched_exposure_figure(public, a):
    """One additional PNG, using saved relative gains rather than a new evaluation."""
    fig, ax = plt.subplots(figsize=(11, 4.8))
    fig.subplots_adjust(left=0.23, right=0.96, bottom=0.23, top=0.73)
    title(
        fig,
        "Risk control improves beyond lower average exposure",
        "Full VOL vs matched static | same sample, 1bp and cash proxy | EXPOSED_HISTORY",
    )
    columns = [
        "annual_vol_dynamic_fraction",
        "ES95_5D_dynamic_fraction",
        "MaxDD_dynamic_fraction",
    ]
    for j, (symbol, color) in enumerate([("SPY", NAVY), ("QQQ", TEAL)]):
        values = (
            a.set_index("asset").loc[symbol, columns].astype(float).to_numpy() * 100
        )
        y = np.array([2.0, 1.0, 0.0]) + (0.17 if j == 0 else -0.17)
        ax.barh(y, values, height=0.27, color=color, label=symbol)
        for yi, value in zip(y, values):
            ax.text(
                value + 0.45,
                yi,
                f"{value:.1f}%",
                va="center",
                color=color,
                fontweight="bold",
            )
    ax.set(
        yticks=[2, 1, 0],
        yticklabels=["Annual volatility", "5D ES95", "MaxDD"],
        xlim=(0, a[columns].to_numpy().max() * 125),
        ylim=(-0.6, 2.6),
        xlabel="Risk reduction versus matched static (%)",
    )
    ax.grid(axis="x", color=SHADE)
    fig.legend(
        *ax.get_legend_handles_labels(),
        loc="lower left",
        bbox_to_anchor=(0.09, 0.07),
        ncol=2,
    )
    fig.text(
        0.09,
        0.02,
        "Ex-post diagnostic, not a deployable control. Timing returns are weak / negative; gains are not stable in every regime.",
        fontsize=8,
        color=GRAY,
    )
    fig.savefig(public / "results/figures/MATCHED_EXPOSURE_RISK_GAIN.png", dpi=220)
    plt.close(fig)


def render(out, public):
    style()
    folder = public / "results/figures"
    sources = [
        out / "forecast/BENCHMARK_LOSS_GAINS.csv",
        out / "forecast/BENCHMARK_METRICS.csv",
        out / "forecast/DATA_COVERAGE.csv",
    ]
    gains = pd.read_csv(public / "results/forecast/HEADLINE_GAINS.csv")
    accounts = pd.read_csv(public / "results/strategy/HEADLINE_ACCOUNTS.csv")
    hero = accounts[accounts.rule.isin(["BUYHOLD", "VOL"])].copy()
    sources += [out / "strategy" / s / "PORTFOLIO_RESULTS.csv" for s in ["SPY", "QQQ"]]
    reductions = []
    for s in ["SPY", "QQQ"]:
        z = hero[hero.asset == s].set_index("rule")
        b, v = z.loc["BUYHOLD"], z.loc["VOL"]
        reductions.append(
            dict(
                asset=s,
                volatility_reduction=1 - v.annual_vol / b.annual_vol,
                drawdown_reduction=1 - v.MaxDD / b.MaxDD,
                ES_reduction=1 - v.ES95_5D / b.ES95_5D,
            )
        )
    reduction = pd.DataFrame(reductions)
    forecast_figures(out, folder, gains, sources)
    for s in ["SPY", "QQQ"]:
        account_figure(out, folder, s, accounts, sources)
    tradeoff(folder, accounts)
    timing_figure(folder)
    matched = matched_exposure(public)
    matched_exposure_figure(public, matched)
    sources += [
        out / "strategy" / s / "RETURN_RISK_ATTRIBUTION.csv" for s in ["SPY", "QQQ"]
    ]
    values = {
        "forecast_gains": gains.to_dict("records"),
        "accounts": hero.to_dict("records"),
        "reductions": reductions,
        "matched_exposure": matched.to_dict("records"),
    }
    (folder / "PRESENTATION_DATA.json").write_text(
        json.dumps(values, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    readme = make_readme(public, gains, hero, reduction)
    (public / "README.md").write_text(readme, encoding="utf-8")
    manifest = {
        "scope": "Presentation only; frozen results and ledgers read without modification",
        "sources": {p.relative_to(out).as_posix(): sha(p) for p in sources},
        "readme_sha256": sha(public / "README.md"),
        "figures": {
            p.name: sha(p) for p in folder.iterdir() if p.suffix in [".png", ".pdf"]
        },
    }
    (folder / "PRESENTATION_PROVENANCE.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


def make_readme(public, gains, hero, reduction):
    def table(d):
        return d.to_markdown(index=False, floatfmt=".2f")

    g = (
        gains[gains.baseline == "GARCH"][["symbol", "MSE", "QLIKE"]]
        .copy()
        .sort_values("symbol", ascending=False)
    )
    g[["MSE", "QLIKE"]] *= 100
    g.columns = ["ETF", "MSE reduction (%)", "QLIKE reduction (%)"]
    h = hero.set_index(["asset", "rule"])
    r = reduction.set_index("asset")
    top = []
    for s in ["SPY", "QQQ"]:
        b, v = h.loc[(s, "BUYHOLD")], h.loc[(s, "VOL")]
        top.append(
            {
                "ETF": s,
                "Annual vol (%)": f"{b.annual_vol*100:.2f} → {v.annual_vol*100:.2f}",
                "MaxDD (%)": f"{b.MaxDD*100:.2f} → {v.MaxDD*100:.2f}",
                "5D ES95 (%)": f"{b.ES95_5D*100:.2f} → {v.ES95_5D*100:.2f}",
            }
        )
    cols = ["CAGR", "Return_Retention", "annual_vol", "ES95_5D", "MaxDD"]
    account_table = hero[["asset", "rule"] + cols].copy()
    account_table[cols] *= 100
    account_table["rule"] = account_table.rule.map(
        {"BUYHOLD": "Buy & Hold", "VOL": "Full VOL"}
    )
    account_table.columns = [
        "ETF",
        "Account",
        "CAGR (%)",
        "CAGR retained (%)",
        "Volatility (%)",
        "5D ES95 (%)",
        "MaxDD (%)",
    ]
    red = reduction.copy()
    red.iloc[:, 1:] *= 100
    red.columns = [
        "ETF",
        "Vol reduction (%)",
        "MaxDD reduction (%)",
        "ES reduction (%)",
    ]
    coverage = pd.read_csv(public / "results/strategy/APPLICATION_COVERAGE.csv")
    dates = "; ".join(
        f"{z.asset}: {z.offset0_entry}–{z.offset0_exit}" for z in coverage.itertuples()
    )
    prices = pd.read_csv(public / "results/forecast/DATA_COVERAGE.csv")
    price_span = " and ".join(
        f"{q.symbol} {pd.Timestamp(q.start):%Y}–{pd.Timestamp(q.end):%Y}"
        for q in prices.sort_values("symbol", ascending=False).itertuples()
    )
    matched = matched_exposure(public)
    matched_table = matched[
        [
            "asset",
            "annual_vol_dynamic_fraction",
            "ES95_5D_dynamic_fraction",
            "MaxDD_dynamic_fraction",
        ]
    ].copy()
    matched_table.iloc[:, 1:] *= 100
    matched_table.columns = [
        "ETF",
        "Vol reduction vs matched static (%)",
        "ES reduction vs matched static (%)",
        "MaxDD reduction vs matched static (%)",
    ]
    mean_exposure = "; ".join(
        f"{z.asset}: **{z.dynamic_average*100:.2f}%**" for z in matched.itertuples()
    )
    return rf"""# Market Volatility Forecasting & Risk Control

**Daily OHLC supports medium-horizon risk forecasting; a simple volatility-scaled equity / Treasury-cash overlay materially reduces realized volatility and drawdown.**

Risk forecasting and risk control. **No return-timing alpha claim.** All results are retrospective **EXPOSED_HISTORY**.

### Forecasting · HAR vs training-selected GARCH

{table(g)}

### Risk control · Buy & Hold → Full VOL

{table(pd.DataFrame(top))}

Average forecast improvements are positive; the frozen joint HAR-over-GARCH inference verdict remains **WEAK**. Risk control sacrifices some equity return. These are historical results, not prospective deployment evidence.

## What the model achieves

Lower MSE and QLIKE against both training-selected GARCH and Rolling22, on common model dates for each ETF. No baseline was selected using final test-period performance.

![HAR forecast error reductions for SPY and QQQ](results/figures/FORECAST_ACCURACY.png)

The full-history view below pairs each forecast origin with the risk subsequently realized over the next five holding sessions, on the same annualized quadratic-risk scale. The overlapping targets make this a visual diagnostic; the formal comparisons continue to use the frozen loss and block-inference protocol.

![HAR predicted and realized future five-day risk through time](results/figures/FORECAST_TIMESERIES.png)

## A simple risk-control application

**Forecast future five-day risk → scale equity exposure → residual capital earns short-duration Treasury cash carry.**

Next-open execution every five sessions. No leverage or shorting. The figures use the original primary offset 0, 1bp per traded equity notional and the frozen 3M Treasury yield-carry proxy.

{table(account_table)}

{table(red)}

Account samples: {dates}. ES95 is five-day loss; MaxDD is a positive loss magnitude. Forecast history is longer than account history because FHS and cash eligibility require additional history.

![SPY wealth, drawdown and equity exposure](results/figures/SPY_RISK_CONTROL.png)

### QQQ transfer · same framework, same decision rule, different equity ETF

The risk-budget calibration rule is identical, although its training-derived value differs by asset. QQQ is a historical transfer check, **not independent prospective validation**.

![QQQ wealth, drawdown and equity exposure](results/figures/QQQ_RISK_CONTROL.png)

![Return participation versus risk reduction](results/figures/RISK_RETURN_TRADEOFF.png)

## Is this just lower average equity exposure?

**No, not entirely.** Full VOL holds less equity on average ({mean_exposure}), so part of its risk reduction naturally comes from lower exposure. The **ex-post matched-average-exposure static control** matches Full VOL's realized mean exposure, including drift, using the same dates, cash and costs.

{table(matched_table)}

In these full-history comparisons, **dynamic volatility scaling improves risk control beyond simply maintaining a permanently lower equity allocation.**

**This does not imply return-timing alpha: the return contribution of dynamic timing is weak / negative, and the advantage is not stable across every historical regime.**

![Full VOL risk gains versus matched-average-exposure static controls](results/figures/MATCHED_EXPOSURE_RISK_GAIN.png)

Each reduction uses the matched static account's risk as its denominator, not Buy & Hold risk. The control uses full-period information and is an attribution diagnostic, not a deployable strategy or prospective evidence. [Canonical attribution](results/strategy/HEADLINE_ATTRIBUTION.csv) preserves the underlying comparisons. The original promotion gate remains WEAK with no prospective candidate. [Full report](REPORT.md).

## How it works

Daily adjusted OHLC → session GK plus gap risk → HAR(1,5,22) → future five-day holding risk → Full VOL / cash.

![Session, gap, state and holding-risk alignment](results/figures/SESSION_HOLDING_TIMELINE.png)

$$
\begin{{aligned}}
\mathrm{{GK}}_{{\mathrm{{RTH}},t}}
&= \frac{{1}}{{2}}\left[\log\left(\frac{{H_t}}{{L_t}}\right)\right]^2
{{}}- (2\log 2 - 1)\left[\log\left(\frac{{C_t}}{{O_t}}\right)\right]^2 \\
\mathrm{{GAP2}}_t
&= \left[\log\left(\frac{{O_t}}{{C_{{t-1}}}}\right)\right]^2 \\
\mathrm{{STATE}}_t
&= \mathrm{{GAP2}}_t + \mathrm{{GK}}_{{\mathrm{{RTH}},t}} \\
\mathrm{{HOLD}}_t
&= \mathrm{{GK}}_{{\mathrm{{RTH}},t}} + \mathrm{{GAP2}}_{{t+1}} \\
Y_{{t,5}}
&= \frac{{1}}{{5}}\sum_{{h=1}}^{{5}}\mathrm{{HOLD}}_{{t+h}}.
\end{{aligned}}
$$

The after-close signal at $t$ controls open $t+1$ to open $t+6$; the pre-entry gap is excluded. **Gap² captures only the net overnight shock, not the full intranight price path.** This is a quadratic-risk proxy, not a squared endpoint return or complete latent overnight variance.

Monthly expanding log-HAR uses fixed 1/5/22 state averages, at least 504 mature training observations and training-only smearing. GARCH uses training-only BIC over the frozen (1,1), (1,2), (2,1), Normal/t family and the original bridge to the common holding-risk target. [Frozen protocol](GARCH_RESEARCH_PLAN.md).

$$
\widehat{{v}}_{{t,5}}^{{\mathrm{{HAR}}}}
= \widehat{{s}}_m\exp\left(
\widehat{{\beta}}_{{0,m}}+
\sum_{{k\in\{{1,5,22\}}}}\widehat{{\beta}}_{{k,m}}
\log\overline{{\mathrm{{STATE}}}}_{{t,k}}
\right).
$$

Here $m$ is the current monthly training vintage, $\overline{{\mathrm{{STATE}}}}_{{t,k}}$ is the mean of the latest $k$ valid risk-state observations through $t$, and $\widehat{{s}}_m$ is the training-only mean exponentiated log residual (smearing factor). The existing numerical variance floor is retained in the implementation.

$$
\begin{{aligned}}
w_t^{{\mathrm{{equity}}}}
&= \min\left(
1,
\max\left(
0,
\frac{{B}}{{\sqrt{{5 \widehat{{v}}_{{t,5}}^{{\mathrm{{HAR}}}}}}}}
\right)
\right), \\
w_t^{{\mathrm{{cash}}}}
&= 1 - w_t^{{\mathrm{{equity}}}}.
\end{{aligned}}
$$

Here $B$ is the frozen risk budget and $\widehat{{v}}_{{t,5}}^{{\mathrm{{HAR}}}}$ forecasts the mean daily holding-risk proxy $Y_{{t,5}}$.

The existing budget is calibrated once at the first eligible FHS vintage:

$$
B = 0.8 Q_{{0.5}}\left((s_\tau)_{{\tau \le t_0}}\right).
$$

Here $Q_{{0.5}}$ is the median of the past eligible risk-scale observations available at the initial calibration date $t_0$. The budget is neither newly optimized nor reset to a 15% target. The transparent self-financing engine retains units/cash, natural drift, initial funding fees, no terminal liquidation and the original five rebalance offsets; no second accounting engine is introduced.

Cash uses the frozen DGS3MO 3M Treasury **yield-carry approximation**: at least two prior stock sessions, maximum seven-calendar-day quote age, ACT/365 carry locked for each block. It is not an executable T-bill total-return index. Release-vintage provenance remains PARTIAL. Stale quotes are not filled; the original SPY September-2001 eligibility break is retained. ZERO cash and 0/1/3bp costs remain in the full [SPY results](results/strategy/SPY/PORTFOLIO_RESULTS.csv) and [QQQ results](results/strategy/QQQ/PORTFOLIO_RESULTS.csv).

## Forecast validation · higher predicted risk, higher future risk

![Past-only HAR risk buckets and realized future holding risk](results/figures/FORECAST_VS_REALIZED.png)

This plot reuses the existing past-only percentile buckets; it does not regroup the sample. Each point shows

$$
\mathrm{{RiskScale}}_b (\%) = 100\sqrt{{252 \overline{{v}}_b}},
$$

where $\overline{{v}}_b$ is the bucket mean daily variance proxy. It is an annualized quadratic-risk scale, not the volatility of a five-day endpoint return. The mean curves show risk ranking and average calibration; they are not confidence bands.

Daily input history spans {price_span}. Mature forecast windows and account start dates differ. [Coverage](results/forecast/DATA_COVERAGE.csv), [forecast/regime scores](results/forecast/BENCHMARK_METRICS.csv) and [paired 21/42-session block intervals](results/forecast/BENCHMARK_PAIRED_INTERVALS.csv) retain full history, crisis windows, recent periods and exclusions. Positive average loss improvements do not imply uniform outperformance across every regime.

## Tail-risk interpretation

Filtered Historical Simulation (FHS) uses $\sqrt{{5 \widehat{{v}}_{{t,5}}^{{\mathrm{{HAR}}}}}}$ to scale mature empirical five-day standardized returns and six-open drawdown paths. The fixed expanding history, 1,008-observation minimum and monthly updates remain unchanged. It adds useful VaR, ES, loss-probability and path-risk information over unfiltered HS: [tail scores](results/tail/HEADLINE_METRICS.csv).

Volatility scale captures much of the useful dynamic tail information; a separate dynamic standardized left-tail state was not supported. Rare >5% losses have weaker inference than the primary >2% event. Distribution width and downside scale are more predictable here than return mean or direction.

## What did not add stable value

| Extension | Question | Verdict | Why retired |
| --- | --- | --- | --- |
| Intraday / refined RV | Measurement detail? | Weak | No stable portfolio increment over daily GK |
| Extra risk predictors | More structure? | Weak / not supported | No stable incremental value |
| Gold / Treasury transfer | Cross-asset forecasting? | Mixed | HAR-over-GARCH unconfirmed; GC data blocked |
| Dependence / cDCC | Better decisions? | Weak | Limited covariance/portfolio value |
| Return direction | Return timing? | Not supported | No stable predictive increment |
| Dynamic tail shape | Another mapping? | Weak | Simple scale remained most interpretable |
| Treasury parking | Replace cash? | Weak | No stable conditional gain; adverse 2022 evidence |
| Gold / multi-asset allocation | Broader architecture? | Not promoted | Strategic diversification was historically useful, but dynamic allocation lacked robust increment for this single-asset project |
| Long-horizon / term-structure risk | Combine 5D and 21D? | Not promoted | 21D risk was forecastable and benefited from sequential reforecasting, but nearly collinear signals did not improve the 5D portfolio |

[Research history](RESEARCH_HISTORY_SUMMARY.md) and [post-convergence summary](POST_CONVERGENCE_RESEARCH_SUMMARY.md) preserve qualified findings and closed gates.

## Limitations

Historical selection bias survives walk-forward design and bootstrap. Yahoo adjustments may be revised; adjusted-unit accounting does not establish historical auction fills or impact. Duration-sensitive Treasury ETFs can fall alongside equities and are not risk-free cash. The cash proxy and GK overnight representation have the limits described above. No evidence here authorizes deployment, and the existing FULL_HAR prospective shadow is unchanged.

## Reproduction

```powershell
python -m pip install -r requirements-lock.txt
python -B scripts/reproduce.py --output artifacts/reproduction
python -B -m pytest -q
python -B scripts/audit.py
```

Use a new or empty output directory and the hash-matching [local inputs](data/README.md); raw observations are not redistributed. Default reproduction reruns frozen specifications. `--frozen-forecast` reuses verified marginal forecasts while reproducing FHS/accounts. To redraw only, run `python -B scripts/render_presentation.py --source artifacts/canonical_final --output artifacts/presentation_preview`. Neither entry downloads data or changes models.

Headlines and figures are generated from canonical tables. [Presentation provenance](results/figures/PRESENTATION_PROVENANCE.json) · [refinement notes](PRESENTATION_REFACTOR.md) · [validation](VALIDATION.md) · [project structure](FINAL_PROJECT_STRUCTURE.md).
"""
