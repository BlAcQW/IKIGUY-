from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, List, Any, Optional
import subprocess
import os
import re
import json
import psutil
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

from ..models.service_management import (
    ServiceConfig, ServiceConfigSchema, ServiceStatus,
    ServiceFileTemplate, ServiceActionRequest, ServiceCreateRequest
)

router = APIRouter()

# Service file templates
SERVICE_TEMPLATES = {
    "python": {
        "name": "Python Service",
        "description": "Python application service",
        "category": "application",
        "template": """[Unit]
Description={description}
After=network.target
Wants=network.target

[Service]
Type=simple
User={user}
Group={group}
WorkingDirectory={working_dir}
Environment="PATH={python_env}/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PYTHONPATH={python_path}"
ExecStart={python_env}/bin/python {script_path}
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier={service_name}

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096
MemoryMax={memory_limit}
MemorySwapMax={memory_swap_limit}

[Install]
WantedBy=multi-user.target""",
        "variables": {
            "description": "My Python Service",
            "user": "root",
            "group": "root",
            "working_dir": "/opt/kasaai",
            "python_env": "/opt/kasaai/venv",
            "python_path": "/opt/kasaai",
            "script_path": "/opt/kasaai/service.py",
            "service_name": "my-service",
            "memory_limit": "1G",
            "memory_swap_limit": "2G"
        }
    },
    "node": {
        "name": "Node.js Service",
        "description": "Node.js application service",
        "category": "application",
        "template": """[Unit]
Description={description}
After=network.target

[Service]
Type=simple
User={user}
Group={group}
WorkingDirectory={working_dir}
ExecStart=/usr/bin/node {script_path}
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier={service_name}

# Resource limits
MemoryMax={memory_limit}
MemorySwapMax={memory_swap_limit}

[Install]
WantedBy=multi-user.target""",
        "variables": {
            "description": "My Node Service",
            "user": "www-data",
            "group": "www-data",
            "working_dir": "/opt/app",
            "script_path": "/opt/app/index.js",
            "service_name": "my-node-service",
            "memory_limit": "512M",
            "memory_swap_limit": "1G"
        }
    },
    "generic": {
        "name": "Generic Service",
        "description": "Generic systemd service",
        "category": "system",
        "template": """[Unit]
Description={description}
After=network.target

[Service]
Type=simple
User={user}
ExecStart={exec_start}
Restart={restart}
RestartSec={restart_sec}

[Install]
WantedBy=multi-user.target""",
        "variables": {
            "description": "My Service",
            "user": "root",
            "exec_start": "/usr/bin/myapp",
            "restart": "always",
            "restart_sec": "10"
        }
    }
}

def run_command(cmd: str, timeout: int = 30) -> tuple[int, str, str]:
    """Run a shell command and return exit code, stdout, stderr"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def scan_systemd_services() -> List[Dict]:
    """Scan for all systemd service files"""
    services = []
    
    # Scan system service directories
    service_dirs = [
        "/etc/systemd/system/",
        "/lib/systemd/system/",
        "/usr/lib/systemd/system/"
    ]
    
    # Also include user services if needed
    user_service_dir = f"/home/{os.environ.get('USER', 'root')}/.config/systemd/user/"
    if os.path.exists(user_service_dir):
        service_dirs.append(user_service_dir)
    
    seen_services = set()
    
    # Ensure important voice services are always included
    priority_services = [
        'coqui-tts', 'f5tts', 'melotts', 'openvoice', 
        'tts-coqui', 'tts-metamms', 'tts-openvoice',
        'mongod', 'nginx', 'docker'
    ]
    
    # Add priority services first if they exist
    for service_name in priority_services:
        for service_dir in service_dirs:
            service_file = Path(service_dir) / f"{service_name}.service"
            if service_file.exists() and service_name not in seen_services:
                seen_services.add(service_name)
                description = ""
                try:
                    with open(service_file, 'r') as f:
                        for line in f:
                            if line.startswith("Description="):
                                description = line.split("=", 1)[1].strip()
                                break
                except:
                    pass
                
                services.append({
                    "service_name": service_name,
                    "display_name": generate_display_name(service_name),
                    "description": description,
                    "category": categorize_service(service_name),
                    "file_path": str(service_file)
                })
                break
    
    for service_dir in service_dirs:
        if not os.path.exists(service_dir):
            continue
            
        for file in Path(service_dir).glob("*.service"):
            service_name = file.stem
            
            # Skip if we've already seen this service
            if service_name in seen_services:
                continue
            seen_services.add(service_name)
            
            # Try to extract description from service file
            description = ""
            try:
                with open(file, 'r') as f:
                    for line in f:
                        if line.startswith("Description="):
                            description = line.split("=", 1)[1].strip()
                            break
            except:
                pass
            
            # Auto-categorize based on name patterns
            category = categorize_service(service_name)
            
            services.append({
                "service_name": service_name,
                "display_name": generate_display_name(service_name),
                "description": description,
                "category": category,
                "file_path": str(file)
            })
    
    return sorted(services, key=lambda x: (x['category'], x['service_name']))

def categorize_service(service_name: str) -> str:
    """Auto-categorize service based on name patterns"""
    name_lower = service_name.lower()
    
    # Voice/TTS services
    if any(x in name_lower for x in ['tts', 'voice', 'speech', 'audio', 'melotts', 'coqui', 'openvoice', 'f5tts']):
        return "voice"
    
    # Database services
    if any(x in name_lower for x in ['mongo', 'mysql', 'maria', 'postgres', 'redis', 'elastic', 'cassandra']):
        return "database"
    
    # Web services
    if any(x in name_lower for x in ['nginx', 'apache', 'httpd', 'caddy', 'traefik']):
        return "web"
    
    # Container services
    if any(x in name_lower for x in ['docker', 'containerd', 'podman', 'k3s', 'k8s', 'kubernetes']):
        return "container"
    
    # Monitoring services
    if any(x in name_lower for x in ['grafana', 'prometheus', 'kibana', 'netdata', 'zabbix']):
        return "monitoring"
    
    # Messaging services
    if any(x in name_lower for x in ['kafka', 'rabbitmq', 'mqtt', 'nats', 'zeromq']):
        return "messaging"
    
    # Automation services
    if any(x in name_lower for x in ['n8n', 'airflow', 'jenkins', 'gitlab']):
        return "automation"
    
    # Application services
    if any(x in name_lower for x in ['app', 'api', 'backend', 'frontend', 'service']):
        return "application"
    
    # Network services
    if any(x in name_lower for x in ['vpn', 'ssh', 'ftp', 'dns', 'dhcp']):
        return "network"
    
    return "system"

def generate_display_name(service_name: str) -> str:
    """Generate a human-readable display name from service name"""
    # Remove common suffixes
    name = service_name.replace('.service', '').replace('-service', '').replace('_service', '')
    
    # Handle special cases
    special_names = {
        'mongod': 'MongoDB',
        'mariadbd': 'MariaDB',
        'nginx': 'Nginx',
        'docker': 'Docker',
        'k3s': 'K3s',
        'redis': 'Redis',
        'elasticsearch': 'ElasticSearch',
        'kibana': 'Kibana',
        'grafana-server': 'Grafana',
        'n8n': 'n8n Automation',
        'coqui-tts': 'Coqui TTS',
        'f5tts': 'F5 TTS',
        'openvoice': 'OpenVoice',
        'melotts': 'MeloTTS'
    }
    
    if name in special_names:
        return special_names[name]
    
    # Convert snake_case and kebab-case to Title Case
    name = name.replace('_', ' ').replace('-', ' ')
    return ' '.join(word.capitalize() for word in name.split())

def get_service_status(service_name: str, config: Optional[ServiceConfig] = None) -> ServiceStatus:
    """Get detailed status of a single service"""
    status = ServiceStatus(
        service_name=service_name,
        display_name=config.display_name if config else generate_display_name(service_name),
        category=config.category if config else categorize_service(service_name),
        status="unknown",
        is_enabled=False,
        can_start=True,
        can_stop=True,
        can_restart=True
    )
    
    # Check if service exists
    code, stdout, _ = run_command(f"systemctl list-unit-files {service_name}.service 2>/dev/null | grep {service_name}")
    if code != 0:
        status.status = "not_found"
        status.can_start = False
        status.can_stop = False
        status.can_restart = False
        return status
    
    # Get service status
    code, stdout, _ = run_command(f"systemctl is-active {service_name}")
    status.status = stdout.strip() if code == 0 else "stopped"
    
    # Check if enabled
    code, stdout, _ = run_command(f"systemctl is-enabled {service_name}")
    status.is_enabled = stdout.strip() == "enabled"
    
    # Get detailed status
    code, stdout, _ = run_command(f"systemctl status {service_name} --no-pager -n 0")
    
    # Parse status output
    for line in stdout.split('\n'):
        line = line.strip()
        
        # Get PID
        if 'Main PID:' in line:
            match = re.search(r'Main PID:\s*(\d+)', line)
            if match:
                status.pid = int(match.group(1))
                
                # Get memory usage for this PID
                try:
                    process = psutil.Process(status.pid)
                    mem_info = process.memory_info()
                    status.memory_current = format_bytes(mem_info.rss)
                    status.cpu_usage = f"{process.cpu_percent(interval=0.1):.1f}%"
                except:
                    pass
        
        # Get active since
        if 'Active:' in line:
            match = re.search(r'since\s+([^;]+)', line)
            if match:
                status.active_since = match.group(1).strip()
                # Calculate uptime
                try:
                    active_time = datetime.strptime(status.active_since, "%a %Y-%m-%d %H:%M:%S %Z")
                    uptime = datetime.now() - active_time
                    days = uptime.days
                    hours = uptime.seconds // 3600
                    minutes = (uptime.seconds % 3600) // 60
                    if days > 0:
                        status.uptime = f"{days}d {hours}h {minutes}m"
                    elif hours > 0:
                        status.uptime = f"{hours}h {minutes}m"
                    else:
                        status.uptime = f"{minutes}m"
                except:
                    pass
        
        # Get memory limit
        if 'Memory:' in line:
            match = re.search(r'Memory:\s*([^\s]+)', line)
            if match:
                status.memory_current = match.group(1)
    
    # Get memory limits from config
    if config:
        status.memory_limit = config.memory_limit
    
    # Get recent logs
    code, stdout, _ = run_command(f"journalctl -u {service_name} -n 10 --no-pager --output=short")
    if code == 0:
        status.logs = stdout.strip().split('\n')[-10:] if stdout else []
    
    # Find service file path
    for dir in ["/etc/systemd/system/", "/lib/systemd/system/"]:
        file_path = f"{dir}{service_name}.service"
        if os.path.exists(file_path):
            status.file_path = file_path
            break
    
    return status

def format_bytes(bytes_val: int) -> str:
    """Format bytes to human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} PB"

@router.get("/scan")
async def scan_services():
    """Scan system for all available services"""
    try:
        services = scan_systemd_services()
        return {"services": services, "total": len(services)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_services():
    """List all monitored services with their current status"""
    try:
        # Get all scanned services
        all_services = scan_systemd_services()
        
        # Filter for important services (voice, database, web, application)
        important_categories = ['voice', 'database', 'web', 'application', 'monitoring']
        
        # Prioritize important services
        important_services = [s for s in all_services if s['category'] in important_categories]
        other_services = [s for s in all_services if s['category'] not in important_categories]
        
        # Combine with important services first, limit to 50 for performance
        prioritized_services = (important_services + other_services)[:50]
        
        services_with_status = []
        for service in prioritized_services:
            status = get_service_status(service['service_name'])
            services_with_status.append(status.dict())
        
        return {
            "services": services_with_status,
            "total": len(services_with_status)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{service_name}/status")
async def get_service_status_endpoint(service_name: str):
    """Get detailed status of a specific service"""
    try:
        status = get_service_status(service_name)
        if status.status == "not_found":
            raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{service_name}/action")
async def service_action(service_name: str, request: ServiceActionRequest):
    """Perform an action on a service (start, stop, restart, etc.)"""
    valid_actions = ["start", "stop", "restart", "reload", "enable", "disable"]
    
    if request.action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action. Must be one of: {valid_actions}")
    
    try:
        # Execute the action
        cmd = f"sudo systemctl {request.action} {service_name}"
        code, stdout, stderr = run_command(cmd)
        
        if code != 0:
            raise HTTPException(status_code=500, detail=f"Failed to {request.action} service: {stderr}")
        
        # Get updated status
        status = get_service_status(service_name)
        
        return {
            "success": True,
            "action": request.action,
            "service": service_name,
            "status": status
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{service_name}/logs")
async def get_service_logs(service_name: str, lines: int = 100):
    """Get recent logs for a service"""
    try:
        cmd = f"journalctl -u {service_name} -n {lines} --no-pager --output=short"
        code, stdout, stderr = run_command(cmd)
        
        if code != 0:
            raise HTTPException(status_code=500, detail=f"Failed to get logs: {stderr}")
        
        logs = stdout.strip().split('\n') if stdout else []
        
        return {
            "service": service_name,
            "logs": logs,
            "line_count": len(logs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{service_name}/file")
async def get_service_file(service_name: str):
    """Get the systemd service file content"""
    try:
        # Find service file
        file_path = None
        for dir in ["/etc/systemd/system/", "/lib/systemd/system/"]:
            path = f"{dir}{service_name}.service"
            if os.path.exists(path):
                file_path = path
                break
        
        if not file_path:
            raise HTTPException(status_code=404, detail=f"Service file for {service_name} not found")
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        return {
            "service": service_name,
            "file_path": file_path,
            "content": content
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{service_name}/file")
async def update_service_file(service_name: str, content: Dict[str, str]):
    """Update a systemd service file"""
    try:
        file_path = f"/etc/systemd/system/{service_name}.service"
        
        # Backup existing file if it exists
        if os.path.exists(file_path):
            backup_path = f"{file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            run_command(f"sudo cp {file_path} {backup_path}")
        
        # Write new content
        with open(file_path, 'w') as f:
            f.write(content['content'])
        
        # Reload systemd daemon
        code, _, stderr = run_command("sudo systemctl daemon-reload")
        if code != 0:
            raise HTTPException(status_code=500, detail=f"Failed to reload daemon: {stderr}")
        
        return {
            "success": True,
            "service": service_name,
            "file_path": file_path,
            "message": "Service file updated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create")
async def create_service(request: ServiceCreateRequest):
    """Create a new systemd service"""
    try:
        file_path = f"/etc/systemd/system/{request.service_name}.service"
        
        # Check if service already exists
        if os.path.exists(file_path):
            raise HTTPException(status_code=400, detail=f"Service {request.service_name} already exists")
        
        # Write service file
        with open(file_path, 'w') as f:
            f.write(request.content)
        
        # Set proper permissions
        run_command(f"sudo chmod 644 {file_path}")
        
        # Reload systemd daemon
        code, _, stderr = run_command("sudo systemctl daemon-reload")
        if code != 0:
            raise HTTPException(status_code=500, detail=f"Failed to reload daemon: {stderr}")
        
        # Enable service if requested
        if request.enable:
            run_command(f"sudo systemctl enable {request.service_name}")
        
        # Start service if requested
        if request.start:
            run_command(f"sudo systemctl start {request.service_name}")
        
        # Get status
        status = get_service_status(request.service_name)
        
        return {
            "success": True,
            "service": request.service_name,
            "file_path": file_path,
            "status": status
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{service_name}")
async def delete_service(service_name: str):
    """Delete a systemd service"""
    try:
        file_path = f"/etc/systemd/system/{service_name}.service"
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
        
        # Stop and disable service first
        run_command(f"sudo systemctl stop {service_name}")
        run_command(f"sudo systemctl disable {service_name}")
        
        # Backup before deletion
        backup_path = f"{file_path}.deleted.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        run_command(f"sudo mv {file_path} {backup_path}")
        
        # Reload daemon
        run_command("sudo systemctl daemon-reload")
        
        return {
            "success": True,
            "service": service_name,
            "backup_path": backup_path,
            "message": "Service deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates")
async def get_service_templates():
    """Get available service file templates"""
    templates = []
    for key, template in SERVICE_TEMPLATES.items():
        templates.append({
            "id": key,
            "name": template["name"],
            "description": template["description"],
            "category": template["category"],
            "variables": list(template["variables"].keys())
        })
    return {"templates": templates}

@router.get("/templates/{template_id}")
async def get_service_template(template_id: str):
    """Get a specific service template with content"""
    if template_id not in SERVICE_TEMPLATES:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    
    template = SERVICE_TEMPLATES[template_id]
    return {
        "id": template_id,
        "name": template["name"],
        "description": template["description"],
        "category": template["category"],
        "template": template["template"],
        "variables": template["variables"]
    }

@router.post("/daemon-reload")
async def daemon_reload():
    """Reload systemd daemon configuration"""
    try:
        code, stdout, stderr = run_command("sudo systemctl daemon-reload")
        if code != 0:
            raise HTTPException(status_code=500, detail=f"Failed to reload daemon: {stderr}")
        
        return {
            "success": True,
            "message": "Systemd daemon reloaded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))