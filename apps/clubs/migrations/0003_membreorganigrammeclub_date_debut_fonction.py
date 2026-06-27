from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clubs', '0002_remove_club_contact_maitre_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='membreorganigrammeclub',
            name='date_debut_fonction',
            field=models.DateField(blank=True, null=True),
        ),
    ]
