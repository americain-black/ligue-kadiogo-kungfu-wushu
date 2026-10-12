from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.ligues.models import Ligue
from .identifiants import CLE_SESSION, EMAIL_ENVOYE, EMAIL_ABSENT
from .models import Role, Utilisateur, UtilisateurRole


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class TransmissionIdentifiantsTests(TestCase):
    """Création d'un compte par la Ligue → identifiants transmis → changement obligatoire du mot de passe."""

    def setUp(self):
        self.ligue = Ligue.objects.create(nom_ligue="Ligue Test", sigle="LT", region="Centre")
        self.role_ligue = Role.objects.create(nom_role=Role.GEST_LIGUE)
        self.role_jury = Role.objects.create(nom_role=Role.JURY)
        self.gestionnaire = Utilisateur.objects.create_user(username='gest', password='Gest-Passe-2026', ligue=self.ligue)
        UtilisateurRole.objects.create(utilisateur=self.gestionnaire, role=self.role_ligue)
        self.client.force_login(self.gestionnaire)

    def _creer_compte(self, email):
        return self.client.post(reverse('accounts:creer_utilisateur_ligue'), {
            'role': self.role_jury.pk, 'username': 'jury1', 'first_name': 'Awa', 'last_name': 'Nana',
            'email': email, 'telephone': '65013531', 'sexe': 'F',
        })

    def test_creation_envoie_email_et_affiche_recapitulatif_une_seule_fois(self):
        reponse = self._creer_compte('awa@example.com')
        self.assertRedirects(reponse, reverse('accounts:identifiants_utilisateur'), fetch_redirect_response=False)

        infos = self.client.session[CLE_SESSION]
        self.assertEqual(infos['statut_email'], EMAIL_ENVOYE)
        jury = Utilisateur.objects.get(username='jury1')
        self.assertEqual(jury.ligue, self.ligue)
        self.assertTrue(jury.doit_changer_mot_de_passe)
        self.assertTrue(jury.check_password(infos['mot_de_passe']))

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['awa@example.com'])
        self.assertIn(infos['mot_de_passe'], mail.outbox[0].body)

        page = self.client.get(reverse('accounts:identifiants_utilisateur'))
        self.assertContains(page, infos['mot_de_passe'])
        self.assertContains(page, 'wa.me/22665013531')
        # Deuxième affichage refusé
        self.assertRedirects(self.client.get(reverse('accounts:identifiants_utilisateur')),
                             reverse('accounts:liste_utilisateurs_ligue'))

    def test_creation_sans_email(self):
        self._creer_compte('')
        self.assertEqual(self.client.session[CLE_SESSION]['statut_email'], EMAIL_ABSENT)
        self.assertEqual(len(mail.outbox), 0)

    def test_premiere_connexion_oblige_a_changer_le_mot_de_passe(self):
        self._creer_compte('')
        provisoire = self.client.session[CLE_SESSION]['mot_de_passe']
        self.client.logout()

        self.assertTrue(self.client.login(username='jury1', password=provisoire))
        page_obligatoire = reverse('accounts:changer_mot_de_passe_obligatoire')
        self.assertRedirects(self.client.get(reverse('accounts:tableau_de_bord')), page_obligatoire)

        # Réutiliser le mot de passe provisoire est refusé
        reponse = self.client.post(page_obligatoire, {'new_password1': provisoire, 'new_password2': provisoire})
        self.assertEqual(reponse.status_code, 200)

        self.client.post(page_obligatoire, {'new_password1': 'Mon-Vrai-Passe-2026', 'new_password2': 'Mon-Vrai-Passe-2026'})
        jury = Utilisateur.objects.get(username='jury1')
        self.assertFalse(jury.doit_changer_mot_de_passe)
        self.assertTrue(jury.check_password('Mon-Vrai-Passe-2026'))
        # La session reste ouverte et le site redevient accessible
        self.assertNotEqual(self.client.get(reverse('accounts:tableau_de_bord')).url, page_obligatoire)

    def test_reinitialisation_par_le_gestionnaire(self):
        self._creer_compte('')
        jury = Utilisateur.objects.get(username='jury1')
        jury.set_password('Ancien-Passe-2026')
        jury.doit_changer_mot_de_passe = False
        jury.save()

        reponse = self.client.post(reverse('accounts:reinitialiser_mot_de_passe', args=[jury.pk]))
        self.assertRedirects(reponse, reverse('accounts:identifiants_utilisateur'), fetch_redirect_response=False)
        jury.refresh_from_db()
        self.assertFalse(jury.check_password('Ancien-Passe-2026'))
        self.assertTrue(jury.doit_changer_mot_de_passe)

    def test_reinitialisation_refusee_hors_de_sa_ligue(self):
        autre_ligue = Ligue.objects.create(nom_ligue="Autre", sigle="AL", region="Est")
        etranger = Utilisateur.objects.create_user(username='etranger', password='x-Passe-2026', ligue=autre_ligue)
        reponse = self.client.post(reverse('accounts:reinitialiser_mot_de_passe', args=[etranger.pk]))
        self.assertEqual(reponse.status_code, 404)

    def test_pages_modifiees_s_affichent(self):
        self._creer_compte('')
        for nom in ('liste_utilisateurs_ligue', 'creer_utilisateur_ligue'):
            self.assertEqual(self.client.get(reverse(f'accounts:{nom}')).status_code, 200, nom)
        jury = Utilisateur.objects.get(username='jury1')
        page = self.client.get(reverse('accounts:liste_utilisateurs_ligue'))
        self.assertContains(page, reverse('accounts:reinitialiser_mot_de_passe', args=[jury.pk]))
        self.assertEqual(self.client.get(reverse('accounts:modifier_utilisateur_ligue', args=[jury.pk])).status_code, 200)

        admin = Utilisateur.objects.create_superuser(username='admin', password='Admin-Passe-2026')
        self.client.force_login(admin)
        for nom in ('liste_utilisateurs', 'creer_utilisateur'):
            self.assertEqual(self.client.get(reverse(f'accounts:{nom}')).status_code, 200, nom)
