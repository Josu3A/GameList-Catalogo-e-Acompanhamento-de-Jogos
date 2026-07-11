"""Trigger de updated_at em lists (função criada em accounts.0002)."""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0001_initial'),
        ('accounts', '0002_updated_at_trigger'),
    ]

    operations = [
        migrations.RunSQL(
            'CREATE TRIGGER trg_lists_updated_at '
            'BEFORE UPDATE ON lists '
            'FOR EACH ROW EXECUTE FUNCTION set_updated_at();',
            reverse_sql='DROP TRIGGER IF EXISTS trg_lists_updated_at ON lists;',
        ),
    ]
