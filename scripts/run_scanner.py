#!/usr/bin/env python3
"""
Run the Cautus Scanner end-to-end.

Usage:
    python scripts/run_scanner.py
"""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from scanner import ScannerModule

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)


def main():
    """Run a single scan cycle."""
    config_path = Path(__file__).parent.parent / "scanner.yaml"
    
    logger.info(f"Loading config from: {config_path}")
    
    try:
        # Create scanner from config
        scanner = ScannerModule.from_config(str(config_path))
        
        logger.info("Starting scan...")
        results = scanner.scan()
        
        # Print results
        print("\n" + "=" * 60)
        print("SCAN RESULTS")
        print("=" * 60)
        
        if not results:
            print("No symbols passed all pillars.")
        else:
            for result in results:
                status = "✅ PASSED" if result.passed_all else "❌ FAILED"
                print(f"\n{result.symbol} - {status}")
                print(f"  Price: ${result.price:.2f}")
                print(f"  % Change: {result.pct_change:+.2f}%")
                print(f"  RVol: {result.relative_volume:.2f}x")
                print(f"  Float: {result.float_shares:,}" if result.float_shares else "  Float: N/A")
                print(f"  Catalyst: {result.catalyst}" if result.catalyst else "  Catalyst: None")
                print(f"  Passed: {', '.join(result.passed_pillars)}")
                print(f"  Failed: {', '.join(result.failed_pillars)}" if result.failed_pillars else "")
        
        print("\n" + "=" * 60)
        logger.info("Scan complete!")
        
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        raise


if __name__ == "__main__":
    main()
