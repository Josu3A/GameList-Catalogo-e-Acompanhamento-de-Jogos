"""Função set_updated_at() + trigger em users (paridade com db/schema.sql §6).

O trigger mantém updated_at correto mesmo em UPDATEs feitos fora do Django
(decisão registrada no LOG.md de 2026-07-10).
"""
from django.db import migrations

CREATE_FUNCTION = """
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            CREATE_FUNCTION,
            reverse_sql='DROP FUNCTION IF EXISTS set_updated_at() CASCADE;',
        ),
        migrations.RunSQL(
            'CREATE TRIGGER trg_users_updated_at '
            'BEFORE UPDATE ON users '
            'FOR EACH ROW EXECUTE FUNCTION set_updated_at();',
            reverse_sql='DROP TRIGGER IF EXISTS trg_users_updated_at ON users;',
        ),
    ]
