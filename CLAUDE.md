# Projet Ligue du Kadiogo de Kung-Fu Wushu

Application web de gestion de la Ligue du Kadiogo de Kung-Fu Wushu (Burkina Faso) :
clubs et affiliations, licenciés (pratiquants), examens de grades, évaluations par jury,
résultats, paiements, actualités.

## Consignes de travail
- Toujours répondre en **français**, avec des explications simples (l'utilisateur débute avec Claude Code).
- Messages de commit en français, courts et descriptifs (voir `git log`).
- En début de séance : lire `SUIVI.md` pour savoir où on en est.
- En fin de séance (ou quand l'utilisateur le demande) : mettre à jour `SUIVI.md`, puis commit + push.

## Technique
- **Django 6** (Python), serveur ASGI via **Daphne** + **Channels** (temps réel pour les évaluations, Redis en production).
- Configuration par variables d'environnement dans `.env` (via `python-decouple`) — ce fichier n'est pas dans git.
- Base de données : SQLite en local (`db.sqlite3`), PostgreSQL en production.
- PDF générés avec **WeasyPrint** (attestations, impressions).
- Langue `fr-fr`, fuseau `Africa/Ouagadougou`.
- Production : domaine `kadiogokungfu.teeritech.bf`.

## Organisation
- `config/` : réglages (`settings.py`), URLs principales, emails.
- `apps/` : une application Django par domaine :
  `accounts` (utilisateurs, rôles, permissions), `ligues`, `clubs`, `practitioners` (licenciés),
  `exams`, `evaluations` (notation jury, WebSocket), `results`, `payments`, `communication` (actualités).
- `templates/` : un dossier par app ; `base.html` ; `includes/` (navbar, footer, barres latérales club / jury / ligue).
- `static/` : CSS, JS, images, polices.
- Rôles utilisateurs définis dans `apps/accounts/models.py` (SUPER_ADMIN, GEST_LIGUE, GEST_TECHNIQUE, …) ;
  commande `python manage.py seed_roles` pour les créer.

## Charte graphique
- Couleur principale **rouge** (`btn-danger` / `btn-outline-danger`), pas de badges multicolores.
- Champs de saisie et selects rectangulaires, boutons d'action sous forme d'icônes.

## Lancer en local
```
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
