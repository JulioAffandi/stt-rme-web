from decimal import Decimal

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Icd10Master(Base):
    """Master diagnosis ICD-10."""

    __tablename__ = "icd10_master"

    code: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)


class DrugMaster(Base):
    """Master obat."""

    __tablename__ = "drug_master"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    unit: Mapped[str] = mapped_column(String(30), default="tablet")
    price: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))


class ProcedureMaster(Base):
    """Master tindakan."""

    __tablename__ = "procedure_master"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
