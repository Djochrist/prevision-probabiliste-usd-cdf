# Protocole du premier essai des modèles probabilistes retenus

Date : 27 octobre 2026. Statut : comparaison rétrospective exploratoire. Les familles de modèles et les sept indicateurs sont retenus à la suite des validations dans la conversation. Les paramètres ci-dessous sont des réglages de départ, enregistrés avant le calcul des scores. Aucun réglage n'est sélectionné sur ces scores. Aucun résultat n'est garanti et aucun modèle final n'est désigné d'avance.

## Source et cible

Source : copie intacte de l'export BCC, du 3 janvier 2006 au 19 octobre 2026. Empreinte et versions des bibliothèques enregistrées dans parametres_avant_scores.json. Les dates restent sur leur grille originale. Aucune imputation. Les sept indicateurs et leurs règles d'indisponibilité sont ceux décrits dans analyses/indicateurs_2026-10-27/note_indicateurs.md.

La cible évaluée est la variation simple en pourcentage du cours indicatif en CDF pour 1 USD aux horizons 5, 10 et 20 observations. Les modèles internes utilisent 100 × log(S(t+h)/S(t)). Leurs distributions sont ensuite reconverties par 100 × (exp(L/100)-1), ce qui respecte la positivité des cours. Les probabilités et les scores portent sur la variation simple approuvée. Le signe positif signifie une dépréciation du CDF à l'échéance.

## Chronologie effective

Les ajustements ont lieu à la première date observée de chaque mois, à partir de janvier 2012. Leur calendrier ne dépend pas de l'existence des valeurs futures qui serviront à calculer les scores. Les coefficients et les arbres restent fixes dans le mois. Les indicateurs de la date de prévision sont actualisés à chaque observation.

Le calcul est réparti entre au plus quatre processus indépendants par mois, avec un seul thread par forêt et par solveur HiGHS. À l'intérieur d'un mois, un ajustement est réutilisé seulement si les indices, les indicateurs et les cibles d'apprentissage sont strictement identiques, avec tous les paramètres fixés identiques. Il s'agit d'optimisations d'exécution. Les distributions sont sauvegardées par mois avec l'empreinte de configuration, ce qui permet une reprise sans changer les règles de l'expérience.

À une date d'ajustement a, le modèle d'horizon h utilise les 1 000 positions d'origine allant de a-h-999 à a-h. Ainsi, chaque cible d'apprentissage est arrivée à échéance au plus en a. Les lignes incomplètes sont écartées dans cette fenêtre, sans prendre des lignes plus anciennes en remplacement. Un minimum de 80 % de lignes exploitables est exigé. Le centrage et la réduction de la régression quantile sont estimés uniquement sur ces lignes. La forêt reçoit les mêmes valeurs explicatives, sans normalisation supplémentaire.

La période de notation va de janvier 2012 à la dernière origine ayant une échéance de 20 observations dans le fichier. Les mêmes origines sont notées pour tous les modèles, horizons et configurations. Cette intersection est construite après identification des valeurs observées nécessaires aux scores. Elle ne sert pas à choisir les dates d'ajustement ni les paramètres. Les dates manquantes restent à leur position originale.

La comparaison porte sur 3 518 origines communes aux données brutes et au scénario de masquage, parmi 3 584 origines exploitables en brut. Les 66 autres dates brutes ne satisfont pas les critères de disponibilité dans le scénario de masquage. Les résultats appariés ne constituent donc pas une évaluation de toutes les dates brutes.

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

Le protocole et ses paramètres sont conservés avant les résultats. Les versions des bibliothèques nécessaires à l’exécution sont indiquées dans `requirements.txt`.

Références techniques : https://zillow.github.io/quantile-forest/generated/quantile_forest.RandomForestQuantileRegressor.html ; https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.QuantileRegressor.html
