"""
Simple local batch manager for processing 15K domains on a laptop.
Features: checkpointing, resume capability, progress monitoring, parallel processing.
"""
import asyncio
import json
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .logging_config import get_logger
from .scanner import PixelScanner

logger = get_logger(__name__)


class LocalBatchManager:
    """Manage large batch scans on local machine with monitoring"""
    
    def __init__(
        self,
        max_concurrent: int = 3,  # Conservative for laptop
        checkpoint_every: int = 50,  # Save progress every 50 domains
        results_dir: str = "results",
    ):
        self.max_concurrent = max_concurrent
        self.checkpoint_every = checkpoint_every
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # Progress tracking
        self.completed: set[str] = set()
        self.failed: dict[str, str] = {}
        self.start_time: float = 0
        self.last_checkpoint_time: float = 0
        
        # Graceful shutdown
        self.should_stop = False
        signal.signal(signal.SIGINT, self._handle_shutdown)
    
    def _handle_shutdown(self, signum: int, frame: Any) -> None:
        """Allow Ctrl+C to gracefully stop"""
        print("\n⚠️  Graceful shutdown initiated. Saving progress...")
        self.should_stop = True
    
    def _load_progress(self, batch_name: str) -> list[str]:
        """Load previous progress if exists"""
        progress_file = self.results_dir / f"{batch_name}_progress.json"
        if progress_file.exists():
            with open(progress_file) as f:
                data = json.load(f)
                self.completed = set(data.get("completed", []))
                self.failed = data.get("failed", {})
                logger.info(f"Resumed: {len(self.completed)} completed, {len(self.failed)} failed")
                return list(data.get("remaining", []))
        return []
    
    def _save_progress(self, batch_name: str, all_domains: list[str]) -> None:
        """Save current progress"""
        remaining = [d for d in all_domains if d not in self.completed and d not in self.failed]
        progress_data = {
            "batch_name": batch_name,
            "total": len(all_domains),
            "completed": list(self.completed),
            "failed": self.failed,
            "remaining": remaining,
            "timestamp": datetime.now().isoformat(),
            "elapsed_hours": (time.time() - self.start_time) / 3600,
        }
        
        progress_file = self.results_dir / f"{batch_name}_progress.json"
        temp_file = progress_file.with_suffix(".tmp")
        with open(temp_file, "w") as f:
            json.dump(progress_data, f, indent=2)
        temp_file.replace(progress_file)
        
        self.last_checkpoint_time = time.time()
    
    def _print_status(self, total_domains: int) -> None:
        """Print current status with ETA"""
        processed = len(self.completed) + len(self.failed)
        if processed == 0:
            return
        
        elapsed = time.time() - self.start_time
        rate = processed / elapsed
        remaining = total_domains - processed
        eta_seconds = remaining / rate if rate > 0 else 0
        
        success_rate = (len(self.completed) / processed * 100) if processed > 0 else 0
        
        # Clear line and print status
        print(f"\r📊 Progress: {processed}/{total_domains} ({processed/total_domains*100:.1f}%) | "
              f"✅ Success: {success_rate:.1f}% | "
              f"⚡ Rate: {rate*60:.1f}/min | "
              f"⏱️ ETA: {timedelta(seconds=int(eta_seconds))}", end="", flush=True)
    
    async def scan_batch(
        self,
        domains_file: str,
        batch_name: str,
        resume: bool = True,
        scanner_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Scan a batch of domains from file"""
        self.start_time = time.time()
        
        # Load domains
        with open(domains_file) as f:
            all_domains = [line.strip() for line in f if line.strip()]
        
        logger.info(f"📋 Loaded {len(all_domains)} domains from {domains_file}")
        
        # Check for resume
        if resume:
            remaining = self._load_progress(batch_name)
            if remaining:
                domains_to_scan = remaining
                logger.info(f"♻️  Resuming with {len(domains_to_scan)} remaining domains")
            else:
                domains_to_scan = all_domains
        else:
            domains_to_scan = all_domains
            self.completed.clear()
            self.failed.clear()
        
        # Create output directory for this batch
        batch_dir = self.results_dir / batch_name
        batch_dir.mkdir(exist_ok=True)
        
        # Initialize scanner with laptop-friendly settings
        scanner_config = scanner_config or {}
        scanner = PixelScanner(
            max_concurrent_scans=self.max_concurrent,
            timeout=30000,  # 30 seconds
            headless=True,
            stealth_mode=True,
            screenshot=False,  # Save disk space
            pre_check_health=True,  # Skip dead domains
            max_retries=1,  # Minimal retries to save time
            **scanner_config
        )
        
        # Process in chunks for memory efficiency
        chunk_size = 20
        print(f"\n🚀 Starting scan of {len(domains_to_scan)} domains")
        print(f"   Max concurrent: {self.max_concurrent}")
        print(f"   Checkpoint every: {self.checkpoint_every} domains")
        print("   Press Ctrl+C to pause (progress will be saved)\n")
        
        try:
            for i in range(0, len(domains_to_scan), chunk_size):
                if self.should_stop:
                    break
                
                chunk = domains_to_scan[i:i + chunk_size]
                
                # Scan chunk
                results = await scanner.scan_multiple(chunk)
                
                # Process results
                for result in results:
                    if result.success:
                        self.completed.add(result.domain)
                        
                        # Save successful results
                        output_file = batch_dir / f"{result.domain.replace('.', '_')}.json"
                        with open(output_file, "w") as f:
                            json.dump(result.model_dump(), f, indent=2, default=str)
                    else:
                        self.failed[result.domain] = result.error_message or "Unknown error"
                
                # Update progress display
                self._print_status(len(all_domains))
                
                # Checkpoint periodically
                if (len(self.completed) + len(self.failed)) % self.checkpoint_every == 0:
                    self._save_progress(batch_name, all_domains)
                
                # Brief pause between chunks
                await asyncio.sleep(0.5)
        
        except KeyboardInterrupt:
            logger.warning("Interrupted by user")
        finally:
            # Final save
            self._save_progress(batch_name, all_domains)
            print("\n")  # New line after progress
        
        # Generate summary
        total_processed = len(self.completed) + len(self.failed)
        elapsed = time.time() - self.start_time
        
        summary = {
            "batch_name": batch_name,
            "total_domains": len(all_domains),
            "processed": total_processed,
            "completed": len(self.completed),
            "failed": len(self.failed),
            "skipped": len(all_domains) - total_processed,
            "success_rate": (len(self.completed) / total_processed * 100) if total_processed > 0 else 0,
            "elapsed_hours": elapsed / 3600,
            "domains_per_minute": (total_processed / elapsed * 60) if elapsed > 0 else 0,
            "estimated_total_hours": (
                (elapsed / total_processed * len(all_domains) / 3600) if total_processed > 0 else 0
            ),
            "timestamp": datetime.now().isoformat(),
        }
        
        # Save summary
        summary_file = self.results_dir / f"{batch_name}_summary.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)
        
        # Print final summary
        print("\n" + "="*60)
        print("📊 SCAN SUMMARY")
        print("="*60)
        print(f"Total domains: {len(all_domains)}")
        print(f"Processed: {total_processed}")
        print(f"✅ Successful: {len(self.completed)}")
        print(f"❌ Failed: {len(self.failed)}")
        print(f"⏭️  Skipped: {len(all_domains) - total_processed}")
        print(f"Success rate: {summary['success_rate']:.1f}%")
        print(f"Time elapsed: {summary['elapsed_hours']:.2f} hours")
        print(f"Scan rate: {summary['domains_per_minute']:.1f} domains/minute")
        print("="*60)
        
        if len(self.failed) > 0:
            print(f"\n⚠️  Failed domains saved to: {self.results_dir}/{batch_name}_progress.json")
        
        return summary


# CLI interface for easy execution
async def main() -> None:
    """Simple CLI for batch scanning"""
    
    if len(sys.argv) < 3:
        print("Usage: python -m pixel_detector.batch_manager <domains_file> <batch_name>")
        print("Example: python -m pixel_detector.batch_manager clients/portfolio.txt client_scan_2025")
        sys.exit(1)
    
    domains_file = sys.argv[1]
    batch_name = sys.argv[2]
    
    manager = LocalBatchManager(
        max_concurrent=3,  # Adjust based on your laptop
        checkpoint_every=50,
        results_dir="scan_results"
    )
    
    await manager.scan_batch(domains_file, batch_name, resume=True)


if __name__ == "__main__":
    asyncio.run(main())