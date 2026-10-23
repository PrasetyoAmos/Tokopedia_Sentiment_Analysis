"""
Emoji Enhanced Sentiment Analyzer
A sentiment analyzer that handles emoji, negation, and Indonesian slang
"""

import json
import os
import re
import emoji
import pandas as pd
from collections import Counter
from .advanced_negation_handler import AdvancedNegationHandler

class EmojiEnhancedSentimentAnalyzer:
    def __init__(self):
        """Initialize the emoji enhanced sentiment analyzer"""
        self.lexicon = self.load_lexicon()
        self.negation_handler = AdvancedNegationHandler()
        
        # Load all positive and negative words from different categories
        self.positive_words = set()
        self.negative_words = set()
        self.intensifiers = set()
        
        if isinstance(self.lexicon.get('positive'), dict):
            for category, words in self.lexicon['positive'].items():
                if category == 'intensifiers':
                    self.intensifiers.update(words)
                else:
                    self.positive_words.update(words)
        else:
            self.positive_words.update(self.lexicon.get('positive', []))
        
        if isinstance(self.lexicon.get('negative'), dict):
            for category, words in self.lexicon['negative'].items():
                self.negative_words.update(words)
        else:
            self.negative_words.update(self.lexicon.get('negative', []))
        
        # Load other components
        self.emoji_weights = self.lexicon.get('emoji_weights', {})
        self.contextual_phrases = self.lexicon.get('contextual_phrases', {})
        self.slang_normalization = self.lexicon.get('slang_normalization', {})
        
        # NEW: Contrast words for detecting mixed sentiment
        self.contrast_words = {
            'tapi', 'tetapi', 'namun', 'akan tetapi', 'cuma', 'cm', 
            'hanya', 'sayangnya', 'sayang', 'padahal', 'malah', 'cman',
            'cuman', 'tapi nya', 'tapiny', 'tp', 'but', 'however'
        }
        
        # NEW: Complaint phrases for e-commerce context
        self.complaint_phrases = {
            'gak responsif', 'tidak responsif', 'lama banget', 'lama sekali',
            'tidak lengkap', 'gak lengkap', 'kurang memuaskan', 'tidak memuaskan',
            'gak sesuai', 'tidak sesuai', 'bukan ori', 'tidak original',
            'cancel ditolak', 'dibales pake template', 'bot ga mampu',
            'pengiriman lama', 'kirim lama', 'lama sampai', 'lambat banget',
            'status tidak jelas', 'tracking error', 'pick up failure',
            'dikurangi', 'mengecewakan', 'kecewa banget', 'sangat kecewa',
            'palsu', 'kw', 'replica', 'imitasi', 'tidak asli', 'fake',
            'rusak', 'cacat', 'penyok', 'lecet', 'kotor', 'buram',
            'tidak berfungsi', 'gak berfungsi', 'error', 'bermasalah'
        }
        
        print(f"✅ Emoji Enhanced Analyzer initialized:")
        print(f"   - Positive words: {len(self.positive_words)}")
        print(f"   - Negative words: {len(self.negative_words)}")
        print(f"   - Intensifiers: {len(self.intensifiers)}")
        print(f"   - Emoji weights: {len(self.emoji_weights)}")
        print(f"   - Contextual phrases: {len(self.contextual_phrases)}")
        print(f"   - Contrast words: {len(self.contrast_words)}")
        print(f"   - Complaint phrases: {len(self.complaint_phrases)}")
        print(f"   - Slang mappings: {len(self.slang_normalization)}")
    
    def load_lexicon(self):
        """Load sentiment lexicon from JSON file"""
        lexicon_path = os.path.join('utils', 'sentiment_lexicon.json')
        
        # If file doesn't exist or is empty, create a basic lexicon
        if not os.path.exists(lexicon_path) or os.path.getsize(lexicon_path) == 0:
            return self.create_basic_lexicon()
        
        try:
            with open(lexicon_path, 'r', encoding='utf-8') as f:
                lexicon = json.load(f)
            return lexicon
        except (json.JSONDecodeError, FileNotFoundError):
            return self.create_basic_lexicon()
    
    def create_basic_lexicon(self):
        """Create a basic sentiment lexicon"""
        lexicon = {
            'positive': [
                'bagus', 'baik', 'mantap', 'oke', 'ok', 'good', 'recommended',
                'suka', 'puas', 'senang', 'keren', 'cantik', 'cocok', 'sesuai',
                'murah', 'cepat', 'responsive', 'ramah', 'berkualitas', 'memuaskan',
                'mantul', 'joss', 'josss', 'kece', 'top', 'perfect', 'excellent',
                'amazing', 'awesome', 'fantastic', 'great', 'wonderful', 'love',
                'sukses', 'berhasil', 'lancar', 'smooth', 'mudah', 'simple',
                'terpercaya', 'original', 'ori', 'legit', 'real', 'genuine'
            ],
            'negative': [
                'jelek', 'buruk', 'tidak', 'kecewa', 'lambat', 'mahal', 'rusak',
                'cacat', 'bad', 'terrible', 'awful', 'mengecewakan', 'payah',
                'zonk', 'fake', 'palsu', 'bohong', 'menipu', 'scam', 'penipuan',
                'lelet', 'slow', 'ribet', 'susah', 'sulit', 'complicated',
                'error', 'bug', 'broken', 'damage', 'defect', 'problem',
                'masalah', 'trouble', 'issue', 'fail', 'gagal', 'batal'
            ],
            'emoji_mapping': {
                '😊': 'positive', '😀': 'positive', '😃': 'positive', '😄': 'positive',
                '😁': 'positive', '😆': 'positive', '😂': 'positive', '🤣': 'positive',
                '😉': 'positive', '😎': 'positive', '🥰': 'positive', '😍': 'positive',
                '🤩': 'positive', '😋': 'positive', '😚': 'positive', '😘': 'positive',
                '❤️': 'positive', '💖': 'positive', '💕': 'positive', '💗': 'positive',
                '👍': 'positive', '👏': 'positive', '🎉': 'positive', '🔥': 'positive',
                '💯': 'positive', '✨': 'positive', '⭐': 'positive', '🌟': 'positive',
                '😢': 'negative', '😭': 'negative', '😰': 'negative', '😨': 'negative',
                '😱': 'negative', '😡': 'negative', '😠': 'negative', '🤬': 'negative',
                '😤': 'negative', '😞': 'negative', '😔': 'negative', '😟': 'negative',
                '😕': 'negative', '🙁': 'negative', '☹️': 'negative', '😣': 'negative',
                '😖': 'negative', '😫': 'negative', '😩': 'negative', '🤢': 'negative',
                '🤮': 'negative', '👎': 'negative', '💔': 'negative', '🗑️': 'negative'
            },
            'slang_normalization': {
                'dgn': 'dengan', 'gue': 'saya', 'tdk': 'tidak', 'blm': 'belum',
                'gx': 'tidak', 'gk': 'tidak', 'ga': 'tidak', 'gak': 'tidak',
                'bgt': 'bagus', 'bngt': 'bagus', 'mantul': 'mantap', 'joss': 'bagus',
                'josss': 'bagus', 'kece': 'bagus', 'top': 'bagus', 'zonk': 'jelek',
                'lelet': 'lambat', 'ribet': 'susah', 'ori': 'original', 'tq': 'terima kasih',
                'thx': 'terima kasih', 'thanks': 'terima kasih', 'makasih': 'terima kasih',
                'rec': 'recommended', 'recomended': 'recommended', 'recomen': 'recommended',
                'sip': 'baik', 'siip': 'baik', 'sippp': 'baik', 'kualitas': 'berkualitas',
                'terpercaya': 'terpercaya', 'trusted': 'terpercaya', 'trust': 'terpercaya'
            }
        }
        
        # Save the basic lexicon
        lexicon_path = os.path.join('utils', 'sentiment_lexicon.json')
        try:
            os.makedirs(os.path.dirname(lexicon_path), exist_ok=True)
            with open(lexicon_path, 'w', encoding='utf-8') as f:
                json.dump(lexicon, f, ensure_ascii=False, indent=2)
            print(f"✅ Basic sentiment lexicon created at {lexicon_path}")
        except Exception as e:
            print(f"⚠️ Could not save lexicon: {e}")
        
        return lexicon
    
    def preprocess_text(self, text):
        """Preprocess text with emoji extraction and slang normalization"""
        if pd.isna(text) or text is None:
            return ""
        
        text = str(text).lower().strip()
        
        # Extract emojis
        emojis = emoji.emoji_list(text)
        
        # Normalize slang
        for slang, normal in self.slang_normalization.items():
            text = re.sub(r'\b' + re.escape(slang) + r'\b', normal, text)
        
        # Clean text
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip(), emojis
    
    def detect_domain(self, text):
        """Detect the domain/category of the review"""
        text_lower = text.lower()
        domain_keywords = self.lexicon.get('domain_keywords', {})
        
        domain_scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                domain_scores[domain] = score
        
        if domain_scores:
            return max(domain_scores.items(), key=lambda x: x[1])[0]
        return 'general'
    
    def detect_contrast_sentiment(self, text):
        """Detect sentiment when there's contrast (tapi, cuma, etc)"""
        text_lower = text.lower()
        
        # Check for contrast words
        for contrast in self.contrast_words:
            if contrast in text_lower:
                # Find the position of contrast word
                contrast_pos = text_lower.find(contrast)
                if contrast_pos != -1:
                    # Split text at contrast word
                    before_contrast = text_lower[:contrast_pos].strip()
                    after_contrast = text_lower[contrast_pos + len(contrast):].strip()
                    
                    if before_contrast and after_contrast:
                        # Analyze sentiment before and after contrast
                        before_sentiment = self.analyze_text_part(before_contrast)
                        after_sentiment = self.analyze_text_part(after_contrast)
                        
                        # After contrast usually dominates sentiment
                        # Especially for complaints in e-commerce
                        if after_sentiment < -0.5:  # Negative after contrast
                            return after_sentiment * 1.5  # Amplify negative after contrast
                        elif after_sentiment > 0.5:  # Positive after contrast
                            return after_sentiment * 1.2  # Slightly amplify positive
                        else:
                            # Mixed or neutral after contrast
                            return after_sentiment * 1.3
        
        return None
    
    def analyze_text_part(self, text_part):
        """Analyze sentiment for a part of text (used in contrast detection)"""
        tokens = text_part.split()
        positive_count = 0
        negative_count = 0
        
        for token in tokens:
            if token in self.positive_words:
                positive_count += 1
            elif token in self.negative_words:
                negative_count += 1
        
        # Check for complaint phrases
        if self.has_complaint_phrases(text_part):
            negative_count += 2  # Strong negative signal
        
        # Calculate simple sentiment score
        if positive_count > negative_count:
            return (positive_count - negative_count) / max(len(tokens), 1)
        elif negative_count > positive_count:
            return -(negative_count - positive_count) / max(len(tokens), 1)
        else:
            return 0
    
    def has_complaint_phrases(self, text):
        """Check if text contains complaint phrases"""
        text_lower = text.lower()
        
        # Direct phrase matching
        for phrase in self.complaint_phrases:
            if phrase in text_lower:
                return True
        
        # Pattern matching for common complaints
        complaint_patterns = [
            r'tidak\s+\w+\s+sesuai',  # tidak [word] sesuai
            r'gak\s+\w+\s+sesuai',    # gak [word] sesuai
            r'lama\s+(banget|sekali|kali)',  # lama banget/sekali/kali
            r'(kurang|tidak|gak)\s+memuaskan',
            r'(kurang|tidak|gak)\s+responsif',
            r'cancel\s+ditolak',
            r'(tidak|gak)\s+lengkap',
            r'(tidak|gak)\s+ori\w*',  # tidak ori/original
            r'bukan\s+ori\w*',        # bukan ori/original
            r'(rusak|cacat|error)\s+\w*',  # rusak/cacat/error [word]
            r'(lambat|lama)\s+(banget|sekali|kali)',  # lambat/lama banget/sekali/kali
            r'(mengecewakan|kecewa)\s+\w*'  # mengecewakan/kecewa [word]
        ]
        
        for pattern in complaint_patterns:
            if re.search(pattern, text_lower):
                return True
                
        return False
    
    def calculate_final_sentiment(self, text_score, confidence, rating, text):
        """Combine text sentiment with rating consideration and contrast detection"""
        
        # First check for contrast
        contrast_score = self.detect_contrast_sentiment(text)
        if contrast_score is not None:
            text_score = contrast_score
        
        # Check for complaint phrases
        has_complaints = self.has_complaint_phrases(text)
        
        # Enhanced sentiment determination based on rating
        if rating <= 2:  # Low rating (1-2 stars) - special handling
            if has_complaints or text_score < -0.5:
                return 'Negatif', min(confidence * 1.2, 0.95)  # High confidence for negative
            elif text_score > 2:  # Very positive text with low rating
                # Likely sarcasm or mixed sentiment
                return 'Negatif', confidence * 0.8
            else:
                # Default to negative for low ratings
                return 'Negatif', confidence * 0.9
                
        elif rating >= 4:  # High rating (4-5 stars)
            if text_score < -2 or has_complaints:
                # Negative text with high rating - conflicting signals
                return 'Negatif', confidence * 0.7
            elif text_score > 0:
                return 'Positif', min(confidence * 1.1, 0.95)
            else:
                return 'Positif', confidence * 0.8
                
        else:  # Rating 3 or neutral/unknown rating
            if text_score > 1 and not has_complaints:
                return 'Positif', confidence * 0.8
            elif text_score < -1 or has_complaints:
                return 'Negatif', confidence * 0.8
            else:
                # For neutral cases, lean on complaint detection
                if has_complaints:
                    return 'Negatif', confidence * 0.6
                else:
                    return 'Netral', confidence * 0.5
    
    def calculate_sentiment_score(self, text, domain='general'):
        """Calculate sentiment with domain awareness and weighted scoring"""
        
        # Preprocess
        processed_text, emojis = self.preprocess_text(text)
        tokens = processed_text.split()
        
        # Word sentiment scores
        word_sentiments = {}
        
        # Score words based on domain
        positive_categories = self.lexicon.get('positive', {})
        negative_categories = self.lexicon.get('negative', {})
        
        for token in tokens:
            score = 0
            
            # Check general + domain-specific lexicons
            if isinstance(positive_categories, dict):
                if token in positive_categories.get('general', []):
                    score += 1.0
                if token in positive_categories.get(domain, []):
                    score += 0.5  # Domain-specific bonus
            else:
                if token in positive_categories:
                    score += 1.0
            
            if isinstance(negative_categories, dict):
                if token in negative_categories.get('general', []):
                    score -= 1.0
                if token in negative_categories.get(domain, []):
                    score -= 0.5
            else:
                if token in negative_categories:
                    score -= 1.0
            
            if score != 0:
                word_sentiments[token] = score
        
        # Handle intensifiers
        for i, token in enumerate(tokens):
            if token in self.intensifiers:
                # Amplify next word's sentiment
                if i + 1 < len(tokens) and tokens[i + 1] in word_sentiments:
                    word_sentiments[tokens[i + 1]] *= 1.5
        
        # Check for contextual phrases
        contextual_score = self.check_contextual_phrases(processed_text)
        
        # Handle negation properly using advanced handler
        word_sentiments = self.negation_handler.handle_negation(tokens, word_sentiments)
        
        # Calculate emoji score with weights
        emoji_score = 0
        for emoji_data in emojis:
            emoji_char = emoji_data['emoji']
            weight = self.emoji_weights.get(emoji_char, 0)
            emoji_score += weight
        
        # Combine scores
        word_score = sum(word_sentiments.values())
        total_score = word_score + (emoji_score * 0.7) + (contextual_score * 0.8)
        
        # Calculate confidence based on various factors
        confidence = self.calculate_confidence(text, word_sentiments, emoji_score, contextual_score)
        
        return total_score, confidence
    
    def check_contextual_phrases(self, text):
        """Check for contextual phrases that indicate strong sentiment"""
        positive_phrases = self.contextual_phrases.get('positive', [])
        negative_phrases = self.contextual_phrases.get('negative', [])
        
        score = 0
        for phrase in positive_phrases:
            if phrase in text:
                score += 1.5  # Strong positive indicator
        
        for phrase in negative_phrases:
            if phrase in text:
                score -= 1.5  # Strong negative indicator
        
        return score
    
    def calculate_confidence(self, text, word_sentiments, emoji_score, contextual_score):
        """Calculate confidence based on multiple factors"""
        confidence_markers = self.lexicon.get('confidence_markers', {})
        
        # Base confidence
        confidence = 0.5
        
        # Adjust based on sentiment strength
        sentiment_strength = abs(sum(word_sentiments.values()))
        confidence += min(0.3, sentiment_strength * 0.05)
        
        # Adjust based on emoji presence
        if abs(emoji_score) > 0:
            confidence += 0.1
        
        # Adjust based on contextual phrases
        if abs(contextual_score) > 0:
            confidence += 0.15
        
        # Check for confidence markers in text
        text_lower = text.lower()
        
        # High confidence markers
        high_conf_words = confidence_markers.get('high_confidence', [])
        if any(word in text_lower for word in high_conf_words):
            confidence += 0.2
        
        # Low confidence markers
        low_conf_words = confidence_markers.get('low_confidence', [])
        if any(word in text_lower for word in low_conf_words):
            confidence -= 0.2
        
        # Negation analysis
        negation_analysis = self.negation_handler.analyze_negation_context(text)
        confidence *= negation_analysis.get('confidence_modifier', 1.0)
        
        return min(0.95, max(0.1, confidence))
    
    def analyze_sentiment(self, csv_path, progress_callback=None):
        """Analyze sentiment of reviews in CSV file with enhanced features"""
        try:
            df = pd.read_csv(csv_path)
            
            if 'Ulasan' not in df.columns:
                raise ValueError("CSV must contain 'Ulasan' column")
            
            sentiments = []
            confidences = []
            methods = []
            domains = []
            sentiment_scores = []
            
            total_rows = len(df)
            
            for idx, row in df.iterrows():
                review = str(row['Ulasan'])
                rating = row.get('Rating', 3)
                
                # Extract rating as number
                if isinstance(rating, str):
                    rating = float(rating.replace('bintang', '').strip())
                else:
                    rating = float(rating)
                
                # Detect domain for this review
                domain = self.detect_domain(review)
                
                # Calculate base sentiment score using enhanced method
                sentiment_score, base_confidence = self.calculate_sentiment_score(review, domain)
                
                # NEW: Apply contrast detection and complaint-aware sentiment
                final_sentiment, final_confidence = self.calculate_final_sentiment(
                    sentiment_score, base_confidence, rating, review
                )
                
                # Track additional metrics
                has_contrast = self.detect_contrast_sentiment(review) is not None
                has_complaints = self.has_complaint_phrases(review)
                
                sentiments.append(final_sentiment)
                confidences.append(final_confidence)
                methods.append('advanced_emoji_enhanced_v2')  # Updated method name
                domains.append(domain)
                sentiment_scores.append(sentiment_score)
                
                # Update progress
                if progress_callback:
                    progress = int((idx + 1) / total_rows * 100)
                    progress_callback(progress, f"Processing review {idx + 1}/{total_rows}")
            
            # Add results to dataframe
            df['Sentiment'] = sentiments
            df['Confidence'] = confidences
            df['Prediction_Method'] = methods
            df['Domain'] = domains
            df['Sentiment_Score'] = sentiment_scores
            
            # Calculate enhanced metrics
            sentiment_counts = df['Sentiment'].value_counts()
            positive_percentage = (sentiment_counts.get('Positif', 0) / len(df)) * 100
            negative_percentage = (sentiment_counts.get('Negatif', 0) / len(df)) * 100
            neutral_percentage = (sentiment_counts.get('Netral', 0) / len(df)) * 100
            
            # Calculate confidence stats
            avg_confidence = df['Confidence'].mean()
            high_confidence_count = len(df[df['Confidence'] > 0.7])
            
            # Domain distribution
            domain_counts = df['Domain'].value_counts()
            
            # NEW: Enhanced metrics for contrast detection and complaints
            contrast_handled = sum(1 for _, row in df.iterrows() 
                                 if self.detect_contrast_sentiment(row['Ulasan']) is not None)
            complaints_detected = sum(1 for _, row in df.iterrows() 
                                    if self.has_complaint_phrases(row['Ulasan']))
            
            # Get enhanced keywords by domain
            positive_keywords = self.extract_enhanced_keywords(df[df['Sentiment'] == 'Positif'])
            negative_keywords = self.extract_enhanced_keywords(df[df['Sentiment'] == 'Negatif'])
            
            metrics = {
                'total_reviews': len(df),
                'positive_count': int(sentiment_counts.get('Positif', 0)),
                'negative_count': int(sentiment_counts.get('Negatif', 0)),
                'neutral_count': int(sentiment_counts.get('Netral', 0)),
                'positive_percentage': float(positive_percentage),
                'negative_percentage': float(negative_percentage),
                'neutral_percentage': float(neutral_percentage),
                'average_confidence': float(avg_confidence),
                'high_confidence_count': int(high_confidence_count),
                'high_confidence_percentage': float((high_confidence_count / len(df)) * 100),
                'domain_distribution': domain_counts.to_dict(),
                'contrast_handled': int(contrast_handled),
                'complaints_detected': int(complaints_detected),
                'positive_keywords': positive_keywords[:10],
                'negative_keywords': negative_keywords[:10],
                'method': 'advanced_emoji_enhanced_v2',
                'features': {
                    'emoji_weighted_scoring': True,
                    'advanced_negation_handling': True,
                    'domain_aware_analysis': True,
                    'contextual_phrases': True,
                    'intensifier_detection': True,
                    'confidence_scoring': True,
                    'slang_normalization': True,
                    'contrast_detection': True,
                    'complaint_phrase_detection': True,
                    'rating_aware_sentiment': True
                }
            }
            
            return df, metrics
            
        except Exception as e:
            print(f"❌ Error in advanced emoji enhanced sentiment analysis: {e}")
            raise e
    
    def extract_enhanced_keywords(self, sentiment_df):
        """Extract keywords with domain and context awareness"""
        all_keywords = []
        
        for _, row in sentiment_df.iterrows():
            review = str(row['Ulasan'])
            domain = row.get('Domain', 'general')
            
            processed_text, _ = self.preprocess_text(review)
            words = processed_text.split()
            
            # Extract relevant words based on sentiment and domain
            for word in words:
                if word in self.positive_words or word in self.negative_words:
                    all_keywords.append(word)
        
        # Count and return most common
        word_counts = Counter(all_keywords)
        return [word for word, count in word_counts.most_common(20)]
    
    def analyze_single_text(self, text, domain=None):
        """Analyze sentiment for a single text - useful for testing"""
        if domain is None:
            domain = self.detect_domain(text)
        
        sentiment_score, confidence = self.calculate_sentiment_score(text, domain)
        
        if sentiment_score > 0.1:
            sentiment = 'Positif'
        elif sentiment_score < -0.1:
            sentiment = 'Negatif'
        else:
            sentiment = 'Netral'
        
        # Get negation analysis
        negation_analysis = self.negation_handler.analyze_negation_context(text)
        
        return {
            'text': text,
            'sentiment': sentiment,
            'sentiment_score': sentiment_score,
            'confidence': confidence,
            'domain': domain,
            'negation_analysis': negation_analysis
        }
    
    def test_analyzer(self):
        """Test the analyzer with sample cases"""
        test_cases = [
            ("tidak jelek sih, malah bagus", "Positif"),
            ("bagus tapi mahal 😅", "Positif"),
            ("😍😍😍", "Positif"),
            ("gak worth it, nyesel beli", "Negatif"),
            ("pengiriman lama tapi barang oke", "Positif"),
            ("sangat recommended banget 👍", "Positif"),
            ("tidak buruk malah bagus banget", "Positif"),
            ("zonk total, bohong deskripsinya", "Negatif"),
            ("bukan tidak bagus, tapi ya biasa aja", "Netral"),
            ("pelayanan ramah, respon cepat 😊", "Positif")
        ]
        
        print("🧪 Testing Enhanced Sentiment Analyzer:")
        print("=" * 60)
        
        correct_predictions = 0
        total_predictions = len(test_cases)
        
        for text, expected in test_cases:
            result = self.analyze_single_text(text)
            predicted = result['sentiment']
            confidence = result['confidence']
            score = result['sentiment_score']
            domain = result['domain']
            
            is_correct = predicted == expected
            if is_correct:
                correct_predictions += 1
            
            status = "✅" if is_correct else "❌"
            print(f"{status} Text: {text}")
            print(f"   Expected: {expected} | Got: {predicted}")
            print(f"   Score: {score:.3f} | Confidence: {confidence:.3f} | Domain: {domain}")
            
            # Show negation analysis if present
            if result['negation_analysis']['has_negation']:
                print(f"   Negation: {result['negation_analysis']}")
            
            print("---")
        
        accuracy = (correct_predictions / total_predictions) * 100
        print(f"🎯 Accuracy: {accuracy:.1f}% ({correct_predictions}/{total_predictions})")
        print("=" * 60)
        
        return accuracy
    
    def extract_keywords(self, reviews, word_set):
        """Extract top keywords from reviews - legacy method"""
        all_text = ' '.join(reviews)
        processed_text, _ = self.preprocess_text(all_text)
        words = processed_text.split()
        
        # Filter by word set and count
        relevant_words = [word for word in words if word in word_set]
        word_counts = Counter(relevant_words)
        
        return [word for word, count in word_counts.most_common(20)]
