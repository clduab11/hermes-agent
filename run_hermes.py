#!/usr/bin/env python3
"""
HERMES System Launcher - Unified entry point for different system modes.
"""
import argparse
import sys
import uvicorn
from typing import Optional

from hermes.config import settings


def run_full_system(
    host: str = None, 
    port: int = None,
    reload: bool = None
):
    """Run the full HERMES system with all components."""
    print("🚀 Starting HERMES AI Voice Agent - Full System Mode")
    print("   Features: Voice Processing, Dashboard, Analytics, MCP, Workflows")
    
    uvicorn.run(
        "hermes.main:app",
        host=host or settings.api_host,
        port=port or settings.api_port,
        reload=reload if reload is not None else settings.debug,
        log_level="info" if not settings.debug else "debug"
    )


def run_dashboard_only(
    host: str = None,
    port: int = None,
    reload: bool = None
):
    """Run dashboard-only mode for testing/demo."""
    print("📊 Starting HERMES Dashboard - Demo Mode")
    print("   Features: Dashboard UI, Analytics API, Mock Data")
    
    # Set environment variable to indicate dashboard-only mode
    import os
    os.environ["HERMES_DASHBOARD_ONLY"] = "true"
    
    uvicorn.run(
        "hermes.main:app",
        host=host or "0.0.0.0",
        port=port or 8000,
        reload=reload if reload is not None else True,
        log_level="info"
    )


def main():
    """Main entry point with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="HERMES AI Voice Agent System Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Run full system
  %(prog)s --dashboard-only         # Run dashboard only for demo
  %(prog)s --port 8080              # Run on custom port
  %(prog)s --host 127.0.0.1         # Run on custom host
  %(prog)s --no-reload              # Disable auto-reload
        """
    )
    
    parser.add_argument(
        "--dashboard-only",
        action="store_true",
        help="Run in dashboard-only mode (for testing/demo)"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        help="Host to bind to (default: from config)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        help="Port to bind to (default: from config)"
    )
    
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable auto-reload (useful for production)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    args = parser.parse_args()
    
    # Override settings if debug flag is provided
    if args.debug:
        import os
        os.environ["DEBUG"] = "true"
    
    # Determine reload setting
    reload = not args.no_reload if args.no_reload else None
    
    # Run in appropriate mode
    if args.dashboard_only:
        run_dashboard_only(
            host=args.host,
            port=args.port,
            reload=reload
        )
    else:
        run_full_system(
            host=args.host,
            port=args.port,
            reload=reload
        )


if __name__ == "__main__":
    main()