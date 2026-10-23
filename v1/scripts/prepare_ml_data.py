"""
🔧 ML DATA PREPARATION SCRIPT
Script untuk mempersiapkan data training yang optimal untuk IndoBERT fine-tuning

Author: AI Assistant  
Purpose: Clean, balance, dan prepare data untuk ML model training
"""

import pandas as pd
import numpy as np
import os
import json
from typing import Dict, List, Tuple
from sklearn.model_selection import train_test_split
from collections import Counter
import re
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLDataPreparator:
    """
    Class untuk mempersiapkan data training yang optimal untuk ML models
    """
    
    def __init__(self, workspace_path: str = "."):
        """
        Initialize data preparator
        
        Args:
            workspace_path: Path ke workspace folder
        """
        self.workspace_path = workspace_path
        self.min_text_length = 10  # Minimum characters untuk valid review
        self.max_text_length = 512  # Maximum untuk IndoBERT
        
        # Quality filters
        self.spam_patterns = [
            r'^[a-z]\s*$',  # Single letter reviews
            r'^.{1,3}$',    # Very short reviews
            r'^[^\w\s]+$',  # Only symbols
            r'^[0-9\s]+$'   # Only numbers
        ]
        
    def load_existing_data(self) -> pd.DataFrame:
        """
        Load semua CSV files yang ada di workspace
        
        Returns:
            Combined DataFrame dari semua files
        """
        logger.info("Loading existing CSV files...")
        
        # Find all CSV files in workspace and uploads folder
        csv_files = []
        
        # Check uploads folder first
        uploads_path = os.path.join(self.workspace_path, 'uploads')
        if os.path.exists(uploads_path):
            for file in os.listdir(uploads_path):
                if file.endswith('.csv') and not file.startswith('processed_'):
                    csv_files.append(os.path.join('uploads', file))
        
        # Then check workspace root
        for file in os.listdir(self.workspace_path):
            if file.endswith('.csv') and not file.startswith('processed_'):
                csv_files.append(file)
        
        if not csv_files:
            logger.warning("No CSV files found in workspace")
            return pd.DataFrame()
        
        # Load and combine all CSV files
        combined_df = pd.DataFrame()
        
        for csv_file in csv_files:
            try:
                filepath = os.path.join(self.workspace_path, csv_file)
                df = pd.read_csv(filepath, encoding='utf-8')
                
                # Standardize column names
                df = self._standardize_columns(df)
                
                # Add source file info
                df['source_file'] = csv_file
                
                combined_df = pd.concat([combined_df, df], ignore_index=True)
                logger.info(f"Loaded {len(df)} reviews from {csv_file}")
                
            except Exception as e:
                logger.warning(f"Error loading {csv_file}: {e}")
        
        logger.info(f"Total loaded: {len(combined_df)} reviews from {len(csv_files)} files")
        return combined_df
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize column names untuk consistency
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame dengan standardized columns
        """
        # Common column name mappings
        column_mappings = {
            'ulasan': 'review_text',
            'review': 'review_text',
            'text': 'review_text',
            'komentar': 'review_text',
            'rating': 'rating',
            'bintang': 'rating',
            'score': 'rating',
            'sentiment': 'sentiment_label',
            'label': 'sentiment_label'
        }
        
        # Rename columns
        df_renamed = df.rename(columns={col: column_mappings.get(col.lower(), col) 
                                      for col in df.columns})
        
        # Ensure required columns exist
        if 'review_text' not in df_renamed.columns:
            # Try to find text column
            text_columns = [col for col in df_renamed.columns if 
                          any(keyword in col.lower() for keyword in ['text', 'review', 'ulasan', 'comment'])]
            if text_columns:
                df_renamed['review_text'] = df_renamed[text_columns[0]]
        
        return df_renamed
    
    def clean_text_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean dan preprocess text data untuk training
        
        Args:
            df: Input DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        logger.info("Cleaning text data...")
        
        initial_count = len(df)
        
        # Remove rows tanpa review text
        df = df.dropna(subset=['review_text'])
        
        # Convert to string dan basic cleaning
        df['review_text'] = df['review_text'].astype(str)
        df['review_text'] = df['review_text'].str.strip()
        
        # Remove spam patterns
        for pattern in self.spam_patterns:
            df = df[~df['review_text'].str.match(pattern, case=False)]
        
        # Filter by text length
        df['text_length'] = df['review_text'].str.len()
        df = df[(df['text_length'] >= self.min_text_length) & 
                (df['text_length'] <= self.max_text_length)]
        
        # Remove duplicates (keep first occurrence)
        df = df.drop_duplicates(subset=['review_text'], keep='first')
        
        # Remove extremely repetitive text (same char repeated)
        df = df[~df['review_text'].str.match(r'^(.)\1{5,}$')]
        
        cleaned_count = len(df)
        logger.info(f"Text cleaning: {initial_count} -> {cleaned_count} reviews "
                   f"({cleaned_count/initial_count*100:.1f}% retained)")
        
        return df.drop('text_length', axis=1)
    
    def create_sentiment_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create consistent sentiment labels dari berbagai sumber
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame dengan sentiment labels
        """
        logger.info("Creating sentiment labels...")
        
        # If sentiment_label already exists, use it
        if 'sentiment_label' in df.columns:
            # Standardize existing labels
            df['sentiment_label'] = df['sentiment_label'].str.lower()
            df['sentiment_label'] = df['sentiment_label'].map({
                'positif': 1, 'positive': 1, 'pos': 1, '1': 1, 1: 1,
                'negatif': 0, 'negative': 0, 'neg': 0, '0': 0, 0: 0
            })
        
        # Create labels from rating if available
        elif 'rating' in df.columns:
            df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
            # Assume 5-star rating system: 1-2 = negative, 3 = neutral, 4-5 = positive
            # We'll exclude neutral (3) untuk cleaner binary classification
            df['sentiment_label'] = df['rating'].apply(lambda x: 
                1 if x >= 4 else (0 if x <= 2 else None))
            
            # Remove neutral ratings untuk binary classification
            df = df.dropna(subset=['sentiment_label'])
            df['sentiment_label'] = df['sentiment_label'].astype(int)
        
        else:
            logger.warning("No rating or sentiment columns found. Labels will need manual annotation.")
            return df
        
        # Remove rows dengan invalid labels
        df = df.dropna(subset=['sentiment_label'])
        
        label_counts = df['sentiment_label'].value_counts()
        logger.info(f"Label distribution: {dict(label_counts)}")
        
        return df
    
    def balance_dataset(self, df: pd.DataFrame, target_size: int = 10000) -> pd.DataFrame:
        """
        Balance dataset untuk optimal training
        
        Args:
            df: Input DataFrame
            target_size: Target total dataset size
            
        Returns:
            Balanced DataFrame
        """
        logger.info("Balancing dataset...")
        
        if 'sentiment_label' not in df.columns:
            logger.warning("No sentiment labels found. Cannot balance dataset.")
            return df
        
        # Calculate samples per class
        samples_per_class = target_size // 2
        
        positive_samples = df[df['sentiment_label'] == 1].sample(
            n=min(samples_per_class, len(df[df['sentiment_label'] == 1])),
            random_state=42
        )
        
        negative_samples = df[df['sentiment_label'] == 0].sample(
            n=min(samples_per_class, len(df[df['sentiment_label'] == 0])),
            random_state=42
        )
        
        balanced_df = pd.concat([positive_samples, negative_samples], ignore_index=True)
        balanced_df = balanced_df.sample(frac=1, random_state=42).reset_index(drop=True)
        
        final_counts = balanced_df['sentiment_label'].value_counts()
        logger.info(f"Balanced dataset: {dict(final_counts)} (total: {len(balanced_df)})")
        
        return balanced_df
    
    def enhance_with_synthetic_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enhance dataset dengan synthetic samples untuk edge cases
        
        Args:
            df: Input DataFrame
            
        Returns:
            Enhanced DataFrame dengan synthetic samples
        """
        logger.info("Adding synthetic edge case samples...")
        
        # Edge case samples untuk better model performance
        edge_cases = [
            # Negation cases
            ("tidak recommended produk ini", 0),
            ("tidak worth to buy", 0),
            ("tidak sebagus yang diharapkan", 0),
            ("tidak sesuai dengan foto", 0),
            ("tidak jelek sih tapi biasa aja", 0),
            ("tidak buruk tapi tidak bagus juga", 0),
            ("bukan yang terbaik tapi oke lah", 1),
            ("tidak mengecewakan", 1),
            
            # Indonesian expressions
            ("lumayan sih untuk harga segini", 1),
            ("cukup bagus untuk daily use", 1),
            ("sesuai ekspektasi", 1),
            ("worth to buy", 1),
            ("packaging rapi dan aman", 1),
            ("biasa aja gak spesial", 0),
            ("kurang memuaskan dibanding brand lain", 0),
            ("over price untuk kualitas segini", 0),
            ("agak mengecewakan", 0),
            
            # Emoji + text combinations
            ("bagus banget 😍😍😍", 1),
            ("kecewa 😞", 0),
            ("mantap jiwa 👍", 1),
            ("zonk 😤", 0),
            ("perfect 💯", 1),
            ("😐😐😐 biasa aja", 0),
            
            # Mixed sentiment (leaning direction)
            ("bagus tapi mahal", 1),
            ("murah tapi kualitas biasa", 0),
            ("pengiriman lama tapi produk oke", 1),
            ("pelayanan bagus tapi produk mengecewakan", 0),
            
            # E-commerce specific
            ("cod aman seller responsive", 1),
            ("sesuai foto dan deskripsi", 1),
            ("fast response seller", 1),
            ("packaging bubble wrap tebal", 1),
            ("barang ori tidak tiruan", 1),
            ("seller slow response", 0),
            ("packaging asal-asalan", 0),
            ("tidak sesuai size chart", 0),
            ("barang bekas dijual sebagai baru", 0)
        ]
        
        # Create synthetic DataFrame
        synthetic_df = pd.DataFrame(edge_cases, columns=['review_text', 'sentiment_label'])
        synthetic_df['source_file'] = 'synthetic_edge_cases'
        
        # Combine dengan existing data
        enhanced_df = pd.concat([df, synthetic_df], ignore_index=True)
        
        logger.info(f"Added {len(synthetic_df)} synthetic edge case samples")
        return enhanced_df
    
    def create_train_val_test_split(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Split data into train, validation, dan test sets
        
        Args:
            df: Input DataFrame
            
        Returns:
            Tuple of (train_df, val_df, test_df)
        """
        logger.info("Creating train/validation/test split...")
        
        # First split: separate test set (15%)
        train_val_df, test_df = train_test_split(
            df, test_size=0.15, random_state=42, 
            stratify=df['sentiment_label'] if 'sentiment_label' in df.columns else None
        )
        
        # Second split: separate train and validation (70% train, 15% val)
        train_df, val_df = train_test_split(
            train_val_df, test_size=0.176, random_state=42,  # 0.176 ≈ 15/85
            stratify=train_val_df['sentiment_label'] if 'sentiment_label' in train_val_df.columns else None
        )
        
        logger.info(f"Split sizes - Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
        
        # Log label distributions
        if 'sentiment_label' in df.columns:
            for name, data in [('Train', train_df), ('Val', val_df), ('Test', test_df)]:
                counts = data['sentiment_label'].value_counts()
                logger.info(f"{name} label distribution: {dict(counts)}")
        
        return train_df, val_df, test_df
    
    def save_prepared_data(self, train_df: pd.DataFrame, val_df: pd.DataFrame, 
                          test_df: pd.DataFrame, output_dir: str = "ml_data"):
        """
        Save prepared data untuk ML training
        
        Args:
            train_df: Training DataFrame
            val_df: Validation DataFrame  
            test_df: Test DataFrame
            output_dir: Output directory
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Save DataFrames
        train_df.to_csv(f"{output_dir}/train_data.csv", index=False, encoding='utf-8')
        val_df.to_csv(f"{output_dir}/val_data.csv", index=False, encoding='utf-8')
        test_df.to_csv(f"{output_dir}/test_data.csv", index=False, encoding='utf-8')
        
        # Save metadata
        metadata = {
            'total_samples': len(train_df) + len(val_df) + len(test_df),
            'train_samples': len(train_df),
            'val_samples': len(val_df),
            'test_samples': len(test_df),
            'features': list(train_df.columns),
            'label_distribution': {
                'train': dict(train_df['sentiment_label'].value_counts()) if 'sentiment_label' in train_df.columns else {},
                'val': dict(val_df['sentiment_label'].value_counts()) if 'sentiment_label' in val_df.columns else {},
                'test': dict(test_df['sentiment_label'].value_counts()) if 'sentiment_label' in test_df.columns else {}
            },
            'preparation_params': {
                'min_text_length': self.min_text_length,
                'max_text_length': self.max_text_length,
                'balanced': True,
                'synthetic_samples': True
            }
        }
        
        with open(f"{output_dir}/metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Data saved to {output_dir}/")
        logger.info(f"Files created: train_data.csv, val_data.csv, test_data.csv, metadata.json")
    
    def generate_quality_report(self, df: pd.DataFrame) -> Dict:
        """
        Generate quality report untuk prepared data
        
        Args:
            df: Prepared DataFrame
            
        Returns:
            Quality report dictionary
        """
        report = {
            'total_samples': len(df),
            'columns': list(df.columns),
            'missing_values': dict(df.isnull().sum()),
            'text_length_stats': {
                'mean': float(df['review_text'].str.len().mean()),
                'median': float(df['review_text'].str.len().median()),
                'min': int(df['review_text'].str.len().min()),
                'max': int(df['review_text'].str.len().max())
            }
        }
        
        if 'sentiment_label' in df.columns:
            report['label_distribution'] = dict(df['sentiment_label'].value_counts())
            report['label_balance'] = {
                'is_balanced': abs(df['sentiment_label'].value_counts().iloc[0] - 
                                 df['sentiment_label'].value_counts().iloc[1]) < len(df) * 0.1
            }
        
        # Text quality checks
        avg_words = df['review_text'].str.split().str.len().mean()
        report['text_quality'] = {
            'avg_words_per_review': float(avg_words),
            'has_emoji': int(df['review_text'].str.contains('😀|😊|😍|😭|😡', regex=True).sum()),
            'has_numbers': int(df['review_text'].str.contains(r'\d').sum())
        }
        
        return report


def main():
    """
    Main function untuk menjalankan data preparation
    """
    logger.info("🚀 Starting ML Data Preparation...")
    
    # Initialize preparator
    preparator = MLDataPreparator()
    
    # Step 1: Load existing data
    df = preparator.load_existing_data()
    if df.empty:
        logger.error("No data found. Please ensure CSV files are in the workspace.")
        return
    
    # Step 2: Clean text data
    df_clean = preparator.clean_text_data(df)
    
    # Step 3: Create sentiment labels
    df_labeled = preparator.create_sentiment_labels(df_clean)
    
    # Step 4: Balance dataset
    df_balanced = preparator.balance_dataset(df_labeled, target_size=10000)
    
    # Step 5: Enhance dengan synthetic data
    df_enhanced = preparator.enhance_with_synthetic_data(df_balanced)
    
    # Step 6: Create train/val/test split
    train_df, val_df, test_df = preparator.create_train_val_test_split(df_enhanced)
    
    # Step 7: Save prepared data
    preparator.save_prepared_data(train_df, val_df, test_df)
    
    # Step 8: Generate quality report
    report = preparator.generate_quality_report(df_enhanced)
    
    with open("ml_data/quality_report.json", 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info("✅ Data preparation completed successfully!")
    logger.info("📊 Quality Report Summary:")
    logger.info(f"   Total samples: {report['total_samples']}")
    logger.info(f"   Average words per review: {report['text_quality']['avg_words_per_review']:.1f}")
    if 'label_distribution' in report:
        logger.info(f"   Label distribution: {report['label_distribution']}")
    
    logger.info("\n🎯 Next Steps:")
    logger.info("1. Review quality_report.json untuk data insights")
    logger.info("2. Run ML training dengan prepared data:")
    logger.info("   python -c \"from ml_integration_template import IndoBERTSentimentAnalyzer; analyzer = IndoBERTSentimentAnalyzer(); analyzer.load_model()\"")
    logger.info("3. Fine-tune model dengan train_data.csv")


if __name__ == "__main__":
    main()
