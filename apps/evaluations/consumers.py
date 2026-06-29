import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class NotationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket pour la synchronisation des notes en temps réel.

    URL        : ws/evaluations/session/<session_id>/notation/
    Groupe     : session_<session_id>
    Autorisés  : Jury affecté à la session + Gestionnaire Ligue de la ligue
    """

    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.group_name = f'session_{self.session_id}'

        user = self.scope['user']
        if not user.is_authenticated:
            await self.close()
            return

        if not await self._est_autorise(user):
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await self.send(text_data=json.dumps({
            'type': 'connexion_etablie',
            'session_id': self.session_id,
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        # Le client est en lecture seule via WS.
        # Les mises à jour sont déclenchées par les vues HTTP.
        pass

    # ── Handlers des événements diffusés par les vues ─────────────────────────

    async def note_saisie(self, event):
        """Diffuse la sauvegarde/validation d'une note à tous les connectés."""
        await self.send(text_data=json.dumps({
            'type': 'note_saisie',
            'data': event['data'],
        }))

    async def note_deverrouillee(self, event):
        """Diffuse le déverrouillage d'une note par le Gestionnaire Ligue."""
        await self.send(text_data=json.dumps({
            'type': 'note_deverrouillee',
            'data': event['data'],
        }))

    async def notes_manquantes(self, event):
        """Signale qu'il manque encore des notes pour clore l'évaluation."""
        await self.send(text_data=json.dumps({
            'type': 'notes_manquantes',
            'data': event['data'],
        }))

    async def resultat_calcule(self, event):
        """Diffuse le résultat final d'un candidat dès qu'il est calculé."""
        await self.send(text_data=json.dumps({
            'type': 'resultat_calcule',
            'data': event['data'],
        }))

    # ── Vérification d'autorisation ───────────────────────────────────────────

    @database_sync_to_async
    def _est_autorise(self, user):
        from apps.exams.models import SessionExamen, AffectationJury

        try:
            session = SessionExamen.objects.select_related('annee_sportive__ligue').get(
                pk=self.session_id
            )
        except SessionExamen.DoesNotExist:
            return False

        if user.is_superuser:
            return True

        if user.est_gest_ligue():
            return (
                user.ligue is not None
                and session.annee_sportive.ligue == user.ligue
            )

        if user.est_jury():
            return AffectationJury.objects.filter(
                session=session, jury=user
            ).exists()

        return False
