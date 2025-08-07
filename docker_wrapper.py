#!/usr/bin/env python3
"""
Docker wrapper script that provides a friendly CLI interface for the production scanner.
Supports both single domain scanning and batch file processing.
"""

import sys
import os
import asyncio
from pathlib import Path
import tempfile
import shutil

# Ensure we can import the production scanner
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/src')

async def main():
    """Main entry point for Docker wrapper."""
    
    if len(sys.argv) < 2:
        print("Pixel Detector - Docker Edition")
        print("\nUsage:")
        print("  Single domain:  docker run pixel-scanner scan <domain>")
        print("  Batch file:     docker run pixel-scanner batch <input_file> <output_dir>")
        print("  Help:           docker run pixel-scanner --help")
        print("\nExamples:")
        print("  docker run --rm pixel-scanner scan google.com")
        print("  docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output \\")
        print("    pixel-scanner batch /app/input/domains.txt /app/output")
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    if command in ['--help', '-h', 'help']:
        print("Pixel Detector - Docker Edition")
        print("\nCommands:")
        print("  scan <domain>     - Scan a single domain")
        print("  batch <file> <output> - Scan multiple domains from file")
        print("\nOptions for batch mode:")
        print("  --concurrent N    - Max concurrent scans (default: 5)")
        print("  --timeout N       - Timeout in ms (default: 30000)")
        print("  --no-variations   - Don't try URL variations")
        sys.exit(0)
    
    elif command == 'scan':
        # Single domain scan mode
        if len(sys.argv) < 3:
            print("Error: Please provide a domain to scan")
            print("Usage: docker run pixel-scanner scan <domain>")
            sys.exit(1)
        
        domain = sys.argv[2]
        
        # Create temporary input file with single domain
        temp_dir = Path("/tmp/scan_temp")
        temp_dir.mkdir(exist_ok=True)
        
        input_file = temp_dir / "single_domain.txt"
        output_dir = temp_dir / "output"
        output_dir.mkdir(exist_ok=True)
        
        # Write domain to temp file
        with open(input_file, 'w') as f:
            f.write(domain + '\n')
        
        print(f"Scanning {domain}...")
        
        # Import and run production scanner
        from production_scanner import ProductionScanner
        
        scanner = ProductionScanner(
            input_file=input_file,
            output_dir=output_dir,
            mode="ondemand",
            max_concurrent=1,
            timeout_ms=30000,
            try_variations=True
        )
        
        scanner.preprocess_input()
        await scanner.run_scanner()
        scanner.generate_output()
        
        # Read and display results
        results_file = output_dir / "scan_results.csv"
        if results_file.exists():
            print("\n" + "=" * 60)
            with open(results_file, 'r') as f:
                import csv
                reader = csv.DictReader(f)
                for row in reader:
                    if row['status'] == 'success':
                        if row['pixels_detected']:
                            print(f"✅ Found pixels: {row['pixels_detected']}")
                            print(f"   Risk levels: {row['risk_levels']}")
                        else:
                            print("✅ No tracking pixels detected")
                    else:
                        print(f"❌ Scan failed: {row.get('error', 'Unknown error')}")
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    elif command == 'batch':
        # Batch file scan mode - pass through to production scanner
        if len(sys.argv) < 4:
            print("Error: Batch mode requires input file and output directory")
            print("Usage: docker run pixel-scanner batch <input_file> <output_dir>")
            sys.exit(1)
        
        # Import and run production scanner with all arguments
        from production_scanner import main as prod_main
        
        # Adjust sys.argv to match production scanner expectations
        sys.argv = ['production_scanner.py'] + sys.argv[2:]
        await prod_main()
    
    else:
        # Assume it's a file path for backward compatibility
        # This handles: docker run pixel-scanner /app/input/file.txt /app/output
        if len(sys.argv) >= 3 and Path(sys.argv[1]).suffix in ['.txt', '.csv']:
            from production_scanner import main as prod_main
            sys.argv = ['production_scanner.py'] + sys.argv[1:]
            await prod_main()
        else:
            print(f"Error: Unknown command '{command}'")
            print("Use --help for usage information")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())