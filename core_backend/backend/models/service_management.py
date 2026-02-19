from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Dict, List, Any

Base = declarative_base()

class ServiceConfig(Base):
    """Database model for service configurations"""
    __tablename__ = "service_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String, unique=True, index=True)
    display_name = Column(String)
    category = Column(String)
    description = Column(Text)
    is_monitored = Column(Boolean, default=True)
    is_critical = Column(Boolean, default=False)
    memory_limit = Column(String, nullable=True)
    memory_swap_limit = Column(String, nullable=True)
    auto_restart = Column(Boolean, default=True)
    restart_delay = Column(Integer, default=10)
    custom_config = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ServiceConfigSchema(BaseModel):
    """Pydantic schema for service configuration"""
    service_name: str
    display_name: str
    category: str
    description: Optional[str] = ""
    is_monitored: bool = True
    is_critical: bool = False
    memory_limit: Optional[str] = None
    memory_swap_limit: Optional[str] = None
    auto_restart: bool = True
    restart_delay: int = 10
    custom_config: Dict[str, Any] = {}

class ServiceStatus(BaseModel):
    """Current status of a service"""
    service_name: str
    display_name: str
    category: str
    status: str
    is_enabled: bool
    memory_current: Optional[str] = None
    memory_limit: Optional[str] = None
    cpu_usage: Optional[str] = None
    uptime: Optional[str] = None
    pid: Optional[int] = None
    active_since: Optional[str] = None
    logs: List[str] = []
    can_start: bool = True
    can_stop: bool = True
    can_restart: bool = True
    file_path: Optional[str] = None

class ServiceFileTemplate(BaseModel):
    """Template for creating new service files"""
    name: str
    description: str
    template: str
    category: str
    variables: Dict[str, str] = {}

class ServiceActionRequest(BaseModel):
    """Request for service actions"""
    action: str
    service_name: str

class ServiceCreateRequest(BaseModel):
    """Request for creating a new service"""
    service_name: str
    display_name: str
    category: str
    description: str
    content: str
    enable: bool = True
    start: bool = False