"""
Unit tests for chunk embedding functionality.

Tests:
- Embedding text building with/without concepts
- Chunk loading with concept resolution
- Verification logic
"""
import pytest
import sys
from pathlib import Path
from uuid import UUID, uuid4

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / "apps" / "api"))

# Mock models for testing
class MockChunk:
    """Mock ReadingChunk for testing."""
    def __init__(self, id=None, title="Test Chunk", content="This is test content.", corpus_section="3.2.1"):
        self.id = id or uuid4()
        self.title = title
        self.content = content
        self.corpus_section = corpus_section


class MockConcept:
    """Mock Concept for testing."""
    def __init__(self, id=None, name="Test Concept"):
        self.id = id or uuid4()
        self.name = name


# =============================================================================
# Test Embedding Text Building
# =============================================================================

class TestEmbeddingTextBuilding:
    """Test embedding text building from chunks and concepts."""

    def test_build_chunk_embedding_text_with_concepts(self):
        """Test embedding text building with concepts."""
        from src.services.embedding_service import EmbeddingService

        chunk = MockChunk(
            title="Stakeholder Analysis",
            content="Stakeholder analysis is the process of analyzing stakeholders.",
            corpus_section="3.2.1"
        )
        concepts = [
            MockConcept(name="Stakeholder Analysis"),
            MockConcept(name="Communication Planning")
        ]

        text = EmbeddingService.build_chunk_embedding_text(chunk, concepts)

        # Should include title, content, and concept names
        assert "Stakeholder Analysis." in text
        assert "Stakeholder analysis is the process" in text
        assert "Concepts: Stakeholder Analysis, Communication Planning" in text

    def test_build_chunk_embedding_text_without_concepts(self):
        """Test embedding text building without concepts (fallback to section)."""
        from src.services.embedding_service import EmbeddingService

        chunk = MockChunk(
            title="Introduction",
            content="This is an introduction section.",
            corpus_section="1.0"
        )
        concepts = []

        text = EmbeddingService.build_chunk_embedding_text(chunk, concepts)

        # Should include title, content, and section reference (fallback)
        assert "Introduction." in text
        assert "This is an introduction section." in text
        assert "Section: 1.0" in text

    def test_build_chunk_embedding_text_single_concept(self):
        """Test embedding text building with single concept."""
        from src.services.embedding_service import EmbeddingService

        chunk = MockChunk(
            title="SWOT Analysis",
            content="SWOT analysis examines strengths, weaknesses, opportunities, and threats."
        )
        concepts = [MockConcept(name="SWOT Analysis")]

        text = EmbeddingService.build_chunk_embedding_text(chunk, concepts)

        assert "SWOT Analysis." in text
        assert "Concepts: SWOT Analysis" in text

    def test_build_chunk_embedding_text_multiple_concepts(self):
        """Test embedding text building with multiple concepts."""
        from src.services.embedding_service import EmbeddingService

        chunk = MockChunk(title="Requirements", content="Requirements define the needed capabilities.")
        concepts = [
            MockConcept(name="Functional Requirements"),
            MockConcept(name="Non-Functional Requirements"),
            MockConcept(name="Business Requirements")
        ]

        text = EmbeddingService.build_chunk_embedding_text(chunk, concepts)

        assert "Concepts: Functional Requirements, Non-Functional Requirements, Business Requirements" in text

    def test_build_chunk_embedding_text_truncation(self):
        """Test that very long texts are truncated to avoid exceeding token limits."""
        from src.services.embedding_service import EmbeddingService, MAX_EMBEDDING_TOKENS

        # Create chunk with very long content (exceeds max tokens)
        very_long_content = "word " * 10000  # ~10k words
        chunk = MockChunk(
            title="Long Document",
            content=very_long_content,
            corpus_section="99.99"
        )
        concepts = [MockConcept(name="Test Concept")]

        text = EmbeddingService.build_chunk_embedding_text(chunk, concepts)

        # Should be truncated (rough estimate: 1 token ~= 4 chars)
        max_chars = MAX_EMBEDDING_TOKENS * 4
        assert len(text) <= max_chars


# =============================================================================
# Test Chunk Loading (Mock-based)
# =============================================================================

class TestChunkLoading:
    """Test chunk loading with concept resolution."""

    def test_chunk_with_concepts_dataclass(self):
        """Test ChunkWithConcepts dataclass structure."""
        # Import the dataclass from the script
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        sys.path.append(str(project_root / "scripts"))

        from generate_chunk_embeddings import ChunkWithConcepts

        chunk = MockChunk()
        concepts = [MockConcept(name="Concept 1"), MockConcept(name="Concept 2")]

        item = ChunkWithConcepts(chunk=chunk, concepts=concepts)

        assert item.chunk == chunk
        assert item.concepts == concepts
        assert len(item.concepts) == 2

    def test_chunk_with_empty_concepts(self):
        """Test ChunkWithConcepts with no concepts."""
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        sys.path.append(str(project_root / "scripts"))

        from generate_chunk_embeddings import ChunkWithConcepts

        chunk = MockChunk()
        concepts = []

        item = ChunkWithConcepts(chunk=chunk, concepts=concepts)

        assert item.chunk == chunk
        assert item.concepts == []


# =============================================================================
# Test Progress Tracking
# =============================================================================

class TestProgressTracker:
    """Test progress tracking functionality."""

    def test_progress_tracker_initialization(self):
        """Test ProgressTracker initialization."""
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        sys.path.append(str(project_root / "scripts"))

        from generate_chunk_embeddings import ProgressTracker

        tracker = ProgressTracker(total_chunks=100)

        assert tracker.total_chunks == 100
        assert tracker.chunks_processed == 0
        assert tracker.embeddings_generated == 0
        assert tracker.vectors_uploaded == 0

    def test_progress_tracker_updates(self):
        """Test ProgressTracker update methods."""
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        sys.path.append(str(project_root / "scripts"))

        from generate_chunk_embeddings import ProgressTracker

        tracker = ProgressTracker(total_chunks=100)

        tracker.update_processed(10)
        tracker.update_embeddings(10)
        tracker.update_uploaded(8)

        assert tracker.chunks_processed == 10
        assert tracker.embeddings_generated == 10
        assert tracker.vectors_uploaded == 8


# =============================================================================
# Test Verification Report
# =============================================================================

class TestVerificationReport:
    """Test verification report functionality."""

    def test_verification_report_creation(self):
        """Test VerificationReport creation."""
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        sys.path.append(str(project_root / "scripts"))

        from generate_chunk_embeddings import VerificationReport

        report = VerificationReport(
            chunks_in_postgres=100,
            vectors_in_qdrant=100,
            vectors_with_course_id=100,
            vectors_with_concepts=98,
            missing_vectors=[],
            vectors_without_concepts=[uuid4(), uuid4()],
            verified=True
        )

        assert report.chunks_in_postgres == 100
        assert report.vectors_in_qdrant == 100
        assert report.vectors_with_concepts == 98
        assert len(report.vectors_without_concepts) == 2
        assert report.verified is True

    def test_verification_report_failed(self):
        """Test VerificationReport when verification fails."""
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        sys.path.append(str(project_root / "scripts"))

        from generate_chunk_embeddings import VerificationReport

        missing_ids = [uuid4(), uuid4(), uuid4()]
        report = VerificationReport(
            chunks_in_postgres=100,
            vectors_in_qdrant=97,
            vectors_with_course_id=97,
            vectors_with_concepts=97,
            missing_vectors=missing_ids,
            vectors_without_concepts=[],
            verified=False
        )

        assert report.chunks_in_postgres == 100
        assert report.vectors_in_qdrant == 97
        assert len(report.missing_vectors) == 3
        assert report.verified is False


# =============================================================================
# Test ChunkVectorItem
# =============================================================================

class TestChunkVectorItem:
    """Test ChunkVectorItem dataclass."""

    def test_chunk_vector_item_creation(self):
        """Test ChunkVectorItem creation with all fields."""
        from src.services.qdrant_upload_service import ChunkVectorItem

        chunk_id = uuid4()
        course_id = uuid4()
        vector = [0.1] * 3072  # 3072 dimensions

        item = ChunkVectorItem(
            chunk_id=chunk_id,
            course_id=course_id,
            vector=vector,
            title="Test Chunk",
            knowledge_area_id="ba-planning",
            corpus_section="3.2.1",
            concept_ids=["uuid-1", "uuid-2"],
            concept_names=["Concept 1", "Concept 2"],
            text_content="This is test content.",
            estimated_read_time=5
        )

        assert item.chunk_id == chunk_id
        assert item.course_id == course_id
        assert len(item.vector) == 3072
        assert item.title == "Test Chunk"
        assert item.knowledge_area_id == "ba-planning"
        assert item.corpus_section == "3.2.1"
        assert len(item.concept_ids) == 2
        assert len(item.concept_names) == 2
        assert item.estimated_read_time == 5

    def test_chunk_vector_item_with_empty_concepts(self):
        """Test ChunkVectorItem with no concepts."""
        from src.services.qdrant_upload_service import ChunkVectorItem

        item = ChunkVectorItem(
            chunk_id=uuid4(),
            course_id=uuid4(),
            vector=[0.1] * 3072,
            title="Test Chunk",
            knowledge_area_id="ba-planning",
            corpus_section="1.0",
            concept_ids=[],
            concept_names=[],
            text_content="Content",
            estimated_read_time=2
        )

        assert len(item.concept_ids) == 0
        assert len(item.concept_names) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
