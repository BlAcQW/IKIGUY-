"""
Industry Module Factory

This module provides a factory for creating and managing industry-specific modules.
"""

import logging
from typing import Dict, List, Optional, Type, Any
from .base import BaseIndustryModule, ModuleCapability
from .healthcare import HealthcareModule
from .financial import FinancialModule
from .retail import RetailModule
from .manufacturing import ManufacturingModule
from .telecom import TelecomModule
from .insurance import InsuranceModule
from .real_estate import RealEstateModule
from .education import EducationModule
from .professional_services import ProfessionalServicesModule
from .automotive import AutomotiveModule
from .hospitality import HospitalityModule
from .utilities import UtilitiesModule
from .logistics import LogisticsModule


class IndustryModuleFactory:
    """Factory for creating and managing industry modules"""
    
    def __init__(self):
        """Initialize the factory"""
        self.logger = logging.getLogger("IndustryModuleFactory")
        self._modules: Dict[str, Type[BaseIndustryModule]] = {}
        self._instances: Dict[str, BaseIndustryModule] = {}
        self._register_default_modules()
    
    def _register_default_modules(self):
        """Register the default industry modules"""
        self.register_module("healthcare", HealthcareModule)
        self.register_module("financial", FinancialModule)
        self.register_module("retail", RetailModule)
        self.register_module("manufacturing", ManufacturingModule)
        self.register_module("telecom", TelecomModule)
        self.register_module("insurance", InsuranceModule)
        self.register_module("real_estate", RealEstateModule)
        self.register_module("education", EducationModule)
        self.register_module("professional_services", ProfessionalServicesModule)
        self.register_module("automotive", AutomotiveModule)
        self.register_module("hospitality", HospitalityModule)
        self.register_module("utilities", UtilitiesModule)
        self.register_module("logistics", LogisticsModule)
    
    def register_module(self, industry: str, module_class: Type[BaseIndustryModule]):
        """Register a new industry module"""
        if not issubclass(module_class, BaseIndustryModule):
            raise ValueError(f"Module class must inherit from BaseIndustryModule")
        
        self._modules[industry] = module_class
        self.logger.info(f"Registered module for industry: {industry}")
    
    @staticmethod
    def create_module(industry: str, tenant_id: str) -> BaseIndustryModule:
        """Create a module instance for a specific industry and tenant"""
        factory = IndustryModuleFactory()
        return factory._create_module_instance(industry, tenant_id)
    
    def _create_module_instance(self, industry: str, tenant_id: str) -> BaseIndustryModule:
        """Create a module instance"""
        if industry not in self._modules:
            raise ValueError(f"No module registered for industry: {industry}")
        
        module_class = self._modules[industry]
        instance_key = f"{industry}_{tenant_id}"
        
        if instance_key in self._instances:
            return self._instances[instance_key]
        
        # Create new instance
        instance = module_class()
        self._instances[instance_key] = instance
        
        self.logger.info(f"Created module instance for {industry} (tenant: {tenant_id})")
        return instance
    
    @staticmethod
    def get_available_industries() -> List[str]:
        """Get list of available industries"""
        factory = IndustryModuleFactory()
        return list(factory._modules.keys())
    
    @staticmethod
    def get_industry_capabilities(industry: str) -> List[ModuleCapability]:
        """Get capabilities for a specific industry"""
        factory = IndustryModuleFactory()
        return factory._get_industry_capabilities(industry)
    
    def _get_industry_capabilities(self, industry: str) -> List[ModuleCapability]:
        """Get capabilities for a specific industry"""
        if industry not in self._modules:
            raise ValueError(f"No module registered for industry: {industry}")
        
        # Create a temporary instance to get capabilities
        module_class = self._modules[industry]
        temp_instance = module_class()
        
        # This would typically call the async method, but for factory we'll use sync version
        # In a real implementation, you might want to cache this information
        return temp_instance.capabilities
    
    def get_module_info(self, industry: str) -> Dict[str, Any]:
        """Get information about a specific industry module"""
        if industry not in self._modules:
            raise ValueError(f"No module registered for industry: {industry}")
        
        module_class = self._modules[industry]
        temp_instance = module_class()
        
        return {
            "industry": industry,
            "module_id": temp_instance.module_id,
            "name": temp_instance.name,
            "description": temp_instance.description,
            "category": temp_instance.category,
            "capabilities_count": len(temp_instance.capabilities),
            "automation_workflows_count": len(temp_instance.automation_workflows),
            "integration_points_count": len(temp_instance.integration_points),
            "compliance_frameworks_count": len(temp_instance.compliance_frameworks)
        }
    
    def get_all_modules_info(self) -> List[Dict[str, Any]]:
        """Get information about all registered modules"""
        return [self.get_module_info(industry) for industry in self._modules.keys()]
    
    def validate_industry(self, industry: str) -> bool:
        """Validate if an industry is supported"""
        return industry in self._modules
    
    def get_supported_industries(self) -> List[str]:
        """Get list of supported industries"""
        return list(self._modules.keys())
    
    def get_module_class(self, industry: str) -> Type[BaseIndustryModule]:
        """Get the module class for a specific industry"""
        if industry not in self._modules:
            raise ValueError(f"No module registered for industry: {industry}")
        
        return self._modules[industry]
    
    def unregister_module(self, industry: str):
        """Unregister a module for an industry"""
        if industry in self._modules:
            del self._modules[industry]
            
            # Remove any existing instances
            instances_to_remove = [key for key in self._instances.keys() if key.startswith(f"{industry}_")]
            for key in instances_to_remove:
                del self._instances[key]
            
            self.logger.info(f"Unregistered module for industry: {industry}")
    
    def clear_instances(self):
        """Clear all module instances"""
        self._instances.clear()
        self.logger.info("Cleared all module instances")
    
    def get_instance_count(self) -> int:
        """Get the number of active module instances"""
        return len(self._instances)
    
    def get_instance_info(self) -> List[Dict[str, Any]]:
        """Get information about all active instances"""
        info = []
        for key, instance in self._instances.items():
            industry, tenant_id = key.split("_", 1)
            info.append({
                "instance_key": key,
                "industry": industry,
                "tenant_id": tenant_id,
                "module_id": instance.module_id,
                "status": instance.status,
                "capabilities_count": len(instance.capabilities),
                "automation_workflows_count": len(instance.automation_workflows)
            })
        return info


# Global factory instance
_global_factory: Optional[IndustryModuleFactory] = None


def get_factory() -> IndustryModuleFactory:
    """Get the global factory instance"""
    global _global_factory
    if _global_factory is None:
        _global_factory = IndustryModuleFactory()
    return _global_factory


def create_module(industry: str, tenant_id: str) -> BaseIndustryModule:
    """Create a module using the global factory"""
    return get_factory()._create_module_instance(industry, tenant_id)


def get_available_industries() -> List[str]:
    """Get available industries using the global factory"""
    return get_factory().get_available_industries()


def get_industry_capabilities(industry: str) -> List[ModuleCapability]:
    """Get industry capabilities using the global factory"""
    return get_factory()._get_industry_capabilities(industry)


def validate_industry(industry: str) -> bool:
    """Validate industry using the global factory"""
    return get_factory().validate_industry(industry)
