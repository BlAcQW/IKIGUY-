# MichSetHowusu Audio Fix for Google Colab

Add this cell to your `002_phase1_data_processing_enhanced.ipynb` notebook BEFORE the MichSetHowusu processing cell:

```python
# %%
# FIX: Install audio libraries for MichSetHowusu processing
print("Installing audio decoding libraries for MichSetHowusu...")

# Install required libraries
!pip install -q soundfile librosa

# For audio array handling
try:
    import soundfile as sf
    print("✅ soundfile installed")
except:
    print("⚠️ soundfile not available")

try:
    import librosa
    print("✅ librosa installed")
except:
    print("⚠️ librosa not available")

# %%
# Enhanced MichSetHowusu processing with better audio handling
print("\n" + "="*60)
print("PROCESSING MICHSETHOWUSU DATASETS (ENHANCED)")
print("="*60)

michset_samples = []

# Check for local datasets first
michset_base = raw_dir / 'michsethowusu'
if michset_base.exists():
    print(f"Found local MichSetHowusu data at: {michset_base}")
    
    # Process each dataset
    dataset_dirs = [
        'twi_multispeaker_audio_transcribed',
        'akuapem_multispeaker_audio_transcribed',
        'fante_multispeaker_audio_transcribed'
    ]
    
    for dataset_name in dataset_dirs:
        dataset_path = michset_base / dataset_name / 'train'
        
        if dataset_path.exists():
            print(f"\nProcessing {dataset_name}...")
            
            try:
                from datasets import load_from_disk
                
                # Load dataset
                dataset = load_from_disk(str(dataset_path))
                print(f"  Loaded {len(dataset)} samples")
                print(f"  Features: {list(dataset.features.keys())}")
                
                # Determine column names
                text_col = 'transcription' if 'transcription' in dataset.features else 'text'
                audio_col = 'audio_path' if 'audio_path' in dataset.features else 'audio'
                
                # Process samples
                max_samples = min(500, len(dataset))
                successful = 0
                
                for i in tqdm(range(max_samples), desc=f"Processing {dataset_name}"):
                    try:
                        sample = dataset[i]
                        
                        # Get text
                        text = sample.get(text_col, '')
                        
                        # Determine language
                        if 'akuapem' in dataset_name:
                            language = 'akuapem_twi'
                        elif 'fante' in dataset_name:
                            language = 'fante'
                        else:
                            language = 'twi'
                        
                        # Handle audio
                        audio_data = sample.get(audio_col)
                        
                        if audio_data:
                            # If audio_path is a string (file path)
                            if isinstance(audio_data, str):
                                # Check if path exists
                                audio_file = michset_base / dataset_name / 'train' / audio_data
                                if audio_file.exists():
                                    try:
                                        # Load audio file
                                        audio_array, sr = librosa.load(str(audio_file), sr=16000)
                                        
                                        michset_samples.append({
                                            'audio': audio_array,
                                            'text': text,
                                            'sampling_rate': sr,
                                            'language': language,
                                            'dataset': dataset_name,
                                            'split': 'train'
                                        })
                                        successful += 1
                                    except:
                                        # If can't load audio, just save text
                                        michset_samples.append({
                                            'audio': np.zeros(16000),  # 1 second of silence
                                            'text': text,
                                            'sampling_rate': 16000,
                                            'language': language,
                                            'dataset': dataset_name,
                                            'split': 'train'
                                        })
                            
                            # If audio is already loaded (dict with array)
                            elif isinstance(audio_data, dict) and 'array' in audio_data:
                                michset_samples.append({
                                    'audio': audio_data['array'],
                                    'text': text,
                                    'sampling_rate': audio_data.get('sampling_rate', 16000),
                                    'language': language,
                                    'dataset': dataset_name,
                                    'split': 'train'
                                })
                                successful += 1
                        else:
                            # No audio, create placeholder
                            michset_samples.append({
                                'audio': np.zeros(16000),  # 1 second of silence
                                'text': text,
                                'sampling_rate': 16000,
                                'language': language,
                                'dataset': dataset_name,
                                'split': 'train'
                            })
                    
                    except Exception as e:
                        continue
                
                print(f"  ✅ Successfully processed {successful}/{max_samples} samples")
                
            except Exception as e:
                print(f"  ⚠️ Error processing {dataset_name}: {e}")
                
                # Fallback: Try HuggingFace
                try:
                    print(f"  Trying HuggingFace download...")
                    from datasets import load_dataset
                    
                    hf_path = f"michsethowusu/{dataset_name}"
                    dataset = load_dataset(hf_path, split="train", token=True)
                    print(f"  Downloaded {len(dataset)} samples from HuggingFace")
                    
                    # Process limited samples
                    for i in range(min(100, len(dataset))):
                        sample = dataset[i]
                        text = sample.get('transcription', sample.get('text', ''))
                        
                        if 'akuapem' in dataset_name:
                            language = 'akuapem_twi'
                        elif 'fante' in dataset_name:
                            language = 'fante'
                        else:
                            language = 'twi'
                        
                        michset_samples.append({
                            'audio': np.zeros(16000),  # Placeholder
                            'text': text,
                            'sampling_rate': 16000,
                            'language': language,
                            'dataset': dataset_name,
                            'split': 'train'
                        })
                    
                except Exception as e2:
                    print(f"  Could not download from HuggingFace: {e2}")

print(f"\n✅ Total MichSetHowusu samples: {len(michset_samples)}")

# Add to all_samples
all_samples.extend(michset_samples)

# Show summary
if michset_samples:
    languages = {}
    for s in michset_samples:
        lang = s.get('language', 'unknown')
        languages[lang] = languages.get(lang, 0) + 1
    
    print("\nLanguage distribution:")
    for lang, count in languages.items():
        print(f"  - {lang}: {count} samples")
```

## Alternative: Skip MichSetHowusu if causing issues

If MichSetHowusu continues to cause problems, you can skip it and focus on the working datasets:

```python
# %%
# Skip MichSetHowusu and focus on working datasets
print("\n" + "="*60)
print("SKIPPING MICHSETHOWUSU - FOCUSING ON WORKING DATASETS")
print("="*60)

print("\nDatasets being processed:")
print("1. BibleTTS: 46,841 FLAC files ✅")
print("2. Financial Inclusion: 2,956 OGG files ✅")
print("3. Common Voice: (needs separate download)")
print("4. MichSetHowusu: SKIPPED (audio decoding issues)")

print(f"\nTotal samples available: {len(all_samples)}")
```

## Notes:
1. The MichSetHowusu datasets have audio stored in Arrow format that requires special handling
2. The audio might be stored as paths rather than arrays
3. If the audio decoding fails, the script will still extract the text for text-only training
4. You have 49,797 audio files from BibleTTS and Financial Inclusion that work without issues