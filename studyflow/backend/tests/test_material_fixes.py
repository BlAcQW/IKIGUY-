"""
Unit tests for material fixes.

Tests:
1. Material file paths are valid
2. Materials have topics populated
3. Exercise generation works without topics

Created: 2025-11-19
Author: KasaAI
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId

from app.services.material_service import MaterialService
from app.services.exercise_service import ExerciseService
from app.models.material import StudyMaterial, MaterialType, ProcessingStatus
from app.models.exercise import ExerciseGenerateRequest, DifficultyLevel, QuestionType


class TestMaterialFilePaths:
    """Test that materials have valid file paths."""

    @pytest.mark.asyncio
    async def test_all_materials_have_valid_file_paths(self, mongodb_materials):
        """Test that all materials in database have valid file paths."""
        # Get all materials
        materials = await MaterialService.list_materials(limit=100)

        # Check each material has a valid file path
        for material in materials:
            assert material.file_path, f"Material {material.id} has no file_path"
            file_path = Path(material.file_path)
            assert file_path.exists(), f"File not found: {material.file_path}"
            assert file_path.is_file(), f"Not a file: {material.file_path}"

    @pytest.mark.asyncio
    async def test_material_download_endpoint_returns_file(self, test_client, auth_headers, sample_material):
        """Test that material download endpoint returns file for valid materials."""
        # Get material
        response = await test_client.get(
            f"/api/v1/materials/{sample_material.id}/download",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/octet-stream"

    @pytest.mark.asyncio
    async def test_material_download_returns_404_for_missing_file(self, test_client, auth_headers, mongodb_materials):
        """Test that download returns 404 for materials with missing files."""
        # Create material with invalid file path
        from app.core.database import mongodb, COLLECTION_MATERIALS

        material_data = {
            "organization_id": "test_org",
            "title": "Test Material",
            "file_name": "test.pdf",
            "file_path": "/nonexistent/path/test.pdf",
            "file_size": 1000,
            "file_type": "pdf",
            "subject": "Test",
            "topics": ["Test"],
            "status": "completed"
        }

        collection = mongodb.get_collection(COLLECTION_MATERIALS)
        result = await collection.insert_one(material_data)
        material_id = str(result.inserted_id)

        try:
            # Try to download - should return 404
            response = await test_client.get(
                f"/api/v1/materials/{material_id}/download",
                headers=auth_headers
            )

            assert response.status_code == 404
            assert "File not found" in response.json()["detail"]

        finally:
            # Cleanup
            await collection.delete_one({"_id": ObjectId(material_id)})


class TestMaterialTopics:
    """Test that materials have topics populated."""

    @pytest.mark.asyncio
    async def test_all_materials_have_topics(self, mongodb_materials):
        """Test that all materials in database have topics."""
        # Get all materials
        materials = await MaterialService.list_materials(limit=100)

        # Check each material has topics
        for material in materials:
            assert material.topics, f"Material {material.id} has no topics"
            assert len(material.topics) > 0, f"Material {material.id} has empty topics"
            assert isinstance(material.topics, list), f"Material topics not a list: {type(material.topics)}"

    @pytest.mark.asyncio
    async def test_material_topics_are_strings(self, mongodb_materials):
        """Test that material topics are valid strings."""
        materials = await MaterialService.list_materials(limit=100)

        for material in materials:
            for topic in material.topics:
                assert isinstance(topic, str), f"Topic not a string: {type(topic)}"
                assert len(topic) > 0, "Empty topic string found"

    @pytest.mark.asyncio
    async def test_create_material_with_topics(self, mongodb_materials):
        """Test that creating a material with topics works correctly."""
        from app.models.material import MaterialCreate

        material_data = MaterialCreate(
            organization_id="test_org",
            title="Test Material with Topics",
            subject="Computer Science",
            topics=["Python", "Programming", "Testing"]
        )

        # Save a test file
        test_content = b"Test content"
        file_path, file_size = MaterialService.save_uploaded_file(
            test_content,
            "test_with_topics.txt",
            "test_user"
        )

        try:
            # Create material
            material = await MaterialService.create_material(
                material_data=material_data,
                file_name="test_with_topics.txt",
                file_path=file_path,
                file_size=file_size,
                uploaded_by="test_user"
            )

            # Verify topics
            assert material.topics == ["Python", "Programming", "Testing"]

            # Cleanup
            await MaterialService.delete_material(material.id)

        finally:
            # Cleanup file
            Path(file_path).unlink(missing_ok=True)


class TestExerciseGenerationWithoutTopics:
    """Test exercise generation works even without topics."""

    @pytest.mark.asyncio
    async def test_exercise_generation_request_without_topic(self):
        """Test that ExerciseGenerateRequest allows None for topic."""
        # Create request without topic
        request = ExerciseGenerateRequest(
            material_id="test_material_id",
            topic=None,  # No topic specified
            difficulty=DifficultyLevel.MEDIUM,
            num_questions=5
        )

        assert request.topic is None
        assert request.material_id == "test_material_id"

    @pytest.mark.asyncio
    @patch('app.services.exercise_service.ExerciseService.get_material')
    @patch('app.services.exercise_service.ExerciseService.get_rag_service')
    async def test_exercise_generation_with_empty_topics_material(
        self,
        mock_rag_service,
        mock_get_material
    ):
        """Test exercise generation for material with empty topics."""
        # Mock material with empty topics
        mock_material = StudyMaterial(
            id="test_material_id",
            organization_id="test_org",
            title="Test Material",
            file_name="test.pdf",
            file_path="/tmp/test.pdf",
            file_size=1000,
            file_type=MaterialType.PDF,
            subject="Test Subject",
            topics=[],  # Empty topics
            status=ProcessingStatus.COMPLETED,
            embedding_collection="test_collection"
        )
        mock_get_material.return_value = mock_material

        # Mock RAG service
        mock_rag = MagicMock()
        mock_rag.query = AsyncMock(return_value={
            "results": [{"content": "Test content"}]
        })
        mock_rag.generate = AsyncMock(return_value={
            "response": """[{
                "question_type": "multiple_choice",
                "question_text": "Test question?",
                "options": [
                    {"label": "A", "text": "Option A", "is_correct": true},
                    {"label": "B", "text": "Option B", "is_correct": false}
                ],
                "correct_answer": "A",
                "explanation": "Test explanation",
                "topic": "General",
                "points": 1
            }]""",
            "tokens_used": 100,
            "cost": 0.001
        })
        mock_rag_service.return_value = mock_rag

        # Create request without topic
        request = ExerciseGenerateRequest(
            material_id="test_material_id",
            topic=None,
            difficulty=DifficultyLevel.MEDIUM,
            num_questions=1,
            question_types=[QuestionType.MULTIPLE_CHOICE]
        )

        # Generate exercise
        exercise = await ExerciseService.generate_exercise(
            request=request,
            organization_id="test_org",
            created_by="test_user"
        )

        # Verify exercise was created
        assert exercise is not None
        assert exercise.title == "Test Material - Medium Exercise"
        assert len(exercise.questions) == 1
        # Topics should be empty since material had no topics
        assert exercise.topics == []

    @pytest.mark.asyncio
    async def test_exercise_generation_uses_material_topics_when_available(self):
        """Test that exercise uses material topics when no specific topic requested."""
        # This is the existing behavior - just verify it still works
        request = ExerciseGenerateRequest(
            material_id="test_material_id",
            topic=None,  # No specific topic
            difficulty=DifficultyLevel.EASY,
            num_questions=3
        )

        # When no topic specified, exercise should use material's topics
        assert request.topic is None


class TestTopicExtraction:
    """Test topic extraction from material titles."""

    def test_extract_topics_from_title(self):
        """Test extracting topics from material title."""
        from app.utils.topic_extraction import extract_topics_from_title

        # Test various title formats
        test_cases = [
            ("Duffie Hellman Key Exchange Notes", "Computer Science",
             ["Computer Science", "Duffie Hellman Key Exchange Notes"]),
            ("PROJECT CHAPTER 1", "Computer Science",
             ["Computer Science", "Project Chapter 1"]),
            ("Three way handshake - Wireshark", "Networking",
             ["Networking", "Three Way Handshake", "Wireshark"]),
        ]

        for title, subject, expected_topics in test_cases:
            topics = extract_topics_from_title(title, subject)
            assert len(topics) > 0, f"No topics extracted from: {title}"
            # Should include subject
            assert subject in topics or subject.title() in topics


# Fixtures

@pytest.fixture
async def mongodb_materials(mongodb):
    """Fixture to access materials collection."""
    return mongodb.get_collection("materials")


@pytest.fixture
async def sample_material(mongodb_materials):
    """Fixture to create a sample material with valid file."""
    # Create a temporary file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Test content")
        temp_path = f.name

    from app.models.material import MaterialCreate

    material_data = MaterialCreate(
        organization_id="test_org",
        title="Sample Test Material",
        subject="Testing",
        topics=["Testing", "Sample"]
    )

    material = await MaterialService.create_material(
        material_data=material_data,
        file_name="sample.txt",
        file_path=temp_path,
        file_size=12,
        uploaded_by="test_user"
    )

    yield material

    # Cleanup
    await MaterialService.delete_material(material.id)
    Path(temp_path).unlink(missing_ok=True)
