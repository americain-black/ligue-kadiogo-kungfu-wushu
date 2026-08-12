from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('clubs', '0010_demandeaffiliation_approuve_par_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE clubs_club DROP COLUMN IF EXISTS maitre;',
            reverse_sql=migrations.RunSQL.noop
        ),
    ]
