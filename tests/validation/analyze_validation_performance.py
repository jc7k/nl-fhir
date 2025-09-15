#!/usr/bin/env python3
"""
Clinical Validation Performance Analysis
Generates honest performance metrics and visualizations
"""

import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Dict, List, Tuple
import pandas as pd
from collections import defaultdict

def load_test_results(filepath: str) -> Dict:
    """Load validation test results"""
    with open(filepath, 'r') as f:
        return json.load(f)

def create_confusion_matrix_data(results: List[Dict]) -> Tuple[int, int, int, int]:
    """
    Create confusion matrix data from test results
    
    Returns:
        (true_positives, false_positives, true_negatives, false_negatives)
    """
    true_positives = 0   # Correctly detected problematic cases
    false_positives = 0  # Incorrectly flagged as problematic  
    true_negatives = 0   # Correctly passed valid cases (not applicable - all test cases are negative)
    false_negatives = 0  # Missed problematic cases
    
    for result in results:
        detected_issues = result['validation_result']['issues_detected'] > 0
        detected_correctly = result.get('detected_correctly', False)
        
        if detected_issues and detected_correctly:
            true_positives += 1
        elif detected_issues and not detected_correctly:
            false_positives += 1
        elif not detected_issues:  # Missed detection
            false_negatives += 1
        # true_negatives = 0 (all test cases are problematic by design)
    
    return true_positives, false_positives, true_negatives, false_negatives

def plot_confusion_matrix(tp: int, fp: int, tn: int, fn: int, title: str = "Clinical Validation Performance"):
    """Plot confusion matrix"""
    
    # Create confusion matrix
    cm = np.array([[tp, fp],
                   [fn, tn if tn > 0 else 0]])  # Handle case where tn=0
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, 
                annot=True, 
                fmt='d', 
                cmap='Blues',
                xticklabels=['Predicted: Issue', 'Predicted: OK'],
                yticklabels=['Actual: Issue', 'Actual: OK'])
    
    plt.title(f'{title}\nActual Performance Metrics')
    plt.ylabel('Actual Condition')
    plt.xlabel('Predicted Condition')
    
    # Add performance metrics as text
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    metrics_text = f"""
Performance Metrics:
Precision: {precision:.1%} ({tp}/{tp + fp})
Recall: {recall:.1%} ({tp}/{tp + fn})
F1-Score: {f1_score:.3f}
False Positive Rate: {fp / (tp + fp):.1%}
    """.strip()
    
    plt.figtext(0.02, 0.02, metrics_text, fontsize=10, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
    
    plt.tight_layout()
    plt.savefig('clinical_results/confusion_matrix.png', dpi=300, bbox_inches='tight')
    plt.show()

def analyze_category_performance(results: List[Dict]) -> pd.DataFrame:
    """Analyze performance by medical specialty"""
    
    category_stats = defaultdict(lambda: {'total': 0, 'detected': 0, 'correct': 0, 'missed': 0, 'false_pos': 0})
    
    for result in results:
        specialty = result['test_case']['specialty']
        detected = result['validation_result']['issues_detected'] > 0
        correct = result.get('detected_correctly', False)
        
        category_stats[specialty]['total'] += 1
        
        if detected:
            category_stats[specialty]['detected'] += 1
            if correct:
                category_stats[specialty]['correct'] += 1
            else:
                category_stats[specialty]['false_pos'] += 1
        else:
            category_stats[specialty]['missed'] += 1
    
    # Convert to DataFrame
    data = []
    for specialty, stats in category_stats.items():
        precision = stats['correct'] / stats['detected'] if stats['detected'] > 0 else 0
        recall = stats['correct'] / stats['total']
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        data.append({
            'Specialty': specialty,
            'Total Cases': stats['total'],
            'Detected': stats['detected'], 
            'Correct': stats['correct'],
            'False Positives': stats['false_pos'],
            'Missed': stats['missed'],
            'Precision': precision,
            'Recall': recall,
            'F1-Score': f1
        })
    
    return pd.DataFrame(data)

def plot_specialty_performance(df: pd.DataFrame):
    """Plot performance by medical specialty"""
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Clinical Validation Performance by Medical Specialty', fontsize=16)
    
    # Precision by specialty
    axes[0,0].bar(range(len(df)), df['Precision'])
    axes[0,0].set_title('Precision by Specialty')
    axes[0,0].set_ylabel('Precision')
    axes[0,0].set_xticks(range(len(df)))
    axes[0,0].set_xticklabels(df['Specialty'], rotation=45, ha='right')
    axes[0,0].axhline(y=0.5, color='r', linestyle='--', alpha=0.7, label='50% baseline')
    axes[0,0].legend()
    
    # Recall by specialty
    axes[0,1].bar(range(len(df)), df['Recall'], color='orange')
    axes[0,1].set_title('Recall by Specialty') 
    axes[0,1].set_ylabel('Recall')
    axes[0,1].set_xticks(range(len(df)))
    axes[0,1].set_xticklabels(df['Specialty'], rotation=45, ha='right')
    axes[0,1].axhline(y=0.5, color='r', linestyle='--', alpha=0.7, label='50% baseline')
    axes[0,1].legend()
    
    # False Positives
    axes[1,0].bar(range(len(df)), df['False Positives'], color='red', alpha=0.7)
    axes[1,0].set_title('False Positives by Specialty')
    axes[1,0].set_ylabel('False Positive Count')
    axes[1,0].set_xticks(range(len(df)))
    axes[1,0].set_xticklabels(df['Specialty'], rotation=45, ha='right')
    
    # F1-Score
    axes[1,1].bar(range(len(df)), df['F1-Score'], color='green', alpha=0.7)
    axes[1,1].set_title('F1-Score by Specialty')
    axes[1,1].set_ylabel('F1-Score')
    axes[1,1].set_xticks(range(len(df)))
    axes[1,1].set_xticklabels(df['Specialty'], rotation=45, ha='right')
    axes[1,1].axhline(y=0.5, color='r', linestyle='--', alpha=0.7, label='50% baseline')
    axes[1,1].legend()
    
    plt.tight_layout()
    plt.savefig('clinical_results/specialty_performance.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_performance_summary_table(tp: int, fp: int, tn: int, fn: int) -> pd.DataFrame:
    """Create summary performance table"""
    
    total = tp + fp + tn + fn
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    accuracy = (tp + tn) / total if total > 0 else 0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    
    data = {
        'Metric': [
            'True Positives', 'False Positives', 'True Negatives', 'False Negatives',
            'Precision', 'Recall (Sensitivity)', 'Specificity', 'F1-Score', 'Accuracy'
        ],
        'Value': [
            tp, fp, tn, fn,
            f"{precision:.1%}", f"{recall:.1%}", f"{specificity:.1%}", 
            f"{f1_score:.3f}", f"{accuracy:.1%}"
        ],
        'Clinical Interpretation': [
            'Correctly identified problematic orders',
            'Valid orders incorrectly flagged as problematic',
            'Valid orders correctly passed (N/A - all test cases problematic)',
            'Problematic orders missed by system',
            'Of flagged cases, how many were actually problematic',
            'Of problematic cases, how many were caught',
            'Of valid cases, how many were correctly passed',
            'Harmonic mean of precision and recall',
            'Overall correctness rate'
        ]
    }
    
    return pd.DataFrame(data)

def main():
    """Main analysis function"""
    print("🔍 Clinical Validation Performance Analysis")
    print("=" * 50)
    
    # Load test results
    results_data = load_test_results('clinical_results/negative_validation_results_20250911_224718.json')
    detailed_results = results_data['detailed_results']
    
    # Calculate confusion matrix
    tp, fp, tn, fn = create_confusion_matrix_data(detailed_results)
    
    print(f"Raw Numbers:")
    print(f"  True Positives (Correct detections): {tp}")
    print(f"  False Positives (Incorrect flags): {fp}")
    print(f"  False Negatives (Missed cases): {fn}")
    print(f"  True Negatives: {tn} (N/A - all test cases problematic)")
    
    # Create visualizations
    plot_confusion_matrix(tp, fp, tn, fn)
    
    # Analyze by specialty
    specialty_df = analyze_category_performance(detailed_results)
    plot_specialty_performance(specialty_df)
    
    # Create summary table
    summary_df = create_performance_summary_table(tp, fp, tn, fn)
    print("\n" + "=" * 50)
    print("PERFORMANCE SUMMARY TABLE")
    print("=" * 50)
    print(summary_df.to_string(index=False))
    
    # Save detailed analysis
    specialty_df.to_csv('clinical_results/specialty_analysis.csv', index=False)
    summary_df.to_csv('clinical_results/performance_summary.csv', index=False)
    
    print(f"\n📊 Visualizations saved:")
    print(f"  - clinical_results/confusion_matrix.png")
    print(f"  - clinical_results/specialty_performance.png")
    print(f"  - clinical_results/specialty_analysis.csv")
    print(f"  - clinical_results/performance_summary.csv")

if __name__ == "__main__":
    main()