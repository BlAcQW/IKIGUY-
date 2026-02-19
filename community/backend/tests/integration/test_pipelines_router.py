"""
Integration tests for Training Pipelines Router.

Tests pipeline creation, stage management, metrics tracking,
and artifact management with real MongoDB database connections.

TASK-003: Execute pipelines router integration tests
"""

import pytest
from datetime import datetime
from bson import ObjectId
import uuid

pytestmark = [pytest.mark.integration, pytest.mark.api]


class TestPipelineCreation:
    """Test pipeline creation workflows."""

    async def test_create_pipeline_success(
        self, api_client, dev_auth_headers, real_test_db
    ):
        """
        Test successful pipeline creation.

        Verifies:
        - Pipeline is created with all 5 stages
        - pipeline_uuid is generated
        - Initial stage is set correctly
        - Pipeline is persisted in database
        """
        pipeline_data = {
            "name": "Test TTS Training Pipeline",
            "description": "Integration test pipeline",
            "model_type": "tts",
            "target_version": "1.0.0",
            "priority": "high",
            "current_stage": "data_acquisition",
            "tags": ["test", "tts"],
            "datasets": [],
            "team_members": []
        }

        response = await api_client.post(
            "/api/v1/pipelines",
            json=pipeline_data,
            headers=dev_auth_headers
        )

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()

        # Verify response structure
        assert "pipeline_uuid" in data
        assert data["name"] == pipeline_data["name"]
        assert data["model_type"] == pipeline_data["model_type"]
        assert data["current_stage"] == pipeline_data["current_stage"]
        assert data["is_active"] is True

        # Verify stages are initialized
        assert "stages" in data
        assert len(data["stages"]) == 5
        stage_names = [s["stage_name"] for s in data["stages"]]
        assert "data_acquisition" in stage_names
        assert "preprocessing" in stage_names
        assert "training" in stage_names
        assert "evaluation" in stage_names
        assert "deployment" in stage_names

        # Verify persisted in database
        db_pipeline = await real_test_db.ml_training_pipelines.find_one(
            {"pipeline_uuid": data["pipeline_uuid"]}
        )
        assert db_pipeline is not None
        assert db_pipeline["name"] == pipeline_data["name"]

    async def test_create_pipeline_without_auth_fails(self, api_client):
        """Test that pipeline creation without authentication fails."""
        pipeline_data = {
            "name": "Unauthorized Pipeline",
            "model_type": "tts",
            "target_version": "1.0.0"
        }

        response = await api_client.post("/api/v1/pipelines", json=pipeline_data)

        assert response.status_code == 403

    async def test_create_pipeline_with_datasets(
        self, api_client, dev_auth_headers, real_test_db
    ):
        """Test creating pipeline with dataset references."""
        pipeline_data = {
            "name": "Pipeline with Datasets",
            "model_type": "asr",
            "target_version": "1.0.0",
            "priority": "medium",
            "current_stage": "data_acquisition",
            "datasets": [
                {
                    "dataset_id": str(ObjectId()),
                    "version": "1.0.0",
                    "role": "training",
                    "split_percentage": 80.0
                }
            ],
            "tags": ["asr", "datasets"]
        }

        response = await api_client.post(
            "/api/v1/pipelines",
            json=pipeline_data,
            headers=dev_auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert len(data["datasets"]) == 1
        assert data["datasets"][0]["role"] == "training"


class TestPipelineRetrieval:
    """Test pipeline listing and retrieval workflows."""

    @pytest.fixture
    async def seeded_pipeline(self, real_test_db, test_user_id):
        """Create a test pipeline in the database."""
        pipeline_doc = {
            "_id": ObjectId(),
            "pipeline_uuid": str(uuid.uuid4()),
            "name": "Seeded Test Pipeline",
            "description": "A test pipeline",
            "model_type": "tts",
            "current_stage": "training",
            "stage_progress": 45.0,
            "target_version": "1.0.0",
            "stages": [
                {"stage_name": "data_acquisition", "status": "completed", "progress_percentage": 100,
                 "artifacts": [], "metrics": {}, "logs": [], "checkpoints": []},
                {"stage_name": "preprocessing", "status": "completed", "progress_percentage": 100,
                 "artifacts": [], "metrics": {}, "logs": [], "checkpoints": []},
                {"stage_name": "training", "status": "in_progress", "progress_percentage": 45,
                 "artifacts": [], "metrics": {"loss": 0.25}, "logs": [], "checkpoints": []},
                {"stage_name": "evaluation", "status": "pending", "progress_percentage": 0,
                 "artifacts": [], "metrics": {}, "logs": [], "checkpoints": []},
                {"stage_name": "deployment", "status": "pending", "progress_percentage": 0,
                 "artifacts": [], "metrics": {}, "logs": [], "checkpoints": []}
            ],
            "datasets": [],
            "team_members": [],
            "created_by": test_user_id,
            "is_active": True,
            "priority": "high",
            "tags": ["test"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        await real_test_db.ml_training_pipelines.insert_one(pipeline_doc)
        return pipeline_doc

    async def test_list_pipelines_empty(self, api_client):
        """Test listing pipelines when database is empty."""
        response = await api_client.get("/api/v1/pipelines")

        assert response.status_code == 200
        data = response.json()
        assert "pipelines" in data
        assert data["total"] == 0

    async def test_list_pipelines_with_data(self, api_client, seeded_pipeline):
        """Test listing pipelines returns seeded data."""
        response = await api_client.get("/api/v1/pipelines")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

        # Verify seeded pipeline is in response
        pipeline_uuids = [p["pipeline_uuid"] for p in data["pipelines"]]
        assert seeded_pipeline["pipeline_uuid"] in pipeline_uuids

    async def test_get_pipeline_by_uuid(self, api_client, seeded_pipeline):
        """Test retrieving a specific pipeline by UUID."""
        response = await api_client.get(
            f"/api/v1/pipelines/{seeded_pipeline['pipeline_uuid']}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["pipeline_uuid"] == seeded_pipeline["pipeline_uuid"]
        assert data["name"] == seeded_pipeline["name"]
        assert data["current_stage"] == "training"

    async def test_get_pipeline_not_found(self, api_client):
        """Test retrieving non-existent pipeline returns 404."""
        fake_uuid = str(uuid.uuid4())
        response = await api_client.get(f"/api/v1/pipelines/{fake_uuid}")

        assert response.status_code == 404

    async def test_list_pipelines_filter_by_stage(
        self, api_client, seeded_pipeline, dev_auth_headers
    ):
        """Test filtering pipelines by current stage."""
        response = await api_client.get(
            "/api/v1/pipelines",
            params={"current_stage": "training"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for pipeline in data["pipelines"]:
            assert pipeline["current_stage"] == "training"

    async def test_list_pipelines_filter_by_model_type(
        self, api_client, seeded_pipeline, dev_auth_headers, real_test_db
    ):
        """Test filtering pipelines by model type."""
        # Create ASR pipeline
        asr_pipeline = {
            "name": "ASR Pipeline",
            "model_type": "asr",
            "target_version": "1.0.0",
            "priority": "medium",
            "current_stage": "data_acquisition",
            "datasets": [],
            "tags": []
        }
        await api_client.post("/api/v1/pipelines", json=asr_pipeline, headers=dev_auth_headers)

        # Filter by TTS
        response = await api_client.get(
            "/api/v1/pipelines",
            params={"model_type": "tts"}
        )

        assert response.status_code == 200
        data = response.json()
        for pipeline in data["pipelines"]:
            assert pipeline["model_type"] == "tts"

    async def test_list_pipelines_filter_active(self, api_client, seeded_pipeline):
        """Test filtering active pipelines."""
        response = await api_client.get(
            "/api/v1/pipelines",
            params={"is_active": True}
        )

        assert response.status_code == 200
        data = response.json()
        for pipeline in data["pipelines"]:
            assert pipeline["is_active"] is True


class TestPipelineStageManagement:
    """Test pipeline stage updates and progression."""

    @pytest.fixture
    async def active_pipeline(self, api_client, dev_auth_headers, real_test_db):
        """Create an active pipeline for testing."""
        pipeline_data = {
            "name": "Stage Test Pipeline",
            "model_type": "tts",
            "target_version": "1.0.0",
            "priority": "high",
            "current_stage": "data_acquisition",
            "datasets": [],
            "tags": []
        }
        response = await api_client.post(
            "/api/v1/pipelines",
            json=pipeline_data,
            headers=dev_auth_headers
        )
        return response.json()

    async def test_update_stage_progress(
        self, api_client, active_pipeline, dev_auth_headers, real_test_db
    ):
        """Test updating stage progress."""
        stage_update = {
            "status": "in_progress",
            "metrics": {"samples_processed": 5000}
        }

        response = await api_client.put(
            f"/api/v1/pipelines/{active_pipeline['pipeline_uuid']}/stages/data_acquisition",
            json=stage_update,
            headers=dev_auth_headers
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()

        # Find the data_acquisition stage
        stage = next(s for s in data["stages"] if s["stage_name"] == "data_acquisition")
        assert stage["status"] == "in_progress"
        # Check metrics were updated
        assert stage["metrics"].get("samples_processed") == 5000

    async def test_complete_stage(
        self, api_client, active_pipeline, dev_auth_headers, real_test_db
    ):
        """Test completing a stage and transitioning to next."""
        stage_update = {
            "status": "completed",
            "metrics": {"samples_collected": 10000, "validation_passed": True}
        }

        response = await api_client.put(
            f"/api/v1/pipelines/{active_pipeline['pipeline_uuid']}/stages/data_acquisition",
            json=stage_update,
            headers=dev_auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify stage completed
        stage = next(s for s in data["stages"] if s["stage_name"] == "data_acquisition")
        assert stage["status"] == "completed"

    async def test_update_invalid_stage_fails(
        self, api_client, active_pipeline, dev_auth_headers
    ):
        """Test updating non-existent stage fails."""
        stage_update = {"status": "completed"}

        response = await api_client.put(
            f"/api/v1/pipelines/{active_pipeline['pipeline_uuid']}/stages/invalid_stage",
            json=stage_update,
            headers=dev_auth_headers
        )

        assert response.status_code == 404


class TestPipelineArtifacts:
    """Test pipeline artifact management."""

    @pytest.fixture
    async def active_pipeline(self, api_client, dev_auth_headers):
        """Create an active pipeline for testing."""
        pipeline_data = {
            "name": "Artifact Test Pipeline",
            "model_type": "tts",
            "target_version": "1.0.0",
            "priority": "high",
            "current_stage": "training",
            "datasets": [],
            "tags": []
        }
        response = await api_client.post(
            "/api/v1/pipelines",
            json=pipeline_data,
            headers=dev_auth_headers
        )
        return response.json()

    async def test_add_artifact_to_stage(
        self, api_client, active_pipeline, dev_auth_headers, real_test_db
    ):
        """Test adding an artifact to a pipeline stage."""
        # Use correct field names: artifact_name and stage_name per PipelineArtifactUpload model
        artifact_data = {
            "artifact_name": "checkpoint_epoch_10.pt",
            "stage_name": "training",
            "artifact_type": "checkpoint",
            "file_path": f"pipelines/{active_pipeline['pipeline_uuid']}/training/checkpoint_epoch_10.pt",
            "description": "Training checkpoint at epoch 10"
        }

        response = await api_client.post(
            f"/api/v1/pipelines/{active_pipeline['pipeline_uuid']}/artifacts",
            json=artifact_data,
            headers=dev_auth_headers
        )

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()

        # Response is {"message": ..., "artifact": ...}
        assert data["message"] == "Artifact added successfully"
        assert "artifact" in data
        artifact = data["artifact"]
        assert artifact["name"] == artifact_data["artifact_name"]
        assert artifact["artifact_type"] == "checkpoint"

        # Verify artifact is persisted in database
        db_pipeline = await real_test_db.ml_training_pipelines.find_one(
            {"pipeline_uuid": active_pipeline["pipeline_uuid"]}
        )
        training_stage = next(s for s in db_pipeline["stages"] if s["stage_name"] == "training")
        assert len(training_stage["artifacts"]) >= 1

    async def test_add_artifact_invalid_stage_fails(
        self, api_client, active_pipeline, dev_auth_headers
    ):
        """Test adding artifact to invalid stage fails.

        Note: The API returns 422 for invalid stage_name enum value since
        PipelineStage is an enum, not a plain string.
        """
        artifact_data = {
            "artifact_name": "test.pt",
            "stage_name": "nonexistent_stage",  # Invalid enum value
            "artifact_type": "checkpoint",
            "file_path": "/some/path"
        }

        response = await api_client.post(
            f"/api/v1/pipelines/{active_pipeline['pipeline_uuid']}/artifacts",
            json=artifact_data,
            headers=dev_auth_headers
        )

        # Expect 422 (validation error) because stage_name is an enum
        assert response.status_code == 422


class TestPipelineMetrics:
    """Test pipeline metrics tracking."""

    @pytest.fixture
    async def training_pipeline(self, api_client, dev_auth_headers):
        """Create a pipeline in training stage."""
        pipeline_data = {
            "name": "Metrics Test Pipeline",
            "model_type": "tts",
            "target_version": "1.0.0",
            "priority": "high",
            "current_stage": "training",
            "datasets": [],
            "tags": []
        }
        response = await api_client.post(
            "/api/v1/pipelines",
            json=pipeline_data,
            headers=dev_auth_headers
        )
        return response.json()

    async def test_get_pipeline_metrics(self, api_client, training_pipeline, dev_auth_headers):
        """Test retrieving pipeline metrics."""
        # First update stage with metrics
        stage_update = {
            "status": "in_progress",
            "metrics": {"loss": 0.15, "epoch": 10, "learning_rate": 0.001}
        }
        await api_client.put(
            f"/api/v1/pipelines/{training_pipeline['pipeline_uuid']}/stages/training",
            json=stage_update,
            headers=dev_auth_headers
        )

        # Get metrics
        response = await api_client.get(
            f"/api/v1/pipelines/{training_pipeline['pipeline_uuid']}/metrics"
        )

        assert response.status_code == 200
        data = response.json()
        # API returns {"metrics": {...}} where keys are stage names
        assert "metrics" in data
        assert "training" in data["metrics"]


class TestPipelineCompletion:
    """Test pipeline completion workflows."""

    @pytest.fixture
    async def almost_complete_pipeline(self, api_client, dev_auth_headers, real_test_db):
        """Create a pipeline nearly complete."""
        pipeline_data = {
            "name": "Completion Test Pipeline",
            "model_type": "tts",
            "target_version": "1.0.0",
            "priority": "high",
            "current_stage": "deployment",
            "datasets": [],
            "tags": []
        }
        response = await api_client.post(
            "/api/v1/pipelines",
            json=pipeline_data,
            headers=dev_auth_headers
        )
        pipeline = response.json()

        # Complete all stages except deployment
        for stage in ["data_acquisition", "preprocessing", "training", "evaluation"]:
            await api_client.put(
                f"/api/v1/pipelines/{pipeline['pipeline_uuid']}/stages/{stage}",
                json={"status": "completed", "progress_percentage": 100},
                headers=dev_auth_headers
            )

        return pipeline

    async def test_complete_pipeline(
        self, api_client, almost_complete_pipeline, dev_auth_headers, real_test_db
    ):
        """Test completing a pipeline."""
        # Complete deployment stage
        await api_client.put(
            f"/api/v1/pipelines/{almost_complete_pipeline['pipeline_uuid']}/stages/deployment",
            json={"status": "completed", "progress_percentage": 100},
            headers=dev_auth_headers
        )

        completion_data = {
            "result_model_id": str(ObjectId()),
            "final_metrics": {"mos": 4.2, "rtf": 0.3},
            "notes": "Pipeline completed successfully"
        }

        response = await api_client.post(
            f"/api/v1/pipelines/{almost_complete_pipeline['pipeline_uuid']}/complete",
            json=completion_data,
            headers=dev_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
        assert data["completed_at"] is not None


class TestPipelineStats:
    """Test pipeline statistics endpoint."""

    async def test_get_pipeline_stats_empty(self, api_client):
        """Test getting stats when no pipelines exist."""
        response = await api_client.get("/api/v1/pipelines/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_pipelines"] == 0

    async def test_get_pipeline_stats_with_data(
        self, api_client, dev_auth_headers, real_test_db
    ):
        """Test getting stats with pipelines in database."""
        # Create multiple pipelines
        for i, model_type in enumerate(["tts", "asr", "tts"]):
            pipeline_data = {
                "name": f"Stats Pipeline {i}",
                "model_type": model_type,
                "target_version": "1.0.0",
                "priority": "medium",
                "current_stage": "training" if i % 2 == 0 else "evaluation",
                "datasets": [],
                "tags": []
            }
            await api_client.post(
                "/api/v1/pipelines",
                json=pipeline_data,
                headers=dev_auth_headers
            )

        response = await api_client.get("/api/v1/pipelines/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_pipelines"] >= 3
        assert "pipelines_by_stage" in data
        assert "pipelines_by_type" in data
        assert "active_pipelines" in data


class TestPipelineUpdate:
    """Test pipeline metadata updates."""

    @pytest.fixture
    async def test_pipeline(self, api_client, dev_auth_headers):
        """Create a test pipeline."""
        pipeline_data = {
            "name": "Update Test Pipeline",
            "model_type": "tts",
            "target_version": "1.0.0",
            "priority": "medium",
            "current_stage": "data_acquisition",
            "datasets": [],
            "tags": ["original"]
        }
        response = await api_client.post(
            "/api/v1/pipelines",
            json=pipeline_data,
            headers=dev_auth_headers
        )
        return response.json()

    async def test_update_pipeline_metadata(
        self, api_client, test_pipeline, dev_auth_headers, real_test_db
    ):
        """Test updating pipeline metadata."""
        update_data = {
            "name": "Updated Pipeline Name",
            "description": "Updated description",
            "priority": "critical",
            "tags": ["updated", "important"]
        }

        response = await api_client.put(
            f"/api/v1/pipelines/{test_pipeline['pipeline_uuid']}",
            json=update_data,
            headers=dev_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["priority"] == "critical"
        assert "updated" in data["tags"]

    async def test_update_pipeline_not_found(self, api_client, dev_auth_headers):
        """Test updating non-existent pipeline."""
        fake_uuid = str(uuid.uuid4())
        response = await api_client.put(
            f"/api/v1/pipelines/{fake_uuid}",
            json={"name": "Updated"},
            headers=dev_auth_headers
        )

        assert response.status_code == 404


class TestPipelineSearch:
    """Test pipeline search functionality."""

    async def test_search_pipelines_by_name(
        self, api_client, dev_auth_headers, real_test_db
    ):
        """Test searching pipelines by name."""
        # Create pipeline with unique name
        unique_name = f"UniqueSearch_{uuid.uuid4().hex[:8]}"
        pipeline_data = {
            "name": unique_name,
            "model_type": "tts",
            "target_version": "1.0.0",
            "priority": "medium",
            "current_stage": "data_acquisition",
            "datasets": [],
            "tags": []
        }
        await api_client.post(
            "/api/v1/pipelines",
            json=pipeline_data,
            headers=dev_auth_headers
        )

        # Search
        response = await api_client.get(
            "/api/v1/pipelines",
            params={"query": unique_name[:10]}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    async def test_search_pipelines_advanced(
        self, api_client, dev_auth_headers, real_test_db
    ):
        """Test advanced filtering using the list endpoint with filters."""
        # Pipelines don't have a separate /search endpoint, use list with filters
        response = await api_client.get(
            "/api/v1/pipelines",
            params={
                "model_type": "tts",
                "is_active": True,
                "sort_by": "created_at",
                "sort_order": "desc"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "pipelines" in data


class TestPerformance:
    """Test API performance requirements."""

    async def test_list_pipelines_response_time(self, api_client, measure_time):
        """Test that pipeline listing responds within acceptable time."""
        with measure_time() as timer:
            response = await api_client.get("/api/v1/pipelines")

        assert response.status_code == 200
        assert timer.elapsed < 1.0, f"Response took {timer.elapsed:.2f}s, expected < 1s"

    async def test_get_pipeline_response_time(
        self, api_client, dev_auth_headers, measure_time
    ):
        """Test that single pipeline retrieval responds quickly."""
        # Create a pipeline first
        pipeline_data = {
            "name": "Performance Test Pipeline",
            "model_type": "tts",
            "target_version": "1.0.0",
            "priority": "medium",
            "current_stage": "data_acquisition",
            "datasets": [],
            "tags": []
        }
        create_response = await api_client.post(
            "/api/v1/pipelines",
            json=pipeline_data,
            headers=dev_auth_headers
        )
        pipeline_uuid = create_response.json()["pipeline_uuid"]

        with measure_time() as timer:
            response = await api_client.get(f"/api/v1/pipelines/{pipeline_uuid}")

        assert response.status_code == 200
        assert timer.elapsed < 0.5, f"Response took {timer.elapsed:.2f}s, expected < 0.5s"
