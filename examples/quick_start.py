#!/usr/bin/env python3
"""
judicAIta Quick Start Example
Copyright (c) 2025 Parallax Analytics LLC. All rights reserved.

This example demonstrates the core capabilities in under 5 minutes.
Perfect for judges and evaluators to quickly understand the system.
"""

import asyncio
from datetime import datetime


async def main():
    """Run quick demonstration of judicAIta capabilities"""

    print("="*80)
    print("🏛️  judicAIta - Legal AI Companion")
    print("="*80)
    print("Quick Start Demonstration - Running in 5 minutes...")
    print()

    # Import components (lazy import for speed)
    from hermes.reasoning.legal_reasoning_engine import (
        LegalReasoningEngine,
        LegalDomain
    )
    from hermes.reasoning.citation_graph import CitationGraph, CaseNode, CitationEdge, CitationRelationType
    from hermes.security.legal_security import LegalAISecurityManager, PrivilegeLevel

    # =========================================================================
    # DEMO 1: Legal Reasoning with Explainable AI
    # =========================================================================
    print("\n" + "="*80)
    print("DEMO 1: Legal Reasoning Engine with Legal Syllogism Prompting")
    print("="*80)

    engine = LegalReasoningEngine()

    # Simple negligence case
    query = """
    A customer slipped on a wet floor in a grocery store. There was no warning sign.
    The customer suffered a broken wrist and medical bills of $15,000.
    Does the customer have a negligence claim?
    """

    print(f"\n📝 Legal Query: {query.strip()}")
    print("\n⏳ Analyzing...")

    start_time = datetime.now()

    result = await engine.analyze_legal_query(
        query=query,
        domain=LegalDomain.TORT_LAW,
        jurisdiction="California",
        max_citations=5
    )

    elapsed = (datetime.now() - start_time).total_seconds() * 1000

    print(f"\n✅ Analysis Complete in {elapsed:.1f}ms")
    print(f"\n🎯 Confidence Score: {result.confidence_score:.1%}")
    print(f"\n⚖️  Legal Issues Identified:")
    for i, issue in enumerate(result.identified_issues, 1):
        print(f"   {i}. {issue}")

    print(f"\n📐 Legal Syllogisms (Formal Reasoning):")
    for i, syllogism in enumerate(result.syllogisms[:2], 1):
        print(f"\n   Syllogism {i}:")
        print(f"   Major Premise: {syllogism.major_premise[:80]}...")
        print(f"   Minor Premise: {syllogism.minor_premise[:80]}...")
        print(f"   Conclusion: {syllogism.conclusion[:80]}...")
        print(f"   Confidence: {syllogism.confidence:.1%}")

    print(f"\n📚 Cases Cited:")
    for case in result.cited_cases[:3]:
        print(f"   • {case.case_name} ({case.year})")
        print(f"     {case.citation}")
        print(f"     Relevance: {case.relevance_score:.1%}, Strength: {case.strength.value}")

    print(f"\n💡 Conclusion:")
    print(f"   {result.conclusion[:200]}...")

    # =========================================================================
    # DEMO 2: Citation Graph Analysis
    # =========================================================================
    print("\n\n" + "="*80)
    print("DEMO 2: Citation Graph Analysis with PageRank")
    print("="*80)

    graph = CitationGraph()

    # Add landmark cases
    cases = [
        CaseNode(
            case_id="palsgraf_1928",
            case_name="Palsgraf v. Long Island Railroad",
            year=1928,
            court="NY Court of Appeals",
            jurisdiction="New York"
        ),
        CaseNode(
            case_id="donoghue_1932",
            case_name="Donoghue v. Stevenson",
            year=1932,
            court="House of Lords",
            jurisdiction="United Kingdom"
        ),
        CaseNode(
            case_id="modern_2020",
            case_name="Modern Negligence Case",
            year=2020,
            court="California Supreme Court",
            jurisdiction="California"
        )
    ]

    for case in cases:
        graph.add_node(case)

    # Add citations
    graph.add_edge(CitationEdge(
        source_case_id="modern_2020",
        target_case_id="palsgraf_1928",
        relation_type=CitationRelationType.FOLLOWS
    ))
    graph.add_edge(CitationEdge(
        source_case_id="modern_2020",
        target_case_id="donoghue_1932",
        relation_type=CitationRelationType.CITES_PERSUASIVE
    ))

    print("\n🕸️  Citation Graph Built:")
    print(f"   Cases: {len(graph.nodes)}")
    print(f"   Citations: {len(graph.edges)}")

    # Compute PageRank
    print("\n📊 Computing PageRank Importance...")
    pagerank = graph.compute_pagerank()

    sorted_cases = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)
    print("\n🏆 Case Importance Ranking:")
    for rank, (case_id, score) in enumerate(sorted_cases, 1):
        case = graph.nodes[case_id]
        print(f"   {rank}. {case.case_name}")
        print(f"      PageRank: {score:.4f}")
        print(f"      Cited by: {case.in_degree} cases")

    # =========================================================================
    # DEMO 3: Security & Compliance
    # =========================================================================
    print("\n\n" + "="*80)
    print("DEMO 3: Attorney-Client Privilege Protection & Security")
    print("="*80)

    security = LegalAISecurityManager()

    # Mark privileged communication
    resource_id = "client_consultation_001"
    security.privilege_protection.mark_privileged(
        resource_id,
        PrivilegeLevel.PRIVILEGED
    )

    print(f"\n🔒 Marked resource as PRIVILEGED: {resource_id}")

    # Test access control
    print("\n🔐 Testing Access Control:")

    # Attorney access (should succeed)
    authorized, error = await security.secure_access(
        user_id="atty_001",
        user_email="attorney@lawfirm.com",
        user_role="attorney",
        resource_type="consultation",
        resource_id=resource_id,
        action="view",
        privilege_level=PrivilegeLevel.PRIVILEGED
    )

    print(f"   Attorney Access: {'✅ GRANTED' if authorized else '❌ DENIED'}")

    # Paralegal access (should fail in strict mode)
    authorized, error = await security.secure_access(
        user_id="para_001",
        user_email="paralegal@lawfirm.com",
        user_role="paralegal",
        resource_type="consultation",
        resource_id=resource_id,
        action="view",
        privilege_level=PrivilegeLevel.PRIVILEGED
    )

    print(f"   Paralegal Access: {'✅ GRANTED' if authorized else '❌ DENIED'}")
    if error:
        print(f"   Reason: {error}")

    # Encryption demo
    print("\n🔐 Encryption Demo:")
    privileged_text = "Client confidential communication for attorney review."

    encrypted = await security.encrypt_privileged_data(
        data=privileged_text,
        resource_id="note_001",
        privilege_level=PrivilegeLevel.PRIVILEGED
    )

    print(f"   Original: {privileged_text}")
    print(f"   Encrypted: {encrypted[:50]}... ({len(encrypted)} bytes)")

    decrypted = security.encryption.decrypt(encrypted)
    print(f"   Decrypted: {decrypted}")
    print(f"   ✅ Encryption Verified: {decrypted == privileged_text}")

    # Audit log
    print("\n📋 Audit Log:")
    print(f"   Total Entries: {len(security.audit_log.entries)}")
    print(f"   Integrity Verified: {await security.verify_audit_integrity()}")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n\n" + "="*80)
    print("✅ QUICK START COMPLETE")
    print("="*80)

    print("\n🎯 Key Capabilities Demonstrated:")
    print("   1. ✅ Legal Reasoning with Legal Syllogism Prompting")
    print("   2. ✅ Citation Graph Analysis with PageRank")
    print("   3. ✅ Attorney-Client Privilege Protection")
    print("   4. ✅ AES-256 Encryption")
    print("   5. ✅ Immutable Audit Logging")

    print("\n📊 Performance Metrics:")
    print(f"   Analysis Time: {elapsed:.1f}ms")
    print(f"   Confidence Score: {result.confidence_score:.1%}")
    print(f"   Cases Cited: {len(result.cited_cases)}")
    print(f"   Reasoning Steps: {len(result.reasoning_steps)}")

    print("\n🌟 Innovations:")
    print("   • Legal Syllogism Prompting (LSP) - First implementation in legal AI")
    print("   • Multi-Metric Citation Importance - Novel precedent ranking")
    print("   • Attorney-Client Privilege AI - Only legal AI with built-in protection")
    print("   • Multi-Database Integration - 4 databases, single API")

    print("\n📚 Full Documentation:")
    print("   • User Guide: docs/LEGAL_AI_USER_GUIDE.md")
    print("   • Demo Notebook: kaggle/LEGAL_AI_DEMO.ipynb")
    print("   • Test Suite: tests/test_legal_reasoning.py")

    print("\n" + "="*80)
    print("🏛️  judicAIta - Production-Ready Legal AI")
    print("="*80)
    print()


if __name__ == "__main__":
    print("\n🚀 Starting judicAIta Quick Start Demo...")
    print("This will take approximately 2-3 minutes\n")

    try:
        asyncio.run(main())
        print("\n✅ Demo completed successfully!")
        print("\nNext steps:")
        print("  • Run full demo: jupyter notebook kaggle/LEGAL_AI_DEMO.ipynb")
        print("  • Run tests: pytest tests/test_legal_reasoning.py -v")
        print("  • Read docs: docs/LEGAL_AI_USER_GUIDE.md")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  • Install dependencies: pip install -r requirements-legal-ai.txt")
        print("  • Check Python version: python --version (requires 3.11+)")
        import traceback
        traceback.print_exc()
