from pydantic import BaseModel


class ProyekSaatMencetakDto(BaseModel):
    enititas: str
    start_date: str
    coa_number: str
    coa_label: str
    end_date: str
    view: int
