
# pyrefly: ignore [missing-import]
from django.db import models


class Ligue(models.Model):
    nom_ligue            = models.CharField(max_length=200, unique=True)
    sigle                = models.CharField(max_length=20,unique=True)
    region               = models.CharField(max_length=100)
    adresse_siege = models.CharField(max_length=200, blank=True)
    email_contact = models.EmailField(blank=True)
    telephone     = models.CharField(max_length=20, blank=True)
    lien_facebook = models.URLField(max_length=300, blank=True, verbose_name="Lien Facebook Officiel", default="https://facebook.com/lkkfw")
    lien_whatsapp = models.CharField(max_length=200, blank=True, verbose_name="Lien / Numéro WhatsApp", default="https://wa.me/22673868616")
    lien_youtube  = models.URLField(max_length=300, blank=True, verbose_name="Lien YouTube Officiel", default="https://youtube.com")
    logo          = models.ImageField(upload_to='ligues/', null=True, blank=True)
    statut               = models.CharField(
        max_length=20,
        choices=[('ACTIVE', 'Active'), ('INACTIVE', 'Inactive')],
        default='ACTIVE'
    )
    date_creation        = models.DateField(auto_now_add=True)

    # Informations "À Propos" et Présentation
    presentation_generale = models.TextField(blank=True, verbose_name="Présentation générale")
    historique            = models.TextField(blank=True, verbose_name="Historique du Wushu dans la région")
    objectif_general      = models.TextField(blank=True, verbose_name="Objectif général")
    objectifs_specifiques = models.TextField(blank=True, verbose_name="Objectifs spécifiques")
    vision                = models.TextField(blank=True, verbose_name="Vision stratégique")
    valeurs               = models.TextField(blank=True, verbose_name="Valeurs fondamentales")
    mot_president         = models.TextField(blank=True, verbose_name="Mot du Président / de la Présidente")
    nom_president         = models.CharField(max_length=150, blank=True, verbose_name="Nom & Titre du Président")
    photo_president       = models.ImageField(upload_to='ligues/president/', null=True, blank=True, verbose_name="Photo du Président")

    # Titres des boutons & menus "À PROPOS" personnalisables (ex: Mot de la Présidente)
    titre_presentation     = models.CharField(max_length=100, default="Présentation de la Ligue", blank=True, verbose_name="Titre du bouton Présentation")
    titre_mot_president    = models.CharField(max_length=100, default="Mot du Président", blank=True, verbose_name="Titre du bouton Mot du Président / Présidente")
    titre_organigramme     = models.CharField(max_length=100, default="Organigramme & Direction", blank=True, verbose_name="Titre du bouton Organigramme")
    titre_vision_missions  = models.CharField(max_length=100, default="Vision & Missions", blank=True, verbose_name="Titre du bouton Vision & Missions")
    titre_contact          = models.CharField(max_length=100, default="Contact", blank=True, verbose_name="Titre du bouton Contact")

    # Configuration du Bulletin de Note (Modifiables depuis le tableau de bord)
    bulletin_header_gauche_ligne1 = models.CharField(max_length=200, default="FEDERATION BURKINABE DE KUNG FU WUSHU (FBKFW)", blank=True, verbose_name="En-tête gauche - Ligne 1 (Fédération)")
    bulletin_header_gauche_ligne2 = models.CharField(max_length=200, default="LIGUE DU KADIOGO DE KUNG FU WUSHU (LKKFW)", blank=True, verbose_name="En-tête gauche - Ligne 2 (Ligue)")
    bulletin_header_droite_ligne1 = models.CharField(max_length=150, default="BURKINA FASO", blank=True, verbose_name="En-tête droite - Pays")
    bulletin_header_droite_devise = models.CharField(max_length=150, default="La Patrie ou la Mort, nous Vaincrons", blank=True, verbose_name="En-tête droite - Devise")
    bulletin_signataire_titre     = models.CharField(max_length=100, default="Directeur Technique", blank=True, verbose_name="Titre du signataire")
    bulletin_signataire_nom       = models.CharField(max_length=150, default="Pr Issa BOUSSIM", blank=True, verbose_name="Nom du signataire")
    bulletin_signataire_grade     = models.CharField(max_length=100, default="CN 3è Duan", blank=True, verbose_name="Grade/Titre du signataire")
    bulletin_pied_legal           = models.TextField(default="LIGUE DU KADIOGO DE KUNG FU WUSHU (LKKFW)\nSiège social : Ouagadougou, Récépissé n° : 2024-22/MSJE/RCEN/DRSL-CEN/SRRIS\nMail : ligueducentrekungfuwushu@gmail.com Tél : (+226) 65 08 92 62 / 73 86 86 16", blank=True, verbose_name="Pied de page légal du bulletin")
    bulletin_mention_exemplaire   = models.CharField(max_length=200, default="Ceci est un document original, il n'est délivré qu'en un seul exemplaire.", blank=True, verbose_name="Mention d'exemplaire unique (bas de page)")

    # Configuration de la Bannière d'Accueil (Textes & Animation)
    titre_hero_accueil = models.CharField(
        max_length=250,
        default="",
        blank=True,
        verbose_name="Titre principal fixe de la Bannière (Optionnel)"
    )
    soustitre_hero_accueil = models.TextField(
        default="Suivez chaque parcours, du club jusqu'au grade obtenu, en toute transparence",
        blank=True,
        verbose_name="Sous-titre de la Bannière d'Accueil"
    )
    phrases_hero_accueil = models.TextField(
        default="Gestion des passages de grades sportifs\nAffiliations et Licences des Clubs\nRégularisation et Homologation des Ceintures\nPromotion et Développement du Wushu",
        blank=True,
        verbose_name="Phrases dynamiques tournantes (1 par ligne)",
        help_text="Entrez les phrases d'animation de la bannière d'accueil (une phrase par ligne)."
    )

    class Meta:
        verbose_name        = 'Ligue'
        verbose_name_plural = 'Ligues'

    def __str__(self):
        return f"{self.sigle} — {self.nom_ligue}"

    def est_active(self):
        return self.statut == 'ACTIVE'

    def get_phrases_hero_list(self):
        if not self.phrases_hero_accueil:
            return [
                "Gestion des passages de grades sportifs",
                "Affiliations et Licences des Clubs",
                "Régularisation et Homologation des Ceintures",
                "Promotion et Développement du Wushu"
            ]
        lines = [l.strip() for l in self.phrases_hero_accueil.splitlines() if l.strip()]
        return lines if lines else ["Gestion des passages de grades sportifs"]

    def get_presentation_generale(self):
        if self.presentation_generale and self.presentation_generale.strip():
            return self.presentation_generale
        return "La Ligue du Kadiogo de Kung-Fu Wushu est une structure sportive régionale affiliée à la Fédération Burkinabè de Kung-Fu Wushu (FBKFW)."

    def get_historique(self):
        if self.historique and self.historique.strip():
            return self.historique
        return (
            "Fondée en 2006, la Ligue de Kung Fu Wushu de la région du Kadiogo a débuté avec moins de 10 clubs affiliés. "
            "Aujourd’hui, elle compte 36 clubs membres et regroupe plus de 400 athlètes compétiteurs, témoignant d’une croissance remarquable et d’un dynamisme constant.\n\n"
            "La Ligue du Kadiogo est structurée autour de deux instances majeures :\n"
            "➢ Le Bureau Exécutif, chargé de la gestion administrative et stratégique\n"
            "➢ La Direction Technique, responsable de l’encadrement sportif et du développement des compétences\n\n"
            "Le bureau exécutif est élu à l’Assemblée Générale par les clubs membres pour un mandat de quatre (4) ans. "
            "Depuis le 29 Septembre 2024, un nouveau bureau a été élu pour un mandat de quatre (4) ans."
        )

    def get_objectif_general(self):
        if self.objectif_general and self.objectif_general.strip():
            return self.objectif_general
        return "Organiser un championnat régional pour promouvoir le Kung Fu Wushu et valoriser les athlètes de la région du Kadiogo."

    def get_objectifs_specifiques(self):
        if self.objectifs_specifiques and self.objectifs_specifiques.strip():
            return self.objectifs_specifiques
        return (
            "• rassembler les clubs de Kung Fu Wushu de la ligue du Kadiogo ;\n"
            "• offrir un cadre officiel de compétition et de sélection ;\n"
            "• renforcer les capacités d’organisation sportive au niveau régional ;\n"
            "• sensibiliser le public aux valeurs du Kung Fu Wushu : discipline, respect, persévérance"
        )

    def get_objectifs_specifiques_list(self):
        text = self.get_objectifs_specifiques()
        lines = [line.strip().lstrip('•').lstrip('➢').lstrip('-').strip() for line in text.split('\n') if line.strip()]
        return lines

    def get_mot_president(self):
        if self.mot_president and self.mot_president.strip():
            return self.mot_president
        return (
            "Chers pratiquants, chers responsables de clubs, passionnés d’arts martiaux,\n\n"
            "C’est avec un grand honneur que nous vous accueillons sur la plateforme numérique officielle de la Ligue du Kadiogo de Kung-Fu Wushu. "
            "La modernisation de nos outils de gestion s’inscrit dans notre volonté d’offrir une transparence totale et un service de qualité à l'ensemble des acteurs de notre discipline.\n\n"
            "Notre ambition commune est claire : élever le niveau technique de nos athlètes, soutenir le travail remarquable des maîtres d’armes dans nos clubs, et garantir des passages de grades conformes aux standards internationaux.\n\n"
            "À travers ce portail, chaque athlète peut désormais suivre son parcours et consulter ses résultats officiels en toute sécurité. Nous invitons tous les clubs à poursuivre leurs efforts pour le rayonnement du Wushu au Burkina Faso."
        )

    def get_nom_president(self):
        if self.nom_president and self.nom_president.strip():
            return self.nom_president
        return "Président de la Ligue du Kadiogo"

    def get_vision(self):
        if self.vision and self.vision.strip():
            return self.vision
        return "Faire du Kadiogo le pôle d'excellence du Kung-Fu Wushu en Afrique de l'Ouest, reconnu pour la qualité technique de ses athlètes, la rigueur de ses cadres et la transparence de sa gouvernance."

    def get_valeurs(self):
        if self.valeurs and self.valeurs.strip():
            return self.valeurs
        return (
            "• Discipline & Respect : Cultiver la rigueur morale, la fraternité et le respect des enseignants et camarades.\n"
            "• Excellence Technique : Promouvoir la maîtrise martiale des Taolu (formes) et du Sanda (combat libre).\n"
            "• Transparence & Gouvernance : Offrir une gestion numérique moderne des résultats et des inscriptions."
        )

    def get_titre_presentation(self):
        return self.titre_presentation or "Présentation de la Ligue"

    def get_titre_mot_president(self):
        return self.titre_mot_president or "Mot du Président"

    def get_titre_organigramme(self):
        return self.titre_organigramme or "Organigramme & Direction"

    def get_titre_vision_missions(self):
        return self.titre_vision_missions or "Vision & Missions"

    def get_titre_contact(self):
        return self.titre_contact or "Contact"

    def get_bulletin_header_gauche_ligne1(self):
        return self.bulletin_header_gauche_ligne1 or "FEDERATION BURKINABE DE KUNG FU WUSHU (FBKFW)"

    def get_bulletin_header_gauche_ligne2(self):
        return self.bulletin_header_gauche_ligne2 or f"{self.nom_ligue.upper()} ({self.sigle.upper()})"

    def get_bulletin_header_droite_ligne1(self):
        return self.bulletin_header_droite_ligne1 or "BURKINA FASO"

    def get_bulletin_header_droite_devise(self):
        return self.bulletin_header_droite_devise or "La Patrie ou la Mort, nous Vaincrons"

    def get_bulletin_signataire_titre(self):
        return self.bulletin_signataire_titre or "Directeur Technique"

    def get_bulletin_signataire_nom(self):
        return self.bulletin_signataire_nom or "Pr Issa BOUSSIM"

    def get_bulletin_signataire_grade(self):
        return self.bulletin_signataire_grade or "CN 3è Duan"

    def get_bulletin_pied_legal(self):
        return self.bulletin_pied_legal or f"{self.nom_ligue} ({self.sigle})\nSiège social : {self.adresse_siege}\nMail : {self.email_contact} Tél : {self.telephone}"

    def get_bulletin_mention_exemplaire(self):
        return self.bulletin_mention_exemplaire or "Ceci est un document original, il n'est délivré qu'en un seul exemplaire."


class VoletOrganigramme(models.Model):
    ligue       = models.ForeignKey(Ligue, on_delete=models.CASCADE, related_name='volets')
    nom_volet   = models.CharField(max_length=200)
    ordre       = models.PositiveIntegerField(default=0)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Volet organigramme'
        verbose_name_plural = 'Volets organigramme'
        ordering            = ['ordre', 'date_creation']

    @property
    def membres_ligue(self):
        return self.membres.filter(club__isnull=True).order_by('ordre', 'nom')

    def __str__(self):
        return f"{self.ligue.sigle} — {self.nom_volet}"


class MembreOrganigramme(models.Model):
    FONCTION_CHOICES = [
        ('PDT', 'Présidente / Président'),
        ('VPT', 'Vice-Président(e)'),
        ('SG',  'Secrétaire Général(e)'),
        ('SGA', 'Secrétaire Général(e) Adjoint(e)'),
        ('TG',  'Trésorier(e) Général(e)'),
        ('TA',  'Trésorier(e) Adjoint(e)'),
        ('SO',  "Secrétaire à l'Organisation"),
        ('SAO', "Secrétaire Adjoint(e) à l'Organisation"),
        ('SIC', "Secrétaire à l'Information et à la Communication"),
        ('CC1', '1er Commissaire aux Comptes'),
        ('CC2', '2e Commissaire aux Comptes'),
        ('CJ',  'Conseiller Juridique'),
        ('DT',  'Directeur Technique'),
        ('DTA', 'Directeur Technique Adjoint'),
        ('ENT', "Entraîneur"),
    ]

    volet               = models.ForeignKey(VoletOrganigramme, on_delete=models.CASCADE, related_name='membres')
    club                = models.ForeignKey('clubs.Club', on_delete=models.CASCADE, null=True, blank=True, related_name='membres_organigramme')
    nom                 = models.CharField(max_length=100)
    prenom              = models.CharField(max_length=100)
    contact             = models.CharField(max_length=50, blank=True)
    fonction            = models.CharField(max_length=200)
    ordre               = models.PositiveIntegerField(default=1, verbose_name="Ligne / Rang hiérarchique", help_text="Numéro de ligne : 1 = Ligne du haut (Président), 2 = Ligne du dessous (VP), 3 = Ligne 3...")
    date_debut_fonction = models.DateField(null=True, blank=True)
    actif               = models.BooleanField(default=True)
    date_ajout          = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Membre organigramme'
        verbose_name_plural = 'Membres organigramme'
        ordering            = ['-actif', 'ordre', 'nom', 'prenom']

    def __str__(self):
        return f"[Ligne {self.ordre}] {self.prenom} {self.nom} — {self.fonction}"

    @property
    def sigle_seul(self):
        f = (self.fonction or '').strip()
        if not f:
            return ""
            
        f_lower = f.lower().replace('é', 'e').replace('è', 'e')
        
        SIGLES = [
            ('vice-president', 'VPT'),
            ('vice president', 'VPT'),
            ('vice-président', 'VPT'),
            ('vice président', 'VPT'),
            ('president', 'PDT'),
            ('président', 'PDT'),
            ('secretaire general adjoint', 'SGA'),
            ('secretaire generale adjointe', 'SGA'),
            ('secretaire general', 'SG'),
            ('secretaire generale', 'SG'),
            ('tresoriere generale', 'TG'),
            ('tresorier general', 'TG'),
            ('tresoriere adjointe', 'TA'),
            ('tresorier adjoint', 'TA'),
            ('secretaire adjoint', 'SAO'),
            ('secretaire adjointe', 'SAO'),
            ('organisation', 'SO'),
            ('information', 'SIC'),
            ('communication', 'SIC'),
            ('1er commissaire', 'CC1'),
            ('2e commissaire', 'CC2'),
            ('commissaire aux comptes 1', 'CC1'),
            ('commissaire aux comptes 2', 'CC2'),
            ('conseiller juridique', 'CJ'),
            ('directeur technique adjoint', 'DTA'),
            ('directeur technique', 'DT'),
            ('entraineur', 'ENT'),
            ('entraîneur', 'ENT'),
        ]
        
        for kw, sigle in SIGLES:
            if kw in f_lower:
                return sigle
                
        if len(f) <= 5:
            return f.upper()
            
        return f