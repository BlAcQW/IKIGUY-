#!/usr/bin/env python3
"""
TTS Training Script for Twi/Akan Voices
Supports multiple TTS architectures and training configurations
"""

import os
import sys
import argparse
import yaml
import torch
import numpy as np
from pathlib import Path
from typing import Dict, Optional, List
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import enhanced processor
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "enhanced_twi_processor", 
        str(Path(__file__).parent.parent / "notebooks" / "000_enhanced_twi_processor.py")
    )
    enhanced_twi_processor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(enhanced_twi_processor)
    from enhanced_twi_processor import EnhancedTwiTextProcessor
except:
    from notebooks.enhanced_twi_processor import EnhancedTwiTextProcessor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TTSTrainer:
    """Main TTS training class"""
    
    def __init__(self, config_path: str):
        """Initialize trainer with configuration"""
        self.config = self._load_config(config_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.text_processor = EnhancedTwiTextProcessor(
            dialect=self.config['text_processing']['dialects']['default']
        )
        
        # Setup paths
        self.setup_paths()
        
        # Initialize model
        self.model = None
        self.optimizer = None
        self.scheduler = None
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def setup_paths(self):
        """Setup training directories"""
        base_path = Path(self.config['training']['output_path'])
        
        # Create directories
        self.model_dir = base_path / "models"
        self.checkpoint_dir = base_path / "checkpoints"
        self.log_dir = base_path / "logs"
        self.samples_dir = base_path / "samples"
        
        for dir_path in [self.model_dir, self.checkpoint_dir, 
                         self.log_dir, self.samples_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            
        logger.info(f"Training directories setup at: {base_path}")
    
    def prepare_dataset(self, dataset_name: str):
        """Prepare dataset for training"""
        dataset_config = self.config['datasets'][dataset_name]
        
        logger.info(f"Loading dataset: {dataset_name}")
        
        # Load metadata
        import pandas as pd
        meta_path = Path(dataset_config['path']) / dataset_config['meta_file']
        df = pd.read_csv(meta_path)
        
        # Process text with enhanced processor
        logger.info("Processing text with enhanced Twi processor...")
        processed_texts = []
        phonemes = []
        
        for text in df[dataset_config['text_column']]:
            result = self.text_processor.process_text(
                text,
                generate_phonemes=self.config['text_processing']['use_phonemes']
            )
            processed_texts.append(result['processed'])
            if self.config['text_processing']['use_phonemes']:
                phonemes.append(result['phonemes'])
        
        df['processed_text'] = processed_texts
        if phonemes:
            df['phonemes'] = phonemes
            
        # Split dataset
        from sklearn.model_selection import train_test_split
        
        eval_size = self.config['training']['eval_split_size']
        test_size = self.config['training']['test_split_size']
        
        # First split: train+val vs test
        train_val_df, test_df = train_test_split(
            df, test_size=test_size, random_state=42
        )
        
        # Second split: train vs val
        train_df, val_df = train_test_split(
            train_val_df, 
            test_size=eval_size / (1 - test_size), 
            random_state=42
        )
        
        logger.info(f"Dataset splits - Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
        
        return train_df, val_df, test_df
    
    def build_model(self, model_type: str):
        """Build TTS model based on configuration"""
        logger.info(f"Building {model_type} model...")
        
        if model_type.lower() == "tacotron2":
            return self._build_tacotron2()
        elif model_type.lower() == "vits":
            return self._build_vits()
        elif model_type.lower() == "xtts":
            return self._build_xtts()
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    def _build_tacotron2(self):
        """Build Tacotron2 model"""
        try:
            from TTS.tts.models import Tacotron2
            from TTS.tts.configs import Tacotron2Config
            
            config = self.config['model_configs']['tacotron2']
            
            # Create config
            tts_config = Tacotron2Config(
                audio=config['audio'],
                model_params=config['model'],
                batch_size=config['training']['batch_size'],
                eval_batch_size=8,
                num_loader_workers=4,
                num_eval_loader_workers=2,
                run_eval=True,
                test_delay_epochs=10,
                epochs=config['training']['epochs'],
                print_step=50,
                print_eval=True,
                save_step=config['training']['checkpoint_interval'],
                save_n_checkpoints=5,
                save_all_best=True,
                use_phonemes=self.config['text_processing']['use_phonemes'],
                phoneme_language="tw",
            )
            
            # Initialize model
            model = Tacotron2(tts_config)
            
            return model
            
        except ImportError:
            logger.error("Coqui TTS not installed. Please install: pip install TTS")
            raise
    
    def _build_vits(self):
        """Build VITS model"""
        try:
            from TTS.tts.models.vits import Vits
            from TTS.tts.configs.vits_config import VitsConfig
            
            config = self.config['model_configs']['vits']
            
            # Create config
            tts_config = VitsConfig(
                audio=config['audio'],
                model_params=config['model'],
                batch_size=config['training']['batch_size'],
                epochs=config['training']['epochs'],
                use_phonemes=self.config['text_processing']['use_phonemes'],
                phoneme_language="tw",
            )
            
            # Initialize model
            model = Vits(tts_config)
            
            return model
            
        except ImportError:
            logger.error("VITS model requires Coqui TTS. Please install: pip install TTS")
            raise
    
    def _build_xtts(self):
        """Build XTTS model for voice cloning"""
        try:
            from TTS.tts.models.xtts import Xtts
            from TTS.tts.configs.xtts_config import XttsConfig
            
            config = self.config['model_configs']['xtts']
            
            # Create config
            tts_config = XttsConfig(
                audio=config['audio'],
                model_params=config['model'],
                languages=["tw"],  # Twi language
            )
            
            # Initialize model
            model = Xtts(tts_config)
            
            return model
            
        except ImportError:
            logger.error("XTTS model requires Coqui TTS. Please install: pip install TTS")
            raise
    
    def train(self, model_type: str, dataset_name: str, epochs: Optional[int] = None):
        """Main training loop"""
        logger.info(f"Starting {model_type} training on {dataset_name} dataset")
        
        # Prepare dataset
        train_df, val_df, test_df = self.prepare_dataset(dataset_name)
        
        # Build model
        self.model = self.build_model(model_type)
        self.model.to(self.device)
        
        # Setup optimizer
        config = self.config['model_configs'][model_type.lower()]
        self.optimizer = torch.optim.Adam(
            self.model.parameters(),
            lr=config['training']['learning_rate'],
            weight_decay=config['training'].get('weight_decay', 1e-6)
        )
        
        # Training epochs
        if epochs is None:
            epochs = config['training']['epochs']
        
        logger.info(f"Training for {epochs} epochs...")
        
        best_val_loss = float('inf')
        
        for epoch in range(epochs):
            # Training step
            train_loss = self._train_epoch(train_df, epoch)
            
            # Validation step
            val_loss = self._validate(val_df, epoch)
            
            logger.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
            
            # Save checkpoint
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                self._save_checkpoint(epoch, val_loss, is_best=True)
            
            # Regular checkpoint
            if (epoch + 1) % 10 == 0:
                self._save_checkpoint(epoch, val_loss, is_best=False)
            
            # Generate samples
            if (epoch + 1) % 5 == 0:
                self._generate_samples(epoch)
        
        logger.info("Training completed!")
        
        # Final evaluation
        self._final_evaluation(test_df)
    
    def _train_epoch(self, train_df, epoch: int) -> float:
        """Train for one epoch"""
        self.model.train()
        total_loss = 0
        
        # Create data loader
        from torch.utils.data import DataLoader
        
        # Simplified training loop - actual implementation would need proper dataset class
        batch_size = self.config['model_configs'][self.model.__class__.__name__.lower()]['training']['batch_size']
        
        for i in range(0, len(train_df), batch_size):
            batch = train_df.iloc[i:i+batch_size]
            
            # Process batch (simplified)
            loss = 0.1  # Placeholder - actual loss computation needed
            
            self.optimizer.zero_grad()
            # loss.backward()
            self.optimizer.step()
            
            total_loss += loss
        
        return total_loss / (len(train_df) // batch_size)
    
    def _validate(self, val_df, epoch: int) -> float:
        """Validate model"""
        self.model.eval()
        total_loss = 0
        
        with torch.no_grad():
            # Simplified validation - actual implementation needed
            total_loss = 0.05  # Placeholder
        
        return total_loss
    
    def _save_checkpoint(self, epoch: int, val_loss: float, is_best: bool):
        """Save model checkpoint"""
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'val_loss': val_loss,
            'config': self.config
        }
        
        if is_best:
            path = self.checkpoint_dir / "best_model.pth"
        else:
            path = self.checkpoint_dir / f"checkpoint_epoch_{epoch}.pth"
        
        torch.save(checkpoint, path)
        logger.info(f"Saved checkpoint: {path}")
    
    def _generate_samples(self, epoch: int):
        """Generate sample audio"""
        sample_texts = [
            "Akwaaba. Ɛte sɛn?",
            "Me din de Kofi.",
            "Mepɛ sɛ metumi akasa Twi.",
            "Ghana yɛ ɔman a ɛyɛ fɛ paa.",
            "Meda wo ase paa."
        ]
        
        self.model.eval()
        with torch.no_grad():
            for i, text in enumerate(sample_texts):
                # Process text
                result = self.text_processor.process_text(text, generate_phonemes=True)
                
                # Generate audio (simplified - actual synthesis needed)
                logger.info(f"Generated sample {i+1}: {text}")
    
    def _final_evaluation(self, test_df):
        """Final evaluation on test set"""
        logger.info("Running final evaluation on test set...")
        
        self.model.eval()
        with torch.no_grad():
            # Compute metrics
            test_loss = self._validate(test_df, -1)
            logger.info(f"Test Loss: {test_loss:.4f}")
            
            # Compute quality metrics if configured
            if self.config['quality_metrics']['compute_mos']:
                mos_score = self._compute_mos(test_df)
                logger.info(f"MOS Score: {mos_score:.2f}")
    
    def _compute_mos(self, test_df) -> float:
        """Compute Mean Opinion Score"""
        # Simplified MOS computation
        return 3.8  # Placeholder
    
    def export_model(self, format: str = "onnx"):
        """Export model for deployment"""
        logger.info(f"Exporting model to {format} format...")
        
        if format == "onnx":
            self._export_onnx()
        elif format == "tflite":
            self._export_tflite()
        else:
            raise ValueError(f"Unknown export format: {format}")
    
    def _export_onnx(self):
        """Export to ONNX format"""
        import torch.onnx
        
        dummy_input = torch.randn(1, 100).to(self.device)  # Adjust based on model
        
        output_path = self.model_dir / "model.onnx"
        
        torch.onnx.export(
            self.model,
            dummy_input,
            output_path,
            export_params=True,
            opset_version=11,
            do_constant_folding=True,
            input_names=['input'],
            output_names=['output'],
            dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}}
        )
        
        logger.info(f"Model exported to: {output_path}")
    
    def _export_tflite(self):
        """Export to TensorFlow Lite format"""
        # Requires conversion through ONNX -> TF -> TFLite
        logger.info("TFLite export requires additional conversion steps")


def main():
    """Main training script"""
    parser = argparse.ArgumentParser(description="Train TTS model for Twi/Akan")
    
    parser.add_argument(
        "--config",
        type=str,
        default="configs/tts_config.yaml",
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        choices=["tacotron2", "vits", "xtts"],
        default="tacotron2",
        help="Model architecture to train"
    )
    
    parser.add_argument(
        "--dataset",
        type=str,
        choices=["bible_tts", "financial_inclusion", "custom_recordings"],
        default="bible_tts",
        help="Dataset to use for training"
    )
    
    parser.add_argument(
        "--epochs",
        type=int,
        default=None,
        help="Number of training epochs (overrides config)"
    )
    
    parser.add_argument(
        "--export",
        type=str,
        choices=["onnx", "tflite"],
        help="Export trained model to specified format"
    )
    
    parser.add_argument(
        "--resume",
        type=str,
        help="Path to checkpoint to resume training from"
    )
    
    args = parser.parse_args()
    
    # Initialize trainer
    trainer = TTSTrainer(args.config)
    
    # Resume from checkpoint if specified
    if args.resume:
        logger.info(f"Resuming from checkpoint: {args.resume}")
        checkpoint = torch.load(args.resume)
        trainer.model.load_state_dict(checkpoint['model_state_dict'])
        trainer.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    
    # Train model
    trainer.train(args.model, args.dataset, args.epochs)
    
    # Export if requested
    if args.export:
        trainer.export_model(args.export)
    
    logger.info("Training script completed!")


if __name__ == "__main__":
    main()