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
- **Transmission des identifiants aux nouveaux utilisateurs** (problème : aujourd'hui rien n'est prévu).
  Plan validé : mot de passe provisoire généré automatiquement, email au nouvel utilisateur,
  page récapitulative Copier/Imprimer (si pas d'email), changement de mot de passe obligatoire à la 1re connexion.
- **Reste à faire sur le serveur de production** : mettre à jour le `.env` du serveur (lignes EMAIL_*) puis redémarrer le site.

### Prochaines étapes / idées
- (à compléter)

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

