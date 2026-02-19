"""
Comprehensive Dataset Verification Script
Checks all Twi voice datasets and reports their status
"""

from pathlib import Path
import pandas as pd
import json
from datetime import datetime

def check_bibletts(raw_dir: Path):
    """Check BibleTTS dataset availability."""
    print("\n" + "="*60)
    print("BIBLETTS DATASET")
    print("="*60)
    
    bibletts_dir = raw_dir / 'bibletts'
    status = {'available': False, 'audio_files': 0, 'dialects': []}
    
    if bibletts_dir.exists():
        # Check for dialect folders (with hyphens!)
        dialect_dirs = {
            'akuapem-twi': bibletts_dir / 'akuapem-twi',
            'asante-twi': bibletts_dir / 'asante-twi'
        }
        
        for dialect, dialect_dir in dialect_dirs.items():
            if dialect_dir.exists():
                # Check recursively for FLAC files (they're in book subdirectories)
                flac_files = list(dialect_dir.rglob('*.flac'))
                
                if flac_files:
                    print(f"[OK] {dialect}: {len(flac_files)} FLAC files")
                    status['audio_files'] += len(flac_files)
                    status['dialects'].append(dialect)
                else:
                    print(f"[WARNING] {dialect}: Directory exists but no FLAC files")
            else:
                print(f"[ERROR] {dialect}: Directory not found at {dialect_dir}")
        
        status['available'] = status['audio_files'] > 0
    else:
        print(f"[ERROR] BibleTTS directory not found at {bibletts_dir}")
    
    return status


def check_financial_inclusion(raw_dir: Path):
    """Check Financial Inclusion dataset availability."""
    print("\n" + "="*60)
    print("FINANCIAL INCLUSION DATASET")
    print("="*60)
    
    fi_dir = raw_dir / 'financial_inclusion'
    status = {'available': False, 'audio_files': 0, 'languages': []}
    
    if fi_dir.exists():
        # Check nested structure
        language_configs = {
            'fante_10': fi_dir / 'fante_10' / 'fisd-fanti-10p' / 'audios',
            'ga_10': fi_dir / 'ga_10' / 'fisd-ga-10p' / 'audios',
            'twi_10': fi_dir / 'twi_10' / 'fisd-twi-10p' / 'audios'
        }
        
        for lang, audio_dir in language_configs.items():
            if audio_dir.exists():
                ogg_files = list(audio_dir.glob('*.ogg'))
                if ogg_files:
                    print(f"[OK] {lang}: {len(ogg_files)} OGG files")
                    status['audio_files'] += len(ogg_files)
                    status['languages'].append(lang)
                    
                    # Check for transcript
                    transcript = audio_dir.parent / 'transcript.csv'
                    if transcript.exists():
                        print(f"   [TEXT] Transcript found: {transcript.name}")
                else:
                    print(f"[WARNING] {lang}: Directory exists but no OGG files")
            else:
                print(f"[ERROR] {lang}: Directory not found at {audio_dir}")
        
        status['available'] = status['audio_files'] > 0
    else:
        print(f"[ERROR] Financial Inclusion directory not found at {fi_dir}")
    
    return status


def check_common_voice(raw_dir: Path):
    """Check Common Voice dataset availability."""
    print("\n" + "="*60)
    print("COMMON VOICE DATASET")
    print("="*60)
    
    cv_dir = raw_dir / 'common_voice'
    status = {'available': False, 'audio_files': 0, 'has_metadata': False}
    
    if cv_dir.exists():
        # Look for the actual data directory
        tw_dir = cv_dir / 'cv-corpus-22.0-delta-2025-06-20-tw' / 'cv-corpus-22.0-delta-2025-06-20' / 'tw'
        
        if tw_dir.exists():
            # Check for clips
            clips_dir = tw_dir / 'clips'
            if clips_dir.exists():
                mp3_files = list(clips_dir.glob('*.mp3'))
                print(f"[DIR] Clips directory: {len(mp3_files)} MP3 files")
                status['audio_files'] = len(mp3_files)
                
                if status['audio_files'] == 0:
                    print("[WARNING] WARNING: No audio files found! Only metadata present.")
                    print("   Need to download with audio=True parameter")
            
            # Check for metadata files
            tsv_files = list(tw_dir.glob('*.tsv'))
            if tsv_files:
                print(f"[STATS] Metadata files: {len(tsv_files)} TSV files")
                status['has_metadata'] = True
                
                # Check validated.tsv
                validated = tw_dir / 'validated.tsv'
                if validated.exists():
                    df = pd.read_csv(validated, sep='\t', nrows=5)
                    total_rows = sum(1 for _ in open(validated, encoding='utf-8')) - 1
                    print(f"   [OK] validated.tsv: {total_rows} sentences")
            
            status['available'] = status['audio_files'] > 0 or status['has_metadata']
        else:
            print(f"[ERROR] Common Voice TW directory not found at {tw_dir}")
    else:
        print(f"[ERROR] Common Voice directory not found at {cv_dir}")
    
    return status


def check_michsethowusu(raw_dir: Path):
    """Check MichSetHowusu dataset availability."""
    print("\n" + "="*60)
    print("MICHSETHOWUSU DATASET")
    print("="*60)
    
    michset_dir = raw_dir / 'michsethowusu'
    status = {'available': False, 'arrow_files': 0, 'datasets': []}
    
    if michset_dir.exists():
        # Check for Arrow dataset directories
        dataset_dirs = [
            'twi_multispeaker_audio_transcribed',
            'akuapem_multispeaker_audio_transcribed',
            'fante_multispeaker_audio_transcribed'
        ]
        
        for dataset_name in dataset_dirs:
            dataset_path = michset_dir / dataset_name / 'train'
            if dataset_path.exists():
                arrow_files = list(dataset_path.glob('*.arrow'))
                if arrow_files:
                    print(f"[OK] {dataset_name}: {len(arrow_files)} Arrow files")
                    status['arrow_files'] += len(arrow_files)
                    status['datasets'].append(dataset_name)
                    
                    # Check for dataset_info.json
                    info_file = dataset_path.parent / 'dataset_info.json'
                    if info_file.exists():
                        with open(info_file, 'r') as f:
                            info = json.load(f)
                            if 'splits' in info:
                                for split, details in info['splits'].items():
                                    if 'num_examples' in details:
                                        print(f"   [STATS] {split}: {details['num_examples']} examples")
                else:
                    print(f"[WARNING] {dataset_name}: Directory exists but no Arrow files")
            else:
                print(f"[ERROR] {dataset_name}: Not found at {dataset_path}")
        
        status['available'] = status['arrow_files'] > 0
    else:
        print(f"[ERROR] MichSetHowusu directory not found at {michset_dir}")
    
    return status


def check_other_datasets(raw_dir: Path):
    """Check other datasets that were supposed to be downloaded."""
    print("\n" + "="*60)
    print("OTHER DATASETS")
    print("="*60)
    
    other_status = {}
    
    # African Whisper
    african_whisper = raw_dir / 'african_whisper'
    if african_whisper.exists():
        audio_files = []
        for ext in ['.wav', '.mp3', '.flac', '.ogg']:
            audio_files.extend(list(african_whisper.rglob(f'*{ext}')))
        
        if audio_files:
            print(f"[OK] African Whisper: {len(audio_files)} audio files")
        else:
            # Check if it's just code
            py_files = list(african_whisper.glob('*.py'))
            if py_files:
                print(f"[WARNING] African Whisper: Found Python code only (no audio data)")
            else:
                print(f"[WARNING] African Whisper: Directory exists but no audio files")
        
        other_status['african_whisper'] = len(audio_files) > 0
    else:
        print(f"[ERROR] African Whisper: Not found")
        other_status['african_whisper'] = False
    
    # JW300
    jw300 = raw_dir / 'jw300'
    if jw300.exists():
        # JW300 is typically text-only
        txt_files = list(jw300.rglob('*.txt'))
        print(f"[TEXT] JW300: {len(txt_files)} text files (text-only corpus)")
        other_status['jw300'] = True
    else:
        print(f"[ERROR] JW300: Not found")
        other_status['jw300'] = False
    
    # AfriSpeech
    afrispeech = raw_dir / 'afrispeech'
    if afrispeech.exists():
        audio_files = []
        for ext in ['.wav', '.mp3', '.flac', '.ogg']:
            audio_files.extend(list(afrispeech.rglob(f'*{ext}')))
        print(f"{'[OK]' if audio_files else '[WARNING]'} AfriSpeech: {len(audio_files)} audio files")
        other_status['afrispeech'] = len(audio_files) > 0
    else:
        print(f"[ERROR] AfriSpeech: Not found")
        other_status['afrispeech'] = False
    
    # Lingua Libre
    lingua_libre = raw_dir / 'lingua_libre'
    if lingua_libre.exists():
        audio_files = []
        for ext in ['.wav', '.mp3', '.flac', '.ogg']:
            audio_files.extend(list(lingua_libre.rglob(f'*{ext}')))
        print(f"{'[OK]' if audio_files else '[WARNING]'} Lingua Libre: {len(audio_files)} audio files")
        other_status['lingua_libre'] = len(audio_files) > 0
    else:
        print(f"[ERROR] Lingua Libre: Not found")
        other_status['lingua_libre'] = False
    
    return other_status


def generate_report(results: dict, output_path: Path = None):
    """Generate a comprehensive report of dataset status."""
    
    print("\n" + "="*60)
    print("DATASET VERIFICATION REPORT")
    print("="*60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Summary statistics
    total_audio_files = 0
    ready_datasets = []
    needs_processing = []
    missing_datasets = []
    
    # BibleTTS
    if results['bibletts']['available']:
        ready_datasets.append(f"BibleTTS ({results['bibletts']['audio_files']} files)")
        total_audio_files += results['bibletts']['audio_files']
    else:
        missing_datasets.append("BibleTTS")
    
    # Financial Inclusion
    if results['financial_inclusion']['available']:
        ready_datasets.append(f"Financial Inclusion ({results['financial_inclusion']['audio_files']} files)")
        total_audio_files += results['financial_inclusion']['audio_files']
    else:
        missing_datasets.append("Financial Inclusion")
    
    # Common Voice
    if results['common_voice']['audio_files'] > 0:
        ready_datasets.append(f"Common Voice ({results['common_voice']['audio_files']} files)")
        total_audio_files += results['common_voice']['audio_files']
    elif results['common_voice']['has_metadata']:
        needs_processing.append("Common Voice (metadata only, needs audio download)")
    else:
        missing_datasets.append("Common Voice")
    
    # MichSetHowusu
    if results['michsethowusu']['available']:
        needs_processing.append(f"MichSetHowusu ({results['michsethowusu']['arrow_files']} Arrow files)")
    else:
        missing_datasets.append("MichSetHowusu")
    
    # Print summary
    print("\n[STATS] SUMMARY:")
    print(f"Total audio files ready: {total_audio_files:,}")
    
    print(f"\n[OK] Ready to use ({len(ready_datasets)}):")
    for dataset in ready_datasets:
        print(f"   - {dataset}")
    
    if needs_processing:
        print(f"\n[WARNING] Needs processing ({len(needs_processing)}):")
        for dataset in needs_processing:
            print(f"   - {dataset}")
    
    if missing_datasets:
        print(f"\n[ERROR] Missing ({len(missing_datasets)}):")
        for dataset in missing_datasets:
            print(f"   - {dataset}")
    
    # Save report if output path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_audio_files': total_audio_files,
                'ready_datasets': ready_datasets,
                'needs_processing': needs_processing,
                'missing_datasets': missing_datasets
            },
            'details': results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n[SAVE] Report saved to: {output_path}")
    
    return total_audio_files > 0


def main():
    """Main verification function."""
    
    # Determine paths
    if Path("G:/My Drive/voice-lab-data/raw").exists():
        raw_dir = Path("G:/My Drive/voice-lab-data/raw")
        print(f"[OK] Using Google Drive: {raw_dir}")
    else:
        raw_dir = Path("./data/raw")
        print(f"[DIR] Using local directory: {raw_dir}")
    
    if not raw_dir.exists():
        print(f"[ERROR] Raw data directory not found: {raw_dir}")
        return False
    
    # Run all checks
    results = {
        'bibletts': check_bibletts(raw_dir),
        'financial_inclusion': check_financial_inclusion(raw_dir),
        'common_voice': check_common_voice(raw_dir),
        'michsethowusu': check_michsethowusu(raw_dir),
        'other': check_other_datasets(raw_dir)
    }
    
    # Generate report
    output_path = raw_dir.parent / 'dataset_verification_report.json'
    success = generate_report(results, output_path)
    
    # Recommendations
    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    
    if not results['common_voice']['audio_files']:
        print("\n1. Download Common Voice with audio:")
        print("   Run: python download_common_voice_with_audio.py")
    
    if results['michsethowusu']['available']:
        print("\n2. Process MichSetHowusu Arrow files:")
        print("   Run: python process_michsethowusu_arrow.py")
    
    if results['bibletts']['available'] and results['financial_inclusion']['available']:
        print("\n3. Ready to run processing pipeline:")
        print("   Open and run: 002_phase1_data_processing_enhanced.ipynb")
    
    print("\n" + "="*60)
    
    return success


if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n[OK] Verification complete! Some datasets are ready for processing.")
    else:
        print("\n[WARNING] No datasets found. Please run data acquisition first.")