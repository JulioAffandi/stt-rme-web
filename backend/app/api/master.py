from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import DrugMaster, Icd10Master, ProcedureMaster
from app.schemas.clinical import DrugOut, Icd10Out, ProcedureMasterOut

router = APIRouter(tags=["master"], dependencies=[Depends(get_current_user)])

_Q = Query(default=None, max_length=100)
_LIMIT = Query(default=20, ge=1, le=500)


@router.get("/icd10", response_model=list[Icd10Out])
def search_icd10(
    q: str | None = _Q, limit: int = _LIMIT, db: Session = Depends(get_db)
) -> list[Icd10Out]:
    stmt = select(Icd10Master)
    if q and q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Icd10Master.code.ilike(like), Icd10Master.name.ilike(like)))
    rows = db.scalars(stmt.order_by(Icd10Master.code).limit(limit)).all()
    return [Icd10Out.model_validate(r) for r in rows]


@router.get("/drugs", response_model=list[DrugOut])
def search_drugs(
    q: str | None = _Q, limit: int = _LIMIT, db: Session = Depends(get_db)
) -> list[DrugOut]:
    stmt = select(DrugMaster)
    if q and q.strip():
        stmt = stmt.where(DrugMaster.name.ilike(f"%{q.strip()}%"))
    rows = db.scalars(stmt.order_by(DrugMaster.name).limit(limit)).all()
    return [DrugOut.model_validate(r) for r in rows]


@router.get("/procedures", response_model=list[ProcedureMasterOut])
def search_procedures(
    q: str | None = _Q, limit: int = _LIMIT, db: Session = Depends(get_db)
) -> list[ProcedureMasterOut]:
    stmt = select(ProcedureMaster)
    if q and q.strip():
        stmt = stmt.where(ProcedureMaster.name.ilike(f"%{q.strip()}%"))
    rows = db.scalars(stmt.order_by(ProcedureMaster.name).limit(limit)).all()
    return [ProcedureMasterOut.model_validate(r) for r in rows]
