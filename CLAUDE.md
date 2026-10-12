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
- Production : site sur `salma.kadiogokungfu.bf` (VPS 167.86.109.31), PostgreSQL `ligue_kadiogo_db`.
- Emails envoyés depuis `contact@kadiogokungfu.bf` via `mail.teeritech.bf` (port 465 SSL, cPanel Ecodev).
  DNS du domaine gérés chez Ecoweb (PowerDNS) : utiliser `@` pour le domaine lui-même.

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

## Mise en ligne (VPS)
L'utilisateur colle les commandes lui-même (Claude n'a pas accès au serveur). Donner les commandes **une par une**
(les longues chaînes se coupent au collage). Méthode habituelle :
```
cd /var/www/ligue-kadiogo-kungfu-wushu && source venv/bin/activate
git pull origin main
python manage.py migrate          # vérifier avant avec : python manage.py migrate --plan
python manage.py collectstatic --noinput
sudo systemctl restart daphne
```
- Sauvegarde avant migration : `sudo -u postgres pg_dump ligue_kadiogo_db > /root/sauvegarde_ligue_$(date +%F_%H%M).sql`
- **Ne jamais lancer `makemigrations` sur le serveur** : les migrations se créent en local puis arrivent par git.
- Le `.env` du serveur n'est pas dans git ; dans le terminal VS Code, Ctrl+O de nano est intercepté → modifier avec `sed`/`printf`.

