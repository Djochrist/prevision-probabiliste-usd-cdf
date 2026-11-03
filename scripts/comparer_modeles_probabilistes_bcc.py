"""Essai retrospectif de RQ lineaire et QRF face a une reference empirique.

Le calendrier des ajustements depend uniquement des dates passees, jamais des
cibles futures utilisables pour les scores. Bibliotheques isolees dans analyses.
"""
import csv
import hashlib
import importlib.metadata
import json
import os
import platform
import sys
import time
import warnings
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[name] = "1"

import numpy as np
from quantile_forest import RandomForestQuantileRegressor
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import QuantileRegressor
from scipy.optimize import OptimizeWarning
from threadpoolctl import threadpool_limits

from preparer_indicateurs_bcc import FEATURES, HORIZONS, MASK, SOURCE, EXPECTED_HASH, build, targets

OUT = ROOT / "analyses" / "modeles_probabilistes_2026-10-27"
GRID = np.array([.01, .05, .1, .25, .5, .75, .9, .95, .99])
SCENARIOS = 200
PROBS = (np.arange(SCENARIOS) + .5) / SCENARIOS
WEIGHTS_ISO = np.diff(np.r_[0., (GRID[:-1]+GRID[1:])/2, 1.])
ALPHA = .001
SEED = 20261027
FOREST_PARAMS = {"n_estimators": 100, "max_depth": 6, "min_samples_leaf": 20,
                 "max_samples_leaf": None, "max_features": 1.0, "bootstrap": True,
                 "random_state": SEED, "n_jobs": 1}
CONFIGS = (("principal", 1000, False, False), ("sensibilite_donnees", 1000, True, False),
           ("fenetre_500", 500, False, False), ("cours_seul", 1000, False, True))
MODELS = ("historique", "quantile_lineaire", "qrf")
PACKAGES = ("numpy", "scipy", "scikit-learn", "quantile-forest", "joblib", "threadpoolctl", "cloudpickle", "narwhals")
SOLVER_OPTIONS = {"threads": 1, "parallel": False}
WORKERS = min(4, os.cpu_count() or 1)
warnings.filterwarnings("ignore", category=OptimizeWarning, message="Unrecognized options detected.*")
WORKER_STATE = None


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_source():
    raw = SOURCE.read_bytes()
    assert sha(raw) == EXPECTED_HASH
    rows = list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
    rows = [r for r in rows if "2006-01-03" <= r["Date"] <= "2026-10-19"]
    dates = [r["Date"] for r in rows]
    columns = list(rows[0])[1:5]
    values = np.array([[float(r[c]) if r[c] else np.nan for c in columns] for r in rows])
    assert dates == sorted(set(dates)) and len(dates) == 5273
    return dates, values


def make_data(dates, values, masked):
    v = values.copy()
    if masked:
        for d in MASK:
            if d in dates:
                v[dates.index(d), 0] = np.nan
    x = build(*v.T)
    y_pct = targets(v[:, 0])
    y_log = {h: 100 * np.log1p(y_pct[h]/100) for h in HORIZONS}
    return x, y_log, y_pct


def training_indices(x, y, anchor, h, window):
    first, last = anchor-h-window+1, anchor-h
    if first < 20:
        return None
    idx = np.arange(first, last+1)
    # Les memes lignes historiques sont utilisees dans l'ablation cours seul.
    idx = idx[np.all(np.isfinite(x[idx]), axis=1) & np.isfinite(y[idx])]
    if len(idx) < .8*window:
        return None
    assert idx.max()+h <= anchor
    return idx


def fit_models(x, y, anchor, h, window, course_only, cache=None):
    idx = training_indices(x, y, anchor, h, window)
    if idx is None:
        raise ValueError(f"Historique insuffisant en indice {anchor}, h={h}, fenetre={window}")
    count_features = 5 if course_only else 7
    xt, yt = x[idx, :count_features], y[idx]
    cache_key = sha(idx.tobytes()+np.ascontiguousarray(xt).tobytes()+yt.tobytes())
    if cache is not None and cache_key in cache:
        return {**cache[cache_key], "reused": True}
    center, scale = xt.mean(axis=0), xt.std(axis=0, ddof=0)
    scale[scale < 1e-12] = 1.
    z = (xt-center)/scale
    linear = []
    for q in GRID:
        model = QuantileRegressor(quantile=float(q), alpha=ALPHA, solver="highs", solver_options=SOLVER_OPTIONS)
        model.fit(z, yt)
        linear.append(model)
    forest = RandomForestQuantileRegressor(**FOREST_PARAMS)
    forest.fit(xt, yt)
    fitted = {"idx": idx, "historique": yt.copy(), "center": center, "scale": scale,
              "linear": linear, "forest": forest, "count_features": count_features, "reused": False}
    if cache is not None:
        cache[cache_key] = fitted
    return fitted


def predict_distributions(fit, x):
    xp = np.atleast_2d(x)[:, :fit["count_features"]]
    z = (xp-fit["center"])/fit["scale"]
    quantiles = np.column_stack([m.predict(z) for m in fit["linear"]])
    crossing = np.any(np.diff(quantiles, axis=1) < -1e-9, axis=1)
    iso = IsotonicRegression(increasing=True)
    adjusted = np.array([iso.fit_transform(GRID, row, sample_weight=WEIGHTS_ISO) for row in quantiles])
    qr_log = np.array([np.interp(PROBS, GRID, row) for row in adjusted])
    # weighted_leaves inverse la taille des feuilles, avec toutes leurs observations.
    qrf_log = fit["forest"].predict(xp, quantiles=PROBS.tolist(), interpolation="linear",
                                   weighted_quantile=True, weighted_leaves=True,
                                   aggregate_leaves_first=True)
    hist = np.quantile(fit["historique"], PROBS, method="inverted_cdf")
    distributions = {"historique": np.tile(hist, (len(xp), 1)),
                     "quantile_lineaire": qr_log, "qrf": np.atleast_2d(qrf_log)}
    distributions = {name: 100*np.expm1(v/100) for name, v in distributions.items()}
    for values in distributions.values():
        if not np.all(np.isfinite(values)) or not np.all(values > -100):
            raise ArithmeticError("Distribution non finie ou cours non positif; aucun score ignore")
        assert np.all(np.diff(values, axis=1) >= -1e-8)
    return distributions, crossing


def score_samples(samples, actual):
    x = np.sort(samples)
    n = len(x)
    crps = float(np.mean(abs(x-actual)) - np.dot(2*np.arange(1, n+1)-n-1, x)/n**2)
    q05, median, q95 = np.quantile(x, [.05, .5, .95], method="linear")
    p_dep, p_app, p_zero = [float(np.mean(condition)) for condition in (x > 0, x < 0, x == 0)]
    assert crps >= -1e-9 and abs(p_dep+p_app+p_zero-1) < 1e-12
    return {"crps": max(0., crps), "brier_depreciation": (p_dep-(actual > 0))**2,
            "mediane_pct": float(median), "q05_pct": float(q05), "q95_pct": float(q95),
            "prob_depreciation": p_dep, "prob_appreciation": p_app, "prob_stabilite_exacte": p_zero,
            "erreur_absolue_mediane": float(abs(median-actual)),
            "couverture_90": int(q05 <= actual <= q95), "largeur_90": float(q95-q05)}


def basic_checks():
    sample = np.array([-3., 0., 2., 7.])
    for actual in (-4., 1., 9.):
        expected = np.mean(abs(sample-actual)) - .5*np.mean(abs(sample[:, None]-sample))
        assert abs(expected-score_samples(sample, actual)["crps"]) < 1e-12
    # Une courbe volontairement croisee doit devenir monotone sans recourir a une cible.
    values = np.array([-1., -2., -.4, .1, .2, .15, 1., .8, 2.])
    repaired = IsotonicRegression(increasing=True).fit_transform(GRID, values, sample_weight=WEIGHTS_ISO)
    assert np.all(np.diff(repaired) >= 0)


def benchmark():
    print("Bibliotheques chargees; debut du controle d'ajustement", flush=True)
    dates, values = load_source()
    x, y, _ = make_data(dates, values, False)
    anchor = dates.index("2012-01-03")
    start = time.perf_counter()
    fit = fit_models(x, y[5], anchor, 5, 1000, False)
    elapsed = time.perf_counter()-start
    print(json.dumps({"ajustement_termine_secondes": elapsed}), flush=True)
    predict_distributions(fit, x[anchor])
    print(json.dumps({"temps_secondes_un_ajustement_9_quantiles_et_100_arbres": elapsed,
                      "versions": {name: importlib.metadata.version(name) for name in PACKAGES}}, ensure_ascii=False), flush=True)


def configuration(dates, anchors):
    return {"statut": "comparaison retrospective exploratoire, sans optimisation des parametres",
            "date_travail": "2026-10-27", "execution_utc": datetime.now(timezone.utc).isoformat(),
            "python": platform.python_version(), "versions": {name: importlib.metadata.version(name) for name in PACKAGES},
            "source": str(SOURCE), "sha256_source": EXPECTED_HASH,
            "sha256_programme": sha(Path(__file__).read_bytes()),
            "sha256_preparation": sha((ROOT/"preparer_indicateurs_bcc.py").read_bytes()),
            "horizons": HORIZONS, "indicateurs": FEATURES, "configurations": CONFIGS,
            "grille_quantiles_lineaires": GRID.tolist(), "penalite_l1_quantile_lineaire": ALPHA,
            "solveur": "highs", "options_solveur": SOLVER_OPTIONS, "processus_calcul": WORKERS,
            "reutilisation_ajustements": "seulement si indices, entrees et cibles d'apprentissage strictement identiques, avec parametres fixes identiques",
            "normalisation": "moyenne et ecart-type des seules lignes d'ajustement",
            "reparation_quantiles": "projection isotone L2 ponderee; interpolation lineaire et queues constantes",
            "poids_projection_isotone": WEIGHTS_ISO.tolist(),
            "parametres_foret": FOREST_PARAMS,
            "prediction_foret": {"interpolation": "linear", "weighted_quantile": True,
                "weighted_leaves": True, "aggregate_leaves_first": True},
            "representation_distributions": f"{SCENARIOS} scenarios deterministes aux probabilites (k+0.5)/{SCENARIOS}",
            "cible_interne": "100*log(S_(t+h)/S_t), distribution reconvertie en variation simple en pourcentage",
            "calendrier_refit": "premiere observation source de chaque mois, sans utiliser la disponibilite des cibles futures",
            "dates_refit": [dates[a] for a in anchors],
            "periode_origines_depuis": "2012-01-01", "selection_dates_scores": "intersection a posteriori des indicateurs et cibles disponibles, tous horizons et toutes configurations",
            "calibration_supplementaire": "aucune", "test_final_inconnu": False,
            "regle_echeance_cible_apprentissage": "origine_historique+h <= date_refit",
            "min_fraction_historique_valide": .8, "commentaire_fenetre": "nombre de positions d'origine, sans remplacement des lignes incompletes par des lignes plus anciennes"}


def initialize_worker(dates, values, common, check_dates):
    global WORKER_STATE
    WORKER_STATE = (dates, values, make_data(dates, values, False),
                    make_data(dates, values, True), common, check_dates)


def process_month(task):
    month, positions = task
    dates, values, raw, masked, common, check_dates = WORKER_STATE
    anchor = positions[0]
    prediction_idx = np.array([t for t in positions if common[t]], dtype=int)
    records, fit_records, checks, cache = [], [], [], {}
    if not len(prediction_idx):
        return {"mois": month, "previsions": records, "ajustements": fit_records, "controles": checks}
    with threadpool_limits(limits=1):
        for config_name, window, sensitivity, course_only in CONFIGS:
            x, y_log, y_pct = masked if sensitivity else raw
            for h in HORIZONS:
                fit = fit_models(x, y_log[h], anchor, h, window, course_only, cache=cache)
                predictions, crossing = predict_distributions(fit, x[prediction_idx])
                fit_info = {"configuration": config_name, "horizon": h, "date_refit": dates[anchor],
                    "debut_fenetre_origines": dates[anchor-h-window+1], "fin_fenetre_origines": dates[anchor-h],
                    "n_apprentissage": len(fit["idx"]), "echeance_max_apprentissage": dates[int(fit["idx"].max()+h)],
                    "n_indicateurs_modele_conditionnel": fit["count_features"],
                    "reutilisation_ajustement_identique": int(fit["reused"])}
                assert fit_info["echeance_max_apprentissage"] <= fit_info["date_refit"]
                fit_records.append(fit_info)
                for j, t in enumerate(prediction_idx):
                    for model in MODELS:
                        observed = float(raw[2][h][t])
                        rec = {"configuration": config_name, "horizon": h, "modele": model,
                            "indice_origine": int(t), "origine": dates[t], "echeance": dates[t+h],
                            "date_refit": dates[anchor], "n_apprentissage": len(fit["idx"]),
                            "echeance_max_apprentissage": fit_info["echeance_max_apprentissage"],
                            "variation_observee_pct": observed,
                            "quantiles_croises_avant_projection": int(crossing[j]) if model == "quantile_lineaire" else 0}
                        rec.update(score_samples(predictions[model][j], observed))
                        records.append(rec)
                if config_name == "principal":
                    for t in prediction_idx:
                        if check_dates.get(dates[t]) != h:
                            continue
                        prefix = make_data(dates[:t+1], values[:t+1], False)
                        prefix_fit = fit_models(prefix[0], prefix[1][h], anchor, h, window, False)
                        replay, _ = predict_distributions(prefix_fit, prefix[0][t])
                        j = list(prediction_idx).index(t)
                        for model in MODELS:
                            assert np.allclose(predictions[model][j], replay[model][0], rtol=0, atol=1e-10)
                            checks.append({"origine": dates[t], "horizon": h, "modele": model,
                                           "recalcul_source_tronquee_identique": True})
    return {"mois": month, "previsions": records, "ajustements": fit_records, "controles": checks}


def main():
    basic_checks()
    dates, values = load_source()
    raw = make_data(dates, values, False)
    masked = make_data(dates, values, True)
    n = len(dates)
    common = np.array([d >= "2012-01-01" and t+max(HORIZONS) < n for t, d in enumerate(dates)])
    eligible_raw = common & np.all(np.isfinite(raw[0]), axis=1)
    for h in HORIZONS:
        eligible_raw &= np.isfinite(raw[2][h])
    assert int(eligible_raw.sum()) == 3584
    common &= np.all(np.isfinite(raw[0]), axis=1) & np.all(np.isfinite(masked[0]), axis=1)
    for h in HORIZONS:
        common &= np.isfinite(raw[2][h]) & np.isfinite(masked[2][h])
    assert int(common.sum()) == 3518
    eligible = np.where(common)[0]
    last = int(eligible[-1])
    check_dates = {}
    for prefix, check_h in (("2013-06", 5), ("2018-09", 10), ("2025-09", 20), ("2025-10", 10)):
        selected = [dates[t] for t in eligible if dates[t].startswith(prefix)]
        assert selected
        check_dates[selected[0]] = check_h
    # Ancres independantes des valeurs futures, y compris de leurs absences.
    groups = defaultdict(list)
    for t, d in enumerate(dates):
        if d >= "2012-01-01" and t <= last:
            groups[d[:7]].append(t)
    anchors = [positions[0] for positions in groups.values()]
    OUT.mkdir(parents=True, exist_ok=True)
    config = configuration(dates, anchors)
    stable_config = {k: v for k, v in config.items() if k != "execution_utc"}
    fingerprint = sha(json.dumps(stable_config, sort_keys=True).encode())
    config["empreinte_configuration"] = fingerprint
    config_path = OUT/"parametres_avant_scores.json"
    if config_path.exists():
        previous = json.loads(config_path.read_text(encoding="utf-8"))
        if previous.get("empreinte_configuration") != fingerprint:
            raise ValueError("Configuration differente : conserver les anciens calculs et choisir un nouveau dossier")
    else:
        config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT/"requirements_versions.txt").write_text("\n".join(f"{p}=={v}" for p, v in config["versions"].items())+"\n", encoding="utf-8")
    write_protocol()
    records, fit_records, checks = [], [], []
    start = time.perf_counter()
    chunks = OUT/"mois"
    chunks.mkdir(exist_ok=True)
    assert chunks.resolve().is_relative_to(ROOT.resolve())
    pending, packets = [], {}
    for month, positions in groups.items():
        chunk_path = chunks/f"{month}.json"
        if chunk_path.exists():
            packet = json.loads(chunk_path.read_text(encoding="utf-8"))
            assert packet["empreinte_configuration"] == fingerprint and packet["mois"] == month
            packets[month] = packet
        else:
            pending.append((month, positions))
    print(json.dumps({"debut": True, "origines_communes": len(eligible), "mois_total": len(groups),
                      "mois_deja_sauvegardes": len(packets), "processus": WORKERS}), flush=True)
    if pending:
        with ProcessPoolExecutor(max_workers=WORKERS, initializer=initialize_worker,
                                 initargs=(dates, values, common, check_dates)) as pool:
            futures = {pool.submit(process_month, task): task[0] for task in pending}
            for future in as_completed(futures):
                packet = future.result()
                month = packet["mois"]
                packet["empreinte_configuration"] = fingerprint
                chunk_path = chunks/f"{month}.json"
                temporary_path = chunk_path.with_suffix(".json.tmp")
                temporary_path.write_text(json.dumps(packet, ensure_ascii=False), encoding="utf-8")
                temporary_path.replace(chunk_path)
                packets[month] = packet
                print(json.dumps({"mois_termine": month, "mois_termines": len(packets),
                    "mois_total": len(groups), "secondes": round(time.perf_counter()-start, 1)}), flush=True)
    for month in groups:
        packet = packets[month]
        records.extend(packet["previsions"])
        fit_records.extend(packet["ajustements"])
        checks.extend(packet["controles"])
    assert len(records) == len(eligible)*len(HORIZONS)*len(CONFIGS)*len(MODELS)
    assert len(checks) == 12
    assert sha(SOURCE.read_bytes()) == EXPECTED_HASH
    write_records(OUT/"previsions.csv", records)
    write_records(OUT/"ajustements.csv", fit_records)
    by_key = defaultdict(list)
    for r in records:
        for period in ("ensemble", r["origine"][:4], "2012-2023" if r["origine"] < "2024" else "2024-2026"):
            by_key[(r["configuration"], r["horizon"], r["modele"], period)].append(r)
    summaries = []
    for (cfg, h, model, period), rows in by_key.items():
        summary = {"configuration": cfg, "horizon": h, "modele": model, "periode": period,
                   "n": len(rows), "premiere_origine": rows[0]["origine"], "derniere_origine": rows[-1]["origine"]}
        for metric in ("crps", "brier_depreciation", "erreur_absolue_mediane", "couverture_90", "largeur_90", "quantiles_croises_avant_projection"):
            summary[metric] = float(np.mean([r[metric] for r in rows]))
        summaries.append(summary)
    baselines = {(s["configuration"], s["horizon"], s["periode"]): s for s in summaries if s["modele"] == "historique"}
    for s in summaries:
        base = baselines[(s["configuration"], s["horizon"], s["periode"])]
        s["gain_crps_pct"] = 100*(1-s["crps"]/base["crps"])
        s["gain_brier_pct"] = 100*(1-s["brier_depreciation"]/base["brier_depreciation"])
    write_records(OUT/"comparaisons.csv", summaries)
    case = [r for r in records if r["configuration"] == "principal" and
            ((r["origine"] == "2025-09-03" and r["horizon"] == 20) or r["echeance"] == "2025-10-15")]
    write_records(OUT/"episode_2025.csv", case)
    result = {"origines_communes": len(eligible), "previsions": len(records),
              "origines_possibles_brutes": int(eligible_raw.sum()),
              "origines_brutes_ecartees_pour_comparaison_appariee": int(eligible_raw.sum()-common.sum()),
              "premiere_origine": dates[int(eligible[0])], "derniere_origine": dates[last],
              "ajustements_groupes": len(fit_records), "recalculs_tronques": checks,
              "ajustements_reutilises_identiques": sum(f["reutilisation_ajustement_identique"] for f in fit_records),
              "secondes_calcul": time.perf_counter()-start, "resume": summaries}
    (OUT/"resultats.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_results(result, summaries, case)
    for s in summaries:
        if s["periode"] == "ensemble":
            print(json.dumps(s, ensure_ascii=False), flush=True)
    print("TERMINE", flush=True)


def write_records(path, rows):
    if not rows:
        return
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_protocol():
    protocol = """# Protocole du premier essai des modèles probabilistes retenus

Date : 27 octobre 2026. Statut : comparaison rétrospective exploratoire. Les familles de modèles et les sept indicateurs sont retenus à la suite des validations dans la conversation. Les paramètres ci-dessous sont des réglages de départ, enregistrés avant le calcul des scores. Aucun réglage n'est sélectionné sur ces scores. Aucun résultat n'est garanti et aucun modèle final n'est désigné d'avance.

## Source et cible

Source : copie intacte de l'export BCC, du 3 janvier 2006 au 19 octobre 2026. Empreinte et versions des bibliothèques enregistrées dans parametres_avant_scores.json. Les dates restent sur leur grille originale. Aucune imputation. Les sept indicateurs et leurs règles d'indisponibilité sont ceux décrits dans analyses/indicateurs_2026-10-27/note_indicateurs.md.

La cible évaluée est la variation simple en pourcentage du cours indicatif en CDF pour 1 USD aux horizons 5, 10 et 20 observations. Les modèles internes utilisent 100 × log(S(t+h)/S(t)). Leurs distributions sont ensuite reconverties par 100 × (exp(L/100)-1), ce qui respecte la positivité des cours. Les probabilités et les scores portent sur la variation simple approuvée. Le signe positif signifie une dépréciation du CDF à l'échéance.

## Chronologie effective

Les ajustements ont lieu à la première date observée de chaque mois, à partir de janvier 2012. Leur calendrier ne dépend pas de l'existence des valeurs futures qui serviront à calculer les scores. Les coefficients et les arbres restent fixes dans le mois. Les indicateurs de la date de prévision sont actualisés à chaque observation.

Le calcul est réparti entre au plus quatre processus indépendants par mois, avec un seul thread par forêt et par solveur HiGHS. À l'intérieur d'un mois, un ajustement est réutilisé seulement si les indices, les indicateurs et les cibles d'apprentissage sont strictement identiques, avec tous les paramètres fixés identiques. Il s'agit d'optimisations d'exécution. Les distributions sont sauvegardées par mois avec l'empreinte de configuration, ce qui permet une reprise sans changer les règles de l'expérience.

À une date d'ajustement a, le modèle d'horizon h utilise les 1 000 positions d'origine allant de a-h-999 à a-h. Ainsi, chaque cible d'apprentissage est arrivée à échéance au plus en a. Les lignes incomplètes sont écartées dans cette fenêtre, sans prendre des lignes plus anciennes en remplacement. Un minimum de 80 % de lignes exploitables est exigé. Le centrage et la réduction de la régression quantile sont estimés uniquement sur ces lignes. La forêt reçoit les mêmes valeurs explicatives, sans normalisation supplémentaire.

La période de notation va de janvier 2012 à la dernière origine ayant une échéance de 20 observations dans le fichier. Les mêmes origines sont notées pour tous les modèles, horizons et configurations. Cette intersection est construite après identification des valeurs observées nécessaires aux scores. Elle ne sert pas à choisir les dates d'ajustement ni les paramètres. Les dates manquantes restent à leur position originale.

La comparaison porte sur 3 518 origines communes aux données brutes et au scénario de masquage, parmi 3 584 origines exploitables en brut. Les 66 dates supplémentaires brutes sont exclues de cette comparaison appariée autour des séquences signalées. Les résultats ne constituent donc pas une évaluation de toutes les dates brutes. Ces effectifs ne sont pas ceux de l'ancien essai à trois indicateurs de cours, qui utilisait 3 666 origines.

Les valeurs datées du cours sont supposées connues après l'observation t. L'activité est décalée d'une observation. Les dates de première publication et les versions historiques ne sont pas connues. Cette simulation à partir d'un export rétrospectif ne démontre pas qu'une alerte était effectivement réalisable en temps réel. Les scores antérieurs de 2012 à 2026 ont déjà été examinés : le présent essai n'est pas un test final resté inconnu.

## Modèles et représentation des distributions

La référence empirique utilise à poids égaux exactement les mêmes cibles historiques arrivées à échéance que les deux modèles conditionnels. Elle ne conditionne pas la distribution sur les indicateurs actuels.

La régression quantile linéaire ajuste les niveaux 0,01 ; 0,05 ; 0,10 ; 0,25 ; 0,50 ; 0,75 ; 0,90 ; 0,95 ; 0,99. Elle utilise la perte quantile et une pénalité L1 de 0,001, sur des indicateurs centrés et réduits. La constante n'est pas pénalisée. Ce réglage modère les coefficients et reste provisoire. Le solveur est HiGHS. Les quantiles prédits sont projetés sur un ordre croissant par régression isotone L2, avec des poids correspondant aux largeurs de leurs cellules de probabilités. La courbe est interpolée linéairement entre ces niveaux et reste constante au-delà des quantiles 0,01 et 0,99. Cette convention définit une approximation de la distribution et des queues bornées, avec des masses aux extrémités. Elle est explicite et fait partie du modèle évalué. Le nombre de prévisions présentant des croisements avant correction est enregistré.

QRF utilise 100 arbres, une profondeur maximale de 6 et au moins 20 observations par feuille. Toutes les observations de chaque feuille sont conservées ; il ne s'agit pas d'une distribution de moyennes d'arbres. La prédiction utilise les quantiles pondérés avec une pondération inverse de la taille des feuilles. Les autres paramètres et la graine aléatoire figurent dans le fichier de paramètres. Ces choix limitent la complexité pour cet essai, sans preuve d'optimalité. QRF reste limité au support des cibles de son ajustement.

Les trois distributions sont représentées par 200 scénarios déterministes aux probabilités (k+0,5)/200. La référence utilise les quantiles empiriques inverses ; QRF utilise les quantiles pondérés de sa distribution ; la régression linéaire utilise sa courbe corrigée et interpolée. La probabilité de dépréciation est la proportion des scénarios strictement positifs. Elle est discrétisée par pas de 0,005. Les intervalles à 90 % et le CRPS sont calculés sur cette représentation finie. Le CRPS est donc exact pour la distribution discrétisée et approché pour la distribution sous-jacente. Cette approximation diffère du premier essai, qui utilisait directement les valeurs empiriques : les chiffres des deux essais ne sont pas comparés sans tenir compte de cette différence.

Aucune recalibration supplémentaire des probabilités ou des intervalles n'est appliquée dans ce premier essai. La couverture effective est mesurée. Une valeur de 0 ou 1 pour une probabilité estimée n'est pas une certitude économique.

## Quatre configurations fixées

1. Principale : données brutes, 1 000 positions d'origine, sept indicateurs.
2. Sensibilité des données : sept cours signalés en juillet 2017 et 2018 rendus indisponibles dans une copie, mêmes règles et paramètres.
3. Sensibilité de fenêtre : données brutes, 500 positions d'origine, mêmes règles et paramètres.
4. Apport de l'activité : données brutes, 1 000 positions d'origine, cinq indicateurs de cours seulement. Les lignes historiques utilisables et les dates notées sont exactement celles de la configuration principale afin d'isoler l'effet des deux indicateurs d'activité.

Le scénario de masquage s'appuie sur une inspection rétrospective des séquences. Il mesure une sensibilité et ne représente pas une correction automatique connue aux dates simulées. Les variantes sont testées séparément, sans effectuer tous leurs croisements. Les nombres d'origines incomplets ne sont pas compressés avant les calculs.

## Évaluation et traçabilité

Les mesures sont le CRPS, le Brier de la dépréciation à l'échéance, l'erreur absolue de la médiane, la couverture et la largeur des intervalles à 90 %. Les gains sont calculés par rapport à la référence de la même configuration et au même horizon. Le résumé comprend l'ensemble, chaque année d'origine et deux sous-périodes descriptives, 2012-2023 et 2024-2026. Aucun classement n'est établi sur un score brut comparant des horizons différents.

Les prévisions se chevauchent et leurs erreurs sont dépendantes. Aucun test de significativité ni intervalle de confiance des gains n'est calculé dans cet essai. Les effectifs ne sont pas interprétés comme autant d'expériences indépendantes. L'épisode de 2025 est une illustration connue, pas un test final indépendant.

Chaque ligne sauvegarde l'origine, l'échéance, la date de réajustement, la dernière échéance d'apprentissage, l'effectif, les prévisions et les scores. Les bornes d'apprentissage sont également conservées par ajustement. Des recalculs de distributions sur des données tronquées à l'origine vérifient la chronologie sur des dates choisies avant les scores. Le score CRPS est vérifié contre sa définition par double somme.

Les sources BCC, Overleaf, GitHub et la plateforme ne sont pas modifiés par cet essai. Les bibliothèques de calcul supplémentaires sont isolées dans analyses/_libs_modeles. Le protocole et ses paramètres sont conservés avant les résultats.

Références techniques : https://zillow.github.io/quantile-forest/generated/quantile_forest.RandomForestQuantileRegressor.html ; https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.QuantileRegressor.html
"""
    (OUT/"protocole_avant_scores.md").write_text(protocol, encoding="utf-8")


def fr(x, digits=2):
    return f"{x:.{digits}f}".replace(".", ",")


def write_results(result, summaries, case):
    note = "# Résultats du premier essai des modèles probabilistes retenus\n\n"
    note += (f"Comparaison rétrospective exploratoire du 27 octobre 2026. {result['origines_communes']} origines communes, "
             f"de {result['premiere_origine']} à {result['derniere_origine']}. {result['previsions']} distributions notées "
             "en comptant les horizons, modèles et variantes. Les prévisions se chevauchent.\n\n")
    note += (f"Ces {result['origines_communes']} origines sont l'intersection avec le scénario de masquage, parmi "
             f"{result['origines_possibles_brutes']} origines exploitables en brut. Les "
             f"{result['origines_brutes_ecartees_pour_comparaison_appariee']} autres dates brutes ne sont pas notées ici. "
             "La conclusion porte sur cette comparaison appariée rétrospective.\n\n")
    note += "Les réglages et limites figurent dans [le protocole enregistré avant les scores](protocole_avant_scores.md). Aucun réglage n'est optimisé sur les scores ci-dessous.\n\n"
    note += "## Configuration principale\n\n| Horizon | Modèle | CRPS | Gain CRPS (%) | Brier | Couverture 90 % |\n| --- | --- | ---: | ---: | ---: | ---: |\n"
    for s in summaries:
        if s["configuration"] == "principal" and s["periode"] == "ensemble":
            note += f"| {s['horizon']} | {s['modele']} | {fr(s['crps'],4)} | {fr(s['gain_crps_pct'])} | {fr(s['brier_depreciation'],4)} | {fr(100*s['couverture_90'])} % |\n"
    note += "\n## Sensibilités\n\nGain CRPS relativement à l'historique de la même configuration. Un gain négatif est une dégradation.\n\n| Configuration | Horizon | Quantile linéaire (%) | QRF (%) |\n| --- | --- | ---: | ---: |\n"
    for cfg, *_ in CONFIGS:
        for h in HORIZONS:
            subset = {s["modele"]: s for s in summaries if s["configuration"] == cfg and s["horizon"] == h and s["periode"] == "ensemble"}
            note += f"| {cfg} | {h} | {fr(subset['quantile_lineaire']['gain_crps_pct'])} | {fr(subset['qrf']['gain_crps_pct'])} |\n"
    note += "\n## Épisode connu de 2025\n\n| Origine | Échéance | Horizon | Modèle | Médiane (%) | Observé (%) | Borne 5 % | Borne 95 % |\n| --- | --- | --- | --- | ---: | ---: | ---: | ---: |\n"
    for r in case:
        note += f"| {r['origine']} | {r['echeance']} | {r['horizon']} | {r['modele']} | {fr(r['mediane_pct'])} | {fr(r['variation_observee_pct'])} | {fr(r['q05_pct'])} | {fr(r['q95_pct'])} |\n"
    note += (f"\n{len(result['recalculs_tronques'])} distributions ont été recalculées depuis des données tronquées à l'origine et retrouvées. "
             "Les détails et les agrégats par période sont conservés dans les fichiers associés. L'interprétation scientifique et le choix du modèle final restent à arrêter.\n")
    (OUT/"lecture_resultats.md").write_text(note, encoding="utf-8")


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        if "--benchmark" in sys.argv:
            benchmark()
        else:
            main()
