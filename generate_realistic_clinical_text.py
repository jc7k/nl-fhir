#!/usr/bin/env python3
"""
Realistic Clinical Text Generator for F1 Validation
Generates clinical orders with real-world complexity to test overfitting hypothesis
"""

import random
import re
from typing import List, Dict, Any
from datetime import datetime

class RealisticClinicalTextGenerator:
    """Generates clinical text with real-world complexity and variations"""

    def __init__(self):
        # Real-world medication variations (includes common misspellings, abbreviations)
        self.medications = {
            "amoxicillin": ["amoxicillin", "amoxil", "amox", "amoxicillin/clavulanate", "amoxicillin-clavulanic acid"],
            "ibuprofen": ["ibuprofen", "advil", "motrin", "IBU", "ibu"],
            "lisinopril": ["lisinopril", "prinivil", "zestril", "ACE inhibitor lisinopril"],
            "metformin": ["metformin", "glucophage", "metformin HCl", "metformin hydrochloride"],
            "albuterol": ["albuterol", "ventolin", "proventil", "salbutamol", "albuterol sulfate"],
            "prednisone": ["prednisone", "deltasone", "prednisolone", "pred"],
            "warfarin": ["warfarin", "coumadin", "warfarin sodium"],
            "morphine": ["morphine", "MS", "morphine sulfate", "MSO4", "morphine SO4"],
            "epinephrine": ["epinephrine", "epi", "adrenaline", "epinephrine HCl"]
        }

        # Real dosage variations (messy, inconsistent formats)
        self.dosage_patterns = [
            "{amount}mg", "{amount} mg", "{amount}MG", "{amount} MG",
            "{amount}mcg", "{amount} mcg", "{amount}μg",
            "{amount} milligrams", "{amount}mg/kg", "{amount} mg/kg body weight",
            "{amount}mg/m2", "{amount} mg per kg", "{amount}mg/day divided",
            "~{amount}mg", "approximately {amount}mg", "{amount}-{amount2}mg",
            "{amount} to {amount2}mg", "{amount}mg (range: {amount}-{amount2}mg)"
        ]

        # Real frequency variations (clinical abbreviations, inconsistencies)
        self.frequency_patterns = [
            "daily", "once daily", "QD", "q24h", "every 24 hours",
            "twice daily", "BID", "b.i.d.", "q12h", "every 12 hours", "2x/day",
            "three times daily", "TID", "t.i.d.", "q8h", "every 8 hours", "3x daily",
            "four times daily", "QID", "q.i.d.", "q6h", "every 6 hours",
            "as needed", "PRN", "p.r.n.", "when needed", "if needed",
            "at bedtime", "QHS", "q.h.s.", "before sleep", "nightly",
            "every other day", "QOD", "q.o.d.", "alternate days",
            "weekly", "once weekly", "q7d", "every week"
        ]

        # Real clinical conditions with variations
        self.conditions = {
            "infection": ["infection", "bacterial infection", "UTI", "upper respiratory infection", "cellulitis"],
            "pain": ["pain", "acute pain", "chronic pain", "post-operative pain", "breakthrough pain"],
            "hypertension": ["hypertension", "HTN", "high blood pressure", "elevated BP", "hypertensive crisis"],
            "diabetes": ["diabetes", "DM", "diabetes mellitus", "T2DM", "type 2 diabetes", "diabetic"],
            "asthma": ["asthma", "bronchial asthma", "reactive airway disease", "RAD", "asthmatic bronchitis"],
            "anxiety": ["anxiety", "anxiety disorder", "GAD", "generalized anxiety", "panic disorder"]
        }

        # Real patient name variations (including titles, nicknames)
        self.patient_names = [
            "John Smith", "J. Smith", "Mr. John Smith", "Smith, John",
            "Maria Rodriguez", "M. Rodriguez", "Mrs. Rodriguez", "Rodriguez, M.",
            "David Chen", "D. Chen", "Dr. Chen", "Chen, David MD",
            "Sarah Johnson", "S. Johnson", "Ms. Johnson", "Johnson, Sarah RN",
            "Michael Brown", "Mike Brown", "M. Brown", "Brown, Michael",
            "Jennifer Davis", "Jen Davis", "J. Davis", "Davis, Jennifer",
            "Robert Wilson", "Bob Wilson", "R. Wilson", "Wilson, Robert",
            "Lisa Anderson", "L. Anderson", "Anderson, Lisa", "Ms. Anderson"
        ]

        # Clinical context variations (real documentation styles)
        self.clinical_contexts = [
            "Started patient {patient} on {medication} {dosage} {frequency} for {condition}.",
            "Prescribed {medication} {dosage} {frequency} to patient {patient} for treatment of {condition}.",
            "Patient {patient}: Begin {medication} {dosage} {frequency} for {condition} management.",
            "{patient} - {medication} {dosage} {frequency} indicated for {condition}.",
            "Rx: {medication} {dosage} {frequency} for {patient} (diagnosis: {condition})",
            "Plan: {medication} {dosage} {frequency} for {patient}'s {condition}",
            "{patient} to start {medication} {dosage} {frequency} secondary to {condition}",
            "Initiate {medication} therapy {dosage} {frequency} in patient {patient} due to {condition}",
            "Patient {patient} will receive {medication} {dosage} {frequency} given {condition}",
            "{medication} {dosage} {frequency} ordered for {patient} - working diagnosis {condition}"
        ]

        # Real clinical complications (makes parsing harder)
        self.clinical_complications = [
            "Continue current dose if tolerated well",
            "Adjust dose based on renal function",
            "Monitor for side effects",
            "May increase to maximum dose if needed",
            "Taper slowly if discontinuing",
            "Take with food to reduce GI upset",
            "Check levels in 1 week",
            "Hold if systolic BP <100",
            "Contraindicated if allergic to penicillin",
            "Use caution in elderly patients"
        ]

    def generate_clean_cases(self, num_cases: int = 20) -> List[Dict[str, Any]]:
        """Generate clean, well-structured cases similar to our test data"""
        cases = []

        for i in range(num_cases):
            # Use consistent, clean patterns
            medication = random.choice(list(self.medications.keys()))
            dosage = f"{random.choice([25, 50, 100, 250, 500])}mg"
            frequency = random.choice(["daily", "twice daily", "three times daily"])
            condition = random.choice([
                "acute otitis media", "hypertension", "type 2 diabetes",
                "asthma exacerbation", "bacterial infection"
            ])
            patient = random.choice(self.patient_names[:5])  # Use clean names

            text = f"Started patient {patient} on {medication} {dosage} {frequency} for {condition}."

            expected = {
                "patient": patient,
                "medication": medication,
                "dosage": dosage,
                "frequency": frequency,
                "condition": condition
            }

            cases.append({
                "text": text,
                "expected": expected,
                "complexity": "clean",
                "case_id": f"clean_{i+1}"
            })

        return cases

    def generate_realistic_cases(self, num_cases: int = 50) -> List[Dict[str, Any]]:
        """Generate realistic clinical text with real-world complexity"""
        cases = []

        for i in range(num_cases):
            # Use varied medication names
            base_med = random.choice(list(self.medications.keys()))
            medication = random.choice(self.medications[base_med])

            # Use varied dosage patterns
            amount = random.choice([5, 10, 15, 20, 25, 50, 75, 100, 125, 250, 500, 1000])
            amount2 = amount + random.choice([5, 10, 25])
            dosage_pattern = random.choice(self.dosage_patterns)
            dosage = dosage_pattern.format(amount=amount, amount2=amount2)

            # Use varied frequency patterns
            frequency = random.choice(self.frequency_patterns)

            # Use varied condition descriptions
            base_condition = random.choice(list(self.conditions.keys()))
            condition = random.choice(self.conditions[base_condition])

            # Use varied patient names
            patient = random.choice(self.patient_names)

            # Use varied clinical context
            context = random.choice(self.clinical_contexts)

            # Add clinical complications sometimes
            complication = ""
            if random.random() < 0.3:  # 30% chance
                complication = " " + random.choice(self.clinical_complications)

            text = context.format(
                patient=patient,
                medication=medication,
                dosage=dosage,
                frequency=frequency,
                condition=condition
            ) + complication

            # Expected values use base forms for comparison
            expected = {
                "patient": patient.split(',')[0].replace('Mr. ', '').replace('Mrs. ', '').replace('Ms. ', '').replace('Dr. ', '').strip(),
                "medication": base_med,  # Base medication name
                "dosage": dosage,
                "frequency": frequency,
                "condition": condition
            }

            cases.append({
                "text": text,
                "expected": expected,
                "complexity": "realistic",
                "case_id": f"realistic_{i+1}"
            })

        return cases

    def generate_complex_cases(self, num_cases: int = 30) -> List[Dict[str, Any]]:
        """Generate highly complex clinical text that mimics real EHR notes"""
        cases = []

        complex_templates = [
            "Assessment and Plan: {patient} is a {age}-year-old with history of {condition}. Continue {medication} {dosage} {frequency}. {complication} Follow-up in clinic.",
            "ORDERS: For patient {patient} - {medication} {dosage} {frequency} for {condition}. {complication} Will reassess response.",
            "{patient} (MRN: {mrn}) - {condition} stable on current regimen. Continuing {medication} {dosage} {frequency}. {complication}",
            "Plan for {patient}: 1) {condition} - continue {medication} {dosage} {frequency} 2) {complication} 3) Lab follow-up in 1 week",
            "Patient {patient} presents with {condition}. Initiating treatment with {medication} {dosage} {frequency}. {complication} Pharmacy consulted.",
            "DISCHARGE ORDERS: {patient} to go home on {medication} {dosage} {frequency} for {condition}. {complication} RTC PRN worsening symptoms."
        ]

        for i in range(num_cases):
            # Complex variations
            base_med = random.choice(list(self.medications.keys()))
            medication = random.choice(self.medications[base_med])

            # Complex dosage with ranges and modifications
            amount = random.choice([2.5, 5, 7.5, 12.5, 37.5, 62.5, 87.5, 125, 375, 625])
            dosage_variations = [
                f"{amount}mg",
                f"{amount}mg (start), may increase to {amount*2}mg",
                f"{amount}-{amount+5}mg depending on response",
                f"~{amount}mg (approximately)",
                f"{amount}mg divided doses"
            ]
            dosage = random.choice(dosage_variations)

            # Complex frequency with modifications
            base_freq = random.choice(self.frequency_patterns)
            freq_modifications = [
                base_freq,
                f"{base_freq} with meals",
                f"{base_freq} (may adjust based on tolerance)",
                f"{base_freq}, hold if SBP <100",
                f"{base_freq} x 7 days, then reassess"
            ]
            frequency = random.choice(freq_modifications)

            # Complex conditions
            base_condition = random.choice(list(self.conditions.keys()))
            condition_variations = self.conditions[base_condition] + [
                f"acute exacerbation of {base_condition}",
                f"chronic {base_condition} with acute flare",
                f"{base_condition} refractory to previous treatment"
            ]
            condition = random.choice(condition_variations)

            # Complex patient identifiers
            patient_base = random.choice(self.patient_names)
            patient_variations = [
                patient_base,
                f"{patient_base} (DOB: {random.randint(1940, 2000)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d})",
                f"{patient_base.split()[0]} {patient_base.split()[1][0]}.",
                patient_base.replace(' ', ', ')
            ]
            patient = random.choice(patient_variations)

            # Complex clinical context
            template = random.choice(complex_templates)
            age = random.randint(18, 89)
            mrn = f"{random.randint(100000, 999999)}"
            complication = random.choice(self.clinical_complications)

            text = template.format(
                patient=patient,
                age=age,
                mrn=mrn,
                medication=medication,
                dosage=dosage,
                frequency=frequency,
                condition=condition,
                complication=complication
            )

            # Expected values for comparison
            expected = {
                "patient": patient_base.split(',')[0].replace('Mr. ', '').replace('Mrs. ', '').replace('Ms. ', '').replace('Dr. ', '').strip(),
                "medication": base_med,
                "dosage": dosage,
                "frequency": frequency,
                "condition": condition
            }

            cases.append({
                "text": text,
                "expected": expected,
                "complexity": "complex",
                "case_id": f"complex_{i+1}"
            })

        return cases

    def generate_all_test_cases(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generate comprehensive test dataset"""

        print("🏭 Generating realistic clinical text for F1 validation...")

        clean_cases = self.generate_clean_cases(20)
        realistic_cases = self.generate_realistic_cases(50)
        complex_cases = self.generate_complex_cases(30)

        all_cases = {
            "clean": clean_cases,
            "realistic": realistic_cases,
            "complex": complex_cases,
            "summary": {
                "clean_count": len(clean_cases),
                "realistic_count": len(realistic_cases),
                "complex_count": len(complex_cases),
                "total_count": len(clean_cases) + len(realistic_cases) + len(complex_cases)
            }
        }

        print(f"✅ Generated {all_cases['summary']['total_count']} clinical text cases:")
        print(f"   - Clean cases: {all_cases['summary']['clean_count']}")
        print(f"   - Realistic cases: {all_cases['summary']['realistic_count']}")
        print(f"   - Complex cases: {all_cases['summary']['complex_count']}")

        return all_cases

def main():
    """Generate and save realistic clinical test cases"""
    generator = RealisticClinicalTextGenerator()
    test_cases = generator.generate_all_test_cases()

    # Save to JSON file
    import json
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"realistic_clinical_test_cases_{timestamp}.json"

    with open(filename, 'w') as f:
        json.dump(test_cases, f, indent=2)

    print(f"\n💾 Test cases saved to: {filename}")

    # Display sample cases
    print(f"\n📋 Sample Cases by Complexity:")
    print(f"\n🟢 CLEAN Example:")
    print(f"   Text: {test_cases['clean'][0]['text']}")
    print(f"   Expected: {test_cases['clean'][0]['expected']}")

    print(f"\n🟡 REALISTIC Example:")
    print(f"   Text: {test_cases['realistic'][0]['text']}")
    print(f"   Expected: {test_cases['realistic'][0]['expected']}")

    print(f"\n🔴 COMPLEX Example:")
    print(f"   Text: {test_cases['complex'][0]['text']}")
    print(f"   Expected: {test_cases['complex'][0]['expected']}")

    return test_cases

if __name__ == "__main__":
    main()