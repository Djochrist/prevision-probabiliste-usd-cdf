#!/usr/bin/env python3
"""Post-hoc paired CRPS tests; preserve the original observation-index grid."""
import csv
import json
import math
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "previsions_brutes_completes.csv"
OUT = ROOT / "tests_statistiques_retro_2026-11-02.json"
REPORT = ROOT / "tests_statistiques_retro_2026-11-02.md"
HORIZONS = (5, 10, 20)
BLOCKS = (5, 10, 20, 40, 60)
B = 3000
SEED = 20261102


def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def mean(xs):
    return math.fsum(xs) / len(xs)


def quantile(xs, p):
    z = sorted(xs)
    pos = (len(z) - 1) * p
    lo = int(pos)
    hi = min(lo + 1, len(z) - 1)
    return z[lo] + (pos - lo) * (z[hi] - z[lo])


def hac(values, indices, bandwidth):
    n = len(values)
    m = mean(values)
    centered = [x - m for x in values]
    # Missing origin positions remain genuine gaps: lag k means k source rows.
    by_index = dict(zip(indices, centered))
    lrv = math.fsum(x * x for x in centered)
    for lag in range(1, bandwidth + 1):
        covsum = math.fsum(by_index[i] * by_index[i-lag]
                           for i in by_index if i-lag in by_index)
        lrv += 2.0 * (1.0 - lag / (bandwidth + 1.0)) * covsum
    se = math.sqrt(max(0.0, lrv)) / n
    z = m / se if se else (0.0 if m == 0 else math.copysign(math.inf, m))
    # Negative difference means QRF lower loss/better.
    p_one = norm_cdf(z)
    p_two = min(1.0, 2.0 * min(p_one, 1.0-p_one))
    return {"hac_lag_positions": bandwidth, "mean_difference": m,
            "se_hac": se, "z": z, "p_one_sided_qrf_better": p_one,
            "p_two_sided": p_two}


def block_bootstrap(values, indices, block, rng):
    lo, hi = min(indices), max(indices)
    grid = dict(zip(indices, values))
    span = hi - lo + 1
    means = []
    for _ in range(B):
        total = 0.0
        count = 0
        sampled_positions = 0
        while sampled_positions < span:
            start = rng.randrange(lo, hi + 1)
            take = min(block, span-sampled_positions)
            for k in range(take):
                j = lo + ((start-lo+k) % span)
                if j in grid:
                    total += grid[j]
                    count += 1
            sampled_positions += take
        means.append(total/count)
    obs = mean(values)
    # Centered bootstrap null for the one-sided alternative mean difference < 0.
    centered = [x-obs for x in means]
    p = (1 + sum(x <= obs for x in centered))/(B+1)
    return {"block_length_positions": block, "replicates": B,
            "ci95_percentile": [quantile(means, .025), quantile(means, .975)],
            "p_one_sided_centered": p}


def holm(items):
    order = sorted(range(len(items)), key=lambda i: items[i])
    result = [None] * len(items)
    running = 0.0
    n = len(items)
    for rank, idx in enumerate(order):
        running = max(running, (n-rank)*items[idx])
        result[idx] = min(1.0, running)
    return result


rows = defaultdict(dict)
with SOURCE.open(encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        if r["configuration"] != "principal":
            continue
        h = int(r["horizon"])
        if h not in HORIZONS:
            continue
        key = int(r["indice_origine"])
        rows[h].setdefault(key, {})[r["modele"]] = float(r["crps"])

rng = random.Random(SEED)
results = []
for h in HORIZONS:
    matched = [(i, v["qrf"]-v["historique"])
               for i, v in sorted(rows[h].items())
               if "qrf" in v and "historique" in v]
    indices = [x[0] for x in matched]
    diffs = [x[1] for x in matched]
    ref = [rows[h][i]["historique"] for i in indices]
    qrf = [rows[h][i]["qrf"] for i in indices]
    gain = 100.0*(mean(ref)-mean(qrf))/mean(ref)
    tests = [hac(diffs, indices, lag) for lag in (h-1, 2*h, 60)]
    boots = [block_bootstrap(diffs, indices, block, rng) for block in BLOCKS]
    results.append({"horizon": h, "n_paires": len(diffs),
                    "premier_indice": min(indices), "dernier_indice": max(indices),
                    "moyenne_crps_historique": mean(ref), "moyenne_crps_qrf": mean(qrf),
                    "gain_crps_relatif_pct": gain,
                    "difference_moyenne_qrf_moins_historique": mean(diffs),
                    "hac": tests, "bootstrap_circulaire_par_bloc": boots})

# Primary family-wise adjustment: one-sided Newey-West p at 60 source positions.
raw = [x["hac"][2]["p_one_sided_qrf_better"] for x in results]
adj = holm(raw)
for x, p in zip(results, adj):
    x["p_hac_lag60_holm"] = p

payload = {
    "date_utc": datetime.now(timezone.utc).isoformat(),
    "source": SOURCE.name,
    "question": "QRF versus historical reference on paired CRPS, principal configuration",
    "direction": "difference = CRPS_QRF - CRPS_historique; negative favors QRF",
    "primary_test": "one-sided Newey-West HAC at 60 source positions; Holm over three horizons",
    "sensitivity_hac_lags": "h-1 and 2h source positions",
    "bootstrap": {"method": "circular moving blocks on original index span; absent rows stay absent",
                  "lengths_source_positions": list(BLOCKS), "replicates": B, "seed": SEED},
    "limitations": ["post-hoc exploratory analysis; scores and data were already inspected",
                    "large-sample normal HAC p-values; no independent prospective holdout",
                    "bootstrap intervals are sensitivity estimates, not confirmatory evidence",
                    "only primary CRPS comparison is tested; secondary scores are not significance-tested"],
    "horizons": results,
}
OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

lines = ["# Tests statistiques rétrospectifs des différences de CRPS", "",
         "Analyse post hoc appariée, datée du 2 novembre 2026. Une différence négative (CRPS QRF − CRPS historique) favorise la forêt quantile. Le test principal est unilatéral, avec variance HAC de Newey–West sur 60 positions de la série; les trois valeurs p sont corrigées par Holm.",
         "", "Les longueurs HAC de h−1 et 2h et les blocs circulaires de 5, 10, 20, 40 et 60 positions sont des sensibilités. Les positions manquantes restent des lacunes sur la grille d’origine. Le bootstrap utilise 3 000 réplications et la graine 20261102.", "",
         "| Horizon | Paires | CRPS historique | CRPS QRF | Gain relatif | Différence QRF−réf. | p HAC 60 (brute) | p HAC 60 (Holm) | IC bootstrap 95 %, bloc 60 | p bootstrap bloc 60 |",
         "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
for x in results:
    b = x["bootstrap_circulaire_par_bloc"][-1]
    lines.append(f"| {x['horizon']} | {x['n_paires']} | {x['moyenne_crps_historique']:.5f} | {x['moyenne_crps_qrf']:.5f} | {x['gain_crps_relatif_pct']:.2f}% | {x['difference_moyenne_qrf_moins_historique']:.5f} | {x['hac'][2]['p_one_sided_qrf_better']:.4g} | {x['p_hac_lag60_holm']:.4g} | [{b['ci95_percentile'][0]:.5f}, {b['ci95_percentile'][1]:.5f}] | {b['p_one_sided_centered']:.4g} |")
lines += ["", "## Interprétation et limites", "",
          "Ces tests quantifient l’incertitude liée à la dépendance temporelle sur les prévisions déjà calculées; ils ne transforment pas cette comparaison rétrospective en validation indépendante. Les valeurs p sont asymptotiques. Les conclusions doivent tenir compte de la correction de Holm et de la stabilité aux longueurs HAC/blocs. Aucun test de significativité des autres indicateurs n’est ajouté.",
          "", "Données et protocole antérieurs conservés sans modification. Script reproductible : `tests_statistiques_retro_2026-11-02.py`."]
REPORT.write_text("\n".join(lines)+"\n", encoding="utf-8")
print(REPORT.read_text(encoding="utf-8"))
