"""
Base Module Class

This module provides the base class for all industry-specific modules.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from apps.shared.config.interfaces import ModuleInfo, ModuleInstance


@dataclass
class ModuleCapability:
    """Module capability definition"""
    name: str
    description: str
    enabled: bool = True
    settings: Dict[str, Any] = None


@dataclass
class AutomationWorkflow:
    """Automation workflow definition"""
    workflow_id: str
    name: str
    description: str
    steps: List[Dict[str, Any]]
    enabled: bool = True
    settings: Dict[str, Any] = None


@dataclass
class IntegrationPoint:
    """Integration point definition"""
    name: str
    type: str  # 'email', 'sms', 'whatsapp', 'calendar', 'database', 'api', etc.
    description: str
    enabled: bool = True
    settings: Dict[str, Any] = None


@dataclass
class ComplianceFramework:
    """Compliance framework definition"""
    name: str
    version: str
    description: str
    requirements: List[str]
    enabled: bool = True


class BaseIndustryModule(ABC):
    """Base class for all industry-specific modules"""
    
    def __init__(self, module_id: str, name: str, description: str, category: str):
        """Initialize the base module"""
        self.module_id = module_id
        self.name = name
        self.description = description
        self.category = category
        self.logger = logging.getLogger(f"Module.{module_id}")
        self.capabilities: List[ModuleCapability] = []
        self.automation_workflows: List[AutomationWorkflow] = []
        self.integration_points: List[IntegrationPoint] = []
        self.compliance_frameworks: List[ComplianceFramework] = []
        self.settings: Dict[str, Any] = {}
        self.status = "inactive"
        self.error_message: Optional[str] = None
        
    @abstractmethod
    async def initialize(self, tenant_id: str, settings: Dict[str, Any]) -> bool:
        """Initialize the module for a tenant"""
        pass
        
    @abstractmethod
    async def shutdown(self) -> bool:
        """Shutdown the module"""
        pass
        
    @abstractmethod
    async def get_capabilities(self) -> List[ModuleCapability]:
        """Get module capabilities"""
        pass
        
    @abstractmethod
    async def execute_capability(self, capability_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a module capability"""
        pass
        
    @abstractmethod
    async def validate_settings(self, settings: Dict[str, Any]) -> List[str]:
        """Validate module settings"""
        pass
        
    @abstractmethod
    async def get_compliance_info(self) -> Dict[str, Any]:
        """Get compliance information for the module"""
        pass

    # New abstract methods for Task 1.1.1
    @abstractmethod
    async def get_automation_workflows(self) -> List[Dict[str, Any]]:
        """Get automation workflows for the module"""
        pass

    @abstractmethod
    async def get_integration_points(self) -> List[Dict[str, Any]]:
        """Get integration points for the module"""
        pass

    @abstractmethod
    async def get_compliance_frameworks(self) -> List[Dict[str, Any]]:
        """Get compliance frameworks for the module"""
        pass

    @abstractmethod
    async def get_industry_specific_analytics(self) -> Dict[str, Any]:
        """Get industry-specific analytics for the module"""
        pass

    # New methods for automation workflow execution
    async def execute_workflow(self, workflow_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an automation workflow"""
        try:
            workflow = next((w for w in self.automation_workflows if w.workflow_id == workflow_id), None)
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            if not workflow.enabled:
                raise ValueError(f"Workflow {workflow_id} is disabled")
            
            self.log_activity("workflow_execution_started", {
                "workflow_id": workflow_id,
                "params": params
            })
            
            result = await self._execute_workflow_steps(workflow, params)
            
            self.log_activity("workflow_execution_completed", {
                "workflow_id": workflow_id,
                "result": result
            })
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.log_error(f"Workflow execution failed: {e}", {
                "workflow_id": workflow_id,
                "params": params
            })
            return {
                "success": False,
                "workflow_id": workflow_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _execute_workflow_steps(self, workflow: AutomationWorkflow, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow steps"""
        results = []
        
        for step in workflow.steps:
            step_type = step.get("type")
            step_config = step.get("config", {})
            
            if step_type == "capability":
                result = await self.execute_capability(step_config["capability"], params)
                results.append({"step": step, "result": result})
            elif step_type == "integration":
                result = await self._execute_integration_step(step_config, params)
                results.append({"step": step, "result": result})
            elif step_type == "condition":
                result = await self._execute_condition_step(step_config, params, results)
                results.append({"step": step, "result": result})
            elif step_type == "delay":
                await asyncio.sleep(step_config.get("seconds", 0))
                results.append({"step": step, "result": {"delayed": True}})
            else:
                raise ValueError(f"Unknown workflow step type: {step_type}")
        
        return {
            "steps_executed": len(results),
            "results": results
        }

    async def _execute_integration_step(self, config: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an integration step"""
        integration_type = config.get("integration_type")
        integration_name = config.get("integration_name")
        
        # This will be implemented by subclasses based on their specific integrations
        return {
            "integration_type": integration_type,
            "integration_name": integration_name,
            "status": "not_implemented"
        }

    async def _execute_condition_step(self, config: Dict[str, Any], params: Dict[str, Any], previous_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a condition step"""
        condition = config.get("condition")
        condition_type = config.get("condition_type", "simple")
        
        if condition_type == "simple":
            # Simple boolean condition
            result = eval(condition, {"params": params, "results": previous_results})
            return {"condition_met": bool(result)}
        else:
            raise ValueError(f"Unknown condition type: {condition_type}")

    # New methods for integration point management
    async def test_integration(self, integration_name: str) -> Dict[str, Any]:
        """Test an integration point"""
        try:
            integration = next((i for i in self.integration_points if i.name == integration_name), None)
            if not integration:
                raise ValueError(f"Integration {integration_name} not found")
            
            if not integration.enabled:
                raise ValueError(f"Integration {integration_name} is disabled")
            
            # This will be implemented by subclasses
            result = await self._test_integration_point(integration)
            
            return {
                "success": True,
                "integration_name": integration_name,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "integration_name": integration_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _test_integration_point(self, integration: IntegrationPoint) -> Dict[str, Any]:
        """Test a specific integration point - to be implemented by subclasses"""
        return {
            "status": "not_implemented",
            "integration_type": integration.type
        }

    # New methods for compliance framework management
    async def validate_compliance(self, framework_name: str) -> Dict[str, Any]:
        """Validate compliance with a specific framework"""
        try:
            framework = next((f for f in self.compliance_frameworks if f.name == framework_name), None)
            if not framework:
                raise ValueError(f"Compliance framework {framework_name} not found")
            
            if not framework.enabled:
                raise ValueError(f"Compliance framework {framework_name} is disabled")
            
            # This will be implemented by subclasses
            result = await self._validate_compliance_framework(framework)
            
            return {
                "success": True,
                "framework_name": framework_name,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "framework_name": framework_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _validate_compliance_framework(self, framework: ComplianceFramework) -> Dict[str, Any]:
        """Validate a specific compliance framework - to be implemented by subclasses"""
        return {
            "status": "not_implemented",
            "framework_name": framework.name,
            "version": framework.version
        }

    # Enhanced analytics method
    async def get_enhanced_analytics(self) -> Dict[str, Any]:
        """Get enhanced analytics including industry-specific metrics"""
        try:
            base_metrics = await self.get_metrics()
            industry_analytics = await self.get_industry_specific_analytics()
            
            return {
                **base_metrics,
                "industry_analytics": industry_analytics,
                "automation_workflows_count": len(self.automation_workflows),
                "enabled_workflows_count": len([w for w in self.automation_workflows if w.enabled]),
                "integration_points_count": len(self.integration_points),
                "enabled_integrations_count": len([i for i in self.integration_points if i.enabled]),
                "compliance_frameworks_count": len(self.compliance_frameworks),
                "enabled_frameworks_count": len([f for f in self.compliance_frameworks if f.enabled])
            }
        except Exception as e:
            self.log_error(f"Analytics generation failed: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        
    def get_module_info(self) -> ModuleInfo:
        """Get module information"""
        return ModuleInfo(
            module_id=self.module_id,
            name=self.name,
            version="1.0.0",
            description=self.description,
            author="KasaAI",
            license="MIT",
            dependencies=self.get_dependencies(),
            permissions=self.get_permissions(),
            features=self.get_features(),
            api_endpoints=self.get_api_endpoints(),
            ui_components=self.get_ui_components(),
            category=self.category,
            tags=self.get_tags()
        )
        
    def get_dependencies(self) -> List[str]:
        """Get module dependencies"""
        return []
        
    def get_permissions(self) -> List[str]:
        """Get required permissions"""
        return [f"{self.module_id}:read", f"{self.module_id}:write"]
        
    def get_features(self) -> List[str]:
        """Get provided features"""
        return [cap.name for cap in self.capabilities if cap.enabled]
        
    def get_api_endpoints(self) -> List[str]:
        """Get API endpoints"""
        return [f"/api/{self.module_id}/*"]
        
    def get_ui_components(self) -> List[str]:
        """Get UI components"""
        return [f"{self.name}Dashboard", f"{self.name}Configuration"]
        
    def get_tags(self) -> List[str]:
        """Get module tags"""
        return [self.category, "industry", "specialized"]
        
    async def health_check(self) -> Dict[str, Any]:
        """Perform module health check"""
        try:
            return {
                "status": "healthy",
                "module_id": self.module_id,
                "timestamp": datetime.now().isoformat(),
                "capabilities": len(self.capabilities),
                "active_capabilities": len([c for c in self.capabilities if c.enabled]),
                "automation_workflows": len(self.automation_workflows),
                "active_workflows": len([w for w in self.automation_workflows if w.enabled]),
                "integration_points": len(self.integration_points),
                "active_integrations": len([i for i in self.integration_points if i.enabled])
            }
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "module_id": self.module_id,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
            
    async def get_metrics(self) -> Dict[str, Any]:
        """Get module metrics"""
        return {
            "module_id": self.module_id,
            "capabilities_count": len(self.capabilities),
            "enabled_capabilities": len([c for c in self.capabilities if c.enabled]),
            "status": self.status,
            "last_activity": datetime.now().isoformat()
        }
        
    def log_activity(self, activity: str, details: Dict[str, Any] = None):
        """Log module activity"""
        self.logger.info(f"Activity: {activity}", extra=details or {})
        
    def log_error(self, error: str, details: Dict[str, Any] = None):
        """Log module error"""
        self.logger.error(f"Error: {error}", extra=details or {})
        self.error_message = error
        self.status = "error"
