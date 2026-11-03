"""Indicateurs candidats, sans imputation ni modification du CSV source."""
import csv
import hashlib
import json
import platform
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "sources_bcc" / "marche-des-changes-quotidien_2026-10-19.csv"
OUT = ROOT / "analyses" / "indicateurs_2026-10-27"
EXPECTED_HASH = "346d6cea9383b75ea642b2b16ab341cc6538c5b00a164325c035f19b2791882d"
MASK = ("2017-07-03", "2017-07-04", "2017-07-05", "2018-07-02",
        "2018-07-03", "2018-07-04", "2018-07-05")
HORIZONS = (5, 10, 20)
FEATURES = ("variation_passee_1_pct", "variation_passee_5_pct", "variation_passee_10_pct",
            "variation_passee_20_pct", "ecart_type_variations_20_points_pct",
            "log1p_volume_musd_decale_1", "ecart_relatif_achats_ventes_pct_decale_1")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def build(prices, volume, purchases, sales):
    n = len(prices)
    x = np.full((n, len(FEATURES)), np.nan)
    for col, lag in enumerate((1, 5, 10, 20)):
        x[lag:, col] = 100 * (prices[lag:] / prices[:-lag] - 1)
    for t in range(20, n):
        r = x[t-19:t+1, 0]
        if np.all(np.isfinite(r)):
            x[t, 4] = r.std(ddof=1)
    finite_volume = np.isfinite(volume[:-1]) & (volume[:-1] >= 0)
    x[1:, 5][finite_volume] = np.log1p(volume[:-1][finite_volume])
    denominator = purchases[:-1] + sales[:-1]
    valid_ratio = np.isfinite(purchases[:-1]) & np.isfinite(sales[:-1]) & (denominator > 0)
    x[1:, 6][valid_ratio] = 100 * (purchases[:-1][valid_ratio] - sales[:-1][valid_ratio]) / denominator[valid_ratio]
    assert np.all(abs(x[np.isfinite(x[:, 6]), 6]) <= 100 + 1e-10)
    return x


def targets(prices):
    out = {}
    for h in HORIZONS:
        y = np.full(len(prices), np.nan)
        y[:-h] = 100 * (prices[h:] / prices[:-h] - 1)
        out[h] = y
    return out


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: "" if isinstance(v, float) and not np.isfinite(v) else v for k, v in row.items()})


def main():
    raw = SOURCE.read_bytes()
    assert digest(raw) == EXPECTED_HASH
    rows = list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
    rows = [r for r in rows if "2006-01-03" <= r["Date"] <= "2026-10-19"]
    dates = [r["Date"] for r in rows]
    assert len(dates) == 5273 and dates == sorted(set(dates))
    columns = list(rows[0])[1:5]
    source_values = np.array([[float(r[c]) if r[c] else np.nan for c in columns] for r in rows])
    prices, volume, purchases, sales = source_values.T
    assert np.all(prices[np.isfinite(prices)] > 0)
    assert not np.any(source_values[:, 1:][np.isfinite(source_values[:, 1:])] < 0)
    x = build(prices, volume, purchases, sales)
    y = targets(prices)
    masked_prices = prices.copy()
    for d in MASK:
        masked_prices[dates.index(d)] = np.nan
    xs = build(masked_prices, volume, purchases, sales)
    ys = targets(masked_prices)
    # Verifications d'information: retirer ou alterer le futur ne change aucun indicateur en t.
    for d in ("2013-06-03", "2018-07-06", "2025-09-03", "2025-10-01"):
        t = dates.index(d)
        prefix = build(prices[:t+1], volume[:t+1], purchases[:t+1], sales[:t+1])
        changed = source_values.copy()
        changed[t+1:] *= 1.6
        changed_x = build(*changed.T)
        assert np.allclose(x[t], prefix[t], equal_nan=True, atol=1e-12)
        assert np.allclose(x[t], changed_x[t], equal_nan=True, atol=1e-12)
        # Modifier l'activite de la date t ne doit pas affecter les indicateurs decales.
        changed_now = source_values.copy()
        changed_now[t, 1:] *= 3.1
        assert np.allclose(x[t, 5:], build(*changed_now.T)[t, 5:], equal_nan=True, atol=1e-12)
    # Verifier les fenetres avec une formule scalaire independante a une date complete.
    t = dates.index("2025-09-03")
    manual_returns = [100 * (float(prices[j])/float(prices[j-1]) - 1) for j in range(t-19, t+1)]
    mean = sum(manual_returns) / 20
    manual_sd = (sum((r-mean)**2 for r in manual_returns) / 19)**.5
    assert abs(manual_sd - x[t, 4]) < 1e-12
    assert x[t, 5] == np.log1p(volume[t-1])
    zero_denom_origins = np.where(np.isfinite(purchases[:-1] + sales[:-1]) & ((purchases[:-1] + sales[:-1]) == 0))[0] + 1
    assert np.all(np.isnan(x[zero_denom_origins, 6]))
    zero_volume_origins = np.where(np.isfinite(volume[:-1]) & (volume[:-1] == 0))[0] + 1
    assert np.all(x[zero_volume_origins, 5] == 0)
    OUT.mkdir(parents=True, exist_ok=True)
    for label, features, outcomes in (("bruts", x, y), ("sensibilite", xs, ys)):
        feature_rows = []
        target_rows = []
        for t, d in enumerate(dates):
            record = {"date_origine": d, "date_activite_utilisee": dates[t-1] if t else ""}
            record.update(zip(FEATURES, map(float, features[t])))
            feature_rows.append(record)
            tr = {"date_origine": d}
            for h in HORIZONS:
                tr[f"echeance_{h}"] = dates[t+h] if t+h < len(dates) else ""
                tr[f"variation_future_{h}_pct"] = float(outcomes[h][t])
            target_rows.append(tr)
        write_csv(OUT / f"indicateurs_{label}.csv", list(feature_rows[0]), feature_rows)
        write_csv(OUT / f"cibles_{label}.csv", list(target_rows[0]), target_rows)
    candidates = np.array([d >= "2012-01-01" and t+max(HORIZONS) < len(dates) for t, d in enumerate(dates)])
    targets_valid = np.all(np.column_stack([np.isfinite(y[h]) for h in HORIZONS]), axis=1)
    masked_targets_valid = np.all(np.column_stack([np.isfinite(ys[h]) for h in HORIZONS]), axis=1)
    price_only = candidates & targets_valid & np.all(np.isfinite(x[:, :5]), axis=1)
    with_activity = candidates & targets_valid & np.all(np.isfinite(x), axis=1)
    masked_with_activity = candidates & masked_targets_valid & np.all(np.isfinite(xs), axis=1)
    common = with_activity & masked_with_activity
    exclusion_rows = []
    for t in np.where(candidates & ~with_activity)[0]:
        missing_x = [name for j, name in enumerate(FEATURES) if not np.isfinite(x[t, j])]
        missing_y = [str(h) for h in HORIZONS if not np.isfinite(y[h][t])]
        exclusion_rows.append({"date_origine": dates[t], "indicateurs_indisponibles": ";".join(missing_x),
                               "horizons_cible_indisponible": ";".join(missing_y)})
    write_csv(OUT / "origines_incompletes_brutes.csv",
              ["date_origine", "indicateurs_indisponibles", "horizons_cible_indisponible"], exclusion_rows)
    valid_activity = np.all(np.isfinite(source_values[:, 1:]), axis=1)
    discrepancy = volume[valid_activity] - purchases[valid_activity] - sales[valid_activity]
    descriptions = [
        {"nom": FEATURES[0], "definition": "100*(S_t/S_(t-1)-1)", "information_max": "t", "role_propose": "dernier mouvement observe"},
        {"nom": FEATURES[1], "definition": "100*(S_t/S_(t-5)-1)", "information_max": "t", "role_propose": "mouvement cumule recent"},
        {"nom": FEATURES[2], "definition": "100*(S_t/S_(t-10)-1)", "information_max": "t", "role_propose": "mouvement cumule recent"},
        {"nom": FEATURES[3], "definition": "100*(S_t/S_(t-20)-1)", "information_max": "t", "role_propose": "mouvement cumule recent"},
        {"nom": FEATURES[4], "definition": "ecart-type echantillonnal des 20 variations entre observations consecutives, denominateur 19; les 20 variations sont requises", "information_max": "t", "role_propose": "variabilite recente"},
        {"nom": FEATURES[5], "definition": "log(1+volume_total_(t-1)) ; volume exprime en millions USD", "information_max": "t-1", "role_propose": "niveau d'activite rapporte; log pour comprimer l'echelle"},
        {"nom": FEATURES[6], "definition": "100*(achats_(t-1)-ventes_(t-1))/(achats_(t-1)+ventes_(t-1)); indisponible si denominateur nul", "information_max": "t-1", "role_propose": "ecart relatif entre les montants rapportes; aucune assimilation automatique a la demande ou l'offre globales"},
    ]
    summary = {"statut": "preparation de sept indicateurs retenus par l'utilisateur, non optimises; ce script n'ajuste aucun modele",
               "date_travail": "2026-10-27", "source": str(SOURCE), "sha256_source": EXPECTED_HASH,
               "sha256_programme": digest(Path(__file__).read_bytes()),
               "python": platform.python_version(), "numpy": np.__version__,
               "dates_source": len(dates), "cours_disponibles": int(np.isfinite(prices).sum()),
               "disponibilite_par_indicateur": {f: int(np.isfinite(x[:, j]).sum()) for j, f in enumerate(FEATURES)},
               "dates_sept_indicateurs_disponibles": int(np.all(np.isfinite(x), axis=1).sum()),
               "origine_candidats_2012_2026": int(candidates.sum()),
               "origines_cours_seul_cinq_indicateurs_et_trois_cibles": int(price_only.sum()),
               "origines_sept_indicateurs_et_trois_cibles_brutes": int(with_activity.sum()),
               "origines_sept_indicateurs_et_trois_cibles_sensibilite": int(masked_with_activity.sum()),
               "origines_communes_brut_sensibilite": int(common.sum()),
               "date_premiere_origine_complete": dates[np.where(with_activity)[0][0]],
               "date_derniere_origine_complete": dates[np.where(with_activity)[0][-1]],
               "origines_ratio_indisponible_denominateur_nul": len(zero_denom_origins),
               "volume_egal_zero_conserve_dans_log1p": len(zero_volume_origins),
               "reconciliation_volume_n": int(valid_activity.sum()),
               "reconciliation_ecart_absolu_max_musd": float(np.max(abs(discrepancy))),
               "reconciliation_n_ecart_inferieur_0001_musd": int(np.sum(abs(discrepancy) <= .001 + 1e-9)),
               "definition_indicateurs": descriptions,
               "verifications": ["source inchangee", "ordre et nombre des dates conserves", "aucune imputation",
                    "indicateurs a quatre dates inchanges apres retrait ou alteration de toutes les valeurs futures",
                    "activite courante sans effet sur les indicateurs d'activite decales a quatre dates",
                    "ecart-type reconcilie avec calcul scalaire independant", "denominateurs nuls laisses indisponibles",
                    "volume zero conserve comme zero dans log1p", "cibles futures sauvegardees separement des entrees"]}
    assert digest(SOURCE.read_bytes()) == EXPECTED_HASH
    (OUT / "controle_indicateurs.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_note(summary)
    print(json.dumps({k: v for k, v in summary.items() if k not in ("definition_indicateurs", "verifications")}, ensure_ascii=False), flush=True)


def write_note(s):
    note = f"""# Préparation des sept indicateurs retenus

Travail du 27 octobre 2026. Les familles de modèles retenues pour la comparaison sont la référence empirique historique, la régression quantile linéaire et QRF. Le message « alors avançons », après leur recommandation, valide ce périmètre. Après une explication simple de leur rôle et de leur calcul, le dernier message « allons y » valide l'utilisation des sept indicateurs ci-dessous pour cette comparaison. Aucun gagnant n'est désigné. Cette préparation contrôle les indicateurs ; elle n'ajuste aucun des nouveaux modèles et n'établit pas leur efficacité prédictive.

## Informations retenues pour les modèles

| Groupe | Indicateurs | Justification |
| --- | --- | --- |
| Mouvements récents du cours | Variations passées sur 1, 5, 10 et 20 observations | Décrire le dernier mouvement et les mouvements cumulés sur plusieurs longueurs d'historique |
| Variabilité récente | Écart-type des 20 dernières variations entre observations consécutives | Décrire si les variations récentes sont plus ou moins dispersées |
| Activité rapportée | Logarithme de 1 + volume total, décalé d'une observation | Décrire le niveau d'activité sur une échelle comprimée, en conservant les volumes nuls |
| Achats et ventes rapportés | Écart relatif (achats - ventes)/(achats + ventes), exprimé en pourcentage et décalé d'une observation | Utiliser ces deux montants sans présenter le volume et ses composantes comme trois informations indépendantes |

Les horizons 5, 10 et 20 concernent des variations futures à prévoir. Les fenêtres des indicateurs ci-dessus concernent des observations passées. Leur égalité numérique est un choix de départ pratique et non une saisonnalité constatée, une périodicité prouvée ou un optimum estimé. La fenêtre de 20 pour l'écart-type est également un choix de départ. Aucune longueur n'est optimisée sur les résultats d'évaluation. Ces définitions sont retenues pour le premier essai après validation des sept indicateurs ; leur optimalité et les paramètres définitifs des modèles restent à établir.

Les quatre séries sources déjà sélectionnées sont donc conservées. Le cours et les montants restent intacts. Les sept colonnes retenues sont des calculs dérivés sur une copie de travail. L'écart achats-ventes décrit les opérations rapportées dans la source. Il n'est pas assimilé automatiquement à l'offre ou à la demande globales de dollars.

## Chronologie et disponibilité

Les indicateurs du cours en t utilisent des cours datés au plus t. Cette convention suppose une prévision après disponibilité du cours de t. Les indicateurs d'activité utilisent les montants datés t-1. Ce décalage impose l'usage d'une observation plus ancienne. Les heures et dates réelles de première publication et les révisions de la BCC ne sont pas connues : ce décalage ne prouve pas que les valeurs étaient effectivement accessibles en temps réel.

Pour une variation cumulée passée, les cours des deux extrémités suffisent. L'écart-type exige les vingt variations successives, donc les vingt et un cours nécessaires. Les valeurs manquantes restent indisponibles et toutes les dates restent à leur place. Le ratio achats-ventes reste indisponible lorsque sa somme au dénominateur est nulle. Un volume total nul donne en revanche log(1+0)=0, valeur connue.

## Résultats de préparation

- {s['dates_source']} dates de source, dont {s['cours_disponibles']} cours disponibles.
- {s['dates_sept_indicateurs_disponibles']} dates disposent des sept indicateurs sur l'ensemble de la période.
- Sur les {s['origine_candidats_2012_2026']} origines candidates du premier essai, {s['origines_cours_seul_cinq_indicateurs_et_trois_cibles']} disposent des cinq indicateurs de cours et des trois cibles observées aux horizons 5, 10 et 20.
- {s['origines_sept_indicateurs_et_trois_cibles_brutes']} origines disposent des sept indicateurs et des trois cibles sur les données brutes, de {s['date_premiere_origine_complete']} à {s['date_derniere_origine_complete']}.
- {s['origines_sept_indicateurs_et_trois_cibles_sensibilite']} origines sont exploitables selon les mêmes critères dans la copie masquant les sept cours signalés. L'intersection brut/sensibilité comprend {s['origines_communes_brut_sensibilite']} origines.
- {s['origines_ratio_indisponible_denominateur_nul']} origines ont un ratio d'activité indisponible à cause d'un dénominateur nul. Ces absences concernent l'indicateur dérivé et ne sont pas des cours ou des volumes sources manquants.

Les 3666 origines du premier essai des horizons concernent les méthodes historique, tendance et régression ridge, avec leurs propres variables et conditions de disponibilité. Elles ne constituent pas l'étape préalable du filtrage actuel. Dans cette préparation, les {s['origines_cours_seul_cinq_indicateurs_et_trois_cibles']} origines correspondent aux cinq indicateurs de cours et aux trois cibles disponibles sur les données brutes ; les {s['origines_sept_indicateurs_et_trois_cibles_brutes']} ajoutent les deux indicateurs d'activité ; les {s['origines_communes_brut_sensibilite']} forment l'intersection des données brutes et du scénario masquant les sept cours. Ces quatre effectifs décrivent donc des conditions différentes. L'écart entre 3666 et {s['origines_communes_brut_sensibilite']} ne peut pas être attribué entièrement aux indicateurs d'activité.

Ces nombres décrivent uniquement la disponibilité technique des indicateurs et des cibles. Ils ne fixent pas les effectifs d'apprentissage ou d'évaluation des nouveaux modèles, qui dépendent du protocole. Les conditions de maturité des cibles dans l'apprentissage restent distinctes du fait de posséder, rétrospectivement, leur valeur observée.

## Contrôles et fichiers conservés

Le retrait ou l'altération de toutes les valeurs futures laisse les sept indicateurs inchangés à quatre dates de contrôle. La modification des montants de t n'affecte pas les indicateurs d'activité de t, qui utilisent t-1. Le calcul de l'écart-type est réconcilié avec une formule scalaire indépendante. Les zéros, dénominateurs nuls et empreintes de la source sont contrôlés.

Les fichiers indicateurs_bruts.csv et indicateurs_sensibilite.csv contiennent les entrées retenues et la date d'activité utilisée. Les fichiers cibles_bruts.csv et cibles_sensibilite.csv contiennent séparément les cibles, avec leurs dates d'échéance. Cette séparation réduit le risque de confondre les colonnes à prévoir avec les informations d'entrée. Les origines incomplètes et leurs motifs sont conservés dans origines_incompletes_brutes.csv. Le dictionnaire détaillé, les empreintes et les résultats numériques figurent dans controle_indicateurs.json.

La comparaison proposée entre cours seul et cours avec activité nécessite les mêmes origines de départ pour mesurer l'apport de l'activité. Les modèles conditionnels doivent également recevoir les mêmes indicateurs dans une comparaison de familles. L'efficacité prédictive de ces indicateurs n'est pas établie par leur disponibilité.
"""
    (OUT / "note_indicateurs.md").write_text(note, encoding="utf-8")


if __name__ == "__main__":
    main()
