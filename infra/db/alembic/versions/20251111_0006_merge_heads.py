"""merge heads after fixing duplicate"""

from alembic import op
import sqlalchemy as sa

# НОВИЙ id ревізії (унікальний)
revision = "20251111_0006"
# СЮДИ впиши саме ті два head-и, що показує `alembic heads -v` після кроку 1.
# Судячи з твоїх логів — це "20251111_0002" і "20251111_0005".
down_revision = ("20251111_0004", "20251111_0005")
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
