from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any
import subprocess
import os
import psutil
import hashlib
from datetime import datetime
from pathlib import Path
import json
import re

router = APIRouter()

def get_auth_user(authorization: str = None):
    """Simple auth check - expand as needed"""
    # For now, allow access without auth for testing
    # In production, integrate with proper auth system
    return True

def run_command(cmd: str, timeout: int = 30) -> str:
    """Run a shell command and return output"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        return ""
    except Exception as e:
        print(f"Error running command {cmd}: {e}")
        return ""

def parse_df_output(df_output: str) -> List[Dict]:
    """Parse df -h output"""
    lines = df_output.strip().split('\n')
    if len(lines) < 2:
        return []
    
    disks = []
    for line in lines[1:]:
        parts = line.split()
        if len(parts) >= 6:
            use_percent = parts[4].rstrip('%')
            try:
                use_percent = int(use_percent)
            except:
                use_percent = 0
                
            disks.append({
                "filesystem": parts[0],
                "size": parts[1],
                "used": parts[2],
                "available": parts[3],
                "usePercent": use_percent,
                "mountPoint": parts[5]
            })
    
    # Filter to main filesystems only
    main_disks = [d for d in disks if d['mountPoint'] in ['/', '/home', '/var', '/opt']]
    if not main_disks:
        main_disks = [d for d in disks if d['filesystem'].startswith('/dev/')][:3]
    
    return main_disks

def get_large_files(path: str = "/", size_mb: int = 500, limit: int = 20) -> List[Dict]:
    """Find large files"""
    cmd = f"find {path} -type f -size +{size_mb}M 2>/dev/null | head -{limit} | xargs -I {{}} sh -c 'ls -la \"{{}}\" | awk \"{{print \\$5, \\$9}}\"'"
    output = run_command(cmd)
    
    files = []
    for line in output.strip().split('\n'):
        if line:
            parts = line.split(None, 1)
            if len(parts) == 2:
                try:
                    size_bytes = int(parts[0])
                    files.append({
                        "path": parts[1],
                        "size": format_bytes(size_bytes),
                        "sizeBytes": size_bytes,
                        "lastModified": ""
                    })
                except:
                    pass
    
    return sorted(files, key=lambda x: x['sizeBytes'], reverse=True)

def find_duplicate_files() -> List[Dict]:
    """Find duplicate CUDA libraries and other large duplicate files"""
    duplicates = []
    
    # Check for duplicate CUDA libraries
    cuda_libs = [
        "libcublasLt.so.12",
        "libcudnn_engines_precompiled.so.9",
        "libtorch_cuda.so"
    ]
    
    for lib in cuda_libs:
        cmd = f"find /opt /usr/local /root -name '{lib}' -type f 2>/dev/null"
        output = run_command(cmd)
        paths = [p for p in output.strip().split('\n') if p]
        
        if len(paths) > 1:
            # Get size of first file
            size_cmd = f"ls -la '{paths[0]}' 2>/dev/null | awk '{{print $5}}'"
            size_output = run_command(size_cmd)
            try:
                size_bytes = int(size_output.strip())
                duplicates.append({
                    "paths": paths,
                    "size": format_bytes(size_bytes),
                    "sizeBytes": size_bytes,
                    "hash": lib  # Use lib name as identifier
                })
            except:
                pass
    
    return duplicates

def get_docker_usage() -> Dict:
    """Get Docker disk usage"""
    cmd = "docker system df 2>/dev/null"
    output = run_command(cmd)
    
    usage = {
        "images": "N/A",
        "containers": "N/A",
        "volumes": "N/A",
        "buildCache": "N/A",
        "reclaimable": "N/A"
    }
    
    lines = output.strip().split('\n')
    for line in lines:
        if 'Images' in line:
            parts = line.split()
            if len(parts) >= 7:
                usage["images"] = parts[6]
                usage["reclaimable"] = parts[6]
        elif 'Containers' in line:
            parts = line.split()
            if len(parts) >= 6:
                usage["containers"] = parts[5]
        elif 'Local Volumes' in line:
            parts = line.split()
            if len(parts) >= 7:
                usage["volumes"] = parts[6]
    
    return usage

def get_pip_cache_info() -> Dict:
    """Get pip cache information"""
    cmd = "pip cache info 2>/dev/null"
    output = run_command(cmd)
    
    cache_info = {
        "size": "N/A",
        "fileCount": 0
    }
    
    # Parse pip cache info output
    for line in output.split('\n'):
        if 'cache size:' in line.lower():
            match = re.search(r'(\d+\.?\d*)\s*(MB|GB|KB)', line)
            if match:
                cache_info["size"] = f"{match.group(1)} {match.group(2)}"
        elif 'Number of HTTP files:' in line:
            match = re.search(r'(\d+)', line)
            if match:
                cache_info["fileCount"] = int(match.group(1))
    
    return cache_info

def get_mongo_logs_info() -> Dict:
    """Get MongoDB log file information"""
    log_path = "/var/log/mongodb/mongod.log"
    
    try:
        if os.path.exists(log_path):
            size = os.path.getsize(log_path)
            return {
                "size": format_bytes(size),
                "path": log_path
            }
    except:
        pass
    
    return {"size": "N/A", "path": log_path}

def get_services_status() -> List[Dict]:
    """Get status of key services"""
    services = [
        "mongod",
        "nginx", 
        "docker",
        "k3s",
        "postgresql",
        "redis",
        "elasticsearch",
        "kibana",
        "grafana",
        "prometheus"
    ]
    
    service_status = []
    
    for service in services:
        status = {
            "name": service,
            "status": "unknown",
            "memory": "N/A",
            "cpu": "N/A",
            "uptime": "N/A",
            "logs": []
        }
        
        # Check if service is running
        cmd = f"systemctl is-active {service} 2>/dev/null"
        output = run_command(cmd).strip()
        
        if output == "active":
            status["status"] = "running"
            
            # Get memory and CPU usage
            cmd = f"systemctl status {service} 2>/dev/null | grep 'Memory\\|CPU'"
            output = run_command(cmd)
            for line in output.split('\n'):
                if 'Memory:' in line:
                    match = re.search(r'Memory:\s*(\S+)', line)
                    if match:
                        status["memory"] = match.group(1)
                elif 'CPU:' in line:
                    match = re.search(r'CPU:\s*(\S+)', line)
                    if match:
                        status["cpu"] = match.group(1)
            
            # Get last 5 log lines
            cmd = f"journalctl -u {service} -n 5 --no-pager 2>/dev/null"
            log_output = run_command(cmd)
            status["logs"] = log_output.strip().split('\n')[-5:] if log_output else []
            
        elif output == "inactive":
            status["status"] = "stopped"
        elif output == "failed":
            status["status"] = "failed"
        
        service_status.append(status)
    
    return service_status

def get_memory_usage() -> Dict:
    """Get system memory usage"""
    try:
        mem = psutil.virtual_memory()
        return {
            "total": format_bytes(mem.total),
            "used": format_bytes(mem.used),
            "free": format_bytes(mem.available),
            "percent": round(mem.percent, 1)
        }
    except:
        return {
            "total": "N/A",
            "used": "N/A",
            "free": "N/A",
            "percent": 0
        }

def format_bytes(bytes_val: int) -> str:
    """Format bytes to human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} PB"

@router.get("/health")
async def get_system_health(authorized: bool = Depends(get_auth_user)):
    """Get comprehensive system health data"""
    try:
        # Get disk usage
        df_output = run_command("df -h")
        disk_usage = parse_df_output(df_output)
        
        # Get large files
        large_files = get_large_files()
        
        # Find duplicates
        duplicate_files = find_duplicate_files()
        
        # Get Docker usage
        docker_usage = get_docker_usage()
        
        # Get pip cache info
        pip_cache = get_pip_cache_info()
        
        # Get MongoDB logs info
        mongo_logs = get_mongo_logs_info()
        
        # Get services status
        services = get_services_status()
        
        # Get memory usage
        memory_usage = get_memory_usage()
        
        return {
            "diskUsage": disk_usage,
            "largeFiles": large_files,
            "duplicateFiles": duplicate_files,
            "dockerUsage": docker_usage,
            "pipCache": pip_cache,
            "mongoLogs": mongo_logs,
            "services": services,
            "memoryUsage": memory_usage
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_gpu_info() -> Dict:
    """
    Get GPU information using nvidia-smi.

    Returns:
        Dict: GPU monitoring data including utilization, memory, temperature, and processes.
    """
    try:
        # Check if nvidia-smi is available
        check_cmd = "which nvidia-smi"
        check_output = run_command(check_cmd, timeout=5)

        if not check_output.strip():
            return {
                "available": False,
                "error": "nvidia-smi not found. NVIDIA drivers may not be installed.",
                "gpus": [],
                "timestamp": datetime.now().isoformat()
            }

        # Get GPU information using nvidia-smi
        # Query format: index, name, driver_version, memory.total, memory.used, memory.free,
        # utilization.gpu, utilization.memory, temperature.gpu, power.draw, power.limit
        query_cmd = (
            "nvidia-smi --query-gpu=index,name,driver_version,memory.total,memory.used,"
            "memory.free,utilization.gpu,utilization.memory,temperature.gpu,power.draw,"
            "power.limit --format=csv,noheader,nounits"
        )

        gpu_output = run_command(query_cmd, timeout=10)

        if not gpu_output.strip():
            return {
                "available": False,
                "error": "Failed to query GPU information",
                "gpus": [],
                "timestamp": datetime.now().isoformat()
            }

        gpus = []

        # Parse GPU information
        for line in gpu_output.strip().split('\n'):
            if not line:
                continue

            parts = [p.strip() for p in line.split(',')]
            if len(parts) < 11:
                continue

            try:
                gpu_index = int(parts[0])
                total_memory_mb = float(parts[3])
                used_memory_mb = float(parts[4])
                free_memory_mb = float(parts[5])

                # Get CUDA version
                cuda_cmd = "nvcc --version 2>/dev/null | grep 'release' | awk '{print $5}' | sed 's/,//'"
                cuda_output = run_command(cuda_cmd, timeout=5)
                cuda_version = cuda_output.strip() if cuda_output.strip() else "N/A"

                # Get running processes on this GPU
                processes_cmd = (
                    f"nvidia-smi --query-compute-apps=pid,process_name,used_memory "
                    f"--format=csv,noheader,nounits -i {gpu_index}"
                )
                processes_output = run_command(processes_cmd, timeout=10)

                processes = []
                if processes_output.strip():
                    for proc_line in processes_output.strip().split('\n'):
                        proc_parts = [p.strip() for p in proc_line.split(',')]
                        if len(proc_parts) >= 3:
                            try:
                                proc_memory_mb = float(proc_parts[2])
                                processes.append({
                                    "pid": int(proc_parts[0]),
                                    "processName": proc_parts[1],
                                    "usedMemory": format_bytes(int(proc_memory_mb * 1024 * 1024)),
                                    "usedMemoryBytes": int(proc_memory_mb * 1024 * 1024)
                                })
                            except:
                                pass

                gpu_data = {
                    "index": gpu_index,
                    "name": parts[1],
                    "driverVersion": parts[2],
                    "cudaVersion": cuda_version,
                    "totalMemory": format_bytes(int(total_memory_mb * 1024 * 1024)),
                    "usedMemory": format_bytes(int(used_memory_mb * 1024 * 1024)),
                    "freeMemory": format_bytes(int(free_memory_mb * 1024 * 1024)),
                    "memoryPercent": round((used_memory_mb / total_memory_mb) * 100, 1) if total_memory_mb > 0 else 0,
                    "utilizationGpu": int(parts[6]) if parts[6] != '[N/A]' else 0,
                    "utilizationMemory": int(parts[7]) if parts[7] != '[N/A]' else 0,
                    "temperature": int(float(parts[8])) if parts[8] != '[N/A]' else 0,
                    "powerDraw": f"{parts[9]} W" if parts[9] != '[N/A]' else "N/A",
                    "powerLimit": f"{parts[10]} W" if parts[10] != '[N/A]' else "N/A",
                    "processes": processes
                }

                gpus.append(gpu_data)

            except Exception as e:
                print(f"Error parsing GPU line: {line}, error: {e}")
                continue

        return {
            "available": len(gpus) > 0,
            "gpus": gpus,
            "timestamp": datetime.now().isoformat(),
            "error": None if len(gpus) > 0 else "No GPUs found"
        }

    except Exception as e:
        return {
            "available": False,
            "error": f"Error querying GPU information: {str(e)}",
            "gpus": [],
            "timestamp": datetime.now().isoformat()
        }


@router.get("/gpu")
async def get_gpu_monitoring(authorized: bool = Depends(get_auth_user)):
    """
    Get GPU monitoring data including utilization, memory, temperature, and running processes.

    Returns:
        Dict: Comprehensive GPU monitoring information.
    """
    try:
        gpu_data = get_gpu_info()
        return gpu_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overview")
async def get_system_overview(authorized: bool = Depends(get_auth_user)):
    """
    Get system overview including CPU, memory, uptime, and top processes.

    Returns:
        Dict: System overview data.
    """
    try:
        # Get CPU information
        cpu_count = run_command("nproc").strip()
        load_avg = run_command("uptime | awk -F'load average:' '{print $2}'").strip()

        # Get uptime
        uptime_output = run_command("uptime -p").strip()

        # Get memory usage
        memory_usage = get_memory_usage()

        # Get top CPU-consuming processes
        top_cpu_cmd = "ps aux --sort=-%cpu | head -11 | tail -10"
        top_cpu_output = run_command(top_cpu_cmd)

        top_cpu_processes = []
        for line in top_cpu_output.strip().split('\n'):
            if line:
                parts = line.split(None, 10)
                if len(parts) >= 11:
                    try:
                        top_cpu_processes.append({
                            "user": parts[0],
                            "pid": int(parts[1]),
                            "cpu": float(parts[2]),
                            "mem": float(parts[3]),
                            "command": parts[10][:100]  # Limit command length
                        })
                    except:
                        pass

        # Get top memory-consuming processes
        top_mem_cmd = "ps aux --sort=-%mem | head -11 | tail -10"
        top_mem_output = run_command(top_mem_cmd)

        top_mem_processes = []
        for line in top_mem_output.strip().split('\n'):
            if line:
                parts = line.split(None, 10)
                if len(parts) >= 11:
                    try:
                        top_mem_processes.append({
                            "user": parts[0],
                            "pid": int(parts[1]),
                            "cpu": float(parts[2]),
                            "mem": float(parts[3]),
                            "command": parts[10][:100]  # Limit command length
                        })
                    except:
                        pass

        # Get running services count
        services_count_cmd = "systemctl list-units --type=service --state=running --no-pager | grep -c '.service'"
        services_count = run_command(services_count_cmd).strip() or "0"

        # Get Docker info if available
        docker_containers = {}
        docker_ps_output = run_command("docker ps --format '{{.Status}}' 2>/dev/null")
        if docker_ps_output:
            docker_lines = docker_ps_output.strip().split('\n')
            docker_containers = {
                "running": len([l for l in docker_lines if l]),
                "total": len([l for l in docker_lines if l])
            }

        # Get disk usage summary
        df_output = run_command("df -h / | tail -1")
        disk_usage_summary = {}
        if df_output:
            parts = df_output.split()
            if len(parts) >= 5:
                disk_usage_summary = {
                    "total": parts[1],
                    "used": parts[2],
                    "available": parts[3],
                    "percent": int(parts[4].rstrip('%'))
                }

        return {
            "cpu": {
                "count": int(cpu_count) if cpu_count.isdigit() else 0,
                "loadAverage": load_avg
            },
            "uptime": uptime_output,
            "memory": memory_usage,
            "disk": disk_usage_summary,
            "topCpuProcesses": top_cpu_processes,
            "topMemProcesses": top_mem_processes,
            "servicesRunning": int(services_count) if services_count.isdigit() else 0,
            "dockerContainers": docker_containers,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def perform_cleanup(cleanup_data: Dict[str, Any], authorized: bool = Depends(get_auth_user)):
    """Perform system cleanup based on type"""
    cleanup_type = cleanup_data.get("type")

    if not cleanup_type:
        raise HTTPException(status_code=400, detail="Cleanup type required")

    try:
        freed_space = "0 MB"

        if cleanup_type == "mongo_logs":
            # Rotate MongoDB logs
            commands = [
                "sudo systemctl stop mongod",
                "sudo mv /var/log/mongodb/mongod.log /var/log/mongodb/mongod.log.old",
                "sudo systemctl start mongod",
                "sudo rm -f /var/log/mongodb/mongod.log.old"
            ]

            # Get size before deletion
            size_cmd = "ls -la /var/log/mongodb/mongod.log 2>/dev/null | awk '{print $5}'"
            size_output = run_command(size_cmd)
            try:
                size_bytes = int(size_output.strip())
                freed_space = format_bytes(size_bytes)
            except:
                pass

            for cmd in commands:
                run_command(cmd)

        elif cleanup_type == "pip_cache":
            # Clear pip cache
            output = run_command("pip cache purge 2>&1")
            # Extract freed space from output
            match = re.search(r'(\d+)\s*files', output)
            if match:
                freed_space = f"{match.group(1)} files cleared"

        elif cleanup_type == "docker":
            # Docker system prune
            output = run_command("docker system prune -a --volumes -f 2>&1")
            # Extract reclaimed space
            match = re.search(r'reclaimed:\s*(\S+\s*\S+)', output, re.IGNORECASE)
            if match:
                freed_space = match.group(1)

        elif cleanup_type == "apt":
            # Remove unused packages
            run_command("sudo apt-get autoremove -y")
            freed_space = "Unused packages removed"

        elif cleanup_type == "git":
            # Git garbage collection
            run_command("cd /opt/kasaai && git gc --prune=now")
            freed_space = "Git repository optimized"

        else:
            raise HTTPException(status_code=400, detail=f"Unknown cleanup type: {cleanup_type}")

        return {
            "success": True,
            "type": cleanup_type,
            "freedSpace": freed_space
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/kill")
async def kill_process(process_data: Dict[str, Any], authorized: bool = Depends(get_auth_user)):
    """
    Kill a process by PID.

    Args:
        process_data: Dict containing 'pid' (int) and optional 'signal' (str, default: 'TERM')

    Returns:
        Dict: Success status and message
    """
    pid = process_data.get("pid")
    signal = process_data.get("signal", "TERM")  # Default to SIGTERM for graceful shutdown

    if not pid:
        raise HTTPException(status_code=400, detail="Process ID (pid) required")

    try:
        pid = int(pid)

        # Verify the process exists and get its info first
        try:
            proc = psutil.Process(pid)
            process_name = proc.name()
            process_cmdline = ' '.join(proc.cmdline())
        except psutil.NoSuchProcess:
            raise HTTPException(status_code=404, detail=f"Process with PID {pid} not found")
        except psutil.AccessDenied:
            raise HTTPException(status_code=403, detail=f"Access denied to process {pid}")

        # Use kill command with sudo for processes that may require elevated permissions
        # Validate signal to prevent command injection
        valid_signals = ['TERM', 'KILL', 'INT', 'HUP', 'QUIT']
        if signal not in valid_signals:
            raise HTTPException(status_code=400, detail=f"Invalid signal. Must be one of: {', '.join(valid_signals)}")

        # Try to kill the process
        kill_cmd = f"sudo kill -{signal} {pid} 2>&1"
        output = run_command(kill_cmd, timeout=5)

        # Wait a moment and check if the process is still running
        import time
        time.sleep(0.5)

        try:
            # If we can still get the process, it's still running
            psutil.Process(pid)
            is_running = True
        except psutil.NoSuchProcess:
            is_running = False

        if is_running and signal == 'TERM':
            return {
                "success": True,
                "pid": pid,
                "signal": signal,
                "processName": process_name,
                "status": "termination_signal_sent",
                "message": f"Termination signal sent to process {pid} ({process_name}). Process may take a moment to shutdown gracefully."
            }
        elif is_running:
            return {
                "success": False,
                "pid": pid,
                "signal": signal,
                "processName": process_name,
                "status": "still_running",
                "message": f"Process {pid} ({process_name}) is still running after {signal} signal. May require SIGKILL."
            }
        else:
            return {
                "success": True,
                "pid": pid,
                "signal": signal,
                "processName": process_name,
                "status": "terminated",
                "message": f"Process {pid} ({process_name}) has been terminated successfully"
            }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid PID format. Must be an integer")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error killing process: {str(e)}")


# Docker Service Management Endpoints

@router.get("/docker/{service_id}/status")
async def get_docker_service_status(service_id: str, authorized: bool = Depends(get_auth_user)):
    """
    Get status of a Docker TTS service.

    Args:
        service_id: Docker container ID/name (moshi, coqui, melotts, openvoice, kokoro)

    Returns:
        Service status including running state and GPU memory usage
    """
    try:
        # Check if container exists and get status (use head -1 to get first match if multiple)
        check_cmd = f"docker ps -a --filter name={service_id} --format '{{{{.Status}}}}' | head -1"
        status_output = run_command(check_cmd).strip()

        if not status_output:
            # Container doesn't exist
            return {
                "service_id": service_id,
                "status": "unknown",
                "gpu_memory": None,
                "error": f"Container {service_id} not found"
            }

        # Parse status
        status = "unknown"
        if "Up" in status_output:
            status = "running"
        elif "Exited" in status_output:
            status = "stopped"
        elif "Paused" in status_output:
            status = "paused"
        elif "Restarting" in status_output:
            status = "restarting"

        # Get GPU memory if running
        gpu_memory = None
        if status == "running":
            try:
                # Use nvidia-smi to check GPU memory usage for this container
                gpu_cmd = f"nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader,nounits 2>/dev/null"
                gpu_output = run_command(gpu_cmd)

                # Get container PID
                pid_cmd = f"docker inspect --format '{{{{.State.Pid}}}}' {service_id}"
                container_pid = run_command(pid_cmd).strip()

                if gpu_output and container_pid:
                    # Find GPU memory for container processes
                    for line in gpu_output.strip().split('\n'):
                        if line:
                            parts = line.split(',')
                            if len(parts) == 2:
                                gpu_memory = f"{parts[1].strip()} MB"
                                break
            except Exception as e:
                print(f"Error getting GPU memory for {service_id}: {e}")

        return {
            "service_id": service_id,
            "status": status,
            "gpu_memory": gpu_memory,
            "raw_status": status_output
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting Docker service status: {str(e)}")


@router.post("/docker/{service_id}/start")
async def start_docker_service(service_id: str, authorized: bool = Depends(get_auth_user)):
    """
    Start a Docker TTS service.

    Args:
        service_id: Docker container ID/name
    """
    try:
        # Check if container exists (use head -1 to get first match if multiple)
        check_cmd = f"docker ps -a --filter name={service_id} --format '{{{{.Names}}}}' | head -1"
        container_name = run_command(check_cmd).strip()

        if not container_name:
            raise HTTPException(status_code=404, detail=f"Container {service_id} not found")

        # Start the container
        start_cmd = f"docker start {service_id}"
        output = run_command(start_cmd)

        if service_id in output or not output:
            # Success (either container name returned or no output means success)
            return {
                "success": True,
                "service_id": service_id,
                "message": f"Container {service_id} started successfully",
                "output": output.strip()
            }
        else:
            raise HTTPException(status_code=500, detail=f"Failed to start {service_id}: {output}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting Docker service: {str(e)}")


@router.post("/docker/{service_id}/stop")
async def stop_docker_service(service_id: str, authorized: bool = Depends(get_auth_user)):
    """
    Stop a Docker TTS service.

    Args:
        service_id: Docker container ID/name
    """
    try:
        # Check if container exists (use head -1 to get first match if multiple)
        check_cmd = f"docker ps -a --filter name={service_id} --format '{{{{.Names}}}}' | head -1"
        container_name = run_command(check_cmd).strip()

        if not container_name:
            raise HTTPException(status_code=404, detail=f"Container {service_id} not found")

        # Stop the container
        stop_cmd = f"docker stop {service_id}"
        output = run_command(stop_cmd)

        if service_id in output or not output:
            return {
                "success": True,
                "service_id": service_id,
                "message": f"Container {service_id} stopped successfully",
                "output": output.strip()
            }
        else:
            raise HTTPException(status_code=500, detail=f"Failed to stop {service_id}: {output}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping Docker service: {str(e)}")


@router.post("/docker/{service_id}/restart")
async def restart_docker_service(service_id: str, authorized: bool = Depends(get_auth_user)):
    """
    Restart a Docker TTS service.

    Args:
        service_id: Docker container ID/name
    """
    try:
        # Check if container exists (use head -1 to get first match if multiple)
        check_cmd = f"docker ps -a --filter name={service_id} --format '{{{{.Names}}}}' | head -1"
        container_name = run_command(check_cmd).strip()

        if not container_name:
            raise HTTPException(status_code=404, detail=f"Container {service_id} not found")

        # Restart the container
        restart_cmd = f"docker restart {service_id}"
        output = run_command(restart_cmd)

        if service_id in output or not output:
            return {
                "success": True,
                "service_id": service_id,
                "message": f"Container {service_id} restarted successfully",
                "output": output.strip()
            }
        else:
            raise HTTPException(status_code=500, detail=f"Failed to restart {service_id}: {output}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error restarting Docker service: {str(e)}")