#!/usr/bin/env python3
"""
Debug regex patterns directly
"""

import re

def test_pattern_matching():
    """Test individual regex patterns"""
    
    # Test cases
    test_cases = [
        "Order CBC and comprehensive metabolic panel for routine health screening",
        "Order HbA1c level and lipid panel for diabetes monitoring",
        "Start patient on Sertraline 100mg daily for depression",
        "Prescribe Albuterol inhaler 2 puffs every 6 hours",
        "Start metformin 500mg twice daily"
    ]
    
    # Current lab patterns
    lab_patterns = [
        r'(blood\s+test|cbc|complete\s+blood\s+count|chemistry|lipid\s+panel|glucose\s+monitoring|a1c|hba1c|hemoglobin\s+a1c|bun|creatinine|renal\s+function|electrolytes|liver\s+enzymes|comprehensive\s+metabolic\s+panel|cmp|basic\s+metabolic\s+panel|bmp)',
        r'(lab|laboratory)\s+(?:test|work|panel)',
        r'draw\s+(blood|labs)',
        r'order\s+(blood\s+work|labs|lipid\s+panel)',
        r'baseline\s+(renal\s+function|electrolytes|liver\s+function)'
    ]
    
    # Current medication patterns
    med_patterns = [
        r'(\w+)\s*(\d+)\s*(mg|g|ml|units?)\s*(daily|twice|three times|once)',
        r'(prozac|fluoxetine|amoxicillin|metformin|lisinopril|aspirin|sertraline|zoloft|albuterol|ceftriaxone|insulin|glargine|ibuprofen|digoxin|tramadol|timolol|calcium|carbonate|finasteride|doxycycline|montelukast|acetylcysteine|prednisone|fluconazole|nicotine|rosuvastatin|lorazepam|tylenol|acetaminophen|ambien|zolpidem|atorvastatin|lipitor)\s*(\d+)?\s*(mg|g|ml|units?|puffs?|drops?|patch|inhaler)?',
        r'start\s+(?:patient\s+)?(?:on\s+)?(\w+)',
    ]
    
    print("🔍 Debug Pattern Matching")
    print("=" * 50)
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {text}")
        text_lower = text.lower()
        
        # Test lab patterns
        lab_found = []
        for pattern in lab_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                print(f"   Lab pattern '{pattern[:50]}...' matched: {matches}")
                lab_found.extend(matches)
        
        # Test med patterns
        med_found = []
        for pattern in med_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                print(f"   Med pattern '{pattern[:50]}...' matched: {matches}")
                med_found.extend(matches)
        
        print(f"   📊 Total matches - Labs: {len(lab_found)}, Medications: {len(med_found)}")

if __name__ == "__main__":
    test_pattern_matching()