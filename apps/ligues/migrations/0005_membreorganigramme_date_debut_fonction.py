from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ligues', '0004_remove_ligue_contact_secretaire_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='membreorganigramme',
            name='date_debut_fonction',
            field=models.DateField(blank=True, null=True),
        ),
    ]
