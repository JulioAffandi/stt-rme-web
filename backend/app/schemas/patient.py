from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator


def _not_future(value: date | None) -> date | None:
    if value is not None and value > date.today():
        raise ValueError("Tanggal lahir tidak boleh di masa depan")
    return value


class PatientBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    birth_date: date
    gender: str = Field(pattern="^(M|F)$")
    address: str | None = Field(default=None, max_length=500)
    phone_number: str | None = Field(default=None, max_length=30)

    @field_validator("full_name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Nama tidak boleh kosong")
        return value

    _check_birth = field_validator("birth_date")(_not_future)


class PatientCreate(PatientBase):
    # Bila kosong, No. RM dibuat otomatis (format RM-<tahun>-<urut>).
    medical_record_no: str | None = Field(default=None, min_length=1, max_length=30)


class PatientUpdate(BaseModel):
    medical_record_no: str | None = Field(default=None, min_length=1, max_length=30)
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    birth_date: date | None = None
    gender: str | None = Field(default=None, pattern="^(M|F)$")
    address: str | None = Field(default=None, max_length=500)
    phone_number: str | None = Field(default=None, max_length=30)

    _check_birth = field_validator("birth_date")(_not_future)


class PatientOut(PatientBase):
    id: int
    medical_record_no: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PatientListOut(BaseModel):
    items: list[PatientOut]
    total: int
