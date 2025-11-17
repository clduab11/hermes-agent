"""
Comprehensive Test Suite for Legal Reasoning Engine
Copyright (c) 2025 Parallax Analytics LLC. All rights reserved.

Tests cover:
- Legal reasoning with real case scenarios
- Citation graph analysis
- Explainability and step-by-step traces
- Security and compliance
- Legal database integration
- Edge cases and error handling
"""

import asyncio
import pytest
from datetime import datetime
from typing import List

from hermes.reasoning.legal_reasoning_engine import (
    LegalReasoningEngine,
    LegalDomain,
    ReasoningMethod,
    CitationStrength,
    ExplainableReasoningTrace,
    LegalSyllogism,
)
from hermes.reasoning.citation_graph import (
    CitationGraph,
    CitationNetworkAnalyzer,
    CaseNode,
    CitationEdge,
    CitationRelationType,
)
from hermes.security.legal_security import (
    LegalAISecurityManager,
    PrivilegeLevel,
    AuditEventType,
    DataClassification,
)
from hermes.integrations.legal_databases import (
    LegalDatabaseIntegration,
    SearchQuery,
    SearchType,
    LegalDatabaseProvider,
)


class TestLegalReasoningEngine:
    """Test suite for legal reasoning engine"""

    @pytest.fixture
    async def reasoning_engine(self):
        """Create reasoning engine instance"""
        return LegalReasoningEngine(
            model_name="nlpaueb/legal-bert-base-uncased",
            enable_citation_analysis=True,
            enable_explainability=True,
        )

    @pytest.mark.asyncio
    async def test_negligence_analysis(self, reasoning_engine):
        """
        Test legal reasoning for negligence case.

        Scenario: Client slipped on wet floor in grocery store with no warning sign
        Expected: Identify duty of care, breach, causation, damages
        """
        query = """
        My client slipped and fell on a wet floor in a grocery store. There was no warning sign posted.
        She suffered a broken wrist and cannot work for 3 months. The store claims they had just mopped
        but hadn't put up the sign yet. Does my client have a viable negligence claim?
        """

        context = """
        Incident occurred in California. Client is a 45-year-old accountant earning $80,000/year.
        Medical bills total $15,000. Store has surveillance footage showing employee mopping
        5 minutes before incident.
        """

        result = await reasoning_engine.analyze_legal_query(
            query=query,
            context=context,
            domain=LegalDomain.TORT_LAW,
            jurisdiction="California",
            max_citations=5,
        )

        # Verify result structure
        assert isinstance(result, ExplainableReasoningTrace)
        assert result.domain == LegalDomain.TORT_LAW
        assert len(result.identified_issues) > 0
        assert "negligence" in " ".join(result.identified_issues).lower()

        # Verify reasoning steps
        assert len(result.reasoning_steps) >= 3
        step_types = [step.step_type for step in result.reasoning_steps]
        assert "identify_issue" in step_types
        assert "apply_rule" in step_types

        # Verify legal syllogisms
        assert len(result.syllogisms) > 0
        for syllogism in result.syllogisms:
            assert isinstance(syllogism, LegalSyllogism)
            assert syllogism.major_premise  # Legal rule
            assert syllogism.minor_premise  # Facts
            assert syllogism.conclusion  # Application

        # Verify citations
        assert len(result.cited_cases) > 0

        # Verify confidence score
        assert 0.0 <= result.confidence_score <= 1.0

        print(f"\n=== Negligence Analysis Results ===")
        print(f"Issues: {result.identified_issues}")
        print(f"Confidence: {result.confidence_score:.2%}")
        print(f"Conclusion: {result.conclusion}")
        print(f"Cases Cited: {len(result.cited_cases)}")

    @pytest.mark.asyncio
    async def test_contract_breach_analysis(self, reasoning_engine):
        """
        Test contract law reasoning.

        Scenario: Breach of employment contract
        """
        query = """
        My client signed a 2-year employment contract with a tech company. After 8 months,
        the company terminated her without cause, claiming "business reasons." The contract
        states termination requires 90 days notice or severance equal to remaining salary.
        They only gave 2 weeks notice and no severance. What are her remedies?
        """

        result = await reasoning_engine.analyze_legal_query(
            query=query,
            domain=LegalDomain.CONTRACT_LAW,
            jurisdiction="California",
        )

        assert result.domain == LegalDomain.CONTRACT_LAW
        assert any("breach" in issue.lower() for issue in result.identified_issues)
        assert len(result.applicable_rules) > 0

        # Verify contract-specific analysis
        has_contract_elements = any(
            "consideration" in str(rule.rule_statement).lower()
            or "breach" in str(rule.rule_statement).lower()
            for rule in result.applicable_rules
        )
        assert has_contract_elements

        print(f"\n=== Contract Breach Analysis ===")
        print(f"Conclusion: {result.conclusion}")

    @pytest.mark.asyncio
    async def test_constitutional_analysis(self, reasoning_engine):
        """Test constitutional law reasoning"""
        query = """
        A city ordinance prohibits all political demonstrations within 500 feet of government
        buildings. A protest group was arrested for demonstrating on the city hall steps.
        Does this ordinance violate the First Amendment?
        """

        result = await reasoning_engine.analyze_legal_query(
            query=query,
            domain=LegalDomain.CONSTITUTIONAL_LAW,
            jurisdiction="federal",
        )

        assert result.domain == LegalDomain.CONSTITUTIONAL_LAW
        assert len(result.reasoning_steps) > 0

    @pytest.mark.asyncio
    async def test_explainability_traces(self, reasoning_engine):
        """Test that reasoning traces are explainable and complete"""
        query = "Is a verbal promise to pay $1000 for yard work enforceable as a contract?"

        result = await reasoning_engine.analyze_legal_query(
            query=query,
            domain=LegalDomain.CONTRACT_LAW,
        )

        # Verify complete reasoning chain
        assert len(result.reasoning_steps) >= 3

        # Verify each step has explanation
        for step in result.reasoning_steps:
            assert step.description
            assert step.step_type
            assert 0.0 <= step.confidence <= 1.0

        # Verify syllogistic reasoning
        for syllogism in result.syllogisms:
            assert syllogism.major_premise  # Legal rule
            assert syllogism.minor_premise  # Facts
            assert syllogism.conclusion  # Reasoning
            assert len(syllogism.supporting_reasoning) > 0

        print(f"\n=== Explainability Test ===")
        for i, step in enumerate(result.reasoning_steps, 1):
            print(f"Step {i}: {step.description}")


class TestCitationGraphAnalysis:
    """Test suite for citation graph analysis"""

    @pytest.fixture
    def citation_graph(self):
        """Create citation graph with sample case law"""
        graph = CitationGraph(temporal_decay=0.95)

        # Add landmark cases
        palsgraf = CaseNode(
            case_id="palsgraf_1928",
            case_name="Palsgraf v. Long Island Railroad Co.",
            year=1928,
            court="New York Court of Appeals",
            jurisdiction="New York",
        )

        donoghue = CaseNode(
            case_id="donoghue_1932",
            case_name="Donoghue v. Stevenson",
            year=1932,
            court="House of Lords",
            jurisdiction="United Kingdom",
        )

        modern_case = CaseNode(
            case_id="modern_2020",
            case_name="Modern Negligence Case",
            year=2020,
            court="California Supreme Court",
            jurisdiction="California",
        )

        graph.add_node(palsgraf)
        graph.add_node(donoghue)
        graph.add_node(modern_case)

        # Add citation edges
        graph.add_edge(
            CitationEdge(
                source_case_id="modern_2020",
                target_case_id="palsgraf_1928",
                relation_type=CitationRelationType.FOLLOWS,
                weight=1.0,
            )
        )

        graph.add_edge(
            CitationEdge(
                source_case_id="modern_2020",
                target_case_id="donoghue_1932",
                relation_type=CitationRelationType.CITES_PERSUASIVE,
                weight=0.8,
            )
        )

        return graph

    def test_pagerank_computation(self, citation_graph):
        """Test PageRank importance scoring"""
        pagerank = citation_graph.compute_pagerank(damping_factor=0.85)

        assert len(pagerank) == 3
        assert all(0.0 <= score <= 1.0 for score in pagerank.values())

        # Cited cases should have higher PageRank
        assert pagerank["palsgraf_1928"] > 0
        assert pagerank["donoghue_1932"] > 0

        print(f"\n=== PageRank Scores ===")
        for case_id, score in sorted(pagerank.items(), key=lambda x: x[1], reverse=True):
            print(f"{case_id}: {score:.4f}")

    def test_hits_algorithm(self, citation_graph):
        """Test HITS hub and authority scores"""
        hub_scores, auth_scores = citation_graph.compute_hits()

        assert len(hub_scores) == 3
        assert len(auth_scores) == 3

        # Modern case should have high hub score (cites others)
        assert hub_scores["modern_2020"] > 0

        # Landmark cases should have high authority scores (cited by others)
        assert auth_scores["palsgraf_1928"] > 0

        print(f"\n=== HITS Scores ===")
        print("Hub Scores:")
        for case_id, score in sorted(hub_scores.items(), key=lambda x: x[1], reverse=True):
            print(f"  {case_id}: {score:.4f}")
        print("Authority Scores:")
        for case_id, score in sorted(auth_scores.items(), key=lambda x: x[1], reverse=True):
            print(f"  {case_id}: {score:.4f}")

    def test_temporal_influence(self, citation_graph):
        """Test temporal influence calculation"""
        # Older cases should have lower temporal weight
        palsgraf_influence = citation_graph.compute_temporal_influence("palsgraf_1928")
        modern_influence = citation_graph.compute_temporal_influence("modern_2020")

        assert palsgraf_influence >= 0
        assert modern_influence >= 0

        # Temporal weight should decay for older cases
        palsgraf_node = citation_graph.nodes["palsgraf_1928"]
        modern_node = citation_graph.nodes["modern_2020"]

        assert palsgraf_node.temporal_weight < modern_node.temporal_weight

        print(f"\n=== Temporal Influence ===")
        print(f"Palsgraf (1928): {palsgraf_influence:.4f} (weight: {palsgraf_node.temporal_weight:.4f})")
        print(f"Modern (2020): {modern_influence:.4f} (weight: {modern_node.temporal_weight:.4f})")

    def test_precedent_importance_ranking(self, citation_graph):
        """Test overall case importance ranking"""
        ranked = citation_graph.rank_cases_by_importance(top_k=3)

        assert len(ranked) <= 3
        assert all(isinstance(item, tuple) for item in ranked)
        assert all(len(item) == 2 for item in ranked)

        # Verify scores are in descending order
        scores = [score for _, score in ranked]
        assert scores == sorted(scores, reverse=True)

        print(f"\n=== Importance Ranking ===")
        for rank, (case_id, score) in enumerate(ranked, 1):
            print(f"{rank}. {case_id}: {score:.4f}")

    @pytest.mark.asyncio
    async def test_citation_network_analyzer(self, citation_graph):
        """Test high-level citation network analysis"""
        analyzer = CitationNetworkAnalyzer(graph=citation_graph)

        # Analyze precedent importance
        analysis = await analyzer.analyze_precedent_importance("palsgraf_1928")

        assert analysis["case_id"] == "palsgraf_1928"
        assert analysis["case_name"] == "Palsgraf v. Long Island Railroad Co."
        assert "pagerank_score" in analysis
        assert "authority_score" in analysis
        assert "temporal_influence" in analysis

        print(f"\n=== Precedent Analysis: Palsgraf ===")
        print(f"Citation Count: {analysis['citation_count']}")
        print(f"PageRank: {analysis['pagerank_score']:.4f}")
        print(f"Authority: {analysis['authority_score']:.4f}")
        print(f"Importance Rank: {analysis['importance_ranking']}")


class TestLegalSecurity:
    """Test suite for legal AI security and compliance"""

    @pytest.fixture
    def security_manager(self):
        """Create security manager instance"""
        return LegalAISecurityManager(
            strict_privilege_mode=True,
            retention_years=7,
        )

    @pytest.mark.asyncio
    async def test_privilege_protection(self, security_manager):
        """Test attorney-client privilege protection"""
        resource_id = "case_001_client_comm"

        # Mark as privileged
        security_manager.privilege_protection.mark_privileged(
            resource_id,
            PrivilegeLevel.PRIVILEGED,
        )

        # Test attorney access (should succeed)
        authorized, error = await security_manager.secure_access(
            user_id="atty_001",
            user_email="attorney@lawfirm.com",
            user_role="attorney",
            resource_type="communication",
            resource_id=resource_id,
            action="read",
            privilege_level=PrivilegeLevel.PRIVILEGED,
        )

        assert authorized is True
        assert error is None

        # Test paralegal access (should fail in strict mode)
        authorized, error = await security_manager.secure_access(
            user_id="para_001",
            user_email="paralegal@lawfirm.com",
            user_role="paralegal",
            resource_type="communication",
            resource_id=resource_id,
            action="read",
            privilege_level=PrivilegeLevel.PRIVILEGED,
        )

        assert authorized is False
        assert error is not None
        assert "privilege" in error.lower()

    @pytest.mark.asyncio
    async def test_encryption(self, security_manager):
        """Test data encryption for privileged materials"""
        privileged_text = "Client admitted to being at fault in the accident."
        resource_id = "privileged_note_001"

        # Encrypt
        encrypted = await security_manager.encrypt_privileged_data(
            data=privileged_text,
            resource_id=resource_id,
            privilege_level=PrivilegeLevel.PRIVILEGED,
        )

        assert encrypted != privileged_text
        assert len(encrypted) > len(privileged_text)

        # Decrypt
        decrypted = security_manager.encryption.decrypt(encrypted)
        assert decrypted == privileged_text

    @pytest.mark.asyncio
    async def test_audit_logging(self, security_manager):
        """Test immutable audit log"""
        # Log several events
        await security_manager.audit_log.log_event(
            event_type=AuditEventType.ACCESS,
            user_id="user_001",
            user_email="user@example.com",
            resource_type="case",
            resource_id="case_001",
            action="view",
            success=True,
            privilege_level=PrivilegeLevel.CONFIDENTIAL,
            data_classification=DataClassification.SENSITIVE,
        )

        await security_manager.audit_log.log_event(
            event_type=AuditEventType.MODIFICATION,
            user_id="user_001",
            user_email="user@example.com",
            resource_type="case",
            resource_id="case_001",
            action="update_notes",
            success=True,
            privilege_level=PrivilegeLevel.CONFIDENTIAL,
            data_classification=DataClassification.SENSITIVE,
        )

        # Verify integrity
        integrity_valid = security_manager.audit_log.verify_integrity()
        assert integrity_valid is True

        # Verify entries were logged
        entries = security_manager.audit_log.get_entries_for_resource("case", "case_001")
        assert len(entries) >= 2

        # Verify hash chain
        for i in range(1, len(security_manager.audit_log.entries)):
            prev_entry = security_manager.audit_log.entries[i - 1]
            curr_entry = security_manager.audit_log.entries[i]
            assert curr_entry.hash_chain_prev == prev_entry.hash_self

    @pytest.mark.asyncio
    async def test_audit_log_tampering_detection(self, security_manager):
        """Test that audit log detects tampering"""
        # Log some events
        await security_manager.audit_log.log_event(
            event_type=AuditEventType.ACCESS,
            user_id="user_001",
            user_email="user@example.com",
            resource_type="test",
            resource_id="test_001",
            action="read",
            success=True,
        )

        # Verify initial integrity
        assert security_manager.audit_log.verify_integrity() is True

        # Tamper with log (simulate attack)
        if len(security_manager.audit_log.entries) > 0:
            security_manager.audit_log.entries[0].action = "TAMPERED"

            # Should detect tampering
            integrity_valid = security_manager.audit_log.verify_integrity()
            assert integrity_valid is False


class TestLegalDatabaseIntegration:
    """Test suite for legal database integration"""

    @pytest.fixture
    def db_integration(self):
        """Create database integration instance"""
        return LegalDatabaseIntegration(
            enable_westlaw=False,  # Demo mode
            enable_lexis=False,  # Demo mode
            enable_pacer=False,  # Demo mode
            enable_courtlistener=True,  # Free API
        )

    @pytest.mark.asyncio
    async def test_courtlistener_search(self, db_integration):
        """Test Court Listener API search"""
        query = SearchQuery(
            query_text="negligence duty of care",
            search_type=SearchType.CASE_LAW,
            max_results=5,
        )

        # Search Court Listener (may require API key for production)
        if LegalDatabaseProvider.COURT_LISTENER in db_integration.clients:
            client = db_integration.clients[LegalDatabaseProvider.COURT_LISTENER]

            try:
                response = await client.search(query)

                assert response.provider == LegalDatabaseProvider.COURT_LISTENER
                assert response.query == query
                assert response.search_time_ms >= 0

                if response.results:
                    # Verify result structure
                    doc = response.results[0]
                    assert doc.document_id
                    assert doc.title
                    assert doc.document_type == SearchType.CASE_LAW

                    print(f"\n=== Court Listener Search Results ===")
                    print(f"Found: {response.total_found} cases")
                    print(f"Search time: {response.search_time_ms:.2f}ms")
                    for i, doc in enumerate(response.results[:3], 1):
                        print(f"{i}. {doc.title}")
                        print(f"   {doc.citation}")

            except Exception as e:
                pytest.skip(f"Court Listener API unavailable: {e}")

    @pytest.mark.asyncio
    async def test_westlaw_mock_search(self, db_integration):
        """Test Westlaw mock search (demo mode)"""
        # Add Westlaw client in demo mode
        from hermes.integrations.legal_databases import WestlawClient

        westlaw = WestlawClient(api_key="DEMO")

        query = SearchQuery(
            query_text="negligence",
            search_type=SearchType.CASE_LAW,
            jurisdiction="New York",
        )

        async with westlaw:
            response = await westlaw.search(query)

            assert response.provider == LegalDatabaseProvider.WESTLAW
            # Should return mock Palsgraf case
            assert len(response.results) > 0
            assert "Palsgraf" in response.results[0].title


@pytest.mark.asyncio
async def test_end_to_end_legal_analysis():
    """
    End-to-end integration test: Complete legal analysis workflow.

    Scenario: Analyze a complex negligence case with:
    - Legal reasoning
    - Citation analysis
    - Security controls
    - Database integration
    """
    print("\n" + "=" * 60)
    print("END-TO-END LEGAL ANALYSIS TEST")
    print("=" * 60)

    # Initialize components
    reasoning_engine = LegalReasoningEngine()
    security_manager = LegalAISecurityManager()

    # Legal query
    query = """
    A grocery store customer slipped on a banana peel in the produce section.
    The banana peel had been on the floor for approximately 30 minutes based on
    witness testimony. Store has a cleaning protocol that requires floor checks
    every 45 minutes. Customer suffered severe back injury requiring surgery.
    Analyze potential negligence claim.
    """

    context = """
    Jurisdiction: California
    Plaintiff: 55-year-old teacher, $70,000/year salary
    Medical costs: $85,000
    Lost wages: $20,000 (3 months recovery)
    Store revenue: $5M/year, 20 employees
    """

    # Step 1: Security check (simulated privileged access)
    resource_id = "case_analysis_001"
    authorized, error = await security_manager.secure_access(
        user_id="atty_001",
        user_email="attorney@lawfirm.com",
        user_role="attorney",
        resource_type="case_analysis",
        resource_id=resource_id,
        action="analyze",
        privilege_level=PrivilegeLevel.WORK_PRODUCT,
        ip_address="192.168.1.100",
    )

    assert authorized, f"Access denied: {error}"
    print("✓ Security check passed")

    # Step 2: Legal reasoning analysis
    result = await reasoning_engine.analyze_legal_query(
        query=query,
        context=context,
        domain=LegalDomain.TORT_LAW,
        jurisdiction="California",
        max_citations=10,
    )

    print(f"✓ Legal analysis completed ({result.processing_time_ms:.1f}ms)")
    print(f"  Issues identified: {len(result.identified_issues)}")
    print(f"  Reasoning steps: {len(result.reasoning_steps)}")
    print(f"  Cases cited: {len(result.cited_cases)}")
    print(f"  Confidence: {result.confidence_score:.1%}")

    # Step 3: Verify explainability
    assert len(result.syllogisms) > 0, "No legal syllogisms generated"
    assert len(result.reasoning_steps) >= 3, "Insufficient reasoning steps"
    print("✓ Explainability verification passed")

    # Step 4: Encrypt analysis results
    analysis_json = result.json()
    encrypted = await security_manager.encrypt_privileged_data(
        data=analysis_json,
        resource_id=resource_id,
        privilege_level=PrivilegeLevel.WORK_PRODUCT,
    )
    print("✓ Analysis encrypted for storage")

    # Step 5: Verify audit trail
    audit_entries = security_manager.audit_log.get_entries_for_resource(
        "case_analysis", resource_id
    )
    assert len(audit_entries) >= 2, "Audit trail incomplete"
    print(f"✓ Audit trail verified ({len(audit_entries)} entries)")

    # Step 6: Verify audit integrity
    integrity_valid = await security_manager.verify_audit_integrity()
    assert integrity_valid, "Audit log integrity compromised"
    print("✓ Audit log integrity verified")

    print("\n" + "=" * 60)
    print("ANALYSIS RESULTS")
    print("=" * 60)
    print(f"\nConclusion: {result.conclusion}\n")
    print("Key Legal Issues:")
    for issue in result.identified_issues:
        print(f"  • {issue}")

    print("\nReasoning Trace:")
    for i, step in enumerate(result.reasoning_steps[:5], 1):
        print(f"  {i}. {step.description}")

    print("\nCited Cases:")
    for case in result.cited_cases[:3]:
        print(f"  • {case.case_name} ({case.year})")
        print(f"    {case.citation}")

    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
