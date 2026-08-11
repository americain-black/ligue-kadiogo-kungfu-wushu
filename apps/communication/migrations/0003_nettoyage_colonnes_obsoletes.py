from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('communication', '0002_actualite_est_public'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE communication_actualite DROP COLUMN IF EXISTS tous_les_comptes_ligue;
            ALTER TABLE communication_actualite DROP COLUMN IF EXISTS visibilite;
            """,
            reverse_sql=""
        ),
    ]
