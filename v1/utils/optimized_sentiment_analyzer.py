"""
Optimized Sentiment Analyzer for Large Datasets
==================================================

Solusi komprehensif untuk meningkatkan akurasi dan performa pada dataset besar:
- Set-based lookup untuk O(1) complexity
- Adaptive thresholds berdasarkan karakteristik dataset
- Batch/vectorized processing
- Dynamic lexicon expansion
- Pattern recognition untuk spam/sarcasm
- Memory-efficient implementation
- Multi-stage analysis pipeline

Author: Enhanced Tokopedia Sentiment Analysis System
Version: 3.0 (Optimized for Large Datasets)
"""

import os
import re
import json
import pandas as pd
import numpy as np
from collections import Counter
from typing import Dict, List, Tuple, Optional, Union
import warnings
warnings.filterwarnings('ignore')

class RobustPatternMatcher:
    """Enhanced pattern matcher for large datasets"""
    
    def __init__(self):
        self.spam_patterns = [
            r'^test\s*$',
            r'^tes\s*$', 
            r'^ok\s*$',
            r'^\.+$',
            r'^\d+$',
            r'^-+$',
            r'^\w{1,2}$',  # Very short words
            r'^[.,!?]+$',  # Only punctuation
            r'^(bagus|jelek|mantap|ok|oke|baik|buruk)\s*$'  # Single word reviews
        ]
        
        # Sarcasm indicators
        self.sarcasm_patterns = [
            r'mantap.*kecewa',
            r'bagus.*tapi.*jelek',
            r'recommended.*not',
            r'puas.*banget.*\(bohong\)',
            r'keren.*banget.*\(sarkastik\)',
            r'worth.*it.*banget.*tapi.*jelek',
            r'good.*job.*\(ironis\)',
            r'sempurna.*\(bukan\)',
            r'amazing.*\(bohong\)'
        ]
        
        # Complaint patterns yang lebih spesifik
        self.complaint_patterns = [
            r'tidak.*sesuai.*ekspektasi',
            r'mengecewakan.*sekali',
            r'sangat.*tidak.*puas',
            r'menyesal.*beli',
            r'rugi.*beli.*ini',
            r'jangan.*beli.*ini',
            r'tidak.*recommended',
            r'waste.*of.*money',
            r'totally.*disappointed',
            r'very.*unsatisfied'
        ]
        
        self.compile_patterns()
    
    def compile_patterns(self):
        """Pre-compile all regex patterns for efficiency"""
        self.compiled_spam = [re.compile(pattern, re.IGNORECASE) for pattern in self.spam_patterns]
        self.compiled_sarcasm = [re.compile(pattern, re.IGNORECASE) for pattern in self.sarcasm_patterns]
        self.compiled_complaint = [re.compile(pattern, re.IGNORECASE) for pattern in self.complaint_patterns]
    
    def detect_spam_review(self, text: str) -> bool:
        """Detect spam or low-quality reviews"""
        if len(text.strip()) < 5:
            return True
            
        # Check for repetitive characters
        if len(set(text.lower())) < 3:
            return True
            
        for pattern in self.compiled_spam:
            if pattern.match(text.lower().strip()):
                return True
                
        return False
    
    def detect_sarcasm(self, text: str, sentiment_score: float, rating: int = None) -> bool:
        """Detect potential sarcasm"""
        for pattern in self.compiled_sarcasm:
            if pattern.search(text.lower()):
                return True
                
        # High positive score with low rating might be sarcasm
        if rating and sentiment_score > 2 and rating <= 2:
            return True
            
        # Check for excessive positivity with negative context
        if sentiment_score > 3 and any(word in text.lower() for word in ['tapi', 'namun', 'sayangnya', 'cuma', 'cm']):
            return True
            
        return False
    
    def detect_complaint(self, text: str) -> bool:
        """Detect complaint patterns"""
        for pattern in self.compiled_complaint:
            if pattern.search(text.lower()):
                return True
        return False


class OptimizedSentimentAnalyzer:
    """Optimized sentiment analyzer for large datasets with cultural context awareness"""
    
    def __init__(self):
        print("🚀 Initializing OptimizedSentimentAnalyzer with Cultural Context...")
        
        # Load lexicon
        self.lexicon = self.load_lexicon()
        
        # Handle nested structure if present
        positive_words = []
        negative_words = []
        
        if 'positive' in self.lexicon:
            if isinstance(self.lexicon['positive'], dict):
                # Nested structure - flatten all positive categories
                for category, words in self.lexicon['positive'].items():
                    if isinstance(words, list):
                        positive_words.extend(words)
            elif isinstance(self.lexicon['positive'], list):
                # Simple list structure
                positive_words = self.lexicon['positive']
        
        if 'negative' in self.lexicon:
            if isinstance(self.lexicon['negative'], dict):
                # Nested structure - flatten all negative categories
                for category, words in self.lexicon['negative'].items():
                    if isinstance(words, list):
                        negative_words.extend(words)
            elif isinstance(self.lexicon['negative'], list):
                # Simple list structure
                negative_words = self.lexicon['negative']
        
        # Convert lists to sets for O(1) lookup
        self.positive_words = set(positive_words)
        self.negative_words = set(negative_words)
        self.contrast_words = set(self.lexicon.get('contrast_words', []))
        self.complaint_phrases = set(self.lexicon.get('complaint_phrases', []))
        
        # CULTURAL CONTEXT: Strong positive indicators (syukur, terima kasih, etc.)
        self.strong_positive_indicators = {
            'alhamdulillah', 'syukur', 'puji tuhan', 'terima kasih', 'makasih',
            'thanks', 'thank you', 'trimakasih', 'mksh', 'thx', 'tks',
            'grateful', 'bersyukur', 'blessed', 'berkah', 'barakallah',
            'perfect', 'sempurna', 'amazing', 'luar biasa', 'incredible',
            'excellent', 'outstanding', 'fantastic', 'wonderful', 'brilliant'
        }
        
        # PHRASE-BASED POSITIVE NEGATION: "no cacat", "ga kecewa", etc.
        self.positive_negation_phrases = {
            'no cacat', 'tidak cacat', 'ga cacat', 'gak cacat',
            'no kecewa', 'tidak kecewa', 'ga kecewa', 'gak kecewa', 'nggak kecewa',
            'no penyok', 'tidak penyok', 'ga penyok', 'gak penyok',
            'no lecet', 'tidak lecet', 'ga lecet', 'gak lecet',
            'no rusak', 'tidak rusak', 'ga rusak', 'gak rusak',
            'no masalah', 'tidak ada masalah', 'ga ada masalah', 'gak ada masalah',
            'no complain', 'tidak complain', 'ga complain', 'gak complain',
            'no complaint', 'tidak complaint', 'ga complaint', 'gak complaint',
            'tanpa cacat', 'tanpa penyok', 'tanpa lecet', 'tanpa rusak',
            'bebas cacat', 'bebas penyok', 'bebas lecet', 'bebas rusak'
        }
        
        # CONTEXT-AWARE NEGATION WORDS: kata-kata yang bisa positif jika ada negasi
        self.context_negative_words = {
            'kecewa', 'disappointed', 'complain', 'complaint', 'menyesal',
            'cacat', 'defect', 'rusak', 'broken', 'jelek', 'bad',
            'penyok', 'dent', 'lecet', 'scratch', 'buruk', 'awful',
            'masalah', 'problem', 'issue', 'trouble', 'error'
        }
        
        # TYPO CORRECTION ENHANCEMENTS: untuk mengatasi typo seperti "sampah tujuan" → "sampai tujuan"
        self.advanced_typo_corrections = {
            'sampah tujuan': 'sampai tujuan',
            'sampah rumah': 'sampai rumah',
            'sampah tempat': 'sampai tempat',
            'sampah lokasi': 'sampai lokasi',
            'sampah alamat': 'sampai alamat',
            'dateng': 'datang',
            'nympe': 'nyampe',
            'nyampe': 'sampai',
            'pket': 'paket',
            'brng': 'barang',
            'kualtas': 'kualitas',
            'harganya': 'harga',
            'barangnya': 'barang',
            'packaging': 'packing',
            'packing nya': 'packingnya',
            'kualitasnya': 'kualitas'
        }
        
        # Emoji mappings
        self.emoji_mapping = self.lexicon.get('emoji_mapping', {})
        self.slang_normalization = self.lexicon.get('slang_normalization', {})
        
        # Temporary expanded lexicon (for large datasets)
        self.temp_positive_words = set()
        self.temp_negative_words = set()
        
        # Cache for processed texts
        self.cache = {}
        self.cache_size = 10000
        
        # Pre-compile regex patterns
        self.compile_patterns()
        
        # Initialize pattern matcher
        self.pattern_matcher = RobustPatternMatcher()
        
        # Default thresholds (will be adjusted adaptively)
        self.positive_threshold = 1.0
        self.negative_threshold = -1.0
        self.confidence_threshold = 0.5
        
        # Progress callback
        self.progress_callback = None
        
        print("✅ OptimizedSentimentAnalyzer initialized successfully")
    
    def load_lexicon(self) -> Dict:
        """Load sentiment lexicon"""
        lexicon_path = os.path.join(os.path.dirname(__file__), 'sentiment_lexicon.json')
        
        try:
            with open(lexicon_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ Lexicon file not found: {lexicon_path}")
            return self.get_default_lexicon()
        except Exception as e:
            print(f"⚠️ Error loading lexicon: {e}")
            return self.get_default_lexicon()
    
    def get_default_lexicon(self) -> Dict:
        """Default lexicon if file not found"""
        return {
            'positive': ['bagus', 'baik', 'mantap', 'oke', 'suka', 'puas', 'recommended', 'worth'],
            'negative': ['jelek', 'buruk', 'kecewa', 'tidak', 'benci', 'mahal', 'lama', 'rusak'],
            'contrast_words': ['tapi', 'namun', 'sayangnya', 'cuma', 'cm', 'hanya', 'sayang'],
            'complaint_phrases': ['tidak sesuai', 'mengecewakan', 'tidak puas', 'menyesal beli'],
            'emoji_mapping': {'😊': 'senang', '😢': 'sedih', '😡': 'marah', '👍': 'bagus', '👎': 'jelek'},
            'slang_normalization': {'bgus': 'bagus', 'mantep': 'mantap', 'jelek': 'jelek'}
        }
    
    def compile_patterns(self):
        """Pre-compile all regex patterns for efficiency"""
        self.typo_patterns = {
            r'b+a+g+u+s+': 'bagus',
            r'm+a+n+t+a+p+': 'mantap',
            r'j+e+l+e+k+': 'jelek',
            r'o+k+e+': 'oke',
            r'l+a+m+a+': 'lama',
            r'k+e+r+e+n+': 'keren',
            r'b+u+r+u+k+': 'buruk',
            r'r+u+s+a+k+': 'rusak',
            r'p+u+a+s+': 'puas',
            r'k+e+c+e+w+a+': 'kecewa'
        }
        
        self.compiled_patterns = {
            pattern: re.compile(pattern, re.IGNORECASE) 
            for pattern in self.typo_patterns
        }
        
        # Negation patterns
        self.negation_pattern = re.compile(r'\b(tidak|jangan|bukan|belum|ga|gak|nggak|enggak)\b', re.IGNORECASE)
        
        # Intensifier patterns
        self.intensifier_pattern = re.compile(r'\b(sangat|banget|sekali|amat|bener|bgt|paling|super|ultra)\b', re.IGNORECASE)
    
    def calculate_adaptive_thresholds(self, df_sample: pd.DataFrame):
        """Calculate thresholds based on dataset characteristics"""
        print("📊 Calculating adaptive thresholds...")
        
        # Analyze a sample to understand distribution
        sample_size = min(1000, len(df_sample))
        if len(df_sample) > sample_size:
            sample = df_sample.sample(n=sample_size, random_state=42)
        else:
            sample = df_sample
        
        # Calculate text length distribution
        text_lengths = sample['Ulasan'].fillna('').str.len()
        avg_length = text_lengths.mean()
        
        # Adjust thresholds based on text characteristics
        if avg_length < 50:  # Short reviews
            self.positive_threshold = 0.5
            self.negative_threshold = -0.5
        elif avg_length < 100:  # Medium reviews
            self.positive_threshold = 1.0
            self.negative_threshold = -1.0
        else:  # Long reviews
            self.positive_threshold = 2.0
            self.negative_threshold = -2.0
        
        # Adjust for rating distribution
        if 'Rating' in sample.columns:
            rating_dist = sample['Rating'].value_counts(normalize=True)
            
            # If dataset is highly skewed positive (many 5-star ratings)
            if rating_dist.get(5, 0) > 0.6:
                self.positive_threshold *= 0.8
                self.negative_threshold *= 1.2
            
            # If dataset has many negative ratings
            elif rating_dist.get(1, 0) > 0.3:
                self.negative_threshold *= 0.8
                self.positive_threshold *= 1.2
        
        # Adjust confidence threshold based on dataset size
        if len(df_sample) > 10000:
            self.confidence_threshold = 0.3  # Lower confidence for large datasets
        else:
            self.confidence_threshold = 0.5
        
        print(f"✅ Adaptive thresholds set:")
        print(f"   Positive threshold: {self.positive_threshold}")
        print(f"   Negative threshold: {self.negative_threshold}")
        print(f"   Confidence threshold: {self.confidence_threshold}")
    
    def expand_lexicon_dynamically(self, df: pd.DataFrame):
        """Expand lexicon based on dataset patterns"""
        print("🔄 Expanding lexicon dynamically...")
        
        if 'Rating' not in df.columns:
            print("⚠️ No Rating column found, skipping lexicon expansion")
            return
        
        # Find high-rated and low-rated reviews
        high_rated = df[df['Rating'] >= 5]['Ulasan'].fillna('')
        low_rated = df[df['Rating'] <= 2]['Ulasan'].fillna('')
        
        def get_frequent_unknown_words(texts, existing_words, top_n=50):
            """Extract frequent words not in existing lexicon"""
            all_words = []
            for text in texts:
                # Clean and split text
                clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
                words = clean_text.split()
                all_words.extend([w for w in words if len(w) > 3])
            
            word_freq = Counter(all_words)
            
            # Filter out existing words and get frequent unknowns
            unknown_frequent = [
                word for word, count in word_freq.most_common(top_n * 2)
                if word not in existing_words and count > 10 and len(word) > 3
            ]
            
            return unknown_frequent[:top_n]
        
        # Get all existing words
        all_existing = self.positive_words | self.negative_words
        
        # Find candidate words
        positive_candidates = get_frequent_unknown_words(high_rated, all_existing)
        negative_candidates = get_frequent_unknown_words(low_rated, all_existing)
        
        # Add to temporary lexicon
        self.temp_positive_words = set(positive_candidates)
        self.temp_negative_words = set(negative_candidates)
        
        print(f"✅ Dynamic lexicon expansion completed:")
        print(f"   Added {len(positive_candidates)} temporary positive words")
        print(f"   Added {len(negative_candidates)} temporary negative words")
        
        if positive_candidates:
            print(f"   Sample positive: {positive_candidates[:10]}")
        if negative_candidates:
            print(f"   Sample negative: {negative_candidates[:10]}")
    
    def normalize_text_optimized(self, text: str) -> str:
        """Optimized text normalization"""
        if not text or pd.isna(text):
            return ""
        
        text = str(text).lower().strip()
        
        # Apply typo correction using pre-compiled patterns
        for pattern, replacement in self.typo_patterns.items():
            text = self.compiled_patterns[pattern].sub(replacement, text)
        
        # Apply slang normalization
        for slang, normal in self.slang_normalization.items():
            text = text.replace(slang, normal)
        
        # Apply emoji normalization
        for emoji, meaning in self.emoji_mapping.items():
            text = text.replace(emoji, f' {meaning} ')
        
        return text
    
    def apply_advanced_typo_correction(self, text: str) -> str:
        """Apply advanced typo corrections for cultural context and common errors"""
        if not text or pd.isna(text):
            return ""
        
        text = str(text).lower().strip()
        
        # Apply advanced typo corrections
        for typo, correction in self.advanced_typo_corrections.items():
            text = text.replace(typo, correction)
        
        # Additional pattern-based corrections
        text = re.sub(r'\bsampah\s+(tujuan|rumah|tempat|lokasi|alamat)\b', r'sampai \1', text)
        text = re.sub(r'\bbrng\b', 'barang', text)
        text = re.sub(r'\bpket\b', 'paket', text)
        text = re.sub(r'\bkualtas\b', 'kualitas', text)
        
        return text
    
    def extract_features_optimized(self, text: str, rating: int = None) -> Dict:
        """Extract features from text with optimized approach and cultural context awareness"""
        
        # Apply advanced typo correction first
        corrected_text = self.apply_advanced_typo_correction(text)
        
        # Normalize text
        normalized_text = self.normalize_text_optimized(corrected_text)
        words = normalized_text.split()
        
        # === CULTURAL CONTEXT DETECTION ===
        # 1. Strong positive indicators (Alhamdulillah, syukur, terima kasih, etc.)
        strong_positive_found = any(indicator in normalized_text for indicator in self.strong_positive_indicators)
        strong_positive_count = sum(1 for indicator in self.strong_positive_indicators if indicator in normalized_text)
        
        # 2. Positive negation phrases (no cacat, ga kecewa, etc.)
        positive_negation_found = any(phrase in normalized_text for phrase in self.positive_negation_phrases)
        positive_negation_phrases = [phrase for phrase in self.positive_negation_phrases if phrase in normalized_text]
        
        # 3. Context-aware negative word detection
        context_negative_count = 0
        negated_negative_count = 0  # Negative words that are negated (should be positive)
        
        for word in words:
            if word in self.context_negative_words:
                # Check if this negative word is preceded by negation
                word_index = normalized_text.find(word)
                if word_index > 0:
                    preceding_text = normalized_text[:word_index].split()[-3:]  # Check last 3 words
                    if any(neg in ' '.join(preceding_text) for neg in ['tidak', 'ga', 'gak', 'no', 'tanpa', 'bebas']):
                        negated_negative_count += 1  # This should be positive
                    else:
                        context_negative_count += 1
                else:
                    context_negative_count += 1
        
        # === STANDARD SENTIMENT ANALYSIS ===
        # Initialize counters
        positive_count = 0
        negative_count = 0
        
        # Count using O(1) set lookups (excluding context-aware negative words)
        for word in words:
            if word in self.positive_words or word in self.temp_positive_words:
                positive_count += 1
            elif word in self.negative_words or word in self.temp_negative_words:
                # Don't count if it's a context-negative word that's been handled above
                if word not in self.context_negative_words:
                    negative_count += 1
        
        # Add context-aware negative count to standard negative count
        negative_count += context_negative_count
        
        # Check for patterns
        has_contrast = any(word in self.contrast_words for word in words)
        has_complaint = self.pattern_matcher.detect_complaint(text)
        is_spam = self.pattern_matcher.detect_spam_review(text)
        
        # Check for negation
        negation_matches = self.negation_pattern.findall(text)
        has_negation = len(negation_matches) > 0
        
        # Check for intensifiers
        intensifier_matches = self.intensifier_pattern.findall(text)
        intensifier_count = len(intensifier_matches)
        
        # === PRIORITY-BASED SENTIMENT CALCULATION ===
        # Start with standard score
        base_score = positive_count - negative_count
        
        # Add points for negated negative words (these are actually positive)
        base_score += negated_negative_count * 2
        
        # Apply cultural context adjustments
        cultural_boost = 0
        if strong_positive_found:
            cultural_boost += strong_positive_count * 3  # Strong boost for cultural positive indicators
        
        if positive_negation_found:
            cultural_boost += len(positive_negation_phrases) * 2  # Boost for positive negation phrases
        
        # Apply cultural boost
        base_score += cultural_boost
        
        # Apply standard logic adjustments
        if has_negation and not positive_negation_found:  # Don't reverse if positive negation is found
            base_score *= -0.8  # Reverse and reduce intensity
        
        # Apply intensifier
        if intensifier_count > 0:
            base_score *= (1 + intensifier_count * 0.2)
        
        # Apply contrast penalty (reduced if cultural positives are present)
        if has_contrast:
            contrast_penalty = 0.6 if not strong_positive_found else 0.8
            base_score *= contrast_penalty
        
        # Apply complaint penalty (reduced if cultural positives are present)
        if has_complaint:
            complaint_penalty = 2 if not strong_positive_found else 1
            base_score -= complaint_penalty
        
        # Check for sarcasm
        is_sarcastic = self.pattern_matcher.detect_sarcasm(text, base_score, rating)
        if is_sarcastic and not strong_positive_found:  # Don't reverse if strong positive indicators
            base_score *= -0.5  # Reverse sarcastic sentiment
        
        return {
            'base_score': base_score,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'context_negative_count': context_negative_count,
            'negated_negative_count': negated_negative_count,
            'strong_positive_found': strong_positive_found,
            'strong_positive_count': strong_positive_count,
            'positive_negation_found': positive_negation_found,
            'positive_negation_phrases': positive_negation_phrases,
            'cultural_boost': cultural_boost,
            'has_contrast': has_contrast,
            'has_complaint': has_complaint,
            'has_negation': has_negation,
            'intensifier_count': intensifier_count,
            'is_spam': is_spam,
            'is_sarcastic': is_sarcastic,
            'text_length': len(text),
            'word_count': len(words),
            'corrected_text': corrected_text != text  # Flag if text was corrected
        }
    
    def calculate_sentiment_optimized(self, features: Dict, rating: int = None) -> Dict:
        """Calculate sentiment with optimized logic and cultural context priority"""
        
        base_score = features['base_score']
        
        # Handle spam - assign to Positif with low confidence instead of Netral
        if features['is_spam']:
            return {
                'sentiment': 'Positif',
                'confidence': 0.1,
                'score': 0,
                'method': 'spam_detection',
                'cultural_context': False
            }
        
        # === PRIORITY-BASED SENTIMENT OVERRIDE ===
        # Strong positive indicators override normal analysis
        if features.get('strong_positive_found', False):
            confidence_boost = min(0.4, features.get('strong_positive_count', 0) * 0.15)
            return {
                'sentiment': 'Positif',
                'confidence': 0.85 + confidence_boost,
                'score': max(2.5, base_score),
                'method': 'cultural_positive_override',
                'cultural_context': True,
                'cultural_indicators': features.get('strong_positive_count', 0)
            }
        
        # Positive negation phrases strongly indicate positive sentiment
        if features.get('positive_negation_found', False):
            confidence_boost = min(0.3, len(features.get('positive_negation_phrases', [])) * 0.1)
            return {
                'sentiment': 'Positif',
                'confidence': 0.80 + confidence_boost,
                'score': max(2.0, base_score),
                'method': 'positive_negation_override',
                'cultural_context': True,
                'negation_phrases': features.get('positive_negation_phrases', [])
            }
        
        # === STANDARD ANALYSIS WITH CULTURAL ENHANCEMENTS ===
        # Rating-aware adjustment
        if rating:
            if rating >= 5:
                rating_bias = 1.0
            elif rating >= 4:
                rating_bias = 0.5
            elif rating <= 2:
                rating_bias = -0.5
            else:
                rating_bias = 0
            
            adjusted_score = base_score + rating_bias
        else:
            adjusted_score = base_score
        
        # Apply cultural boost to confidence calculation
        cultural_boost = features.get('cultural_boost', 0)
        base_confidence_modifier = 1.0 + (cultural_boost * 0.05)  # Small boost for cultural context
        
        # Apply adaptive thresholds - force binary classification
        if adjusted_score > self.positive_threshold:
            sentiment = 'Positif'
            confidence = min(0.95, (0.5 + abs(adjusted_score) * 0.1) * base_confidence_modifier)
        elif adjusted_score < self.negative_threshold:
            sentiment = 'Negatif'
            confidence = min(0.95, (0.5 + abs(adjusted_score) * 0.1) * base_confidence_modifier)
        else:
            # Instead of Netral, use rating-based classification or default to Positif
            if rating and rating <= 3:
                sentiment = 'Negatif'
                confidence = 0.6 * base_confidence_modifier
            else:
                sentiment = 'Positif'
                confidence = 0.6 * base_confidence_modifier
        
        # Adjust confidence based on text quality
        if features['text_length'] < 10:
            confidence *= 0.7
        
        # Boost confidence if negated negative words were found (these are contextually positive)
        if features.get('negated_negative_count', 0) > 0:
            confidence = min(0.95, confidence + features['negated_negative_count'] * 0.1)
        
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'score': adjusted_score,
            'method': 'cultural_enhanced_analysis',
            'cultural_context': cultural_boost > 0 or features.get('negated_negative_count', 0) > 0,
            'cultural_boost': cultural_boost,
            'negated_negatives': features.get('negated_negative_count', 0)
        }
    
    def analyze_single_optimized(self, text: str, rating: int = None) -> Dict:
        """Analyze single text with optimized approach"""
        
        # Extract features
        features = self.extract_features_optimized(text, rating)
        
        # Calculate sentiment
        result = self.calculate_sentiment_optimized(features, rating)
        
        # Add feature info for debugging
        result['features'] = features
        
        return result
    
    def analyze_single_review(self, text: str, rating: int = None) -> Dict:
        """
        Analyze single review text - compatibility method
        This method provides a consistent interface for single review analysis
        """
        return self.analyze_single_optimized(text, rating)
    
    def process_batch_vectorized(self, batch: pd.DataFrame) -> List[Dict]:
        """Process batch with vectorized operations where possible"""
        
        # Pre-process all texts at once using vectorized operations
        texts = batch['Ulasan'].fillna('').astype(str).str.lower()
        
        # Vectorized typo correction
        for pattern, replacement in self.typo_patterns.items():
            texts = texts.str.replace(pattern, replacement, regex=True)
        
        # Process each text
        results = []
        for idx, (text, row) in enumerate(zip(texts, batch.itertuples())):
            # Get rating if available
            rating = getattr(row, 'Rating', None)
            
            # Use cache if available
            cache_key = hash(text + str(rating))
            if cache_key in self.cache:
                results.append(self.cache[cache_key])
            else:
                result = self.analyze_single_optimized(text, rating)
                
                # Cache the result
                self.cache[cache_key] = result
                results.append(result)
                
                # Maintain cache size
                if len(self.cache) > self.cache_size:
                    # Remove oldest entries (simple FIFO)
                    oldest_keys = list(self.cache.keys())[:len(self.cache) - self.cache_size]
                    for key in oldest_keys:
                        del self.cache[key]
        
        return results
    
    def analyze_sentiment_batch(self, df: pd.DataFrame, batch_size: int = 500) -> List[Dict]:
        """Process in batches for better performance"""
        
        results = []
        total_batches = (len(df) + batch_size - 1) // batch_size
        
        print(f"📊 Processing {len(df)} reviews in {total_batches} batches...")
        
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            
            # Process batch
            batch_results = self.process_batch_vectorized(batch)
            results.extend(batch_results)
            
            # Update progress
            current_batch = i // batch_size + 1
            if self.progress_callback:
                progress = (i + len(batch)) / len(df) * 100
                self.progress_callback(progress, f"Processing batch {current_batch}/{total_batches}")
            
            if current_batch % 10 == 0:
                print(f"✅ Processed {current_batch}/{total_batches} batches ({len(results)} reviews)")
        
        return results
    
    def apply_consistency_checks(self, results: List[Dict], df: pd.DataFrame) -> List[Dict]:
        """Apply post-processing consistency checks"""
        
        print("🔍 Applying consistency checks...")
        
        corrected = []
        corrections_made = 0
        
        for i, (result, row) in enumerate(zip(results, df.itertuples())):
            original_sentiment = result['sentiment']
            
            # Get rating if available
            rating = getattr(row, 'Rating', None)
            
            if rating:
                # Fix obvious rating-sentiment mismatches
                if rating >= 5 and result['sentiment'] == 'Negatif' and result['confidence'] < 0.7:
                    result['sentiment'] = 'Positif'
                    result['confidence'] *= 0.8
                    result['method'] = 'consistency_correction'
                    corrections_made += 1
                    
                elif rating <= 2 and result['sentiment'] == 'Positif' and result['confidence'] < 0.7:
                    result['sentiment'] = 'Negatif'
                    result['confidence'] *= 0.8
                    result['method'] = 'consistency_correction'
                    corrections_made += 1
            
            # Mark if correction was applied
            if result['sentiment'] != original_sentiment:
                result['was_corrected'] = True
            else:
                result['was_corrected'] = False
            
            corrected.append(result)
        
        print(f"✅ Consistency checks completed: {corrections_made} corrections made")
        return corrected
    
    def analyze_large_dataset(self, csv_path: str) -> Tuple[pd.DataFrame, Dict]:
        """Optimized pipeline for large datasets"""
        
        print("🚀 Starting large dataset analysis pipeline...")
        
        # 1. Load data efficiently
        print("📂 Loading dataset...")
        try:
            # Try to load in chunks for very large files
            file_size = os.path.getsize(csv_path)
            if file_size > 100 * 1024 * 1024:  # 100MB
                print("⚠️ Very large file detected, loading in chunks...")
                chunk_size = 1000
                chunks = []
                for chunk in pd.read_csv(csv_path, chunksize=chunk_size):
                    chunks.append(chunk)
                df = pd.concat(chunks, ignore_index=True)
            else:
                df = pd.read_csv(csv_path)
        except Exception as e:
            print(f"❌ Error loading dataset: {e}")
            return None, None
        
        print(f"✅ Dataset loaded: {len(df)} rows, {len(df.columns)} columns")
        
        # 2. Pre-analysis to understand dataset characteristics
        print("📊 Analyzing dataset characteristics...")
        self.calculate_adaptive_thresholds(df)
        
        # 3. Dynamic lexicon expansion for large datasets
        if len(df) > 5000:
            print("🔄 Expanding lexicon for large dataset...")
            self.expand_lexicon_dynamically(df)
        
        # 4. Process in optimized batches
        print("⚡ Processing reviews in optimized batches...")
        results = self.analyze_sentiment_batch(df)
        
        # 5. Apply post-processing consistency checks
        print("🔍 Applying consistency checks...")
        results = self.apply_consistency_checks(results, df)
        
        # 6. Compile final results
        print("📊 Compiling final results...")
        
        # Add results to DataFrame
        df['Sentiment'] = [r['sentiment'] for r in results]
        df['Confidence'] = [r['confidence'] for r in results]
        df['Sentiment_Score'] = [r['score'] for r in results]
        df['Prediction_Method'] = [r['method'] for r in results]
        df['Was_Corrected'] = [r.get('was_corrected', False) for r in results]
        
        # Calculate metrics
        sentiment_counts = df['Sentiment'].value_counts()
        avg_confidence = df['Confidence'].mean()
        corrections_made = df['Was_Corrected'].sum()
        
        # Enhanced metrics
        metrics = {
            'total_reviews': len(df),
            'sentiment_distribution': sentiment_counts.to_dict(),
            'average_confidence': float(avg_confidence),
            'corrections_made': int(corrections_made),
            'processing_method': 'optimized_large_dataset',
            'cache_hits': len(self.cache),
            'adaptive_thresholds': {
                'positive': self.positive_threshold,
                'negative': self.negative_threshold,
                'confidence': self.confidence_threshold
            },
            'lexicon_expansion': {
                'temp_positive_words': len(self.temp_positive_words),
                'temp_negative_words': len(self.temp_negative_words)
            }
        }
        
        # Add rating analysis if available
        if 'Rating' in df.columns:
            metrics['rating_distribution'] = df['Rating'].value_counts().sort_index().to_dict()
            
            # Rating-sentiment correlation
            rating_sentiment = df.groupby('Rating')['Sentiment'].value_counts(normalize=True).unstack(fill_value=0)
            metrics['rating_sentiment_correlation'] = rating_sentiment.to_dict()
        
        # Method distribution
        method_counts = df['Prediction_Method'].value_counts()
        metrics['method_distribution'] = method_counts.to_dict()
        
        # Confidence distribution
        confidence_stats = df['Confidence'].describe()
        metrics['confidence_statistics'] = confidence_stats.to_dict()
        
        print("✅ Large dataset analysis completed successfully!")
        print(f"   Total reviews: {len(df):,}")
        print(f"   Average confidence: {avg_confidence:.3f}")
        print(f"   Corrections made: {corrections_made:,}")
        print(f"   Sentiment distribution: {dict(sentiment_counts)}")
        
        return df, metrics
    
    def analyze_sentiment(self, csv_path: str, progress_callback=None) -> Tuple[pd.DataFrame, Dict]:
        """Main entry point - automatically chooses optimal method"""
        
        self.progress_callback = progress_callback
        
        # Check file size to determine approach
        file_size = os.path.getsize(csv_path)
        is_large = file_size > 50 * 1024 * 1024  # 50MB threshold
        
        # Also check row count for better decision
        try:
            # Quick row count check
            with open(csv_path, 'r', encoding='utf-8') as f:
                row_count = sum(1 for line in f) - 1  # Subtract header
            is_large = is_large or row_count > 10000
        except:
            pass
        
        if is_large:
            print("📊 Large dataset detected, using optimized pipeline...")
            return self.analyze_large_dataset(csv_path)
        else:
            print("📊 Small-medium dataset detected, using standard pipeline...")
            # For smaller datasets, use simpler approach
            return self.analyze_standard_dataset(csv_path)
    
    def analyze_standard_dataset(self, csv_path: str) -> Tuple[pd.DataFrame, Dict]:
        """Standard analysis for smaller datasets"""
        
        print("📂 Loading standard dataset...")
        df = pd.read_csv(csv_path)
        
        print(f"✅ Dataset loaded: {len(df)} rows")
        
        # Set standard thresholds
        self.positive_threshold = 1.0
        self.negative_threshold = -1.0
        self.confidence_threshold = 0.5
        
        # Process all at once
        results = []
        for idx, row in df.iterrows():
            text = row.get('Ulasan', '')
            rating = row.get('Rating', None)
            
            result = self.analyze_single_optimized(text, rating)
            results.append(result)
            
            # Update progress
            if self.progress_callback and idx % 100 == 0:
                progress = (idx + 1) / len(df) * 100
                self.progress_callback(progress, f"Processing review {idx + 1}/{len(df)}")
        
        # Add results to DataFrame
        df['Sentiment'] = [r['sentiment'] for r in results]
        df['Confidence'] = [r['confidence'] for r in results]
        df['Sentiment_Score'] = [r['score'] for r in results]
        df['Prediction_Method'] = [r['method'] for r in results]
        
        # Calculate metrics
        sentiment_counts = df['Sentiment'].value_counts()
        avg_confidence = df['Confidence'].mean()
        
        metrics = {
            'total_reviews': len(df),
            'sentiment_distribution': sentiment_counts.to_dict(),
            'average_confidence': float(avg_confidence),
            'processing_method': 'standard_dataset',
            'cache_hits': len(self.cache)
        }
        
        if 'Rating' in df.columns:
            metrics['rating_distribution'] = df['Rating'].value_counts().sort_index().to_dict()
        
        print("✅ Standard dataset analysis completed!")
        return df, metrics
    
    def preview_analysis_results(self, df: pd.DataFrame, max_rows: int = 10, 
                               wrap_width: int = 70, show_details: bool = True) -> None:
        """
        Preview hasil analisis sentimen dengan text wrapping
        
        Args:
            df: DataFrame hasil analisis
            max_rows: Maksimal baris yang ditampilkan
            wrap_width: Lebar text wrapping
            show_details: Tampilkan detail tambahan
        """
        import textwrap
        
        print("📊 PREVIEW HASIL ANALISIS SENTIMEN")
        print("=" * 100)
        
        if len(df) == 0:
            print("⚠️ Tidak ada data untuk ditampilkan")
            return
        
        # Statistik ringkas
        print(f"📈 STATISTIK RINGKAS:")
        print(f"   Total ulasan: {len(df):,}")
        
        if 'Sentiment' in df.columns:
            sentiment_counts = df['Sentiment'].value_counts()
            sentiment_colors = {'Positif': '🟢', 'Negatif': '🔴'}
            
            for sentiment, count in sentiment_counts.items():
                emoji = sentiment_colors.get(sentiment, '⚪')
                percentage = (count / len(df)) * 100
                print(f"   {emoji} {sentiment}: {count:,} ({percentage:.1f}%)")
        
        if 'Confidence' in df.columns:
            avg_confidence = df['Confidence'].mean()
            print(f"   📊 Rata-rata confidence: {avg_confidence:.3f}")
        
        print("\n" + "=" * 100)
        print("📋 PREVIEW DATA (Text Wrapped)")
        print("=" * 100)
        
        # Preview sample data
        sample_df = df.head(max_rows)
        
        for idx, row in sample_df.iterrows():
            print(f"\n🔍 ULASAN #{idx + 1}")
            print("-" * 60)
            
            # Ulasan dengan text wrapping
            ulasan = row.get('Ulasan', 'N/A')
            if not pd.isna(ulasan):
                wrapped_lines = textwrap.wrap(str(ulasan), width=wrap_width)
                print(f"📝 Ulasan:")
                for line in wrapped_lines:
                    print(f"   {line}")
            else:
                print(f"📝 Ulasan: N/A")
            
            # Sentiment dengan emoji
            if 'Sentiment' in row:
                sentiment = row['Sentiment']
                emoji = sentiment_colors.get(sentiment, '⚪')
                print(f"🎯 Sentimen: {emoji} {sentiment}")
            
            # Confidence dengan bar visual
            if 'Confidence' in row:
                confidence = row['Confidence']
                if not pd.isna(confidence):
                    confidence_percent = confidence * 100
                    bar_length = 20
                    filled_length = int(bar_length * confidence)
                    bar = '█' * filled_length + '░' * (bar_length - filled_length)
                    print(f"📊 Confidence: {confidence_percent:.1f}% {bar}")
                else:
                    print(f"📊 Confidence: N/A")
            
            # Rating dengan bintang
            if 'Rating' in row:
                rating = row['Rating']
                if not pd.isna(rating):
                    stars = '⭐' * int(rating)
                    print(f"⭐ Rating: {rating} {stars}")
                else:
                    print(f"⭐ Rating: N/A")
            
            # Method
            if 'Prediction_Method' in row:
                method = row['Prediction_Method']
                print(f"🔧 Method: {method}")
            
            # Score
            if 'Sentiment_Score' in row:
                score = row['Sentiment_Score']
                if not pd.isna(score):
                    print(f"📈 Score: {score:.3f}")
            
            # Detail tambahan
            if show_details:
                # Cultural context detection
                method = row.get('Prediction_Method', '')
                if 'cultural' in str(method).lower():
                    print(f"🌟 Cultural Context: Terdeteksi")
                
                # Text info
                if not pd.isna(ulasan):
                    text_length = len(str(ulasan))
                    word_count = len(str(ulasan).split())
                    print(f"📏 Info Teks: {text_length} karakter, {word_count} kata")
        
        # Info tambahan
        if len(df) > max_rows:
            print(f"\n... dan {len(df) - max_rows:,} ulasan lainnya")
        
        print("\n" + "=" * 100)
        print("✅ Preview selesai!")
    
    def preview_by_sentiment_type(self, df: pd.DataFrame, sentiment_type: str = 'Positif', 
                                max_rows: int = 5, wrap_width: int = 60) -> None:
        """
        Preview ulasan berdasarkan jenis sentimen tertentu dengan text wrapping
        
        Args:
            df: DataFrame hasil analisis
            sentiment_type: Jenis sentimen ('Positif', 'Negatif')
            max_rows: Maksimal baris yang ditampilkan
            wrap_width: Lebar text wrapping
        """
        import textwrap
        
        if 'Sentiment' not in df.columns:
            print("⚠️ Kolom 'Sentiment' tidak ditemukan")
            return
        
        filtered_df = df[df['Sentiment'] == sentiment_type]
        sentiment_colors = {'Positif': '🟢', 'Negatif': '🔴'}
        emoji = sentiment_colors.get(sentiment_type, '⚪')
        
        print(f"{emoji} PREVIEW ULASAN {sentiment_type.upper()}")
        print("=" * 70)
        
        if len(filtered_df) == 0:
            print(f"⚠️ Tidak ada ulasan dengan sentimen {sentiment_type}")
            return
        
        print(f"📊 Total ulasan {sentiment_type}: {len(filtered_df):,}")
        
        # Urutkan berdasarkan confidence (tertinggi dulu)
        if 'Confidence' in filtered_df.columns:
            filtered_df = filtered_df.sort_values('Confidence', ascending=False)
        
        sample_df = filtered_df.head(max_rows)
        
        for i, (idx, row) in enumerate(sample_df.iterrows(), 1):
            print(f"\n📝 Ulasan {sentiment_type} #{i}")
            print("-" * 50)
            
            # Ulasan dengan wrapping
            ulasan = row.get('Ulasan', 'N/A')
            if not pd.isna(ulasan):
                wrapped_lines = textwrap.wrap(str(ulasan), width=wrap_width)
                for line in wrapped_lines:
                    print(f"   {line}")
            else:
                print(f"   N/A")
            
            # Info tambahan
            if 'Confidence' in row and not pd.isna(row['Confidence']):
                confidence = row['Confidence']
                print(f"   💯 Confidence: {confidence:.3f}")
            
            if 'Rating' in row and not pd.isna(row['Rating']):
                rating = row['Rating']
                print(f"   ⭐ Rating: {rating}")
            
            if 'Sentiment_Score' in row and not pd.isna(row['Sentiment_Score']):
                score = row['Sentiment_Score']
                print(f"   📈 Score: {score:.3f}")
        
        print(f"\n✅ Preview {sentiment_type} selesai!")
