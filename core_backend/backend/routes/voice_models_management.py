from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from typing import Dict, List, Any, Optional
import subprocess
import os
import json
import shutil
import asyncio
from pathlib import Path
from datetime import datetime
import hashlib
import requests
from pydantic import BaseModel
import psutil
import re

router = APIRouter()

# Model directories for each service
MODEL_PATHS = {
    "coqui": {
        "base_path": "/opt/kasaai/voice_coqui_env",
        "models_dir": "/opt/kasaai/voice_models/coqui_models",
        "cache_dir": "/root/.cache/coqui",
        "service_name": "coqui-tts"
    },
    "openvoice": {
        "base_path": "/opt/kasaai/voice_models/OpenVoice",
        "models_dir": "/opt/kasaai/voice_models/OpenVoice/checkpoints",
        "cache_dir": "/opt/kasaai/voice_models/models_cache/openvoice",
        "service_name": "openvoice"
    },
    "f5tts": {
        "base_path": "/opt/kasaai/voice_models/F5-TTS",
        "models_dir": "/opt/kasaai/voice_models/F5-TTS/ckpts",
        "cache_dir": "/opt/kasaai/voice_models/models_cache/f5tts",
        "service_name": "f5tts"
    },
    "melotts": {
        "base_path": "/opt/kasaai/voice_models/MeloTTS",
        "models_dir": "/opt/kasaai/voice_models/MeloTTS/models",
        "cache_dir": "/opt/kasaai/voice_models/models_cache/melotts",
        "service_name": "melotts"
    },
    "metamms": {
        "base_path": "/opt/kasaai/voice_models_env",
        "models_dir": "/opt/kasaai/voice_models/mms_models",
        "cache_dir": "/opt/kasaai/voice_models_cache",
        "service_name": "mms-tts"
    }
}

# Model repositories
MODEL_REPOS = {
    "huggingface": {
        "coqui": [
            {"id": "tts_models/en/ljspeech/tacotron2-DDC", "name": "LJSpeech Tacotron2", "size": "107MB", "languages": ["en"]},
            {"id": "tts_models/en/ljspeech/glow-tts", "name": "LJSpeech Glow-TTS", "size": "119MB", "languages": ["en"]},
            {"id": "tts_models/en/vctk/vits", "name": "VCTK VITS Multi-speaker", "size": "133MB", "languages": ["en"]},
            {"id": "tts_models/multilingual/multi-dataset/xtts_v2", "name": "XTTS v2 Multilingual", "size": "1.8GB", "languages": ["en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "ja", "ko", "hu", "hi"]},
            {"id": "tts_models/multilingual/multi-dataset/your_tts", "name": "YourTTS Multilingual", "size": "880MB", "languages": ["en", "fr", "pt"]}
        ],
        "openvoice": [
            {"id": "myshell-ai/OpenVoice", "name": "OpenVoice Base", "size": "330MB", "languages": ["en", "zh"]},
            {"id": "myshell-ai/OpenVoiceV2", "name": "OpenVoice V2", "size": "380MB", "languages": ["en", "zh", "ja", "ko", "es"]}
        ],
        "f5tts": [
            {"id": "SWivid/F5-TTS", "name": "F5-TTS Base", "size": "1.2GB", "languages": ["en", "zh"]},
            {"id": "SWivid/E2-TTS", "name": "E2-TTS Enhanced", "size": "1.5GB", "languages": ["en", "zh"]}
        ],
        "melotts": [
            {"id": "myshell-ai/MeloTTS-English", "name": "MeloTTS English", "size": "380MB", "languages": ["en"]},
            {"id": "myshell-ai/MeloTTS-Chinese", "name": "MeloTTS Chinese", "size": "420MB", "languages": ["zh"]},
            {"id": "myshell-ai/MeloTTS-Multi", "name": "MeloTTS Multilingual", "size": "650MB", "languages": ["en", "zh", "ja", "ko", "es", "fr", "de"]}
        ],
        "metamms": [
            {"id": "facebook/mms-tts-eng", "name": "MMS English", "size": "50MB", "languages": ["en"]},
            {"id": "facebook/mms-tts-twi", "name": "MMS Twi", "size": "50MB", "languages": ["twi"]},
            {"id": "facebook/mms-tts-ewe", "name": "MMS Ewe", "size": "50MB", "languages": ["ewe"]},
            {"id": "facebook/mms-tts-aka", "name": "MMS Akan", "size": "50MB", "languages": ["aka"]},
            {"id": "facebook/mms-tts-hau", "name": "MMS Hausa", "size": "50MB", "languages": ["hau"]},
            {"id": "facebook/mms-tts", "name": "MMS All Languages", "size": "12GB", "languages": ["1100+ languages"]}
        ]
    },
    "github": {
        "openvoice": [
            {"url": "https://github.com/myshell-ai/OpenVoice", "name": "OpenVoice Repository", "branch": "main"},
            {"url": "https://github.com/myshell-ai/OpenVoice", "name": "OpenVoice V2", "branch": "v2"}
        ],
        "f5tts": [
            {"url": "https://github.com/SWivid/F5-TTS", "name": "F5-TTS Repository", "branch": "main"}
        ],
        "melotts": [
            {"url": "https://github.com/myshell-ai/MeloTTS", "name": "MeloTTS Repository", "branch": "main"}
        ]
    }
}

class ModelInfo(BaseModel):
    """Information about a voice model"""
    id: str
    name: str
    service: str
    size: str
    languages: List[str]
    installed: bool
    path: Optional[str] = None
    last_modified: Optional[str] = None
    source: str  # huggingface, github, local
    download_url: Optional[str] = None

class ModelDownloadRequest(BaseModel):
    """Request to download a model"""
    service: str
    model_id: str
    source: str = "huggingface"  # huggingface, github, url

class ModelActionRequest(BaseModel):
    """Request for model actions"""
    action: str  # download, delete, update
    service: str
    model_id: str

def get_directory_size(path: str) -> int:
    """Get total size of directory in bytes"""
    total = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total += os.path.getsize(fp)
    except:
        pass
    return total

def format_bytes(bytes_val: int) -> str:
    """Format bytes to human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} PB"

def scan_installed_models(service: str) -> List[Dict]:
    """Scan for installed models for a specific service"""
    installed = []
    
    if service not in MODEL_PATHS:
        return installed
    
    paths = MODEL_PATHS[service]
    
    # Check models directory
    models_dir = paths.get("models_dir")
    if models_dir and os.path.exists(models_dir):
        for item in os.listdir(models_dir):
            item_path = os.path.join(models_dir, item)
            if os.path.isdir(item_path) or item.endswith(('.pth', '.pt', '.ckpt', '.bin', '.safetensors')):
                stat = os.stat(item_path)
                size = get_directory_size(item_path) if os.path.isdir(item_path) else stat.st_size
                
                installed.append({
                    "id": item,
                    "name": item.replace('_', ' ').replace('-', ' ').title(),
                    "path": item_path,
                    "size": format_bytes(size),
                    "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "source": "local"
                })
    
    # Check cache directory
    cache_dir = paths.get("cache_dir")
    if cache_dir and os.path.exists(cache_dir):
        for item in os.listdir(cache_dir):
            item_path = os.path.join(cache_dir, item)
            if os.path.isdir(item_path):
                # Skip if already found in models_dir
                if any(m['id'] == item for m in installed):
                    continue
                    
                stat = os.stat(item_path)
                size = get_directory_size(item_path)
                
                installed.append({
                    "id": item,
                    "name": item.replace('_', ' ').replace('-', ' ').title(),
                    "path": item_path,
                    "size": format_bytes(size),
                    "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "source": "cache"
                })
    
    return installed

def download_huggingface_model(service: str, model_id: str) -> Dict:
    """Download a model from HuggingFace"""
    if service == "coqui":
        # Use Coqui TTS download command
        cmd = f"cd {MODEL_PATHS[service]['base_path']} && ./bin/python -c \"from TTS.api import TTS; tts = TTS('{model_id}', progress_bar=True)\""
    elif service == "metamms":
        # Use HuggingFace transformers
        cmd = f"cd {MODEL_PATHS[service]['base_path']} && ./bin/python -c \"from transformers import VitsModel, VitsTokenizer; model = VitsModel.from_pretrained('{model_id}'); tokenizer = VitsTokenizer.from_pretrained('{model_id}')\""
    else:
        # Use git lfs for other models
        model_dir = os.path.join(MODEL_PATHS[service]['models_dir'], model_id.split('/')[-1])
        cmd = f"git clone https://huggingface.co/{model_id} {model_dir}"
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            raise Exception(f"Download failed: {result.stderr}")
        return {"success": True, "message": f"Model {model_id} downloaded successfully"}
    except subprocess.TimeoutExpired:
        raise Exception("Download timeout (10 minutes)")
    except Exception as e:
        raise Exception(f"Download failed: {str(e)}")

def download_github_model(service: str, repo_url: str, branch: str = "main") -> Dict:
    """Clone or update a model from GitHub"""
    model_name = repo_url.split('/')[-1]
    model_dir = os.path.join(MODEL_PATHS[service]['models_dir'], model_name)
    
    if os.path.exists(model_dir):
        # Update existing repo
        cmd = f"cd {model_dir} && git pull origin {branch}"
    else:
        # Clone new repo
        os.makedirs(os.path.dirname(model_dir), exist_ok=True)
        cmd = f"git clone -b {branch} {repo_url} {model_dir}"
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise Exception(f"Git operation failed: {result.stderr}")
        return {"success": True, "message": f"Repository {model_name} updated successfully"}
    except Exception as e:
        raise Exception(f"Git operation failed: {str(e)}")

@router.get("/voice-models/list")
async def list_voice_models(service: Optional[str] = None):
    """List all available and installed voice models"""
    try:
        models = {}
        
        services = [service] if service else MODEL_PATHS.keys()
        
        for svc in services:
            # Get available models from repos
            available = []
            
            # HuggingFace models
            if svc in MODEL_REPOS["huggingface"]:
                for model in MODEL_REPOS["huggingface"][svc]:
                    available.append({
                        **model,
                        "service": svc,
                        "source": "huggingface",
                        "installed": False
                    })
            
            # GitHub models
            if svc in MODEL_REPOS["github"]:
                for repo in MODEL_REPOS["github"][svc]:
                    available.append({
                        "id": repo["url"].split('/')[-1],
                        "name": repo["name"],
                        "service": svc,
                        "source": "github",
                        "url": repo["url"],
                        "branch": repo.get("branch", "main"),
                        "installed": False
                    })
            
            # Get installed models
            installed = scan_installed_models(svc)
            
            # Mark available models as installed if found
            for avail in available:
                for inst in installed:
                    if avail["id"].split('/')[-1] in inst["id"] or inst["id"] in avail["id"]:
                        avail["installed"] = True
                        avail["path"] = inst["path"]
                        avail["actual_size"] = inst["size"]
                        avail["last_modified"] = inst["last_modified"]
            
            # Add installed models not in available list
            for inst in installed:
                if not any(inst["id"] in a.get("id", "") or a.get("id", "") in inst["id"] for a in available):
                    available.append({
                        "id": inst["id"],
                        "name": inst["name"],
                        "service": svc,
                        "source": inst["source"],
                        "installed": True,
                        "path": inst["path"],
                        "size": inst["size"],
                        "last_modified": inst["last_modified"],
                        "languages": ["unknown"]
                    })
            
            models[svc] = {
                "service_name": svc.upper(),
                "models": available,
                "total_available": len([m for m in available if not m["installed"]]),
                "total_installed": len([m for m in available if m["installed"]]),
                "storage_used": format_bytes(sum(get_directory_size(m["path"]) for m in installed if "path" in m))
            }
        
        return {
            "services": models,
            "total_models": sum(len(m["models"]) for m in models.values()),
            "disk_usage": get_disk_usage()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/voice-models/{service}/installed")
async def get_installed_models(service: str):
    """Get list of installed models for a service"""
    try:
        if service not in MODEL_PATHS:
            raise HTTPException(status_code=404, detail=f"Service {service} not found")
        
        installed = scan_installed_models(service)
        
        return {
            "service": service,
            "models": installed,
            "total": len(installed),
            "storage_used": format_bytes(sum(
                get_directory_size(m["path"]) if os.path.isdir(m["path"]) else os.path.getsize(m["path"])
                for m in installed if "path" in m and os.path.exists(m["path"])
            ))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/voice-models/download")
async def download_model(request: ModelDownloadRequest, background_tasks: BackgroundTasks):
    """Download a voice model"""
    try:
        if request.service not in MODEL_PATHS:
            raise HTTPException(status_code=404, detail=f"Service {request.service} not found")
        
        # Create models directory if it doesn't exist
        models_dir = MODEL_PATHS[request.service]["models_dir"]
        os.makedirs(models_dir, exist_ok=True)
        
        if request.source == "huggingface":
            # Download from HuggingFace
            background_tasks.add_task(download_huggingface_model, request.service, request.model_id)
            return {
                "success": True,
                "message": f"Download started for {request.model_id}",
                "status": "downloading"
            }
        elif request.source == "github":
            # Clone from GitHub
            # Find the repo URL
            github_models = MODEL_REPOS["github"].get(request.service, [])
            repo = next((r for r in github_models if request.model_id in r["url"]), None)
            
            if not repo:
                raise HTTPException(status_code=404, detail=f"GitHub repository not found for {request.model_id}")
            
            background_tasks.add_task(download_github_model, request.service, repo["url"], repo.get("branch", "main"))
            return {
                "success": True,
                "message": f"Git clone started for {request.model_id}",
                "status": "cloning"
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported source: {request.source}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/voice-models/{service}/{model_id}")
async def delete_model(service: str, model_id: str):
    """Delete an installed model"""
    try:
        if service not in MODEL_PATHS:
            raise HTTPException(status_code=404, detail=f"Service {service} not found")
        
        # Find the model
        installed = scan_installed_models(service)
        model = next((m for m in installed if m["id"] == model_id), None)
        
        if not model:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        # Delete the model
        model_path = model["path"]
        if os.path.exists(model_path):
            if os.path.isdir(model_path):
                shutil.rmtree(model_path)
            else:
                os.remove(model_path)
        
        return {
            "success": True,
            "message": f"Model {model_id} deleted successfully",
            "freed_space": model["size"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_disk_usage():
    """Get disk usage for voice models"""
    try:
        usage = {}
        total_used = 0
        
        for service, paths in MODEL_PATHS.items():
            service_usage = 0
            
            for key in ["models_dir", "cache_dir"]:
                dir_path = paths.get(key)
                if dir_path and os.path.exists(dir_path):
                    size = get_directory_size(dir_path)
                    service_usage += size
            
            usage[service] = format_bytes(service_usage)
            total_used += service_usage
        
        # Get total disk info
        try:
            disk = psutil.disk_usage('/')
            disk_info = {
                "disk_total": format_bytes(disk.total),
                "disk_free": format_bytes(disk.free),
                "disk_percent": disk.percent
            }
        except:
            disk_info = {
                "disk_total": "N/A",
                "disk_free": "N/A",
                "disk_percent": 0
            }
        
        return {
            "services": usage,
            "total_used": format_bytes(total_used),
            **disk_info
        }
    except Exception as e:
        return {
            "services": {},
            "total_used": "0 B",
            "disk_total": "N/A",
            "disk_free": "N/A",
            "disk_percent": 0
        }

@router.get("/voice-models/disk-usage")
async def get_disk_usage_endpoint():
    """Get disk usage for voice models"""
    return get_disk_usage()

@router.post("/voice-models/cleanup")
async def cleanup_models(service: Optional[str] = None):
    """Clean up unused model files and caches"""
    try:
        cleaned = {}
        total_freed = 0
        
        services = [service] if service else MODEL_PATHS.keys()
        
        for svc in services:
            paths = MODEL_PATHS[svc]
            freed = 0
            
            # Clean cache directory
            cache_dir = paths.get("cache_dir")
            if cache_dir and os.path.exists(cache_dir):
                # Remove .tmp files
                for root, dirs, files in os.walk(cache_dir):
                    for file in files:
                        if file.endswith('.tmp') or file.startswith('tmp'):
                            file_path = os.path.join(root, file)
                            size = os.path.getsize(file_path)
                            os.remove(file_path)
                            freed += size
            
            cleaned[svc] = format_bytes(freed)
            total_freed += freed
        
        return {
            "success": True,
            "services_cleaned": cleaned,
            "total_freed": format_bytes(total_freed)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/voice-models/search")
async def search_models(query: str):
    """Search for models across all services"""
    try:
        results = []
        query_lower = query.lower()
        
        # Search in available models
        for service in MODEL_PATHS.keys():
            # HuggingFace models
            if service in MODEL_REPOS["huggingface"]:
                for model in MODEL_REPOS["huggingface"][service]:
                    if (query_lower in model["id"].lower() or 
                        query_lower in model["name"].lower() or
                        any(query_lower in lang for lang in model.get("languages", []))):
                        results.append({
                            **model,
                            "service": service,
                            "source": "huggingface"
                        })
            
            # Installed models
            installed = scan_installed_models(service)
            for model in installed:
                if query_lower in model["id"].lower() or query_lower in model["name"].lower():
                    results.append({
                        **model,
                        "service": service,
                        "installed": True
                    })
        
        return {
            "query": query,
            "results": results,
            "total": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/voice-models/recommendations")
async def get_model_recommendations():
    """Get recommended models for different use cases"""
    recommendations = {
        "multilingual": [
            {
                "service": "coqui",
                "model_id": "tts_models/multilingual/multi-dataset/xtts_v2",
                "name": "XTTS v2",
                "reason": "Best quality multilingual TTS with 16 languages support"
            },
            {
                "service": "melotts",
                "model_id": "myshell-ai/MeloTTS-Multi",
                "name": "MeloTTS Multilingual",
                "reason": "Fast multilingual synthesis with good quality"
            }
        ],
        "african_languages": [
            {
                "service": "metamms",
                "model_id": "facebook/mms-tts-twi",
                "name": "MMS Twi",
                "reason": "Specialized for Twi language"
            },
            {
                "service": "metamms",
                "model_id": "facebook/mms-tts-hau",
                "name": "MMS Hausa",
                "reason": "Specialized for Hausa language"
            }
        ],
        "voice_cloning": [
            {
                "service": "openvoice",
                "model_id": "myshell-ai/OpenVoiceV2",
                "name": "OpenVoice V2",
                "reason": "Latest voice cloning with improved quality"
            },
            {
                "service": "coqui",
                "model_id": "tts_models/multilingual/multi-dataset/your_tts",
                "name": "YourTTS",
                "reason": "Zero-shot voice cloning capability"
            }
        ],
        "fast_inference": [
            {
                "service": "melotts",
                "model_id": "myshell-ai/MeloTTS-English",
                "name": "MeloTTS English",
                "reason": "Optimized for speed with good quality"
            },
            {
                "service": "metamms",
                "model_id": "facebook/mms-tts-eng",
                "name": "MMS English",
                "reason": "Lightweight and fast"
            }
        ],
        "high_quality": [
            {
                "service": "f5tts",
                "model_id": "SWivid/F5-TTS",
                "name": "F5-TTS",
                "reason": "State-of-the-art quality with natural prosody"
            },
            {
                "service": "coqui",
                "model_id": "tts_models/en/vctk/vits",
                "name": "VCTK VITS",
                "reason": "High-quality multi-speaker English TTS"
            }
        ]
    }
    
    return recommendations