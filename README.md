# Prévision probabiliste du cours USD/CDF

Ce dépôt rassemble les programmes et le protocole de la comparaison rétrospective exploratoire décrite dans le mémoire. Il permet de reproduire les calculs à partir de l’export BCC exact indiqué ci-dessous. Les résultats ne constituent pas une validation prospective et ne démontrent pas qu’un modèle sera supérieur à l’avenir.

## Contenu

- `scripts/preparer_indicateurs_bcc.py` : contrôle de la source et préparation des indicateurs.
- `scripts/comparer_modeles_probabilistes_bcc.py` : comparaison des trois méthodes et production des sorties détaillées.
- `analyses/modeles_probabilistes_2026-10-27/tests_statistiques_retro_2026-11-02.py` : analyse complémentaire des différences entre la forêt quantile et la référence historique.
- `protocole_avant_scores.md` et `parametres_avant_scores.json` : protocole et réglages enregistrés.
- `bilan_comparaison.md` et `tests_statistiques_retro_2026-11-02.md` : synthèses des résultats existants.

## Données

L’analyse initiale utilise l’export BCC du 19 octobre 2026. L’archive CSV n’est pas incluse dans ce dépôt. Consulter `sources_bcc/README.md` pour l’obtenir et vérifier son empreinte SHA-256 avant l’exécution. Un export plus récent est une autre version des données et ne reproduit pas exactement cette expérience.

## Reproduction

Python 3.12.14 est l’environnement utilisé. Dans un environnement virtuel, installer les versions de `requirements.txt`, placer le CSV indiqué dans `sources_bcc/`, puis lancer depuis la racine du dépôt :

```bash
python -m pip install -r requirements.txt
python scripts/preparer_indicateurs_bcc.py
python scripts/comparer_modeles_probabilistes_bcc.py
python analyses/modeles_probabilistes_2026-10-27/tests_statistiques_retro_2026-11-02.py
```

Le calcul complet peut être long. Il écrit ses résultats intermédiaires et détaillés dans `analyses/`; ces sorties générées ne sont pas suivies par Git. Le dernier programme exige les prévisions brutes complètes produites par le programme de comparaison.

## Résultats et limites

Le bilan porte sur 3 584 origines brutes; les analyses de sensibilité appariées portent sur 3 518 origines. La forêt quantile obtient des scores globaux plus favorables que la référence historique sur certains critères, mais aucun modèle ne domine toutes les périodes et dimensions. L’analyse statistique complémentaire a été menée après examen des résultats; elle ne remplace pas une validation sur des données futures restées inconnues. Voir les deux rapports fournis pour les résultats et réserves détaillés.

## Citation

Les métadonnées de citation sont dans `CITATION.cff`. Après publication, compléter la version, la date et le DOI de l’archive si elle est déposée sur Zenodo.

## Licences

Tous les fichiers de code Python (`.py`) sont sous licence MIT (`LICENSE-MIT.txt`). Le README, le protocole, les paramètres et les rapports de recherche sont sous licence CC BY 4.0 (`LICENSE-CC-BY-4.0.txt` ; texte intégral dans `CC-BY-4.0-LEGALCODE.txt`). Les données BCC ne sont pas incluses et ne sont couvertes par aucune de ces licences.

## Source des données

Banque Centrale du Congo, « Marché des changes », https://www.bcc.cd/statistiques/secteur-exterieur/marche-des-changes.
