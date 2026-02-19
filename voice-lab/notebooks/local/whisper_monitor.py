#!/usr/bin/env python3
"""
Robust monitoring script for Whisper Medium training.

Tracks:
- Process health and memory usage
- Preprocessing progress
- Crash detection and logging
- GPU utilization
"""

import os
import re
import sys
import time
import psutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List


class WhisperTrainingMonitor:
    """Monitor Whisper training process with crash detection."""

    def __init__(
        self,
        script_path: str = "/opt/kasaai/apps/voice-lab/notebooks/local/006_faster_whisper_medium_twi.py",
        log_file: str = "/opt/kasaai/apps/voice-lab/notebooks/local/whisper_medium_twi_training.log",
        monitor_log: str = "/opt/kasaai/apps/voice-lab/notebooks/local/whisper_monitor.log",
        check_interval: int = 30,
    ):
        """
        Initialize the monitor.

        Args:
            script_path: Path to training script
            log_file: Path to training log
            monitor_log: Path to monitor's own log
            check_interval: Seconds between checks
        """
        self.script_path = script_path
        self.log_file = Path(log_file)
        self.monitor_log = Path(monitor_log)
        self.check_interval = check_interval
        self.process: Optional[psutil.Process] = None
        self.last_progress = 0
        self.last_progress_time = time.time()
        self.crash_count = 0
        self.start_time = datetime.now()

    def log(self, message: str, level: str = "INFO"):
        """Write to monitor log and stdout."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}"
        print(log_line)
        with open(self.monitor_log, "a") as f:
            f.write(log_line + "\n")

    def find_process(self) -> Optional[psutil.Process]:
        """Find the Whisper training process."""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and '006_faster_whisper_medium_twi.py' in ' '.join(cmdline):
                    return psutil.Process(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None

    def get_gpu_memory(self) -> Dict[str, float]:
        """Get GPU memory usage in MB."""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=memory.used,memory.total,utilization.gpu',
                 '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split(',')
                return {
                    'used_mb': float(parts[0]),
                    'total_mb': float(parts[1]),
                    'gpu_util': float(parts[2])
                }
        except Exception as e:
            self.log(f"GPU check failed: {e}", "WARNING")
        return {'used_mb': 0, 'total_mb': 0, 'gpu_util': 0}

    def parse_progress(self) -> Dict:
        """Parse training log for latest progress."""
        try:
            if not self.log_file.exists():
                return {'status': 'no_log', 'progress': 0, 'total': 212468}

            # Read last 100 lines for efficiency
            with open(self.log_file, 'r') as f:
                lines = f.readlines()[-100:]

            # Find latest progress line
            progress_pattern = r'Processing training data:\s+(\d+)%\|.*?\|\s+(\d+)/(\d+)\s+\[.*?\]\s+([\d.]+)\s+examples/s'

            for line in reversed(lines):
                match = re.search(progress_pattern, line)
                if match:
                    percent = int(match.group(1))
                    current = int(match.group(2))
                    total = int(match.group(3))
                    speed = float(match.group(4))
                    return {
                        'status': 'preprocessing',
                        'percent': percent,
                        'current': current,
                        'total': total,
                        'speed': speed
                    }

            # Check if preprocessing just started
            if any('Preparing train dataset' in line for line in lines):
                return {'status': 'starting', 'progress': 0, 'total': 212468}

            # Check if model is loaded
            if any('Model loaded' in line for line in lines):
                return {'status': 'loaded', 'progress': 0, 'total': 212468}

            return {'status': 'unknown', 'progress': 0, 'total': 212468}

        except Exception as e:
            self.log(f"Error parsing progress: {e}", "ERROR")
            return {'status': 'error', 'progress': 0, 'total': 212468}

    def check_stalled(self, progress_info: Dict) -> bool:
        """Check if training has stalled (no progress for 10 minutes)."""
        current_progress = progress_info.get('current', 0)

        if current_progress > self.last_progress:
            self.last_progress = current_progress
            self.last_progress_time = time.time()
            return False

        # No progress for 10 minutes = stalled
        time_since_progress = time.time() - self.last_progress_time
        if time_since_progress > 600:  # 10 minutes
            return True

        return False

    def get_process_memory(self, proc: psutil.Process) -> Dict:
        """Get detailed memory info for process."""
        try:
            mem = proc.memory_info()
            mem_percent = proc.memory_percent()
            return {
                'rss_mb': mem.rss / 1024 / 1024,  # Resident Set Size
                'vms_mb': mem.vms / 1024 / 1024,  # Virtual Memory Size
                'percent': mem_percent,
                'num_threads': proc.num_threads()
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None

    def monitor_iteration(self):
        """Single monitoring iteration."""
        # Find or check process
        if self.process is None or not self.process.is_running():
            self.process = self.find_process()

            if self.process is None:
                self.log("⚠️  Training process NOT RUNNING", "WARNING")
                self.crash_count += 1
                return {
                    'running': False,
                    'crash_count': self.crash_count
                }

        # Get process stats
        mem_info = self.get_process_memory(self.process)
        if mem_info is None:
            self.log("Process died during check", "ERROR")
            self.process = None
            return {'running': False}

        # Get GPU stats
        gpu_info = self.get_gpu_memory()

        # Parse training progress
        progress = self.parse_progress()

        # Check for stalls
        is_stalled = self.check_stalled(progress)

        # Build status report
        status = {
            'running': True,
            'pid': self.process.pid,
            'memory': mem_info,
            'gpu': gpu_info,
            'progress': progress,
            'stalled': is_stalled,
            'uptime_minutes': (datetime.now() - self.start_time).total_seconds() / 60
        }

        # Log current status
        if progress.get('status') == 'preprocessing':
            self.log(
                f"✅ PID {self.process.pid} | "
                f"Progress: {progress['percent']}% ({progress['current']:,}/{progress['total']:,}) | "
                f"Speed: {progress['speed']:.1f} ex/s | "
                f"RAM: {mem_info['rss_mb']:.1f}MB ({mem_info['percent']:.1f}%) | "
                f"GPU: {gpu_info['used_mb']:.0f}/{gpu_info['total_mb']:.0f}MB ({gpu_info['gpu_util']:.0f}%)"
            )
        else:
            self.log(
                f"📊 PID {self.process.pid} | "
                f"Status: {progress.get('status', 'unknown')} | "
                f"RAM: {mem_info['rss_mb']:.1f}MB | "
                f"GPU: {gpu_info['used_mb']:.0f}MB"
            )

        # Warn on issues
        if is_stalled:
            self.log("🛑 STALLED: No progress for 10+ minutes!", "ERROR")

        if mem_info['rss_mb'] > 50000:  # 50GB warning
            self.log(f"⚠️  High memory usage: {mem_info['rss_mb']:.1f}MB", "WARNING")

        if progress.get('speed', 0) < 50 and progress.get('status') == 'preprocessing':
            self.log(f"⚠️  Slow preprocessing: {progress['speed']:.1f} ex/s", "WARNING")

        return status

    def run(self):
        """Main monitoring loop."""
        self.log("=" * 80)
        self.log("🔍 Whisper Training Monitor Started")
        self.log(f"📝 Training log: {self.log_file}")
        self.log(f"📊 Monitor log: {self.monitor_log}")
        self.log(f"⏱️  Check interval: {self.check_interval}s")
        self.log("=" * 80)

        try:
            while True:
                status = self.monitor_iteration()

                if not status['running']:
                    self.log(
                        f"❌ Process not running (crashes: {self.crash_count})",
                        "ERROR"
                    )

                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.log("\n👋 Monitor stopped by user")
        except Exception as e:
            self.log(f"❌ Monitor error: {e}", "ERROR")
            raise


def main():
    """Main entry point."""
    monitor = WhisperTrainingMonitor(
        check_interval=30  # Check every 30 seconds
    )

    monitor.run()


if __name__ == "__main__":
    main()
