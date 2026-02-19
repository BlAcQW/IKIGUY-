"""
Industry Modules Package

This package contains industry-specific modules for the KasaAI platform.
"""

from .base import (
    BaseIndustryModule,
    ModuleCapability,
    AutomationWorkflow,
    IntegrationPoint,
    ComplianceFramework
)

from .workflow import (
    AutomationWorkflow as WorkflowBase,
    WorkflowStep,
    WorkflowExecution,
    WorkflowStatus,
    WorkflowStepType
)

from .factory import (
    IndustryModuleFactory,
    get_factory,
    create_module,
    get_available_industries,
    get_industry_capabilities,
    validate_industry
)

from .api import router as modules_api_router

from .healthcare import HealthcareModule
from .financial import FinancialModule
from .retail import RetailModule
from .manufacturing import ManufacturingModule
from .telecom import TelecomModule
from .insurance import InsuranceModule

__all__ = [
    # Base classes
    "BaseIndustryModule",
    "ModuleCapability",
    "AutomationWorkflow",
    "IntegrationPoint",
    "ComplianceFramework",
    
    # Workflow components
    "WorkflowBase",
    "WorkflowStep",
    "WorkflowExecution",
    "WorkflowStatus",
    "WorkflowStepType",
    
    # Factory
    "IndustryModuleFactory",
    "get_factory",
    "create_module",
    "get_available_industries",
    "get_industry_capabilities",
    "validate_industry",
    
    # API
    "modules_api_router",
    
    # Industry modules
    "HealthcareModule",
    "FinancialModule",
    "RetailModule",
    "ManufacturingModule",
    "TelecomModule",
    "InsuranceModule"
]
