#!/usr/bin/env python3
"""
Real-time monitoring dashboard for large batch scans.
Run this in a separate terminal while scanning.
"""
import json
import time
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
CLEAR = '\033[2J\033[H'


class ScanMonitor:
    """Monitor ongoing batch scans with live dashboard"""
    
    def __init__(self, results_dir: str = "scan_results"):
        self.results_dir = Path(results_dir)
    
    def get_latest_batch(self) -> Optional[str]:
        """Find the most recently modified progress file"""
        progress_files = list(self.results_dir.glob("*_progress.json"))
        if not progress_files:
            return None
        
        latest = max(progress_files, key=lambda p: p.stat().st_mtime)
        return latest.stem.replace("_progress", "")
    
    def load_progress(self, batch_name: str) -> dict:
        """Load current progress data"""
        progress_file = self.results_dir / f"{batch_name}_progress.json"
        if not progress_file.exists():
            return {}
        
        try:
            with open(progress_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def format_time(self, seconds: float) -> str:
        """Format seconds into human readable time"""
        return str(timedelta(seconds=int(seconds)))
    
    def print_dashboard(self, batch_name: str) -> None:
        """Print monitoring dashboard"""
        data = self.load_progress(batch_name)
        if not data:
            print(f"No data found for batch: {batch_name}")
            return
        
        # Calculate statistics
        total = data.get('total', 0)
        completed = len(data.get('completed', []))
        failed = len(data.get('failed', {}))
        processed = completed + failed
        remaining = total - processed
        
        # Time calculations
        elapsed_hours = data.get('elapsed_hours', 0)
        elapsed_seconds = elapsed_hours * 3600
        
        if processed > 0 and elapsed_seconds > 0:
            rate = processed / elapsed_seconds
            domains_per_minute = rate * 60
            eta_seconds = remaining / rate if rate > 0 else 0
            success_rate = (completed / processed) * 100
        else:
            domains_per_minute = 0
            eta_seconds = 0
            success_rate = 0
        
        # Clear screen and print dashboard
        print(CLEAR)
        print("="*70)
        print(f"{BLUE}🖥️  PIXEL DETECTOR SCAN MONITOR{RESET}")
        print("="*70)
        print(f"\n📁 Batch: {batch_name}")
        print(f"🕒 Last Update: {data.get('timestamp', 'Unknown')}")
        print(f"\n{'-'*70}")
        
        # Progress bar
        progress = processed / total if total > 0 else 0
        bar_length = 40
        filled = int(bar_length * progress)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"\n📊 Progress: [{bar}] {progress*100:.1f}%")
        print(f"   {processed:,} / {total:,} domains")
        
        print(f"\n{'-'*70}")
        
        # Statistics
        print("\n📈 Statistics:")
        print(f"   {GREEN}✅ Successful:{RESET} {completed:,}")
        print(f"   {RED}❌ Failed:{RESET} {failed:,}")
        print(f"   {YELLOW}⏭️  Remaining:{RESET} {remaining:,}")
        print(f"   📏 Success Rate: {success_rate:.1f}%")
        
        print(f"\n⚡ Performance:")
        print(f"   ⏱️  Elapsed: {self.format_time(elapsed_seconds)}")
        print(f"   🚀 Rate: {domains_per_minute:.1f} domains/minute")
        
        if remaining > 0:
            print(f"   ⏳ ETA: {self.format_time(eta_seconds)}")
            eta_time = datetime.now() + timedelta(seconds=eta_seconds)
            print(f"   🏁 Estimated Completion: {eta_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Recent failures
        if failed > 0:
            print(f"\n{RED}Recent Failures:{RESET}")
            failed_domains = list(data.get('failed', {}).items())[-5:]
            for domain, error in failed_domains:
                print(f"   • {domain}: {error[:50]}...")
        
        # File locations
        print(f"\n📂 Output Directory: {self.results_dir / batch_name}")
        print(f"📄 Progress File: {self.results_dir / f'{batch_name}_progress.json'}")
        
        print("\n" + "="*70)
        print("Press Ctrl+C to exit monitor (scan will continue)")
    
    def run(self, batch_name: Optional[str] = None, refresh_seconds: int = 5):
        """Run the monitoring dashboard"""
        if not batch_name:
            batch_name = self.get_latest_batch()
            if not batch_name:
                print("No active scans found. Please specify a batch name.")
                return
        
        print(f"Monitoring batch: {batch_name}")
        print(f"Refreshing every {refresh_seconds} seconds...")
        time.sleep(2)
        
        try:
            while True:
                self.print_dashboard(batch_name)
                time.sleep(refresh_seconds)
        except KeyboardInterrupt:
            print("\n\nMonitor stopped. Scan continues in background.")


def main():
    """CLI entry point"""
    if len(sys.argv) > 1:
        batch_name = sys.argv[1]
        monitor = ScanMonitor()
        monitor.run(batch_name)
    else:
        monitor = ScanMonitor()
        monitor.run()


if __name__ == "__main__":
    main()