from django.db import migrations

def drop_maitre_column(apps, schema_editor):
    vendor = schema_editor.connection.vendor
    if vendor == 'postgresql':
        schema_editor.execute('ALTER TABLE clubs_club DROP COLUMN IF EXISTS maitre;')
    elif vendor == 'sqlite':
        with schema_editor.connection.cursor() as cursor:
            cursor.execute("PRAGMA table_info(clubs_club)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'maitre' in columns:
                cursor.execute("ALTER TABLE clubs_club DROP COLUMN maitre;")

class Migration(migrations.Migration):

    dependencies = [
        ('clubs', '0010_demandeaffiliation_approuve_par_and_more'),
    ]

    operations = [
        migrations.RunPython(drop_maitre_column, reverse_code=migrations.RunPython.noop),
    ]
