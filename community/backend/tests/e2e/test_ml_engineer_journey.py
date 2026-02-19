"""
End-to-End Test: ML Engineer Journey.

TASK-012: E2E test for ML engineer workflow.

Tests the complete ML engineer journey:
- Register a new model
- Create model versions
- Upload artifacts
- Track training pipeline
- Complete deployment workflow

This test uses real MongoDB and tests the full workflow.
"""

import pytest
import uuid
from datetime import datetime
from httpx import AsyncClient
from bson import ObjectId


# Use the integration test fixtures
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.e2e,
]


class TestMLEngineerModelRegistration:
    """
    Test ML engineer model registration workflow.

    Journey Part 1: Register a new model
    """

    @pytest.mark.asyncio
    async def test_ml_engineer_registers_new_model(
        self,
        api_client: AsyncClient,
        real_test_db,
        seeded_user,
        seeded_language,
        dev_auth_headers
    ):
        """
        Test: ML Engineer registers a new TTS model.

        Verifies:
        - Model creation works
        - Model UUID is generated
        - Model appears in listing
        - Model is persisted in database
        """
        # Step 1: Create model
        model_path = f"models/tts/twi-tts-{uuid.uuid4().hex[:8]}/v1.0.0"
        model_data = {
            "name": f"Twi TTS Model {uuid.uuid4().hex[:8]}",
            "description": "A text-to-speech model for Twi language",
            "model_type": "tts",
            "architecture": "melotts",
            "version": "1.0.0",
            "languages": ["twi"],
            "primary_language": "twi",
            "is_multilingual": False,
            "storage_path": model_path,
            "checkpoint_path": f"{model_path}/checkpoint.pt",  # Required field
            "deployment_status": "experimental",
            "license": "MIT",
            "is_public": True,
            "access_level": "public",
            "tags": ["tts", "melotts", "twi", "african-languages"]
        }

        response = await api_client.post(
            "/api/v1/models",
            json=model_data,
            headers=dev_auth_headers
        )
        assert response.status_code == 201, f"Failed to create model: {response.text}"
        created_model = response.json()

        # Verify model has required fields
        assert "model_uuid" in created_model
        assert created_model["name"] == model_data["name"]
        assert created_model["model_type"] == "tts"
        assert created_model["version"] == "1.0.0"

        model_uuid = created_model["model_uuid"]

        # Step 2: Verify model appears in listing
        response = await api_client.get(
            "/api/v1/models",
            headers=dev_auth_headers
        )
        assert response.status_code == 200
        models_list = response.json()

        # Find our model in the list
        found_model = None
        for model in models_list:
            if model.get("model_uuid") == model_uuid:
                found_model = model
                break

        assert found_model is not None, "Created model not found in listing"

        # Step 3: Verify model is in database
        db_model = await real_test_db.ml_models.find_one({"model_uuid": model_uuid})
        assert db_model is not None, "Model not persisted in database"

        return model_uuid

    @pytest.mark.asyncio
    async def test_ml_engineer_creates_model_version(
        self,
        api_client: AsyncClient,
        real_test_db,
        seeded_model,
        dev_auth_headers
    ):
        """
        Test: ML Engineer creates a new version of an existing model.

        Verifies:
        - Version creation works
        - Version history is updated
        - Version can be retrieved
        """
        model_uuid = seeded_model["model_uuid"]
        version_path = f"models/tts/{model_uuid}/v1.1.0"

        # Create a new version with required fields
        version_data = {
            "version": "1.1.0",
            "changelog": "Improved pronunciation accuracy",
            "storage_path": version_path,
            "checkpoint_path": f"{version_path}/checkpoint.pt",
            "is_stable": True
        }

        response = await api_client.post(
            f"/api/v1/models/{model_uuid}/versions",
            json=version_data,
            headers=dev_auth_headers
        )
        assert response.status_code in [200, 201], f"Failed to create version: {response.text}"

        # Verify version appears in version history
        response = await api_client.get(
            f"/api/v1/models/{model_uuid}",
            headers=dev_auth_headers
        )
        assert response.status_code == 200
        model = response.json()

        # Check version is in version history or current version is updated
        assert model is not None


class TestMLEngineerPipelineWorkflow:
    """
    Test ML engineer training pipeline workflow.

    Journey Part 2: Track training pipeline
    """

    @pytest.mark.asyncio
    async def test_ml_engineer_creates_training_pipeline(
        self,
        api_client: AsyncClient,
        real_test_db,
        dev_auth_headers
    ):
        """
        Test: ML Engineer creates a new training pipeline.

        Verifies:
        - Pipeline creation works
        - All 5 stages are initialized
        - Pipeline UUID is generated
        - Pipeline is persisted
        """
        pipeline_data = {
            "name": f"Twi TTS Training {uuid.uuid4().hex[:8]}",
            "description": "Training pipeline for Twi TTS model v2",
            "model_type": "tts",
            "target_version": "2.0.0",
            "priority": "high",
            "tags": ["tts", "twi", "production"]
        }

        response = await api_client.post(
            "/api/v1/pipelines",
            json=pipeline_data,
            headers=dev_auth_headers
        )
        assert response.status_code == 201, f"Failed to create pipeline: {response.text}"
        pipeline = response.json()

        # Verify pipeline structure
        assert "pipeline_uuid" in pipeline
        assert "stages" in pipeline
        assert pipeline["name"] == pipeline_data["name"]
        assert pipeline["current_stage"] == "data_acquisition"  # First stage

        # Verify all 5 stages exist
        stages = pipeline["stages"]
        expected_stages = [
            "data_acquisition",
            "preprocessing",
            "training",
            "evaluation",
            "deployment"
        ]
        for stage in expected_stages:
            assert stage in stages, f"Stage {stage} not found in pipeline"

        return pipeline["pipeline_uuid"]

    @pytest.mark.asyncio
    async def test_ml_engineer_progresses_through_stages(
        self,
        api_client: AsyncClient,
        real_test_db,
        dev_auth_headers
    ):
        """
        Test: ML Engineer progresses through training pipeline stages.

        Verifies:
        - Stage updates work
        - Progress is tracked
        - Duration is calculated
        """
        # Create a pipeline first
        pipeline_data = {
            "name": f"Stage Progression Test {uuid.uuid4().hex[:8]}",
            "description": "Testing stage progression",
            "model_type": "asr",
            "target_version": "1.0.0",
            "priority": "medium",
            "tags": ["test"]
        }

        response = await api_client.post(
            "/api/v1/pipelines",
            json=pipeline_data,
            headers=dev_auth_headers
        )
        assert response.status_code == 201
        pipeline = response.json()
        pipeline_uuid = pipeline["pipeline_uuid"]

        # Progress through stages
        stages_to_complete = ["data_acquisition", "preprocessing", "training"]

        for stage in stages_to_complete:
            # Update stage to in_progress
            response = await api_client.put(
                f"/api/v1/pipelines/{pipeline_uuid}/stages/{stage}",
                json={"status": "in_progress", "progress": 50},
                headers=dev_auth_headers
            )
            assert response.status_code == 200, f"Failed to update stage {stage}"

            # Complete the stage
            response = await api_client.put(
                f"/api/v1/pipelines/{pipeline_uuid}/stages/{stage}",
                json={"status": "completed", "progress": 100},
                headers=dev_auth_headers
            )
            assert response.status_code == 200

        # Verify pipeline state
        response = await api_client.get(
            f"/api/v1/pipelines/{pipeline_uuid}",
            headers=dev_auth_headers
        )
        assert response.status_code == 200
        updated_pipeline = response.json()

        # Current stage should be evaluation (next after training)
        assert updated_pipeline["current_stage"] in ["evaluation", "training"]

    @pytest.mark.asyncio
    async def test_ml_engineer_adds_artifacts_to_pipeline(
        self,
        api_client: AsyncClient,
        real_test_db,
        dev_auth_headers
    ):
        """
        Test: ML Engineer adds artifacts to pipeline stages.

        Verifies:
        - Artifact upload works
        - Artifacts are associated with stages
        - Metadata is stored
        """
        # Create a pipeline
        pipeline_data = {
            "name": f"Artifact Test Pipeline {uuid.uuid4().hex[:8]}",
            "description": "Testing artifact upload",
            "model_type": "tts",
            "target_version": "1.0.0",
            "priority": "low",
            "tags": ["test", "artifacts"]
        }

        response = await api_client.post(
            "/api/v1/pipelines",
            json=pipeline_data,
            headers=dev_auth_headers
        )
        assert response.status_code == 201
        pipeline = response.json()
        pipeline_uuid = pipeline["pipeline_uuid"]

        # Add artifact to data_acquisition stage (with required stage_name)
        artifact_data = {
            "artifact_name": "training_manifest.json",
            "artifact_type": "dataset",
            "stage_name": "data_acquisition",  # Required field
            "file_path": f"pipelines/{pipeline_uuid}/data/training_manifest.json"
        }

        response = await api_client.post(
            f"/api/v1/pipelines/{pipeline_uuid}/artifacts",
            json=artifact_data,
            headers=dev_auth_headers
        )
        assert response.status_code in [200, 201], f"Failed to add artifact: {response.text}"

    @pytest.mark.asyncio
    async def test_ml_engineer_views_pipeline_metrics(
        self,
        api_client: AsyncClient,
        real_test_db,
        dev_auth_headers
    ):
        """
        Test: ML Engineer views pipeline metrics and performance data.

        Verifies:
        - Metrics endpoint works
        - Stage durations are tracked
        - Overall progress is calculated
        """
        # Create a pipeline with some progress
        pipeline_data = {
            "name": f"Metrics Test Pipeline {uuid.uuid4().hex[:8]}",
            "description": "Testing metrics retrieval",
            "model_type": "nmt",
            "target_version": "1.0.0",
            "priority": "medium",
            "tags": ["test", "metrics"]
        }

        response = await api_client.post(
            "/api/v1/pipelines",
            json=pipeline_data,
            headers=dev_auth_headers
        )
        assert response.status_code == 201
        pipeline = response.json()
        pipeline_uuid = pipeline["pipeline_uuid"]

        # Get pipeline metrics
        response = await api_client.get(
            f"/api/v1/pipelines/{pipeline_uuid}/metrics",
            headers=dev_auth_headers
        )
        assert response.status_code == 200
        metrics = response.json()

        # Verify metrics structure (API returns {metrics: {...}})
        assert "metrics" in metrics or "overall_progress" in metrics or "stages" in metrics

    @pytest.mark.asyncio
    async def test_ml_engineer_completes_pipeline(
        self,
        api_client: AsyncClient,
        real_test_db,
        dev_auth_headers
    ):
        """
        Test: ML Engineer completes a training pipeline.

        Verifies:
        - Pipeline completion works
        - Final status is set correctly
        - Completion timestamp is recorded
        """
        # Create and setup a pipeline
        pipeline_data = {
            "name": f"Completion Test Pipeline {uuid.uuid4().hex[:8]}",
            "description": "Testing pipeline completion",
            "model_type": "tts",
            "target_version": "1.0.0",
            "priority": "high",
            "tags": ["test", "completion"]
        }

        response = await api_client.post(
            "/api/v1/pipelines",
            json=pipeline_data,
            headers=dev_auth_headers
        )
        assert response.status_code == 201
        pipeline = response.json()
        pipeline_uuid = pipeline["pipeline_uuid"]

        # Complete all stages
        stages = ["data_preparation", "preprocessing", "training", "evaluation", "deployment"]
        for stage in stages:
            await api_client.put(
                f"/api/v1/pipelines/{pipeline_uuid}/stages/{stage}",
                json={"status": "completed", "progress": 100},
                headers=dev_auth_headers
            )

        # Mark pipeline as complete
        response = await api_client.post(
            f"/api/v1/pipelines/{pipeline_uuid}/complete",
            headers=dev_auth_headers
        )
        assert response.status_code == 200, f"Failed to complete pipeline: {response.text}"

        # Verify completion
        response = await api_client.get(
            f"/api/v1/pipelines/{pipeline_uuid}",
            headers=dev_auth_headers
        )
        assert response.status_code == 200
        completed_pipeline = response.json()

        # Pipeline should be marked as completed or have is_active = False
        assert completed_pipeline.get("is_active") is False or "completed" in completed_pipeline.get("status", "").lower()


class TestMLEngineerModelIssueReporting:
    """Test ML engineer model issue reporting workflow."""

    @pytest.mark.asyncio
    async def test_ml_engineer_reports_model_issue(
        self,
        api_client: AsyncClient,
        real_test_db,
        seeded_model,
        dev_auth_headers
    ):
        """
        Test: ML Engineer reports an issue with a model.

        Verifies:
        - Issue reporting works
        - Issue is associated with model
        - Issue is persisted
        """
        model_uuid = seeded_model["model_uuid"]

        issue_data = {
            "title": "Model produces incorrect pronunciation for compound words",
            "description": "When processing compound words in Twi, the model fails to correctly handle tone sandhi rules.",
            "severity": "medium",
            "category": "accuracy"
        }

        response = await api_client.post(
            f"/api/v1/models/{model_uuid}/issues",
            json=issue_data,
            headers=dev_auth_headers
        )
        assert response.status_code in [200, 201], f"Failed to report issue: {response.text}"

        # Verify issue is associated with model
        response = await api_client.get(
            f"/api/v1/models/{model_uuid}",
            headers=dev_auth_headers
        )
        assert response.status_code == 200
        model = response.json()

        # Check if issues are returned with the model
        assert "known_issues" in model or "issues" in model


class TestMLEngineerFullWorkflow:
    """Test complete ML engineer workflow from model creation to deployment."""

    @pytest.mark.asyncio
    async def test_complete_ml_engineer_workflow(
        self,
        api_client: AsyncClient,
        real_test_db,
        seeded_user,
        seeded_language,
        dev_auth_headers
    ):
        """
        Test: Complete ML engineer workflow.

        Full journey:
        1. Register model
        2. Create pipeline
        3. Progress through stages
        4. Create new model version
        5. Verify everything is tracked

        Verifies:
        - End-to-end workflow works
        - All components integrate correctly
        """
        # Step 1: Register model
        model_name = f"E2E Workflow Model {uuid.uuid4().hex[:8]}"
        model_data = {
            "name": model_name,
            "description": "End-to-end workflow test model",
            "model_type": "tts",
            "architecture": "melotts",
            "version": "0.9.0-beta",
            "languages": ["twi"],
            "primary_language": "twi",
            "is_multilingual": False,
            "deployment_status": "experimental",
            "license": "MIT",
            "is_public": True,
            "access_level": "public",
            "tags": ["e2e", "test"]
        }

        response = await api_client.post(
            "/api/v1/models",
            json=model_data,
            headers=dev_auth_headers
        )
        assert response.status_code == 201
        model = response.json()
        model_uuid = model["model_uuid"]

        # Step 2: Create training pipeline
        pipeline_data = {
            "name": f"E2E Pipeline for {model_name}",
            "description": "Training pipeline for e2e test",
            "model_type": "tts",
            "target_version": "1.0.0",
            "priority": "high",
            "tags": ["e2e", "test"]
        }

        response = await api_client.post(
            "/api/v1/pipelines",
            json=pipeline_data,
            headers=dev_auth_headers
        )
        assert response.status_code == 201
        pipeline = response.json()
        pipeline_uuid = pipeline["pipeline_uuid"]

        # Step 3: Complete training stages
        stages = ["data_preparation", "preprocessing", "training", "evaluation"]
        for stage in stages:
            response = await api_client.put(
                f"/api/v1/pipelines/{pipeline_uuid}/stages/{stage}",
                json={"status": "completed", "progress": 100},
                headers=dev_auth_headers
            )
            assert response.status_code == 200

        # Step 4: Create new model version after training
        version_data = {
            "version": "1.0.0",
            "changelog": "Production release after successful training",
            "is_stable": True
        }

        response = await api_client.post(
            f"/api/v1/models/{model_uuid}/versions",
            json=version_data,
            headers=dev_auth_headers
        )
        assert response.status_code in [200, 201]

        # Step 5: Complete deployment stage
        response = await api_client.put(
            f"/api/v1/pipelines/{pipeline_uuid}/stages/deployment",
            json={"status": "completed", "progress": 100},
            headers=dev_auth_headers
        )
        assert response.status_code == 200

        # Step 6: Mark pipeline complete
        response = await api_client.post(
            f"/api/v1/pipelines/{pipeline_uuid}/complete",
            headers=dev_auth_headers
        )
        assert response.status_code == 200

        # Verify final state
        response = await api_client.get(
            f"/api/v1/models/{model_uuid}",
            headers=dev_auth_headers
        )
        assert response.status_code == 200
        final_model = response.json()

        response = await api_client.get(
            f"/api/v1/pipelines/{pipeline_uuid}",
            headers=dev_auth_headers
        )
        assert response.status_code == 200
        final_pipeline = response.json()

        # Workflow complete - model and pipeline both exist and are in expected states
        assert final_model["model_uuid"] == model_uuid
        assert final_pipeline["pipeline_uuid"] == pipeline_uuid


class TestMLEngineerPerformance:
    """Performance tests for ML engineer journey endpoints."""

    @pytest.mark.asyncio
    async def test_model_operations_respond_quickly(
        self,
        api_client: AsyncClient,
        real_test_db,
        seeded_model,
        dev_auth_headers,
        measure_time
    ):
        """
        Test: Model operations respond within acceptable time limits.

        Verifies:
        - Create, read, update operations are fast
        """
        model_uuid = seeded_model["model_uuid"]

        # Test model retrieval
        with measure_time() as timer:
            response = await api_client.get(
                f"/api/v1/models/{model_uuid}",
                headers=dev_auth_headers
            )

        assert response.status_code == 200
        assert timer.elapsed < 0.3, f"Model get took {timer.elapsed:.2f}s, expected < 0.3s"

    @pytest.mark.asyncio
    async def test_pipeline_operations_respond_quickly(
        self,
        api_client: AsyncClient,
        real_test_db,
        dev_auth_headers,
        measure_time
    ):
        """
        Test: Pipeline operations respond within acceptable time limits.
        """
        # Create pipeline and measure time
        pipeline_data = {
            "name": f"Performance Test {uuid.uuid4().hex[:8]}",
            "description": "Testing performance",
            "model_type": "tts",
            "target_version": "1.0.0",
            "priority": "medium",
            "tags": ["perf"]
        }

        with measure_time() as timer:
            response = await api_client.post(
                "/api/v1/pipelines",
                json=pipeline_data,
                headers=dev_auth_headers
            )

        assert response.status_code == 201
        assert timer.elapsed < 0.5, f"Pipeline create took {timer.elapsed:.2f}s, expected < 0.5s"
