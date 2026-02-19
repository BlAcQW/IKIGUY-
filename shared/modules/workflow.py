"""
Automation Workflow Base Class

This module provides the base class for automation workflows used across industry modules.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStepType(Enum):
    """Types of workflow steps"""
    CAPABILITY = "capability"
    INTEGRATION = "integration"
    CONDITION = "condition"
    DELAY = "delay"
    LOOP = "loop"
    PARALLEL = "parallel"
    WEBHOOK = "webhook"
    CUSTOM = "custom"


@dataclass
class WorkflowStep:
    """Individual workflow step definition"""
    step_id: str
    name: str
    step_type: WorkflowStepType
    config: Dict[str, Any]
    enabled: bool = True
    timeout: int = 300  # seconds
    retry_count: int = 3
    retry_delay: int = 5  # seconds
    depends_on: List[str] = field(default_factory=list)  # step dependencies


@dataclass
class WorkflowExecution:
    """Workflow execution context"""
    execution_id: str
    workflow_id: str
    status: WorkflowStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    params: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    step_results: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AutomationWorkflow:
    """Base class for automation workflows"""
    
    def __init__(self, workflow_id: str, name: str, description: str):
        """Initialize the workflow"""
        self.workflow_id = workflow_id
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"Workflow.{workflow_id}")
        self.steps: List[WorkflowStep] = []
        self.enabled: bool = True
        self.settings: Dict[str, Any] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow with given parameters"""
        execution_id = f"{self.workflow_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=self.workflow_id,
            status=WorkflowStatus.PENDING,
            start_time=datetime.now(),
            params=params
        )
        
        self.executions[execution_id] = execution
        
        try:
            # Validate parameters
            validation_errors = await self.validate_params(params)
            if validation_errors:
                execution.status = WorkflowStatus.FAILED
                execution.error_message = f"Parameter validation failed: {validation_errors}"
                return {
                    "success": False,
                    "execution_id": execution_id,
                    "error": execution.error_message,
                    "validation_errors": validation_errors
                }
            
            # Check required integrations
            required_integrations = await self.get_required_integrations()
            if required_integrations:
                # This would typically check if integrations are available
                pass
            
            # Execute workflow
            execution.status = WorkflowStatus.RUNNING
            result = await self._execute_workflow(execution)
            
            execution.status = WorkflowStatus.COMPLETED
            execution.end_time = datetime.now()
            execution.results = result
            
            return {
                "success": True,
                "execution_id": execution_id,
                "result": result,
                "execution_time": (execution.end_time - execution.start_time).total_seconds()
            }
            
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.end_time = datetime.now()
            execution.error_message = str(e)
            
            self.logger.error(f"Workflow execution failed: {e}", exc_info=True)
            
            return {
                "success": False,
                "execution_id": execution_id,
                "error": str(e),
                "execution_time": (execution.end_time - execution.start_time).total_seconds()
            }
    
    async def validate_params(self, params: Dict[str, Any]) -> List[str]:
        """Validate workflow parameters"""
        errors = []
        
        # Basic validation - subclasses can override for specific validation
        if not isinstance(params, dict):
            errors.append("Parameters must be a dictionary")
        
        # Check for required parameters if defined in settings
        required_params = self.settings.get("required_params", [])
        for param in required_params:
            if param not in params:
                errors.append(f"Required parameter '{param}' is missing")
        
        return errors
    
    async def get_required_integrations(self) -> List[str]:
        """Get list of required integrations for this workflow"""
        integrations = []
        
        for step in self.steps:
            if step.step_type == WorkflowStepType.INTEGRATION:
                integration_name = step.config.get("integration_name")
                if integration_name:
                    integrations.append(integration_name)
        
        return list(set(integrations))  # Remove duplicates
    
    async def _execute_workflow(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute the workflow steps"""
        step_results = {}
        
        # Sort steps by dependencies
        sorted_steps = self._sort_steps_by_dependencies()
        
        for step in sorted_steps:
            if not step.enabled:
                continue
                
            try:
                self.logger.info(f"Executing step: {step.name} ({step.step_id})")
                
                # Check dependencies
                if not self._check_step_dependencies(step, step_results):
                    raise ValueError(f"Step dependencies not met for {step.step_id}")
                
                # Execute step with retry logic
                step_result = await self._execute_step_with_retry(step, execution.params, step_results)
                step_results[step.step_id] = step_result
                execution.step_results[step.step_id] = step_result
                
                self.logger.info(f"Step completed: {step.name} ({step.step_id})")
                
            except Exception as e:
                self.logger.error(f"Step failed: {step.name} ({step.step_id}): {e}")
                step_results[step.step_id] = {
                    "success": False,
                    "error": str(e),
                    "step_id": step.step_id
                }
                execution.step_results[step.step_id] = step_results[step.step_id]
                
                # Check if step is critical
                if step.config.get("critical", False):
                    raise e
        
        return {
            "steps_executed": len(step_results),
            "step_results": step_results,
            "workflow_id": self.workflow_id,
            "execution_id": execution.execution_id
        }
    
    def _sort_steps_by_dependencies(self) -> List[WorkflowStep]:
        """Sort steps by their dependencies"""
        # Simple topological sort
        steps_dict = {step.step_id: step for step in self.steps}
        visited = set()
        temp_visited = set()
        sorted_steps = []
        
        def visit(step_id: str):
            if step_id in temp_visited:
                raise ValueError(f"Circular dependency detected: {step_id}")
            if step_id in visited:
                return
            
            temp_visited.add(step_id)
            step = steps_dict[step_id]
            
            for dep_id in step.depends_on:
                if dep_id in steps_dict:
                    visit(dep_id)
            
            temp_visited.remove(step_id)
            visited.add(step_id)
            sorted_steps.append(step)
        
        for step in self.steps:
            if step.step_id not in visited:
                visit(step.step_id)
        
        return sorted_steps
    
    def _check_step_dependencies(self, step: WorkflowStep, step_results: Dict[str, Any]) -> bool:
        """Check if step dependencies are met"""
        for dep_id in step.depends_on:
            if dep_id not in step_results:
                return False
            if not step_results[dep_id].get("success", False):
                return False
        return True
    
    async def _execute_step_with_retry(self, step: WorkflowStep, params: Dict[str, Any], step_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a step with retry logic"""
        last_error = None
        
        for attempt in range(step.retry_count + 1):
            try:
                result = await self._execute_single_step(step, params, step_results)
                return {
                    "success": True,
                    "result": result,
                    "step_id": step.step_id,
                    "attempt": attempt + 1
                }
                
            except Exception as e:
                last_error = e
                if attempt < step.retry_count:
                    self.logger.warning(f"Step {step.step_id} failed (attempt {attempt + 1}), retrying in {step.retry_delay}s: {e}")
                    await asyncio.sleep(step.retry_delay)
                else:
                    self.logger.error(f"Step {step.step_id} failed after {step.retry_count} retries: {e}")
        
        return {
            "success": False,
            "error": str(last_error),
            "step_id": step.step_id,
            "attempts": step.retry_count + 1
        }
    
    async def _execute_single_step(self, step: WorkflowStep, params: Dict[str, Any], step_results: Dict[str, Any]) -> Any:
        """Execute a single workflow step"""
        step_type = step.step_type
        config = step.config
        
        if step_type == WorkflowStepType.CAPABILITY:
            return await self._execute_capability_step(config, params, step_results)
        elif step_type == WorkflowStepType.INTEGRATION:
            return await self._execute_integration_step(config, params, step_results)
        elif step_type == WorkflowStepType.CONDITION:
            return await self._execute_condition_step(config, params, step_results)
        elif step_type == WorkflowStepType.DELAY:
            return await self._execute_delay_step(config, params, step_results)
        elif step_type == WorkflowStepType.LOOP:
            return await self._execute_loop_step(config, params, step_results)
        elif step_type == WorkflowStepType.PARALLEL:
            return await self._execute_parallel_step(config, params, step_results)
        elif step_type == WorkflowStepType.WEBHOOK:
            return await self._execute_webhook_step(config, params, step_results)
        elif step_type == WorkflowStepType.CUSTOM:
            return await self._execute_custom_step(config, params, step_results)
        else:
            raise ValueError(f"Unknown step type: {step_type}")
    
    async def _execute_capability_step(self, config: Dict[str, Any], params: Dict[str, Any], step_results: Dict[str, Any]) -> Any:
        """Execute a capability step"""
        capability_name = config.get("capability")
        if not capability_name:
            raise ValueError("Capability name not specified in step config")
        
        # This would typically call the parent module's execute_capability method
        # For now, return a placeholder
        return {
            "capability": capability_name,
            "status": "executed",
            "params": config.get("params", {})
        }
    
    async def _execute_integration_step(self, config: Dict[str, Any], params: Dict[str, Any], step_results: Dict[str, Any]) -> Any:
        """Execute an integration step"""
        integration_name = config.get("integration_name")
        integration_type = config.get("integration_type")
        
        if not integration_name:
            raise ValueError("Integration name not specified in step config")
        
        return {
            "integration": integration_name,
            "type": integration_type,
            "status": "executed",
            "params": config.get("params", {})
        }
    
    async def _execute_condition_step(self, config: Dict[str, Any], params: Dict[str, Any], step_results: Dict[str, Any]) -> Any:
        """Execute a condition step"""
        condition = config.get("condition")
        condition_type = config.get("condition_type", "simple")
        
        if not condition:
            raise ValueError("Condition not specified in step config")
        
        if condition_type == "simple":
            # Simple boolean condition evaluation
            result = eval(condition, {
                "params": params,
                "results": step_results,
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool
            })
            return {"condition_met": bool(result), "result": result}
        else:
            raise ValueError(f"Unknown condition type: {condition_type}")
    
    async def _execute_delay_step(self, config: Dict[str, Any], params: Dict[str, Any], step_results: Dict[str, Any]) -> Any:
        """Execute a delay step"""
        seconds = config.get("seconds", 0)
        if seconds > 0:
            await asyncio.sleep(seconds)
        return {"delayed": True, "seconds": seconds}
    
    async def _execute_loop_step(self, config: Dict[str, Any], params: Dict[str, Any], step_results: Dict[str, Any]) -> Any:
        """Execute a loop step"""
        loop_config = config.get("loop", {})
        loop_type = loop_config.get("type", "for")
        
        if loop_type == "for":
            items = loop_config.get("items", [])
            sub_steps = loop_config.get("steps", [])
            
            results = []
            for item in items:
                item_params = {**params, "loop_item": item}
                item_results = {}
                
                for sub_step_config in sub_steps:
                    sub_step = WorkflowStep(
                        step_id=f"loop_{len(results)}_{len(item_results)}",
                        name="loop_sub_step",
                        step_type=WorkflowStepType.CUSTOM,
                        config=sub_step_config
                    )
                    result = await self._execute_single_step(sub_step, item_params, item_results)
                    item_results[sub_step.step_id] = result
                
                results.append(item_results)
            
            return {"loop_results": results, "items_processed": len(items)}
        else:
            raise ValueError(f"Unknown loop type: {loop_type}")
    
    async def _execute_parallel_step(self, config: Dict[str, Any], params: Dict[str, Any], step_results: Dict[str, Any]) -> Any:
        """Execute parallel steps"""
        parallel_steps = config.get("steps", [])
        
        async def execute_parallel_step(step_config: Dict[str, Any], step_index: int):
            step = WorkflowStep(
                step_id=f"parallel_{step_index}",
                name="parallel_step",
                step_type=WorkflowStepType.CUSTOM,
                config=step_config
            )
            return await self._execute_single_step(step, params, step_results)
        
        # Execute all parallel steps concurrently
        tasks = [execute_parallel_step(step_config, i) for i, step_config in enumerate(parallel_steps)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "parallel_results": results,
            "steps_executed": len(parallel_steps)
        }
    
    async def _execute_webhook_step(self, config: Dict[str, Any], params: Dict[str, Any], step_results: Dict[str, Any]) -> Any:
        """Execute a webhook step"""
        url = config.get("url")
        method = config.get("method", "POST")
        headers = config.get("headers", {})
        body = config.get("body", {})
        
        if not url:
            raise ValueError("Webhook URL not specified in step config")
        
        # This would typically make an HTTP request
        # For now, return a placeholder
        return {
            "webhook": url,
            "method": method,
            "status": "executed",
            "headers": headers,
            "body": body
        }
    
    async def _execute_custom_step(self, config: Dict[str, Any], params: Dict[str, Any], step_results: Dict[str, Any]) -> Any:
        """Execute a custom step"""
        custom_type = config.get("custom_type")
        
        if not custom_type:
            raise ValueError("Custom type not specified in step config")
        
        # This would typically call a custom handler
        return {
            "custom_type": custom_type,
            "status": "executed",
            "params": config.get("params", {})
        }
    
    def add_step(self, step: WorkflowStep):
        """Add a step to the workflow"""
        self.steps.append(step)
    
    def remove_step(self, step_id: str):
        """Remove a step from the workflow"""
        self.steps = [step for step in self.steps if step.step_id != step_id]
    
    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get a step by ID"""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None
    
    def get_execution_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get execution status by ID"""
        return self.executions.get(execution_id)
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """Get workflow information"""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "steps_count": len(self.steps),
            "enabled_steps_count": len([s for s in self.steps if s.enabled]),
            "executions_count": len(self.executions),
            "settings": self.settings
        }
