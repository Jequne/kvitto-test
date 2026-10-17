"""Create tariff and promo code reference tables.

Revision ID: 20261017_01
Revises:
"""

from collections.abc import Sequence
from uuid import UUID

import sqlalchemy as sa
from alembic import op


revision: str = "20261017_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tariffs",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(length=32), nullable=False, unique=True),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("price", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("price > 0", name="ck_tariffs_price_positive"),
    )
    op.create_table(
        "promo_codes",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(length=64), nullable=False, unique=True),
        sa.Column("discount_percent", sa.SmallInteger(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "discount_percent BETWEEN 0 AND 100",
            name="ck_promo_codes_discount_percent_range",
        ),
    )

    tariffs = sa.table(
        "tariffs",
        sa.column("id", sa.Uuid(as_uuid=True)),
        sa.column("code", sa.String()),
        sa.column("title", sa.String()),
        sa.column("price", sa.BigInteger()),
    )
    op.bulk_insert(
        tariffs,
        [
            {
                "id": UUID("a1138f45-bb1d-4cc3-90e5-4d84ec6b50c1"),
                "code": "basic",
                "title": "Basic",
                "price": 990000,
            },
            {
                "id": UUID("b1a50c2e-1e3d-499a-8c3a-8fdc802dc60c"),
                "code": "standard",
                "title": "Standard",
                "price": 1990000,
            },
            {
                "id": UUID("e5559895-a7c5-49d0-b4dc-0141ba56a6c9"),
                "code": "premium",
                "title": "Premium",
                "price": 2990000,
            },
        ],
    )
    promo_codes = sa.table(
        "promo_codes",
        sa.column("id", sa.Uuid(as_uuid=True)),
        sa.column("code", sa.String()),
        sa.column("discount_percent", sa.SmallInteger()),
    )
    op.bulk_insert(
        promo_codes,
        [
            {
                "id": UUID("fdf36080-3f12-4f1d-a339-06aeb26cd751"),
                "code": "KVITTO10",
                "discount_percent": 10,
            }
        ],
    )


def downgrade() -> None:
    op.drop_table("promo_codes")
    op.drop_table("tariffs")
