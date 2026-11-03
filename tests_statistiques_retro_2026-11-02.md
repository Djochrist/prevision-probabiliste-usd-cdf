# Tests statistiques rétrospectifs des différences de CRPS

Analyse post hoc appariée, datée du 2 novembre 2026. Une différence négative (CRPS QRF − CRPS historique) favorise la forêt quantile. Le test principal est unilatéral, avec variance HAC de Newey–West sur 60 positions de la série; les trois valeurs p sont corrigées par Holm.

Les longueurs HAC de h−1 et 2h et les blocs circulaires de 5, 10, 20, 40 et 60 positions sont des sensibilités. Les positions manquantes restent des lacunes sur la grille d’origine. Le bootstrap utilise 3 000 réplications et la graine 20261102.

| Horizon | Paires | CRPS historique | CRPS QRF | Gain relatif | Différence QRF−réf. | p HAC 60 (brute) | p HAC 60 (Holm) | IC bootstrap 95 %, bloc 60 | p bootstrap bloc 60 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 3584 | 0.61041 | 0.55321 | 9.37% | -0.05719 | 0.0005791 | 0.001737 | [-0.09350, -0.02622] | 0.001999 |
| 10 | 3584 | 0.78034 | 0.69286 | 11.21% | -0.08748 | 0.0005791 | 0.001737 | [-0.14563, -0.03842] | 0.001666 |
| 20 | 3584 | 1.09356 | 0.96243 | 11.99% | -0.13113 | 0.004502 | 0.004502 | [-0.23084, -0.03795] | 0.008664 |

## Interprétation et limites

Ces tests quantifient l’incertitude liée à la dépendance temporelle sur les prévisions déjà calculées; ils ne transforment pas cette comparaison rétrospective en validation indépendante. Les valeurs p sont asymptotiques. Les conclusions doivent tenir compte de la correction de Holm et de la stabilité aux longueurs HAC/blocs. Aucun test de significativité des autres indicateurs n’est ajouté.

Données et protocole antérieurs conservés sans modification. Script reproductible : `tests_statistiques_retro_2026-11-02.py`.
