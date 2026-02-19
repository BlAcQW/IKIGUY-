#!/usr/bin/env python3
"""
Production Integration Examples for Enhanced Twi Text Processor
Demonstrates real-world usage patterns for voice technology applications
"""

import sys
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd

# Import the enhanced processor
from enhanced_twi_processor import EnhancedTwiTextProcessor


class TwiTTSPreprocessor:
    """Text preprocessing for TTS synthesis in production."""
    
    def __init__(self, dialect: str = 'asante', cache_phonemes: bool = True):
        self.processor = EnhancedTwiTextProcessor(dialect=dialect)
        self.dialect = dialect
        self.phoneme_cache = {} if cache_phonemes else None
        
    def preprocess_for_synthesis(self, text: str, speaker_id: Optional[str] = None) -> Dict:
        """Preprocess text for TTS synthesis."""
        
        # Check cache first
        cache_key = f"{text}_{self.dialect}"
        if self.phoneme_cache and cache_key in self.phoneme_cache:
            return self.phoneme_cache[cache_key]
        
        # Process text with all enhancements
        result = self.processor.process_text(
            text,
            expand_numbers=True,
            expand_abbreviations=True,
            process_datetime=True,
            apply_dialect=True,
            generate_phonemes=True
        )
        
        # Prepare for TTS
        synthesis_data = {
            'text': result['processed'],
            'phonemes': result['phonemes'],
            'speaker_id': speaker_id or f"default_{self.dialect}",
            'dialect': self.dialect,
            'word_count': result['word_count'],
            'estimated_duration': result['word_count'] * 0.6,  # ~0.6s per word
            'has_twi_content': result['has_twi_chars'],
            'metadata': {
                'original': result['original'],
                'processing_timestamp': datetime.now().isoformat(),
                'char_count': result['char_count']
            }
        }
        
        # Cache if enabled
        if self.phoneme_cache:
            self.phoneme_cache[cache_key] = synthesis_data
            
        return synthesis_data
    
    def batch_preprocess(self, texts: List[str], speaker_id: Optional[str] = None) -> List[Dict]:
        """Process multiple texts for batch synthesis."""
        results = []
        for text in texts:
            result = self.preprocess_for_synthesis(text, speaker_id)
            results.append(result)
        return results


class TwiASRPostprocessor:
    """Post-processing for ASR outputs in production."""
    
    def __init__(self, dialect: str = 'asante'):
        self.processor = EnhancedTwiTextProcessor(dialect=dialect)
        self.dialect = dialect
        
    def postprocess_recognition(self, asr_output: str, confidence: float = 1.0) -> Dict:
        """Post-process ASR output for better readability."""
        
        # Basic processing without phonemes (ASR output is already text)
        result = self.processor.process_text(
            asr_output,
            expand_numbers=False,  # Numbers already in text form from ASR
            expand_abbreviations=True,
            process_datetime=False,  # Times already in text form
            apply_dialect=True,
            generate_phonemes=False
        )
        
        return {
            'recognized_text': result['processed'],
            'confidence': confidence,
            'dialect': self.dialect,
            'has_twi_content': result['has_twi_chars'],
            'word_count': result['word_count'],
            'quality_indicators': {
                'likely_valid': confidence > 0.7 and result['word_count'] > 1,
                'contains_twi': result['has_twi_chars'],
                'reasonable_length': 2 <= result['word_count'] <= 50
            }
        }


class TwiVoiceAssistant:
    """Complete voice assistant with Twi processing."""
    
    def __init__(self, dialect: str = 'asante'):
        self.tts_processor = TwiTTSPreprocessor(dialect=dialect)
        self.asr_processor = TwiASRPostprocessor(dialect=dialect)
        self.dialog_history = []
        
    def process_user_input(self, audio_file: str) -> Dict:
        """Process user audio input (simulated ASR)."""
        # In real implementation, this would call ASR service
        # For demo, we'll simulate ASR output
        simulated_asr = "Ɛte sɛn? Me pɛ nkwan bi."
        confidence = 0.85
        
        return self.asr_processor.postprocess_recognition(simulated_asr, confidence)
    
    def generate_response(self, user_input: str, response_text: str) -> Dict:
        """Generate TTS response."""
        # Log dialog
        self.dialog_history.append({
            'user': user_input,
            'assistant': response_text,
            'timestamp': datetime.now().isoformat()
        })
        
        return self.tts_processor.preprocess_for_synthesis(response_text)
    
    def get_dialog_summary(self) -> Dict:
        """Get dialog session summary."""
        return {
            'session_length': len(self.dialog_history),
            'total_exchanges': len(self.dialog_history),
            'dialect': self.tts_processor.dialect,
            'last_interaction': self.dialog_history[-1] if self.dialog_history else None
        }


class TwiBroadcastProcessor:
    """Processing for news/radio broadcast content."""
    
    def __init__(self, dialect: str = 'asante'):
        self.processor = EnhancedTwiTextProcessor(dialect=dialect)
        
    def process_news_script(self, script: str, segment_length: int = 100) -> List[Dict]:
        """Process news script for broadcast synthesis."""
        
        # Split into sentences
        sentences = script.replace('.', '.\n').replace('!', '!\n').replace('?', '?\n').split('\n')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        segments = []
        current_segment = ""
        
        for sentence in sentences:
            # Check if adding sentence exceeds segment length
            if len(current_segment) + len(sentence) > segment_length and current_segment:
                # Process current segment
                result = self.processor.process_text(
                    current_segment,
                    expand_numbers=True,
                    expand_abbreviations=True,
                    process_datetime=True,
                    generate_phonemes=True
                )
                
                segments.append({
                    'segment_id': len(segments) + 1,
                    'text': result['processed'],
                    'phonemes': result['phonemes'],
                    'estimated_duration': result['word_count'] * 0.6,
                    'word_count': result['word_count']
                })
                
                current_segment = sentence
            else:
                current_segment += " " + sentence if current_segment else sentence
        
        # Process final segment
        if current_segment:
            result = self.processor.process_text(
                current_segment,
                expand_numbers=True,
                expand_abbreviations=True,
                process_datetime=True,
                generate_phonemes=True
            )
            
            segments.append({
                'segment_id': len(segments) + 1,
                'text': result['processed'],
                'phonemes': result['phonemes'],
                'estimated_duration': result['word_count'] * 0.6,
                'word_count': result['word_count']
            })
        
        return segments


class TwiEducationalProcessor:
    """Processing for educational content."""
    
    def __init__(self, dialect: str = 'asante'):
        self.processor = EnhancedTwiTextProcessor(dialect=dialect)
        
    def process_lesson_content(self, lesson_text: str, lesson_type: str = 'general') -> Dict:
        """Process educational content with appropriate settings."""
        
        # Different processing based on lesson type
        if lesson_type == 'mathematics':
            # Emphasize number processing
            result = self.processor.process_text(
                lesson_text,
                expand_numbers=True,
                expand_abbreviations=True,
                process_datetime=False,
                generate_phonemes=True
            )
        elif lesson_type == 'science':
            # Emphasize abbreviations and units
            result = self.processor.process_text(
                lesson_text,
                expand_numbers=True,
                expand_abbreviations=True,
                process_datetime=False,
                generate_phonemes=True
            )
        else:
            # General processing
            result = self.processor.process_text(
                lesson_text,
                expand_numbers=True,
                expand_abbreviations=True,
                process_datetime=True,
                generate_phonemes=True
            )
        
        return {
            'lesson_type': lesson_type,
            'processed_content': result['processed'],
            'phonemes': result['phonemes'],
            'complexity_indicators': {
                'word_count': result['word_count'],
                'character_count': result['char_count'],
                'has_twi_content': result['has_twi_chars'],
                'estimated_reading_time': result['word_count'] / 150  # words per minute
            }
        }


def demo_tts_integration():
    """Demonstrate TTS integration."""
    print("🎙️  TTS INTEGRATION DEMO")
    print("=" * 50)
    
    tts = TwiTTSPreprocessor(dialect='asante')
    
    # Sample texts for synthesis
    texts = [
        "Mema mo akwaaba! Nnɛ yɛbɛka GH₵500 ho asɛm.",
        "Dr. Mensah bɛba KNUST Monday at 10:30 AM.",
        "The weather is 25°C today with 3 people attending."
    ]
    
    for i, text in enumerate(texts, 1):
        print(f"\nText {i}: {text}")
        result = tts.preprocess_for_synthesis(text, speaker_id="speaker_001")
        print(f"Processed: {result['text'][:80]}...")
        print(f"Duration: {result['estimated_duration']:.1f}s")
        print(f"Has Twi: {result['has_twi_content']}")


def demo_asr_integration():
    """Demonstrate ASR integration."""
    print("\n🎤  ASR INTEGRATION DEMO")
    print("=" * 50)
    
    asr = TwiASRPostprocessor(dialect='asante')
    
    # Simulate ASR outputs
    asr_outputs = [
        ("me pe nkwan bi", 0.9),
        ("dr mensah ba knust monday", 0.7),
        ("gh cedi nnum ne twenty", 0.8)
    ]
    
    for text, confidence in asr_outputs:
        result = asr.postprocess_recognition(text, confidence)
        print(f"\nASR Output: {text}")
        print(f"Processed: {result['recognized_text']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Quality: {'✅' if result['quality_indicators']['likely_valid'] else '❌'}")


def demo_voice_assistant():
    """Demonstrate voice assistant integration."""
    print("\n🤖  VOICE ASSISTANT DEMO")
    print("=" * 50)
    
    assistant = TwiVoiceAssistant(dialect='asante')
    
    # Simulate conversation
    conversations = [
        ("Ɛte sɛn?", "Eye, me ho yɛ. Wo nso ɛ?"),
        ("Me pɛ nkwan.", "Nkwan bɛn na wopɛ? Yɛwɔ palmnut soup ne groundnut soup."),
        ("Palmnut soup dodoɔ sen?", "Palmnut soup yɛ GH₵25.")
    ]
    
    for user_input, assistant_response in conversations:
        # Process user input (simulated)
        user_result = assistant.asr_processor.postprocess_recognition(user_input, 0.85)
        print(f"\nUser: {user_result['recognized_text']}")
        
        # Generate response
        response_result = assistant.generate_response(user_input, assistant_response)
        print(f"Assistant: {response_result['text']}")
        print(f"Duration: {response_result['estimated_duration']:.1f}s")
    
    # Show session summary
    summary = assistant.get_dialog_summary()
    print(f"\nSession Summary: {summary['session_length']} exchanges")


def demo_broadcast_processing():
    """Demonstrate broadcast processing."""
    print("\n📻  BROADCAST PROCESSING DEMO")
    print("=" * 50)
    
    broadcaster = TwiBroadcastProcessor(dialect='asante')
    
    news_script = """
    Mema mo akwaaba wɔ nnɛ anɔpa nsɛm mu. Nnɛ ne December 25, 2024. 
    President no aka sɛ ɔbɛma GH₵500 million ama adesua mu. 
    Prof. Agyemang fi KNUST aka sɛ ɛyɛ adwene pa. 
    Weather no nso, ɔhyew no bɛyɛ 28°C bi.
    """
    
    segments = broadcaster.process_news_script(news_script, segment_length=80)
    
    for segment in segments:
        print(f"\nSegment {segment['segment_id']}:")
        print(f"Text: {segment['text'][:70]}...")
        print(f"Duration: {segment['estimated_duration']:.1f}s")
        print(f"Words: {segment['word_count']}")


def demo_educational_processing():
    """Demonstrate educational content processing."""
    print("\n📚  EDUCATIONAL PROCESSING DEMO")
    print("=" * 50)
    
    educator = TwiEducationalProcessor(dialect='asante')
    
    lessons = [
        ("Mathematics: Yɛn suban no yɛ 1 + 2 = 3. Sika no yɛ GH₵100.", "mathematics"),
        ("Science: H2O yɛ nsuo. Temperature no yɛ 25°C.", "science"),
        ("General: Nnɛ yɛ Monday. Yɛbɛkɔ KNUST.", "general")
    ]
    
    for lesson_text, lesson_type in lessons:
        result = educator.process_lesson_content(lesson_text, lesson_type)
        print(f"\n{lesson_type.upper()} Lesson:")
        print(f"Original: {lesson_text}")
        print(f"Processed: {result['processed_content'][:70]}...")
        print(f"Reading time: {result['complexity_indicators']['estimated_reading_time']:.1f} minutes")


def benchmark_performance():
    """Benchmark processing performance."""
    print("\n⚡  PERFORMANCE BENCHMARK")
    print("=" * 50)
    
    import time
    
    processor = EnhancedTwiTextProcessor()
    
    # Test texts of varying lengths
    test_texts = [
        "Me pɛ nkwan.",  # Short
        "Dr. Mensah bɛba Monday at 10:30 AM wɔ KNUST. Ɔbɛka GH₵500 ho asɛm.",  # Medium
        " ".join(["Yɛn abusuafo nyinaa bɛba afahyɛ no mu."] * 10)  # Long
    ]
    
    for i, text in enumerate(test_texts):
        start_time = time.time()
        
        # Process 100 times
        for _ in range(100):
            result = processor.process_text(text, generate_phonemes=True)
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 100
        
        print(f"\nText {i+1} ({len(text)} chars):")
        print(f"Average processing time: {avg_time*1000:.2f}ms")
        print(f"Throughput: {len(text)/avg_time:.0f} chars/sec")


def export_api_examples():
    """Export examples for API documentation."""
    print("\n📋  EXPORTING API EXAMPLES")
    print("=" * 50)
    
    examples = {
        'tts_preprocessing': {
            'description': 'Preprocess text for TTS synthesis',
            'input': 'Dr. Mensah will pay GH₵500 on Monday at 10:30.',
            'output': None  # Will be filled
        },
        'asr_postprocessing': {
            'description': 'Postprocess ASR output',
            'input': 'me pe nkwan bi',
            'output': None
        },
        'batch_processing': {
            'description': 'Process multiple texts',
            'input': ['Hello', 'Ɛte sɛn?', 'GH₵100'],
            'output': None
        }
    }
    
    # Fill in outputs
    tts = TwiTTSPreprocessor()
    asr = TwiASRPostprocessor()
    
    examples['tts_preprocessing']['output'] = tts.preprocess_for_synthesis(
        examples['tts_preprocessing']['input']
    )
    
    examples['asr_postprocessing']['output'] = asr.postprocess_recognition(
        examples['asr_postprocessing']['input'], 0.85
    )
    
    examples['batch_processing']['output'] = tts.batch_preprocess(
        examples['batch_processing']['input']
    )
    
    # Save to file
    with open('api_examples.json', 'w', encoding='utf-8') as f:
        json.dump(examples, f, indent=2, ensure_ascii=False)
    
    print("API examples saved to api_examples.json")


def main():
    """Run all integration demos."""
    print("🚀  TWII TEXT PROCESSOR - PRODUCTION INTEGRATION EXAMPLES")
    print("=" * 70)
    
    # Run all demos
    demo_tts_integration()
    demo_asr_integration()
    demo_voice_assistant()
    demo_broadcast_processing()
    demo_educational_processing()
    benchmark_performance()
    export_api_examples()
    
    print(f"\n✅  ALL INTEGRATION EXAMPLES COMPLETED")
    print("=" * 70)
    print("\nReady for production deployment! 🎉")
    print("\nIntegration points covered:")
    print("  ✅ TTS preprocessing with phonemes")
    print("  ✅ ASR postprocessing with confidence")
    print("  ✅ Voice assistant dialog management") 
    print("  ✅ Broadcast content segmentation")
    print("  ✅ Educational content processing")
    print("  ✅ Performance benchmarking")
    print("  ✅ API documentation examples")


if __name__ == '__main__':
    main()