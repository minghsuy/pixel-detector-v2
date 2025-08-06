"""
Enterprise-grade batch processor for large-scale domain scanning.
Handles 15K+ domains with checkpointing, resumability, and fault tolerance.
"""
import asyncio
import json
import signal
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from .logging_config import get_logger
from .scanner import PixelScanner

logger = get_logger(__name__)


class BatchProcessor:
    """Process large batches of domains with checkpoint/resume capability"""
    
    def __init__(
        self,
        checkpoint_dir: str = "checkpoints",
        max_concurrent: int = 5,
        checkpoint_interval: int = 100,
        scanner_config: dict[str, Any] | None = None,
    ):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)
        self.max_concurrent = max_concurrent
        self.checkpoint_interval = checkpoint_interval
        self.scanner_config = scanner_config or {}
        
        # State tracking
        self.completed_domains: set[str] = set()
        self.failed_domains: dict[str, str] = {}
        self.in_progress: set[str] = set()
        self.start_time: float = 0
        self.checkpoint_file: Path | None = None
        self.should_stop = False
        
        # Setup graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
    
    def _handle_shutdown(self, signum: int, frame: Any) -> None:
        """Handle graceful shutdown on SIGINT/SIGTERM"""
        logger.warning(f"Received signal {signum}, initiating graceful shutdown...")
        self.should_stop = True
    
    def _create_checkpoint_filename(self, batch_id: str) -> Path:
        """Create checkpoint filename with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.checkpoint_dir / f"checkpoint_{batch_id}_{timestamp}.json"
    
    def save_checkpoint(self, domains_list: list[str], batch_id: str) -> None:
        """Save current progress to checkpoint file"""
        checkpoint_data = {
            "batch_id": batch_id,
            "total_domains": len(domains_list),
            "completed": list(self.completed_domains),
            "failed": self.failed_domains,
            "remaining": [d for d in domains_list if d not in self.completed_domains],
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": time.time() - self.start_time,
            "stats": {
                "completed_count": len(self.completed_domains),
                "failed_count": len(self.failed_domains),
                "success_rate": (
                    len(self.completed_domains) / 
                    max(len(self.completed_domains) + len(self.failed_domains), 1)
                ),
            }
        }
        
        if not self.checkpoint_file:
            self.checkpoint_file = self._create_checkpoint_filename(batch_id)
        
        # Write atomically to avoid corruption
        temp_file = self.checkpoint_file.with_suffix(".tmp")
        with open(temp_file, "w") as f:
            json.dump(checkpoint_data, f, indent=2)
        temp_file.replace(self.checkpoint_file)
        
        logger.info(f"Checkpoint saved: {len(self.completed_domains)}/{len(domains_list)} completed")
    
    def load_checkpoint(self, checkpoint_file: str) -> tuple[list[str], str]:
        """Load progress from checkpoint file"""
        checkpoint_path = Path(checkpoint_file)
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint file not found: {checkpoint_file}")
        
        with open(checkpoint_path) as f:
            data = json.load(f)
        
        self.completed_domains = set(data["completed"])
        self.failed_domains = data["failed"]
        self.checkpoint_file = checkpoint_path
        
        logger.info(
            f"Resumed from checkpoint: {len(self.completed_domains)} completed, "
            f"{len(data['remaining'])} remaining"
        )
        
        return data["remaining"], data["batch_id"]
    
    async def process_batch(
        self,
        domains: list[str],
        output_dir: str,
        batch_id: str,
        resume_from: str | None = None,
    ) -> dict[str, Any]:
        """Process a batch of domains with checkpointing"""
        self.start_time = time.time()
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Load checkpoint if resuming
        if resume_from:
            domains, batch_id = self.load_checkpoint(resume_from)
        
        # Create scanner with memory-efficient settings
        scanner = PixelScanner(
            max_concurrent_scans=self.max_concurrent,
            pre_check_health=True,  # Skip unreachable domains
            timeout=60000,  # 60 second timeout
            **self.scanner_config
        )
        
        # Process domains in chunks to prevent memory buildup
        chunk_size = 50
        all_results = []
        
        for i in range(0, len(domains), chunk_size):
            if self.should_stop:
                logger.warning("Graceful shutdown requested, saving checkpoint...")
                self.save_checkpoint(domains, batch_id)
                break
            
            chunk = domains[i:i + chunk_size]
            logger.info(f"Processing chunk {i//chunk_size + 1}/{(len(domains) + chunk_size - 1)//chunk_size}")
            
            # Filter out already completed domains
            chunk_to_process = [d for d in chunk if d not in self.completed_domains]
            
            if not chunk_to_process:
                continue
            
            # Process chunk
            try:
                results = await scanner.scan_multiple(chunk_to_process)
                
                # Save results immediately
                for result in results:
                    if result.success:
                        self.completed_domains.add(result.domain)
                    else:
                        self.failed_domains[result.domain] = result.error_message or "Unknown error"
                    
                    # Save individual result
                    result_file = output_path / f"{result.domain.replace('.', '_')}.json"
                    with open(result_file, "w") as f:
                        json.dump(result.model_dump(), f, indent=2, default=str)
                    
                    all_results.append(result)
                
                # Checkpoint every N domains
                if len(self.completed_domains) % self.checkpoint_interval == 0:
                    self.save_checkpoint(domains, batch_id)
                
                # Log progress
                total_processed = len(self.completed_domains) + len(self.failed_domains)
                if total_processed > 0:
                    success_rate = len(self.completed_domains) / total_processed * 100
                    elapsed = time.time() - self.start_time
                    rate = total_processed / elapsed
                    eta = (len(domains) - total_processed) / rate if rate > 0 else 0
                    
                    logger.info(
                        f"Progress: {total_processed}/{len(domains)} "
                        f"({success_rate:.1f}% success rate, "
                        f"{rate:.1f} domains/sec, ETA: {eta/3600:.1f} hours)"
                    )
                
            except Exception as e:
                logger.error(f"Chunk processing failed: {e}")
                # Mark chunk as failed but continue
                for domain in chunk_to_process:
                    self.failed_domains[domain] = str(e)
            
            # Force garbage collection between chunks
            import gc
            gc.collect()
            
            # Small delay between chunks
            await asyncio.sleep(1)
        
        # Final checkpoint
        self.save_checkpoint(domains, batch_id)
        
        # Generate summary report
        summary = {
            "batch_id": batch_id,
            "total_domains": len(domains),
            "completed": len(self.completed_domains),
            "failed": len(self.failed_domains),
            "success_rate": (
                len(self.completed_domains) / 
                max(len(self.completed_domains) + len(self.failed_domains), 1)
            ),
            "elapsed_time": time.time() - self.start_time,
            "domains_per_second": len(self.completed_domains) / (time.time() - self.start_time),
            "timestamp": datetime.now().isoformat(),
            "checkpoint_file": str(self.checkpoint_file),
        }
        
        summary_file = output_path / f"batch_summary_{batch_id}.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Batch processing complete: {summary}")
        
        return summary