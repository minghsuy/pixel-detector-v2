import asyncio
import json
from pathlib import Path
from typing import Optional

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
    
    # Read input file - support both TXT and CSV
    import csv
    import re
    from datetime import datetime
    
    # List of tuples: (custom_id, original_url, normalized_domain)
    domains_to_scan: list[tuple[str, str, str | None]] = []
    
    if input_file.suffix.lower() == ".csv":
        # CSV mode with custom_id,url columns
        with open(input_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames or "custom_id" not in reader.fieldnames or "url" not in reader.fieldnames:
                logger.error("Error: CSV must have 'custom_id' and 'url' columns")
                raise typer.Exit(1)
            
            for row in reader:
                custom_id = row["custom_id"].strip()
                url = row["url"].strip()
                
                if custom_id and url:
                    # Basic URL normalization
                    domain = url.lower()
                    # Remove common prefixes
                    domain = re.sub(r"^(https?://)?(www\.)?", "", domain)
                    # Remove trailing slashes and paths
                    domain = domain.split("/")[0]
                    # Remove port numbers
                    domain = domain.split(":")[0]
                    
                    # Basic validation
                    if "." in domain and len(domain) > 3:
                        domains_to_scan.append((custom_id, url, domain))
                    else:
                        domains_to_scan.append((custom_id, url, None))  # Invalid domain
    else:
        # TXT mode - one domain per line
        with open(input_file) as f:
            for line_num, line in enumerate(f, 1):
                domain = line.strip()
                if domain and not domain.startswith("#"):
                    # Use line number as custom_id for TXT files
                    custom_id = f"LINE_{line_num}"
                    # Basic normalization
                    clean_domain = domain.lower()
                    clean_domain = re.sub(r"^(https?://)?(www\.)?", "", clean_domain)
                    clean_domain = clean_domain.split("/")[0].split(":")[0]
                    domains_to_scan.append((custom_id, domain, clean_domain))
    
    if not domains_to_scan:
        logger.error("Error: No domains found in input file")
        raise typer.Exit(1)
    
    # Extract valid domains for scanning
    valid_domains = [d[2] for d in domains_to_scan if d[2]]
    invalid_count = len([d for d in domains_to_scan if not d[2]])
    
    if invalid_count > 0:
        logger.warning(f"Found {invalid_count} invalid domain(s) that will be marked as rejected")
    
    logger.info(f"Found {len(valid_domains)} valid domains to scan")
    
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
    
    # Run scans on valid domains only
    results = asyncio.run(scanner.scan_multiple(valid_domains)) if valid_domains else []
    
    # Create a map of domain -> result for joining
    results_map = {r.domain: r for r in results}
    
    # Save CSV output with custom_id joined back
    csv_output = output_dir / "scan_results.csv"
    with open(csv_output, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "custom_id", "url", "domain", "scan_status", "has_pixel", 
            "pixel_count", "pixel_names", "timestamp", "duration_seconds", "error"
        ])
        
        scan_timestamp = datetime.now().isoformat() + "Z"
        
        for custom_id, original_url, domain in domains_to_scan:
            if not domain:
                # Invalid domain
                writer.writerow([
                    custom_id, original_url, "", "rejected", 0, 0, "", 
                    scan_timestamp, 0, "Invalid domain format"
                ])
            elif domain in results_map:
                result = results_map[domain]
                pixel_names = "|".join([p.type.value for p in result.pixels_detected])
                duration = result.scan_metadata.scan_duration if result.scan_metadata else 0
                
                writer.writerow([
                    custom_id, original_url, domain, 
                    "success" if result.success else "failed",
                    1 if result.pixels_detected else 0,
                    len(result.pixels_detected),
                    pixel_names,
                    result.timestamp.isoformat() + "Z" if result.timestamp else scan_timestamp,
                    f"{duration:.2f}",
                    result.error_message or ""
                ])
            else:
                # Domain was valid but not in results
                writer.writerow([
                    custom_id, original_url, domain, "not_scanned", 0, 0, "",
                    scan_timestamp, 0, "Scan skipped or failed"
                ])
    
    # Also save individual JSON results for backward compatibility
    for result in results:
        domain_file = output_dir / f"{result.domain.replace('.', '_')}.json"
        with open(domain_file, "w") as f:
            json.dump(result.model_dump(), f, indent=2, default=str)
    
    # Save summary JSON
    summary = []
    for custom_id, _, domain in domains_to_scan:
        if domain and domain in results_map:
            result = results_map[domain]
            summary.append({
                "custom_id": custom_id,
                "domain": result.domain,
                "pixels_found": len(result.pixels_detected),
                "pixel_types": [p.type.value for p in result.pixels_detected],
                "success": result.success,
            })
    
    summary_file = output_dir / "summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    
    # Print summary table
    table = Table(title="Batch Scan Summary")
    table.add_column("Custom ID", style="cyan")
    table.add_column("Domain", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Pixels", style="yellow")
    table.add_column("Types", style="red")
    
    for custom_id, original_url, domain in domains_to_scan[:10]:  # Show first 10
        if domain and domain in results_map:
            result = results_map[domain]
            pixel_names = "|".join([p.type.value for p in result.pixels_detected])
            table.add_row(
                custom_id,
                domain,
                "✓" if result.success else "✗",
                str(len(result.pixels_detected)),
                pixel_names if pixel_names else "None"
            )
        elif domain:
            table.add_row(custom_id, domain, "⚠", "0", "Not scanned")
        else:
            table.add_row(custom_id, original_url[:30], "✗", "0", "Invalid")
    
    if len(domains_to_scan) > 10:
        console.print(f"[dim]... and {len(domains_to_scan) - 10} more[/dim]")
    
    console.print(table)
    logger.info(f"\nResults saved to {output_dir}/")
    logger.info(f"CSV output: {csv_output}")


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