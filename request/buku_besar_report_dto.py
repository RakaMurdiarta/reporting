from pydantic import BaseModel

class PreparingDto(BaseModel):
    enititas: str
    start_date: str
    coa: str
    end_date: str

class ProcessingDto(BaseModel):
    preparing_task_id: str

class DownloadDto(BaseModel):
    filename: str

class CheckProgressDto(BaseModel):
    task_id: str


2010101
'2024-01-01','2024-12-31'