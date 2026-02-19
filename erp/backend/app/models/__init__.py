"""ERP Data Models."""

from .base import BaseModel
from .crm import Customer, Lead, Opportunity, Contact
from .hr import Employee, Payroll, Benefit, Recruitment
from .finance import Account, Transaction, Invoice, Expense, RecurrenceFrequency
from .project import Project, Task, Resource, Timesheet
from .bi import Report, Dashboard, KPI
from .system import Integration, Workflow, AuditLog
from .onboarding import EmployeeOnboarding, OnboardingTemplate
from .legal import LegalDocument, DocumentSignature

__all__ = [
    "BaseModel",
    # CRM
    "Customer",
    "Lead",
    "Opportunity",
    "Contact",
    # HR
    "Employee",
    "Payroll",
    "Benefit",
    "Recruitment",
    # Finance
    "Account",
    "Transaction",
    "Invoice",
    "Expense",
    "RecurrenceFrequency",
    # Projects
    "Project",
    "Task",
    "Resource",
    "Timesheet",
    # BI
    "Report",
    "Dashboard",
    "KPI",
    # System
    "Integration",
    "Workflow",
    "AuditLog",
    # Onboarding
    "EmployeeOnboarding",
    "OnboardingTemplate",
    # Legal
    "LegalDocument",
    "DocumentSignature",
]
