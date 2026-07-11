"""Trigger de updated_at em games (função criada em accounts.0002)."""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
        ('accounts', '0002_updated_at_trigger'),
    ]

    operations = [
        migrations.RunSQL(
            'CREATE TRIGGER trg_games_updated_at '
            'BEFORE UPDATE ON games '
            'FOR EACH ROW EXECUTE FUNCTION set_updated_at();',
            reverse_sql='DROP TRIGGER IF EXISTS trg_games_updated_at ON games;',
        ),
    ]
