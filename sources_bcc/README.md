# Source BCC requise

Fichier attendu : `marche-des-changes-quotidien_2026-10-19.csv`.

Il s’agit de l’export BCC du marché des changes utilisé dans la comparaison rétrospective. Télécharger ou récupérer cette archive auprès de la Banque Centrale du Congo (https://www.bcc.cd/statistiques/secteur-exterieur/marche-des-changes), puis enregistrer le fichier sous le nom indiqué dans ce dossier.

Avant tout calcul, vérifier que son empreinte SHA-256 est :

```text
346d6cea9383b75ea642b2b16ab341cc6538c5b00a164325c035f19b2791882d
```

Le script de préparation vérifie aussi cette empreinte. Un fichier différent ne reproduit pas l’expérience décrite; ne pas remplacer silencieusement l’archive par un export courant.
