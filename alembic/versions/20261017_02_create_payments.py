"""Create payment and installment tables.

Revision ID: 20261017_02
Revises: 20261017_01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20261017_02"
down_revision: str | None = "20261017_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "payments",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "tariff_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("tariffs.id"),
            nullable=False,
        ),
        sa.Column(
            "promo_code_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("promo_codes.id"),
            nullable=True,
        ),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("method", sa.String(length=20), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("discount", sa.BigInteger(), nullable=False),
        sa.Column("installment_months", sa.SmallInteger(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "method IN ('card', 'sbp', 'installment')",
            name="ck_payments_method_valid",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'succeeded', 'failed', 'refunded')",
            name="ck_payments_status_valid",
        ),
        sa.CheckConstraint("amount > 0", name="ck_payments_amount_positive"),
        sa.CheckConstraint("discount >= 0", name="ck_payments_discount_nonnegative"),
        sa.CheckConstraint(
            "installment_months IS NULL OR installment_months IN (3, 6, 12)",
            name="ck_payments_installment_months_valid",
        ),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_table(
        "payment_installments",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "payment_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("payments.id"),
            nullable=False,
        ),
        sa.Column("sequence", sa.SmallInteger(), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.CheckConstraint(
            "sequence > 0", name="ck_payment_installments_sequence_positive"
        ),
        sa.CheckConstraint(
            "amount > 0", name="ck_payment_installments_amount_positive"
        ),
        sa.UniqueConstraint(
            "payment_id", "sequence", name="uq_payment_installments_payment_sequence"
        ),
    )


def downgrade() -> None:
    op.drop_table("payment_installments")
    op.drop_table("payments")
