"""
Load and use MichSetHowusu Arrow format datasets from Google Drive
"""

from datasets import Dataset, load_from_disk
import pyarrow.parquet as pq
import pyarrow as pa
import pandas as pd
from pathlib import Path
import pickle
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

# Method 1: If you have the Arrow files locally
def load_arrow_files_locally():
    """Load Arrow files from local directory."""
    
    # Path to the Arrow files (after downloading from Google Drive)
    arrow_dir = Path("G:/My Drive/voice-lab-data/raw/michsethowusu/fante_multispeaker_audio_transcribed/train")
    
    if not arrow_dir.exists():
        print(f"Directory not found: {arrow_dir}")
        return None
    
    # Load the dataset from Arrow files
    try:
        # Method 1: Load as Hugging Face dataset
        dataset = load_from_disk(str(arrow_dir))
        print(f"Loaded dataset with {len(dataset)} samples")
        print(f"Features: {dataset.features}")
        
        # Convert to pandas for exploration
        df = dataset.to_pandas()
        print(f"\nDataFrame shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
        
        # Show sample data
        print("\nFirst few samples:")
        print(df.head())
        
        return dataset
        
    except Exception as e:
        print(f"Error loading as HF dataset: {e}")
        
        # Method 2: Try loading individual Arrow files
        arrow_files = list(arrow_dir.glob("*.arrow"))
        print(f"\nFound {len(arrow_files)} Arrow files")
        
        dfs = []
        for arrow_file in arrow_files:
            try:
                # Read Arrow file as table
                table = pq.read_table(arrow_file)
                df = table.to_pandas()
                dfs.append(df)
                print(f"  Loaded {arrow_file.name}: {len(df)} rows")
            except Exception as e:
                print(f"  Error reading {arrow_file.name}: {e}")
        
        if dfs:
            combined_df = pd.concat(dfs, ignore_index=True)
            print(f"\nCombined DataFrame: {combined_df.shape}")
            return combined_df
        
    return None

# Method 2: Download from Google Drive and load
def download_and_load_michset():
    """Download MichSetHowusu data from Google Drive."""
    
    service = get_drive_service()
    
    # Find the folder
    results = service.files().list(
        q="name='fante_multispeaker_audio_transcribed' and mimeType='application/vnd.google-apps.folder'",
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    
    if not results.get('files'):
        print("Folder not found")
        return None
    
    folder_id = results['files'][0]['id']
    
    # Find train subfolder
    results = service.files().list(
        q=f"'{folder_id}' in parents and name='train'",
        spaces='drive',
        fields='files(id)'
    ).execute()
    
    if not results.get('files'):
        print("Train folder not found")
        return None
    
    train_folder_id = results['files'][0]['id']
    
    # List Arrow files
    results = service.files().list(
        q=f"'{train_folder_id}' in parents and name contains '.arrow'",
        spaces='drive',
        fields='files(id, name, size)'
    ).execute()
    
    arrow_files = results.get('files', [])
    print(f"Found {len(arrow_files)} Arrow files")
    
    # Download and combine
    dfs = []
    for file_info in arrow_files:
        print(f"Downloading {file_info['name']}...")
        
        request = service.files().get_media(fileId=file_info['id'])
        file_data = io.BytesIO()
        downloader = MediaIoBaseDownload(file_data, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"  Downloaded {int(status.progress() * 100)}%")
        
        # Read Arrow data
        file_data.seek(0)
        try:
            table = pa.ipc.open_stream(file_data).read_all()
            df = table.to_pandas()
            dfs.append(df)
            print(f"  Loaded {len(df)} samples")
        except Exception as e:
            print(f"  Error reading Arrow data: {e}")
    
    if dfs:
        combined_df = pd.concat(dfs, ignore_index=True)
        print(f"\nTotal samples: {len(combined_df)}")
        return combined_df
    
    return None

def get_drive_service():
    """Get authenticated Google Drive service."""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build('drive', 'v3', credentials=creds)

# Method 3: Use directly from Hugging Face
def load_from_huggingface():
    """Load MichSetHowusu datasets directly from Hugging Face."""
    
    from datasets import load_dataset
    
    datasets_to_load = [
        "michsethowusu/fante_multispeaker_audio_transcribed",
        "michsethowusu/twi_multispeaker_audio_transcribed",
        "michsethowusu/akuapem_multispeaker_audio_transcribed"
    ]
    
    all_data = []
    
    for dataset_name in datasets_to_load:
        print(f"\nLoading {dataset_name}...")
        try:
            dataset = load_dataset(dataset_name, token=True)
            
            # Check what's in the dataset
            print(f"  Splits: {list(dataset.keys())}")
            
            if 'train' in dataset:
                train_data = dataset['train']
                print(f"  Train samples: {len(train_data)}")
                print(f"  Features: {train_data.features}")
                
                # Check if it has audio and text
                if 'audio' in train_data.features and 'text' in train_data.features:
                    print("  ✓ Has audio and text columns")
                    
                    # Get a sample
                    sample = train_data[0]
                    print(f"  Sample text: {sample['text'][:100]}...")
                    print(f"  Audio info: {sample['audio']}")
                    
                    all_data.append(train_data)
                elif 'sentence' in train_data.features:
                    print("  ✓ Has sentence column")
                    all_data.append(train_data)
                else:
                    print(f"  Columns: {list(train_data.features.keys())}")
                    
        except Exception as e:
            print(f"  Error: {e}")
    
    return all_data

# Processing function for Arrow data
def process_arrow_data(data):
    """Process Arrow format data for training."""
    
    if isinstance(data, pd.DataFrame):
        df = data
    else:
        # Convert HF dataset to pandas
        df = data.to_pandas()
    
    print(f"\nProcessing {len(df)} samples...")
    print(f"Columns: {df.columns.tolist()}")
    
    # Common column mappings
    text_columns = ['text', 'sentence', 'transcript', 'transcription']
    audio_columns = ['audio', 'path', 'audio_path', 'file']
    
    # Find text column
    text_col = None
    for col in text_columns:
        if col in df.columns:
            text_col = col
            break
    
    # Find audio column
    audio_col = None
    for col in audio_columns:
        if col in df.columns:
            audio_col = col
            break
    
    if text_col:
        print(f"Text column: {text_col}")
        print(f"Sample texts:")
        for i in range(min(3, len(df))):
            print(f"  {i+1}. {df[text_col].iloc[i][:100]}...")
    
    if audio_col:
        print(f"\nAudio column: {audio_col}")
        # Check audio format
        sample_audio = df[audio_col].iloc[0]
        print(f"Audio format: {type(sample_audio)}")
        
        if isinstance(sample_audio, dict):
            print(f"Audio keys: {sample_audio.keys()}")
            if 'array' in sample_audio:
                print(f"Audio array shape: {len(sample_audio['array'])}")
            if 'sampling_rate' in sample_audio:
                print(f"Sampling rate: {sample_audio['sampling_rate']}")
    
    # Create training-ready format
    training_data = []
    for idx, row in df.iterrows():
        if text_col and audio_col:
            sample = {
                'text': row[text_col],
                'audio': row[audio_col],
                'id': idx
            }
            
            # Add metadata if available
            if 'language' in row:
                sample['language'] = row['language']
            if 'speaker_id' in row:
                sample['speaker_id'] = row['speaker_id']
                
            training_data.append(sample)
    
    print(f"\nPrepared {len(training_data)} training samples")
    return training_data

if __name__ == "__main__":
    print("="*60)
    print("LOADING MICHSETHOWUSU ARROW DATA")
    print("="*60)
    
    # Try Method 1: Local files
    print("\nMethod 1: Loading from local Arrow files...")
    data = load_arrow_files_locally()
    
    if data is not None:
        training_data = process_arrow_data(data)
    else:
        print("\nMethod 2: Loading from Hugging Face...")
        datasets = load_from_huggingface()
        
        if datasets:
            for dataset in datasets:
                training_data = process_arrow_data(dataset)