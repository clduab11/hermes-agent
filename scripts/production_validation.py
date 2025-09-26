#!/usr/bin/env python3
"""
HERMES Production Validation Suite Runner
Enterprise-grade validation for law firm clients ($2,497/month)

Usage:
    python scripts/production_validation.py [--verbose] [--output-format json|text] [--save-report]

This script runs comprehensive production validation tests to ensure HERMES
is ready for enterprise law firm clients with stringent SLA requirements.
"""

import asyncio
import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hermes.performance.production_validator import production_validator
from hermes.config import settings

class ProductionValidationRunner:
    """CLI runner for production validation suite."""

    def __init__(self, verbose: bool = False, output_format: str = "text"):
        self.verbose = verbose
        self.output_format = output_format

    async def run_validation(self, save_report: bool = False) -> Dict[str, Any]:
        """Run the complete production validation suite."""

        print("🚀 HERMES Production Validation Suite")
        print("=" * 50)
        print(f"🎯 Target: Law Firm Clients ($2,497/month)")
        print(f"🏛️ Validator: PRODUCTION-VALIDATOR")
        print(f"📊 Coordinator: PERF-ANALYZER")
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        print()

        # Run the validation suite
        try:
            validation_report = await production_validator.run_full_validation()

            # Display results
            if self.output_format == "json":
                self._display_json_results(validation_report)
            else:
                self._display_text_results(validation_report)

            # Save report if requested
            if save_report:
                self._save_report(validation_report)

            return validation_report

        except Exception as e:
            print(f"❌ Validation suite failed: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return {"status": "ERROR", "error": str(e)}

    def _display_text_results(self, report: Dict[str, Any]):
        """Display validation results in human-readable text format."""

        exec_summary = report.get("executive_summary", {})
        readiness = exec_summary.get("production_readiness", "UNKNOWN")
        overall_score = exec_summary.get("overall_score", 0)

        # Display executive summary
        print("📋 EXECUTIVE SUMMARY")
        print("-" * 30)

        status_emoji = {
            "READY": "✅",
            "READY_WITH_WARNINGS": "⚠️",
            "NOT_READY": "❌"
        }.get(readiness, "❓")

        print(f"{status_emoji} Production Readiness: {readiness}")
        print(f"📊 Overall Score: {overall_score}%")
        print(f"🧪 Total Tests: {exec_summary.get('total_tests', 0)}")
        print(f"✅ Passed: {exec_summary.get('passed_tests', 0)}")
        print(f"⚠️  Warnings: {exec_summary.get('warning_tests', 0)}")
        print(f"❌ Failed: {exec_summary.get('failed_tests', 0)}")
        print(f"⏱️  Execution Time: {exec_summary.get('total_execution_time_ms', 0):.1f}ms")
        print()

        print(exec_summary.get("readiness_message", ""))
        print()

        # Display detailed test results
        print("🔍 DETAILED TEST RESULTS")
        print("-" * 30)

        test_results = report.get("test_results", [])
        for result in test_results:
            status_emoji = {
                "PASS": "✅",
                "WARNING": "⚠️",
                "FAIL": "❌",
                "SKIP": "⏭️"
            }.get(result.get("status", "UNKNOWN"), "❓")

            print(f"{status_emoji} {result.get('test_name', 'Unknown Test')}")
            print(f"   Score: {result.get('score', 0):.1f}%")
            print(f"   Time: {result.get('execution_time_ms', 0):.1f}ms")

            if self.verbose:
                details = result.get("details", {})
                if details:
                    print("   Details:")
                    for key, value in details.items():
                        if isinstance(value, (dict, list)):
                            print(f"     {key}: {json.dumps(value, indent=2)}")
                        else:
                            print(f"     {key}: {value}")

            recommendations = result.get("recommendations", [])
            if recommendations:
                print("   Recommendations:")
                for rec in recommendations[:3]:  # Show top 3 recommendations
                    print(f"     • {rec}")
            print()

        # Display law firm readiness
        law_firm_readiness = report.get("law_firm_readiness", {})
        print("🏛️ LAW FIRM CLIENT READINESS")
        print("-" * 30)

        readiness_items = [
            ("Enterprise Performance", law_firm_readiness.get("enterprise_performance", False)),
            ("Multi-tenant Security", law_firm_readiness.get("multi_tenant_security", False)),
            ("Compliance Ready", law_firm_readiness.get("compliance_ready", False)),
            ("Scalability Validated", law_firm_readiness.get("scalability_validated", False)),
            ("Monitoring Configured", law_firm_readiness.get("monitoring_configured", False))
        ]

        for item, status in readiness_items:
            emoji = "✅" if status else "❌"
            print(f"{emoji} {item}")
        print()

        # Display critical recommendations
        critical_recs = report.get("critical_recommendations", [])
        if critical_recs:
            print("🚨 CRITICAL RECOMMENDATIONS")
            print("-" * 30)
            for rec in critical_recs:
                print(f"❗ {rec}")
            print()

        # Display next steps
        next_steps = report.get("next_steps", [])
        if next_steps:
            print("📋 NEXT STEPS")
            print("-" * 30)
            for step in next_steps:
                print(f"   {step}")
            print()

        # Final assessment
        print("🎯 FINAL ASSESSMENT FOR LAW FIRM CLIENTS")
        print("=" * 50)

        if readiness == "READY":
            print("✅ SYSTEM IS READY FOR PRODUCTION DEPLOYMENT")
            print("🏛️ Approved for law firm clients paying $2,497/month")
            print("🚀 Proceed with confidence to production deployment")
        elif readiness == "READY_WITH_WARNINGS":
            print("⚠️  SYSTEM MOSTLY READY - ATTENTION REQUIRED")
            print("🔧 Address warnings before serving premium law firm clients")
            print("📊 Consider enhanced monitoring for identified areas")
        else:
            print("❌ SYSTEM NOT READY FOR PRODUCTION")
            print("🛠️  Significant work required before law firm deployment")
            print("⏰ Do not proceed until critical issues are resolved")

        print()

    def _display_json_results(self, report: Dict[str, Any]):
        """Display validation results in JSON format."""
        print(json.dumps(report, indent=2, default=str))

    def _save_report(self, report: Dict[str, Any]):
        """Save validation report to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"hermes_production_validation_{timestamp}.json"

        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)

        report_path = reports_dir / filename

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"📄 Validation report saved to: {report_path}")
        print(f"📊 Report can be shared with compliance teams and management")

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="HERMES Production Validation Suite for Law Firm Clients",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run basic validation
    python scripts/production_validation.py

    # Run with verbose output
    python scripts/production_validation.py --verbose

    # Save JSON report for compliance documentation
    python scripts/production_validation.py --output-format json --save-report

    # Full validation with all options
    python scripts/production_validation.py --verbose --save-report
        """
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output with detailed test information"
    )

    parser.add_argument(
        "--output-format", "-f",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )

    parser.add_argument(
        "--save-report", "-s",
        action="store_true",
        help="Save validation report to JSON file for compliance documentation"
    )

    args = parser.parse_args()

    # Create and run validation
    runner = ProductionValidationRunner(
        verbose=args.verbose,
        output_format=args.output_format
    )

    try:
        # Run the async validation
        report = asyncio.run(runner.run_validation(save_report=args.save_report))

        # Exit with appropriate code
        exec_summary = report.get("executive_summary", {})
        readiness = exec_summary.get("production_readiness", "NOT_READY")

        if readiness == "READY":
            sys.exit(0)  # Success
        elif readiness == "READY_WITH_WARNINGS":
            sys.exit(1)  # Warnings - manual review needed
        else:
            sys.exit(2)  # Critical issues - must fix before production

    except KeyboardInterrupt:
        print("\n❌ Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()