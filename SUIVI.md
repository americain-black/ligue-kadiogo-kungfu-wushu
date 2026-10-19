# Journal de suivi du projet

> À mettre à jour à la fin de chaque séance de travail.
> Pour reprendre : demander à Claude « lis SUIVI.md et dis-moi où on en était ».

## Où on en est (au 10/10/2026)

### Déjà fait (derniers travaux)
- Tableau de bord du **jury** refait : liste filtrable des licenciés par grade et club,
  page dédiée « Licenciés à évaluer », boutons de notation sous forme d'icônes.
- Harmonisation visuelle de toute l'application avec la **charte rouge**.
- Pièces justificatives et preuves de paiement : conservation et prévisualisation (images / PDF).
- Grades : champ « ordre d'affichage » unique.
- Footer : icônes blanches, style de texte uniforme.

### En cours
- **Sauvegarde automatique quotidienne** de toutes les bases PostgreSQL du VPS (script + cron) : à mettre en place.
- Sécurité du VPS : installer fail2ban, puis connexion SSH par clé.

### Prochaines étapes / idées
- 🔒 Changer la `SECRET_KEY` et le mot de passe PostgreSQL du serveur (ils ont été affichés dans une conversation le 12/10/2026).
- Supprimer le fichier parasite `FETCH_HEAD` à la racine du projet sur le serveur.
- Vérifier `CSRF_TRUSTED_ORIGINS` du `.env` serveur : il ne liste pas `https://salma.kadiogokungfu.bf`.
- Environnement local : le venv a Django 4.2 alors que `requirements.txt` et le serveur utilisent Django 6.0.6 → réinstaller le venv local.

---

## Historique des séances

### 10/10/2026
- Prise en main de Claude Code.
- Création de `CLAUDE.md` (fiche du projet pour Claude) et de ce fichier `SUIVI.md`.
- Sécurité : retrait du token GitHub écrit en clair dans la configuration git.

### 11/10/2026
- Token GitHub supprimé sur github.com par l'utilisateur.
- Retrait du fichier temporaire Word `~$ssier_Recrutement...doc` du dépôt + règle `~$*` dans `.gitignore`.
- Dépôt GitHub laissé en **public** (choix de l'utilisateur).

### 12/10/2026
- Configuration de l'adresse d'envoi **contact@kadiogokungfu.bf** :
  - boîte créée dans le cPanel Ecodev (teeritech.bf), domaine kadiogokungfu.bf ajouté au cPanel ;
  - DNS chez Ecoweb (PowerDNS) : MX `@ → mail.teeritech.bf.`, SPF, DKIM (`default._domainkey`), DMARC (`_dmarc`).
  - Piège Ecoweb : utiliser `@` pour le domaine lui-même (un nom `kadiogokungfu.bf` sans point final est mal interprété).
  - Envoi réel des emails par Ecodev depuis 209.42.18.113 (s940.lon1.mysecurecloudhost.com).
- `.env` local mis à jour (EMAIL_HOST=mail.teeritech.bf, port 465 SSL) : test d'envoi réussi.
- Constat : l'ancienne config (info@kadiogokungfu.teeritech.bf) ne fonctionnait pas, et le code masque les échecs d'envoi (`fail_silently=True`).
- **Transmission des identifiants** (développé et testé, 6 tests automatiques OK) :
  - le gestionnaire ne choisit plus le mot de passe : un mot de passe provisoire est généré (ex. `Kf-4827-hmtq`) ;
  - envoi automatique par email ; page récapitulative affichée une seule fois (Copier / WhatsApp / Imprimer) ;
  - changement de mot de passe obligatoire à la 1re connexion (middleware `apps/accounts/middleware.py`) ;
  - bouton 🔑 « Réinitialiser le mot de passe » dans les listes d'utilisateurs (Ligue et Super Admin) ;
  - les échecs d'envoi d'email sont maintenant journalisés au lieu d'être cachés.
- **Mise en production réussie** sur le VPS :
  - migrations du serveur `0005_alter_role_nom_role` et `0006_merge_20260921_1055` (créées sur le serveur, absentes de git) ajoutées à git ; nouvelle migration renumérotée `0007` ;
  - sauvegarde : `/root/sauvegarde_ligue_2026-10-12_0413.sql` ; anciens fichiers de migration rangés dans `/root/migrations_serveur/` ;
  - `.env` serveur : les lignes EMAIL_* n'existaient pas (les emails du site n'avaient jamais fonctionné) → ajoutées ; test d'envoi depuis le serveur OK.

### 16/10 → 19/10/2026 — Incident : bases de données supprimées sur le VPS
- **16/10 vers 23h20** : suppression de `ligue_kadiogo_db`, `echeancepro_db` et de la base liasse (les DROP de `auto_ecole_db` et `DB_SYMEFIC` ont échoué).
  Session SSH du compte `deployer` depuis 102.178.228.229 (fibre Orange Ouagadougou, adresse habituelle de ce compte),
  suivie à 23h24 de l'effacement de journaux (`truncate` de syslog/secure/messages, historiques supprimés).
  PostgreSQL n'est pas exposé à Internet. Cause exacte à confirmer avec l'utilisateur du compte `deployer`.
- **19/10** : ligue restaurée depuis `/root/sauvegarde_ligue_2026-10-12_0413.sql` + `migrate` (0007).
  Données saisies entre le 12/10 04h13 et le 16/10 23h20 perdues.
- Mot de passe `root` du VPS changé.
- Preuves conservées dans `/root/preuves_incident/` (si la commande de copie a été lancée).

