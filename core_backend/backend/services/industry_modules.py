"""
Industry Module Service for Core Backend.

This service provides business logic for managing industry-specific modules,
their capabilities, workflows, and analytics.
"""

from typing import Dict, List, Any, Optional
import logging
import asyncio
from datetime import datetime, timedelta

# Import shared modules
try:
    from apps.shared.modules.education import EducationModule
    from apps.shared.modules.hospitality import HospitalityModule
    from apps.shared.modules.utilities import UtilitiesModule
    from apps.shared.modules.real_estate import RealEstateModule
    from apps.shared.modules.professional_services import ProfessionalServicesModule
    from apps.shared.modules.automotive import AutomotiveModule
    from apps.shared.modules.healthcare import HealthcareModule
    from apps.shared.modules.financial import FinancialModule
    from apps.shared.modules.retail import RetailModule
    from apps.shared.modules.manufacturing import ManufacturingModule
    from apps.shared.modules.logistics import LogisticsModule
    from apps.shared.modules.telecom import TelecomModule
    from apps.shared.modules.government import GovernmentModule
    from apps.shared.modules.insurance import InsuranceModule
except ImportError as e:
    logging.warning(f"Some industry modules not available: {e}")

logger = logging.getLogger(__name__)


class IndustryModuleService:
    """Service for managing industry-specific modules."""

    def __init__(self):
        """Initialize the industry module service."""
        self._modules = {}
        self._module_cache = {}
        self._available_industries = [
            "education", "hospitality", "utilities", "real_estate",
            "professional_services", "automotive", "healthcare", "financial",
            "retail", "manufacturing", "logistics", "telecom", "government",
            "insurance"
        ]
        
        # Module class mapping
        self._module_classes = {
            "education": EducationModule,
            "hospitality": HospitalityModule,
            "utilities": UtilitiesModule,
            "real_estate": RealEstateModule,
            "professional_services": ProfessionalServicesModule,
            "automotive": AutomotiveModule,
            "healthcare": HealthcareModule,
            "financial": FinancialModule,
            "retail": RetailModule,
            "manufacturing": ManufacturingModule,
            "logistics": LogisticsModule,
            "telecom": TelecomModule,
            "government": GovernmentModule,
            "insurance": InsuranceModule,
        }

    async def initialize_module(
        self,
        tenant_id: str,
        industry: str,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Initialize an industry module for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            industry: Industry type
            settings: Module configuration settings
            
        Returns:
            Dict containing initialization results
        """
        try:
            if industry not in self._available_industries:
                raise ValueError(f"Unsupported industry: {industry}")
            
            if industry not in self._module_classes:
                raise ValueError(f"Module class not available for industry: {industry}")
            
            # Create module instance
            module_class = self._module_classes[industry]
            module = module_class()
            
            # Store module instance
            module_key = f"{industry}_{tenant_id}"
            self._modules[module_key] = module
            
            # Get module capabilities and workflows
            capabilities = await module.get_capabilities()
            workflows = await module.get_automation_workflows()
            
            logger.info(f"Initialized {industry} module for tenant {tenant_id}")
            
            return {
                "capabilities": capabilities,
                "workflows": workflows,
                "settings": settings,
                "initialized_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to initialize {industry} module for tenant {tenant_id}: {e}")
            raise

    async def execute_capability(
        self,
        tenant_id: str,
        industry: str,
        capability: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a specific capability of an industry module.
        
        Args:
            tenant_id: Tenant identifier
            industry: Industry type
            capability: Capability name to execute
            params: Execution parameters
            
        Returns:
            Dict containing execution results
        """
        try:
            module_key = f"{industry}_{tenant_id}"
            if module_key not in self._modules:
                await self.initialize_module(tenant_id, industry, {})
            
            module = self._modules[module_key]
            
            # Execute the capability
            if hasattr(module, f"execute_{capability}"):
                method = getattr(module, f"execute_{capability}")
                result = await method(**params)
            else:
                # Try generic capability execution
                result = await module.execute_capability(capability, params)
            
            logger.info(f"Executed capability {capability} for {industry} module, tenant {tenant_id}")
            
            return {
                "success": True,
                "capability": capability,
                "result": result,
                "executed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to execute capability {capability} for {industry} module: {e}")
            raise

    async def execute_workflow(
        self,
        tenant_id: str,
        industry: str,
        workflow: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a specific workflow of an industry module.
        
        Args:
            tenant_id: Tenant identifier
            industry: Industry type
            workflow: Workflow name to execute
            params: Execution parameters
            
        Returns:
            Dict containing workflow execution results
        """
        try:
            module_key = f"{industry}_{tenant_id}"
            if module_key not in self._modules:
                await self.initialize_module(tenant_id, industry, {})
            
            module = self._modules[module_key]
            
            # Execute the workflow
            workflows = await module.get_automation_workflows()
            workflow_config = next((w for w in workflows if w.get("id") == workflow), None)
            
            if not workflow_config:
                raise ValueError(f"Workflow {workflow} not found for {industry} module")
            
            # Execute workflow steps
            result = await module.execute_workflow(workflow, params)
            
            logger.info(f"Executed workflow {workflow} for {industry} module, tenant {tenant_id}")
            
            return {
                "success": True,
                "workflow": workflow,
                "result": result,
                "executed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to execute workflow {workflow} for {industry} module: {e}")
            raise

    async def get_module_capabilities(
        self,
        tenant_id: str,
        industry: str
    ) -> List[Dict[str, Any]]:
        """
        Get available capabilities for an industry module.
        
        Args:
            tenant_id: Tenant identifier
            industry: Industry type
            
        Returns:
            List of available capabilities
        """
        try:
            module_key = f"{industry}_{tenant_id}"
            if module_key not in self._modules:
                await self.initialize_module(tenant_id, industry, {})
            
            module = self._modules[module_key]
            capabilities = await module.get_capabilities()
            
            return capabilities
            
        except Exception as e:
            logger.error(f"Failed to get capabilities for {industry} module: {e}")
            raise

    async def get_module_workflows(
        self,
        tenant_id: str,
        industry: str
    ) -> List[Dict[str, Any]]:
        """
        Get available workflows for an industry module.
        
        Args:
            tenant_id: Tenant identifier
            industry: Industry type
            
        Returns:
            List of available workflows
        """
        try:
            module_key = f"{industry}_{tenant_id}"
            if module_key not in self._modules:
                await self.initialize_module(tenant_id, industry, {})
            
            module = self._modules[module_key]
            workflows = await module.get_automation_workflows()
            
            return workflows
            
        except Exception as e:
            logger.error(f"Failed to get workflows for {industry} module: {e}")
            raise

    async def get_module_analytics(
        self,
        tenant_id: str,
        industry: str,
        metrics: List[str],
        time_range: str = "7d",
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get analytics data for an industry module.
        
        Args:
            tenant_id: Tenant identifier
            industry: Industry type
            metrics: List of metrics to retrieve
            time_range: Time range for analytics
            filters: Optional filters
            
        Returns:
            Dict containing analytics data
        """
        try:
            module_key = f"{industry}_{tenant_id}"
            if module_key not in self._modules:
                await self.initialize_module(tenant_id, industry, {})
            
            module = self._modules[module_key]
            
            # Get industry-specific analytics
            analytics = await module.get_industry_specific_analytics()
            
            # Filter by requested metrics
            filtered_analytics = {}
            for metric in metrics:
                if metric in analytics:
                    filtered_analytics[metric] = analytics[metric]
            
            return {
                "industry": industry,
                "metrics": filtered_analytics,
                "time_range": time_range,
                "filters": filters or {},
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get analytics for {industry} module: {e}")
            raise

    async def get_module_compliance(
        self,
        tenant_id: str,
        industry: str
    ) -> Dict[str, Any]:
        """
        Get compliance information for an industry module.
        
        Args:
            tenant_id: Tenant identifier
            industry: Industry type
            
        Returns:
            Dict containing compliance information
        """
        try:
            module_key = f"{industry}_{tenant_id}"
            if module_key not in self._modules:
                await self.initialize_module(tenant_id, industry, {})
            
            module = self._modules[module_key]
            
            # Get compliance frameworks
            compliance = await module.get_compliance_frameworks()
            
            return {
                "industry": industry,
                "compliance_frameworks": compliance,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get compliance for {industry} module: {e}")
            raise

    async def get_module_integrations(
        self,
        tenant_id: str,
        industry: str
    ) -> Dict[str, Any]:
        """
        Get integration points for an industry module.
        
        Args:
            tenant_id: Tenant identifier
            industry: Industry type
            
        Returns:
            Dict containing integration points
        """
        try:
            module_key = f"{industry}_{tenant_id}"
            if module_key not in self._modules:
                await self.initialize_module(tenant_id, industry, {})
            
            module = self._modules[module_key]
            
            # Get integration points
            integrations = await module.get_integration_points()
            
            return {
                "industry": industry,
                "integration_points": integrations,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get integrations for {industry} module: {e}")
            raise

    async def get_module_health(
        self,
        tenant_id: str,
        industry: str
    ) -> Dict[str, Any]:
        """
        Get health status for an industry module.
        
        Args:
            tenant_id: Tenant identifier
            industry: Industry type
            
        Returns:
            Dict containing health status
        """
        try:
            module_key = f"{industry}_{tenant_id}"
            
            # Check if module is initialized
            if module_key not in self._modules:
                return {
                    "status": "not_initialized",
                    "message": f"Module {industry} not initialized for tenant {tenant_id}",
                    "last_check": datetime.utcnow().isoformat()
                }
            
            module = self._modules[module_key]
            
            # Perform health checks
            health_status = {
                "status": "healthy",
                "module_id": module_key,
                "industry": industry,
                "capabilities_count": len(await module.get_capabilities()),
                "workflows_count": len(await module.get_automation_workflows()),
                "last_check": datetime.utcnow().isoformat()
            }
            
            return health_status
            
        except Exception as e:
            logger.error(f"Failed to get health for {industry} module: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }

    async def get_available_industries(self) -> List[Dict[str, Any]]:
        """
        Get list of available industry modules.
        
        Returns:
            List of available industries with their information
        """
        try:
            industries = []
            
            for industry in self._available_industries:
                if industry in self._module_classes:
                    # Try to get module info
                    try:
                        module_class = self._module_classes[industry]
                        module = module_class()
                        
                        industries.append({
                            "id": industry,
                            "name": module.name,
                            "description": module.description,
                            "category": module.category,
                            "available": True
                        })
                    except Exception as e:
                        logger.warning(f"Could not get info for {industry} module: {e}")
                        industries.append({
                            "id": industry,
                            "name": industry.replace("_", " ").title(),
                            "description": f"{industry.replace('_', ' ').title()} industry module",
                            "category": industry,
                            "available": False
                        })
                else:
                    industries.append({
                        "id": industry,
                        "name": industry.replace("_", " ").title(),
                        "description": f"{industry.replace('_', ' ').title()} industry module",
                        "category": industry,
                        "available": False
                    })
            
            return industries
            
        except Exception as e:
            logger.error(f"Failed to get available industries: {e}")
            raise
