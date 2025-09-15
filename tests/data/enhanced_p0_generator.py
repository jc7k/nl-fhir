#!/usr/bin/env python3
"""
Enhanced P0 Specialty Test Generator
Production-ready test case generation for critical specialties
Focus: Emergency Medicine, Pediatrics, Cardiology, Oncology
"""

import random
import re
import json
import asyncio
from typing import List, Dict, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

# Import existing research sources
from mine_clinicaltrials_text import ClinicalTrialsMiner
from generate_realistic_clinical_text import RealisticClinicalTextGenerator

@dataclass
class EnhancedTestCase:
    text: str
    expected: Dict[str, Any]
    specialty: str
    complexity: str
    case_type: str
    priority: str
    test_level: str
    case_id: str
    source: str
    clinical_context: str
    f1_optimization_focus: str
    validation_notes: str = ""

class EnhancedP0SpecialtyGenerator:
    """Enhanced generator for P0 specialties with F1 optimization focus"""

    def __init__(self):
        self.clinical_trials_miner = ClinicalTrialsMiner()
        self.realistic_generator = RealisticClinicalTextGenerator()
        self.p0_patterns = self._load_enhanced_p0_patterns()

    def _load_enhanced_p0_patterns(self) -> Dict[str, Dict]:
        """Load enhanced patterns for P0 specialties based on F1 research"""

        return {
            "emergency": {
                "priority": "P0",
                "current_f1": 0.571,
                "target_f1": 0.80,
                "f1_gap_analysis": {
                    "missing_urgency_detection": "Critical time indicators not captured",
                    "severity_modifier_confusion": "Mild vs severe not distinguished",
                    "multi_medication_orders": "Complex orders with multiple meds"
                },
                "enhanced_medications": {
                    "critical_care": ["epinephrine", "norepinephrine", "dopamine", "vasopressin"],
                    "pain_management": ["morphine", "fentanyl", "hydromorphone", "ketamine"],
                    "sedation": ["midazolam", "propofol", "dexmedetomidine", "lorazepam"],
                    "cardiac": ["adenosine", "amiodarone", "metoprolol", "esmolol"],
                    "respiratory": ["albuterol", "ipratropium", "methylprednisolone"]
                },
                "urgency_indicators": {
                    "immediate": ["STAT", "NOW", "IMMEDIATELY", "EMERGENT", "CRITICAL"],
                    "time_specific": ["within 5 minutes", "q5min", "every 5 minutes", "continuous"],
                    "conditional": ["if needed", "PRN severe pain", "if BP >180", "hold if HR <60"]
                },
                "clinical_contexts": {
                    "trauma": ["polytrauma", "head trauma", "chest trauma", "hemorrhagic shock"],
                    "cardiac": ["STEMI", "NSTEMI", "cardiogenic shock", "cardiac arrest", "VT/VF"],
                    "respiratory": ["respiratory failure", "acute asthma", "pulmonary edema", "PE"],
                    "neurological": ["stroke", "status epilepticus", "increased ICP"],
                    "toxicological": ["overdose", "poisoning", "withdrawal", "anaphylaxis"]
                },
                "dosing_patterns": {
                    "bolus": ["{amount}mg IV push", "{amount}mcg bolus", "give {amount}mg now"],
                    "infusion": ["{amount}mcg/min", "{amount}mg/hr drip", "titrate {amount}-{max}"],
                    "weight_based": ["{amount}mcg/kg", "{amount}mg/kg bolus", "{amount}mcg/kg/min"]
                },
                "negative_scenarios": {
                    "contraindications": ["bradycardia with beta-blockers", "hypotension with ACE-I"],
                    "timing_errors": ["delayed administration", "missed STAT order"],
                    "dosing_errors": ["decimal point errors", "unit confusion mg/mcg"]
                }
            },

            "pediatrics": {
                "priority": "P0",
                "current_f1": 0.250,
                "target_f1": 0.75,
                "f1_gap_analysis": {
                    "weight_based_calculation": "mg/kg dosing not properly extracted",
                    "age_specific_terminology": "Pediatric terms vs adult equivalents",
                    "developmental_context": "Age-appropriate vs contraindicated"
                },
                "enhanced_medications": {
                    "antibiotics": ["amoxicillin", "azithromycin", "cephalexin", "clindamycin"],
                    "pain_fever": ["acetaminophen", "ibuprofen", "morphine", "fentanyl"],
                    "respiratory": ["albuterol", "prednisolone", "budesonide", "epinephrine"],
                    "emergency": ["epinephrine", "adenosine", "atropine", "midazolam"]
                },
                "age_stratification": {
                    "neonate": {"age_range": "0-28 days", "weight_range": "2-5kg"},
                    "infant": {"age_range": "1-12 months", "weight_range": "4-12kg"},
                    "toddler": {"age_range": "1-3 years", "weight_range": "10-18kg"},
                    "child": {"age_range": "4-11 years", "weight_range": "15-40kg"},
                    "adolescent": {"age_range": "12-18 years", "weight_range": "35-70kg"}
                },
                "dosing_calculations": {
                    "standard": ["{amount}mg/kg", "{amount}mg/kg/day", "{amount}mg/kg/dose"],
                    "divided": ["{amount}mg/kg/day divided BID", "divided every 8 hours"],
                    "maximum": ["max {amount}mg/day", "not to exceed {amount}mg"],
                    "weight_check": ["verify weight {weight}kg", "based on {weight}kg"]
                },
                "pediatric_conditions": {
                    "infectious": ["otitis media", "pharyngitis", "pneumonia", "UTI"],
                    "respiratory": ["asthma", "bronchiolitis", "croup", "wheezing"],
                    "growth": ["failure to thrive", "feeding difficulties", "malnutrition"],
                    "developmental": ["developmental delay", "ADHD", "autism spectrum"]
                },
                "safety_considerations": {
                    "contraindicated": ["aspirin in children", "adult doses", "non-pediatric formulations"],
                    "age_restrictions": ["under 6 months", "not for infants", "adolescent only"],
                    "weight_limits": ["minimum weight required", "too small for dose"]
                }
            },

            "cardiology": {
                "priority": "P0",
                "current_f1": 0.412,
                "target_f1": 0.75,
                "f1_gap_analysis": {
                    "monitoring_parameters": "INR, renal function not captured",
                    "titration_instructions": "Dose adjustment protocols missed",
                    "contraindication_detection": "Heart rate/BP limits not recognized"
                },
                "enhanced_medications": {
                    "ace_inhibitors": ["lisinopril", "enalapril", "captopril", "ramipril"],
                    "beta_blockers": ["metoprolol", "carvedilol", "bisoprolol", "atenolol"],
                    "diuretics": ["furosemide", "hydrochlorothiazide", "spironolactone"],
                    "anticoagulants": ["warfarin", "rivaroxaban", "apixaban", "dabigatran"],
                    "statins": ["atorvastatin", "simvastatin", "rosuvastatin", "pravastatin"],
                    "antiarrhythmics": ["amiodarone", "digoxin", "diltiazem", "verapamil"]
                },
                "cardiac_conditions": {
                    "heart_failure": ["CHF", "systolic dysfunction", "diastolic dysfunction", "cardiomyopathy"],
                    "arrhythmias": ["atrial fibrillation", "atrial flutter", "VT", "bradycardia"],
                    "coronary": ["MI", "STEMI", "NSTEMI", "unstable angina", "stable angina"],
                    "hypertension": ["HTN", "hypertensive crisis", "resistant hypertension"],
                    "valvular": ["mitral regurgitation", "aortic stenosis", "prosthetic valve"]
                },
                "monitoring_requirements": {
                    "laboratory": ["INR", "PT/PTT", "renal function", "electrolytes", "LFTs"],
                    "clinical": ["blood pressure", "heart rate", "weight", "symptoms"],
                    "diagnostic": ["ECG", "echocardiogram", "stress test", "cardiac cath"]
                },
                "titration_protocols": {
                    "beta_blockers": ["start low, titrate q2 weeks", "target HR 60-70"],
                    "ace_inhibitors": ["increase q1-2 weeks", "monitor renal function"],
                    "warfarin": ["adjust based on INR", "target INR 2-3 or 2.5-3.5"]
                }
            },

            "oncology": {
                "priority": "P0",
                "current_f1": 0.389,
                "target_f1": 0.75,
                "f1_gap_analysis": {
                    "cycle_scheduling": "Chemotherapy timing not captured",
                    "supportive_care": "Pre-medications and rescue drugs missed",
                    "toxicity_monitoring": "Dose modifications not recognized"
                },
                "enhanced_medications": {
                    "chemotherapy": ["cisplatin", "carboplatin", "doxorubicin", "cyclophosphamide",
                                  "paclitaxel", "docetaxel", "5-fluorouracil", "methotrexate"],
                    "targeted_therapy": ["trastuzumab", "bevacizumab", "rituximab", "cetuximab"],
                    "supportive_care": ["ondansetron", "dexamethasone", "allopurinol", "leucovorin"],
                    "growth_factors": ["filgrastim", "pegfilgrastim", "epoetin", "darbepoetin"]
                },
                "cancer_types": {
                    "solid_tumors": ["breast cancer", "lung cancer", "colon cancer", "ovarian cancer"],
                    "hematologic": ["lymphoma", "leukemia", "multiple myeloma", "myelodysplastic"],
                    "staging": ["stage I", "stage II", "stage III", "stage IV", "metastatic"]
                },
                "dosing_contexts": {
                    "body_surface": ["{amount}mg/m2", "BSA-based dosing", "per square meter"],
                    "cycle_based": ["day 1", "day 1 and 8", "every 21 days", "q3 weeks"],
                    "continuous": ["continuous infusion", "96-hour infusion", "weekly"]
                },
                "supportive_protocols": {
                    "premedication": ["pre-med with dexamethasone", "antihistamine prophylaxis"],
                    "hydration": ["pre and post hydration", "normal saline 1L"],
                    "rescue": ["leucovorin rescue", "mesna protection"]
                }
            }
        }

    def generate_enhanced_p0_suite(self) -> Dict[str, List[EnhancedTestCase]]:
        """Generate enhanced test suite for all P0 specialties"""

        print("🏥 ENHANCED P0 SPECIALTY TEST GENERATION")
        print("="*60)
        print("Focus: Emergency, Pediatrics, Cardiology, Oncology")
        print("Target: 100 cases per specialty with F1 optimization\n")

        p0_test_cases = {}

        for specialty in ["emergency", "pediatrics", "cardiology", "oncology"]:
            print(f"🔬 Generating enhanced {specialty.upper()} test cases...")

            enhanced_cases = self.generate_enhanced_specialty_cases(specialty, 100)
            p0_test_cases[specialty] = enhanced_cases

            print(f"   ✅ {len(enhanced_cases)} enhanced cases generated")
            print(f"   🎯 F1 optimization: {self._get_f1_focus_summary(enhanced_cases)}")

        total_cases = sum(len(cases) for cases in p0_test_cases.values())
        print(f"\n🎯 ENHANCED P0 TOTAL: {total_cases} test cases")

        return p0_test_cases

    def generate_enhanced_specialty_cases(self, specialty: str, count: int = 100) -> List[EnhancedTestCase]:
        """Generate enhanced test cases for specific P0 specialty"""

        patterns = self.p0_patterns[specialty]

        # Enhanced distribution for P0 specialties
        positive_count = 75  # Increased positive cases for better training
        negative_count = 25  # Focused negative cases for critical edge cases

        positive_cases = self._generate_enhanced_positive_cases(specialty, positive_count)
        negative_cases = self._generate_enhanced_negative_cases(specialty, negative_count)

        return positive_cases + negative_cases

    def _generate_enhanced_positive_cases(self, specialty: str, count: int) -> List[EnhancedTestCase]:
        """Generate enhanced positive cases with F1 optimization focus"""

        patterns = self.p0_patterns[specialty]
        cases = []

        # Enhanced complexity distribution for P0
        simple_count = int(count * 0.25)    # 19 cases - basic scenarios
        realistic_count = int(count * 0.55)  # 41 cases - research-based
        complex_count = count - simple_count - realistic_count  # 15 cases - advanced

        # Simple cases with specialty-specific enhancements
        cases.extend(self._generate_enhanced_simple_cases(specialty, simple_count))

        # Realistic cases using research sources
        cases.extend(self._generate_enhanced_realistic_cases(specialty, realistic_count))

        # Complex cases targeting F1 gaps
        cases.extend(self._generate_enhanced_complex_cases(specialty, complex_count))

        return cases

    def _generate_enhanced_simple_cases(self, specialty: str, count: int) -> List[EnhancedTestCase]:
        """Generate enhanced simple cases targeting F1 improvements"""

        patterns = self.p0_patterns[specialty]
        cases = []

        for i in range(count):
            if specialty == "emergency":
                # Focus on urgency indicators for Emergency F1 improvement
                urgency = random.choice(patterns["urgency_indicators"]["immediate"])
                medication = random.choice(patterns["enhanced_medications"]["critical_care"])
                condition = random.choice(patterns["clinical_contexts"]["cardiac"])
                dosing = random.choice(patterns["dosing_patterns"]["bolus"]).format(amount=random.choice([1, 2, 5, 10]))

                text = f"{urgency}: Give patient John Smith {dosing} of {medication} for {condition}."
                f1_focus = "urgency_detection"

            elif specialty == "pediatrics":
                # Focus on weight-based dosing for Pediatrics F1 improvement
                age_group = random.choice(list(patterns["age_stratification"].keys()))
                weight = random.choice(["8", "12", "18", "25"])
                medication = random.choice(patterns["enhanced_medications"]["antibiotics"])
                dosing = f"{random.choice([10, 15, 20, 25])}mg/kg/day"
                condition = random.choice(patterns["pediatric_conditions"]["infectious"])

                text = f"Start {age_group} patient (weight: {weight}kg) on {medication} {dosing} divided BID for {condition}."
                f1_focus = "weight_based_dosing"

            elif specialty == "cardiology":
                # Focus on monitoring parameters for Cardiology F1 improvement
                medication = random.choice(patterns["enhanced_medications"]["ace_inhibitors"])
                condition = random.choice(patterns["cardiac_conditions"]["heart_failure"])
                monitoring = random.choice(patterns["monitoring_requirements"]["laboratory"])

                text = f"Start patient on {medication} 5mg daily for {condition}. Monitor {monitoring} in 1 week."
                f1_focus = "monitoring_extraction"

            elif specialty == "oncology":
                # Focus on cycle scheduling for Oncology F1 improvement
                medication = random.choice(patterns["enhanced_medications"]["chemotherapy"])
                dosing = f"{random.choice([50, 75, 100])}mg/m2"
                cycle = random.choice(["day 1 every 21 days", "day 1 and 8 q28 days"])
                cancer = random.choice(patterns["cancer_types"]["solid_tumors"])

                text = f"Patient with {cancer}: give {medication} {dosing} {cycle}."
                f1_focus = "cycle_scheduling"

            expected = self._extract_enhanced_expected(text, specialty)

            cases.append(EnhancedTestCase(
                text=text,
                expected=expected,
                specialty=specialty,
                complexity="simple",
                case_type="positive",
                priority="P0",
                test_level="unit",
                case_id=f"{specialty}_enhanced_simple_{i+1}",
                source="enhanced_synthetic",
                clinical_context=self._get_clinical_context(specialty),
                f1_optimization_focus=f1_focus,
                validation_notes=f"Targets F1 improvement in {f1_focus.replace('_', ' ')}"
            ))

        return cases

    def _generate_enhanced_realistic_cases(self, specialty: str, count: int) -> List[EnhancedTestCase]:
        """Generate enhanced realistic cases using research sources"""

        patterns = self.p0_patterns[specialty]
        cases = []

        # Use clinical trials data for realistic patterns
        specialty_medications = []
        for med_category in patterns["enhanced_medications"].values():
            specialty_medications.extend(med_category[:2])  # Limit for API efficiency

        try:
            # Mine clinical trials for this specialty
            trial_data = self.clinical_trials_miner.mine_multiple_medications(specialty_medications[:3])

            # Create enhanced realistic cases from trials
            trial_case_count = min(count // 2, 20)  # Limit trial-based cases

            for med, studies in trial_data.items():
                for study in studies[:trial_case_count // len(trial_data)]:
                    for sentence in study.get('sentences', [])[:2]:
                        enhanced_case = self._create_enhanced_trial_case(sentence, specialty, med)
                        if enhanced_case:
                            cases.append(enhanced_case)

        except Exception as e:
            print(f"   Warning: Clinical trials mining failed for {specialty}: {e}")

        # Generate remaining realistic cases using enhanced patterns
        remaining_count = count - len(cases)
        for i in range(remaining_count):
            enhanced_text = self._generate_enhanced_realistic_text(specialty)
            expected = self._extract_enhanced_expected(enhanced_text, specialty)

            cases.append(EnhancedTestCase(
                text=enhanced_text,
                expected=expected,
                specialty=specialty,
                complexity="realistic",
                case_type="positive",
                priority="P0",
                test_level="integration",
                case_id=f"{specialty}_enhanced_realistic_{i+1}",
                source="enhanced_realistic",
                clinical_context=self._get_clinical_context(specialty),
                f1_optimization_focus="clinical_realism",
                validation_notes="Research-based clinical language patterns"
            ))

        return cases[:count]

    def _generate_enhanced_complex_cases(self, specialty: str, count: int) -> List[EnhancedTestCase]:
        """Generate complex cases targeting specific F1 gaps"""

        patterns = self.p0_patterns[specialty]
        cases = []

        # Complex scenarios targeting F1 improvement areas
        if specialty == "emergency":
            complex_scenarios = [
                "multi_medication_trauma",
                "time_critical_dosing",
                "conditional_administration",
                "severity_based_titration"
            ]
        elif specialty == "pediatrics":
            complex_scenarios = [
                "age_weight_calculation",
                "developmental_consideration",
                "safety_contraindication",
                "growth_based_adjustment"
            ]
        elif specialty == "cardiology":
            complex_scenarios = [
                "titration_protocol",
                "monitoring_integration",
                "contraindication_detection",
                "combination_therapy"
            ]
        elif specialty == "oncology":
            complex_scenarios = [
                "multi_cycle_protocol",
                "supportive_care_integration",
                "toxicity_modification",
                "combination_chemotherapy"
            ]

        for i in range(count):
            scenario = random.choice(complex_scenarios)
            complex_text = self._generate_complex_scenario_text(specialty, scenario)
            expected = self._extract_enhanced_expected(complex_text, specialty)

            cases.append(EnhancedTestCase(
                text=complex_text,
                expected=expected,
                specialty=specialty,
                complexity="complex",
                case_type="positive",
                priority="P0",
                test_level="e2e",
                case_id=f"{specialty}_enhanced_complex_{i+1}",
                source="enhanced_complex",
                clinical_context=self._get_clinical_context(specialty),
                f1_optimization_focus=scenario,
                validation_notes=f"Targets F1 gap: {scenario.replace('_', ' ')}"
            ))

        return cases

    def _generate_enhanced_negative_cases(self, specialty: str, count: int) -> List[EnhancedTestCase]:
        """Generate enhanced negative cases for P0 specialties"""

        patterns = self.p0_patterns[specialty]
        cases = []

        # P0 specialty-specific negative scenarios
        negative_scenarios = patterns.get("negative_scenarios", {})

        per_type = count // len(negative_scenarios) if negative_scenarios else count // 3

        for scenario_type, scenario_examples in negative_scenarios.items():
            for i in range(per_type):
                negative_text = self._generate_negative_scenario_text(specialty, scenario_type, scenario_examples)
                expected = {"error": scenario_type, "safety_concern": True, "extractable": False}

                cases.append(EnhancedTestCase(
                    text=negative_text,
                    expected=expected,
                    specialty=specialty,
                    complexity="realistic",
                    case_type="negative",
                    priority="P0",
                    test_level="integration",
                    case_id=f"{specialty}_enhanced_negative_{scenario_type}_{i+1}",
                    source="enhanced_negative",
                    clinical_context=self._get_clinical_context(specialty),
                    f1_optimization_focus="safety_validation",
                    validation_notes=f"Critical safety scenario: {scenario_type}"
                ))

        return cases[:count]

    def _generate_enhanced_realistic_text(self, specialty: str) -> str:
        """Generate enhanced realistic clinical text"""

        patterns = self.p0_patterns[specialty]

        if specialty == "emergency":
            templates = [
                "TRAUMA ALERT: {patient} presents with {condition}. Give {medication} {dosage} {urgency}. {monitoring}",
                "CODE: {patient} in {condition}. {urgency} {medication} {dosage}. Titrate based on {parameter}.",
                "CRITICAL: {patient} with {condition}. Start {medication} {dosage}, {frequency}. Monitor {safety}."
            ]
        elif specialty == "pediatrics":
            templates = [
                "{age_group} {patient} (weight: {weight}kg) with {condition}. Start {medication} {calculation}. {safety}",
                "Pediatric patient {patient}, {age}, presents with {condition}. Weight-based: {medication} {calculation}.",
                "{patient} ({age}, {weight}kg) needs {medication} for {condition}. Dose: {calculation} {frequency}."
            ]
        elif specialty == "cardiology":
            templates = [
                "{patient} with {condition}: start {medication} {dosage} {frequency}. Monitor {monitoring} q{interval}.",
                "Cardiac patient {patient}: {medication} {dosage}, titrate based on {parameter}. Target {target}.",
                "{patient} s/p {procedure}: continue {medication} {dosage}. Check {lab} in {timeframe}."
            ]
        elif specialty == "oncology":
            templates = [
                "{patient} with {cancer}: {medication} {dosage} {schedule}. Pre-med with {premedication}.",
                "Cycle {cycle_number}: {patient} to receive {medication} {dosage}. {supportive_care}",
                "{patient} ({cancer}): {medication} {dosage} {frequency}. Monitor for {toxicity}."
            ]

        template = random.choice(templates)
        values = self._get_enhanced_template_values(specialty, patterns)

        return template.format(**values)

    def _get_enhanced_template_values(self, specialty: str, patterns: Dict) -> Dict[str, str]:
        """Get enhanced template values for realistic text generation"""

        base_values = {
            "patient": random.choice(["John Smith", "Mary Johnson", "David Brown", "Sarah Wilson"]),
            "medication": random.choice([med for meds in patterns["enhanced_medications"].values() for med in meds]),
            "dosage": f"{random.choice([1, 2, 5, 10, 25, 50])}mg",
            "frequency": random.choice(["daily", "BID", "TID", "q8h"])
        }

        if specialty == "emergency":
            base_values.update({
                "condition": random.choice([cond for conds in patterns["clinical_contexts"].values() for cond in conds]),
                "urgency": random.choice(patterns["urgency_indicators"]["immediate"]),
                "monitoring": "Monitor vitals q5min",
                "parameter": "blood pressure",
                "safety": "cardiac monitoring"
            })

        elif specialty == "pediatrics":
            age_group = random.choice(list(patterns["age_stratification"].keys()))
            base_values.update({
                "age_group": age_group,
                "age": patterns["age_stratification"][age_group]["age_range"],
                "weight": random.choice(["8", "12", "18", "25"]),
                "condition": random.choice([cond for conds in patterns["pediatric_conditions"].values() for cond in conds]),
                "calculation": f"{random.choice([10, 15, 20])}mg/kg/day",
                "safety": "Monitor growth parameters"
            })

        elif specialty == "cardiology":
            base_values.update({
                "condition": random.choice([cond for conds in patterns["cardiac_conditions"].values() for cond in conds]),
                "monitoring": random.choice(patterns["monitoring_requirements"]["laboratory"]),
                "interval": random.choice(["week", "2 weeks", "month"]),
                "parameter": "heart rate",
                "target": "HR 60-70",
                "procedure": "PCI",
                "lab": "renal function",
                "timeframe": "1 week"
            })

        elif specialty == "oncology":
            base_values.update({
                "cancer": random.choice([cancer for cancers in patterns["cancer_types"].values() for cancer in cancers]),
                "schedule": random.choice(["day 1 q21 days", "weekly", "day 1 and 8 q28 days"]),
                "cycle_number": random.choice(["1", "2", "3"]),
                "premedication": "dexamethasone 8mg",
                "supportive_care": "Hydrate pre and post",
                "toxicity": "neutropenia"
            })

        return base_values

    def _create_enhanced_trial_case(self, sentence: str, specialty: str, medication: str) -> EnhancedTestCase:
        """Create enhanced test case from clinical trial sentence"""

        expected = self._extract_enhanced_expected(sentence, specialty)

        return EnhancedTestCase(
            text=sentence,
            expected=expected,
            specialty=specialty,
            complexity="realistic",
            case_type="positive",
            priority="P0",
            test_level="integration",
            case_id=f"{specialty}_trial_{hash(sentence) % 10000}",
            source="clinicaltrials_gov",
            clinical_context=self._get_clinical_context(specialty),
            f1_optimization_focus="research_based_patterns",
            validation_notes="Extracted from clinical trial data"
        )

    def _generate_complex_scenario_text(self, specialty: str, scenario: str) -> str:
        """Generate complex scenario text targeting F1 gaps"""

        patterns = self.p0_patterns[specialty]

        if specialty == "emergency" and scenario == "multi_medication_trauma":
            return "TRAUMA: John Smith, hypotensive, give dopamine 5-15mcg/kg/min drip, morphine 2-4mg IV q5min PRN pain, and midazolam 1-2mg IV PRN agitation."

        elif specialty == "pediatrics" and scenario == "age_weight_calculation":
            return "6-month-old infant (8kg) with acute otitis media: amoxicillin 40mg/kg/day divided BID. Calculate: 40 x 8 = 320mg/day = 160mg BID."

        elif specialty == "cardiology" and scenario == "titration_protocol":
            return "Patient with CHF: start metoprolol 12.5mg BID, increase by 25mg BID q2 weeks as tolerated, target HR 60-70 bpm, hold if SBP <90."

        elif specialty == "oncology" and scenario == "multi_cycle_protocol":
            return "Breast cancer protocol: doxorubicin 60mg/m2 + cyclophosphamide 600mg/m2 day 1 q21 days x 4 cycles, then paclitaxel 175mg/m2 q21 days x 4 cycles."

        # Default complex scenario
        return f"Complex {specialty} scenario for {scenario} testing."

    def _generate_negative_scenario_text(self, specialty: str, scenario_type: str, examples: List[str]) -> str:
        """Generate negative scenario text"""

        if scenario_type == "contraindications":
            return random.choice([
                "Patient with heart rate 45 bpm, give metoprolol 50mg BID.",
                "Patient with systolic BP 80 mmHg, start lisinopril 10mg daily.",
                "Patient allergic to penicillin, prescribe amoxicillin 500mg TID."
            ])
        elif scenario_type == "dosing_errors":
            return random.choice([
                "Give patient morphine 50mg IV push for pain.",  # Overdose
                "Start patient on warfarin 50mg daily.",        # Massive overdose
                "Child: acetaminophen 1000mg q4h."             # Adult dose for child
            ])
        elif scenario_type == "timing_errors":
            return random.choice([
                "STAT epinephrine ordered 30 minutes ago, still not given.",
                "Critical medication delayed due to pharmacy verification.",
                "Time-sensitive medication given 2 hours late."
            ])

        return f"Negative scenario: {scenario_type}"

    def _extract_enhanced_expected(self, text: str, specialty: str) -> Dict[str, Any]:
        """Extract enhanced expected values with specialty-specific focus"""

        expected = {}

        # Basic extraction
        if "patient" in text.lower() or "john" in text.lower() or "mary" in text.lower():
            patient_match = re.search(r'(patient\s+)?([A-Z][a-z]+\s+[A-Z][a-z]+)', text)
            if patient_match:
                expected["patient"] = patient_match.group(2)

        # Medication extraction
        medication_match = re.search(r'\b(morphine|fentanyl|midazolam|amoxicillin|metoprolol|warfarin|cisplatin)\b', text, re.IGNORECASE)
        if medication_match:
            expected["medication"] = medication_match.group(1).lower()

        # Dosage extraction
        dosage_match = re.search(r'(\d+(?:\.\d+)?)\s*(mg|mcg|g)', text, re.IGNORECASE)
        if dosage_match:
            expected["dosage"] = f"{dosage_match.group(1)}{dosage_match.group(2)}"

        # Frequency extraction
        frequency_match = re.search(r'\b(daily|BID|TID|QID|q\d+h|twice daily|three times daily)\b', text, re.IGNORECASE)
        if frequency_match:
            expected["frequency"] = frequency_match.group(1)

        # Specialty-specific extractions
        if specialty == "emergency":
            urgency_match = re.search(r'\b(STAT|NOW|IMMEDIATELY|EMERGENT|CRITICAL)\b', text, re.IGNORECASE)
            if urgency_match:
                expected["urgency"] = urgency_match.group(1)

        elif specialty == "pediatrics":
            weight_match = re.search(r'(\d+)kg', text)
            if weight_match:
                expected["weight"] = f"{weight_match.group(1)}kg"

        elif specialty == "cardiology":
            monitoring_match = re.search(r'\b(INR|renal function|heart rate|blood pressure)\b', text, re.IGNORECASE)
            if monitoring_match:
                expected["monitoring"] = monitoring_match.group(1)

        elif specialty == "oncology":
            cycle_match = re.search(r'\b(day \d+|q\d+ days|every \d+ days)\b', text, re.IGNORECASE)
            if cycle_match:
                expected["cycle"] = cycle_match.group(1)

        return expected

    def _get_clinical_context(self, specialty: str) -> str:
        """Get clinical context for specialty"""

        contexts = {
            "emergency": "Emergency Department - Time-critical care",
            "pediatrics": "Pediatric Unit - Age and weight-based care",
            "cardiology": "Cardiac Unit - Monitoring and titration focus",
            "oncology": "Oncology Unit - Protocol-based chemotherapy"
        }

        return contexts.get(specialty, "General Medical Unit")

    def _get_f1_focus_summary(self, cases: List[EnhancedTestCase]) -> str:
        """Get F1 optimization focus summary"""

        focus_counts = {}
        for case in cases:
            focus = case.f1_optimization_focus
            focus_counts[focus] = focus_counts.get(focus, 0) + 1

        return ", ".join([f"{focus}: {count}" for focus, count in sorted(focus_counts.items())])

    def save_enhanced_p0_cases(self, p0_cases: Dict[str, List[EnhancedTestCase]], output_dir: str = ".") -> str:
        """Save enhanced P0 test cases to JSON file"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enhanced_p0_specialty_test_cases_{timestamp}.json"
        filepath = Path(output_dir) / filename

        # Convert to serializable format
        serializable_cases = {}
        for specialty, cases in p0_cases.items():
            serializable_cases[specialty] = [
                {
                    "text": case.text,
                    "expected": case.expected,
                    "specialty": case.specialty,
                    "complexity": case.complexity,
                    "case_type": case.case_type,
                    "priority": case.priority,
                    "test_level": case.test_level,
                    "case_id": case.case_id,
                    "source": case.source,
                    "clinical_context": case.clinical_context,
                    "f1_optimization_focus": case.f1_optimization_focus,
                    "validation_notes": case.validation_notes
                }
                for case in cases
            ]

        # Add enhanced summary
        summary = {
            "generation_timestamp": timestamp,
            "specialties": list(p0_cases.keys()),
            "total_cases": sum(len(cases) for cases in p0_cases.values()),
            "cases_per_specialty": {specialty: len(cases) for specialty, cases in p0_cases.items()},
            "f1_targets": {
                "emergency": "0.571 → 0.80",
                "pediatrics": "0.250 → 0.75",
                "cardiology": "0.412 → 0.75",
                "oncology": "0.389 → 0.75"
            },
            "enhancement_features": [
                "Specialty-specific F1 gap targeting",
                "Enhanced clinical context extraction",
                "Research-based realistic patterns",
                "Safety-focused negative scenarios",
                "Advanced monitoring parameter detection"
            ]
        }

        output_data = {
            "summary": summary,
            "test_cases": serializable_cases
        }

        with open(filepath, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"\n💾 Enhanced P0 test cases saved to: {filename}")
        return str(filepath)

def main():
    """Generate enhanced P0 specialty test suite"""

    print("🏥 ENHANCED P0 SPECIALTY TEST GENERATION")
    print("="*60)
    print("Production-Ready Test Cases for Critical Specialties")
    print("Focus: F1 Score Optimization and Clinical Safety\n")

    generator = EnhancedP0SpecialtyGenerator()

    # Generate enhanced P0 test suite
    p0_cases = generator.generate_enhanced_p0_suite()

    # Save to file
    output_file = generator.save_enhanced_p0_cases(p0_cases)

    # Print final summary
    total_cases = sum(len(cases) for cases in p0_cases.values())
    print(f"\n🎯 ENHANCED P0 GENERATION COMPLETE")
    print(f"📊 Total P0 Cases: {total_cases}")
    print(f"🏥 P0 Specialties: {len(p0_cases)}")
    print(f"📁 Output File: {output_file}")

    # Show enhanced sample cases
    print(f"\n📋 ENHANCED SAMPLE CASES:")

    for specialty, cases in p0_cases.items():
        print(f"\n🔬 {specialty.upper()}:")

        # Show enhanced positive case
        positive_cases = [c for c in cases if c.case_type == "positive"]
        if positive_cases:
            case = positive_cases[0]
            print(f"   ✅ ENHANCED POSITIVE ({case.f1_optimization_focus}):")
            print(f"      {case.text[:80]}...")
            print(f"      Focus: {case.validation_notes}")

        # Show safety-focused negative case
        negative_cases = [c for c in cases if c.case_type == "negative"]
        if negative_cases:
            case = negative_cases[0]
            print(f"   ❌ SAFETY NEGATIVE ({case.f1_optimization_focus}):")
            print(f"      {case.text[:80]}...")
            print(f"      Focus: {case.validation_notes}")

    return p0_cases

if __name__ == "__main__":
    main()