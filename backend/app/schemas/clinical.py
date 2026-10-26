from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.patient import PatientOut

# 12 organ pemeriksaan fisik (Bagian 4 rancangan) — urutan = urutan tampil di form.
BODY_SITES: list[str] = [
    "Kepala",
    "Mata",
    "Telinga",
    "Leher",
    "Thorax",
    "Paru",
    "Jantung",
    "Abdomen",
    "Inguinal",
    "Ekstremitas Atas",
    "Ekstremitas Bawah",
    "Kulit",
]

Source = Literal["manual", "ai"]


# ---------------------------------------------------------------- master data
class Icd10Out(BaseModel):
    code: str
    name: str

    model_config = {"from_attributes": True}


class DrugOut(BaseModel):
    id: int
    name: str
    unit: str
    price: float

    model_config = {"from_attributes": True}


class ProcedureMasterOut(BaseModel):
    id: int
    name: str
    price: float

    model_config = {"from_attributes": True}


# ------------------------------------------------------------- payload simpan
class PhysicalExamIn(BaseModel):
    body_site: str
    finding: str = Field(min_length=1, max_length=500)

    @field_validator("body_site")
    @classmethod
    def _known_site(cls, value: str) -> str:
        if value not in BODY_SITES:
            raise ValueError(f"Organ tidak dikenal: {value}")
        return value

    @field_validator("finding")
    @classmethod
    def _strip_finding(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Temuan tidak boleh kosong")
        return value


class DiagnosisIn(BaseModel):
    icd_code: str | None = Field(default=None, max_length=10)
    name: str = Field(min_length=1, max_length=255)
    source: Source = "manual"


class MedicationIn(BaseModel):
    drug_id: int
    quantity: int = Field(default=1, ge=1, le=9999)
    source: Source = "manual"


class ProcedureIn(BaseModel):
    procedure_id: int
    source: Source = "manual"


class ExamIn(BaseModel):
    anamnesis: str = Field(default="", max_length=5000)
    physical_exam: list[PhysicalExamIn] = []
    diagnoses: list[DiagnosisIn] = []
    medications: list[MedicationIn] = []
    procedures: list[ProcedureIn] = []
    education: str = Field(default="", max_length=5000)

    @model_validator(mode="after")
    def _no_duplicates(self) -> "ExamIn":
        sites = [p.body_site for p in self.physical_exam]
        if len(sites) != len(set(sites)):
            raise ValueError("Organ pemeriksaan fisik tidak boleh duplikat")
        if len({m.drug_id for m in self.medications}) != len(self.medications):
            raise ValueError("Obat tidak boleh duplikat")
        if len({p.procedure_id for p in self.procedures}) != len(self.procedures):
            raise ValueError("Tindakan tidak boleh duplikat")
        return self


# --------------------------------------------------------------------- output
class PractitionerOut(BaseModel):
    id: int
    full_name: str

    model_config = {"from_attributes": True}


class PhysicalExamOut(BaseModel):
    body_site: str
    finding: str
    source: str
    verified_by_doctor: bool


class DiagnosisOut(BaseModel):
    id: int
    icd_code: str | None
    name: str
    assertion_status: str
    source: str
    verified_by_doctor: bool


class MedicationOut(BaseModel):
    id: int
    drug_id: int | None
    name: str
    doctor: str | None
    unit: str | None
    quantity: int
    unit_price: float
    subtotal: float
    source: str
    verified_by_doctor: bool


class ProcedureOut(BaseModel):
    id: int
    procedure_id: int | None
    name: str
    price: float
    source: str
    verified_by_doctor: bool


class EncounterCreate(BaseModel):
    patient_id: int
    practitioner_id: int | None = None
    reason: str | None = Field(default=None, max_length=255)


class EncounterDetailOut(BaseModel):
    id: int
    status: str
    reason: str | None
    started_at: datetime
    patient: PatientOut
    practitioner: PractitionerOut | None
    anamnesis: str
    education: str
    physical_exam: list[PhysicalExamOut]
    diagnoses: list[DiagnosisOut]
    medications: list[MedicationOut]
    procedures: list[ProcedureOut]
    total_cost: float


class EncounterSummaryOut(BaseModel):
    id: int
    status: str
    reason: str | None
    started_at: datetime
    practitioner: PractitionerOut | None
    diagnoses: list[str]


class DashboardSummaryOut(BaseModel):
    patient_count: int
    encounters_today: int
