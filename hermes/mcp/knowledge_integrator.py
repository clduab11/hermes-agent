"""
Knowledge Integration Module - Mem0 + mcp-omnisearch Integration
Copyright (c) 2025 Parallax Analytics LLC. All rights reserved.

Creates dynamic legal knowledge graph that learns from user interactions
using Mem0 knowledge graph and mcp-omnisearch capabilities.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from ..config import settings

logger = logging.getLogger(__name__)


class EntityType(Enum):
    """Types of entities in the legal knowledge graph."""

    CLIENT = "client"
    MATTER = "matter"
    ATTORNEY = "attorney"
    LEGAL_CONCEPT = "legal_concept"
    PRECEDENT = "precedent"
    STATUTE = "statute"
    REGULATION = "regulation"
    DOCUMENT = "document"
    PROCEDURE = "procedure"


class RelationType(Enum):
    """Types of relationships in the knowledge graph."""

    REPRESENTS = "represents"  # attorney represents client
    ASSIGNED_TO = "assigned_to"  # matter assigned to attorney
    RELATES_TO = "relates_to"  # matter relates to legal concept
    CITES = "cites"  # document cites precedent
    GOVERNED_BY = "governed_by"  # matter governed by statute
    SIMILAR_TO = "similar_to"  # precedent similar to precedent
    CONTAINS = "contains"  # document contains legal concept
    REQUIRES = "requires"  # procedure requires document


@dataclass
class KnowledgeEntity:
    """Represents an entity in the knowledge graph."""

    id: str
    name: str
    entity_type: EntityType
    attributes: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 1.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    interaction_count: int = 0


@dataclass
class KnowledgeRelationship:
    """Represents a relationship between entities."""

    id: str
    from_entity_id: str
    to_entity_id: str
    relationship_type: RelationType
    strength: float = 1.0
    evidence: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LearningInteraction:
    """Represents a user interaction for learning."""

    interaction_id: str
    tenant_id: str
    user_id: str
    conversation_id: str
    query: str
    response: str
    entities_mentioned: List[str]
    concepts_extracted: List[str]
    user_feedback: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


class KnowledgeIntegrator:
    """
    Handles knowledge integration with Mem0 and search capabilities.

    Features:
    - Dynamic legal knowledge graph creation and maintenance
    - Learning from user interactions and conversations
    - Multi-provider search integration for legal research
    - Automated entity extraction and relationship mapping
    - Contextual knowledge retrieval for voice responses
    """

    def __init__(self):
        self.entities: Dict[str, KnowledgeEntity] = {}
        self.relationships: Dict[str, KnowledgeRelationship] = {}
        self.learning_interactions: List[LearningInteraction] = []
        self.search_providers: List[str] = []
        self._learning_task: Optional[asyncio.Task] = None

        # Legal knowledge domains
        self.legal_domains = {
            "corporate": ["contracts", "mergers", "acquisitions", "compliance"],
            "litigation": ["civil", "criminal", "appeals", "discovery"],
            "family": ["divorce", "custody", "adoption", "domestic"],
            "real_estate": ["transactions", "zoning", "leases", "disputes"],
            "intellectual_property": [
                "patents",
                "trademarks",
                "copyrights",
                "trade_secrets",
            ],
            "employment": ["discrimination", "wages", "benefits", "termination"],
        }

    async def initialize(self):
        """Initialize knowledge integration system."""
        logger.info("Initializing Knowledge Integrator...")

        # Initialize search providers
        await self._initialize_search_providers()

        # Load existing knowledge graph
        await self._load_knowledge_graph()

        # Initialize legal concept entities
        await self._initialize_legal_concepts()

        # Start learning process
        self._learning_task = asyncio.create_task(self._continuous_learning_loop())

        logger.info("Knowledge Integrator initialized")

    async def cleanup(self):
        """Clean up knowledge integrator resources."""
        logger.info("Cleaning up Knowledge Integrator...")

        if self._learning_task:
            self._learning_task.cancel()
            try:
                await self._learning_task
            except asyncio.CancelledError:
                pass

        # Save knowledge graph state
        await self._save_knowledge_graph()

        logger.info("Knowledge Integrator cleanup completed")

    async def learn_from_interaction(self, interaction: LearningInteraction):
        """Learn from a user interaction to improve knowledge graph."""
        logger.debug(f"Learning from interaction: {interaction.interaction_id}")

        self.learning_interactions.append(interaction)

        # Extract entities and concepts from the interaction
        entities = await self._extract_entities(
            interaction.query + " " + interaction.response
        )
        concepts = await self._extract_legal_concepts(
            interaction.query + " " + interaction.response
        )

        # Update knowledge graph based on extraction
        for entity_name, entity_type in entities.items():
            await self._update_or_create_entity(
                entity_name, entity_type, interaction.tenant_id
            )

        # Create relationships based on context
        await self._infer_relationships(entities, interaction.conversation_id)

        # Update entity interaction counts
        for entity_id in interaction.entities_mentioned:
            if entity_id in self.entities:
                self.entities[entity_id].interaction_count += 1
                self.entities[entity_id].last_updated = datetime.utcnow()

    async def search_legal_knowledge(
        self, query: str, tenant_id: str, limit: int = 10
    ) -> Dict[str, Any]:
        """Search across multiple legal knowledge sources."""
        logger.debug(f"Searching legal knowledge for: {query}")

        search_results = {
            "query": query,
            "tenant_id": tenant_id,
            "results": [],
            "sources": [],
            "total_results": 0,
            "search_time_ms": 0,
        }

        start_time = datetime.utcnow()

        # Search internal knowledge graph
        internal_results = await self._search_internal_knowledge(
            query, tenant_id, limit
        )
        search_results["results"].extend(internal_results)
        search_results["sources"].append("internal_knowledge_graph")

        # Search external legal databases (via omnisearch)
        external_results = await self._search_external_legal_sources(query, limit)
        search_results["results"].extend(external_results)
        search_results["sources"].extend(["westlaw", "lexisnexis", "google_scholar"])

        # Deduplicate and rank results
        search_results["results"] = await self._rank_and_deduplicate_results(
            search_results["results"]
        )
        search_results["total_results"] = len(search_results["results"])

        end_time = datetime.utcnow()
        search_results["search_time_ms"] = (
            end_time - start_time
        ).total_seconds() * 1000

        logger.info(
            f"Legal knowledge search completed: {search_results['total_results']} results in {search_results['search_time_ms']}ms"
        )
        return search_results

    async def get_contextual_knowledge(
        self, conversation_id: str, tenant_id: str
    ) -> Dict[str, Any]:
        """Get contextual knowledge for a specific conversation."""
        context = {
            "conversation_id": conversation_id,
            "tenant_id": tenant_id,
            "relevant_entities": [],
            "related_concepts": [],
            "applicable_precedents": [],
            "suggested_resources": [],
        }

        # Find entities mentioned in this conversation
        conversation_entities = []
        for interaction in self.learning_interactions:
            if interaction.conversation_id == conversation_id:
                conversation_entities.extend(interaction.entities_mentioned)

        # Get relevant entities and their relationships
        for entity_id in set(conversation_entities):
            if entity_id in self.entities:
                entity = self.entities[entity_id]
                context["relevant_entities"].append(
                    {
                        "id": entity.id,
                        "name": entity.name,
                        "type": entity.entity_type.value,
                        "confidence": entity.confidence_score,
                        "interaction_count": entity.interaction_count,
                    }
                )

                # Find related entities through relationships
                related = await self._find_related_entities(entity_id, max_depth=2)
                for related_entity_id in related:
                    if related_entity_id not in conversation_entities:
                        related_entity = self.entities[related_entity_id]
                        if related_entity.entity_type == EntityType.LEGAL_CONCEPT:
                            context["related_concepts"].append(
                                {
                                    "name": related_entity.name,
                                    "confidence": related_entity.confidence_score,
                                }
                            )
                        elif related_entity.entity_type == EntityType.PRECEDENT:
                            context["applicable_precedents"].append(
                                {
                                    "name": related_entity.name,
                                    "citation": related_entity.attributes.get(
                                        "citation", ""
                                    ),
                                    "relevance": related_entity.confidence_score,
                                }
                            )

        return context

    async def generate_knowledge_insights(self, tenant_id: str) -> Dict[str, Any]:
        """Generate insights about knowledge usage and gaps."""
        insights = {
            "tenant_id": tenant_id,
            "total_entities": len(self.entities),
            "total_relationships": len(self.relationships),
            "most_accessed_concepts": [],
            "knowledge_gaps": [],
            "learning_effectiveness": 0.0,
            "recommendations": [],
        }

        # Find most accessed entities
        tenant_entities = [
            e
            for e in self.entities.values()
            if tenant_id in e.metadata.get("tenant_ids", [])
        ]

        sorted_entities = sorted(
            tenant_entities, key=lambda e: e.interaction_count, reverse=True
        )

        insights["most_accessed_concepts"] = [
            {
                "name": entity.name,
                "type": entity.entity_type.value,
                "access_count": entity.interaction_count,
                "confidence": entity.confidence_score,
            }
            for entity in sorted_entities[:10]
        ]

        # Identify knowledge gaps (low confidence or few interactions)
        low_confidence_entities = [
            e
            for e in tenant_entities
            if e.confidence_score < 0.5 or e.interaction_count < 2
        ]

        insights["knowledge_gaps"] = [
            {
                "name": entity.name,
                "type": entity.entity_type.value,
                "confidence": entity.confidence_score,
                "interactions": entity.interaction_count,
                "suggestion": "Consider additional training data or user validation",
            }
            for entity in low_confidence_entities[:5]
        ]

        # Calculate learning effectiveness
        if self.learning_interactions:
            recent_interactions = [
                i
                for i in self.learning_interactions
                if (datetime.utcnow() - i.timestamp).days <= 7
                and i.tenant_id == tenant_id
            ]

            positive_feedback = len(
                [
                    i
                    for i in recent_interactions
                    if i.user_feedback and "positive" in i.user_feedback.lower()
                ]
            )

            if recent_interactions:
                insights["learning_effectiveness"] = positive_feedback / len(
                    recent_interactions
                )

        # Generate recommendations
        if insights["learning_effectiveness"] < 0.7:
            insights["recommendations"].append(
                "Consider improving response quality through additional training"
            )

        if len(insights["knowledge_gaps"]) > 3:
            insights["recommendations"].append(
                "Focus on filling knowledge gaps in key legal areas"
            )

        return insights

    async def _initialize_search_providers(self):
        """Initialize external search providers."""
        self.search_providers = [
            "westlaw",
            "lexisnexis",
            "google_scholar",
            "justia",
            "findlaw",
        ]
        logger.info(f"Initialized {len(self.search_providers)} search providers")

    async def _load_knowledge_graph(self):
        """Load existing knowledge graph from Mem0."""
        # This would use Mem0 MCP server to load existing graph
        logger.info("Loading existing knowledge graph...")

        # Placeholder for loading existing entities and relationships
        # In real implementation, this would query Mem0 API

        logger.info(
            f"Loaded {len(self.entities)} entities and {len(self.relationships)} relationships"
        )

    async def _save_knowledge_graph(self):
        """Save knowledge graph to Mem0."""
        # This would use Mem0 MCP server to persist the graph
        logger.info("Saving knowledge graph...")

        # Placeholder for saving entities and relationships
        # In real implementation, this would use Mem0 API

        logger.info("Knowledge graph saved")

    async def _initialize_legal_concepts(self):
        """Initialize core legal concept entities."""
        logger.info("Initializing core legal concepts...")

        for domain, concepts in self.legal_domains.items():
            domain_entity = KnowledgeEntity(
                id=str(uuid4()),
                name=domain,
                entity_type=EntityType.LEGAL_CONCEPT,
                attributes={"domain": True, "concepts": concepts},
                confidence_score=1.0,
            )
            self.entities[domain_entity.id] = domain_entity

            for concept in concepts:
                concept_entity = KnowledgeEntity(
                    id=str(uuid4()),
                    name=concept,
                    entity_type=EntityType.LEGAL_CONCEPT,
                    attributes={"parent_domain": domain},
                    confidence_score=0.8,
                )
                self.entities[concept_entity.id] = concept_entity

                # Create relationship between domain and concept
                relationship = KnowledgeRelationship(
                    id=str(uuid4()),
                    from_entity_id=domain_entity.id,
                    to_entity_id=concept_entity.id,
                    relationship_type=RelationType.CONTAINS,
                    strength=1.0,
                )
                self.relationships[relationship.id] = relationship

        logger.info(f"Initialized {len(self.entities)} legal concept entities")

    async def _extract_entities(self, text: str) -> Dict[str, EntityType]:
        """Extract named entities from text."""
        # This would use NLP/AI to extract entities
        # Placeholder implementation
        entities = {}

        # Simple keyword-based extraction for demo
        if "contract" in text.lower():
            entities["contract"] = EntityType.LEGAL_CONCEPT
        if "client" in text.lower():
            entities["client"] = EntityType.CLIENT
        if "attorney" in text.lower():
            entities["attorney"] = EntityType.ATTORNEY

        return entities

    async def _extract_legal_concepts(self, text: str) -> List[str]:
        """Extract legal concepts from text."""
        concepts = []

        # Simple concept extraction for demo
        for domain, domain_concepts in self.legal_domains.items():
            if domain in text.lower():
                concepts.append(domain)
            for concept in domain_concepts:
                if concept in text.lower():
                    concepts.append(concept)

        return list(set(concepts))

    async def _update_or_create_entity(
        self, name: str, entity_type: EntityType, tenant_id: str
    ):
        """Update existing entity or create new one."""
        # Find existing entity by name and type
        existing_entity = None
        for entity in self.entities.values():
            if (
                entity.name.lower() == name.lower()
                and entity.entity_type == entity_type
            ):
                existing_entity = entity
                break

        if existing_entity:
            # Update existing entity
            existing_entity.interaction_count += 1
            existing_entity.last_updated = datetime.utcnow()
            if tenant_id not in existing_entity.metadata.get("tenant_ids", []):
                existing_entity.metadata.setdefault("tenant_ids", []).append(tenant_id)
        else:
            # Create new entity
            new_entity = KnowledgeEntity(
                id=str(uuid4()),
                name=name,
                entity_type=entity_type,
                metadata={"tenant_ids": [tenant_id]},
                confidence_score=0.7,  # Initial confidence for user-generated entities
            )
            self.entities[new_entity.id] = new_entity

    async def _infer_relationships(
        self, entities: Dict[str, EntityType], conversation_id: str
    ):
        """Infer relationships between entities based on context."""
        entity_ids = list(entities.keys())

        # Simple relationship inference for demo
        for i, entity1 in enumerate(entity_ids):
            for entity2 in entity_ids[i + 1 :]:
                # Infer relationship based on entity types
                entity1_obj = next(
                    (e for e in self.entities.values() if e.name == entity1), None
                )
                entity2_obj = next(
                    (e for e in self.entities.values() if e.name == entity2), None
                )

                if entity1_obj and entity2_obj:
                    relationship_type = self._determine_relationship_type(
                        entity1_obj.entity_type, entity2_obj.entity_type
                    )

                    if relationship_type:
                        relationship = KnowledgeRelationship(
                            id=str(uuid4()),
                            from_entity_id=entity1_obj.id,
                            to_entity_id=entity2_obj.id,
                            relationship_type=relationship_type,
                            strength=0.5,  # Inferred relationships have lower strength
                            evidence=[conversation_id],
                        )
                        self.relationships[relationship.id] = relationship

    def _determine_relationship_type(
        self, type1: EntityType, type2: EntityType
    ) -> Optional[RelationType]:
        """Determine relationship type between two entity types."""
        # Simple rule-based relationship determination
        if type1 == EntityType.ATTORNEY and type2 == EntityType.CLIENT:
            return RelationType.REPRESENTS
        elif type1 == EntityType.MATTER and type2 == EntityType.ATTORNEY:
            return RelationType.ASSIGNED_TO
        elif type1 == EntityType.MATTER and type2 == EntityType.LEGAL_CONCEPT:
            return RelationType.RELATES_TO
        elif type1 == EntityType.LEGAL_CONCEPT and type2 == EntityType.LEGAL_CONCEPT:
            return RelationType.SIMILAR_TO

        return None

    async def _find_related_entities(
        self, entity_id: str, max_depth: int = 2
    ) -> Set[str]:
        """Find entities related to the given entity within max_depth."""
        related = set()
        to_explore = {entity_id}
        explored = set()

        for depth in range(max_depth):
            if not to_explore:
                break

            current_level = to_explore.copy()
            to_explore.clear()

            for current_entity_id in current_level:
                if current_entity_id in explored:
                    continue

                explored.add(current_entity_id)

                # Find relationships where this entity is involved
                for relationship in self.relationships.values():
                    if relationship.from_entity_id == current_entity_id:
                        related.add(relationship.to_entity_id)
                        to_explore.add(relationship.to_entity_id)
                    elif relationship.to_entity_id == current_entity_id:
                        related.add(relationship.from_entity_id)
                        to_explore.add(relationship.from_entity_id)

        return related

    async def _search_internal_knowledge(
        self, query: str, tenant_id: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Search internal knowledge graph."""
        results = []

        query_lower = query.lower()

        # Search entities
        for entity in self.entities.values():
            if query_lower in entity.name.lower() and (
                tenant_id in entity.metadata.get("tenant_ids", [])
                or entity.entity_type == EntityType.LEGAL_CONCEPT
            ):
                results.append(
                    {
                        "title": entity.name,
                        "type": "entity",
                        "entity_type": entity.entity_type.value,
                        "confidence": entity.confidence_score,
                        "source": "internal_knowledge_graph",
                        "attributes": entity.attributes,
                    }
                )

        # Sort by confidence and limit results
        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results[:limit]

    async def _search_external_legal_sources(
        self, query: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Search external legal sources via omnisearch."""
        # This would use mcp-omnisearch to query multiple legal databases
        results = []

        # Placeholder results for demo
        mock_results = [
            {
                "title": f"Legal precedent for '{query}'",
                "type": "precedent",
                "source": "westlaw",
                "confidence": 0.85,
                "citation": "123 F.3d 456 (1st Cir. 2023)",
                "summary": f"Relevant case law related to {query}",
            },
            {
                "title": f"Statute regarding '{query}'",
                "type": "statute",
                "source": "lexisnexis",
                "confidence": 0.78,
                "citation": "42 U.S.C. § 1234",
                "summary": f"Federal statute covering {query}",
            },
        ]

        return mock_results[:limit]

    async def _rank_and_deduplicate_results(
        self, results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Rank and deduplicate search results."""
        # Simple deduplication by title
        seen_titles = set()
        deduplicated = []

        for result in results:
            title_lower = result["title"].lower()
            if title_lower not in seen_titles:
                seen_titles.add(title_lower)
                deduplicated.append(result)

        # Sort by confidence score
        deduplicated.sort(key=lambda x: x.get("confidence", 0), reverse=True)

        return deduplicated

    async def _continuous_learning_loop(self):
        """Continuous learning and knowledge graph optimization."""
        while True:
            try:
                # Analyze recent interactions for learning opportunities
                recent_interactions = [
                    i
                    for i in self.learning_interactions
                    if (datetime.utcnow() - i.timestamp).total_seconds() <= 86400
                ]  # 24 hours

                if recent_interactions:
                    logger.info(
                        f"Processing {len(recent_interactions)} recent interactions for learning"
                    )

                    # Update entity confidence scores based on usage
                    await self._update_entity_confidence_scores(recent_interactions)

                    # Strengthen relationships based on co-occurrence
                    await self._strengthen_relationships_from_interactions(
                        recent_interactions
                    )

                    # Save updated knowledge graph
                    await self._save_knowledge_graph()

                # Wait before next learning cycle
                await asyncio.sleep(3600)  # 1 hour

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Continuous learning loop error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def _update_entity_confidence_scores(
        self, interactions: List[LearningInteraction]
    ):
        """Update entity confidence scores based on interactions."""
        for interaction in interactions:
            for entity_id in interaction.entities_mentioned:
                if entity_id in self.entities:
                    entity = self.entities[entity_id]

                    # Increase confidence for frequently mentioned entities
                    confidence_boost = min(0.1, 1.0 / max(1, entity.interaction_count))
                    entity.confidence_score = min(
                        1.0, entity.confidence_score + confidence_boost
                    )

    async def _strengthen_relationships_from_interactions(
        self, interactions: List[LearningInteraction]
    ):
        """Strengthen relationships based on entity co-occurrence in interactions."""
        for interaction in interactions:
            entities = interaction.entities_mentioned

            # Find existing relationships between mentioned entities
            for i, entity1_id in enumerate(entities):
                for entity2_id in entities[i + 1 :]:
                    # Find relationship between these entities
                    for relationship in self.relationships.values():
                        if (
                            relationship.from_entity_id == entity1_id
                            and relationship.to_entity_id == entity2_id
                        ) or (
                            relationship.from_entity_id == entity2_id
                            and relationship.to_entity_id == entity1_id
                        ):
                            # Strengthen the relationship
                            relationship.strength = min(
                                1.0, relationship.strength + 0.1
                            )
                            relationship.last_updated = datetime.utcnow()

                            # Add interaction as evidence
                            if interaction.conversation_id not in relationship.evidence:
                                relationship.evidence.append(
                                    interaction.conversation_id
                                )


# Global knowledge integrator instance
knowledge_integrator = KnowledgeIntegrator()
