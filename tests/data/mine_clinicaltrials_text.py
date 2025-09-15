#!/usr/bin/env python3
"""
ClinicalTrials.gov Text Mining for Realistic Clinical Language
Extracts medication-related text patterns from clinical trial descriptions
"""

import requests
import json
import re
import time
from typing import List, Dict, Any
from datetime import datetime

class ClinicalTrialsMiner:
    """Mines ClinicalTrials.gov for realistic clinical medication language"""

    def __init__(self):
        self.base_url = "https://clinicaltrials.gov/api/v2/studies"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; Clinical-NLP-Research/1.0)'
        })

    def search_medication_studies(self, medication: str, max_studies: int = 50) -> List[Dict]:
        """Search for clinical trials involving specific medications"""

        try:
            params = {
                'query.term': f'"{medication}" AND (dosage OR dose OR mg OR "twice daily" OR "once daily")',
                'format': 'json',
                'countTotal': 'true',
                'pageSize': min(max_studies, 100)
            }

            print(f"🔍 Searching for {medication} studies...")
            response = self.session.get(self.base_url, params=params)

            if response.status_code == 200:
                data = response.json()
                studies = data.get('studies', [])
                print(f"   Found {len(studies)} studies for {medication}")
                return studies
            else:
                print(f"   API Error for {medication}: {response.status_code}")
                return []

        except Exception as e:
            print(f"   Error searching for {medication}: {e}")
            return []

    def extract_medication_text(self, studies: List[Dict], medication: str) -> List[Dict[str, Any]]:
        """Extract medication-related text from study descriptions"""

        extracted_texts = []

        for study in studies:
            try:
                # Extract relevant text fields
                protocol_section = study.get('protocolSection', {})

                # Get study title
                title = protocol_section.get('identificationModule', {}).get('officialTitle', '')

                # Get brief summary
                description_module = protocol_section.get('descriptionModule', {})
                brief_summary = description_module.get('briefSummary', '')
                detailed_description = description_module.get('detailedDescription', '')

                # Get intervention descriptions
                interventions = []
                design_module = protocol_section.get('designModule', {})
                intervention_model = design_module.get('interventionModel', '')

                # Look for arms and interventions
                arms_interventions = protocol_section.get('armsInterventionsModule', {})
                if arms_interventions:
                    for intervention in arms_interventions.get('interventions', []):
                        intervention_name = intervention.get('name', '')
                        intervention_desc = intervention.get('description', '')
                        if medication.lower() in intervention_name.lower() or medication.lower() in intervention_desc.lower():
                            interventions.append({
                                'name': intervention_name,
                                'description': intervention_desc,
                                'type': intervention.get('type', '')
                            })

                # Combine all text
                all_text = f"{title} {brief_summary} {detailed_description}".strip()

                # Extract medication-related sentences
                sentences = self._extract_medication_sentences(all_text, medication)

                if sentences or interventions:
                    extracted_texts.append({
                        'study_id': protocol_section.get('identificationModule', {}).get('nctId', ''),
                        'medication': medication,
                        'title': title,
                        'sentences': sentences,
                        'interventions': interventions,
                        'source': 'clinicaltrials.gov'
                    })

            except Exception as e:
                print(f"   Error processing study: {e}")
                continue

        return extracted_texts

    def _extract_medication_sentences(self, text: str, medication: str) -> List[str]:
        """Extract sentences containing medication and dosing information"""

        if not text:
            return []

        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        medication_sentences = []

        # Dosing patterns to look for
        dosing_patterns = [
            r'\d+\s*mg',
            r'\d+\s*mcg',
            r'\d+\s*g\b',
            r'twice\s+daily',
            r'once\s+daily',
            r'three\s+times',
            r'\bBID\b',
            r'\bTID\b',
            r'\bQD\b',
            r'every\s+\d+\s+hours',
            r'\d+\s*times\s+daily'
        ]

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:  # Skip very short sentences
                continue

            # Check if sentence contains medication name and dosing info
            contains_medication = medication.lower() in sentence.lower()
            contains_dosing = any(re.search(pattern, sentence, re.IGNORECASE) for pattern in dosing_patterns)

            if contains_medication and contains_dosing:
                # Clean up sentence
                cleaned = re.sub(r'\s+', ' ', sentence)
                medication_sentences.append(cleaned)

        return medication_sentences[:5]  # Limit to 5 sentences per study

    def mine_multiple_medications(self, medications: List[str]) -> Dict[str, List[Dict]]:
        """Mine clinical trial data for multiple medications"""

        print("🏥 Mining ClinicalTrials.gov for realistic clinical language...")

        all_results = {}

        for medication in medications:
            studies = self.search_medication_studies(medication, max_studies=20)
            extracted = self.extract_medication_text(studies, medication)
            all_results[medication] = extracted

            # Rate limiting - be respectful to the API
            time.sleep(1)

        return all_results

    def create_test_cases_from_trials(self, trial_data: Dict[str, List[Dict]]) -> List[Dict[str, Any]]:
        """Convert clinical trial text into test cases"""

        test_cases = []
        case_id = 1

        for medication, studies in trial_data.items():
            for study in studies:
                # Process intervention descriptions
                for intervention in study.get('interventions', []):
                    if intervention.get('description'):
                        text = intervention['description']

                        # Try to extract structured information
                        extracted_info = self._extract_structured_info(text, medication)

                        if extracted_info:
                            test_cases.append({
                                'text': text,
                                'expected': extracted_info,
                                'complexity': 'clinical_trial',
                                'case_id': f'trial_{case_id}',
                                'source_study': study.get('study_id', ''),
                                'source_medication': medication
                            })
                            case_id += 1

                # Process extracted sentences
                for sentence in study.get('sentences', []):
                    extracted_info = self._extract_structured_info(sentence, medication)

                    if extracted_info:
                        test_cases.append({
                            'text': sentence,
                            'expected': extracted_info,
                            'complexity': 'clinical_trial',
                            'case_id': f'trial_{case_id}',
                            'source_study': study.get('study_id', ''),
                            'source_medication': medication
                        })
                        case_id += 1

        return test_cases[:30]  # Limit to 30 cases

    def _extract_structured_info(self, text: str, medication: str) -> Dict[str, Any]:
        """Extract structured information from clinical trial text"""

        info = {}

        # Extract medication (use base form)
        info['medication'] = medication

        # Extract dosage
        dosage_patterns = [
            r'(\d+(?:\.\d+)?)\s*(mg|mcg|g|milligrams?|micrograms?)',
            r'(\d+(?:\.\d+)?)\s*(mg/kg|mcg/kg)',
            r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*(mg|mcg|g)'
        ]

        for pattern in dosage_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    info['dosage'] = f"{match.group(1)}{match.group(2)}"
                elif len(match.groups()) == 3:
                    info['dosage'] = f"{match.group(1)}-{match.group(2)}{match.group(3)}"
                break

        # Extract frequency
        frequency_patterns = [
            (r'\bonce\s+daily\b', 'once daily'),
            (r'\btwice\s+daily\b', 'twice daily'),
            (r'\bthree\s+times\s+daily\b', 'three times daily'),
            (r'\bBID\b', 'BID'),
            (r'\bTID\b', 'TID'),
            (r'\bQD\b', 'QD'),
            (r'every\s+(\d+)\s+hours?', lambda m: f'every {m.group(1)} hours'),
            (r'(\d+)\s+times?\s+daily', lambda m: f'{m.group(1)} times daily')
        ]

        for pattern, replacement in frequency_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if callable(replacement):
                    info['frequency'] = replacement(match)
                else:
                    info['frequency'] = replacement
                break

        # Extract condition (basic pattern)
        condition_patterns = [
            r'for\s+(?:the\s+)?(?:treatment\s+of\s+)?([a-zA-Z\s]+?)(?:\.|,|$)',
            r'in\s+(?:patients\s+with\s+)?([a-zA-Z\s]+?)(?:\.|,|$)',
            r'(?:diagnosis|condition):\s*([a-zA-Z\s]+?)(?:\.|,|$)'
        ]

        for pattern in condition_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                condition = match.group(1).strip()
                if len(condition) > 3 and len(condition) < 50:  # Reasonable length
                    info['condition'] = condition
                    break

        # Only return if we have at least medication and one other field
        if len(info) >= 2:
            return info
        else:
            return {}

def main():
    """Mine ClinicalTrials.gov and create test cases"""

    # Focus on common medications that appear in our test data
    medications = [
        'amoxicillin',
        'ibuprofen',
        'metformin',
        'lisinopril',
        'prednisone'
    ]

    miner = ClinicalTrialsMiner()
    trial_data = miner.mine_multiple_medications(medications)

    # Create test cases from trial data
    test_cases = miner.create_test_cases_from_trials(trial_data)

    print(f"\n✅ Created {len(test_cases)} test cases from clinical trials")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save raw trial data
    with open(f'clinical_trials_data_{timestamp}.json', 'w') as f:
        json.dump(trial_data, f, indent=2)

    # Save test cases
    with open(f'clinical_trials_test_cases_{timestamp}.json', 'w') as f:
        json.dump(test_cases, f, indent=2)

    print(f"💾 Data saved to:")
    print(f"   - clinical_trials_data_{timestamp}.json")
    print(f"   - clinical_trials_test_cases_{timestamp}.json")

    # Show sample
    if test_cases:
        print(f"\n📋 Sample Clinical Trial Test Case:")
        sample = test_cases[0]
        print(f"   Text: {sample['text'][:100]}...")
        print(f"   Expected: {sample['expected']}")
        print(f"   Study: {sample['source_study']}")

    return test_cases

if __name__ == "__main__":
    main()