#!/usr/bin/env python3
"""
Comprehensive test suite for Enhanced Twi Text Processor
Tests all linguistic features for production readiness
"""

import unittest
import sys
import importlib.util

# Import the module with numbered prefix
spec = importlib.util.spec_from_file_location(
    "enhanced_twi_processor", 
    "../notebooks/000_enhanced_twi_processor.py"
)
enhanced_twi_processor = importlib.util.module_from_spec(spec)
sys.modules['enhanced_twi_processor'] = enhanced_twi_processor
spec.loader.exec_module(enhanced_twi_processor)

from enhanced_twi_processor import (
    TwiNumberProcessor, 
    TwiPhonemeMapper,
    TwiDateTimeProcessor,
    TwiAbbreviationExpander,
    EnhancedTwiTextProcessor
)


class TestTwiNumberProcessor(unittest.TestCase):
    """Test Twi number conversion system."""
    
    def setUp(self):
        self.processor = TwiNumberProcessor()
    
    def test_basic_units(self):
        """Test numbers 0-10."""
        self.assertEqual(self.processor.convert_number(0), 'hwee')
        self.assertEqual(self.processor.convert_number(1), 'baako')
        self.assertEqual(self.processor.convert_number(5), 'nnum')
        self.assertEqual(self.processor.convert_number(10), 'edu')
    
    def test_teens(self):
        """Test numbers 11-19."""
        self.assertEqual(self.processor.convert_number(11), 'dubaako')
        self.assertEqual(self.processor.convert_number(15), 'dunum')
        self.assertEqual(self.processor.convert_number(19), 'dunkron')
    
    def test_tens(self):
        """Test multiples of 10."""
        self.assertEqual(self.processor.convert_number(20), 'aduonu')
        self.assertEqual(self.processor.convert_number(50), 'aduonum')
        self.assertEqual(self.processor.convert_number(90), 'aduɔkron')
    
    def test_compound_numbers(self):
        """Test compound numbers (e.g., 25, 47, 89)."""
        self.assertEqual(self.processor.convert_number(25), 'aduonu ne nnum')
        self.assertEqual(self.processor.convert_number(47), 'aduanan ne nson')
        self.assertEqual(self.processor.convert_number(89), 'aduɔwɔtwe ne nkron')
    
    def test_hundreds(self):
        """Test hundreds."""
        self.assertEqual(self.processor.convert_number(100), 'ɔha')
        self.assertEqual(self.processor.convert_number(300), 'ahansa')
        self.assertEqual(self.processor.convert_number(567), 
                        'ahanum ne aduosia ne nson')
    
    def test_thousands(self):
        """Test thousands."""
        self.assertEqual(self.processor.convert_number(1000), 'apem')
        self.assertEqual(self.processor.convert_number(2500), 
                        'mmienu apem ne ahanum')
        self.assertEqual(self.processor.convert_number(9876),
                        'nkron apem ne ahanwɔtwe ne aduɔson ne nsia')
    
    def test_large_numbers(self):
        """Test large numbers (>10,000)."""
        self.assertEqual(self.processor.convert_number(10000), 'mpem edu')
        self.assertEqual(self.processor.convert_number(50000), 'mpem nnum')  # 50000 = 5 * 10000 = mpem nnum
        self.assertEqual(self.processor.convert_number(1000000), 'ɔpepem')  # 1 million
    
    def test_currency_ghc(self):
        """Test Ghana Cedi conversion."""
        result = self.processor.process_currency('GH₵100')
        self.assertIn('ɔha Ghana sidi', result)
        
        result = self.processor.process_currency('GH₵250.50')
        self.assertIn('Ghana sidi', result)
        self.assertIn('pesewa', result)
    
    def test_currency_dollars(self):
        """Test US Dollar conversion."""
        result = self.processor.process_currency('$500')
        self.assertIn('ahanum Amerika dɔla', result)
        
    def test_process_mixed_text(self):
        """Test processing text with multiple numbers."""
        text = "I have 5 books and 20 pens"
        result = self.processor.process_all_numbers(text)
        self.assertIn('nnum', result)
        self.assertIn('aduonu', result)


class TestTwiPhonemeMapper(unittest.TestCase):
    """Test IPA phoneme mapping."""
    
    def setUp(self):
        self.mapper = TwiPhonemeMapper()
    
    def test_basic_vowels(self):
        """Test vowel phoneme mapping."""
        self.assertEqual(self.mapper.word_to_phoneme('a'), 'a')
        self.assertEqual(self.mapper.word_to_phoneme('ɛ'), 'ɛ')
        self.assertEqual(self.mapper.word_to_phoneme('ɔ'), 'ɔ')
    
    def test_nasalized_vowels(self):
        """Test nasalized vowel mapping."""
        self.assertEqual(self.mapper.word_to_phoneme('ã'), 'ã')
        self.assertEqual(self.mapper.word_to_phoneme('ɛ̃'), 'ɛ̃')
        self.assertEqual(self.mapper.word_to_phoneme('ɔ̃'), 'ɔ̃')
    
    def test_consonant_clusters(self):
        """Test special consonant cluster mapping."""
        self.assertEqual(self.mapper.word_to_phoneme('kya'), 'tɕa')
        self.assertEqual(self.mapper.word_to_phoneme('gya'), 'dʑa')
        self.assertEqual(self.mapper.word_to_phoneme('twa'), 'tʷa')
        self.assertEqual(self.mapper.word_to_phoneme('nya'), 'ɲa')
    
    def test_complex_words(self):
        """Test phoneme mapping for complex words."""
        # Test word with cluster and special vowels
        result = self.mapper.word_to_phoneme('kyerɛ')
        self.assertIn('tɕ', result)
        self.assertIn('ɛ', result)
        
        # Test word with multiple features
        result = self.mapper.word_to_phoneme('hwɛ')
        self.assertIn('hʷ', result)
        self.assertIn('ɛ', result)
    
    def test_full_text(self):
        """Test phoneme conversion for full text."""
        text = "me din de kofi"
        result = self.mapper.text_to_phonemes(text)
        words = result.split()
        self.assertEqual(len(words), 4)


class TestTwiDateTimeProcessor(unittest.TestCase):
    """Test date and time processing."""
    
    def setUp(self):
        self.processor = TwiDateTimeProcessor()
    
    def test_days_of_week(self):
        """Test day name conversion."""
        result = self.processor.process_all("Monday")
        self.assertIn('Dwowda', result)
        
        result = self.processor.process_all("Friday")
        self.assertIn('Fida', result)
        
        result = self.processor.process_all("Sunday")
        self.assertIn('Kwesida', result)
    
    def test_months(self):
        """Test month name conversion."""
        result = self.processor.process_all("January")
        self.assertIn('Ɔpɛpɔn', result)
        
        result = self.processor.process_all("December")
        self.assertIn('Mfufuoɔpɛpɔn', result)
    
    def test_time_periods(self):
        """Test time period conversion."""
        result = self.processor.process_time("10:30 AM")
        self.assertIn('anɔpa', result)
        self.assertIn('dɔn edu', result)
        
        result = self.processor.process_time("3:00 PM")
        self.assertIn('dɔn mmiɛnsa', result)  # 3 o'clock
        
        result = self.processor.process_time("8:00 PM")
        self.assertIn('dɔn nwɔtwe', result)  # 8 o'clock
    
    def test_date_formats(self):
        """Test various date format conversions."""
        # Test month name conversion
        result = self.processor.process_date("December 25, 2024")
        self.assertIn('Mfufuoɔpɛpɔn', result)
        
        # Test with full processing
        result = self.processor.process_all("December 25, 2024")
        self.assertIn('Mfufuoɔpɛpɔn', result)
    
    def test_mixed_datetime(self):
        """Test mixed date and time expressions."""
        text = "Meet on Monday at 10:00 AM"
        result = self.processor.process_all(text)
        self.assertIn('Dwowda', result)
        self.assertIn('anɔpa', result)


class TestTwiAbbreviationExpander(unittest.TestCase):
    """Test abbreviation expansion."""
    
    def setUp(self):
        self.expander = TwiAbbreviationExpander()
    
    def test_titles(self):
        """Test title expansion."""
        self.assertIn("Dokota", self.expander.expand_all("Dr. Smith"))
        self.assertIn("Owura", self.expander.expand_all("Mr. Jones"))
        self.assertIn("Awura", self.expander.expand_all("Mrs. Brown"))
        self.assertIn("Ɔbenfo", self.expander.expand_all("Prof. Davis"))
    
    def test_organizations(self):
        """Test organization name expansion."""
        result = self.expander.expand_all("NPP meeting")
        self.assertIn('Pi Pi', result)
        
        result = self.expander.expand_all("NDC conference")
        self.assertIn('Di Si', result)
        
        result = self.expander.expand_all("KNUST campus")
        self.assertIn('Kwame Nkrumah', result)
    
    def test_measurement_units(self):
        """Test measurement unit expansion."""
        result = self.expander.expand_all("10 kg")
        self.assertIn('kilogram', result)
        
        result = self.expander.expand_all("5 km")
        self.assertIn('kilomita', result)
    
    def test_mixed_text(self):
        """Test text with multiple abbreviations."""
        text = "Dr. Mensah from KNUST weighs 70 kg"
        result = self.expander.expand_all(text)
        self.assertIn('Dokota', result)
        self.assertIn('kilogram', result)


class TestEnhancedTwiTextProcessor(unittest.TestCase):
    """Test complete text processing pipeline."""
    
    def setUp(self):
        self.processor = EnhancedTwiTextProcessor(dialect='asante')
    
    def test_complete_processing(self):
        """Test full pipeline processing."""
        text = "Dr. Mensah paid GH₵500 on Monday at 10:30 AM"
        result = self.processor.process_text(text)
        
        self.assertIsNotNone(result['processed'])
        self.assertIn('Dokota', result['processed'])
        self.assertIn('ahanum Ghana sidi', result['processed'])
        self.assertIn('Dwowda', result['processed'])
        self.assertIn('anɔpa', result['processed'])
    
    def test_twi_char_detection(self):
        """Test Twi character detection."""
        text_with_twi = "Ɛte sɛn? Ɔdɔ ne me."
        result = self.processor.process_text(text_with_twi)
        self.assertTrue(result['has_twi_chars'])
        
        text_without_twi = "Hello, how are you?"
        result = self.processor.process_text(text_without_twi)
        self.assertFalse(result['has_twi_chars'])
    
    def test_phoneme_generation(self):
        """Test phoneme generation option."""
        text = "Akwaaba, me din de Kofi"
        result = self.processor.process_text(text, generate_phonemes=True)
        
        self.assertIsNotNone(result['phonemes'])
        self.assertIn(' ', result['phonemes'])  # Should have word separators
    
    def test_dialect_variations(self):
        """Test different dialect processing."""
        text = "The meeting is tomorrow"
        
        # Test Asante dialect
        processor_asante = EnhancedTwiTextProcessor(dialect='asante')
        result_asante = processor_asante.process_text(text)
        
        # Test Akuapem dialect
        processor_akuapem = EnhancedTwiTextProcessor(dialect='akuapem')
        result_akuapem = processor_akuapem.process_text(text)
        
        # Both should process but may have variations
        self.assertIsNotNone(result_asante['processed'])
        self.assertIsNotNone(result_akuapem['processed'])
        self.assertEqual(result_asante['dialect'], 'asante')
        self.assertEqual(result_akuapem['dialect'], 'akuapem')
    
    def test_statistics(self):
        """Test text statistics generation."""
        text = "This is a test sentence with several words."
        result = self.processor.process_text(text)
        
        self.assertIsNotNone(result['word_count'])
        self.assertIsNotNone(result['char_count'])
        self.assertGreater(result['word_count'], 0)
        self.assertGreater(result['char_count'], 0)
    
    def test_selective_processing(self):
        """Test selective feature processing."""
        text = "Dr. Smith has 5 books on Monday"
        
        # Process with all features
        result_all = self.processor.process_text(
            text,
            expand_numbers=True,
            expand_abbreviations=True,
            process_datetime=True
        )
        self.assertIn('Dokota', result_all['processed'])
        self.assertIn('nnum', result_all['processed'])
        self.assertIn('Dwowda', result_all['processed'])
        
        # Process with only numbers
        result_numbers = self.processor.process_text(
            text,
            expand_numbers=True,
            expand_abbreviations=False,
            process_datetime=False
        )
        self.assertIn('nnum', result_numbers['processed'])
        self.assertIn('Dr.', result_numbers['processed'])  # Not expanded
        self.assertIn('Monday', result_numbers['processed'])  # Not converted
    
    def test_complex_real_world_text(self):
        """Test complex real-world scenarios."""
        text = """Dr. Akosua Mensah will charge $100 or GH₵500 for consultation 
                  on Tuesday, December 25, 2024 at 2:30 PM. 
                  Call 0244123456 for appointment at KNUST."""
        
        result = self.processor.process_text(text, generate_phonemes=True)
        
        # Check all features were processed
        self.assertIn('Dokota', result['processed'])
        self.assertIn('Ghana sidi', result['processed'])
        self.assertIn('Benada', result['processed'])
        self.assertIn('Mfufuoɔpɛpɔn', result['processed'])  # December
        self.assertIsNotNone(result['phonemes'])
    
    def test_code_mixing_detection(self):
        """Test detection of code-mixed text."""
        # Pure Twi
        pure_twi = "Ɛte sɛn? Me pɛ nkwan."
        result = self.processor.process_text(pure_twi)
        self.assertTrue(result['has_twi_chars'])
        
        # Mixed Twi-English
        mixed = "Please kyerɛ me the way to Kumasi"
        result = self.processor.process_text(mixed)
        # Should still process successfully
        self.assertIsNotNone(result['processed'])
    
    def test_error_handling(self):
        """Test error handling for edge cases."""
        # Empty string
        result = self.processor.process_text("")
        self.assertEqual(result['processed'], "")
        
        # Very long number
        text = "The amount is 999999999"
        result = self.processor.process_text(text)
        self.assertIsNotNone(result['processed'])
        
        # Invalid characters
        text = "Test with symbols @#$%^&*()"
        result = self.processor.process_text(text)
        self.assertIsNotNone(result['processed'])


class TestIntegration(unittest.TestCase):
    """Integration tests for production scenarios."""
    
    def test_news_broadcast_text(self):
        """Test processing for news broadcast scenario."""
        processor = EnhancedTwiTextProcessor()
        text = """Good morning, this is the 7:00 AM news on Monday, January 15, 2024.
                  The President announced a GH₵500 million budget for education.
                  Prof. Agyemang from KNUST praised the initiative."""
        
        result = processor.process_text(text, generate_phonemes=True)
        
        # Should have all conversions
        self.assertIn('anɔpa', result['processed'])
        self.assertIn('Dwowda', result['processed'])
        self.assertIn('Ghana sidi', result['processed'])
        self.assertIn('Ɔbenfo', result['processed'])  # Prof.
        self.assertIsNotNone(result['phonemes'])
    
    def test_customer_service_dialog(self):
        """Test processing for customer service scenario."""
        processor = EnhancedTwiTextProcessor()
        dialog = """Customer: I want to pay GH₵250 for 3 items.
                   Agent: That will be ready by 2:30 PM on Friday.
                   Customer: Can I pay $50 instead?"""
        
        result = processor.process_text(dialog)
        
        self.assertIn('Ghana sidi', result['processed'])
        self.assertIn('mmiɛnsa', result['processed'])
        self.assertIn('Fida', result['processed'])
        self.assertIn('Amerika dɔla', result['processed'])
    
    def test_educational_content(self):
        """Test processing for educational content."""
        processor = EnhancedTwiTextProcessor()
        content = """Chapter 5: Mathematics
                    Today we will learn about numbers from 1 to 100.
                    Exercise: Convert 25, 50, 75, and 100 to Twi."""
        
        result = processor.process_text(content)
        
        self.assertIn('nnum', result['processed'])  # 5
        self.assertIn('baako', result['processed'])  # 1
        self.assertIn('ɔha', result['processed'])  # 100
        self.assertIn('aduonu ne nnum', result['processed'])  # 25


class TestPerformance(unittest.TestCase):
    """Test performance and efficiency."""
    
    def test_large_text_processing(self):
        """Test processing of large texts."""
        processor = EnhancedTwiTextProcessor()
        
        # Create a large text with repeated patterns
        large_text = " ".join([
            f"Item {i} costs GH₵{i*10} on day {i}."
            for i in range(1, 101)
        ])
        
        result = processor.process_text(large_text)
        
        self.assertIsNotNone(result['processed'])
        self.assertGreater(len(result['processed']), len(large_text))
    
    def test_unicode_handling(self):
        """Test handling of various Unicode characters."""
        processor = EnhancedTwiTextProcessor()
        
        # Text with various Unicode characters
        unicode_text = "Ɛyɛ dɛn? 你好 مرحبا ñoño café"
        result = processor.process_text(unicode_text)
        
        self.assertIsNotNone(result['processed'])
        self.assertTrue(result['has_twi_chars'])


# Run tests
if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestTwiNumberProcessor))
    suite.addTests(loader.loadTestsFromTestCase(TestTwiPhonemeMapper))
    suite.addTests(loader.loadTestsFromTestCase(TestTwiDateTimeProcessor))
    suite.addTests(loader.loadTestsFromTestCase(TestTwiAbbreviationExpander))
    suite.addTests(loader.loadTestsFromTestCase(TestEnhancedTwiTextProcessor))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))
    
    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFAILED TESTS:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\nERROR TESTS:")
        for test, traceback in result.errors:
            print(f"  - {test}")