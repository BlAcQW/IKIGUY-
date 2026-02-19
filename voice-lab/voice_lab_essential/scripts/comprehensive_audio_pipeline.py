#!/usr/bin/env python3
"""
Comprehensive Audio Processing Pipeline for Voice Lab
Handles all audio formats including .ogg files from Financial Inclusion dataset
Works with Google Drive integration and processes multiple datasets
"""

import json
import os
import librosa
import soundfile as sf
import numpy as np
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from tqdm import tqdm
from typing import Dict, List, Optional, Tuple
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile
import shutil

class AudioProcessor:
    """Comprehensive audio processing for voice datasets"""
    
    def __init__(self, target_sr: int = 16000, max_duration: float = 30.0):
        self.target_sr = target_sr
        self.max_duration = max_duration
        self.supported_formats = ['.wav', '.mp3', '.flac', '.ogg', '.m4a']
        
    def process_audio_file(self, audio_path: Path, output_path: Path) -> Dict:
        """Process a single audio file to standard format"""
        try:
            # Load audio with librosa (handles all formats including .ogg)
            audio, sr = librosa.load(audio_path, sr=self.target_sr, mono=True)
            
            # Basic audio information
            duration = len(audio) / sr
            
            # Skip if too short (less than 0.5 seconds)
            if duration < 0.5:
                return {
                    'status': 'skipped',
                    'reason': 'too_short',
                    'duration': duration
                }
            
            # Trim silence
            audio, _ = librosa.effects.trim(audio, top_db=20)
            
            # Normalize audio
            audio = librosa.util.normalize(audio)
            
            # Split long audio into segments
            segments = []
            if duration > self.max_duration:
                # Split into overlapping segments
                segment_length = int(self.max_duration * sr)
                hop_length = int(segment_length * 0.75)  # 25% overlap
                
                for i in range(0, len(audio) - segment_length + 1, hop_length):
                    segment = audio[i:i + segment_length]
                    segments.append(segment)
                
                # Add final segment if needed
                if len(audio) > len(segments) * hop_length:
                    segments.append(audio[-segment_length:])
            else:
                segments = [audio]
            
            # Save segments
            saved_files = []
            for i, segment in enumerate(segments):
                if len(segments) == 1:
                    output_file = output_path
                else:
                    stem = output_path.stem
                    suffix = output_path.suffix
                    output_file = output_path.parent / f"{stem}_seg{i:03d}{suffix}"
                
                # Create output directory if needed
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Save as WAV
                sf.write(output_file, segment, self.target_sr)
                saved_files.append(output_file)
            
            return {
                'status': 'success',
                'original_duration': duration,
                'segments_created': len(segments),
                'output_files': saved_files,
                'sample_rate': self.target_sr
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_audio_stats(self, audio_path: Path) -> Dict:
        """Get statistics for an audio file without processing"""
        try:
            audio, sr = librosa.load(audio_path, sr=None, duration=1)  # Just load 1 second for stats
            duration_estimate = librosa.get_duration(path=audio_path)
            
            return {
                'sample_rate': sr,
                'duration': duration_estimate,
                'format': audio_path.suffix.lower(),
                'size_mb': audio_path.stat().st_size / (1024*1024)
            }
        except Exception as e:
            return {
                'error': str(e),
                'size_mb': audio_path.stat().st_size / (1024*1024) if audio_path.exists() else 0
            }

class GoogleDriveAudioPipeline:
    """Pipeline that processes audio files from Google Drive"""
    
    def __init__(self, service_account_path: str = "./credentials/service_account.json"):
        self.service_account_path = service_account_path
        self.service = None
        self.processor = AudioProcessor()
        self.setup_drive_connection()
        
    def setup_drive_connection(self):
        """Setup Google Drive connection"""
        credentials = service_account.Credentials.from_service_account_file(
            self.service_account_path,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        self.service = build('drive', 'v3', credentials=credentials)
    
    def download_and_process_file(self, file_id: str, file_name: str, output_dir: Path) -> Dict:
        """Download a file from Google Drive and process it"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=Path(file_name).suffix, delete=False) as temp_file:
                temp_path = Path(temp_file.name)
            
            # Download from Google Drive
            request = self.service.files().get_media(fileId=file_id)
            with open(temp_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
            
            # Process audio
            output_path = output_dir / f"{Path(file_name).stem}.wav"
            result = self.processor.process_audio_file(temp_path, output_path)
            
            # Cleanup
            temp_path.unlink()
            
            return result
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def process_financial_inclusion_dataset(self, output_dir: Path = Path('./data/processed/financial_inclusion')):
        """Process the Financial Inclusion dataset with .ogg files"""
        print("🎵 PROCESSING FINANCIAL INCLUSION DATASET")
        print("=" * 60)
        
        # Load connection info
        with open('./data/drive_connection_summary.json', 'r') as f:
            connection_info = json.load(f)
            raw_folder_id = connection_info['raw_folder_id']
        
        # Find financial_inclusion folder
        fi_results = self.service.files().list(
            q=f"name='financial_inclusion' and '{raw_folder_id}' in parents and trashed=false",
            fields="files(id, name)"
        ).execute()
        
        if not fi_results.get('files'):
            print("❌ Financial inclusion folder not found")
            return
        
        fi_folder_id = fi_results['files'][0]['id']
        print(f"✅ Found financial inclusion folder: {fi_folder_id}")
        
        # Get all .ogg files recursively
        all_ogg_files = self.get_audio_files_recursive(fi_folder_id, extensions=['.ogg'])
        
        print(f"📁 Found {len(all_ogg_files)} .ogg files")
        
        if not all_ogg_files:
            print("❌ No .ogg files found to process")
            return
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Process files with progress bar
        processed_count = 0
        errors = []
        
        print(f"\n🔄 Processing {len(all_ogg_files)} audio files...")
        
        with tqdm(total=len(all_ogg_files), desc="Processing") as pbar:
            for file_info in all_ogg_files:
                result = self.download_and_process_file(
                    file_info['id'], 
                    file_info['name'], 
                    output_dir
                )
                
                if result['status'] == 'success':
                    processed_count += 1
                else:
                    errors.append({
                        'file': file_info['name'],
                        'error': result.get('error', 'Unknown error')
                    })
                
                pbar.update(1)
        
        # Save processing report
        report = {
            'total_files': len(all_ogg_files),
            'processed_successfully': processed_count,
            'errors': len(errors),
            'error_details': errors[:10],  # First 10 errors
            'output_directory': str(output_dir),
            'processing_date': pd.Timestamp.now().isoformat()
        }
        
        report_path = output_dir / 'processing_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 PROCESSING COMPLETE")
        print(f"  ✅ Successfully processed: {processed_count}/{len(all_ogg_files)} files")
        print(f"  ❌ Errors: {len(errors)}")
        print(f"  📁 Output directory: {output_dir}")
        print(f"  📋 Report saved: {report_path}")
        
        return report
    
    def get_audio_files_recursive(self, folder_id: str, extensions: List[str] = None) -> List[Dict]:
        """Get all audio files recursively from a folder"""
        if extensions is None:
            extensions = self.processor.supported_formats
        
        all_files = []
        folders_to_scan = [folder_id]
        
        while folders_to_scan:
            current_folder = folders_to_scan.pop(0)
            
            results = self.service.files().list(
                q=f"'{current_folder}' in parents and trashed=false",
                fields="files(id, name, size, mimeType)",
                pageSize=1000
            ).execute()
            
            files = results.get('files', [])
            
            for file in files:
                if file['mimeType'] == 'application/vnd.google-apps.folder':
                    folders_to_scan.append(file['id'])
                else:
                    file_name = file['name'].lower()
                    if any(ext in file_name for ext in extensions):
                        all_files.append(file)
        
        return all_files
    
    def analyze_dataset_structure(self, dataset_folder_id: str) -> Dict:
        """Analyze the structure of a dataset folder"""
        print(f"📊 Analyzing dataset structure...")
        
        audio_files = self.get_audio_files_recursive(dataset_folder_id)
        
        # Group by extension
        by_extension = {}
        total_size = 0
        
        for file in audio_files:
            ext = Path(file['name']).suffix.lower()
            size = int(file.get('size', 0))
            
            if ext not in by_extension:
                by_extension[ext] = {'count': 0, 'size': 0}
            
            by_extension[ext]['count'] += 1
            by_extension[ext]['size'] += size
            total_size += size
        
        # Sample a few files for detailed stats
        sample_files = audio_files[:5] if len(audio_files) > 5 else audio_files
        sample_stats = []
        
        for file in sample_files:
            # Download small sample for analysis
            try:
                with tempfile.NamedTemporaryFile(suffix=Path(file['name']).suffix) as temp_file:
                    temp_path = Path(temp_file.name)
                    
                    request = self.service.files().get_media(fileId=file['id'])
                    with open(temp_path, 'wb') as f:
                        downloader = MediaIoBaseDownload(f, request)
                        done = False
                        while done is False:
                            status, done = downloader.next_chunk()
                    
                    stats = self.processor.get_audio_stats(temp_path)
                    stats['filename'] = file['name']
                    sample_stats.append(stats)
                    
            except Exception as e:
                sample_stats.append({
                    'filename': file['name'],
                    'error': str(e)
                })
        
        analysis = {
            'total_files': len(audio_files),
            'by_extension': by_extension,
            'total_size_mb': total_size / (1024*1024),
            'sample_stats': sample_stats
        }
        
        # Print summary
        print(f"📊 Dataset Analysis:")
        print(f"  Total audio files: {len(audio_files):,}")
        print(f"  Total size: {total_size/(1024*1024):.1f} MB")
        print(f"  File types:")
        for ext, info in by_extension.items():
            print(f"    {ext}: {info['count']:,} files ({info['size']/(1024*1024):.1f} MB)")
        
        return analysis

def main():
    """Main function to run the comprehensive audio processing pipeline"""
    print("🎵 COMPREHENSIVE AUDIO PROCESSING PIPELINE")
    print("=" * 60)
    
    pipeline = GoogleDriveAudioPipeline()
    
    # Load connection info
    with open('./data/drive_connection_summary.json', 'r') as f:
        connection_info = json.load(f)
    
    # Process Financial Inclusion dataset (.ogg files)
    print("\n1. Processing Financial Inclusion Dataset")
    fi_report = pipeline.process_financial_inclusion_dataset()
    
    # You can add more datasets here:
    # print("\n2. Processing BibleTTS Dataset")
    # bibletts_report = pipeline.process_bibletts_dataset()
    
    print(f"\n✅ PIPELINE COMPLETE")
    print(f"All processed audio files are in ./data/processed/")
    print(f"Reports saved with processing details")

if __name__ == "__main__":
    main()