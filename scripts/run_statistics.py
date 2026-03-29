#!/usr/bin/env python3
"""Standalone strict statistical analysis for experiment results.

Encodes the full statistical decision tree so the LLM never needs to load
560 lines of statistical-methods.md.  Reads a CSV, runs assumption checks,
selects the right test, computes effect sizes + post-hocs, and writes both
a human-readable Markdown appendix and a machine-readable JSON file.
"""

from __future__ import annotations

import argparse
import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


# ── helpers ─────────────────────────────────────────────────────────────
def _ci95(vals: np.ndarray) -> tuple[float, float]:
    """95 % CI using t-distribution."""
    n = len(vals)
    if n < 2:
        m = float(vals[0]) if n == 1 else float("nan")
        return (m, m)
    se = stats.sem(vals)
    h = se * stats.t.ppf(0.975, n - 1)
    m = float(np.mean(vals))
    return (m - h, m + h)


def _cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return float("nan")
    pooled = np.sqrt(((na - 1) * np.var(a, ddof=1) + (nb - 1) * np.var(b, ddof=1)) / (na + nb - 2))
    return float((np.mean(a) - np.mean(b)) / pooled) if pooled > 0 else float("nan")


def _eta_squared(ss_between: float, ss_total: float) -> float:
    return ss_between / ss_total if ss_total > 0 else float("nan")


def _safe_shapiro(x: np.ndarray) -> tuple[float, float]:
    if len(x) < 3:
        return (float("nan"), float("nan"))
    return tuple(float(v) for v in stats.shapiro(x))  # type: ignore[return-value]


# ── core ────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description="Strict statistical analysis of experiment results.")
    ap.add_argument("--results", required=True, help="Path to CSV with experiment results")
    ap.add_argument("--metric", required=True, help="Column name of the primary metric")
    ap.add_argument("--groupby", default="strategy,task", help="Comma-separated grouping columns")
    ap.add_argument("--seed-col", default="seed", help="Column that holds seed values")
    ap.add_argument("--alpha", type=float, default=0.05, help="Significance level")
    ap.add_argument("--output-dir", default="analysis-output/", help="Directory for output files")
    args = ap.parse_args()

    alpha: float = args.alpha
    groupby_cols = [c.strip() for c in args.groupby.split(",")]
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    # 1. Load & validate ─────────────────────────────────────────────────
    print(f"[1/7] Loading {args.results} …")
    df = pd.read_csv(args.results)
    print(f"       Shape: {df.shape[0]} rows × {df.shape[1]} cols")

    for col in [args.metric, args.seed_col] + groupby_cols:
        if col not in df.columns:
            print(f"ERROR: column '{col}' not found. Available: {list(df.columns)}")
            return 1

    metric_vals = df[args.metric].dropna()
    if metric_vals.empty:
        print("ERROR: metric column is entirely NaN.")
        return 1

    groups = df.groupby(groupby_cols, sort=True)
    group_names: list[str] = ["|".join(str(v) for v in (k if isinstance(k, tuple) else (k,))) for k in groups.groups]
    group_arrays: list[np.ndarray] = [g[args.metric].dropna().values for _, g in groups]
    n_groups = len(group_names)

    if n_groups < 2:
        print("WARNING: fewer than 2 groups — only descriptive stats will be produced.")

    # 2. Metric comparability ────────────────────────────────────────────
    print("[2/7] Checking metric comparability …")
    ranges = [(float(a.min()), float(a.max())) for a in group_arrays if len(a) > 0]
    if ranges:
        all_mins, all_maxs = zip(*ranges)
        if max(all_maxs) > 10 * max(min(all_maxs), 1e-9) and min(all_mins) >= 0:
            span_ratio = max(all_maxs) / max(min(all_maxs), 1e-9)
            if span_ratio > 50:
                print(f"  ⚠ WARNING: metric ranges differ by ~{span_ratio:.0f}×. Verify comparability.")
            else:
                print("  Scales look comparable.")
        else:
            print("  Scales look comparable.")

    # 3. Descriptive stats ───────────────────────────────────────────────
    print("[3/7] Computing descriptive statistics …")
    desc_rows: list[dict] = []
    for name, arr in zip(group_names, group_arrays):
        n = len(arr)
        ci_lo, ci_hi = _ci95(arr)
        desc_rows.append({
            "group": name, "n_seeds": n,
            "mean": float(np.mean(arr)) if n else float("nan"),
            "std": float(np.std(arr, ddof=1)) if n > 1 else float("nan"),
            "SE": float(stats.sem(arr)) if n > 1 else float("nan"),
            "CI95_lo": ci_lo, "CI95_hi": ci_hi,
            "min": float(arr.min()) if n else float("nan"),
            "max": float(arr.max()) if n else float("nan"),
        })
    desc_df = pd.DataFrame(desc_rows)

    results: dict = {"metric": args.metric, "alpha": alpha, "n_groups": n_groups,
                     "descriptive": desc_rows}

    if n_groups < 2:
        _write_outputs(outdir, results, desc_df, args.metric, alpha)
        return 0

    # 4. Assumption checks ───────────────────────────────────────────────
    print("[4/7] Running assumption checks …")
    # Shapiro-Wilk on residuals
    all_vals = np.concatenate(group_arrays)
    grand_mean = np.mean(all_vals)
    residuals = np.concatenate([a - np.mean(a) for a in group_arrays if len(a) >= 3])
    sw_stat, sw_p = _safe_shapiro(residuals)
    normal = sw_p > alpha if not np.isnan(sw_p) else True  # assume normal if untestable
    print(f"  Shapiro-Wilk on residuals: W={sw_stat:.4f}, p={sw_p:.4g} → {'PASS' if normal else 'FAIL'}")

    # Levene's test
    arrays_for_levene = [a for a in group_arrays if len(a) >= 2]
    if len(arrays_for_levene) >= 2:
        lev_stat, lev_p = stats.levene(*arrays_for_levene)
        equal_var = float(lev_p) > alpha
        print(f"  Levene's test: F={float(lev_stat):.4f}, p={float(lev_p):.4g} → {'PASS' if equal_var else 'FAIL'}")
    else:
        lev_stat, lev_p = float("nan"), float("nan")
        equal_var = True

    results["assumptions"] = {
        "shapiro_wilk": {"W": sw_stat, "p": sw_p, "normal": normal},
        "levene": {"F": float(lev_stat), "p": float(lev_p), "equal_var": equal_var},
    }

    # 5. Automatic test selection ────────────────────────────────────────
    print("[5/7] Selecting and running statistical tests …")
    tests: list[dict] = []

    # Check for 2-way ANOVA opportunity
    if len(groupby_cols) == 2 and normal and n_groups >= 4:
        print("  → 2-way ANOVA with interaction")
        try:
            from statsmodels.formula.api import ols
            from statsmodels.stats.anova import anova_lm
            safe = {c: c.replace(" ", "_").replace("-", "_") for c in groupby_cols}
            tmp = df[[args.metric] + groupby_cols].dropna().copy()
            for orig, s in safe.items():
                tmp = tmp.rename(columns={orig: s})
            formula = f"{args.metric} ~ C({safe[groupby_cols[0]]}) * C({safe[groupby_cols[1]]})"
            model = ols(formula, data=tmp).fit()
            table = anova_lm(model, typ=2)
            tests.append({"test": "2-way ANOVA", "table": table.to_dict()})
            print(f"  2-way ANOVA computed (see report for table).")
        except Exception as e:
            print(f"  2-way ANOVA failed ({e}), falling back to 1-way.")

    if n_groups == 2:
        a, b = group_arrays[0], group_arrays[1]
        if normal and equal_var:
            stat, p = stats.ttest_ind(a, b)
            test_name = "Independent t-test"
        elif normal:
            stat, p = stats.ttest_ind(a, b, equal_var=False)
            test_name = "Welch's t-test"
        else:
            stat, p = stats.mannwhitneyu(a, b, alternative="two-sided")
            test_name = "Mann-Whitney U"
        tests.append({"test": test_name, "statistic": float(stat), "p": float(p)})
        print(f"  → {test_name}: stat={float(stat):.4f}, p={float(p):.4g}")

    elif n_groups >= 3:
        if normal and equal_var:
            stat, p = stats.f_oneway(*group_arrays)
            test_name = "One-way ANOVA"
        elif normal:
            stat, p = stats.f_oneway(*group_arrays)  # approximate; scipy lacks Welch ANOVA
            test_name = "Welch ANOVA (approx via f_oneway)"
        else:
            stat, p = stats.kruskal(*group_arrays)
            test_name = "Kruskal-Wallis"
        tests.append({"test": test_name, "statistic": float(stat), "p": float(p)})
        print(f"  → {test_name}: stat={float(stat):.4f}, p={float(p):.4g}")

    results["tests"] = tests

    # 6. Effect sizes ────────────────────────────────────────────────────
    print("[6/7] Computing effect sizes …")
    pairwise_effects: list[dict] = []
    for (n1, a1), (n2, a2) in combinations(zip(group_names, group_arrays), 2):
        d = _cohens_d(a1, a2)
        pairwise_effects.append({"groupA": n1, "groupB": n2, "cohens_d": d})

    # Eta-squared for ANOVA-style tests
    eta_sq = float("nan")
    if n_groups >= 3:
        ss_between = sum(len(a) * (np.mean(a) - grand_mean) ** 2 for a in group_arrays)
        ss_total = np.sum((all_vals - grand_mean) ** 2)
        eta_sq = _eta_squared(ss_between, float(ss_total))
        print(f"  η² = {eta_sq:.4f}")

    results["effect_sizes"] = {"pairwise_cohens_d": pairwise_effects, "eta_squared": eta_sq}

    # 7. Post-hoc (Tukey HSD) ────────────────────────────────────────────
    print("[7/7] Running post-hoc tests …")
    posthoc_rows: list[dict] = []
    if n_groups >= 3:
        try:
            from statsmodels.stats.multicomp import pairwise_tukeyhsd
            all_data = np.concatenate(group_arrays)
            labels = np.concatenate([[name] * len(arr) for name, arr in zip(group_names, group_arrays)])
            tukey = pairwise_tukeyhsd(all_data, labels, alpha=alpha)
            for row in tukey.summary().data[1:]:
                posthoc_rows.append({
                    "groupA": str(row[0]), "groupB": str(row[1]),
                    "meandiff": float(row[2]), "p_adj": float(row[3]),
                    "lower": float(row[4]), "upper": float(row[5]),
                    "reject": bool(row[6]),
                })
            print(f"  Tukey HSD: {sum(r['reject'] for r in posthoc_rows)}/{len(posthoc_rows)} pairs significant.")
        except Exception as e:
            print(f"  Tukey HSD failed: {e}")

    results["posthoc_tukey"] = posthoc_rows
    _write_outputs(outdir, results, desc_df, args.metric, alpha, posthoc_rows)
    return 0


# ── output writers ──────────────────────────────────────────────────────
def _write_outputs(
    outdir: Path,
    results: dict,
    desc_df: pd.DataFrame,
    metric: str,
    alpha: float,
    posthoc: list[dict] | None = None,
) -> None:
    # --- JSON ---
    json_path = outdir / "stats-raw.json"

    class _Enc(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, (np.integer,)):
                return int(o)
            if isinstance(o, (np.floating,)):
                return float(o)
            if isinstance(o, np.ndarray):
                return o.tolist()
            if isinstance(o, (np.bool_,)):
                return bool(o)
            return super().default(o)

    json_path.write_text(json.dumps(results, indent=2, cls=_Enc))
    print(f"\n  Wrote {json_path}")

    # --- Markdown ---
    md_path = outdir / "stats-appendix.md"
    lines: list[str] = ["# Statistical Analysis Appendix\n"]
    lines.append(f"**Metric**: `{metric}` | **α** = {alpha}\n")

    # Descriptive table
    lines.append("## Descriptive Statistics\n")
    lines.append("| Group | n | mean | std | SE | 95% CI | min | max |")
    lines.append("|-------|---|------|-----|----|--------|-----|-----|")
    for _, r in desc_df.iterrows():
        ci = f"[{r['CI95_lo']:.4f}, {r['CI95_hi']:.4f}]"
        lines.append(
            f"| {r['group']} | {r['n_seeds']} | {r['mean']:.4f} | {r['std']:.4f} "
            f"| {r['SE']:.4f} | {ci} | {r['min']:.4f} | {r['max']:.4f} |"
        )
    lines.append("")

    # Assumptions
    if "assumptions" in results:
        a = results["assumptions"]
        lines.append("## Assumption Checks\n")
        sw = a["shapiro_wilk"]
        lines.append(f"- **Shapiro-Wilk** (residuals): W={sw['W']:.4f}, p={sw['p']:.4g} "
                      f"→ {'Normal' if sw['normal'] else 'Non-normal'}")
        lev = a["levene"]
        lines.append(f"- **Levene's test**: F={lev['F']:.4f}, p={lev['p']:.4g} "
                      f"→ {'Equal variance' if lev['equal_var'] else 'Unequal variance'}")
        lines.append("")

    # Tests
    if "tests" in results:
        lines.append("## Statistical Tests\n")
        for t in results["tests"]:
            if "statistic" in t:
                sig = "significant" if t["p"] < alpha else "not significant"
                lines.append(f"- **{t['test']}**: statistic={t['statistic']:.4f}, "
                             f"p={t['p']:.4g} ({sig})")
            else:
                lines.append(f"- **{t['test']}**: see table in JSON output")
        lines.append("")

    # Effect sizes
    if "effect_sizes" in results:
        es = results["effect_sizes"]
        lines.append("## Effect Sizes\n")
        if not np.isnan(es.get("eta_squared", float("nan"))):
            lines.append(f"- **η²** = {es['eta_squared']:.4f}")
        if es.get("pairwise_cohens_d"):
            lines.append("\n| Pair | Cohen's d |")
            lines.append("|------|-----------|")
            for p in es["pairwise_cohens_d"]:
                lines.append(f"| {p['groupA']} vs {p['groupB']} | {p['cohens_d']:.4f} |")
        lines.append("")

    # Post-hoc
    if posthoc:
        lines.append("## Post-hoc: Tukey HSD\n")
        lines.append("| Group A | Group B | Mean Diff | p (adj) | 95% CI | Reject H₀ |")
        lines.append("|---------|---------|-----------|---------|--------|-----------|")
        for r in posthoc:
            ci = f"[{r['lower']:.4f}, {r['upper']:.4f}]"
            lines.append(f"| {r['groupA']} | {r['groupB']} | {r['meandiff']:.4f} "
                         f"| {r['p_adj']:.4g} | {ci} | {'Yes' if r['reject'] else 'No'} |")
        lines.append("")

    md_path.write_text("\n".join(lines))
    print(f"  Wrote {md_path}")


if __name__ == "__main__":
    sys.exit(main())
