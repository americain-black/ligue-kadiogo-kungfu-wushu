from django.db import migrations

def me_nettoyer_colonnes(apps, schema_editor):
    vendor = schema_editor.connection.vendor
    if vendor == 'postgresql':
        schema_editor.execute("ALTER TABLE communication_actualite DROP COLUMN IF EXISTS tous_les_comptes_ligue;")
        schema_editor.execute("ALTER TABLE communication_actualite DROP COLUMN IF EXISTS visibilite;")
    elif vendor == 'sqlite':
        with schema_editor.connection.cursor() as cursor:
            cursor.execute("PRAGMA table_info(communication_actualite)")
            columns = [row[1] for row in cursor.fetchall()]
            for col in ['tous_les_comptes_ligue', 'visibilite']:
                if col in columns:
                    cursor.execute(f"ALTER TABLE communication_actualite DROP COLUMN {col};")

class Migration(migrations.Migration):

    dependencies = [
        ('communication', '0002_actualite_est_public'),
    ]

    operations = [
        migrations.RunPython(me_nettoyer_colonnes, reverse_code=migrations.RunPython.noop),
    ]
