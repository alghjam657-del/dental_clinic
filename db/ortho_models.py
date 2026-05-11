from dataclasses import dataclass
from typing import Optional

@dataclass
class OrthoPatient:
    id: int
    full_name: str
    phone: str
    start_date: str
    notes: Optional[str] = None
    created_at: str = ''

@dataclass
class OrthoInstallment:
    id: int
    ortho_patient_id: int
    due_date: str
    amount: float
    paid: bool = False
    paid_date: Optional[str] = None
    notes: Optional[str] = None
    created_at: str = ''
