"""
Integration Types and Workflow Engine

This module provides extended integration types and a workflow engine for managing
complex integration scenarios across different systems and platforms.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class IntegrationType(Enum):
    """Extended integration types for different systems and platforms"""
    CRM = "crm"
    ERP = "erp"
    PAYMENT = "payment"
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    CALENDAR = "calendar"
    STORAGE = "storage"
    PRODUCTIVITY = "productivity"
    INDUSTRY = "industry"
    CUSTOM = "custom"
    DATABASE = "database"
    DOCUMENT = "document"
    NOTIFICATION = "notification"
    ANALYTICS = "analytics"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    MONITORING = "monitoring"
    BACKUP = "backup"
    API = "api"


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"


class StepType(Enum):
    """Workflow step types"""
    INTEGRATION = "integration"
    TRANSFORM = "transform"
    VALIDATE = "validate"
    CONDITION = "condition"
    DELAY = "delay"
    NOTIFICATION = "notification"
    CUSTOM = "custom"


@dataclass
class WorkflowStep:
    """Individual step in an integration workflow"""
    step_id: str
    name: str
    step_type: StepType
    config: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    timeout: int = 300  # seconds
    retry_count: int = 3
    retry_delay: int = 60  # seconds
    rollback_enabled: bool = True
    rollback_steps: List[str] = field(default_factory=list)


@dataclass
class WorkflowExecution:
    """Workflow execution context and state"""
    execution_id: str
    workflow_id: str
    status: WorkflowStatus
    context: Dict[str, Any]
    steps_executed: List[str] = field(default_factory=list)
    steps_failed: List[str] = field(default_factory=list)
    steps_rolled_back: List[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class IntegrationWorkflow:
    """Integration workflow definition and execution"""
    
    def __init__(self, workflow_id: str, name: str, description: str, steps: List[Dict[str, Any]]):
        self.workflow_id = workflow_id
        self.name = name
        self.description = description
        self.steps = self._parse_steps(steps)
        self.enabled = True
        self.version = "1.0"
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
    def _parse_steps(self, steps_config: List[Dict[str, Any]]) -> List[WorkflowStep]:
        """Parse workflow steps from configuration"""
        steps = []
        for i, step_config in enumerate(steps_config):
            step = WorkflowStep(
                step_id=step_config.get("step_id", f"step_{i+1}"),
                name=step_config.get("name", f"Step {i+1}"),
                step_type=StepType(step_config.get("type", "integration")),
                config=step_config.get("config", {}),
                dependencies=step_config.get("dependencies", []),
                timeout=step_config.get("timeout", 300),
                retry_count=step_config.get("retry_count", 3),
                retry_delay=step_config.get("retry_delay", 60),
                rollback_enabled=step_config.get("rollback_enabled", True),
                rollback_steps=step_config.get("rollback_steps", [])
            )
            steps.append(step)
        return steps
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow with given context"""
        execution_id = str(uuid4())
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=self.workflow_id,
            status=WorkflowStatus.PENDING,
            context=context.copy()
        )
        
        try:
            execution.status = WorkflowStatus.RUNNING
            execution.start_time = datetime.now()
            
            # Execute steps in dependency order
            executed_steps = []
            for step in self._get_ordered_steps():
                if await self._can_execute_step(step, executed_steps):
                    step_result = await self._execute_step(step, execution)
                    if step_result["success"]:
                        executed_steps.append(step.step_id)
                        execution.steps_executed.append(step.step_id)
                    else:
                        execution.steps_failed.append(step.step_id)
                        execution.error_message = step_result["error"]
                        execution.status = WorkflowStatus.FAILED
                        
                        # Rollback if enabled
                        if step.rollback_enabled:
                            await self._rollback_steps(executed_steps, execution)
                        
                        break
            
            if execution.status == WorkflowStatus.RUNNING:
                execution.status = WorkflowStatus.COMPLETED
                execution.result = {"steps_executed": len(executed_steps)}
            
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            logging.error(f"Workflow execution failed: {e}")
        
        finally:
            execution.end_time = datetime.now()
        
        return {
            "execution_id": execution_id,
            "workflow_id": self.workflow_id,
            "status": execution.status.value,
            "steps_executed": execution.steps_executed,
            "steps_failed": execution.steps_failed,
            "steps_rolled_back": execution.steps_rolled_back,
            "start_time": execution.start_time.isoformat() if execution.start_time else None,
            "end_time": execution.end_time.isoformat() if execution.end_time else None,
            "error_message": execution.error_message,
            "result": execution.result
        }
    
    async def validate(self, context: Dict[str, Any]) -> List[str]:
        """Validate workflow configuration and context"""
        errors = []
        
        # Validate workflow configuration
        if not self.workflow_id:
            errors.append("Workflow ID is required")
        
        if not self.name:
            errors.append("Workflow name is required")
        
        if not self.steps:
            errors.append("At least one step is required")
        
        # Validate steps
        step_ids = [step.step_id for step in self.steps]
        for step in self.steps:
            # Check for duplicate step IDs
            if step_ids.count(step.step_id) > 1:
                errors.append(f"Duplicate step ID: {step.step_id}")
            
            # Validate dependencies
            for dep in step.dependencies:
                if dep not in step_ids:
                    errors.append(f"Invalid dependency '{dep}' for step '{step.step_id}'")
            
            # Validate rollback steps
            for rollback_step in step.rollback_steps:
                if rollback_step not in step_ids:
                    errors.append(f"Invalid rollback step '{rollback_step}' for step '{step.step_id}'")
        
        # Validate context
        if not isinstance(context, dict):
            errors.append("Context must be a dictionary")
        
        return errors
    
    async def rollback(self, context: Dict[str, Any]) -> bool:
        """Rollback workflow execution"""
        try:
            # Execute rollback steps in reverse order
            rollback_steps = self._get_rollback_steps()
            for step in reversed(rollback_steps):
                await self._execute_rollback_step(step, context)
            return True
        except Exception as e:
            logging.error(f"Workflow rollback failed: {e}")
            return False
    
    def _get_ordered_steps(self) -> List[WorkflowStep]:
        """Get steps in dependency order using topological sort"""
        # Simple topological sort implementation
        steps_dict = {step.step_id: step for step in self.steps}
        visited = set()
        temp_visited = set()
        ordered_steps = []
        
        def visit(step_id: str):
            if step_id in temp_visited:
                raise ValueError(f"Circular dependency detected: {step_id}")
            if step_id in visited:
                return
            
            temp_visited.add(step_id)
            step = steps_dict[step_id]
            
            for dep in step.dependencies:
                visit(dep)
            
            temp_visited.remove(step_id)
            visited.add(step_id)
            ordered_steps.append(step)
        
        for step in self.steps:
            if step.step_id not in visited:
                visit(step.step_id)
        
        return ordered_steps
    
    async def _can_execute_step(self, step: WorkflowStep, executed_steps: List[str]) -> bool:
        """Check if a step can be executed based on dependencies"""
        return all(dep in executed_steps for dep in step.dependencies)
    
    async def _execute_step(self, step: WorkflowStep, execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute a single workflow step"""
        for attempt in range(step.retry_count + 1):
            try:
                if step.step_type == StepType.INTEGRATION:
                    return await self._execute_integration_step(step, execution.context)
                elif step.step_type == StepType.TRANSFORM:
                    return await self._execute_transform_step(step, execution.context)
                elif step.step_type == StepType.VALIDATE:
                    return await self._execute_validate_step(step, execution.context)
                elif step.step_type == StepType.CONDITION:
                    return await self._execute_condition_step(step, execution.context)
                elif step.step_type == StepType.DELAY:
                    return await self._execute_delay_step(step, execution.context)
                elif step.step_type == StepType.NOTIFICATION:
                    return await self._execute_notification_step(step, execution.context)
                elif step.step_type == StepType.CUSTOM:
                    return await self._execute_custom_step(step, execution.context)
                else:
                    return {"success": False, "error": f"Unknown step type: {step.step_type}"}
                    
            except Exception as e:
                if attempt < step.retry_count:
                    await asyncio.sleep(step.retry_delay)
                    continue
                else:
                    return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Max retry attempts exceeded"}
    
    async def _execute_integration_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute integration step"""
        integration_type = step.config.get("integration_type")
        integration_config = step.config.get("config", {})
        
        # This would integrate with actual integration providers
        # For now, simulate integration execution
        await asyncio.sleep(1)  # Simulate processing time
        
        return {
            "success": True,
            "step_id": step.step_id,
            "integration_type": integration_type,
            "result": {"status": "completed"}
        }
    
    async def _execute_transform_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data transformation step"""
        transform_config = step.config.get("transform", {})
        
        # Apply transformation to context data
        if "input_field" in transform_config and "output_field" in transform_config:
            input_value = context.get(transform_config["input_field"])
            if input_value:
                context[transform_config["output_field"]] = input_value
        
        return {
            "success": True,
            "step_id": step.step_id,
            "result": {"transformed": True}
        }
    
    async def _execute_validate_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute validation step"""
        validation_rules = step.config.get("rules", [])
        
        for rule in validation_rules:
            field = rule.get("field")
            condition = rule.get("condition")
            value = rule.get("value")
            
            if field and condition and value:
                field_value = context.get(field)
                if not self._validate_rule(field_value, condition, value):
                    return {
                        "success": False,
                        "step_id": step.step_id,
                        "error": f"Validation failed for field '{field}'"
                    }
        
        return {
            "success": True,
            "step_id": step.step_id,
            "result": {"validated": True}
        }
    
    async def _execute_condition_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute conditional step"""
        condition_config = step.config.get("condition", {})
        field = condition_config.get("field")
        operator = condition_config.get("operator")
        value = condition_config.get("value")
        
        if field and operator and value:
            field_value = context.get(field)
            result = self._evaluate_condition(field_value, operator, value)
            context["condition_result"] = result
            
            return {
                "success": True,
                "step_id": step.step_id,
                "result": {"condition_result": result}
            }
        
        return {
            "success": False,
            "step_id": step.step_id,
            "error": "Invalid condition configuration"
        }
    
    async def _execute_delay_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute delay step"""
        delay_seconds = step.config.get("delay_seconds", 1)
        await asyncio.sleep(delay_seconds)
        
        return {
            "success": True,
            "step_id": step.step_id,
            "result": {"delayed": delay_seconds}
        }
    
    async def _execute_notification_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute notification step"""
        notification_config = step.config.get("notification", {})
        notification_type = notification_config.get("type")
        
        # This would integrate with actual notification providers
        # For now, simulate notification sending
        await asyncio.sleep(0.5)  # Simulate processing time
        
        return {
            "success": True,
            "step_id": step.step_id,
            "result": {"notification_sent": True, "type": notification_type}
        }
    
    async def _execute_custom_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute custom step"""
        custom_config = step.config.get("custom", {})
        
        # This would execute custom logic
        # For now, simulate custom execution
        await asyncio.sleep(1)  # Simulate processing time
        
        return {
            "success": True,
            "step_id": step.step_id,
            "result": {"custom_executed": True}
        }
    
    def _validate_rule(self, field_value: Any, condition: str, value: Any) -> bool:
        """Validate a single rule"""
        if condition == "equals":
            return field_value == value
        elif condition == "not_equals":
            return field_value != value
        elif condition == "contains":
            return value in field_value if field_value else False
        elif condition == "greater_than":
            return field_value > value if field_value is not None else False
        elif condition == "less_than":
            return field_value < value if field_value is not None else False
        elif condition == "required":
            return field_value is not None and field_value != ""
        else:
            return False
    
    def _evaluate_condition(self, field_value: Any, operator: str, value: Any) -> bool:
        """Evaluate a condition"""
        if operator == "equals":
            return field_value == value
        elif operator == "not_equals":
            return field_value != value
        elif operator == "greater_than":
            return field_value > value if field_value is not None else False
        elif operator == "less_than":
            return field_value < value if field_value is not None else False
        elif operator == "contains":
            return value in field_value if field_value else False
        else:
            return False
    
    def _get_rollback_steps(self) -> List[WorkflowStep]:
        """Get steps that need to be rolled back"""
        rollback_steps = []
        for step in self.steps:
            if step.rollback_steps:
                rollback_steps.extend([s for s in self.steps if s.step_id in step.rollback_steps])
        return rollback_steps
    
    async def _execute_rollback_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute rollback for a step"""
        rollback_config = step.config.get("rollback", {})
        
        # This would execute rollback logic
        # For now, simulate rollback execution
        await asyncio.sleep(0.5)  # Simulate processing time
        
        return {
            "success": True,
            "step_id": step.step_id,
            "result": {"rolled_back": True}
        }
    
    async def _rollback_steps(self, executed_steps: List[str], execution: WorkflowExecution) -> None:
        """Rollback executed steps"""
        for step_id in reversed(executed_steps):
            step = next((s for s in self.steps if s.step_id == step_id), None)
            if step and step.rollback_enabled:
                try:
                    await self._execute_rollback_step(step, execution.context)
                    execution.steps_rolled_back.append(step_id)
                except Exception as e:
                    logging.error(f"Rollback failed for step {step_id}: {e}")


class IntegrationWorkflowEngine:
    """Engine for managing and executing integration workflows"""
    
    def __init__(self):
        self.workflows: Dict[str, IntegrationWorkflow] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.scheduled_workflows: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)
    
    async def register_workflow(self, workflow: IntegrationWorkflow) -> bool:
        """Register a new workflow"""
        try:
            # Validate workflow
            errors = await workflow.validate({})
            if errors:
                self.logger.error(f"Workflow validation failed: {errors}")
                return False
            
            self.workflows[workflow.workflow_id] = workflow
            self.logger.info(f"Workflow registered: {workflow.workflow_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to register workflow: {e}")
            return False
    
    async def execute_workflow(self, workflow_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow"""
        if workflow_id not in self.workflows:
            return {
                "success": False,
                "error": f"Workflow not found: {workflow_id}"
            }
        
        workflow = self.workflows[workflow_id]
        if not workflow.enabled:
            return {
                "success": False,
                "error": f"Workflow is disabled: {workflow_id}"
            }
        
        try:
            result = await workflow.execute(context)
            execution_id = result["execution_id"]
            self.executions[execution_id] = WorkflowExecution(
                execution_id=execution_id,
                workflow_id=workflow_id,
                status=WorkflowStatus(result["status"]),
                context=context,
                steps_executed=result["steps_executed"],
                steps_failed=result["steps_failed"],
                steps_rolled_back=result["steps_rolled_back"],
                start_time=datetime.fromisoformat(result["start_time"]) if result["start_time"] else None,
                end_time=datetime.fromisoformat(result["end_time"]) if result["end_time"] else None,
                error_message=result["error_message"],
                result=result["result"]
            )
            return result
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def schedule_workflow(self, workflow_id: str, schedule: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a workflow for execution"""
        if workflow_id not in self.workflows:
            return {
                "success": False,
                "error": f"Workflow not found: {workflow_id}"
            }
        
        schedule_id = str(uuid4())
        self.scheduled_workflows[schedule_id] = {
            "workflow_id": workflow_id,
            "schedule": schedule,
            "context": context,
            "created_at": datetime.now(),
            "next_execution": self._calculate_next_execution(schedule)
        }
        
        return {
            "success": True,
            "schedule_id": schedule_id,
            "next_execution": self.scheduled_workflows[schedule_id]["next_execution"].isoformat()
        }
    
    async def get_workflow_status(self, execution_id: str) -> Dict[str, Any]:
        """Get status of a workflow execution"""
        if execution_id not in self.executions:
            return {
                "success": False,
                "error": f"Execution not found: {execution_id}"
            }
        
        execution = self.executions[execution_id]
        return {
            "success": True,
            "execution_id": execution_id,
            "workflow_id": execution.workflow_id,
            "status": execution.status.value,
            "steps_executed": execution.steps_executed,
            "steps_failed": execution.steps_failed,
            "steps_rolled_back": execution.steps_rolled_back,
            "start_time": execution.start_time.isoformat() if execution.start_time else None,
            "end_time": execution.end_time.isoformat() if execution.end_time else None,
            "error_message": execution.error_message,
            "result": execution.result
        }
    
    async def list_workflows(self) -> List[Dict[str, Any]]:
        """List all registered workflows"""
        return [
            {
                "workflow_id": workflow.workflow_id,
                "name": workflow.name,
                "description": workflow.description,
                "enabled": workflow.enabled,
                "version": workflow.version,
                "steps_count": len(workflow.steps),
                "created_at": workflow.created_at.isoformat(),
                "updated_at": workflow.updated_at.isoformat()
            }
            for workflow in self.workflows.values()
        ]
    
    async def list_executions(self, workflow_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List workflow executions"""
        executions = []
        for execution in self.executions.values():
            if workflow_id is None or execution.workflow_id == workflow_id:
                executions.append({
                    "execution_id": execution.execution_id,
                    "workflow_id": execution.workflow_id,
                    "status": execution.status.value,
                    "start_time": execution.start_time.isoformat() if execution.start_time else None,
                    "end_time": execution.end_time.isoformat() if execution.end_time else None,
                    "error_message": execution.error_message
                })
        return executions
    
    def _calculate_next_execution(self, schedule: str) -> datetime:
        """Calculate next execution time based on schedule"""
        # Simple schedule parsing - in production, use cron or similar
        if schedule == "immediate":
            return datetime.now()
        elif schedule.startswith("delay:"):
            seconds = int(schedule.split(":")[1])
            return datetime.now() + timedelta(seconds=seconds)
        else:
            # Default to 1 hour from now
            return datetime.now() + timedelta(hours=1)













