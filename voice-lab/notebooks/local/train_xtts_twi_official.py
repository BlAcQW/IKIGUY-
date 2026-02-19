import os

from trainer import Trainer, TrainerArgs

from TTS.config.shared_configs import BaseDatasetConfig
from TTS.tts.datasets import load_tts_samples
from TTS.tts.layers.xtts.trainer.gpt_trainer import GPTArgs, GPTTrainer, GPTTrainerConfig, XttsAudioConfig
from TTS.utils.manage import ModelManager

# Logging parameters
RUN_NAME = "GPT_XTTS_v2.0_Twi_FT"
PROJECT_NAME = "XTTS_Twi_trainer"
DASHBOARD_LOGGER = "tensorboard"
LOGGER_URI = None

# Set here the path that the checkpoints will be saved. Default: ./run/training/
OUT_PATH = "/opt/kasaai/apps/voice-lab/models/coqui_xtts_twi_official"

# Training Parameters
OPTIMIZER_WD_ONLY_ON_WEIGHTS = True  # for multi-gpu training please make it False
START_WITH_EVAL = False  # Disabled to avoid evaluation dataset issues
BATCH_SIZE = 2  # set here the batch size (reduced for GPU memory)
GRAD_ACUMM_STEPS = 126  # set here the grad accumulation steps
# Note: we recommend that BATCH_SIZE * GRAD_ACUMM_STEPS need to be at least 252 for more efficient training. You can increase/decrease BATCH_SIZE but then set GRAD_ACUMM_STEPS accordingly.

# Define here the dataset that you want to use for the fine-tuning on.
config_dataset = BaseDatasetConfig(
    formatter="ljspeech",
    dataset_name="twi_dataset",
    path="/opt/kasaai/apps/voice-lab/data/twi-akan-fante/processed/processed_audio/tts_22k",
    meta_file_train="/opt/kasaai/apps/voice-lab/data/twi-akan-fante/processed/model_manifests/coqui_xtts_train_noext.txt",
    # meta_file_val removed - will use auto-split from training data
    language="en",  # Using 'en' as workaround since 'tw' is not supported
)

# Add here the configs of the datasets
DATASETS_CONFIG_LIST = [config_dataset]

# Use existing XTTS v2.0 files that we already have
CHECKPOINTS_PATH = "/home/dev/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2"

# DVAE files
DVAE_CHECKPOINT = os.path.join(CHECKPOINTS_PATH, "dvae.pth")
MEL_NORM_FILE = os.path.join(CHECKPOINTS_PATH, "mel_stats.pth")

# XTTS transfer learning parameters
TOKENIZER_FILE = os.path.join(CHECKPOINTS_PATH, "vocab.json")
XTTS_CHECKPOINT = os.path.join(CHECKPOINTS_PATH, "model.pth")

# Check if files exist
if not os.path.isfile(DVAE_CHECKPOINT):
    print(f"Warning: DVAE checkpoint not found at {DVAE_CHECKPOINT}")
if not os.path.isfile(MEL_NORM_FILE):
    print(f"Warning: Mel norm file not found at {MEL_NORM_FILE}")
if not os.path.isfile(TOKENIZER_FILE):
    print(f"Warning: Tokenizer file not found at {TOKENIZER_FILE}")
if not os.path.isfile(XTTS_CHECKPOINT):
    print(f"Warning: XTTS checkpoint not found at {XTTS_CHECKPOINT}")


# Training sentences generations - use a sample Twi audio file
# We'll pick one from our training set as reference
SPEAKER_REFERENCE = [
    "/opt/kasaai/apps/voice-lab/data/twi-akan-fante/processed/processed_audio/tts_22k/twi_twi_multispeaker_unknown_speaker_twi_multispeaker_train_unknown_speaker_0.wav"
]
LANGUAGE = "en"  # Use 'en' for test sentences as well


def main():
    # init args and config
    model_args = GPTArgs(
        max_conditioning_length=132300,  # 6 secs
        min_conditioning_length=66150,  # 3 secs
        debug_loading_failures=False,
        max_wav_length=255995,  # ~11.6 seconds
        max_text_length=200,
        mel_norm_file=MEL_NORM_FILE,
        dvae_checkpoint=DVAE_CHECKPOINT,
        xtts_checkpoint=XTTS_CHECKPOINT,  # checkpoint path of the model that you want to fine-tune
        tokenizer_file=TOKENIZER_FILE,
        gpt_num_audio_tokens=1026,
        gpt_start_audio_token=1024,
        gpt_stop_audio_token=1025,
        gpt_use_masking_gt_prompt_approach=True,
        gpt_use_perceiver_resampler=True,
    )
    # define audio config
    audio_config = XttsAudioConfig(sample_rate=22050, dvae_sample_rate=22050, output_sample_rate=24000)
    # training parameters config
    config = GPTTrainerConfig(
        output_path=OUT_PATH,
        model_args=model_args,
        run_name=RUN_NAME,
        project_name=PROJECT_NAME,
        run_description="""
            GPT XTTS training
            """,
        dashboard_logger=DASHBOARD_LOGGER,
        logger_uri=LOGGER_URI,
        audio=audio_config,
        batch_size=BATCH_SIZE,
        batch_group_size=48,
        eval_batch_size=BATCH_SIZE,
        num_loader_workers=8,
        eval_split_max_size=256,
        print_step=50,
        plot_step=100,
        log_model_step=1000,
        save_step=10000,
        save_n_checkpoints=1,
        save_checkpoints=True,
        # target_loss="loss",
        print_eval=False,
        # Optimizer values like tortoise, pytorch implementation with modifications to not apply WD to non-weight parameters.
        optimizer="AdamW",
        optimizer_wd_only_on_weights=OPTIMIZER_WD_ONLY_ON_WEIGHTS,
        optimizer_params={"betas": [0.9, 0.96], "eps": 1e-8, "weight_decay": 1e-2},
        lr=5e-06,  # learning rate
        lr_scheduler="MultiStepLR",
        # it was adjusted accordly for the new step scheme
        lr_scheduler_params={"milestones": [50000 * 18, 150000 * 18, 300000 * 18], "gamma": 0.5, "last_epoch": -1},
        test_sentences=[
            {
                "text": "Ɛte sɛn? Me din de Kofi.",
                "speaker_wav": SPEAKER_REFERENCE,
                "language": LANGUAGE,
            },
            {
                "text": "Meda wo ase paa. Akwaaba!",
                "speaker_wav": SPEAKER_REFERENCE,
                "language": LANGUAGE,
            },
        ],
    )

    # init the model from config
    model = GPTTrainer.init_from_config(config)

    # load training samples
    train_samples, eval_samples = load_tts_samples(
        DATASETS_CONFIG_LIST,
        eval_split=True,
        eval_split_max_size=config.eval_split_max_size,
        eval_split_size=config.eval_split_size,
    )

    # init the trainer and 🚀
    trainer = Trainer(
        TrainerArgs(
            restore_path="/opt/kasaai/apps/voice-lab/models/coqui_xtts_twi_official/GPT_XTTS_v2.0_Twi_FT-October-04-2025_04+55AM-d461a94/checkpoint_60000.pth",  # Resume from checkpoint
            skip_train_epoch=False,
            start_with_eval=START_WITH_EVAL,
            grad_accum_steps=GRAD_ACUMM_STEPS,
        ),
        config,
        output_path=OUT_PATH,
        model=model,
        train_samples=train_samples,
        eval_samples=eval_samples,
    )
    trainer.fit()


if __name__ == "__main__":
    main()
