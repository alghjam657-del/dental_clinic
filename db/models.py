"""
نماذج البيانات - Data Models
تعريف هياكل البيانات المستخدمة في النظام
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class User:
    id: int
    username: str
    full_name: str
    role: str
    created_at: str


@dataclass
class Patient:
    id: int
    full_name: str
    phone: str
    email: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: str = 'male'
    address: Optional[str] = None
    notes: Optional[str] = None
    created_at: str = ''


@dataclass
class MedicalRecord:
    id: int
    patient_id: int
    visit_date: str
    diagnosis: str
    treatment: Optional[str] = None
    tooth_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: str = ''


@dataclass
class TreatmentPlan:
    id: int
    patient_id: int
    description: str
    total_cost: float
    initial_payment: float
    installments_count: int
    amount_paid: float
    status: str = 'active'
    created_at: str = ''

    @property
    def remaining(self):
        return self.total_cost - self.amount_paid


@dataclass
class Payment:
    id: int
    patient_id: int
    amount: float
    payment_date: str
    payment_method: str = 'cash'
    treatment_plan_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: str = ''


@dataclass
class Appointment:
    id: int
    patient_id: int
    appointment_date: str
    appointment_time: str
    duration_minutes: int = 30
    status: str = 'scheduled'
    notes: Optional[str] = None
    created_at: str = ''
