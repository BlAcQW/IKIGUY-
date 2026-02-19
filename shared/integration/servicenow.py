"""
ServiceNow Integration Module

This module provides integration with ServiceNow for IT service management, incident management,
and enterprise workflow automation with comprehensive REST API support.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

try:
    import requests
    SERVICENOW_AVAILABLE = True
except ImportError:
    SERVICENOW_AVAILABLE = False
    logging.warning("ServiceNow APIs not available. Install requests")

logger = logging.getLogger(__name__)


class ServiceNowPriority(Enum):
    """ServiceNow priority levels."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    PLANNING = 5


class ServiceNowState(Enum):
    """ServiceNow state values."""
    NEW = 1
    IN_PROGRESS = 2
    ON_HOLD = 3
    RESOLVED = 4
    CLOSED = 5
    CANCELLED = 6


class ServiceNowCategory(Enum):
    """ServiceNow categories."""
    SOFTWARE = "software"
    HARDWARE = "hardware"
    NETWORK = "network"
    DATABASE = "database"
    SECURITY = "security"
    USER_SERVICE = "user_service"
    INFRASTRUCTURE = "infrastructure"
    OTHER = "other"


class ServiceNowImpact(Enum):
    """ServiceNow impact levels."""
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class ServiceNowUrgency(Enum):
    """ServiceNow urgency levels."""
    HIGH = 1
    MEDIUM = 2
    LOW = 3


@dataclass
class ServiceNowConfig:
    """Configuration for ServiceNow integration."""
    
    instance_url: str
    """ServiceNow instance URL (e.g., 'https://company.service-now.com')."""
    
    username: str
    """ServiceNow username."""
    
    password: str
    """ServiceNow password."""
    
    client_id: Optional[str] = None
    """OAuth client ID (for OAuth authentication)."""
    
    client_secret: Optional[str] = None
    """OAuth client secret (for OAuth authentication)."""
    
    timeout: int = 30
    """Request timeout in seconds."""
    
    verify_ssl: bool = True
    """Verify SSL certificates."""
    
    api_version: str = "v2"
    """API version to use."""


@dataclass
class ServiceNowIncident:
    """ServiceNow incident data structure."""
    
    sys_id: Optional[str] = None
    """System ID."""
    
    number: Optional[str] = None
    """Incident number."""
    
    short_description: str
    """Short description."""
    
    description: str
    """Description."""
    
    category: ServiceNowCategory = ServiceNowCategory.OTHER
    """Category."""
    
    subcategory: Optional[str] = None
    """Subcategory."""
    
    priority: ServiceNowPriority = ServiceNowPriority.MEDIUM
    """Priority."""
    
    impact: ServiceNowImpact = ServiceNowImpact.MEDIUM
    """Impact."""
    
    urgency: ServiceNowUrgency = ServiceNowUrgency.MEDIUM
    """Urgency."""
    
    state: ServiceNowState = ServiceNowState.NEW
    """State."""
    
    assigned_to: Optional[str] = None
    """Assigned to."""
    
    caller_id: str
    """Caller ID."""
    
    opened_by: Optional[str] = None
    """Opened by."""
    
    opened_at: Optional[datetime] = None
    """Opened at."""
    
    resolved_at: Optional[datetime] = None
    """Resolved at."""
    
    closed_at: Optional[datetime] = None
    """Closed at."""
    
    resolved_by: Optional[str] = None
    """Resolved by."""
    
    closed_by: Optional[str] = None
    """Closed by."""
    
    close_notes: Optional[str] = None
    """Close notes."""
    
    resolution_notes: Optional[str] = None
    """Resolution notes."""
    
    business_service: Optional[str] = None
    """Business service."""
    
    cmdb_ci: Optional[str] = None
    """Configuration item."""
    
    location: Optional[str] = None
    """Location."""
    
    company: Optional[str] = None
    """Company."""
    
    department: Optional[str] = None
    """Department."""
    
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    """Custom fields."""


@dataclass
class ServiceNowChangeRequest:
    """ServiceNow change request data structure."""
    
    sys_id: Optional[str] = None
    """System ID."""
    
    number: Optional[str] = None
    """Change request number."""
    
    short_description: str
    """Short description."""
    
    description: str
    """Description."""
    
    category: ServiceNowCategory = ServiceNowCategory.OTHER
    """Category."""
    
    priority: ServiceNowPriority = ServiceNowPriority.MEDIUM
    """Priority."""
    
    impact: ServiceNowImpact = ServiceNowImpact.MEDIUM
    """Impact."""
    
    urgency: ServiceNowUrgency = ServiceNowUrgency.MEDIUM
    """Urgency."""
    
    state: ServiceNowState = ServiceNowState.NEW
    """State."""
    
    requested_by: str
    """Requested by."""
    
    assigned_to: Optional[str] = None
    """Assigned to."""
    
    change_type: Optional[str] = None
    """Change type."""
    
    risk: Optional[str] = None
    """Risk."""
    
    business_justification: Optional[str] = None
    """Business justification."""
    
    implementation_plan: Optional[str] = None
    """Implementation plan."""
    
    test_plan: Optional[str] = None
    """Test plan."""
    
    backout_plan: Optional[str] = None
    """Backout plan."""
    
    scheduled_start: Optional[datetime] = None
    """Scheduled start."""
    
    scheduled_end: Optional[datetime] = None
    """Scheduled end."""
    
    actual_start: Optional[datetime] = None
    """Actual start."""
    
    actual_end: Optional[datetime] = None
    """Actual end."""
    
    opened_at: Optional[datetime] = None
    """Opened at."""
    
    closed_at: Optional[datetime] = None
    """Closed at."""
    
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    """Custom fields."""


@dataclass
class ServiceNowProblem:
    """ServiceNow problem data structure."""
    
    sys_id: Optional[str] = None
    """System ID."""
    
    number: Optional[str] = None
    """Problem number."""
    
    short_description: str
    """Short description."""
    
    description: str
    """Description."""
    
    category: ServiceNowCategory = ServiceNowCategory.OTHER
    """Category."""
    
    priority: ServiceNowPriority = ServiceNowPriority.MEDIUM
    """Priority."""
    
    impact: ServiceNowImpact = ServiceNowImpact.MEDIUM
    """Impact."""
    
    urgency: ServiceNowUrgency = ServiceNowUrgency.MEDIUM
    """Urgency."""
    
    state: ServiceNowState = ServiceNowState.NEW
    """State."""
    
    assigned_to: Optional[str] = None
    """Assigned to."""
    
    opened_by: str
    """Opened by."""
    
    problem_state: Optional[str] = None
    """Problem state."""
    
    root_cause: Optional[str] = None
    """Root cause."""
    
    work_around: Optional[str] = None
    """Work around."""
    
    fix_notes: Optional[str] = None
    """Fix notes."""
    
    cause_notes: Optional[str] = None
    """Cause notes."""
    
    resolution_code: Optional[str] = None
    """Resolution code."""
    
    opened_at: Optional[datetime] = None
    """Opened at."""
    
    resolved_at: Optional[datetime] = None
    """Resolved at."""
    
    closed_at: Optional[datetime] = None
    """Closed at."""
    
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    """Custom fields."""


@dataclass
class ServiceNowUser:
    """ServiceNow user data structure."""
    
    sys_id: Optional[str] = None
    """System ID."""
    
    user_name: str
    """Username."""
    
    first_name: Optional[str] = None
    """First name."""
    
    last_name: Optional[str] = None
    """Last name."""
    
    email: Optional[str] = None
    """Email."""
    
    phone: Optional[str] = None
    """Phone."""
    
    mobile_phone: Optional[str] = None
    """Mobile phone."""
    
    title: Optional[str] = None
    """Title."""
    
    department: Optional[str] = None
    """Department."""
    
    company: Optional[str] = None
    """Company."""
    
    location: Optional[str] = None
    """Location."""
    
    manager: Optional[str] = None
    """Manager."""
    
    active: bool = True
    """Active status."""
    
    last_login: Optional[datetime] = None
    """Last login."""
    
    created_on: Optional[datetime] = None
    """Created on."""
    
    updated_on: Optional[datetime] = None
    """Updated on."""


@dataclass
class ServiceNowConfigurationItem:
    """ServiceNow configuration item data structure."""
    
    sys_id: Optional[str] = None
    """System ID."""
    
    name: str
    """Name."""
    
    sys_class_name: str
    """System class name."""
    
    category: Optional[str] = None
    """Category."""
    
    subcategory: Optional[str] = None
    """Subcategory."""
    
    manufacturer: Optional[str] = None
    """Manufacturer."""
    
    model_number: Optional[str] = None
    """Model number."""
    
    serial_number: Optional[str] = None
    """Serial number."""
    
    asset_tag: Optional[str] = None
    """Asset tag."""
    
    install_status: Optional[str] = None
    """Install status."""
    
    operational_status: Optional[str] = None
    """Operational status."""
    
    ip_address: Optional[str] = None
    """IP address."""
    
    mac_address: Optional[str] = None
    """MAC address."""
    
    hostname: Optional[str] = None
    """Hostname."""
    
    fqdn: Optional[str] = None
    """Fully qualified domain name."""
    
    location: Optional[str] = None
    """Location."""
    
    assigned_to: Optional[str] = None
    """Assigned to."""
    
    owned_by: Optional[str] = None
    """Owned by."""
    
    supported_by: Optional[str] = None
    """Supported by."""
    
    business_criticality: Optional[str] = None
    """Business criticality."""
    
    cost: Optional[float] = None
    """Cost."""
    
    cost_cc: Optional[str] = None
    """Cost center."""
    
    purchase_date: Optional[datetime] = None
    """Purchase date."""
    
    warranty_expiration: Optional[datetime] = None
    """Warranty expiration."""
    
    lease_expiration: Optional[datetime] = None
    """Lease expiration."""
    
    created_on: Optional[datetime] = None
    """Created on."""
    
    updated_on: Optional[datetime] = None
    """Updated on."""


class ServiceNowIntegration:
    """ServiceNow integration for IT service management and workflow automation."""
    
    def __init__(self, config: ServiceNowConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.session = requests.Session()
        self.session.timeout = config.timeout
        self.session.verify = config.verify_ssl
        
        # Set up authentication
        if config.client_id and config.client_secret:
            # OAuth authentication
            self._setup_oauth_auth()
        else:
            # Basic authentication
            self.session.auth = (config.username, config.password)
        
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        
        self.base_url = f"{config.instance_url}/api/{config.api_version}"
    
    def _setup_oauth_auth(self):
        """Set up OAuth authentication."""
        try:
            # Get OAuth token
            token_url = f"{self.config.instance_url}/oauth_token.do"
            token_data = {
                "grant_type": "password",
                "username": self.config.username,
                "password": self.config.password,
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret
            }
            
            response = self.session.post(token_url, data=token_data)
            response.raise_for_status()
            
            token_info = response.json()
            access_token = token_info["access_token"]
            
            self.session.headers.update({
                "Authorization": f"Bearer {access_token}"
            })
            
        except Exception as e:
            self.logger.error(f"Failed to set up OAuth authentication: {e}")
            # Fall back to basic auth
            self.session.auth = (self.config.username, self.config.password)
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to the ServiceNow API."""
        try:
            url = f"{self.base_url}/{endpoint}"
            
            if method.upper() == "GET":
                response = self.session.get(url, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, params=params)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, params=params)
            elif method.upper() == "PATCH":
                response = self.session.patch(url, json=data, params=params)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            if response.content:
                return response.json()
            return {}
            
        except Exception as e:
            self.logger.error(f"Failed to make {method} request to {endpoint}: {e}")
            raise
    
    async def create_incident(self, incident: ServiceNowIncident) -> ServiceNowIncident:
        """
        Create a new incident.
        
        Args:
            incident: Incident data
            
        Returns:
            Created incident
        """
        try:
            data = {
                "short_description": incident.short_description,
                "description": incident.description,
                "category": incident.category.value,
                "priority": incident.priority.value,
                "impact": incident.impact.value,
                "urgency": incident.urgency.value,
                "state": incident.state.value,
                "caller_id": incident.caller_id
            }
            
            if incident.subcategory:
                data["subcategory"] = incident.subcategory
            if incident.assigned_to:
                data["assigned_to"] = incident.assigned_to
            if incident.opened_by:
                data["opened_by"] = incident.opened_by
            if incident.business_service:
                data["business_service"] = incident.business_service
            if incident.cmdb_ci:
                data["cmdb_ci"] = incident.cmdb_ci
            if incident.location:
                data["location"] = incident.location
            if incident.company:
                data["company"] = incident.company
            if incident.department:
                data["department"] = incident.department
            if incident.custom_fields:
                data.update(incident.custom_fields)
            
            result = self._make_request("POST", "table/incident", data)
            
            incident.sys_id = result["result"]["sys_id"]
            incident.number = result["result"]["number"]
            incident.opened_at = datetime.fromisoformat(result["result"]["opened_at"].replace("Z", "+00:00"))
            
            self.logger.info(f"Created ServiceNow incident: {incident.number}")
            return incident
            
        except Exception as e:
            self.logger.error(f"Failed to create incident: {e}")
            raise
    
    async def get_incident(self, sys_id: str) -> ServiceNowIncident:
        """
        Get an incident by sys_id.
        
        Args:
            sys_id: System ID
            
        Returns:
            Incident data
        """
        try:
            result = self._make_request("GET", f"table/incident/{sys_id}")
            
            incident_data = result["result"]
            
            return ServiceNowIncident(
                sys_id=incident_data["sys_id"],
                number=incident_data["number"],
                short_description=incident_data["short_description"],
                description=incident_data["description"],
                category=ServiceNowCategory(incident_data["category"]),
                subcategory=incident_data.get("subcategory"),
                priority=ServiceNowPriority(incident_data["priority"]),
                impact=ServiceNowImpact(incident_data["impact"]),
                urgency=ServiceNowUrgency(incident_data["urgency"]),
                state=ServiceNowState(incident_data["state"]),
                assigned_to=incident_data.get("assigned_to"),
                caller_id=incident_data["caller_id"],
                opened_by=incident_data.get("opened_by"),
                opened_at=datetime.fromisoformat(incident_data["opened_at"].replace("Z", "+00:00")) if incident_data.get("opened_at") else None,
                resolved_at=datetime.fromisoformat(incident_data["resolved_at"].replace("Z", "+00:00")) if incident_data.get("resolved_at") else None,
                closed_at=datetime.fromisoformat(incident_data["closed_at"].replace("Z", "+00:00")) if incident_data.get("closed_at") else None,
                resolved_by=incident_data.get("resolved_by"),
                closed_by=incident_data.get("closed_by"),
                close_notes=incident_data.get("close_notes"),
                resolution_notes=incident_data.get("resolution_notes"),
                business_service=incident_data.get("business_service"),
                cmdb_ci=incident_data.get("cmdb_ci"),
                location=incident_data.get("location"),
                company=incident_data.get("company"),
                department=incident_data.get("department"),
                custom_fields={k: v for k, v in incident_data.items() if k.startswith("u_")}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get incident: {e}")
            raise
    
    async def update_incident(self, sys_id: str, updates: Dict[str, Any]) -> ServiceNowIncident:
        """
        Update an incident.
        
        Args:
            sys_id: System ID
            updates: Update data
            
        Returns:
            Updated incident
        """
        try:
            self._make_request("PATCH", f"table/incident/{sys_id}", updates)
            
            return await self.get_incident(sys_id)
            
        except Exception as e:
            self.logger.error(f"Failed to update incident: {e}")
            raise
    
    async def delete_incident(self, sys_id: str) -> bool:
        """
        Delete an incident.
        
        Args:
            sys_id: System ID
            
        Returns:
            Success status
        """
        try:
            self._make_request("DELETE", f"table/incident/{sys_id}")
            self.logger.info(f"Deleted ServiceNow incident: {sys_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete incident: {e}")
            raise
    
    async def get_incidents(self, filters: Optional[Dict[str, Any]] = None, limit: int = 100) -> List[ServiceNowIncident]:
        """
        Get incidents with optional filters.
        
        Args:
            filters: Filter parameters
            limit: Maximum number of results
            
        Returns:
            List of incidents
        """
        try:
            params = {"sysparm_limit": limit}
            
            if filters:
                query = " AND ".join([f"{k}={v}" for k, v in filters.items()])
                params["sysparm_query"] = query
            
            result = self._make_request("GET", "table/incident", params=params)
            
            incidents = []
            for item in result["result"]:
                incident = ServiceNowIncident(
                    sys_id=item["sys_id"],
                    number=item["number"],
                    short_description=item["short_description"],
                    description=item["description"],
                    category=ServiceNowCategory(item["category"]),
                    subcategory=item.get("subcategory"),
                    priority=ServiceNowPriority(item["priority"]),
                    impact=ServiceNowImpact(item["impact"]),
                    urgency=ServiceNowUrgency(item["urgency"]),
                    state=ServiceNowState(item["state"]),
                    assigned_to=item.get("assigned_to"),
                    caller_id=item["caller_id"],
                    opened_by=item.get("opened_by"),
                    opened_at=datetime.fromisoformat(item["opened_at"].replace("Z", "+00:00")) if item.get("opened_at") else None,
                    resolved_at=datetime.fromisoformat(item["resolved_at"].replace("Z", "+00:00")) if item.get("resolved_at") else None,
                    closed_at=datetime.fromisoformat(item["closed_at"].replace("Z", "+00:00")) if item.get("closed_at") else None,
                    resolved_by=item.get("resolved_by"),
                    closed_by=item.get("closed_by"),
                    close_notes=item.get("close_notes"),
                    resolution_notes=item.get("resolution_notes"),
                    business_service=item.get("business_service"),
                    cmdb_ci=item.get("cmdb_ci"),
                    location=item.get("location"),
                    company=item.get("company"),
                    department=item.get("department"),
                    custom_fields={k: v for k, v in item.items() if k.startswith("u_")}
                )
                incidents.append(incident)
            
            return incidents
            
        except Exception as e:
            self.logger.error(f"Failed to get incidents: {e}")
            raise
    
    async def create_change_request(self, change_request: ServiceNowChangeRequest) -> ServiceNowChangeRequest:
        """
        Create a new change request.
        
        Args:
            change_request: Change request data
            
        Returns:
            Created change request
        """
        try:
            data = {
                "short_description": change_request.short_description,
                "description": change_request.description,
                "category": change_request.category.value,
                "priority": change_request.priority.value,
                "impact": change_request.impact.value,
                "urgency": change_request.urgency.value,
                "state": change_request.state.value,
                "requested_by": change_request.requested_by
            }
            
            if change_request.assigned_to:
                data["assigned_to"] = change_request.assigned_to
            if change_request.change_type:
                data["type"] = change_request.change_type
            if change_request.risk:
                data["risk"] = change_request.risk
            if change_request.business_justification:
                data["business_justification"] = change_request.business_justification
            if change_request.implementation_plan:
                data["implementation_plan"] = change_request.implementation_plan
            if change_request.test_plan:
                data["test_plan"] = change_request.test_plan
            if change_request.backout_plan:
                data["backout_plan"] = change_request.backout_plan
            if change_request.scheduled_start:
                data["start_date"] = change_request.scheduled_start.isoformat()
            if change_request.scheduled_end:
                data["end_date"] = change_request.scheduled_end.isoformat()
            if change_request.custom_fields:
                data.update(change_request.custom_fields)
            
            result = self._make_request("POST", "table/change_request", data)
            
            change_request.sys_id = result["result"]["sys_id"]
            change_request.number = result["result"]["number"]
            change_request.opened_at = datetime.fromisoformat(result["result"]["opened_at"].replace("Z", "+00:00"))
            
            self.logger.info(f"Created ServiceNow change request: {change_request.number}")
            return change_request
            
        except Exception as e:
            self.logger.error(f"Failed to create change request: {e}")
            raise
    
    async def get_change_request(self, sys_id: str) -> ServiceNowChangeRequest:
        """
        Get a change request by sys_id.
        
        Args:
            sys_id: System ID
            
        Returns:
            Change request data
        """
        try:
            result = self._make_request("GET", f"table/change_request/{sys_id}")
            
            change_data = result["result"]
            
            return ServiceNowChangeRequest(
                sys_id=change_data["sys_id"],
                number=change_data["number"],
                short_description=change_data["short_description"],
                description=change_data["description"],
                category=ServiceNowCategory(change_data["category"]),
                priority=ServiceNowPriority(change_data["priority"]),
                impact=ServiceNowImpact(change_data["impact"]),
                urgency=ServiceNowUrgency(change_data["urgency"]),
                state=ServiceNowState(change_data["state"]),
                requested_by=change_data["requested_by"],
                assigned_to=change_data.get("assigned_to"),
                change_type=change_data.get("type"),
                risk=change_data.get("risk"),
                business_justification=change_data.get("business_justification"),
                implementation_plan=change_data.get("implementation_plan"),
                test_plan=change_data.get("test_plan"),
                backout_plan=change_data.get("backout_plan"),
                scheduled_start=datetime.fromisoformat(change_data["start_date"].replace("Z", "+00:00")) if change_data.get("start_date") else None,
                scheduled_end=datetime.fromisoformat(change_data["end_date"].replace("Z", "+00:00")) if change_data.get("end_date") else None,
                actual_start=datetime.fromisoformat(change_data["work_start"].replace("Z", "+00:00")) if change_data.get("work_start") else None,
                actual_end=datetime.fromisoformat(change_data["work_end"].replace("Z", "+00:00")) if change_data.get("work_end") else None,
                opened_at=datetime.fromisoformat(change_data["opened_at"].replace("Z", "+00:00")) if change_data.get("opened_at") else None,
                closed_at=datetime.fromisoformat(change_data["closed_at"].replace("Z", "+00:00")) if change_data.get("closed_at") else None,
                custom_fields={k: v for k, v in change_data.items() if k.startswith("u_")}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get change request: {e}")
            raise
    
    async def create_problem(self, problem: ServiceNowProblem) -> ServiceNowProblem:
        """
        Create a new problem.
        
        Args:
            problem: Problem data
            
        Returns:
            Created problem
        """
        try:
            data = {
                "short_description": problem.short_description,
                "description": problem.description,
                "category": problem.category.value,
                "priority": problem.priority.value,
                "impact": problem.impact.value,
                "urgency": problem.urgency.value,
                "state": problem.state.value,
                "opened_by": problem.opened_by
            }
            
            if problem.assigned_to:
                data["assigned_to"] = problem.assigned_to
            if problem.problem_state:
                data["problem_state"] = problem.problem_state
            if problem.root_cause:
                data["root_cause"] = problem.root_cause
            if problem.work_around:
                data["work_around"] = problem.work_around
            if problem.fix_notes:
                data["fix_notes"] = problem.fix_notes
            if problem.cause_notes:
                data["cause_notes"] = problem.cause_notes
            if problem.resolution_code:
                data["resolution_code"] = problem.resolution_code
            if problem.custom_fields:
                data.update(problem.custom_fields)
            
            result = self._make_request("POST", "table/problem", data)
            
            problem.sys_id = result["result"]["sys_id"]
            problem.number = result["result"]["number"]
            problem.opened_at = datetime.fromisoformat(result["result"]["opened_at"].replace("Z", "+00:00"))
            
            self.logger.info(f"Created ServiceNow problem: {problem.number}")
            return problem
            
        except Exception as e:
            self.logger.error(f"Failed to create problem: {e}")
            raise
    
    async def get_problem(self, sys_id: str) -> ServiceNowProblem:
        """
        Get a problem by sys_id.
        
        Args:
            sys_id: System ID
            
        Returns:
            Problem data
        """
        try:
            result = self._make_request("GET", f"table/problem/{sys_id}")
            
            problem_data = result["result"]
            
            return ServiceNowProblem(
                sys_id=problem_data["sys_id"],
                number=problem_data["number"],
                short_description=problem_data["short_description"],
                description=problem_data["description"],
                category=ServiceNowCategory(problem_data["category"]),
                priority=ServiceNowPriority(problem_data["priority"]),
                impact=ServiceNowImpact(problem_data["impact"]),
                urgency=ServiceNowUrgency(problem_data["urgency"]),
                state=ServiceNowState(problem_data["state"]),
                opened_by=problem_data["opened_by"],
                assigned_to=problem_data.get("assigned_to"),
                problem_state=problem_data.get("problem_state"),
                root_cause=problem_data.get("root_cause"),
                work_around=problem_data.get("work_around"),
                fix_notes=problem_data.get("fix_notes"),
                cause_notes=problem_data.get("cause_notes"),
                resolution_code=problem_data.get("resolution_code"),
                opened_at=datetime.fromisoformat(problem_data["opened_at"].replace("Z", "+00:00")) if problem_data.get("opened_at") else None,
                resolved_at=datetime.fromisoformat(problem_data["resolved_at"].replace("Z", "+00:00")) if problem_data.get("resolved_at") else None,
                closed_at=datetime.fromisoformat(problem_data["closed_at"].replace("Z", "+00:00")) if problem_data.get("closed_at") else None,
                custom_fields={k: v for k, v in problem_data.items() if k.startswith("u_")}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get problem: {e}")
            raise
    
    async def get_user(self, sys_id: str) -> ServiceNowUser:
        """
        Get a user by sys_id.
        
        Args:
            sys_id: System ID
            
        Returns:
            User data
        """
        try:
            result = self._make_request("GET", f"table/sys_user/{sys_id}")
            
            user_data = result["result"]
            
            return ServiceNowUser(
                sys_id=user_data["sys_id"],
                user_name=user_data["user_name"],
                first_name=user_data.get("first_name"),
                last_name=user_data.get("last_name"),
                email=user_data.get("email"),
                phone=user_data.get("phone"),
                mobile_phone=user_data.get("mobile_phone"),
                title=user_data.get("title"),
                department=user_data.get("department"),
                company=user_data.get("company"),
                location=user_data.get("location"),
                manager=user_data.get("manager"),
                active=user_data.get("active", True),
                last_login=datetime.fromisoformat(user_data["last_login"].replace("Z", "+00:00")) if user_data.get("last_login") else None,
                created_on=datetime.fromisoformat(user_data["sys_created_on"].replace("Z", "+00:00")) if user_data.get("sys_created_on") else None,
                updated_on=datetime.fromisoformat(user_data["sys_updated_on"].replace("Z", "+00:00")) if user_data.get("sys_updated_on") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get user: {e}")
            raise
    
    async def search_users(self, query: str, limit: int = 100) -> List[ServiceNowUser]:
        """
        Search users.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of users
        """
        try:
            params = {
                "sysparm_query": query,
                "sysparm_limit": limit
            }
            
            result = self._make_request("GET", "table/sys_user", params=params)
            
            users = []
            for item in result["result"]:
                user = ServiceNowUser(
                    sys_id=item["sys_id"],
                    user_name=item["user_name"],
                    first_name=item.get("first_name"),
                    last_name=item.get("last_name"),
                    email=item.get("email"),
                    phone=item.get("phone"),
                    mobile_phone=item.get("mobile_phone"),
                    title=item.get("title"),
                    department=item.get("department"),
                    company=item.get("company"),
                    location=item.get("location"),
                    manager=item.get("manager"),
                    active=item.get("active", True),
                    last_login=datetime.fromisoformat(item["last_login"].replace("Z", "+00:00")) if item.get("last_login") else None,
                    created_on=datetime.fromisoformat(item["sys_created_on"].replace("Z", "+00:00")) if item.get("sys_created_on") else None,
                    updated_on=datetime.fromisoformat(item["sys_updated_on"].replace("Z", "+00:00")) if item.get("sys_updated_on") else None
                )
                users.append(user)
            
            return users
            
        except Exception as e:
            self.logger.error(f"Failed to search users: {e}")
            raise
    
    async def get_configuration_item(self, sys_id: str) -> ServiceNowConfigurationItem:
        """
        Get a configuration item by sys_id.
        
        Args:
            sys_id: System ID
            
        Returns:
            Configuration item data
        """
        try:
            result = self._make_request("GET", f"table/cmdb_ci/{sys_id}")
            
            ci_data = result["result"]
            
            return ServiceNowConfigurationItem(
                sys_id=ci_data["sys_id"],
                name=ci_data["name"],
                sys_class_name=ci_data["sys_class_name"],
                category=ci_data.get("category"),
                subcategory=ci_data.get("subcategory"),
                manufacturer=ci_data.get("manufacturer"),
                model_number=ci_data.get("model_number"),
                serial_number=ci_data.get("serial_number"),
                asset_tag=ci_data.get("asset_tag"),
                install_status=ci_data.get("install_status"),
                operational_status=ci_data.get("operational_status"),
                ip_address=ci_data.get("ip_address"),
                mac_address=ci_data.get("mac_address"),
                hostname=ci_data.get("hostname"),
                fqdn=ci_data.get("fqdn"),
                location=ci_data.get("location"),
                assigned_to=ci_data.get("assigned_to"),
                owned_by=ci_data.get("owned_by"),
                supported_by=ci_data.get("supported_by"),
                business_criticality=ci_data.get("business_criticality"),
                cost=float(ci_data["cost"]) if ci_data.get("cost") else None,
                cost_cc=ci_data.get("cost_cc"),
                purchase_date=datetime.fromisoformat(ci_data["purchase_date"].replace("Z", "+00:00")) if ci_data.get("purchase_date") else None,
                warranty_expiration=datetime.fromisoformat(ci_data["warranty_expiration"].replace("Z", "+00:00")) if ci_data.get("warranty_expiration") else None,
                lease_expiration=datetime.fromisoformat(ci_data["lease_expiration"].replace("Z", "+00:00")) if ci_data.get("lease_expiration") else None,
                created_on=datetime.fromisoformat(ci_data["sys_created_on"].replace("Z", "+00:00")) if ci_data.get("sys_created_on") else None,
                updated_on=datetime.fromisoformat(ci_data["sys_updated_on"].replace("Z", "+00:00")) if ci_data.get("sys_updated_on") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get configuration item: {e}")
            raise
    
    async def search_configuration_items(self, query: str, limit: int = 100) -> List[ServiceNowConfigurationItem]:
        """
        Search configuration items.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of configuration items
        """
        try:
            params = {
                "sysparm_query": query,
                "sysparm_limit": limit
            }
            
            result = self._make_request("GET", "table/cmdb_ci", params=params)
            
            cis = []
            for item in result["result"]:
                ci = ServiceNowConfigurationItem(
                    sys_id=item["sys_id"],
                    name=item["name"],
                    sys_class_name=item["sys_class_name"],
                    category=item.get("category"),
                    subcategory=item.get("subcategory"),
                    manufacturer=item.get("manufacturer"),
                    model_number=item.get("model_number"),
                    serial_number=item.get("serial_number"),
                    asset_tag=item.get("asset_tag"),
                    install_status=item.get("install_status"),
                    operational_status=item.get("operational_status"),
                    ip_address=item.get("ip_address"),
                    mac_address=item.get("mac_address"),
                    hostname=item.get("hostname"),
                    fqdn=item.get("fqdn"),
                    location=item.get("location"),
                    assigned_to=item.get("assigned_to"),
                    owned_by=item.get("owned_by"),
                    supported_by=item.get("supported_by"),
                    business_criticality=item.get("business_criticality"),
                    cost=float(item["cost"]) if item.get("cost") else None,
                    cost_cc=item.get("cost_cc"),
                    purchase_date=datetime.fromisoformat(item["purchase_date"].replace("Z", "+00:00")) if item.get("purchase_date") else None,
                    warranty_expiration=datetime.fromisoformat(item["warranty_expiration"].replace("Z", "+00:00")) if item.get("warranty_expiration") else None,
                    lease_expiration=datetime.fromisoformat(item["lease_expiration"].replace("Z", "+00:00")) if item.get("lease_expiration") else None,
                    created_on=datetime.fromisoformat(item["sys_created_on"].replace("Z", "+00:00")) if item.get("sys_created_on") else None,
                    updated_on=datetime.fromisoformat(item["sys_updated_on"].replace("Z", "+00:00")) if item.get("sys_updated_on") else None
                )
                cis.append(ci)
            
            return cis
            
        except Exception as e:
            self.logger.error(f"Failed to search configuration items: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the ServiceNow integration.
        
        Returns:
            Health check results
        """
        try:
            # Test API connectivity by getting a single incident
            params = {"sysparm_limit": 1}
            result = self._make_request("GET", "table/incident", params=params)
            
            return {
                "status": "healthy",
                "instance_url": self.config.instance_url,
                "api_version": self.config.api_version,
                "total_incidents": len(result.get("result", [])),
                "api_connectivity": "successful",
                "last_checked": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_checked": datetime.now().isoformat()
            }
