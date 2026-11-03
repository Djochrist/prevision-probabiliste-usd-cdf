# Bilan de la comparaison du 27 octobre 2026

Les calculs sont terminés. Les sorties de la comparaison appariée et du bilan brut complet ont passé deux audits indépendants des calculs de modèles, sans échec. La source BCC est conservée à l'identique. Aucun résultat n'a été publié ni déployé.

## Effectifs et correction du périmètre

Le bilan brut complet porte sur 3 584 origines. Les sensibilités appariées et la comparaison des indicateurs utilisent 3 518 origines communes aux données brutes et au scénario de masquage. Les 66 autres origines brutes ne satisfont pas les critères de disponibilité dans ce scénario. Le détail de ces périmètres est résumé dans le présent rapport.

Pour éviter de conditionner le bilan principal au masque rétrospectif, un complément distinct a conservé les 66 autres origines brutes exploitables. Son plan a été enregistré avant ses ajustements et scores, avec les mêmes paramètres et ancres. Le bilan brut complet porte donc sur **3 584 origines**. Les **3 518 origines communes** restent le périmètre des sensibilités appariées. Aucune valeur source n'a été corrigée ni inventée.

## Résultats bruts complets

Les gains ci-dessous mesurent la réduction du CRPS par rapport à la référence historique de ce nouvel essai. Une valeur négative est une dégradation. Ce ne sont pas des pourcentages de prévisions exactes.

| Horizon | Régression quantile linéaire | QRF | Couverture QRF annoncée à 90 % |
| --- | ---: | ---: | ---: |
| 5 observations | +0,15 % | +9,37 % | 90,99 % |
| 10 observations | -2,31 % | +11,21 % | 88,53 % |
| 20 observations | -4,57 % | +11,99 % | 83,65 % |

La QRF améliore aussi le Brier global de la dépréciation, de 8,01 %, 5,28 % et 3,07 %. Elle obtient les meilleurs scores moyens de CRPS, Brier et erreur absolue de la médiane parmi les trois méthodes de la configuration principale globale. Cette conclusion porte sur les 3 584 origines brutes et doit être distinguée des comparaisons appariées ci-dessous.

## La période récente et les chocs limitent la conclusion

Sur 2024-2026 (679 origines), les gains CRPS de la QRF sont +3,94 %, -1,96 % et -7,04 %. Ses scores de Brier sont moins bons que ceux de la référence aux trois horizons. La couverture à vingt observations n'est que de 80,12 %. Il n'y a donc pas de modèle dominant toutes les périodes et tous les critères.

Le 17 septembre 2025, la QRF prévoit une médiane de variation du cours de +1,01 % à vingt observations. La variation observée au 15 octobre est -23,70 % et sort de son intervalle à 90 %. Les résultats ne prouvent pas une anticipation correcte du mouvement de 2025.

## Lecture des intervalles sur les trois périodes

Lecture des agrégats existants, sans nouveau calcul de prévisions. Les valeurs de chaque case sont **couverture observée en pourcentage / largeur moyenne en points de pourcentage de variation**. La couverture annoncée est de 90 %. Une plus grande couverture obtenue au prix d'une fourchette plus large ne suffit pas à classer un modèle comme meilleur. Ces comparaisons sont descriptives, sans test de significativité.

| Période | Horizon | Historique | Régression quantile | Forêt quantile |
| --- | ---: | ---: | ---: | ---: |
| Ensemble, 3 584 origines | 5 | 87,4 / 1,69 | 87,5 / 2,46 | 91,0 / 3,59 |
| Ensemble, 3 584 origines | 10 | 86,3 / 2,59 | 85,6 / 3,19 | 88,5 / 3,86 |
| Ensemble, 3 584 origines | 20 | 84,7 / 4,46 | 80,9 / 4,70 | 83,6 / 4,27 |
| 2024–2026, 679 origines | 5 | 80,4 / 2,84 | 77,3 / 2,41 | 85,9 / 3,58 |
| 2024–2026, 679 origines | 10 | 78,6 / 3,90 | 76,1 / 3,41 | 85,4 / 4,55 |
| 2024–2026, 679 origines | 20 | 77,8 / 5,32 | 75,6 / 4,30 | 80,1 / 6,37 |
| 2026, 178 origines | 5 | 78,1 / 4,61 | 83,1 / 4,64 | 85,4 / 5,14 |
| 2026, 178 origines | 10 | 84,8 / 6,37 | 89,3 / 6,89 | 86,5 / 7,19 |
| 2026, 178 origines | 20 | 88,8 / 7,68 | 85,4 / 8,94 | 81,5 / 11,91 |

Sur l'ensemble, la forêt à cinq observations est la seule combinaison modèle/horizon dont la couverture observée atteint 90 %. Elle fournit aussi les intervalles les plus larges à cet horizon. Sur 2024–2026, toutes les couvertures sont inférieures à 90 %. La forêt couvre davantage que les deux autres modèles aux trois horizons, avec des intervalles également plus larges.

Sur 2026 seul, le compromis dépend de l'horizon. À cinq observations, la forêt a la couverture la plus élevée, mais les intervalles les plus larges. À dix, la régression quantile est plus proche des 90 % visés et fournit des intervalles plus étroits que la forêt. À vingt, la référence historique couvre davantage que la forêt avec des intervalles beaucoup plus étroits. Les origines de 2026 s'arrêtent au 22 septembre ; les dernières échéances vont au 19 octobre.

Ces résultats montrent des écarts entre incertitude annoncée et couverture observée, particulièrement sur la période récente. Ils ne démontrent pas que le niveau nominal de 90 % est optimal pour l'utilisateur, ni qu'un autre niveau réglerait ces écarts. Le choix de ce niveau reste à justifier en fonction de l'information recherchée par l'analyste et du compromis couverture/largeur. Aucune comparaison nouvelle de niveaux ni recalibration n'a été effectuée pour cette lecture.

Source numérique : `comparaisons_brutes_completes.csv`, colonnes `couverture_90` et `largeur_90`, pour les périodes `ensemble`, `2024-2026` et `2026`.

## Apport de l'activité dans la forêt quantile

Comparaison des sorties existantes de `principal` (sept indicateurs) et `cours_seul` (cinq indicateurs). Les dates évaluées et les lignes d'apprentissage sont identiques entre les deux versions. Le périmètre global apparié comprend 3 518 origines du 3 janvier 2012 au 22 septembre 2026, et non les 3 584 origines du bilan brut complet. Les sous-périodes conservent 679 origines pour 2024–2026 et 178 pour 2026. Les sorties existantes du cours seul ne couvrent pas les 66 autres origines brutes; aucune prévision complémentaire n'a été calculée pour cette lecture.

| Période | Horizon | CRPS cours seul | CRPS avec activité | Brier cours seul | Brier avec activité |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ensemble, 3 518 origines | 5 | 0,3407 | 0,3392 | 0,2028 | 0,2017 |
| Ensemble, 3 518 origines | 10 | 0,4702 | 0,4680 | 0,1961 | 0,1962 |
| Ensemble, 3 518 origines | 20 | 0,7390 | 0,7377 | 0,1837 | 0,1844 |
| 2024–2026, 679 origines | 5 | 0,7092 | 0,7082 | 0,2565 | 0,2546 |
| 2024–2026, 679 origines | 10 | 1,0062 | 1,0040 | 0,2745 | 0,2755 |
| 2024–2026, 679 origines | 20 | 1,5081 | 1,5233 | 0,2769 | 0,2823 |
| 2026, 178 origines | 5 | 0,9890 | 0,9889 | 0,2580 | 0,2589 |
| 2026, 178 origines | 10 | 1,0828 | 1,0864 | 0,2714 | 0,2815 |
| 2026, 178 origines | 20 | 1,3932 | 1,4669 | 0,2648 | 0,2781 |

Plus le score est faible, meilleur il est. L'activité réduit très légèrement le CRPS global aux trois horizons. Son apport n'est pas uniforme : sur 2024–2026, le cours seul a le meilleur CRPS à vingt observations; sur 2026, il a le meilleur CRPS à dix et vingt et le meilleur Brier aux trois horizons. À cinq observations en 2026, les CRPS sont presque identiques. Les erreurs de la médiane sont légèrement plus faibles avec activité sur l'ensemble; en 2026, elles sont plus faibles sans activité à dix et vingt. Les intervalles du cours seul sont aussi plus étroits et plus proches de la couverture nominale à ces deux horizons en 2026.

Ces résultats ne démontrent pas une amélioration générale ou robuste grâce aux indicateurs d'activité. Ils ne prouvent pas que ces données seraient inutiles pour toute méthode. Aucun test de significativité n'est effectué et aucune modification des indicateurs n'est validée par cette lecture. La lecture de la régression quantile est présentée ci-dessous.

Source : `comparaisons.csv`, configurations `principal` et `cours_seul`, modèle `qrf`.

## Apport de l'activité dans la régression quantile linéaire

Lecture des résultats existants sur les mêmes périmètres appariés et avec les mêmes lignes d'apprentissage : 3 518 origines pour l'ensemble, 679 pour 2024–2026 et 178 pour 2026. Les scores ne remplacent pas le bilan brut complet de 3 584 origines. Les valeurs les plus faibles sont les meilleures.

| Période | Horizon | CRPS cours seul | CRPS avec activité | Brier cours seul | Brier avec activité |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ensemble, 3 518 origines | 5 | 0,3477 | 0,3544 | 0,2221 | 0,2248 |
| Ensemble, 3 518 origines | 10 | 0,4738 | 0,4876 | 0,2066 | 0,2093 |
| Ensemble, 3 518 origines | 20 | 0,7268 | 0,7542 | 0,1951 | 0,1962 |
| 2024–2026, 679 origines | 5 | 0,7090 | 0,7084 | 0,2658 | 0,2657 |
| 2024–2026, 679 origines | 10 | 0,9451 | 0,9418 | 0,2822 | 0,2794 |
| 2024–2026, 679 origines | 20 | 1,3713 | 1,3810 | 0,2672 | 0,2669 |
| 2026, 178 origines | 5 | 0,9695 | 0,9640 | 0,2406 | 0,2413 |
| 2026, 178 origines | 10 | 0,9974 | 0,9904 | 0,2691 | 0,2654 |
| 2026, 178 origines | 20 | 1,2398 | 1,2719 | 0,2818 | 0,2777 |

Sur l'ensemble, la version cours seul a un CRPS et un Brier plus faibles aux trois horizons. Son erreur absolue moyenne de la médiane est aussi plus faible; ses couvertures sont plus proches de 90 %, au prix d'intervalles légèrement plus larges. Il n'y a donc pas de gain global observé de l'activité pour ces scores dans cette méthode.

Sur 2024–2026, les deux indicateurs d'activité améliorent légèrement le CRPS à cinq et dix observations et le Brier aux trois horizons. Le cours seul conserve un meilleur CRPS à vingt. Sur 2026, le CRPS est meilleur avec activité à cinq et dix, mais sans activité à vingt; le Brier est meilleur avec activité à dix et vingt, mais sans activité à cinq. Les critères peuvent donc donner des résultats différents à un même horizon.

La lecture des intervalles ne fournit pas de domination uniforme. En 2026, l'activité améliore la couverture aux trois horizons, mais à vingt la largeur augmente de 7,36 à 8,94 points de variation. À dix, les intervalles avec activité sont à la fois plus proches de la couverture nominale (89,33 % contre 88,20 %) et légèrement plus étroits (6,89 contre 6,97).

En rapprochant les deux familles, le bénéfice des indicateurs d'activité dépend du modèle, de l'horizon, de la période et du score. Les résultats de cet essai ne soutiennent pas une amélioration générale et stable. Aucun test de significativité ni modification des indicateurs n'est effectué dans cette lecture.

Source : `comparaisons.csv`, configurations `principal` et `cours_seul`, modèle `quantile_lineaire`.

## Sensibilité à la longueur de l'apprentissage

Lecture des configurations existantes `principal` (1 000 positions) et `fenetre_500`, sur les mêmes 3 518 origines globales, 679 récentes et 178 de 2026. Les indicateurs et les autres réglages sont conservés. La fenêtre reste une plage de positions; les lignes incomplètes y sont retirées selon la règle de complétude, sans remplacement par des origines plus anciennes.

La fenêtre de 1 000 donne un CRPS plus faible que celle de 500 pour chacun des trois modèles, à chaque horizon et sur chacune des trois périodes : 27 comparaisons descriptives. Ces cas se chevauchent et ne sont pas 27 expériences indépendantes. Ce constat justifie de conserver la fenêtre principale de l'essai face à la seule variante testée; il ne prouve pas que 1 000 est une longueur optimale.

Exemple complet pour la forêt, modèle retenu pour l'affichage par défaut :

| Période | Horizon | CRPS, 1 000 | CRPS, 500 | Brier, 1 000 | Brier, 500 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ensemble, 3 518 origines | 5 | 0,3392 | 0,3577 | 0,2017 | 0,2008 |
| Ensemble, 3 518 origines | 10 | 0,4680 | 0,5012 | 0,1962 | 0,1929 |
| Ensemble, 3 518 origines | 20 | 0,7377 | 0,7919 | 0,1844 | 0,1832 |
| 2024–2026, 679 origines | 5 | 0,7082 | 0,7446 | 0,2546 | 0,2563 |
| 2024–2026, 679 origines | 10 | 1,0040 | 1,0624 | 0,2755 | 0,2769 |
| 2024–2026, 679 origines | 20 | 1,5233 | 1,6366 | 0,2823 | 0,2860 |
| 2026, 178 origines | 5 | 0,9889 | 1,0844 | 0,2589 | 0,2572 |
| 2026, 178 origines | 10 | 1,0864 | 1,1464 | 0,2815 | 0,2701 |
| 2026, 178 origines | 20 | 1,4669 | 1,6063 | 0,2781 | 0,2767 |

Le Brier ne donne pas une domination générale de 1 000. Pour la forêt, 500 améliore le Brier global et celui de 2026 aux trois horizons, mais le dégrade sur 2024–2026. Pour la référence historique, 500 améliore le Brier dans les trois périodes et aux trois horizons. Pour la régression, 500 dégrade le Brier global et de 2026 aux trois horizons, avec quelques gains récents à cinq et dix. Le choix d'une fenêtre pour la distribution et celui pour la probabilité de signe peuvent donc répondre à des critères différents.

Les erreurs de la médiane de la forêt et de la régression augmentent avec 500 dans les trois périodes et aux trois horizons. Pour la forêt, ses couvertures avec 500 sont aussi plus éloignées des 90 % visés dans les neuf cas. Aucun nouveau réglage ni test de significativité n'est ajouté.

## Sensibilité aux sept cours masqués

Le scénario `sensibilite_donnees` rend indisponibles, dans une copie, les cours des 3, 4 et 5 juillet 2017 et des 2, 3, 4 et 5 juillet 2018. Le fichier source reste intact. Les mêmes origines d'évaluation sont utilisées entre versions; le masque modifie les indicateurs et cibles d'apprentissage qui dépendent des cours concernés. Il ne change pas les cibles observées conservées dans l'intersection évaluée.

| Modèle | Horizon | CRPS brut apparié | CRPS après masque | Brier brut apparié | Brier après masque |
| --- | ---: | ---: | ---: | ---: | ---: |
| Historique | 5 | 0,3828 | 0,3804 | 0,2200 | 0,2201 |
| Historique | 10 | 0,5445 | 0,5424 | 0,2086 | 0,2087 |
| Historique | 20 | 0,8662 | 0,8650 | 0,1928 | 0,1927 |
| Régression quantile | 5 | 0,3544 | 0,3425 | 0,2248 | 0,2184 |
| Régression quantile | 10 | 0,4876 | 0,4732 | 0,2093 | 0,2087 |
| Régression quantile | 20 | 0,7542 | 0,7382 | 0,1962 | 0,1988 |
| Forêt quantile | 5 | 0,3392 | 0,3252 | 0,2017 | 0,2019 |
| Forêt quantile | 10 | 0,4680 | 0,4573 | 0,1962 | 0,1963 |
| Forêt quantile | 20 | 0,7377 | 0,7244 | 0,1844 | 0,1847 |

Ce tableau porte sur les 3 518 origines communes. Les CRPS globaux diminuent dans les neuf cas, sans amélioration uniforme du Brier ni de la couverture. Les largeurs de la forêt se réduisent fortement, par exemple de 3,49 à 1,63 points à cinq observations. Sa couverture passe de 91,61 % à 91,10 % à cinq, de 89,34 % à 88,40 % à dix et de 84,31 % à 82,58 % à vingt. Une amélioration du CRPS ne signifie donc pas que tous les aspects de l'incertitude sont améliorés.

Pour 2024–2026 et pour 2026 seul, les agrégats CRPS, Brier, erreur de la médiane, couverture et largeur du scénario masqué sont exactement ceux de la configuration principale. Dans cette expérience à fenêtre glissante, les séquences de 2017/2018 ne sont plus dans les fenêtres correspondantes. L'effet global du masque ne doit donc pas être attribué aux prévisions de ces périodes récentes.

Le masque a été défini après inspection des séquences. Il mesure une sensibilité, ne prouve pas que les cours sont erronés et ne constitue pas une règle de nettoyage disponible en temps réel. Il ne justifie pas de remplacer les valeurs sources ou de présenter les meilleurs scores masqués comme bilan principal.

Source des deux sensibilités : `comparaisons.csv`, configurations `principal`, `fenetre_500` et `sensibilite_donnees`. Les variantes ont été examinées séparément; leurs croisements n'ont pas été étudiés.

## Synthèse scientifique de clôture

La lecture des résultats existants du premier point du plan est achevée : comparaison des modèles et des périodes, incertitude, apport de l'activité, fenêtre et masquage. Cette clôture n'ajoute pas de modèle ni de simulation et ne transforme pas l'étude exploratoire en validation opérationnelle.

1. Le bilan principal demeure celui des données brutes, des sept indicateurs et de la fenêtre initiale de 1 000 positions : 3 584 origines évaluées. La forêt réduit le CRPS moyen face à la référence de 9,37 %, 11,21 % et 11,99 %. Les comparaisons de sensibilité utilisent leurs 3 518 dates communes et ne remplacent pas ce bilan.
2. La supériorité moyenne de la forêt ne se maintient pas sur toutes les périodes et tous les critères. Les trois modèles restent dans la comparaison. La forêt est retenue par l'auteur comme affichage par défaut de la future plateforme, avec consultation des deux autres modèles.
3. Le bénéfice des indicateurs d'activité est faible ou variable selon le modèle, l'horizon, la période et le score. Une amélioration générale et stable n'est pas établie; aucune suppression d'indicateur n'a été décidée.
4. La variante 500 ne bat pas la fenêtre 1 000 au CRPS dans les comparaisons examinées. Des gains au Brier existent néanmoins. La longueur 1 000 reste un réglage de l'essai, sans démonstration d'optimalité.
5. Le masquage modifie les résultats globaux et la largeur des intervalles, sans améliorer uniformément les critères. La source reste intacte et le masque reste une sensibilité rétrospective.
6. Le niveau nominal de 90 % est un choix initial de présentation et d'évaluation, pas une preuve de fiabilité. Les couvertures insuffisantes, particulièrement sur la période récente, doivent figurer dans les conclusions.
7. Les données et résultats ont déjà été examinés, les erreurs se chevauchent et aucun test de significativité n'a été fait. Les dates réelles de publication sont inconnues. Ni une prévision effectivement disponible en temps réel, ni une causalité de B-Match, ni un seuil opérationnel d'alerte ne sont démontrés. Les simulations ajoutées sans validation restent hors du périmètre retenu.

Le volet scientifique peut désormais alimenter la rédaction, après alignement des questions, hypothèses et objectifs. Le prochain point du plan est l'inventaire factuel du code et du site de la plateforme, sans lui attribuer des fonctions non vérifiées.

## Sensibilités et traçabilité

Sur les 3 518 origines communes, le gain CRPS global de la QRF reste positif avec le masquage, une fenêtre de 500 positions et les indicateurs du cours seuls. L'apport des données d'activité n'est cependant pas uniformément favorable selon le modèle, la période et le critère. Ces vérifications ne remplacent pas un test final indépendant ni une calibration satisfaisante.

Les deux audits vérifient les empreintes, dates, cibles, probabilités, intervalles et agrégats. Le premier couvre 126 648 lignes et 36 groupes ; le second couvre les 32 256 prévisions principales brutes, dont 31 662 lignes conservées à l'identique et 594 lignes complémentaires disjointes. Douze recalculs sur une source tronquée à l'origine sont enregistrés par le programme. Les audits n'ont réentraîné aucun modèle.

Les 200 scénarios ne sont pas sauvegardés dans les checkpoints ; les résumés, probabilités et scores le sont. Le CRPS individuel est vérifié par la définition et les contrôles internes ; l'audit externe contrôle sa positivité et ses agrégats. Recalculer un autre quantile ou un autre score nécessite de rejouer les modèles. Cette précision rectifie la formulation trop large « distributions sauvegardées » du protocole initial, sans modifier ses paramètres ni ses résultats.

Les réglages ont été fixés avant les scores, sans optimisation sur ceux-ci. Les données ont déjà été explorées et les dates de première publication sont inconnues. Aucun test de significativité des gains ni intervalle de confiance de ces gains n'est calculé. Les prévisions se chevauchent. Ces résultats constituent une comparaison exploratoire rétrospective.

## Fichiers à utiliser

- Protocole enregistré : `protocole_avant_scores.md`.
- Paramètres enregistrés : `parametres_avant_scores.json`.
- Scripts et environnement : voir `README.md` et `requirements.txt`.
