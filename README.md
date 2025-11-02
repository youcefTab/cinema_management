# Cinema — README

> **Important :** lire d'abord la section *Choix importants* pour comprendre certaines décisions de conception.

---

## Choix importants
- **`Auteur` → `ProductionCompany`**
  TMDb n'expose pas un modèle "auteur" qui correspond directement au cahier des charges. Pour rester simple et fidèle aux données TMDb nous avons remplacé l'entité *Auteur* par **`ProductionCompany`** (champs inspirés de `production_companies`).
  Cela simplifie l'import depuis TMDb et conserve la logique métier (films ↔ production companies).
- **Simplicité & bonnes pratiques**
  Nous utilisons Django + DRF + SimpleJWT, serializers imbriqués (pas de `SerializerMethodField`), tests & typing tout au long (TDD), Make pour les raccourci et des pre-commit pour vérifié la qualité du linting...etc. On garde le code simple et maintenable.

---

## Variables d'environnement
Pour simplifier, le `.env` n'est pas en .gitignore

---

## Architecture containers (local/dev)
L'application est prévue pour tourner en containers Docker (exemples) :
- `cinema-backend` — application Django / API (backend).
- `cinema-db` — PostgreSQL.
- `cinema-pgadmin` — PGAdmin.

---
## Lancer le projet (développement)
1. Build & Start:
```docker-compose up --build```

2. Create Django super user for admin:
```make superuser```

3. Populate DB:
```make import-tmdb pages=3```

4. Access To Swagger:
```http://localhost:8000/swagger/``` OR redoc: ```http://localhost:8000/redoc/```.
Pour Swagger vous devez créer un premier compte avec `/register` ou bien utilisé le compte superadmin dans la section authorize, ce qui va vous permettre d'utiliser le reste des endpoints.

5. Raccourcis: dans le fichier `Makefile` vous trouverez une liste de raccourci pour le développement, dont accèder au shell du container cinema-backend, ou lancer les tests pour les apps du projet.
