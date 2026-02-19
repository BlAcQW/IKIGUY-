"""
Tests for Ghanaian Model Fine-tuning System

This module provides comprehensive tests for the Ghanaian model fine-tuning capabilities.
"""

import pytest
import asyncio
import json
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
from typing import List, Dict, Any

# Import the module to test
from apps.shared.ai.ghanaian_model_finetuner import (
    GhanaianModelFineTuner,
    GhanaianModelManager,
    ModelConfig,
    ModelType,
    GhanaianDialect,
    AccentType,
    TrainingData,
    TrainingMetrics,
    ModelEvaluation,
    GhanaianDataset
)


class TestModelConfig:
    """Test ModelConfig dataclass"""
    
    def test_model_config_creation(self):
        """Test creating a ModelConfig instance"""
        config = ModelConfig(
            model_type=ModelType.TTS,
            base_model="test_model",
            target_dialect=GhanaianDialect.TWI_AKAN,
            target_accent=AccentType.URBAN_ACCRA,
            training_data_path="data/train.json",
            validation_data_path="data/val.json",
            output_dir="models/test",
            batch_size=8,
            learning_rate=1e-5,
            num_epochs=10
        )
        
        assert config.model_type == ModelType.TTS
        assert config.base_model == "test_model"
        assert config.target_dialect == GhanaianDialect.TWI_AKAN
        assert config.target_accent == AccentType.URBAN_ACCRA
        assert config.training_data_path == "data/train.json"
        assert config.validation_data_path == "data/val.json"
        assert config.output_dir == "models/test"
        assert config.batch_size == 8
        assert config.learning_rate == 1e-5
        assert config.num_epochs == 10
    
    def test_model_config_defaults(self):
        """Test ModelConfig with default values"""
        config = ModelConfig(
            model_type=ModelType.ASR,
            base_model="test_model",
            target_dialect=GhanaianDialect.GHANA_PIDGIN
        )
        
        assert config.model_type == ModelType.ASR
        assert config.base_model == "test_model"
        assert config.target_dialect == GhanaianDialect.GHANA_PIDGIN
        assert config.target_accent is None
        assert config.training_data_path == ""
        assert config.validation_data_path == ""
        assert config.output_dir == ""
        assert config.batch_size == 8
        assert config.learning_rate == 1e-5
        assert config.num_epochs == 10


class TestTrainingData:
    """Test TrainingData dataclass"""
    
    def test_training_data_creation(self):
        """Test creating a TrainingData instance"""
        data = TrainingData(
            text="Test text in Twi",
            audio_path="/path/to/audio.wav",
            dialect=GhanaianDialect.TWI_AKAN,
            accent=AccentType.URBAN_ACCRA,
            speaker_id="speaker_001",
            duration=5.5,
            quality_score=0.9,
            metadata={"source": "test", "region": "accra"}
        )
        
        assert data.text == "Test text in Twi"
        assert data.audio_path == "/path/to/audio.wav"
        assert data.dialect == GhanaianDialect.TWI_AKAN
        assert data.accent == AccentType.URBAN_ACCRA
        assert data.speaker_id == "speaker_001"
        assert data.duration == 5.5
        assert data.quality_score == 0.9
        assert data.metadata == {"source": "test", "region": "accra"}
    
    def test_training_data_defaults(self):
        """Test TrainingData with default values"""
        data = TrainingData(text="Simple text")
        
        assert data.text == "Simple text"
        assert data.audio_path is None
        assert data.dialect is None
        assert data.accent is None
        assert data.speaker_id is None
        assert data.duration is None
        assert data.quality_score is None
        assert data.metadata == {}


class TestGhanaianDataset:
    """Test GhanaianDataset class"""
    
    def test_dataset_creation(self):
        """Test creating a GhanaianDataset instance"""
        data = [
            TrainingData(text="Text 1", dialect=GhanaianDialect.TWI_AKAN),
            TrainingData(text="Text 2", dialect=GhanaianDialect.EWE),
        ]
        
        dataset = GhanaianDataset(data)
        
        assert len(dataset) == 2
        assert dataset.data == data
    
    def test_dataset_with_tokenizer(self):
        """Test dataset with tokenizer"""
        # Mock tokenizer with proper return values
        mock_tokenizer = Mock()
        
        # Create mock tensors with squeeze method
        mock_input_ids = Mock()
        mock_input_ids.squeeze.return_value = [1, 2, 3]
        mock_attention_mask = Mock()
        mock_attention_mask.squeeze.return_value = [1, 1, 1]
        
        mock_encoding = {
            'input_ids': mock_input_ids,
            'attention_mask': mock_attention_mask
        }
        mock_tokenizer.return_value = mock_encoding
        
        data = [
            TrainingData(text="Test text", dialect=GhanaianDialect.TWI_AKAN)
        ]
        
        dataset = GhanaianDataset(data, tokenizer=mock_tokenizer, max_length=512)
        
        # Test __getitem__
        item = dataset[0]
        assert 'input_ids' in item
        assert 'attention_mask' in item
        assert 'labels' in item
        assert item['dialect'] == 'twi_akan'
    
    def test_dataset_without_tokenizer(self):
        """Test dataset without tokenizer"""
        data = [
            TrainingData(
                text="Test text",
                dialect=GhanaianDialect.TWI_AKAN,
                accent=AccentType.URBAN_ACCRA,
                speaker_id="speaker_001",
                audio_path="/path/to/audio.wav",
                duration=5.0,
                quality_score=0.9
            )
        ]
        
        dataset = GhanaianDataset(data)
        
        item = dataset[0]
        assert item['text'] == "Test text"
        assert item['dialect'] == 'twi_akan'
        assert item['accent'] == 'urban_accra'
        assert item['speaker_id'] == 'speaker_001'
        assert item['audio_path'] == '/path/to/audio.wav'
        assert item['duration'] == 5.0
        assert item['quality_score'] == 0.9


class TestGhanaianModelFineTuner:
    """Test GhanaianModelFineTuner class"""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing"""
        return ModelConfig(
            model_type=ModelType.TTS,
            base_model="test_model",
            target_dialect=GhanaianDialect.TWI_AKAN,
            target_accent=AccentType.URBAN_ACCRA,
            training_data_path="data/train.json",
            validation_data_path="data/val.json",
            output_dir="models/test",
            batch_size=4,
            learning_rate=1e-5,
            num_epochs=5
        )
    
    @pytest.fixture
    def mock_training_data(self):
        """Create mock training data"""
        return [
            TrainingData(
                text="Test text 1",
                audio_path="/path/to/audio1.wav",
                dialect=GhanaianDialect.TWI_AKAN,
                accent=AccentType.URBAN_ACCRA,
                speaker_id="speaker_001",
                duration=5.0,
                quality_score=0.9
            ),
            TrainingData(
                text="Test text 2",
                audio_path="/path/to/audio2.wav",
                dialect=GhanaianDialect.TWI_AKAN,
                accent=AccentType.URBAN_ACCRA,
                speaker_id="speaker_002",
                duration=4.5,
                quality_score=0.8
            )
        ]
    
    @patch('shared.ai.ghanaian_model_finetuner.AI_AVAILABLE', True)
    def test_finetuner_initialization(self, mock_config):
        """Test GhanaianModelFineTuner initialization"""
        # Mock torch.device to avoid import issues
        with patch('shared.ai.ghanaian_model_finetuner.torch') as mock_torch:
            mock_torch.device.return_value = 'cpu'
            finetuner = GhanaianModelFineTuner(mock_config)
            
            assert finetuner.config == mock_config
            assert finetuner.model is None
            assert finetuner.tokenizer is None
            assert finetuner.trainer is None
            assert finetuner.training_metrics == []
            assert finetuner.evaluation_results == []
    
    @patch('shared.ai.ghanaian_model_finetuner.AI_AVAILABLE', False)
    def test_finetuner_initialization_no_ai(self, mock_config):
        """Test initialization when AI libraries are not available"""
        with pytest.raises(ImportError, match="Required AI libraries not available"):
            GhanaianModelFineTuner(mock_config)
    
    @patch('shared.ai.ghanaian_model_finetuner.AI_AVAILABLE', True)
    @patch('torch.device')
    async def test_prepare_training_data(self, mock_device, mock_config):
        """Test preparing training data"""
        finetuner = GhanaianModelFineTuner(mock_config)
        
        # Mock file operations
        mock_train_data = [
            TrainingData(
                text="Train text",
                dialect=GhanaianDialect.TWI_AKAN,
                accent=AccentType.URBAN_ACCRA,
                quality_score=0.9
            )
        ]
        mock_val_data = [
            TrainingData(
                text="Val text",
                dialect=GhanaianDialect.TWI_AKAN,
                accent=AccentType.URBAN_ACCRA,
                quality_score=0.8
            )
        ]
        
        with patch.object(finetuner, '_load_training_data', new_callable=AsyncMock) as mock_load:
            mock_load.side_effect = [mock_train_data, mock_val_data]
            
            train_data, val_data = await finetuner.prepare_training_data()
            
            assert len(train_data) == 1
            assert len(val_data) == 1
            assert train_data[0].dialect == GhanaianDialect.TWI_AKAN
            assert val_data[0].dialect == GhanaianDialect.TWI_AKAN
    
    @patch('shared.ai.ghanaian_model_finetuner.AI_AVAILABLE', True)
    @patch('torch.device')
    async def test_load_training_data_json(self, mock_device, mock_config):
        """Test loading training data from JSON"""
        finetuner = GhanaianModelFineTuner(mock_config)
        
        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([
                {
                    "text": "Test text",
                    "audio_path": "/path/to/audio.wav",
                    "dialect": "twi_akan",
                    "accent": "urban_accra",
                    "speaker_id": "speaker_001",
                    "duration": 5.0,
                    "quality_score": 0.9,
                    "metadata": {"source": "test"}
                }
            ], f)
            temp_file = f.name
        
        try:
            data = await finetuner._load_training_data(temp_file)
            
            assert len(data) == 1
            assert data[0].text == "Test text"
            assert data[0].audio_path == "/path/to/audio.wav"
            assert data[0].dialect == GhanaianDialect.TWI_AKAN
            assert data[0].accent == AccentType.URBAN_ACCRA
            assert data[0].speaker_id == "speaker_001"
            assert data[0].duration == 5.0
            assert data[0].quality_score == 0.9
            assert data[0].metadata == {"source": "test"}
        
        finally:
            os.unlink(temp_file)
    
    @patch('shared.ai.ghanaian_model_finetuner.AI_AVAILABLE', True)
    @patch('torch.device')
    async def test_load_training_data_csv(self, mock_device, mock_config):
        """Test loading training data from CSV"""
        finetuner = GhanaianModelFineTuner(mock_config)
        
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("text,audio_path,dialect,accent,speaker_id,duration,quality_score,metadata\n")
            f.write('"Test text","/path/to/audio.wav","twi_akan","urban_accra","speaker_001",5.0,0.9,"{\\"source\\":\\"test\\"}"\n')
            temp_file = f.name
        
        try:
            with patch('pandas.read_csv'):
                data = await finetuner._load_training_data(temp_file)
                # This would test the CSV loading logic if pandas was available
        
        finally:
            os.unlink(temp_file)
    
    @patch('shared.ai.ghanaian_model_finetuner.AI_AVAILABLE', True)
    @patch('torch.device')
    async def test_load_training_data_nonexistent(self, mock_device, mock_config):
        """Test loading training data from nonexistent file"""
        finetuner = GhanaianModelFineTuner(mock_config)
        
        data = await finetuner._load_training_data("nonexistent_file.json")
        assert data == []
    
    @patch('shared.ai.ghanaian_model_finetuner.AI_AVAILABLE', True)
    @patch('torch.device')
    async def test_setup_tts_model(self, mock_device, mock_config):
        """Test setting up TTS model"""
        finetuner = GhanaianModelFineTuner(mock_config)
        
        with patch('shared.ai.ghanaian_model_finetuner.TTS') as mock_tts, \
             patch('shared.ai.ghanaian_model_finetuner.XttsConfig') as mock_config_class, \
             patch('os.path.join'), \
             patch('os.makedirs'):
            
            mock_config_instance = Mock()
            mock_config_class.return_value = mock_config_instance
            
            await finetuner._setup_tts_model()
            
            mock_tts.assert_called_once_with(mock_config.base_model)
            mock_config_class.assert_called_once()
    
    @patch('shared.ai.ghanaian_model_finetuner.AI_AVAILABLE', True)
    @patch('torch.device')
    async def test_setup_asr_model(self, mock_device, mock_config):
        """Test setting up ASR model"""
        finetuner = GhanaianModelFineTuner(mock_config)
        finetuner.config.model_type = ModelType.ASR
        
        with patch('shared.ai.ghanaian_model_finetuner.AutoTokenizer') as mock_tokenizer, \
             patch('shared.ai.ghanaian_model_finetuner.AutoModelForSequenceClassification') as mock_model:
            
            mock_tokenizer_instance = Mock()
            mock_model_instance = Mock()
            mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
            mock_model.from_pretrained.return_value = mock_model_instance
            
            await finetuner._setup_asr_model()
            
            mock_tokenizer.from_pretrained.assert_called_once_with(mock_config.base_model)
            mock_model.from_pretrained.assert_called_once()
    
    @patch('shared.ai.ghanaian_model_finetuner.AI_AVAILABLE', True)
    @patch('torch.device')
    async def test_setup_nlp_model(self, mock_device, mock_config):
        """Test setting up NLP model"""
        finetuner = GhanaianModelFineTuner(mock_config)
        finetuner.config.model_type = ModelType.SENTIMENT
        
        with patch('shared.ai.ghanaian_model_finetuner.AutoTokenizer') as mock_tokenizer, \
             patch('shared.ai.ghanaian_model_finetuner.AutoModelForSequenceClassification') as mock_model:
            
            mock_tokenizer_instance = Mock()
            mock_model_instance = Mock()
            mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
            mock_model.from_pretrained.return_value = mock_model_instance
            
            await finetuner._setup_nlp_model()
            
            mock_tokenizer.from_pretrained.assert_called_once_with(mock_config.base_model)
            mock_model.from_pretrained.assert_called_once()
    
    @patch('shared.ai.ghanaian_model_finetuner.AI_AVAILABLE', True)
    @patch('torch.device')
    async def test_fine_tune_success(self, mock_device, mock_config, mock_training_data):
        """Test successful fine-tuning"""
        finetuner = GhanaianModelFineTuner(mock_config)
        
        with patch.object(finetuner, 'prepare_training_data', new_callable=AsyncMock) as mock_prepare, \
             patch.object(finetuner, 'setup_model', new_callable=AsyncMock) as mock_setup, \
             patch('shared.ai.ghanaian_model_finetuner.GhanaianDataset') as mock_dataset, \
             patch('shared.ai.ghanaian_model_finetuner.TrainingArguments') as mock_args, \
             patch('shared.ai.ghanaian_model_finetuner.Trainer') as mock_trainer, \
             patch('os.path.join'), \
             patch('os.makedirs'):
            
            mock_prepare.return_value = (mock_training_data, mock_training_data)
            mock_dataset_instance = Mock()
            mock_dataset.return_value = mock_dataset_instance
            
            mock_trainer_instance = Mock()
            mock_trainer.return_value = mock_trainer_instance
            mock_trainer_instance.train.return_value = Mock(training_loss=0.1, metrics={})
            
            result = await finetuner.fine_tune()
            
            mock_prepare.assert_called_once()
            mock_setup.assert_called_once()
            mock_trainer_instance.train.assert_called_once()
            assert result is not None
    
    @patch('shared.ai.ghanaian_model_finetuner.AI_AVAILABLE', True)
    @patch('torch.device')
    async def test_fine_tune_no_data(self, mock_device, mock_config):
        """Test fine-tuning with no training data"""
        finetuner = GhanaianModelFineTuner(mock_config)
        
        with patch.object(finetuner, 'prepare_training_data', new_callable=AsyncMock) as mock_prepare:
            mock_prepare.return_value = ([], [])
            
            with pytest.raises(ValueError, match="No training data available"):
                await finetuner.fine_tune()
    
    @patch('shared.ai.ghanaian_model_finetuner.AI_AVAILABLE', True)
    @patch('torch.device')
    async def test_evaluate_model_tts(self, mock_device, mock_config, mock_training_data):
        """Test TTS model evaluation"""
        finetuner = GhanaianModelFineTuner(mock_config)
        
        with patch('shared.ai.ghanaian_model_finetuner.TTS') as mock_tts, \
             patch('os.path.exists', return_value=True), \
             patch('os.remove'), \
             patch.object(finetuner, '_calculate_mcd', return_value=0.5), \
             patch.object(finetuner, '_calculate_naturalness_score', return_value=0.8), \
             patch.object(finetuner, '_calculate_intelligibility_score', return_value=0.9):
            
            mock_tts_instance = Mock()
            mock_tts.return_value = mock_tts_instance
            
            evaluation = await finetuner.evaluate_model("model_path", mock_training_data)
            
            assert evaluation.model_path == "model_path"
            assert evaluation.model_type == ModelType.TTS
            assert evaluation.dialect == GhanaianDialect.TWI_AKAN
            assert evaluation.mel_cepstral_distortion == 0.5
            assert evaluation.naturalness_score == 0.8
            assert evaluation.intelligibility_score == 0.9
    
    @patch('shared.ai.ghanaian_model_finetuner.AI_AVAILABLE', True)
    @patch('torch.device')
    async def test_evaluate_model_asr(self, mock_device, mock_config, mock_training_data):
        """Test ASR model evaluation"""
        finetuner = GhanaianModelFineTuner(mock_config)
        finetuner.config.model_type = ModelType.ASR
        
        with patch('shared.ai.ghanaian_model_finetuner.AutoTokenizer') as mock_tokenizer, \
             patch('shared.ai.ghanaian_model_finetuner.AutoModelForSequenceClassification') as mock_model, \
             patch('shared.ai.ghanaian_model_finetuner.librosa.load'), \
             patch('os.path.exists', return_value=True), \
             patch.object(finetuner, '_calculate_wer', return_value=0.2), \
             patch.object(finetuner, '_calculate_cer', return_value=0.1):
            
            mock_tokenizer_instance = Mock()
            mock_model_instance = Mock()
            mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
            mock_model.from_pretrained.return_value = mock_model_instance
            
            evaluation = await finetuner.evaluate_model("model_path", mock_training_data)
            
            assert evaluation.model_path == "model_path"
            assert evaluation.model_type == ModelType.ASR
            assert evaluation.wer == 0.2
            assert evaluation.cer == 0.1
            assert evaluation.accuracy == 0.8  # 1.0 - 0.2
    
    @patch('shared.ai.ghanaian_model_finetuner.AI_AVAILABLE', True)
    @patch('torch.device')
    def test_calculate_wer(self, mock_device, mock_config):
        """Test Word Error Rate calculation"""
        finetuner = GhanaianModelFineTuner(mock_config)
        
        # Test exact match
        wer = finetuner._calculate_wer("hello world", "hello world")
        assert wer == 0.0
        
        # Test substitution
        wer = finetuner._calculate_wer("hello world", "hello word")
        assert wer == 0.5  # 1 substitution out of 2 words
        
        # Test insertion
        wer = finetuner._calculate_wer("hello world", "hello big world")
        assert wer == 0.5  # 1 insertion out of 2 words
        
        # Test deletion
        wer = finetuner._calculate_wer("hello world", "hello")
        assert wer == 0.5  # 1 deletion out of 2 words
    
    @patch('shared.ai.ghanaian_model_finetuner.AI_AVAILABLE', True)
    @patch('torch.device')
    def test_calculate_cer(self, mock_device, mock_config):
        """Test Character Error Rate calculation"""
        finetuner = GhanaianModelFineTuner(mock_config)
        
        # Test exact match
        cer = finetuner._calculate_cer("hello", "hello")
        assert cer == 0.0
        
        # Test substitution
        cer = finetuner._calculate_cer("hello", "helpo")
        assert cer == 0.2  # 1 substitution out of 5 characters
        
        # Test insertion
        cer = finetuner._calculate_cer("hello", "helloo")
        assert cer == 0.2  # 1 insertion out of 5 characters
        
        # Test deletion
        cer = finetuner._calculate_cer("hello", "hell")
        assert cer == 0.2  # 1 deletion out of 5 characters
    
    @patch('shared.ai.ghanaian_model_finetuner.AI_AVAILABLE', True)
    @patch('torch.device')
    def test_levenshtein_distance(self, mock_device, mock_config):
        """Test Levenshtein distance calculation"""
        finetuner = GhanaianModelFineTuner(mock_config)
        
        # Test empty strings
        distance = finetuner._levenshtein_distance([], [])
        assert distance == 0
        
        # Test identical sequences
        distance = finetuner._levenshtein_distance(['a', 'b', 'c'], ['a', 'b', 'c'])
        assert distance == 0
        
        # Test substitution
        distance = finetuner._levenshtein_distance(['a', 'b', 'c'], ['a', 'b', 'd'])
        assert distance == 1
        
        # Test insertion
        distance = finetuner._levenshtein_distance(['a', 'b'], ['a', 'b', 'c'])
        assert distance == 1
        
        # Test deletion
        distance = finetuner._levenshtein_distance(['a', 'b', 'c'], ['a', 'b'])
        assert distance == 1
    
    @patch('shared.ai.ghanaian_model_finetuner.AI_AVAILABLE', True)
    @patch('torch.device')
    async def test_optimize_for_local_accents(self, mock_device, mock_config):
        """Test accent optimization"""
        finetuner = GhanaianModelFineTuner(mock_config)
        
        # Create accent-specific data
        accent_data = [
            TrainingData(
                text="Text 1",
                dialect=GhanaianDialect.TWI_AKAN,
                accent=AccentType.URBAN_ACCRA,
                quality_score=0.9
            ),
            TrainingData(
                text="Text 2",
                dialect=GhanaianDialect.TWI_AKAN,
                accent=AccentType.RURAL_ASHANTI,
                quality_score=0.8
            ),
            TrainingData(
                text="Text 3",
                dialect=GhanaianDialect.TWI_AKAN,
                accent=AccentType.URBAN_ACCRA,
                quality_score=0.9
            )
        ]
        
        with patch.object(finetuner, 'fine_tune', new_callable=AsyncMock) as mock_finetune, \
             patch('os.path.join'), \
             patch('os.makedirs'), \
             patch('json.dump'):
            
            mock_finetune.return_value = "optimized_model_path"
            
            result = await finetuner.optimize_for_local_accents("base_model_path", accent_data)
            
            # Should create models for both accents
            assert len(result) == 2
            assert AccentType.URBAN_ACCRA in result
            assert AccentType.RURAL_ASHANTI in result
            assert result[AccentType.URBAN_ACCRA] == "optimized_model_path"
            assert result[AccentType.RURAL_ASHANTI] == "optimized_model_path"
    
    @patch('shared.ai.ghanaian_model_finetuner.AI_AVAILABLE', True)
    @patch('torch.device')
    async def test_deploy_model_local(self, mock_device, mock_config):
        """Test local model deployment"""
        finetuner = GhanaianModelFineTuner(mock_config)
        
        deployment_config = {
            "type": "local",
            "deploy_dir": "deployed_models"
        }
        
        with patch('os.makedirs'), \
             patch('os.path.isdir', return_value=True), \
             patch('shutil.copytree'), \
             patch('json.dump'):
            
            result = await finetuner.deploy_model("model_path", deployment_config)
            
            assert result is not None
    
    @patch('shared.ai.ghanaian_model_finetuner.AI_AVAILABLE', True)
    @patch('torch.device')
    async def test_deploy_model_docker(self, mock_device, mock_config):
        """Test Docker model deployment"""
        finetuner = GhanaianModelFineTuner(mock_config)
        
        deployment_config = {
            "type": "docker"
        }
        
        with patch('builtins.open', create=True), \
             patch('os.path.join'):
            
            result = await finetuner.deploy_model("model_path", deployment_config)
            
            assert result is not None
    
    @patch('shared.ai.ghanaian_model_finetuner.AI_AVAILABLE', True)
    @patch('torch.device')
    async def test_deploy_model_unsupported(self, mock_device, mock_config):
        """Test deployment with unsupported type"""
        finetuner = GhanaianModelFineTuner(mock_config)
        
        deployment_config = {
            "type": "unsupported"
        }
        
        with pytest.raises(ValueError, match="Unsupported deployment type"):
            await finetuner.deploy_model("model_path", deployment_config)


class TestGhanaianModelManager:
    """Test GhanaianModelManager class"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_manager_initialization(self, temp_dir):
        """Test GhanaianModelManager initialization"""
        manager = GhanaianModelManager(temp_dir)
        
        assert manager.base_dir == temp_dir
        assert manager.models == {}
        assert os.path.exists(temp_dir)
    
    async def test_create_finetuning_job(self, temp_dir):
        """Test creating a fine-tuning job"""
        manager = GhanaianModelManager(temp_dir)
        
        config = ModelConfig(
            model_type=ModelType.TTS,
            base_model="test_model",
            target_dialect=GhanaianDialect.TWI_AKAN,
            training_data_path="data/train.json",
            validation_data_path="data/val.json"
        )
        
        job_id = await manager.create_finetuning_job(config)
        
        assert job_id is not None
        assert job_id.startswith("tts_twi_akan_")
        
        # Check that job directory was created
        job_dir = os.path.join(temp_dir, job_id)
        assert os.path.exists(job_dir)
        
        # Check that config was saved
        config_path = os.path.join(job_dir, "config.json")
        assert os.path.exists(config_path)
    
    async def test_run_finetuning_job(self, temp_dir):
        """Test running a fine-tuning job"""
        manager = GhanaianModelManager(temp_dir)
        
        # Create a job first
        config = ModelConfig(
            model_type=ModelType.TTS,
            base_model="test_model",
            target_dialect=GhanaianDialect.TWI_AKAN,
            training_data_path="data/train.json",
            validation_data_path="data/val.json"
        )
        
        job_id = await manager.create_finetuning_job(config)
        
        # Mock the fine-tuning process
        with patch.object(GhanaianModelFineTuner, 'fine_tune', new_callable=AsyncMock) as mock_finetune:
            mock_finetune.return_value = "model_path"
            
            model_path = await manager.run_finetuning_job(job_id)
            
            assert model_path == "model_path"
            assert manager.models[job_id] == "model_path"
    
    async def test_run_finetuning_job_not_found(self, temp_dir):
        """Test running a non-existent fine-tuning job"""
        manager = GhanaianModelManager(temp_dir)
        
        with pytest.raises(ValueError, match="Job configuration not found"):
            await manager.run_finetuning_job("nonexistent_job")
    
    async def test_list_models(self, temp_dir):
        """Test listing models"""
        manager = GhanaianModelManager(temp_dir)
        
        # Add some mock models
        manager.models = {
            "job_1": "model_path_1",
            "job_2": "model_path_2"
        }
        
        # Mock metadata files
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', create=True), \
             patch('json.load', return_value={"model_path": "test_path"}):
            
            models_info = await manager.list_models()
            
            assert len(models_info) == 2
            assert "job_1" in models_info
            assert "job_2" in models_info
    
    async def test_deploy_model(self, temp_dir):
        """Test deploying a model"""
        manager = GhanaianModelManager(temp_dir)
        
        # Add a mock model
        manager.models["job_1"] = "model_path_1"
        
        deployment_config = {"type": "local"}
        
        with patch.object(GhanaianModelFineTuner, 'deploy_model', new_callable=AsyncMock) as mock_deploy, \
             patch('builtins.open', create=True), \
             patch('json.load', return_value={}):
            
            mock_deploy.return_value = "deployment_path"
            
            result = await manager.deploy_model("job_1", deployment_config)
            
            assert result == "deployment_path"
    
    async def test_deploy_model_not_found(self, temp_dir):
        """Test deploying a non-existent model"""
        manager = GhanaianModelManager(temp_dir)
        
        deployment_config = {"type": "local"}
        
        with pytest.raises(ValueError, match="Model not found for job"):
            await manager.deploy_model("nonexistent_job", deployment_config)


class TestIntegration:
    """Integration tests for the fine-tuning system"""
    
    @patch('shared.ai.ghanaian_model_finetuner.AI_AVAILABLE', True)
    @patch('torch.device')
    async def test_end_to_end_tts_finetuning(self, mock_device):
        """Test end-to-end TTS fine-tuning workflow"""
        config = ModelConfig(
            model_type=ModelType.TTS,
            base_model="test_tts_model",
            target_dialect=GhanaianDialect.TWI_AKAN,
            target_accent=AccentType.URBAN_ACCRA,
            training_data_path="data/train.json",
            validation_data_path="data/val.json",
            output_dir="models/test_tts",
            batch_size=4,
            learning_rate=1e-5,
            num_epochs=5
        )
        
        # Create temporary training data
        training_data = [
            TrainingData(
                text="Test text in Twi",
                audio_path="/path/to/audio.wav",
                dialect=GhanaianDialect.TWI_AKAN,
                accent=AccentType.URBAN_ACCRA,
                quality_score=0.9
            )
        ]
        
        with patch.object(GhanaianModelFineTuner, 'prepare_training_data', new_callable=AsyncMock) as mock_prepare, \
             patch.object(GhanaianModelFineTuner, 'setup_model', new_callable=AsyncMock) as mock_setup, \
             patch('shared.ai.ghanaian_model_finetuner.GhanaianDataset') as mock_dataset, \
             patch('shared.ai.ghanaian_model_finetuner.TrainingArguments') as mock_args, \
             patch('shared.ai.ghanaian_model_finetuner.Trainer') as mock_trainer, \
             patch('os.path.join'), \
             patch('os.makedirs'):
            
            mock_prepare.return_value = (training_data, training_data)
            mock_dataset_instance = Mock()
            mock_dataset.return_value = mock_dataset_instance
            
            mock_trainer_instance = Mock()
            mock_trainer.return_value = mock_trainer_instance
            mock_trainer_instance.train.return_value = Mock(training_loss=0.1, metrics={})
            
            finetuner = GhanaianModelFineTuner(config)
            model_path = await finetuner.fine_tune()
            
            assert model_path is not None
            mock_prepare.assert_called_once()
            mock_setup.assert_called_once()
            mock_trainer_instance.train.assert_called_once()
    
    @patch('shared.ai.ghanaian_model_finetuner.AI_AVAILABLE', True)
    @patch('torch.device')
    async def test_end_to_end_asr_finetuning(self, mock_device):
        """Test end-to-end ASR fine-tuning workflow"""
        config = ModelConfig(
            model_type=ModelType.ASR,
            base_model="test_asr_model",
            target_dialect=GhanaianDialect.GHANA_PIDGIN,
            training_data_path="data/train.json",
            validation_data_path="data/val.json",
            output_dir="models/test_asr",
            batch_size=8,
            learning_rate=1e-4,
            num_epochs=10
        )
        
        training_data = [
            TrainingData(
                text="Test text in Pidgin",
                audio_path="/path/to/audio.wav",
                dialect=GhanaianDialect.GHANA_PIDGIN,
                quality_score=0.8
            )
        ]
        
        with patch.object(GhanaianModelFineTuner, 'prepare_training_data', new_callable=AsyncMock) as mock_prepare, \
             patch.object(GhanaianModelFineTuner, 'setup_model', new_callable=AsyncMock) as mock_setup, \
             patch('shared.ai.ghanaian_model_finetuner.GhanaianDataset') as mock_dataset, \
             patch('shared.ai.ghanaian_model_finetuner.TrainingArguments') as mock_args, \
             patch('shared.ai.ghanaian_model_finetuner.Trainer') as mock_trainer, \
             patch('os.path.join'), \
             patch('os.makedirs'):
            
            mock_prepare.return_value = (training_data, training_data)
            mock_dataset_instance = Mock()
            mock_dataset.return_value = mock_dataset_instance
            
            mock_trainer_instance = Mock()
            mock_trainer.return_value = mock_trainer_instance
            mock_trainer_instance.train.return_value = Mock(training_loss=0.2, metrics={})
            
            finetuner = GhanaianModelFineTuner(config)
            model_path = await finetuner.fine_tune()
            
            assert model_path is not None
            mock_prepare.assert_called_once()
            mock_setup.assert_called_once()
            mock_trainer_instance.train.assert_called_once()


# Performance tests
class TestPerformance:
    """Performance tests for the fine-tuning system"""
    
    @patch('shared.ai.ghanaian_model_finetuner.AI_AVAILABLE', True)
    @patch('torch.device')
    async def test_large_dataset_performance(self, mock_device):
        """Test performance with large dataset"""
        config = ModelConfig(
            model_type=ModelType.TTS,
            base_model="test_model",
            target_dialect=GhanaianDialect.TWI_AKAN,
            training_data_path="data/large_train.json",
            validation_data_path="data/large_val.json",
            output_dir="models/large_test",
            batch_size=16,
            learning_rate=1e-5,
            num_epochs=3
        )
        
        # Create large training dataset
        large_training_data = [
            TrainingData(
                text=f"Training text {i}",
                audio_path=f"/path/to/audio_{i}.wav",
                dialect=GhanaianDialect.TWI_AKAN,
                quality_score=0.9
            )
            for i in range(1000)  # 1000 samples
        ]
        
        with patch.object(GhanaianModelFineTuner, 'prepare_training_data', new_callable=AsyncMock) as mock_prepare, \
             patch.object(GhanaianModelFineTuner, 'setup_model', new_callable=AsyncMock) as mock_setup, \
             patch('shared.ai.ghanaian_model_finetuner.GhanaianDataset') as mock_dataset, \
             patch('shared.ai.ghanaian_model_finetuner.TrainingArguments') as mock_args, \
             patch('shared.ai.ghanaian_model_finetuner.Trainer') as mock_trainer, \
             patch('os.path.join'), \
             patch('os.makedirs'):
            
            mock_prepare.return_value = (large_training_data, large_training_data[:100])
            mock_dataset_instance = Mock()
            mock_dataset.return_value = mock_dataset_instance
            
            mock_trainer_instance = Mock()
            mock_trainer.return_value = mock_trainer_instance
            mock_trainer_instance.train.return_value = Mock(training_loss=0.1, metrics={})
            
            finetuner = GhanaianModelFineTuner(config)
            
            # Measure performance
            start_time = asyncio.get_event_loop().time()
            model_path = await finetuner.fine_tune()
            end_time = asyncio.get_event_loop().time()
            
            assert model_path is not None
            assert end_time - start_time < 10.0  # Should complete within 10 seconds for mock


# Error handling tests
class TestErrorHandling:
    """Error handling tests for the fine-tuning system"""
    
    @patch('shared.ai.ghanaian_model_finetuner.AI_AVAILABLE', True)
    @patch('torch.device')
    async def test_setup_model_error(self, mock_device):
        """Test error handling during model setup"""
        config = ModelConfig(
            model_type=ModelType.TTS,
            base_model="invalid_model",
            target_dialect=GhanaianDialect.TWI_AKAN
        )
        
        finetuner = GhanaianModelFineTuner(config)
        
        with patch('shared.ai.ghanaian_model_finetuner.TTS', side_effect=Exception("Model not found")):
            with pytest.raises(Exception, match="Model not found"):
                await finetuner._setup_tts_model()
    
    @patch('shared.ai.ghanaian_model_finetuner.AI_AVAILABLE', True)
    @patch('torch.device')
    async def test_fine_tune_data_error(self, mock_device):
        """Test error handling during data preparation"""
        config = ModelConfig(
            model_type=ModelType.TTS,
            base_model="test_model",
            target_dialect=GhanaianDialect.TWI_AKAN
        )
        
        finetuner = GhanaianModelFineTuner(config)
        
        with patch.object(finetuner, 'prepare_training_data', new_callable=AsyncMock) as mock_prepare:
            mock_prepare.return_value = ([], [])  # No training data
            
            with pytest.raises(ValueError, match="No training data available"):
                await finetuner.fine_tune()
    
    @patch('shared.ai.ghanaian_model_finetuner.AI_AVAILABLE', True)
    @patch('torch.device')
    async def test_evaluation_no_data(self, mock_device):
        """Test error handling during evaluation with no data"""
        config = ModelConfig(
            model_type=ModelType.TTS,
            base_model="test_model",
            target_dialect=GhanaianDialect.TWI_AKAN
        )
        
        finetuner = GhanaianModelFineTuner(config)
        
        with pytest.raises(ValueError, match="No test data provided"):
            await finetuner.evaluate_model("model_path", [])


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
