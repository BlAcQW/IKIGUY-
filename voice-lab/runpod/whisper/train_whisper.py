"""
Whisper Small Fine-tuning Script for Twi-Fante Dataset
Optimized for RunPod RTX 4090
"""

import os
import torch
import evaluate
from dataclasses import dataclass
from typing import Any, Dict, List, Union
from datasets import load_dataset, DatasetDict, Audio
from transformers import (
    WhisperFeatureExtractor,
    WhisperTokenizer,
    WhisperProcessor,
    WhisperForConditionalGeneration,
    Seq2SeqTrainingArguments,
    Seq2SeqTrainer,
    TrainerCallback
)
import wandb

# Configuration
@dataclass
class TrainingConfig:
    # Model
    model_name: str = "openai/whisper-small"
    language: str = "tw"  # Twi language code
    task: str = "transcribe"

    # Data
    data_dir: str = "/workspace/data/twi_asr"
    cache_dir: str = "/workspace/cache"
    max_duration_seconds: float = 30.0

    # Training
    output_dir: str = "/workspace/checkpoints/whisper_twi"
    num_train_epochs: int = 10
    per_device_train_batch_size: int = 16
    per_device_eval_batch_size: int = 16
    gradient_accumulation_steps: int = 1  # Effective batch_size = 16
    learning_rate: float = 1e-5
    warmup_steps: int = 500
    gradient_checkpointing: bool = True
    fp16: bool = True

    # Evaluation
    eval_steps: int = 500
    save_steps: int = 500
    logging_steps: int = 25
    save_total_limit: int = 3

    # Optimization
    dataloader_num_workers: int = 4
    load_best_model_at_end: bool = True
    metric_for_best_model: str = "wer"
    greater_is_better: bool = False

    # WandB
    report_to: List[str] = None

    def __post_init__(self):
        if self.report_to is None:
            self.report_to = ["tensorboard"]
            if os.getenv("WANDB_API_KEY"):
                self.report_to.append("wandb")


class WhisperDataCollator:
    """Data collator for Whisper training"""

    def __init__(self, processor):
        self.processor = processor

    def __call__(self, features: List[Dict[str, Union[List[int], torch.Tensor]]]) -> Dict[str, torch.Tensor]:
        # Split inputs and labels
        input_features = [{"input_features": feature["input_features"]} for feature in features]
        label_features = [{"input_ids": feature["labels"]} for feature in features]

        # Pad inputs
        batch = self.processor.feature_extractor.pad(input_features, return_tensors="pt")

        # Pad labels
        labels_batch = self.processor.tokenizer.pad(label_features, return_tensors="pt")

        # Replace padding with -100 to ignore in loss
        labels = labels_batch["input_ids"].masked_fill(
            labels_batch.attention_mask.ne(1), -100
        )

        # Remove decoder_input_ids if present
        if (labels[:, 0] == self.processor.tokenizer.bos_token_id).all().cpu().item():
            labels = labels[:, 1:]

        batch["labels"] = labels

        return batch


def prepare_dataset(config: TrainingConfig):
    """Load and prepare Twi-Fante dataset"""

    print("=" * 80)
    print("Loading Twi-Fante Dataset")
    print("=" * 80)

    # Load dataset from local directory or HuggingFace
    if os.path.exists(config.data_dir):
        print(f"Loading from local directory: {config.data_dir}")
        dataset = load_dataset(
            "audiofolder",
            data_dir=config.data_dir,
            cache_dir=config.cache_dir
        )
    else:
        print("Local data not found, loading Mozilla Common Voice Twi...")
        dataset = load_dataset(
            "mozilla-foundation/common_voice_13_0",
            "tw",  # Twi language
            cache_dir=config.cache_dir
        )

    print(f"\nDataset structure:")
    print(dataset)

    # Remove unnecessary columns
    columns_to_remove = [col for col in dataset["train"].column_names
                         if col not in ["audio", "sentence", "text"]]
    if columns_to_remove:
        dataset = dataset.remove_columns(columns_to_remove)

    # Rename text column if needed
    if "sentence" in dataset["train"].column_names:
        dataset = dataset.rename_column("sentence", "text")

    return dataset


def preprocess_dataset(dataset: DatasetDict, config: TrainingConfig, processor: WhisperProcessor):
    """Preprocess audio and text data"""

    print("\n" + "=" * 80)
    print("Preprocessing Dataset")
    print("=" * 80)

    # Resample audio to 16kHz (Whisper's expected sample rate)
    dataset = dataset.cast_column("audio", Audio(sampling_rate=16000))

    def prepare_dataset_batch(batch):
        """Process a batch of audio and text"""
        # Load and extract audio features
        audio = batch["audio"]

        # Compute input features
        batch["input_features"] = processor.feature_extractor(
            audio["array"],
            sampling_rate=audio["sampling_rate"]
        ).input_features[0]

        # Encode text labels
        batch["labels"] = processor.tokenizer(batch["text"]).input_ids

        return batch

    # Process datasets
    print("\nProcessing training data...")
    dataset = dataset.map(
        prepare_dataset_batch,
        remove_columns=dataset.column_names["train"],
        num_proc=4  # Parallel processing
    )

    print(f"\nProcessed dataset:")
    print(dataset)

    return dataset


def compute_metrics(pred, processor, metric):
    """Compute WER metric"""
    pred_ids = pred.predictions
    label_ids = pred.label_ids

    # Replace -100 with pad token
    label_ids[label_ids == -100] = processor.tokenizer.pad_token_id

    # Decode predictions and labels
    pred_str = processor.tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
    label_str = processor.tokenizer.batch_decode(label_ids, skip_special_tokens=True)

    # Compute WER
    wer = 100 * metric.compute(predictions=pred_str, references=label_str)

    return {"wer": wer}


class CostTrackingCallback(TrainerCallback):
    """Track training costs in real-time"""

    def __init__(self, gpu_cost_per_hour=0.34):
        self.gpu_cost_per_hour = gpu_cost_per_hour
        self.start_time = None

    def on_train_begin(self, args, state, control, **kwargs):
        import time
        self.start_time = time.time()
        print(f"\n💰 Training started - GPU cost: ${self.gpu_cost_per_hour}/hour")

    def on_log(self, args, state, control, logs=None, **kwargs):
        import time
        if self.start_time and state.global_step % 100 == 0:
            elapsed_hours = (time.time() - self.start_time) / 3600
            current_cost = elapsed_hours * self.gpu_cost_per_hour

            if logs:
                logs["cost_usd"] = round(current_cost, 2)
                logs["elapsed_hours"] = round(elapsed_hours, 2)


def main():
    """Main training function"""

    # Initialize configuration
    config = TrainingConfig()

    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "Whisper Twi-Fante Fine-tuning" + " " * 28 + "║")
    print("╚" + "═" * 78 + "╝\n")

    # Print configuration
    print("Configuration:")
    print("-" * 80)
    for key, value in config.__dict__.items():
        print(f"  {key:30s}: {value}")
    print()

    # Initialize WandB if configured
    if "wandb" in config.report_to:
        wandb.init(
            project="whisper-twi-fante",
            name=f"whisper-small-twi-{os.getenv('RUNPOD_POD_ID', 'local')}",
            config=config.__dict__
        )

    # Load processor
    print("Loading Whisper processor...")
    feature_extractor = WhisperFeatureExtractor.from_pretrained(config.model_name)
    tokenizer = WhisperTokenizer.from_pretrained(
        config.model_name,
        language=config.language,
        task=config.task
    )
    processor = WhisperProcessor.from_pretrained(
        config.model_name,
        language=config.language,
        task=config.task
    )

    # Load dataset
    dataset = prepare_dataset(config)

    # Preprocess dataset
    dataset = preprocess_dataset(dataset, config, processor)

    # Load model
    print("\nLoading Whisper model...")
    model = WhisperForConditionalGeneration.from_pretrained(
        config.model_name,
        cache_dir=config.cache_dir
    )

    # Enable gradient checkpointing for memory efficiency
    model.config.use_cache = False
    if config.gradient_checkpointing:
        model.gradient_checkpointing_enable()

    # Force language and task tokens
    model.config.forced_decoder_ids = None
    model.config.suppress_tokens = []

    # Set language
    model.generation_config.language = config.language
    model.generation_config.task = config.task

    print(f"\nModel loaded: {config.model_name}")
    print(f"Parameters: {model.num_parameters() / 1e6:.1f}M")
    print(f"Language: {config.language}")
    print(f"Task: {config.task}")

    # Initialize metric
    metric = evaluate.load("wer")

    # Initialize data collator
    data_collator = WhisperDataCollator(processor)

    # Training arguments
    training_args = Seq2SeqTrainingArguments(
        output_dir=config.output_dir,
        per_device_train_batch_size=config.per_device_train_batch_size,
        per_device_eval_batch_size=config.per_device_eval_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        warmup_steps=config.warmup_steps,
        num_train_epochs=config.num_train_epochs,
        gradient_checkpointing=config.gradient_checkpointing,
        fp16=config.fp16,
        evaluation_strategy="steps",
        eval_steps=config.eval_steps,
        save_strategy="steps",
        save_steps=config.save_steps,
        logging_steps=config.logging_steps,
        report_to=config.report_to,
        load_best_model_at_end=config.load_best_model_at_end,
        metric_for_best_model=config.metric_for_best_model,
        greater_is_better=config.greater_is_better,
        save_total_limit=config.save_total_limit,
        dataloader_num_workers=config.dataloader_num_workers,
        push_to_hub=False,
        predict_with_generate=True,
        generation_max_length=225,
        remove_unused_columns=False,
        label_names=["labels"],
    )

    # Initialize trainer
    trainer = Seq2SeqTrainer(
        args=training_args,
        model=model,
        train_dataset=dataset["train"],
        eval_dataset=dataset.get("validation", dataset.get("test")),
        data_collator=data_collator,
        compute_metrics=lambda pred: compute_metrics(pred, processor, metric),
        tokenizer=processor.feature_extractor,
        callbacks=[CostTrackingCallback(gpu_cost_per_hour=0.34)]
    )

    # Calculate training estimates
    num_samples = len(dataset["train"])
    steps_per_epoch = num_samples // (config.per_device_train_batch_size * config.gradient_accumulation_steps)
    total_steps = steps_per_epoch * config.num_train_epochs

    # Estimate ~1 second per step with FP16 on RTX 4090
    estimated_hours = total_steps / 3600
    estimated_cost = estimated_hours * 0.34

    print("\n" + "=" * 80)
    print("Training Estimates")
    print("=" * 80)
    print(f"Training samples: {num_samples:,}")
    print(f"Steps per epoch: {steps_per_epoch}")
    print(f"Total training steps: {total_steps:,}")
    print(f"Estimated time: {estimated_hours:.1f} hours ({estimated_hours/24:.1f} days)")
    print(f"Estimated cost (RTX 4090 @ $0.34/hr): ${estimated_cost:.2f}")
    print()

    # Start training
    print("=" * 80)
    print("Starting Training")
    print("=" * 80)
    print()

    trainer.train()

    # Save final model
    print("\n" + "=" * 80)
    print("Training Complete!")
    print("=" * 80)

    final_model_path = os.path.join(config.output_dir, "final_model")
    trainer.save_model(final_model_path)
    processor.save_pretrained(final_model_path)

    print(f"\nModel saved to: {final_model_path}")

    # Evaluate on test set if available
    if "test" in dataset:
        print("\nEvaluating on test set...")
        test_results = trainer.evaluate(dataset["test"])
        print(f"\nTest Results:")
        print(f"  WER: {test_results['eval_wer']:.2f}%")

    print("\n✅ Training completed successfully!")
    print(f"\n📦 Outputs:")
    print(f"  Checkpoints: {config.output_dir}")
    print(f"  Final model: {final_model_path}")
    print(f"\n🚀 Next steps:")
    print(f"  1. Test inference: python test_inference.py")
    print(f"  2. Deploy to RunPod Serverless")
    print(f"  3. Integrate with your backend API")


if __name__ == "__main__":
    main()
