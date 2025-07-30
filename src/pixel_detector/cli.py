import asyncio
import json
from pathlib import Path
from typing import Any, Optional

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .logging_config import get_logger, setup_cli_logging
from .scanner import PixelScanner

app = typer.Typer(
    name="pixel-detector",
    help="Detect tracking pixels on healthcare websites",
    add_completion=False,
)
console = Console()
logger = get_logger(__name__)

# Set up CLI logging on module import
setup_cli_logging()


def version_callback(value: bool) -> None:
    if value:
        # Use print for version info to ensure it's always shown
        print(f"pixel-detector version {__version__}")
        raise typer.Exit()


@app.command()
def scan(
    domain: str = typer.Argument(..., help="Domain to scan (e.g., example.com)"),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output file path for JSON results"
    ),
    screenshot: bool = typer.Option(
        False, "--screenshot", "-s", help="Take screenshot of the page"
    ),
    headless: bool = typer.Option(
        True, "--headless/--no-headless", help="Run browser in headless mode"
    ),
    no_stealth: bool = typer.Option(
        False, "--no-stealth", help="Disable stealth mode"
    ),
    timeout: int = typer.Option(
        30000, "--timeout", "-t", help="Page load timeout in milliseconds"
    ),
    pretty: bool = typer.Option(
        False, "--pretty", "-p", help="Pretty print JSON output"
    ),
    max_retries: int = typer.Option(
        3, "--max-retries", help="Maximum number of retries for failed scans"
    ),
) -> None:
    """Scan a single domain for tracking pixels"""
    scanner = PixelScanner(
        headless=headless,
        stealth_mode=not no_stealth,
        screenshot=screenshot,
        timeout=timeout,
        max_retries=max_retries,
    )
    
    # Run the scan
    result = asyncio.run(scanner.scan_domain(domain))
    
    # Save or print results
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w") as f:
            if pretty:
                json.dump(result.model_dump(), f, indent=2, default=str)
            else:
                json.dump(result.model_dump(), f, default=str)
        logger.info(f"Results saved to {output}")
    else:
        # Print summary table
        table = Table(title=f"Scan Results for {domain}")
        table.add_column("Pixel Type", style="cyan")
        table.add_column("Risk Level", style="yellow")
        table.add_column("HIPAA Concern", style="red")
        table.add_column("Evidence", style="green")
        
        for pixel in result.pixels_detected:
            evidence_count = (
                len(pixel.evidence.network_requests) +
                len(pixel.evidence.script_tags) +
                len(pixel.evidence.cookies_set)
            )
            table.add_row(
                str(pixel.type.value),
                str(pixel.risk_level.value),
                "Yes" if pixel.hipaa_concern else "No",
                f"{evidence_count} items",
            )
        
        console.print(table)
        
        # Print metadata
        logger.info(f"\nScan completed in {result.scan_metadata.scan_duration:.2f}s")
        logger.info(f"Total requests: {result.scan_metadata.total_requests}")
        logger.info(f"Tracking requests: {result.scan_metadata.tracking_requests}")
        
        if pretty:
            console.print("\nFull JSON output:")
            console.print_json(json.dumps(result.model_dump(), default=str))


@app.command()
def batch(
    input_file: Path,
    output_dir: Path = typer.Option(
        Path("results"), "--output-dir", "-o", help="Output directory for results"
    ),
    screenshot: bool = typer.Option(
        False, "--screenshot", "-s", help="Take screenshots of pages"
    ),
    headless: bool = typer.Option(
        True, "--headless/--no-headless", help="Run browser in headless mode"
    ),
    no_stealth: bool = typer.Option(
        False, "--no-stealth", help="Disable stealth mode"
    ),
    timeout: int = typer.Option(
        30000, "--timeout", "-t", help="Page load timeout in milliseconds"
    ),
    max_retries: int = typer.Option(
        3, "--max-retries", help="Maximum number of retries for failed scans"
    ),
    max_concurrent: int = typer.Option(
        5, "--max-concurrent", "-c", help="Maximum concurrent scans"
    ),
    no_health_check: bool = typer.Option(
        False, "--no-health-check", help="Skip pre-scan health checks"
    ),
) -> None:
    """Scan multiple domains from a file"""
    if not input_file.exists():
        logger.error(f"Error: Input file {input_file} not found")
        raise typer.Exit(1)
    
    # Read domains
    domains = []
    with open(input_file) as f:
        for line in f:
            domain = line.strip()
            if domain and not domain.startswith("#"):
                domains.append(domain)
    
    if not domains:
        logger.error("Error: No domains found in input file")
        raise typer.Exit(1)
    
    logger.info(f"Found {len(domains)} domains to scan")
    
    scanner = PixelScanner(
        headless=headless,
        stealth_mode=not no_stealth,
        screenshot=screenshot,
        timeout=timeout,
        max_retries=max_retries,
        max_concurrent_scans=max_concurrent,
        pre_check_health=not no_health_check,
    )
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run scans
    results = asyncio.run(scanner.scan_multiple(domains))
    
    # Save results
    summary: list[dict[str, Any]] = []
    for result in results:
        # Save individual result
        domain_file = output_dir / f"{result.domain.replace('.', '_')}.json"
        with open(domain_file, "w") as f:
            json.dump(result.model_dump(), f, indent=2, default=str)
        
        # Add to summary
        summary.append({
            "domain": result.domain,
            "pixels_found": len(result.pixels_detected),
            "pixel_types": [p.type.value for p in result.pixels_detected],
            "success": result.success,
        })
    
    # Save summary
    summary_file = output_dir / "summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    
    # Print summary table
    table = Table(title="Batch Scan Summary")
    table.add_column("Domain", style="cyan")
    table.add_column("Pixels Found", style="yellow")
    table.add_column("Types", style="red")
    table.add_column("Status", style="green")
    
    for item in summary:
        table.add_row(
            str(item["domain"]),
            str(item["pixels_found"]),
            ", ".join(str(t) for t in item["pixel_types"]) if item["pixel_types"] else "None",
            "✓" if item["success"] else "✗",
        )
    
    console.print(table)
    logger.info(f"\nResults saved to {output_dir}/")


@app.command()
def list_detectors() -> None:
    """List all available pixel detectors"""
    from .detectors import DETECTOR_REGISTRY, register_all_detectors
    
    register_all_detectors()
    
    table = Table(title="Available Pixel Detectors")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="yellow")
    
    for name, detector_class in DETECTOR_REGISTRY.items():
        detector = detector_class()
        table.add_row(name, str(detector.pixel_type.value))
    
    console.print(table)


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", "-v", callback=version_callback, help="Show version"
    ),
) -> None:
    """Healthcare Pixel Tracking Detection System"""
    pass


if __name__ == "__main__":
    app()