from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse


class ChangementMotDePasseObligatoireMiddleware:
    """
    Tant qu'un utilisateur se connecte avec un mot de passe provisoire,
    il est renvoyé vers la page où il doit choisir son propre mot de passe.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated and getattr(user, 'doit_changer_mot_de_passe', False):
            pages_autorisees = (
                reverse('accounts:changer_mot_de_passe_obligatoire'),
                reverse('accounts:logout'),
            )
            chemin = request.path
            fichiers = tuple(p for p in (settings.STATIC_URL, getattr(settings, 'MEDIA_URL', None)) if p)
            if chemin not in pages_autorisees and not chemin.startswith(fichiers):
                return redirect('accounts:changer_mot_de_passe_obligatoire')
        return self.get_response(request)
