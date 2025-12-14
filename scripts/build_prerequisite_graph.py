#!/usr/bin/env python3
"""
Build Prerequisite Graph Script

Constructs concept prerequisite relationships using:
1. Section hierarchy inference (parent sections are prerequisites)
2. Semantic inference (similar concepts with lower difficulty are prerequisites)
3. GPT-4 cross-KA inference (for complex cross-domain prerequisites)

Validates DAG structure, computes depths, exports graph, and stores in PostgreSQL.

Usage:
    python scripts/build_prerequisite_graph.py --course-id <UUID>
    python scripts/build_prerequisite_graph.py --course-id <UUID> --skip-gpt4
    python scripts/build_prerequisite_graph.py --course-id <UUID> --dry-run
"""
import argparse
import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from uuid import UUID

import networkx as nx

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "api"))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


@dataclass
class ConceptInfo:
    """Lightweight concept info for graph operations."""
    id: UUID
    name: str
    corpus_section_ref: Optional[str]
    knowledge_area_id: str
    difficulty_estimate: float
    description: Optional[str] = None


@dataclass
class PrerequisiteEdge:
    """Represents a prerequisite relationship."""
    concept_id: UUID
    prerequisite_concept_id: UUID
    strength: float
    relationship_type: str
    source: str  # 'hierarchy', 'semantic', 'gpt4'


class PrerequisiteGraphBuilder:
    """Builds and validates concept prerequisite graph."""

    def __init__(
        self,
        course_id: UUID,
        skip_embeddings: bool = False,
        skip_gpt4: bool = False,
        dry_run: bool = False,
        output_dir: Optional[str] = None
    ):
        self.course_id = course_id
        self.skip_embeddings = skip_embeddings
        self.skip_gpt4 = skip_gpt4
        self.dry_run = dry_run
        self.output_dir = Path(output_dir) if output_dir else Path("scripts/output")

        self.concepts: List[ConceptInfo] = []
        self.concept_map: Dict[UUID, ConceptInfo] = {}
        self.section_map: Dict[str, List[ConceptInfo]] = {}
        self.edges: List[PrerequisiteEdge] = []
        self.graph: Optional[nx.DiGraph] = None

    async def load_concepts(self, session: AsyncSession) -> None:
        """Load all concepts for the course from database."""
        from src.models.concept import Concept
        from sqlalchemy import select

        logger.info(f"Loading concepts for course {self.course_id}...")

        result = await session.execute(
            select(Concept)
            .where(Concept.course_id == self.course_id)
            .order_by(Concept.corpus_section_ref, Concept.name)
        )
        db_concepts = result.scalars().all()

        for c in db_concepts:
            info = ConceptInfo(
                id=c.id,
                name=c.name,
                corpus_section_ref=c.corpus_section_ref,
                knowledge_area_id=c.knowledge_area_id,
                difficulty_estimate=c.difficulty_estimate,
                description=c.description
            )
            self.concepts.append(info)
            self.concept_map[c.id] = info

            # Build section map for hierarchy inference
            if c.corpus_section_ref:
                if c.corpus_section_ref not in self.section_map:
                    self.section_map[c.corpus_section_ref] = []
                self.section_map[c.corpus_section_ref].append(info)

        logger.info(f"Loaded {len(self.concepts)} concepts")
        logger.info(f"Sections with concepts: {len(self.section_map)}")

    def infer_from_section_hierarchy(self) -> List[PrerequisiteEdge]:
        """
        Infer prerequisites from BABOK section hierarchy.

        Rule: Concepts in parent sections (e.g., 3.2) are prerequisites
        of concepts in child sections (e.g., 3.2.1).
        """
        logger.info("Inferring prerequisites from section hierarchy...")
        edges = []

        for concept in self.concepts:
            if not concept.corpus_section_ref:
                continue

            parent_section = self._get_parent_section(concept.corpus_section_ref)
            if not parent_section:
                continue

            # Find all concepts in parent section
            parent_concepts = self.section_map.get(parent_section, [])

            for parent_concept in parent_concepts:
                # Don't create self-loops
                if parent_concept.id == concept.id:
                    continue

                edge = PrerequisiteEdge(
                    concept_id=concept.id,
                    prerequisite_concept_id=parent_concept.id,
                    strength=0.8,  # Strong relationship for hierarchy
                    relationship_type="required",
                    source="hierarchy"
                )
                edges.append(edge)

        logger.info(f"Inferred {len(edges)} prerequisites from section hierarchy")
        return edges

    def _get_parent_section(self, section_ref: str) -> Optional[str]:
        """Get parent section reference (e.g., '3.2.1' -> '3.2')."""
        parts = section_ref.split('.')
        if len(parts) <= 1:
            return None
        return '.'.join(parts[:-1])

    async def infer_from_embeddings(self) -> List[PrerequisiteEdge]:
        """
        Infer prerequisites from semantic similarity.

        Rule: If concept A is similar to B and A has lower difficulty,
        A is a prerequisite of B.
        """
        if self.skip_embeddings:
            logger.info("Skipping embedding-based inference (--skip-embeddings)")
            return []

        logger.info("Inferring prerequisites from embeddings...")
        edges = []

        try:
            from openai import OpenAI
            client = OpenAI()
        except Exception as e:
            logger.warning(f"Could not initialize OpenAI client: {e}")
            logger.warning("Skipping embedding-based inference")
            return []

        # Generate embeddings for all concepts
        concept_texts = []
        for c in self.concepts:
            text = f"{c.name}"
            if c.description:
                text += f": {c.description}"
            concept_texts.append(text)

        if not concept_texts:
            return edges

        logger.info(f"Generating embeddings for {len(concept_texts)} concepts...")

        # Batch embeddings (max 100 at a time)
        embeddings = []
        batch_size = 100

        for i in range(0, len(concept_texts), batch_size):
            batch = concept_texts[i:i + batch_size]
            try:
                response = client.embeddings.create(
                    model="text-embedding-3-large",
                    input=batch
                )
                for item in response.data:
                    embeddings.append(item.embedding)
                logger.info(f"Generated embeddings for batch {i // batch_size + 1}")
            except Exception as e:
                logger.error(f"Error generating embeddings: {e}")
                return edges

        # Calculate pairwise similarity and infer prerequisites
        import numpy as np

        embeddings_array = np.array(embeddings)
        norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
        normalized = embeddings_array / norms

        # Find similar pairs
        similarity_threshold = 0.7
        difficulty_threshold = 0.1  # Minimum difficulty difference

        for i, concept_a in enumerate(self.concepts):
            for j, concept_b in enumerate(self.concepts):
                if i >= j:  # Skip self and already-checked pairs
                    continue

                similarity = float(np.dot(normalized[i], normalized[j]))

                if similarity < similarity_threshold:
                    continue

                # Lower difficulty concept is prerequisite of higher
                diff_a = concept_a.difficulty_estimate
                diff_b = concept_b.difficulty_estimate

                if abs(diff_a - diff_b) < difficulty_threshold:
                    continue  # Too similar in difficulty

                if diff_a < diff_b:
                    prereq_id = concept_a.id
                    target_id = concept_b.id
                else:
                    prereq_id = concept_b.id
                    target_id = concept_a.id

                # Determine strength based on similarity
                if similarity >= 0.9:
                    strength = 0.9
                elif similarity >= 0.8:
                    strength = 0.7
                else:
                    strength = 0.5

                edge = PrerequisiteEdge(
                    concept_id=target_id,
                    prerequisite_concept_id=prereq_id,
                    strength=strength,
                    relationship_type="related",
                    source="semantic"
                )
                edges.append(edge)

        logger.info(f"Inferred {len(edges)} prerequisites from embeddings")
        return edges

    async def infer_cross_ka_prerequisites(self) -> List[PrerequisiteEdge]:
        """
        Infer cross-KA prerequisites using GPT-4.

        For concepts that might depend on other KAs, use GPT-4 to identify
        prerequisite relationships.
        """
        if self.skip_gpt4:
            logger.info("Skipping GPT-4 inference (--skip-gpt4)")
            return []

        logger.info("Inferring cross-KA prerequisites with GPT-4...")
        edges = []

        try:
            from openai import OpenAI
            client = OpenAI()
        except Exception as e:
            logger.warning(f"Could not initialize OpenAI client: {e}")
            return edges

        # Group concepts by KA
        ka_concepts: Dict[str, List[ConceptInfo]] = {}
        for c in self.concepts:
            if c.knowledge_area_id not in ka_concepts:
                ka_concepts[c.knowledge_area_id] = []
            ka_concepts[c.knowledge_area_id].append(c)

        knowledge_areas = list(ka_concepts.keys())

        if len(knowledge_areas) < 2:
            logger.info("Only one KA found, skipping cross-KA inference")
            return edges

        # For each KA, identify concepts that might have cross-KA prerequisites
        # Focus on higher-difficulty concepts (they're more likely to have prerequisites)
        for ka_id, concepts in ka_concepts.items():
            # Get concepts with difficulty > 0.5 (more advanced)
            advanced_concepts = [c for c in concepts if c.difficulty_estimate > 0.5]

            if not advanced_concepts:
                continue

            # Build list of concepts from other KAs
            other_ka_concepts = []
            for other_ka, other_concepts in ka_concepts.items():
                if other_ka == ka_id:
                    continue
                for c in other_concepts:
                    other_ka_concepts.append({
                        "id": str(c.id),
                        "name": c.name,
                        "ka": other_ka,
                        "difficulty": c.difficulty_estimate
                    })

            if not other_ka_concepts:
                continue

            # Batch process advanced concepts
            for concept in advanced_concepts[:10]:  # Limit to 10 per KA for efficiency
                prompt = self._build_cross_ka_prompt(concept, other_ka_concepts)

                try:
                    response = client.chat.completions.create(
                        model="gpt-4-turbo-preview",
                        messages=[
                            {"role": "system", "content": "You are analyzing prerequisite relationships between BABOK v3 concepts."},
                            {"role": "user", "content": prompt}
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.3
                    )

                    result = json.loads(response.choices[0].message.content)
                    prereqs = result.get("prerequisites", [])

                    for prereq in prereqs:
                        prereq_id = prereq.get("prerequisite_concept_id")
                        if not prereq_id:
                            continue

                        try:
                            prereq_uuid = UUID(prereq_id)
                        except ValueError:
                            continue

                        if prereq_uuid not in self.concept_map:
                            continue

                        edge = PrerequisiteEdge(
                            concept_id=concept.id,
                            prerequisite_concept_id=prereq_uuid,
                            strength=prereq.get("strength", 0.6),
                            relationship_type="helpful",
                            source="gpt4"
                        )
                        edges.append(edge)

                except Exception as e:
                    logger.warning(f"GPT-4 error for concept {concept.name}: {e}")
                    continue

        logger.info(f"Inferred {len(edges)} cross-KA prerequisites from GPT-4")
        return edges

    def _build_cross_ka_prompt(
        self,
        concept: ConceptInfo,
        other_ka_concepts: List[Dict]
    ) -> str:
        """Build prompt for GPT-4 cross-KA prerequisite inference."""
        other_concepts_str = json.dumps(other_ka_concepts[:50], indent=2)  # Limit size

        return f"""You are analyzing prerequisite relationships between BABOK v3 concepts.

Target Concept:
- ID: {concept.id}
- Name: {concept.name}
- Knowledge Area: {concept.knowledge_area_id}
- Description: {concept.description or 'N/A'}
- Difficulty: {concept.difficulty_estimate}

Available Concepts from OTHER Knowledge Areas:
{other_concepts_str}

Identify which concepts from other Knowledge Areas are prerequisites for understanding the target concept.
A prerequisite is knowledge that should be understood BEFORE learning the target concept.

Output as JSON:
{{
  "prerequisites": [
    {{
      "prerequisite_concept_id": "uuid",
      "prerequisite_concept_name": "name",
      "strength": 0.7,
      "reasoning": "Brief explanation"
    }}
  ]
}}

Rules:
- Only include true prerequisites (not just related concepts)
- Maximum 5 prerequisites per concept
- Cross-KA prerequisites are typically "helpful" not "required"
- Use strength 0.5-0.8 for cross-KA relationships
- Return empty array if no clear prerequisites found
"""

    def merge_and_deduplicate(self, all_edges: List[List[PrerequisiteEdge]]) -> None:
        """
        Merge edges from all sources and deduplicate.

        When duplicates exist, keep the edge with highest strength.
        """
        logger.info("Merging and deduplicating prerequisites...")

        edge_map: Dict[Tuple[UUID, UUID], PrerequisiteEdge] = {}

        for edge_list in all_edges:
            for edge in edge_list:
                key = (edge.concept_id, edge.prerequisite_concept_id)

                if key not in edge_map or edge.strength > edge_map[key].strength:
                    edge_map[key] = edge

        self.edges = list(edge_map.values())
        logger.info(f"Total unique prerequisites after merge: {len(self.edges)}")

    def validate_dag(self) -> bool:
        """
        Validate that the prerequisite graph is a DAG (no cycles).

        Returns True if valid, False if cycles detected.
        """
        logger.info("Validating DAG structure...")

        self.graph = nx.DiGraph()

        # Add nodes (all concepts)
        for concept in self.concepts:
            self.graph.add_node(
                concept.id,
                name=concept.name,
                ka=concept.knowledge_area_id,
                difficulty=concept.difficulty_estimate,
                section=concept.corpus_section_ref
            )

        # Add edges (prerequisites point from prereq to dependent)
        for edge in self.edges:
            self.graph.add_edge(
                edge.prerequisite_concept_id,
                edge.concept_id,
                strength=edge.strength,
                relationship_type=edge.relationship_type,
                source=edge.source
            )

        try:
            # Attempt topological sort
            order = list(nx.topological_sort(self.graph))
            logger.info(f"Valid DAG with {len(order)} nodes in topological order")
            return True
        except nx.NetworkXUnfeasible:
            # Cycles detected
            cycles = list(nx.simple_cycles(self.graph))
            logger.error(f"Invalid DAG: {len(cycles)} cycles detected!")

            # Log first few cycles for debugging
            for i, cycle in enumerate(cycles[:5]):
                cycle_names = [self.concept_map[cid].name for cid in cycle if cid in self.concept_map]
                logger.error(f"  Cycle {i + 1}: {' -> '.join(cycle_names)}")

            return False

    def find_and_remove_cycles(self) -> int:
        """
        Find cycles and remove weakest edges to break them.

        Returns number of edges removed.
        """
        logger.info("Finding and removing cycles...")
        removed_count = 0

        while True:
            try:
                nx.topological_sort(self.graph)
                break  # No cycles
            except nx.NetworkXUnfeasible:
                # Find a cycle
                try:
                    cycle = nx.find_cycle(self.graph)
                except nx.NetworkXNoCycle:
                    break

                # Find weakest edge in cycle
                min_strength = float('inf')
                weakest_edge = None

                for u, v in cycle:
                    edge_data = self.graph.edges[u, v]
                    if edge_data['strength'] < min_strength:
                        min_strength = edge_data['strength']
                        weakest_edge = (u, v)

                if weakest_edge:
                    self.graph.remove_edge(*weakest_edge)
                    # Also remove from edges list
                    self.edges = [
                        e for e in self.edges
                        if not (e.prerequisite_concept_id == weakest_edge[0] and
                               e.concept_id == weakest_edge[1])
                    ]
                    removed_count += 1
                    logger.warning(
                        f"Removed edge to break cycle: "
                        f"{self.concept_map.get(weakest_edge[0], {}).name if weakest_edge[0] in self.concept_map else weakest_edge[0]} -> "
                        f"{self.concept_map.get(weakest_edge[1], {}).name if weakest_edge[1] in self.concept_map else weakest_edge[1]}"
                    )

        logger.info(f"Removed {removed_count} edges to ensure DAG")
        return removed_count

    def compute_prerequisite_depths(self) -> Dict[UUID, int]:
        """
        Compute prerequisite depth for each concept using BFS from roots.

        Depth 0 = root concepts (no prerequisites)
        """
        logger.info("Computing prerequisite depths...")

        if self.graph is None:
            raise ValueError("Graph not built. Call validate_dag() first.")

        depths: Dict[UUID, int] = {}

        # Find root nodes (no incoming edges = no prerequisites)
        roots = [n for n in self.graph.nodes() if self.graph.in_degree(n) == 0]
        logger.info(f"Found {len(roots)} root concepts")

        # BFS from all roots
        for root in roots:
            for node, depth in nx.single_source_shortest_path_length(self.graph, root).items():
                # Use minimum depth if node reachable from multiple roots
                if node not in depths or depth < depths[node]:
                    depths[node] = depth

        # Any unreachable nodes get depth 0
        for node in self.graph.nodes():
            if node not in depths:
                depths[node] = 0

        # Log depth distribution
        depth_counts: Dict[int, int] = {}
        for d in depths.values():
            depth_counts[d] = depth_counts.get(d, 0) + 1

        logger.info("Depth distribution:")
        for d in sorted(depth_counts.keys()):
            logger.info(f"  Depth {d}: {depth_counts[d]} concepts")

        return depths

    def compute_graph_statistics(self) -> Dict:
        """Compute comprehensive graph statistics."""
        logger.info("Computing graph statistics...")

        if self.graph is None:
            raise ValueError("Graph not built")

        stats = {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "avg_prerequisites_per_concept": 0.0,
            "max_prerequisites_per_concept": 0,
            "avg_dependents_per_concept": 0.0,
            "max_dependents_per_concept": 0,
            "max_depth": 0,
            "root_concept_count": 0,
            "leaf_concept_count": 0,
            "orphan_count": 0,  # No prereqs AND no dependents
            "edge_sources": {},
            "relationship_types": {}
        }

        if stats["total_nodes"] == 0:
            return stats

        # Prerequisites per concept (in-degree)
        in_degrees = [self.graph.in_degree(n) for n in self.graph.nodes()]
        stats["avg_prerequisites_per_concept"] = sum(in_degrees) / len(in_degrees)
        stats["max_prerequisites_per_concept"] = max(in_degrees)

        # Dependents per concept (out-degree)
        out_degrees = [self.graph.out_degree(n) for n in self.graph.nodes()]
        stats["avg_dependents_per_concept"] = sum(out_degrees) / len(out_degrees)
        stats["max_dependents_per_concept"] = max(out_degrees)

        # Root and leaf counts
        stats["root_concept_count"] = sum(1 for d in in_degrees if d == 0)
        stats["leaf_concept_count"] = sum(1 for d in out_degrees if d == 0)

        # Orphan count (isolated nodes)
        stats["orphan_count"] = sum(
            1 for n in self.graph.nodes()
            if self.graph.in_degree(n) == 0 and self.graph.out_degree(n) == 0
        )

        # Max depth (longest path)
        try:
            stats["max_depth"] = nx.dag_longest_path_length(self.graph)
        except nx.NetworkXUnfeasible:
            stats["max_depth"] = -1  # Not a DAG

        # Edge source distribution
        for edge in self.edges:
            stats["edge_sources"][edge.source] = stats["edge_sources"].get(edge.source, 0) + 1
            stats["relationship_types"][edge.relationship_type] = (
                stats["relationship_types"].get(edge.relationship_type, 0) + 1
            )

        return stats

    def export_to_graphml(self, output_path: Optional[Path] = None) -> Path:
        """Export graph to GraphML format for visualization."""
        if output_path is None:
            output_path = self.output_dir / "prerequisite_graph.graphml"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert UUID nodes to strings for GraphML compatibility
        G_export = nx.DiGraph()
        for node, data in self.graph.nodes(data=True):
            G_export.add_node(str(node), **{k: str(v) for k, v in data.items()})
        for u, v, data in self.graph.edges(data=True):
            G_export.add_edge(str(u), str(v), **{k: str(v) for k, v in data.items()})

        nx.write_graphml(G_export, str(output_path))
        logger.info(f"Exported GraphML to {output_path}")
        return output_path

    def export_to_json(self, output_path: Optional[Path] = None) -> Path:
        """Export graph to JSON format for D3.js visualization."""
        if output_path is None:
            output_path = self.output_dir / "prerequisite_graph.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        nodes = []
        for node, data in self.graph.nodes(data=True):
            nodes.append({
                "id": str(node),
                "name": data.get("name", ""),
                "ka": data.get("ka", ""),
                "difficulty": data.get("difficulty", 0.5),
                "section": data.get("section", "")
            })

        links = []
        for u, v, data in self.graph.edges(data=True):
            links.append({
                "source": str(u),
                "target": str(v),
                "strength": data.get("strength", 1.0),
                "relationship_type": data.get("relationship_type", "required"),
                "edge_source": data.get("source", "unknown")
            })

        graph_data = {"nodes": nodes, "links": links}

        with open(output_path, 'w') as f:
            json.dump(graph_data, f, indent=2)

        logger.info(f"Exported JSON to {output_path}")
        return output_path

    async def store_in_database(self, session: AsyncSession) -> int:
        """Store prerequisites in PostgreSQL."""
        if self.dry_run:
            logger.info("Dry run - skipping database writes")
            return 0

        from src.repositories.concept_repository import ConceptRepository
        from src.schemas.concept_prerequisite import PrerequisiteCreate, RelationshipType

        repo = ConceptRepository(session)

        # Clear existing prerequisites for this course
        deleted = await repo.delete_all_prerequisites_for_course(self.course_id)
        logger.info(f"Deleted {deleted} existing prerequisites")

        # Convert edges to PrerequisiteCreate schemas
        prereqs = []
        for edge in self.edges:
            prereq = PrerequisiteCreate(
                concept_id=edge.concept_id,
                prerequisite_concept_id=edge.prerequisite_concept_id,
                strength=edge.strength,
                relationship_type=RelationshipType(edge.relationship_type)
            )
            prereqs.append(prereq)

        # Bulk insert
        created = await repo.bulk_add_prerequisites(prereqs)
        logger.info(f"Created {created} prerequisites")

        return created

    async def update_concept_depths(
        self,
        session: AsyncSession,
        depths: Dict[UUID, int]
    ) -> int:
        """Update prerequisite_depth for all concepts."""
        if self.dry_run:
            logger.info("Dry run - skipping depth updates")
            return 0

        from src.repositories.concept_repository import ConceptRepository

        repo = ConceptRepository(session)
        updated = await repo.update_prerequisite_depths(depths)
        logger.info(f"Updated depths for {updated} concepts")

        return updated


async def main():
    """Main orchestrator for prerequisite graph construction."""
    parser = argparse.ArgumentParser(
        description="Build concept prerequisite graph"
    )
    parser.add_argument(
        "--course-id",
        type=str,
        required=True,
        help="UUID of the course to process"
    )
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Skip semantic embedding-based inference"
    )
    parser.add_argument(
        "--skip-gpt4",
        action="store_true",
        help="Skip GPT-4 cross-KA inference"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip database writes"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="scripts/output",
        help="Directory for graph exports"
    )
    parser.add_argument(
        "--remove-cycles",
        action="store_true",
        help="Automatically remove cycles instead of failing"
    )

    args = parser.parse_args()

    try:
        course_id = UUID(args.course_id)
    except ValueError:
        logger.error(f"Invalid course ID: {args.course_id}")
        sys.exit(1)

    # Database connection
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/learnr"
    )

    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    builder = PrerequisiteGraphBuilder(
        course_id=course_id,
        skip_embeddings=args.skip_embeddings,
        skip_gpt4=args.skip_gpt4,
        dry_run=args.dry_run,
        output_dir=args.output_dir
    )

    async with async_session() as session:
        try:
            # 1. Load concepts
            await builder.load_concepts(session)

            if not builder.concepts:
                logger.error("No concepts found for this course")
                sys.exit(1)

            # 2-4. Infer prerequisites from multiple sources
            hierarchy_edges = builder.infer_from_section_hierarchy()
            semantic_edges = await builder.infer_from_embeddings()
            gpt4_edges = await builder.infer_cross_ka_prerequisites()

            # 5. Merge and deduplicate
            builder.merge_and_deduplicate([hierarchy_edges, semantic_edges, gpt4_edges])

            # 6. Validate DAG
            if not builder.validate_dag():
                if args.remove_cycles:
                    builder.find_and_remove_cycles()
                    if not builder.validate_dag():
                        logger.error("Could not create valid DAG")
                        sys.exit(1)
                else:
                    logger.error("Graph contains cycles. Use --remove-cycles to auto-fix.")
                    sys.exit(1)

            # 7. Compute depths
            depths = builder.compute_prerequisite_depths()

            # 8. Store in database
            await builder.store_in_database(session)

            # 9. Update concept depths
            await builder.update_concept_depths(session, depths)

            # 10. Export graphs
            builder.export_to_graphml()
            builder.export_to_json()

            # 11. Print statistics
            stats = builder.compute_graph_statistics()

            print("\n" + "=" * 60)
            print("PREREQUISITE GRAPH STATISTICS")
            print("=" * 60)
            print(f"Total concepts: {stats['total_nodes']}")
            print(f"Total prerequisites: {stats['total_edges']}")
            print(f"Avg prerequisites/concept: {stats['avg_prerequisites_per_concept']:.2f}")
            print(f"Max prerequisites/concept: {stats['max_prerequisites_per_concept']}")
            print(f"Root concepts (foundational): {stats['root_concept_count']}")
            print(f"Leaf concepts (advanced): {stats['leaf_concept_count']}")
            print(f"Max depth: {stats['max_depth']}")
            print(f"\nEdge sources: {stats['edge_sources']}")
            print(f"Relationship types: {stats['relationship_types']}")
            print("=" * 60)

            # Validate against targets
            avg_prereqs = stats['avg_prerequisites_per_concept']
            max_depth = stats['max_depth']

            warnings = []
            if avg_prereqs < 2:
                warnings.append(f"Warning: Avg prerequisites ({avg_prereqs:.1f}) below target (2-5)")
            if avg_prereqs > 5:
                warnings.append(f"Warning: Avg prerequisites ({avg_prereqs:.1f}) above target (2-5)")
            if max_depth > 10:
                warnings.append(f"Warning: Max depth ({max_depth}) exceeds target (<=10)")

            for w in warnings:
                logger.warning(w)

            if not args.dry_run:
                await session.commit()
                logger.info("Changes committed to database")

            logger.info("Prerequisite graph construction complete!")

        except Exception as e:
            logger.error(f"Error building prerequisite graph: {e}")
            await session.rollback()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
