#!/usr/bin/env python3
"""
Mozilla Common Voice Dataset Analysis and Download Test
"""

import json
import os
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build

def check_common_voice_in_drive():
    """Check what's in the common_voice folder in Google Drive"""
    print("🎙️ COMMON VOICE DATASET ANALYSIS")
    print("=" * 50)
    
    # Setup Google Drive connection
    service_account_file = "./credentials/service_account.json"
    credentials = service_account.Credentials.from_service_account_file(
        service_account_file,
        scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    service = build('drive', 'v3', credentials=credentials)
    
    # Load connection info
    with open('./data/drive_connection_summary.json', 'r') as f:
        connection_info = json.load(f)
        raw_folder_id = connection_info['raw_folder_id']
    
    # Find common_voice folder
    cv_results = service.files().list(
        q=f"name='common_voice' and '{raw_folder_id}' in parents and trashed=false",
        fields="files(id, name)"
    ).execute()
    
    if not cv_results.get('files'):
        print("❌ Common Voice folder not found")
        return None, None
    
    cv_folder_id = cv_results['files'][0]['id']
    print(f"✅ Found common_voice folder: {cv_folder_id}")
    
    # Check contents
    contents = service.files().list(
        q=f"'{cv_folder_id}' in parents and trashed=false",
        fields="files(id, name, size, mimeType)",
        pageSize=1000
    ).execute()
    
    files = contents.get('files', [])
    print(f"📁 Found {len(files)} items in common_voice folder:")
    
    total_size = 0
    audio_count = 0
    text_count = 0
    
    for file in files:
        file_size = int(file.get('size', 0)) if file.get('size') else 0
        total_size += file_size
        file_name = file['name'].lower()
        
        file_type = "📁" if file['mimeType'] == 'application/vnd.google-apps.folder' else "📄"
        size_mb = file_size / (1024*1024) if file_size > 0 else 0
        
        print(f"  {file_type} {file['name']} ({size_mb:.1f} MB)")
        
        if any(ext in file_name for ext in ['.wav', '.mp3', '.ogg', '.flac']):
            audio_count += 1
        elif any(ext in file_name for ext in ['.txt', '.tsv', '.csv']):
            text_count += 1
    
    print(f"\n📊 Summary:")
    print(f"  🎵 Audio files: {audio_count}")
    print(f"  📄 Text files: {text_count}")
    print(f"  💾 Total size: {total_size/(1024*1024):.1f} MB")
    
    return service, cv_folder_id

def download_common_voice_ak():
    """Download Common Voice Akan dataset using HuggingFace datasets"""
    try:
        from datasets import load_dataset
        print("\n🔄 Attempting to download Common Voice Twi dataset...")
        
        # Try multiple versions and language codes
        versions_to_try = [
            ("mozilla-foundation/common_voice_17_0", "tw"),  # Latest version, Twi
            ("mozilla-foundation/common_voice_16_1", "tw"),  # Previous version
            ("mozilla-foundation/common_voice_13_0", "ak"),  # Older version, Akan
        ]
        
        for dataset_name, lang_code in versions_to_try:
            print(f"📥 Trying {dataset_name} with language code '{lang_code}'...")
            
            try:
                # Use HuggingFace token for authentication
                hf_token = "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"
                dataset = load_dataset(dataset_name, lang_code, split="train", token=hf_token)
                
                print(f"✅ Successfully loaded dataset!")
                print(f"📊 Dataset info:")
                print(f"  📄 Number of samples: {len(dataset)}")
                print(f"  🏷️ Features: {list(dataset.features.keys())}")
                
                # Show a sample
                if len(dataset) > 0:
                    sample = dataset[0]
                    print(f"\n📝 Sample entry:")
                    for key, value in sample.items():
                        if key == 'audio':
                            print(f"  {key}: [audio data - {type(value)}]")
                        else:
                            print(f"  {key}: {str(value)[:100]}...")
                
                # Save dataset info for uploading to Google Drive
                metadata_dir = Path('./data/metadata')
                metadata_dir.mkdir(parents=True, exist_ok=True)
                
                dataset_info = {
                    'dataset_name': dataset_name,
                    'language_code': lang_code,
                    'split': 'train',
                    'num_samples': len(dataset),
                    'features': list(dataset.features.keys()),
                    'analysis_date': '2025-09-05',
                    'status': 'successfully_loaded'
                }
                
                with open(metadata_dir / 'common_voice_analysis.json', 'w') as f:
                    json.dump(dataset_info, f, indent=2)
                
                print(f"✅ Analysis saved to: {metadata_dir / 'common_voice_analysis.json'}")
                
                return dataset
                
            except Exception as e:
                print(f"  ❌ Failed: {e}")
                if "gated" in str(e).lower() or "authenticated" in str(e).lower():
                    print(f"  💡 This dataset requires authentication")
                continue
        
        print(f"\n❌ Could not access any Common Voice dataset")
        return None
        
    except ImportError:
        print("❌ datasets library not installed")
        print("💡 Run: pip install datasets")
        return None
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        return None

def upload_to_drive_folder(service, folder_id, local_file_path, remote_name):
    """Upload a file to Google Drive folder"""
    try:
        from googleapiclient.http import MediaFileUpload
        
        file_metadata = {
            'name': remote_name,
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(local_file_path, resumable=True)
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        print(f"✅ Uploaded {remote_name} to Google Drive: {file.get('id')}")
        return file.get('id')
        
    except Exception as e:
        print(f"❌ Error uploading {remote_name}: {e}")
        return None

def main():
    """Main function to test Common Voice dataset"""
    
    # Check current state in Google Drive
    service, cv_folder_id = check_common_voice_in_drive()
    
    if not service:
        print("❌ Could not connect to Google Drive")
        return
    
    # Test HuggingFace dataset download
    dataset = download_common_voice_ak()
    
    if dataset:
        print(f"\n🎯 COMMON VOICE AKAN ANALYSIS:")
        print(f"  ✅ Dataset successfully loaded from HuggingFace")
        print(f"  📊 Contains {len(dataset)} audio samples")
        print(f"  🏷️ Features: {list(dataset.features.keys())}")
        
        # Save dataset info to local metadata
        metadata_dir = Path('./data/metadata')
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        dataset_info = {
            'dataset_name': 'mozilla-foundation/common_voice_13_0',
            'language': 'ak',
            'split': 'train',
            'num_samples': len(dataset),
            'features': list(dataset.features.keys()),
            'analysis_date': '2025-09-05',
            'status': 'successfully_loaded'
        }
        
        with open(metadata_dir / 'common_voice_analysis.json', 'w') as f:
            json.dump(dataset_info, f, indent=2)
        
        print(f"✅ Analysis saved to: {metadata_dir / 'common_voice_analysis.json'}")
        
    else:
        print(f"\n❌ Could not load Common Voice dataset")
        print(f"💡 This might be due to:")
        print(f"  • Missing datasets library (pip install datasets)")
        print(f"  • Network connectivity issues")
        print(f"  • Dataset access restrictions")
    
    print(f"\n🔗 Google Drive folder: https://drive.google.com/drive/folders/{cv_folder_id}")

if __name__ == "__main__":
    main()