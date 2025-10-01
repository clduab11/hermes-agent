"""
HERMES Knowledge Graph Synchronization
Intelligent knowledge graph integration with cross-system synchronization
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class KnowledgeNodeType(Enum):
    CLIENT = "client"
    MATTER = "matter"
    DOCUMENT = "document"
    LEGAL_ENTITY = "legal_entity"
    CASE_LAW = "case_law"
    ATTORNEY = "attorney"


class RelationshipType(Enum):
    REPRESENTS = "represents"
    WORKS_ON = "works_on"
    REFERENCES = "references"
    RELATES_TO = "relates_to"
    OWNS = "owns"


@dataclass
class KnowledgeNode:
    node_id: str
    node_type: KnowledgeNodeType
    title: str
    properties: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    confidence_score: float
    source_systems: Set[str]


@dataclass
class KnowledgeRelationship:
    relationship_id: str
    source_node_id: str
    target_node_id: str
    relationship_type: RelationshipType
    properties: Dict[str, Any]
    confidence_score: float
    created_at: datetime
    source_systems: Set[str]


class KnowledgeGraphSynchronizer:
    """Knowledge graph synchronization engine"""

    def __init__(self, mem0_client=None, clio_client=None, analytics_engine=None):
        self.mem0 = mem0_client
        self.clio = clio_client
        self.analytics = analytics_engine
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.relationships: Dict[str, KnowledgeRelationship] = {}
        self.last_sync_timestamps: Dict[str, datetime] = {}
        self._mem0_enabled = mem0_client is not None

    async def initialize_knowledge_graph(self) -> Dict[str, Any]:
        """Initialize knowledge graph with seed data"""
        logger.info("Initializing HERMES knowledge graph...")

        core_concepts = [
            {
                "node_type": KnowledgeNodeType.LEGAL_ENTITY,
                "title": "Contract Law",
                "properties": {
                    "description": "Legal framework governing contractual agreements"
                },
            },
            {
                "node_type": KnowledgeNodeType.LEGAL_ENTITY,
                "title": "Personal Injury",
                "properties": {
                    "description": "Legal area covering physical and emotional harm claims"
                },
            },
        ]

        created_nodes = []
        for concept in core_concepts:
            node = await self.create_knowledge_node(
                node_type=concept["node_type"],
                title=concept["title"],
                properties=concept["properties"],
                source_system="hermes_core",
            )
            created_nodes.append(node.node_id)

        return {
            "status": "initialized",
            "core_nodes_created": len(created_nodes),
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def create_knowledge_node(
        self,
        node_type: KnowledgeNodeType,
        title: str,
        properties: Dict[str, Any],
        source_system: str,
        confidence_score: float = 1.0,
    ) -> KnowledgeNode:
        """Create new knowledge node"""

        node_id = f"{node_type.value}_{int(time.time())}_{hash(title) % 10000}"

        node = KnowledgeNode(
            node_id=node_id,
            node_type=node_type,
            title=title,
            properties=properties,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            confidence_score=confidence_score,
            source_systems={source_system},
        )

        self.nodes[node_id] = node
        logger.debug(f"Created knowledge node: {node_id} ({title})")
        return node

    async def run_full_synchronization(self) -> Dict[str, Any]:
        """Run full synchronization across all systems"""
        logger.info("Starting full knowledge graph synchronization...")

        sync_results = {
            "started_at": datetime.utcnow().isoformat(),
            "systems_synced": {},
            "total_nodes_before": len(self.nodes),
            "errors": [],
        }

        try:
            # Sync with Mem0 if available
            if self._mem0_enabled and self.mem0:
                try:
                    mem0_nodes = await self._sync_from_mem0()
                    sync_results["systems_synced"]["mem0"] = {
                        "status": "completed",
                        "nodes_synced": len(mem0_nodes),
                    }
                except Exception as e:
                    logger.error(f"Mem0 sync failed: {e}")
                    sync_results["errors"].append(f"Mem0 sync failed: {str(e)}")
            
            # Sync with Clio if available
            if self.clio:
                try:
                    clio_nodes = await self._sync_from_clio()
                    sync_results["systems_synced"]["clio"] = {
                        "status": "completed",
                        "nodes_synced": len(clio_nodes),
                    }
                except Exception as e:
                    logger.error(f"Clio sync failed: {e}")
                    sync_results["errors"].append(f"Clio sync failed: {str(e)}")
                    
        except Exception as e:
            sync_results["errors"].append(f"Sync failed: {str(e)}")

        sync_results.update(
            {
                "completed_at": datetime.utcnow().isoformat(),
                "total_nodes_after": len(self.nodes),
                "nodes_added": len(self.nodes) - sync_results["total_nodes_before"],
            }
        )

        return sync_results
    
    async def _sync_from_mem0(self) -> List[str]:
        """Sync knowledge from Mem0"""
        if not self.mem0:
            return []
        
        synced_nodes = []
        # Get memories from Mem0 and convert to knowledge nodes
        # This is a placeholder - real implementation would fetch actual data
        logger.info("Syncing from Mem0...")
        return synced_nodes
    
    async def _sync_from_clio(self) -> List[str]:
        """Sync knowledge from Clio"""
        if not self.clio:
            return []
        
        synced_nodes = []
        # Fetch data from Clio and convert to knowledge nodes
        logger.info("Syncing from Clio...")
        return synced_nodes

    async def get_knowledge_graph_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics"""
        node_type_counts = {}
        for node in self.nodes.values():
            node_type_counts[node.node_type.value] = (
                node_type_counts.get(node.node_type.value, 0) + 1
            )

        return {
            "total_nodes": len(self.nodes),
            "total_relationships": len(self.relationships),
            "node_types": node_type_counts,
        }


# Global knowledge graph synchronizer
kg_synchronizer: Optional[KnowledgeGraphSynchronizer] = None


def get_knowledge_graph_synchronizer() -> KnowledgeGraphSynchronizer:
    global kg_synchronizer
    if kg_synchronizer is None:
        kg_synchronizer = KnowledgeGraphSynchronizer()
    return kg_synchronizer
