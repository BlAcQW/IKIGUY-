"""
Detailed Google Drive data analysis
"""

import os
import pickle
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from collections import defaultdict

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_service():
    """Get authenticated Drive service using existing token"""
    creds = None
    
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('drive', 'v3', credentials=creds)

def get_folder_details(service, folder_id, folder_name=""):
    """Get detailed information about folder contents"""
    try:
        results = service.files().list(
            q=f"'{folder_id}' in parents",
            spaces='drive',
            fields='files(id, name, mimeType, size, createdTime, modifiedTime)',
            pageSize=1000
        ).execute()
        
        items = results.get('files', [])
        
        stats = {
            'total_files': 0,
            'total_size': 0,
            'audio_files': 0,
            'text_files': 0,
            'folders': 0,
            'by_extension': defaultdict(int),
            'audio_formats': defaultdict(int)
        }
        
        audio_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.ogg', '.opus', '.aac'}
        text_extensions = {'.txt', '.csv', '.tsv', '.json', '.xml'}
        
        for item in items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                stats['folders'] += 1
            else:
                stats['total_files'] += 1
                size = int(item.get('size', 0))
                stats['total_size'] += size
                
                name = item['name'].lower()
                ext = Path(name).suffix
                stats['by_extension'][ext] += 1
                
                if ext in audio_extensions:
                    stats['audio_files'] += 1
                    stats['audio_formats'][ext] += 1
                elif ext in text_extensions:
                    stats['text_files'] += 1
        
        return stats, items
        
    except HttpError as error:
        print(f'Error: {error}')
        return None, []

def analyze_dataset(service, dataset_id, dataset_name):
    """Analyze a specific dataset folder"""
    stats, items = get_folder_details(service, dataset_id, dataset_name)
    
    if stats:
        print(f"\n[DATASET] {dataset_name}")
        print(f"  Total files: {stats['total_files']}")
        print(f"  Audio files: {stats['audio_files']}")
        print(f"  Text files: {stats['text_files']}")
        print(f"  Subfolders: {stats['folders']}")
        print(f"  Total size: {stats['total_size'] / (1024**3):.2f} GB")
        
        if stats['audio_formats']:
            print(f"  Audio formats:")
            for fmt, count in stats['audio_formats'].items():
                print(f"    {fmt}: {count} files")
        
        # Check for metadata files
        metadata_files = [f for f in items if any(x in f['name'].lower() for x in ['metadata', 'transcript', 'text', '.csv', '.tsv'])]
        if metadata_files:
            print(f"  Metadata files found:")
            for f in metadata_files[:5]:  # Show first 5
                print(f"    - {f['name']}")
    
    return stats

def main():
    print("="*60)
    print("DETAILED GOOGLE DRIVE DATA ANALYSIS")
    print("="*60)
    
    service = get_service()
    
    # Find voice-lab-data folder
    results = service.files().list(
        q="name='voice-lab-data' and mimeType='application/vnd.google-apps.folder'",
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    
    folders = results.get('files', [])
    if not folders:
        print("[ERROR] voice-lab-data folder not found")
        return
    
    base_folder_id = folders[0]['id']
    print(f"[OK] Found voice-lab-data folder")
    
    # Find raw folder
    results = service.files().list(
        q=f"'{base_folder_id}' in parents and name='raw' and mimeType='application/vnd.google-apps.folder'",
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    
    raw_folders = results.get('files', [])
    if not raw_folders:
        print("[ERROR] No raw folder found")
        return
    
    raw_folder_id = raw_folders[0]['id']
    
    # Get all datasets in raw folder
    results = service.files().list(
        q=f"'{raw_folder_id}' in parents and mimeType='application/vnd.google-apps.folder'",
        spaces='drive',
        fields='files(id, name)',
        pageSize=100
    ).execute()
    
    datasets = results.get('files', [])
    
    print(f"\n[INFO] Found {len(datasets)} datasets in /raw folder")
    print("="*60)
    
    total_stats = {
        'total_audio': 0,
        'total_text': 0,
        'total_size': 0,
        'datasets_with_audio': 0,
        'datasets_with_text': 0
    }
    
    # Analyze each dataset
    for dataset in datasets:
        stats = analyze_dataset(service, dataset['id'], dataset['name'])
        if stats:
            total_stats['total_audio'] += stats['audio_files']
            total_stats['total_text'] += stats['text_files']
            total_stats['total_size'] += stats['total_size']
            if stats['audio_files'] > 0:
                total_stats['datasets_with_audio'] += 1
            if stats['text_files'] > 0:
                total_stats['datasets_with_text'] += 1
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total datasets: {len(datasets)}")
    print(f"Datasets with audio: {total_stats['datasets_with_audio']}")
    print(f"Datasets with text: {total_stats['datasets_with_text']}")
    print(f"Total audio files: {total_stats['total_audio']:,}")
    print(f"Total text files: {total_stats['total_text']:,}")
    print(f"Total size: {total_stats['total_size'] / (1024**3):.2f} GB")
    
    # Check processed data
    print("\n" + "="*60)
    print("CHECKING PROCESSED DATA")
    print("="*60)
    
    # Check for processed folder
    results = service.files().list(
        q=f"'{base_folder_id}' in parents and name='processed' and mimeType='application/vnd.google-apps.folder'",
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    
    processed_folders = results.get('files', [])
    if processed_folders:
        processed_id = processed_folders[0]['id']
        stats, _ = get_folder_details(service, processed_id)
        if stats:
            print(f"[OK] Processed folder exists")
            print(f"  Files: {stats['total_files']}")
            print(f"  Size: {stats['total_size'] / (1024**3):.2f} GB")
    else:
        print("[INFO] No processed folder yet - will be created when processing runs")
    
    # Check for metadata
    results = service.files().list(
        q=f"'{base_folder_id}' in parents and name='metadata' and mimeType='application/vnd.google-apps.folder'",
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    
    metadata_folders = results.get('files', [])
    if metadata_folders:
        metadata_id = metadata_folders[0]['id']
        
        # Look for processed CSV
        results = service.files().list(
            q=f"'{metadata_id}' in parents and name contains 'processed'",
            spaces='drive',
            fields='files(id, name, size, modifiedTime)'
        ).execute()
        
        csv_files = results.get('files', [])
        if csv_files:
            print(f"\n[OK] Found {len(csv_files)} processed metadata files:")
            for f in csv_files:
                print(f"  - {f['name']} (modified: {f['modifiedTime'][:10]})")
    
    # Recommendations
    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    
    if total_stats['total_audio'] > 1000:
        print("[OK] Sufficient audio data for training!")
        print("\nNext steps:")
        print("1. Open 002_phase1_data_processing_enhanced.ipynb in Google Colab")
        print("2. Mount your Google Drive")
        print("3. Run all cells to process the data")
        print("4. Expected processing time: 2-4 hours for full dataset")
    elif total_stats['total_audio'] > 100:
        print("[WARNING] Limited audio data available")
        print("You can proceed with processing but consider adding more data")
    else:
        print("[ERROR] Insufficient audio data")
        print("Please upload more datasets to /raw folder")
    
    print("\nData requirements for good TTS model:")
    print("- Minimum: 1,000 audio files")
    print("- Recommended: 10,000+ audio files")
    print("- Best: 50,000+ audio files with diverse speakers")

if __name__ == "__main__":
    main()