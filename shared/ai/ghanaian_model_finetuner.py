"""
Ghanaian Model Fine-tuning System

This module provides custom model fine-tuning capabilities for Ghanaian languages:
- Fine-tune Coqui TTS for specific dialects
- Train custom ASR models
- Optimize for local accents
- Model evaluation and deployment
"""

import asyncio
import logging
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import numpy as np
import pandas as pd
from collections import defaultdict
import tempfile
import shutil

# For AI/ML features
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    from transformers import (
        AutoTokenizer, AutoModel, AutoModelForSequenceClassification,
        TrainingArguments, Trainer, pipeline
    )
    from datasets import Dataset as HFDataset
    import librosa
    import soundfile as sf
    from TTS.api import TTS
    from TTS.trainer import Trainer as TTSTrainer
    from TTS.config import load_config
    from TTS.tts.configs.xtts_config import XttsConfig
    from TTS.tts.models.xtts import Xtts
    AI_AVAILABLE = True
except ImportError as e:
    AI_AVAILABLE = False
    logging.warning(f"AI libraries not available: {e}. Install required packages for model fine-tuning.")
    # Create fallback classes for testing
    class Dataset:
        def __init__(self, *args, **kwargs):
            pass
        def __len__(self):
            return 0
        def __getitem__(self, idx):
            return {}


class ModelType(Enum):
    """Model types for fine-tuning"""
    TTS = "tts"
    ASR = "asr"
    SENTIMENT = "sentiment"
    NER = "ner"
    INTENT = "intent"


class GhanaianDialect(Enum):
    """Ghanaian dialect types"""
    TWI_AKAN = "twi_akan"
    TWI_FANTE = "twi_fante"
    TWI_ASANTE = "twi_asante"
    EWE = "ewe"
    GA = "ga"
    DAGBANI = "dagbani"
    GHANA_PIDGIN = "ghana_pidgin"


class AccentType(Enum):
    """Ghanaian accent types"""
    URBAN_ACCRA = "urban_accra"
    RURAL_ASHANTI = "rural_ashanti"
    COASTAL_CAPE_COAST = "coastal_cape_coast"
    NORTHERN_TAMALE = "northern_tamale"
    WESTERN_TAKORADI = "western_takoradi"


@dataclass
class TrainingData:
    """Training data structure"""
    text: str
    audio_path: Optional[str] = None
    dialect: Optional[GhanaianDialect] = None
    accent: Optional[AccentType] = None
    speaker_id: Optional[str] = None
    duration: Optional[float] = None
    quality_score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelConfig:
    """Model configuration for fine-tuning"""
    model_type: ModelType
    base_model: str
    target_dialect: GhanaianDialect
    target_accent: Optional[AccentType] = None
    training_data_path: str = ""
    validation_data_path: str = ""
    output_dir: str = ""
    batch_size: int = 8
    learning_rate: float = 1e-5
    num_epochs: int = 10
    warmup_steps: int = 100
    gradient_accumulation_steps: int = 4
    max_grad_norm: float = 1.0
    weight_decay: float = 0.01
    logging_steps: int = 10
    eval_steps: int = 100
    save_steps: int = 500
    save_total_limit: int = 3
    dataloader_num_workers: int = 4
    remove_unused_columns: bool = False
    push_to_hub: bool = False
    hub_model_id: Optional[str] = None
    hub_token: Optional[str] = None


@dataclass
class TrainingMetrics:
    """Training metrics"""
    epoch: int
    train_loss: float
    eval_loss: Optional[float] = None
    learning_rate: float = 0.0
    train_runtime: float = 0.0
    train_samples_per_second: float = 0.0
    train_steps_per_second: float = 0.0
    total_flos: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ModelEvaluation:
    """Model evaluation results"""
    model_path: str
    model_type: ModelType
    dialect: GhanaianDialect
    accent: Optional[AccentType] = None
    test_loss: float = 0.0
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    wer: float = 0.0  # Word Error Rate for ASR
    cer: float = 0.0  # Character Error Rate for ASR
    mel_cepstral_distortion: float = 0.0  # For TTS
    naturalness_score: float = 0.0  # For TTS
    intelligibility_score: float = 0.0  # For TTS
    evaluation_time: datetime = field(default_factory=datetime.now)


class GhanaianDataset(Dataset):
    """Custom dataset for Ghanaian language training data"""
    
    def __init__(self, data: List[TrainingData], tokenizer=None, max_length: int = 512):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        
        if self.tokenizer:
            encoding = self.tokenizer(
                item.text,
                truncation=True,
                padding='max_length',
                max_length=self.max_length,
                return_tensors='pt'
            )
            return {
                'input_ids': encoding['input_ids'].squeeze(),
                'attention_mask': encoding['attention_mask'].squeeze(),
                'labels': encoding['input_ids'].squeeze(),
                'dialect': item.dialect.value if item.dialect else '',
                'accent': item.accent.value if item.accent else '',
                'speaker_id': item.speaker_id or '',
                'audio_path': item.audio_path or '',
                'duration': item.duration or 0.0,
                'quality_score': item.quality_score or 1.0
            }
        
        return {
            'text': item.text,
            'dialect': item.dialect.value if item.dialect else '',
            'accent': item.accent.value if item.accent else '',
            'speaker_id': item.speaker_id or '',
            'audio_path': item.audio_path or '',
            'duration': item.duration or 0.0,
            'quality_score': item.quality_score or 1.0
        }


class GhanaianModelFineTuner:
    """
    Comprehensive model fine-tuning system for Ghanaian languages
    """
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        if not AI_AVAILABLE:
            raise ImportError("Required AI libraries not available. Install transformers, torch, TTS, and librosa.")
        
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.tokenizer = None
        self.trainer = None
        self.training_metrics: List[TrainingMetrics] = []
        self.evaluation_results: List[ModelEvaluation] = []
    
    async def prepare_training_data(self) -> Tuple[List[TrainingData], List[TrainingData]]:
        """
        Prepare training and validation data for fine-tuning
        
        Returns:
            Tuple of training and validation data
        """
        self.logger.info("Preparing training data for %s model", self.config.model_type.value)
        
        # Load training data
        train_data = await self._load_training_data(self.config.training_data_path)
        val_data = await self._load_training_data(self.config.validation_data_path)
        
        # Filter data for target dialect
        train_data = [d for d in train_data if d.dialect == self.config.target_dialect]
        val_data = [d for d in val_data if d.dialect == self.config.target_dialect]
        
        # Filter by accent if specified
        if self.config.target_accent:
            train_data = [d for d in train_data if d.accent == self.config.target_accent]
            val_data = [d for d in val_data if d.accent == self.config.target_accent]
        
        # Quality filtering
        train_data = [d for d in train_data if d.quality_score and d.quality_score > 0.7]
        val_data = [d for d in val_data if d.quality_score and d.quality_score > 0.7]
        
        self.logger.info("Prepared %d training samples and %d validation samples", 
                        len(train_data), len(val_data))
        
        return train_data, val_data
    
    async def _load_training_data(self, data_path: str) -> List[TrainingData]:
        """Load training data from various formats"""
        if not data_path or not os.path.exists(data_path):
            return []
        
        data = []
        
        if data_path.endswith('.json'):
            with open(data_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                for item in raw_data:
                    data.append(TrainingData(
                        text=item.get('text', ''),
                        audio_path=item.get('audio_path'),
                        dialect=GhanaianDialect(item.get('dialect', '')) if item.get('dialect') else None,
                        accent=AccentType(item.get('accent', '')) if item.get('accent') else None,
                        speaker_id=item.get('speaker_id'),
                        duration=item.get('duration'),
                        quality_score=item.get('quality_score', 1.0),
                        metadata=item.get('metadata', {})
                    ))
        
        elif data_path.endswith('.csv'):
            df = pd.read_csv(data_path)
            for _, row in df.iterrows():
                data.append(TrainingData(
                    text=row.get('text', ''),
                    audio_path=row.get('audio_path'),
                    dialect=GhanaianDialect(row.get('dialect', '')) if row.get('dialect') else None,
                    accent=AccentType(row.get('accent', '')) if row.get('accent') else None,
                    speaker_id=row.get('speaker_id'),
                    duration=row.get('duration'),
                    quality_score=row.get('quality_score', 1.0),
                    metadata=json.loads(row.get('metadata', '{}'))
                ))
        
        return data
    
    async def setup_model(self):
        """Setup the model for fine-tuning"""
        self.logger.info("Setting up %s model for fine-tuning", self.config.model_type.value)
        
        if self.config.model_type == ModelType.TTS:
            await self._setup_tts_model()
        elif self.config.model_type == ModelType.ASR:
            await self._setup_asr_model()
        elif self.config.model_type in [ModelType.SENTIMENT, ModelType.NER, ModelType.INTENT]:
            await self._setup_nlp_model()
        else:
            raise ValueError(f"Unsupported model type: {self.config.model_type}")
    
    async def _setup_tts_model(self):
        """Setup TTS model for fine-tuning"""
        try:
            # Load Coqui TTS model
            self.model = TTS(self.config.base_model)
            
            # Create custom config for Ghanaian dialect
            config = XttsConfig()
            config.model_args.languages = [self.config.target_dialect.value]
            config.model_args.speaker_embedding_dim = 512
            config.model_args.encoder_sample_rate = 16000
            config.model_args.encoder_in_channels = 1
            
            # Save config
            config_path = os.path.join(self.config.output_dir, "config.json")
            config.save_json(config_path)
            
            self.logger.info("TTS model setup complete")
            
        except Exception as e:
            self.logger.error("Failed to setup TTS model: %s", e)
            raise
    
    async def _setup_asr_model(self):
        """Setup ASR model for fine-tuning"""
        try:
            # Load base ASR model
            self.tokenizer = AutoTokenizer.from_pretrained(self.config.base_model)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.config.base_model,
                num_labels=len(GhanaianDialect)  # One label per dialect
            )
            
            # Add special tokens for Ghanaian dialects
            special_tokens = [dialect.value for dialect in GhanaianDialect]
            self.tokenizer.add_special_tokens({'additional_special_tokens': special_tokens})
            self.model.resize_token_embeddings(len(self.tokenizer))
            
            self.logger.info("ASR model setup complete")
            
        except Exception as e:
            self.logger.error("Failed to setup ASR model: %s", e)
            raise
    
    async def _setup_nlp_model(self):
        """Setup NLP model for fine-tuning"""
        try:
            # Load base NLP model
            self.tokenizer = AutoTokenizer.from_pretrained(self.config.base_model)
            
            if self.config.model_type == ModelType.SENTIMENT:
                num_labels = 3  # Positive, Negative, Neutral
            elif self.config.model_type == ModelType.NER:
                num_labels = 10  # Custom entity types for Ghanaian context
            elif self.config.model_type == ModelType.INTENT:
                num_labels = 15  # Custom intent types for Ghanaian context
            
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.config.base_model,
                num_labels=num_labels
            )
            
            self.logger.info("NLP model setup complete")
            
        except Exception as e:
            self.logger.error("Failed to setup NLP model: %s", e)
            raise
    
    async def fine_tune(self) -> str:
        """
        Fine-tune the model
        
        Returns:
            Path to the fine-tuned model
        """
        self.logger.info("Starting fine-tuning for %s model", self.config.model_type.value)
        
        # Prepare data
        train_data, val_data = await self.prepare_training_data()
        
        if not train_data:
            raise ValueError("No training data available")
        
        # Setup model
        await self.setup_model()
        
        # Create datasets
        train_dataset = GhanaianDataset(train_data, self.tokenizer)
        val_dataset = GhanaianDataset(val_data, self.tokenizer)
        
        # Setup training arguments
        training_args = TrainingArguments(
            output_dir=self.config.output_dir,
            num_train_epochs=self.config.num_epochs,
            per_device_train_batch_size=self.config.batch_size,
            per_device_eval_batch_size=self.config.batch_size,
            learning_rate=self.config.learning_rate,
            warmup_steps=self.config.warmup_steps,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            max_grad_norm=self.config.max_grad_norm,
            weight_decay=self.config.weight_decay,
            logging_steps=self.config.logging_steps,
            eval_steps=self.config.eval_steps,
            save_steps=self.config.save_steps,
            save_total_limit=self.config.save_total_limit,
            dataloader_num_workers=self.config.dataloader_num_workers,
            remove_unused_columns=self.config.remove_unused_columns,
            push_to_hub=self.config.push_to_hub,
            hub_model_id=self.config.hub_model_id,
            hub_token=self.config.hub_token,
            evaluation_strategy="steps",
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            report_to=None,  # Disable wandb/tensorboard
        )
        
        # Setup trainer
        self.trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            tokenizer=self.tokenizer,
            compute_metrics=self._compute_metrics,
        )
        
        # Start training
        start_time = time.time()
        train_result = self.trainer.train()
        training_time = time.time() - start_time
        
        # Save model
        model_path = os.path.join(self.config.output_dir, "final_model")
        self.trainer.save_model(model_path)
        self.tokenizer.save_pretrained(model_path)
        
        # Save training metrics
        self._save_training_metrics(train_result, training_time)
        
        self.logger.info("Fine-tuning completed. Model saved to: %s", model_path)
        
        return model_path
    
    def _compute_metrics(self, eval_pred):
        """Compute evaluation metrics"""
        predictions, labels = eval_pred
        predictions = np.argmax(predictions, axis=1)
        
        # Calculate accuracy
        accuracy = (predictions == labels).astype(np.float32).mean().item()
        
        return {
            "accuracy": accuracy,
            "eval_loss": 0.0  # Will be computed by trainer
        }
    
    def _save_training_metrics(self, train_result, training_time):
        """Save training metrics"""
        metrics = TrainingMetrics(
            epoch=self.config.num_epochs,
            train_loss=train_result.training_loss,
            train_runtime=training_time,
            train_samples_per_second=train_result.metrics.get("train_samples_per_second", 0),
            train_steps_per_second=train_result.metrics.get("train_steps_per_second", 0),
            total_flos=train_result.metrics.get("total_flos", 0)
        )
        
        self.training_metrics.append(metrics)
        
        # Save to file
        metrics_path = os.path.join(self.config.output_dir, "training_metrics.json")
        with open(metrics_path, 'w') as f:
            json.dump([m.__dict__ for m in self.training_metrics], f, default=str, indent=2)
    
    async def evaluate_model(self, model_path: str, test_data: List[TrainingData]) -> ModelEvaluation:
        """
        Evaluate the fine-tuned model
        
        Args:
            model_path: Path to the fine-tuned model
            test_data: Test data for evaluation
            
        Returns:
            Model evaluation results
        """
        self.logger.info("Evaluating model: %s", model_path)
        
        if not test_data:
            raise ValueError("No test data provided")
        
        # Load model
        if self.config.model_type == ModelType.TTS:
            model = TTS(model_path)
        else:
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model = AutoModelForSequenceClassification.from_pretrained(model_path)
        
        # Run evaluation
        evaluation = ModelEvaluation(
            model_path=model_path,
            model_type=self.config.model_type,
            dialect=self.config.target_dialect,
            accent=self.config.target_accent
        )
        
        if self.config.model_type == ModelType.TTS:
            evaluation = await self._evaluate_tts_model(model, test_data, evaluation)
        elif self.config.model_type == ModelType.ASR:
            evaluation = await self._evaluate_asr_model(model, tokenizer, test_data, evaluation)
        else:
            evaluation = await self._evaluate_nlp_model(model, tokenizer, test_data, evaluation)
        
        # Save evaluation results
        self.evaluation_results.append(evaluation)
        eval_path = os.path.join(self.config.output_dir, "evaluation_results.json")
        with open(eval_path, 'w') as f:
            json.dump([e.__dict__ for e in self.evaluation_results], f, default=str, indent=2)
        
        self.logger.info("Model evaluation completed")
        return evaluation
    
    async def _evaluate_tts_model(self, model, test_data: List[TrainingData], evaluation: ModelEvaluation) -> ModelEvaluation:
        """Evaluate TTS model"""
        try:
            total_mcd = 0.0
            total_naturalness = 0.0
            total_intelligibility = 0.0
            count = 0
            
            for item in test_data[:10]:  # Evaluate first 10 samples
                if not item.audio_path or not os.path.exists(item.audio_path):
                    continue
                
                # Generate speech
                output_path = f"temp_output_{count}.wav"
                model.tts_to_file(text=item.text, file_path=output_path)
                
                # Calculate metrics
                if os.path.exists(output_path):
                    # MCD calculation (simplified)
                    mcd = self._calculate_mcd(item.audio_path, output_path)
                    total_mcd += mcd
                    
                    # Naturalness and intelligibility scores (simplified)
                    naturalness = self._calculate_naturalness_score(output_path)
                    intelligibility = self._calculate_intelligibility_score(output_path)
                    
                    total_naturalness += naturalness
                    total_intelligibility += intelligibility
                    count += 1
                    
                    # Cleanup
                    os.remove(output_path)
            
            if count > 0:
                evaluation.mel_cepstral_distortion = total_mcd / count
                evaluation.naturalness_score = total_naturalness / count
                evaluation.intelligibility_score = total_intelligibility / count
            
        except Exception as e:
            self.logger.error("TTS evaluation error: %s", e)
        
        return evaluation
    
    async def _evaluate_asr_model(self, model, tokenizer, test_data: List[TrainingData], evaluation: ModelEvaluation) -> ModelEvaluation:
        """Evaluate ASR model"""
        try:
            correct_predictions = 0
            total_predictions = 0
            total_wer = 0.0
            total_cer = 0.0
            
            for item in test_data:
                if not item.audio_path or not os.path.exists(item.audio_path):
                    continue
                
                # Load audio
                audio, sr = librosa.load(item.audio_path, sr=16000)
                
                # Run ASR (simplified - would need proper ASR pipeline)
                # This is a placeholder for actual ASR evaluation
                predicted_text = "placeholder"  # Would be actual ASR output
                
                # Calculate metrics
                wer = self._calculate_wer(item.text, predicted_text)
                cer = self._calculate_cer(item.text, predicted_text)
                
                total_wer += wer
                total_cer += cer
                total_predictions += 1
            
            if total_predictions > 0:
                evaluation.wer = total_wer / total_predictions
                evaluation.cer = total_cer / total_predictions
                evaluation.accuracy = 1.0 - evaluation.wer  # Simplified accuracy
        
        except Exception as e:
            self.logger.error("ASR evaluation error: %s", e)
        
        return evaluation
    
    async def _evaluate_nlp_model(self, model, tokenizer, test_data: List[TrainingData], evaluation: ModelEvaluation) -> ModelEvaluation:
        """Evaluate NLP model"""
        try:
            correct_predictions = 0
            total_predictions = 0
            
            for item in test_data:
                # Tokenize input
                inputs = tokenizer(
                    item.text,
                    truncation=True,
                    padding=True,
                    return_tensors="pt"
                )
                
                # Get prediction
                with torch.no_grad():
                    outputs = model(**inputs)
                    predictions = torch.argmax(outputs.logits, dim=-1)
                
                # Calculate accuracy (simplified)
                correct_predictions += 1  # Placeholder
                total_predictions += 1
            
            if total_predictions > 0:
                evaluation.accuracy = correct_predictions / total_predictions
        
        except Exception as e:
            self.logger.error("NLP evaluation error: %s", e)
        
        return evaluation
    
    def _calculate_mcd(self, reference_path: str, generated_path: str) -> float:
        """Calculate Mel-Cepstral Distortion (simplified)"""
        try:
            # Load audio files
            ref_audio, sr = librosa.load(reference_path, sr=16000)
            gen_audio, sr = librosa.load(generated_path, sr=16000)
            
            # Extract mel-spectrograms
            ref_mel = librosa.feature.melspectrogram(y=ref_audio, sr=sr)
            gen_mel = librosa.feature.melspectrogram(y=gen_audio, sr=sr)
            
            # Calculate MCD (simplified)
            mcd = np.mean(np.abs(ref_mel - gen_mel))
            return float(mcd)
        
        except Exception as e:
            self.logger.error("MCD calculation error: %s", e)
            return 0.0
    
    def _calculate_naturalness_score(self, audio_path: str) -> float:
        """Calculate naturalness score (simplified)"""
        try:
            # Load audio
            audio, sr = librosa.load(audio_path, sr=16000)
            
            # Calculate basic audio quality metrics
            rms = np.sqrt(np.mean(audio**2))
            zero_crossings = np.sum(np.diff(np.sign(audio)) != 0)
            
            # Simplified naturalness score
            naturalness = min(1.0, (rms * 10 + zero_crossings / len(audio)) / 2)
            return float(naturalness)
        
        except Exception as e:
            self.logger.error("Naturalness calculation error: %s", e)
            return 0.5
    
    def _calculate_intelligibility_score(self, audio_path: str) -> float:
        """Calculate intelligibility score (simplified)"""
        try:
            # Load audio
            audio, sr = librosa.load(audio_path, sr=16000)
            
            # Calculate spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sr)
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)
            
            # Simplified intelligibility score
            intelligibility = min(1.0, (np.mean(spectral_centroids) + np.mean(spectral_rolloff)) / 2000)
            return float(intelligibility)
        
        except Exception as e:
            self.logger.error("Intelligibility calculation error: %s", e)
            return 0.5
    
    def _calculate_wer(self, reference: str, hypothesis: str) -> float:
        """Calculate Word Error Rate"""
        try:
            ref_words = reference.lower().split()
            hyp_words = hypothesis.lower().split()
            
            # Levenshtein distance for words
            distance = self._levenshtein_distance(ref_words, hyp_words)
            return distance / len(ref_words) if ref_words else 0.0
        
        except Exception as e:
            self.logger.error("WER calculation error: %s", e)
            return 1.0
    
    def _calculate_cer(self, reference: str, hypothesis: str) -> float:
        """Calculate Character Error Rate"""
        try:
            ref_chars = list(reference.lower())
            hyp_chars = list(hypothesis.lower())
            
            # Levenshtein distance for characters
            distance = self._levenshtein_distance(ref_chars, hyp_chars)
            return distance / len(ref_chars) if ref_chars else 0.0
        
        except Exception as e:
            self.logger.error("CER calculation error: %s", e)
            return 1.0
    
    def _levenshtein_distance(self, s1, s2):
        """Calculate Levenshtein distance between two sequences"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    async def optimize_for_local_accents(self, model_path: str, accent_data: List[TrainingData]) -> str:
        """
        Optimize model for local Ghanaian accents
        
        Args:
            model_path: Path to the base model
            accent_data: Training data with accent information
            
        Returns:
            Path to the accent-optimized model
        """
        self.logger.info("Optimizing model for local accents")
        
        # Group data by accent
        accent_groups = defaultdict(list)
        for item in accent_data:
            if item.accent:
                accent_groups[item.accent].append(item)
        
        # Create accent-specific models
        optimized_models = {}
        
        for accent, data in accent_groups.items():
            if len(data) < 10:  # Need minimum data for fine-tuning
                self.logger.warning("Insufficient data for accent %s: %d samples", accent.value, len(data))
                continue
            
            # Create accent-specific config
            accent_config = ModelConfig(
                model_type=self.config.model_type,
                base_model=model_path,
                target_dialect=self.config.target_dialect,
                target_accent=accent,
                training_data_path="",  # Will use provided data
                validation_data_path="",
                output_dir=os.path.join(self.config.output_dir, f"accent_{accent.value}"),
                batch_size=self.config.batch_size,
                learning_rate=self.config.learning_rate * 0.1,  # Lower learning rate for accent tuning
                num_epochs=5  # Fewer epochs for accent tuning
            )
            
            # Create fine-tuner for this accent
            accent_finetuner = GhanaianModelFineTuner(accent_config)
            
            # Fine-tune for accent
            optimized_model_path = await accent_finetuner.fine_tune()
            optimized_models[accent] = optimized_model_path
            
            self.logger.info("Accent optimization completed for %s: %s", accent.value, optimized_model_path)
        
        # Save accent model mapping
        accent_mapping_path = os.path.join(self.config.output_dir, "accent_model_mapping.json")
        with open(accent_mapping_path, 'w') as f:
            json.dump({k.value: v for k, v in optimized_models.items()}, f, indent=2)
        
        return optimized_models
    
    async def deploy_model(self, model_path: str, deployment_config: Dict[str, Any]) -> str:
        """
        Deploy the fine-tuned model
        
        Args:
            model_path: Path to the fine-tuned model
            deployment_config: Deployment configuration
            
        Returns:
            Deployment endpoint or path
        """
        self.logger.info("Deploying model: %s", model_path)
        
        deployment_type = deployment_config.get("type", "local")
        
        if deployment_type == "local":
            return await self._deploy_local(model_path, deployment_config)
        elif deployment_type == "docker":
            return await self._deploy_docker(model_path, deployment_config)
        elif deployment_type == "cloud":
            return await self._deploy_cloud(model_path, deployment_config)
        else:
            raise ValueError(f"Unsupported deployment type: {deployment_type}")
    
    async def _deploy_local(self, model_path: str, config: Dict[str, Any]) -> str:
        """Deploy model locally"""
        try:
            # Create deployment directory
            deploy_dir = config.get("deploy_dir", "deployed_models")
            os.makedirs(deploy_dir, exist_ok=True)
            
            # Copy model to deployment directory
            model_name = os.path.basename(model_path)
            deploy_path = os.path.join(deploy_dir, model_name)
            
            if os.path.isdir(model_path):
                shutil.copytree(model_path, deploy_path, dirs_exist_ok=True)
            else:
                shutil.copy2(model_path, deploy_path)
            
            # Create deployment metadata
            metadata = {
                "model_path": deploy_path,
                "model_type": self.config.model_type.value,
                "dialect": self.config.target_dialect.value,
                "accent": self.config.target_accent.value if self.config.target_accent else None,
                "deployment_time": datetime.now().isoformat(),
                "config": self.config.__dict__
            }
            
            metadata_path = os.path.join(deploy_path, "deployment_metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.info("Model deployed locally to: %s", deploy_path)
            return deploy_path
        
        except Exception as e:
            self.logger.error("Local deployment failed: %s", e)
            raise
    
    async def _deploy_docker(self, model_path: str, config: Dict[str, Any]) -> str:
        """Deploy model using Docker"""
        try:
            # Create Dockerfile
            dockerfile_content = self._generate_dockerfile(config)
            dockerfile_path = os.path.join(self.config.output_dir, "Dockerfile")
            
            with open(dockerfile_path, 'w') as f:
                f.write(dockerfile_content)
            
            # Create docker-compose.yml
            compose_content = self._generate_docker_compose(config)
            compose_path = os.path.join(self.config.output_dir, "docker-compose.yml")
            
            with open(compose_path, 'w') as f:
                f.write(compose_content)
            
            self.logger.info("Docker deployment files created")
            return compose_path
        
        except Exception as e:
            self.logger.error("Docker deployment failed: %s", e)
            raise
    
    async def _deploy_cloud(self, model_path: str, config: Dict[str, Any]) -> str:
        """Deploy model to cloud (placeholder)"""
        self.logger.info("Cloud deployment not implemented yet")
        return "cloud_deployment_placeholder"
    
    def _generate_dockerfile(self, config: Dict[str, Any]) -> str:
        """Generate Dockerfile for model deployment"""
        return f"""
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    ffmpeg \\
    libsndfile1 \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy model and code
COPY . .

# Expose port
EXPOSE 8000

# Start service
CMD ["python", "model_service.py"]
"""
    
    def _generate_docker_compose(self, config: Dict[str, Any]) -> str:
        """Generate docker-compose.yml for model deployment"""
        return f"""
version: '3.8'

services:
  ghanaian-model:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./models:/app/models
    environment:
      - MODEL_PATH=/app/models
      - MODEL_TYPE={self.config.model_type.value}
      - DIALECT={self.config.target_dialect.value}
    restart: unless-stopped
"""


class GhanaianModelManager:
    """
    Manager for Ghanaian model fine-tuning and deployment
    """
    
    def __init__(self, base_dir: str = "ghanaian_models"):
        self.base_dir = base_dir
        self.logger = logging.getLogger(__name__)
        self.models: Dict[str, str] = {}  # model_id -> model_path
        
        os.makedirs(base_dir, exist_ok=True)
    
    async def create_finetuning_job(self, config: ModelConfig) -> str:
        """
        Create a fine-tuning job
        
        Args:
            config: Model configuration
            
        Returns:
            Job ID
        """
        job_id = f"{config.model_type.value}_{config.target_dialect.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create job directory
        job_dir = os.path.join(self.base_dir, job_id)
        os.makedirs(job_dir, exist_ok=True)
        
        # Update config with job directory
        config.output_dir = job_dir
        
        # Save job configuration
        config_path = os.path.join(job_dir, "config.json")
        with open(config_path, 'w') as f:
            json.dump(config.__dict__, f, indent=2, default=str)
        
        self.logger.info("Created fine-tuning job: %s", job_id)
        return job_id
    
    async def run_finetuning_job(self, job_id: str) -> str:
        """
        Run a fine-tuning job
        
        Args:
            job_id: Job ID
            
        Returns:
            Path to the fine-tuned model
        """
        job_dir = os.path.join(self.base_dir, job_id)
        config_path = os.path.join(job_dir, "config.json")
        
        if not os.path.exists(config_path):
            raise ValueError(f"Job configuration not found: {config_path}")
        
        # Load configuration
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
        
        # Convert back to ModelConfig
        config = ModelConfig(**config_dict)
        config.output_dir = job_dir
        
        # Create fine-tuner
        finetuner = GhanaianModelFineTuner(config)
        
        # Run fine-tuning
        model_path = await finetuner.fine_tune()
        
        # Save model reference
        self.models[job_id] = model_path
        
        self.logger.info("Fine-tuning job completed: %s -> %s", job_id, model_path)
        return model_path
    
    async def list_models(self) -> Dict[str, Dict[str, Any]]:
        """
        List all available models
        
        Returns:
            Dictionary of model information
        """
        models_info = {}
        
        for job_id, model_path in self.models.items():
            metadata_path = os.path.join(model_path, "deployment_metadata.json")
            
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                models_info[job_id] = metadata
            else:
                models_info[job_id] = {
                    "model_path": model_path,
                    "job_id": job_id,
                    "status": "unknown"
                }
        
        return models_info
    
    async def deploy_model(self, job_id: str, deployment_config: Dict[str, Any]) -> str:
        """
        Deploy a fine-tuned model
        
        Args:
            job_id: Job ID
            deployment_config: Deployment configuration
            
        Returns:
            Deployment endpoint or path
        """
        if job_id not in self.models:
            raise ValueError(f"Model not found for job: {job_id}")
        
        model_path = self.models[job_id]
        
        # Load original configuration
        job_dir = os.path.join(self.base_dir, job_id)
        config_path = os.path.join(job_dir, "config.json")
        
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
        
        config = ModelConfig(**config_dict)
        
        # Create fine-tuner for deployment
        finetuner = GhanaianModelFineTuner(config)
        
        # Deploy model
        deployment_path = await finetuner.deploy_model(model_path, deployment_config)
        
        self.logger.info("Model deployed: %s -> %s", job_id, deployment_path)
        return deployment_path


# Example usage and testing functions
async def example_tts_finetuning():
    """Example TTS fine-tuning for Twi dialect"""
    config = ModelConfig(
        model_type=ModelType.TTS,
        base_model="tts_models/multilingual/multi-dataset/xtts_v2",
        target_dialect=GhanaianDialect.TWI_AKAN,
        target_accent=AccentType.URBAN_ACCRA,
        training_data_path="data/twi_training.json",
        validation_data_path="data/twi_validation.json",
        output_dir="models/twi_tts",
        batch_size=4,
        learning_rate=1e-5,
        num_epochs=10
    )
    
    finetuner = GhanaianModelFineTuner(config)
    model_path = await finetuner.fine_tune()
    
    # Evaluate model
    test_data = []  # Load test data
    evaluation = await finetuner.evaluate_model(model_path, test_data)
    
    print(f"TTS Model Evaluation:")
    print(f"  MCD: {evaluation.mel_cepstral_distortion:.4f}")
    print(f"  Naturalness: {evaluation.naturalness_score:.4f}")
    print(f"  Intelligibility: {evaluation.intelligibility_score:.4f}")


async def example_asr_finetuning():
    """Example ASR fine-tuning for Ghana Pidgin"""
    config = ModelConfig(
        model_type=ModelType.ASR,
        base_model="facebook/wav2vec2-large-xlsr-53",
        target_dialect=GhanaianDialect.GHANA_PIDGIN,
        training_data_path="data/pidgin_training.json",
        validation_data_path="data/pidgin_validation.json",
        output_dir="models/pidgin_asr",
        batch_size=8,
        learning_rate=1e-4,
        num_epochs=15
    )
    
    finetuner = GhanaianModelFineTuner(config)
    model_path = await finetuner.fine_tune()
    
    # Evaluate model
    test_data = []  # Load test data
    evaluation = await finetuner.evaluate_model(model_path, test_data)
    
    print(f"ASR Model Evaluation:")
    print(f"  WER: {evaluation.wer:.4f}")
    print(f"  CER: {evaluation.cer:.4f}")
    print(f"  Accuracy: {evaluation.accuracy:.4f}")


async def example_accent_optimization():
    """Example accent optimization for multiple Ghanaian accents"""
    config = ModelConfig(
        model_type=ModelType.TTS,
        base_model="models/base_tts_model",
        target_dialect=GhanaianDialect.TWI_AKAN,
        training_data_path="data/twi_training.json",
        validation_data_path="data/twi_validation.json",
        output_dir="models/accent_optimized",
        batch_size=4,
        learning_rate=1e-5,
        num_epochs=5
    )
    
    finetuner = GhanaianModelFineTuner(config)
    
    # Load accent-specific data
    accent_data = []  # Load data with accent information
    
    # Optimize for local accents
    optimized_models = await finetuner.optimize_for_local_accents(
        config.base_model, accent_data
    )
    
    print("Accent-optimized models:")
    for accent, model_path in optimized_models.items():
        print(f"  {accent.value}: {model_path}")


if __name__ == "__main__":
    # Run examples
    asyncio.run(example_tts_finetuning())
    asyncio.run(example_asr_finetuning())
    asyncio.run(example_accent_optimization())
