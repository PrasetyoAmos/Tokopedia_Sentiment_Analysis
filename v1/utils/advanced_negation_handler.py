"""
Advanced Negation Handler for Indonesian Sentiment Analysis
Handles negation with proper scope and context awareness
"""

import re
from typing import List, Dict, Tuple

class AdvancedNegationHandler:
    """Advanced negation handling with contextual scope"""
    
    def __init__(self):
        self.negation_words = {
            'tidak', 'tak', 'bukan', 'jangan', 'belum', 
            'tanpa', 'tiada', 'gak', 'ga', 'kagak', 'gk',
            'nggak', 'ngga', 'enggak', 'engga'
        }
        
        # Different scope for different negation types
        self.negation_scopes = {
            'tidak': 3,
            'tak': 3,
            'bukan': 2,
            'gak': 3,
            'ga': 3,
            'belum': 4,
            'jangan': 2,
            'tanpa': 3,
            'tiada': 3
        }
        
        # Words that can terminate negation scope
        self.scope_terminators = {
            'tapi', 'tetapi', 'namun', 'akan tetapi', 'namanya',
            'malah', 'justru', 'sebaliknya', 'padahal',
            'kecuali', 'selain', 'walaupun', 'meskipun'
        }
        
        # Words that indicate continuation (don't terminate negation)
        self.continuation_words = {
            'dan', 'serta', 'juga', 'bahkan', 'pun'
        }
    
    def find_negation_patterns(self, tokens: List[str]) -> List[Dict]:
        """Find all negation patterns in the text"""
        negation_patterns = []
        
        for i, token in enumerate(tokens):
            if token.lower() in self.negation_words:
                scope = self.negation_scopes.get(token.lower(), 3)
                
                # Find actual scope (may be terminated early)
                actual_scope = self._find_actual_scope(tokens, i, scope)
                
                negation_patterns.append({
                    'position': i,
                    'word': token,
                    'scope_start': i + 1,
                    'scope_end': min(i + 1 + actual_scope, len(tokens)),
                    'affected_words': tokens[i + 1:min(i + 1 + actual_scope, len(tokens))]
                })
        
        return negation_patterns
    
    def _find_actual_scope(self, tokens: List[str], neg_pos: int, max_scope: int) -> int:
        """Find the actual scope of negation considering terminators"""
        actual_scope = 0
        
        for i in range(neg_pos + 1, min(neg_pos + 1 + max_scope, len(tokens))):
            token = tokens[i].lower()
            
            # Check for scope terminators
            if token in self.scope_terminators:
                break
            
            # Check for punctuation that might terminate scope
            if token in [',', '.', '!', '?', ';']:
                break
            
            actual_scope += 1
        
        return max(1, actual_scope)  # At least affect one word
    
    def handle_negation(self, tokens: List[str], word_sentiments: Dict[str, float]) -> Dict[str, float]:
        """
        Handle negation with proper scope and context
        Returns modified sentiment scores
        """
        modified_sentiments = word_sentiments.copy()
        negation_patterns = self.find_negation_patterns(tokens)
        
        for pattern in negation_patterns:
            # Check for double negation (negation + negation = positive)
            has_double_negation = self._check_double_negation(
                tokens, pattern['scope_start'], pattern['scope_end']
            )
            
            if has_double_negation:
                # Double negation - don't flip sentiment
                continue
            
            # Apply negation to affected words
            for word_pos in range(pattern['scope_start'], pattern['scope_end']):
                if word_pos < len(tokens):
                    word = tokens[word_pos].lower()
                    
                    if word in word_sentiments:
                        # Check if this is a "but" construction
                        if self._is_but_construction(tokens, pattern['position'], word_pos):
                            # In "tidak bagus tapi oke" - don't flip the second part
                            continue
                        
                        # Flip sentiment with some decay based on distance
                        distance = word_pos - pattern['scope_start']
                        decay_factor = max(0.7, 1.0 - (distance * 0.1))
                        
                        original_sentiment = word_sentiments[word]
                        flipped_sentiment = -original_sentiment * decay_factor
                        
                        modified_sentiments[word] = flipped_sentiment
                        
                        # Add negation confidence marker
                        modified_sentiments[f"_negated_{word}"] = 0.1
        
        return modified_sentiments
    
    def _check_double_negation(self, tokens: List[str], start: int, end: int) -> bool:
        """Check for double negation within scope"""
        negation_count = 0
        
        for i in range(start, end):
            if i < len(tokens) and tokens[i].lower() in self.negation_words:
                negation_count += 1
        
        return negation_count >= 1  # Already have one negation from the pattern
    
    def _is_but_construction(self, tokens: List[str], neg_pos: int, word_pos: int) -> bool:
        """Check if this is a 'but' construction like 'tidak A tapi B'"""
        # Look for conjunctions between negation and word
        for i in range(neg_pos + 1, word_pos):
            if i < len(tokens) and tokens[i].lower() in self.scope_terminators:
                return True
        return False
    
    def analyze_negation_context(self, text: str) -> Dict:
        """Analyze the negation context of the entire text"""
        # Clean and tokenize
        text_clean = re.sub(r'[^\w\s]', ' ', text.lower())
        tokens = text_clean.split()
        
        negation_patterns = self.find_negation_patterns(tokens)
        
        analysis = {
            'has_negation': len(negation_patterns) > 0,
            'negation_count': len(negation_patterns),
            'negation_words': [p['word'] for p in negation_patterns],
            'complex_negation': len(negation_patterns) > 1,
            'but_constructions': self._find_but_constructions(tokens),
            'confidence_modifier': self._calculate_confidence_modifier(negation_patterns)
        }
        
        return analysis
    
    def _find_but_constructions(self, tokens: List[str]) -> List[str]:
        """Find 'but' constructions in text"""
        constructions = []
        
        for i, token in enumerate(tokens):
            if token in self.scope_terminators:
                # Get context around the 'but' word
                start = max(0, i - 3)
                end = min(len(tokens), i + 4)
                context = ' '.join(tokens[start:end])
                constructions.append(context)
        
        return constructions
    
    def _calculate_confidence_modifier(self, negation_patterns: List[Dict]) -> float:
        """Calculate confidence modifier based on negation complexity"""
        if not negation_patterns:
            return 1.0
        
        # Simple negation = higher confidence
        if len(negation_patterns) == 1 and len(negation_patterns[0]['affected_words']) <= 2:
            return 0.9
        
        # Complex negation = lower confidence
        if len(negation_patterns) > 1:
            return 0.6
        
        # Medium complexity
        return 0.8

# Test the negation handler
if __name__ == "__main__":
    handler = AdvancedNegationHandler()
    
    test_cases = [
        "tidak buruk malah bagus banget",
        "gak jelek sih cuma mahal",
        "bukan tidak bagus tapi ya biasa aja",
        "tidak recommended banget",
        "belum pernah nyesal beli"
    ]
    
    for text in test_cases:
        print(f"Text: {text}")
        analysis = handler.analyze_negation_context(text)
        print(f"Analysis: {analysis}")
        print("---")
