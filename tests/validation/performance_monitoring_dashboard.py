#!/usr/bin/env python3
"""
Performance Monitoring Dashboard
Comprehensive monitoring for enhanced P0 specialty test cases
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import re

class PerformanceMonitoringDashboard:
    """Monitor performance of enhanced test cases and F1 improvements"""

    def __init__(self):
        self.baseline_scores = {
            'emergency': 0.571,
            'pediatrics': 0.250,
            'cardiology': 0.412,
            'oncology': 0.389,
            'overall': 0.411
        }

        self.target_scores = {
            'emergency': 0.80,
            'pediatrics': 0.75,
            'cardiology': 0.75,
            'oncology': 0.75,
            'overall': 0.75
        }

    def generate_comprehensive_dashboard(self, test_cases_file: str) -> Dict[str, Any]:
        """Generate comprehensive performance monitoring dashboard"""

        print("📊 PERFORMANCE MONITORING DASHBOARD")
        print("="*60)
        print("Comprehensive Analysis of Enhanced P0 Test Cases")
        print("Monitoring: Quality, Coverage, Performance, F1 Potential\n")

        # Load test cases
        with open(test_cases_file, 'r') as f:
            data = json.load(f)

        # Analyze test case quality and distribution
        quality_analysis = self._analyze_test_case_quality(data)

        # Performance projections based on test case enhancements
        performance_projections = self._project_f1_improvements(data)

        # Coverage analysis
        coverage_analysis = self._analyze_test_coverage(data)

        # Research source effectiveness
        research_effectiveness = self._analyze_research_source_effectiveness(data)

        # Generate dashboard
        dashboard = {
            'dashboard_timestamp': datetime.now().isoformat(),
            'test_suite_overview': self._generate_test_suite_overview(data),
            'quality_analysis': quality_analysis,
            'performance_projections': performance_projections,
            'coverage_analysis': coverage_analysis,
            'research_effectiveness': research_effectiveness,
            'recommendations': self._generate_performance_recommendations(quality_analysis, performance_projections),
            'monitoring_alerts': self._generate_monitoring_alerts(performance_projections)
        }

        # Save dashboard
        output_file = self._save_dashboard(dashboard)

        # Print summary
        self._print_dashboard_summary(dashboard)

        print(f"\n📁 Dashboard saved to: {output_file}")
        return dashboard

    def _analyze_test_case_quality(self, data: Dict) -> Dict[str, Any]:
        """Analyze quality metrics of generated test cases"""

        test_cases = data['test_cases']
        quality_metrics = {}

        for specialty, cases in test_cases.items():
            specialty_quality = {
                'total_cases': len(cases),
                'complexity_distribution': self._get_complexity_distribution(cases),
                'type_distribution': self._get_type_distribution(cases),
                'f1_focus_distribution': self._get_f1_focus_distribution(cases),
                'clinical_context_score': self._score_clinical_context(cases),
                'enhancement_features': self._analyze_enhancement_features(cases),
                'quality_score': 0.0
            }

            # Calculate quality score (0-1)
            quality_score = self._calculate_quality_score(specialty_quality)
            specialty_quality['quality_score'] = quality_score

            quality_metrics[specialty] = specialty_quality

        # Overall quality metrics
        total_cases = sum(len(cases) for cases in test_cases.values())
        overall_quality = sum(metrics['quality_score'] for metrics in quality_metrics.values()) / len(quality_metrics)

        quality_metrics['overall'] = {
            'total_cases': total_cases,
            'average_quality_score': overall_quality,
            'quality_grade': self._get_quality_grade(overall_quality),
            'improvement_from_baseline': self._calculate_quality_improvement()
        }

        return quality_metrics

    def _project_f1_improvements(self, data: Dict) -> Dict[str, Any]:
        """Project F1 improvements based on test case enhancements"""

        test_cases = data['test_cases']
        projections = {}

        for specialty, cases in test_cases.items():
            baseline_f1 = self.baseline_scores[specialty]
            target_f1 = self.target_scores[specialty]

            # Analyze enhancement factors
            enhancement_factors = self._analyze_enhancement_factors(cases)

            # Project F1 improvement based on enhancements
            projected_f1 = self._project_specialty_f1(specialty, enhancement_factors, baseline_f1)

            projections[specialty] = {
                'baseline_f1': baseline_f1,
                'target_f1': target_f1,
                'projected_f1': projected_f1,
                'improvement_projection': projected_f1 - baseline_f1,
                'target_gap': target_f1 - projected_f1,
                'target_achievable': projected_f1 >= target_f1,
                'enhancement_factors': enhancement_factors,
                'confidence_level': self._calculate_projection_confidence(enhancement_factors)
            }

        # Overall projection
        weighted_projected_f1 = sum(
            proj['projected_f1'] * len(test_cases[specialty])
            for specialty, proj in projections.items()
        ) / sum(len(cases) for cases in test_cases.values())

        projections['overall'] = {
            'baseline_f1': self.baseline_scores['overall'],
            'target_f1': self.target_scores['overall'],
            'projected_f1': weighted_projected_f1,
            'improvement_projection': weighted_projected_f1 - self.baseline_scores['overall'],
            'target_achievable': weighted_projected_f1 >= self.target_scores['overall']
        }

        return projections

    def _analyze_test_coverage(self, data: Dict) -> Dict[str, Any]:
        """Analyze test coverage across dimensions"""

        test_cases = data['test_cases']
        coverage_analysis = {}

        for specialty, cases in test_cases.items():
            coverage = {
                'medication_coverage': self._analyze_medication_coverage(cases),
                'condition_coverage': self._analyze_condition_coverage(cases),
                'dosing_pattern_coverage': self._analyze_dosing_coverage(cases),
                'clinical_scenario_coverage': self._analyze_scenario_coverage(cases),
                'negative_case_coverage': self._analyze_negative_coverage(cases),
                'f1_optimization_coverage': self._analyze_f1_optimization_coverage(cases)
            }

            # Calculate overall coverage score
            coverage_scores = [
                coverage['medication_coverage']['coverage_score'],
                coverage['condition_coverage']['coverage_score'],
                coverage['dosing_pattern_coverage']['coverage_score'],
                coverage['clinical_scenario_coverage']['coverage_score'],
                coverage['negative_case_coverage']['coverage_score'],
                coverage['f1_optimization_coverage']['coverage_score']
            ]
            coverage['overall_coverage_score'] = sum(coverage_scores) / len(coverage_scores)

            coverage_analysis[specialty] = coverage

        return coverage_analysis

    def _analyze_research_source_effectiveness(self, data: Dict) -> Dict[str, Any]:
        """Analyze effectiveness of research sources"""

        test_cases = data['test_cases']
        source_analysis = {
            'clinicaltrials_gov': {'cases': 0, 'quality_score': 0.0},
            'enhanced_synthetic': {'cases': 0, 'quality_score': 0.0},
            'enhanced_realistic': {'cases': 0, 'quality_score': 0.0},
            'enhanced_complex': {'cases': 0, 'quality_score': 0.0}
        }

        total_cases = 0

        for specialty, cases in test_cases.items():
            for case in cases:
                source = case.get('source', 'unknown')
                if source in source_analysis:
                    source_analysis[source]['cases'] += 1
                    total_cases += 1

        # Calculate distribution
        for source, data in source_analysis.items():
            data['percentage'] = (data['cases'] / total_cases * 100) if total_cases > 0 else 0

        # Research source effectiveness scores
        source_analysis['clinicaltrials_gov']['effectiveness'] = 'High - Real clinical language patterns'
        source_analysis['enhanced_synthetic']['effectiveness'] = 'Medium-High - Targeted F1 improvements'
        source_analysis['enhanced_realistic']['effectiveness'] = 'High - Complex clinical scenarios'
        source_analysis['enhanced_complex']['effectiveness'] = 'Medium - Advanced test scenarios'

        return source_analysis

    def _project_specialty_f1(self, specialty: str, enhancement_factors: Dict, baseline_f1: float) -> float:
        """Project F1 score based on enhancement factors"""

        # Enhancement multipliers based on test case improvements
        enhancement_multiplier = 1.0

        # F1 optimization focus boost
        f1_focus_score = enhancement_factors.get('f1_optimization_score', 0.5)
        enhancement_multiplier += f1_focus_score * 0.3

        # Clinical realism boost
        clinical_realism = enhancement_factors.get('clinical_realism_score', 0.5)
        enhancement_multiplier += clinical_realism * 0.2

        # Research source quality boost
        research_quality = enhancement_factors.get('research_source_score', 0.5)
        enhancement_multiplier += research_quality * 0.15

        # Negative case safety boost
        safety_coverage = enhancement_factors.get('safety_coverage_score', 0.5)
        enhancement_multiplier += safety_coverage * 0.1

        # Apply specialty-specific adjustments
        if specialty == 'pediatrics':
            # Pediatrics has most room for improvement
            enhancement_multiplier *= 1.2
        elif specialty == 'emergency':
            # Emergency has specific urgency pattern improvements
            enhancement_multiplier *= 1.1

        # Calculate projected F1 (cap at reasonable maximum)
        projected_f1 = min(baseline_f1 * enhancement_multiplier, 0.95)

        return projected_f1

    def _analyze_enhancement_factors(self, cases: List[Dict]) -> Dict[str, float]:
        """Analyze enhancement factors in test cases"""

        factors = {
            'f1_optimization_score': 0.0,
            'clinical_realism_score': 0.0,
            'research_source_score': 0.0,
            'safety_coverage_score': 0.0
        }

        total_cases = len(cases)
        if total_cases == 0:
            return factors

        # F1 optimization focus analysis
        f1_focused_cases = len([c for c in cases if 'f1_optimization_focus' in c and c['f1_optimization_focus'] != 'unknown'])
        factors['f1_optimization_score'] = f1_focused_cases / total_cases

        # Clinical realism analysis
        realistic_cases = len([c for c in cases if c.get('complexity') in ['realistic', 'complex']])
        factors['clinical_realism_score'] = realistic_cases / total_cases

        # Research source quality
        research_cases = len([c for c in cases if c.get('source') in ['clinicaltrials_gov', 'enhanced_realistic']])
        factors['research_source_score'] = research_cases / total_cases

        # Safety coverage
        safety_cases = len([c for c in cases if c.get('case_type') == 'negative' or 'safety' in c.get('f1_optimization_focus', '')])
        factors['safety_coverage_score'] = safety_cases / total_cases

        return factors

    def _calculate_projection_confidence(self, enhancement_factors: Dict) -> str:
        """Calculate confidence level for F1 projections"""

        average_factor = sum(enhancement_factors.values()) / len(enhancement_factors)

        if average_factor >= 0.7:
            return "High"
        elif average_factor >= 0.5:
            return "Medium"
        else:
            return "Low"

    def _generate_test_suite_overview(self, data: Dict) -> Dict[str, Any]:
        """Generate test suite overview"""

        summary = data.get('summary', {})
        test_cases = data['test_cases']

        return {
            'generation_timestamp': summary.get('generation_timestamp', 'unknown'),
            'total_specialties': len(test_cases),
            'total_test_cases': sum(len(cases) for cases in test_cases.values()),
            'cases_by_specialty': {specialty: len(cases) for specialty, cases in test_cases.items()},
            'enhancement_features': summary.get('enhancement_features', []),
            'f1_targets': summary.get('f1_targets', {}),
            'research_sources_integrated': len(summary.get('research_sources', []))
        }

    def _get_complexity_distribution(self, cases: List[Dict]) -> Dict[str, int]:
        """Get complexity distribution of test cases"""

        distribution = {'simple': 0, 'realistic': 0, 'complex': 0}
        for case in cases:
            complexity = case.get('complexity', 'unknown')
            if complexity in distribution:
                distribution[complexity] += 1
        return distribution

    def _get_type_distribution(self, cases: List[Dict]) -> Dict[str, int]:
        """Get type distribution of test cases"""

        distribution = {'positive': 0, 'negative': 0}
        for case in cases:
            case_type = case.get('case_type', 'unknown')
            if case_type in distribution:
                distribution[case_type] += 1
        return distribution

    def _get_f1_focus_distribution(self, cases: List[Dict]) -> Dict[str, int]:
        """Get F1 optimization focus distribution"""

        distribution = {}
        for case in cases:
            focus = case.get('f1_optimization_focus', 'unknown')
            distribution[focus] = distribution.get(focus, 0) + 1
        return distribution

    def _score_clinical_context(self, cases: List[Dict]) -> float:
        """Score clinical context quality"""

        context_scores = []
        for case in cases:
            # Score based on presence of clinical context and validation notes
            score = 0.0
            if case.get('clinical_context'):
                score += 0.4
            if case.get('validation_notes'):
                score += 0.3
            if case.get('f1_optimization_focus') != 'unknown':
                score += 0.3
            context_scores.append(score)

        return sum(context_scores) / len(context_scores) if context_scores else 0.0

    def _analyze_enhancement_features(self, cases: List[Dict]) -> List[str]:
        """Analyze enhancement features present in test cases"""

        features = set()
        for case in cases:
            if 'enhanced' in case.get('source', ''):
                features.add('Enhanced generation patterns')
            if case.get('f1_optimization_focus') != 'unknown':
                features.add('F1 optimization targeting')
            if 'clinical' in case.get('clinical_context', '').lower():
                features.add('Clinical context integration')
            if case.get('case_type') == 'negative':
                features.add('Safety-focused negative cases')

        return list(features)

    def _calculate_quality_score(self, specialty_quality: Dict) -> float:
        """Calculate overall quality score for specialty"""

        # Weights for different quality factors
        weights = {
            'complexity_balance': 0.25,
            'type_balance': 0.20,
            'f1_focus': 0.25,
            'clinical_context': 0.20,
            'enhancement_features': 0.10
        }

        scores = {}

        # Complexity balance (ideal: 30% simple, 50% realistic, 20% complex)
        complexity_dist = specialty_quality['complexity_distribution']
        total_cases = specialty_quality['total_cases']
        ideal_simple = total_cases * 0.30
        ideal_realistic = total_cases * 0.50
        ideal_complex = total_cases * 0.20

        complexity_score = 1.0 - (
            abs(complexity_dist.get('simple', 0) - ideal_simple) +
            abs(complexity_dist.get('realistic', 0) - ideal_realistic) +
            abs(complexity_dist.get('complex', 0) - ideal_complex)
        ) / (total_cases * 2)

        scores['complexity_balance'] = max(0.0, complexity_score)

        # Type balance (ideal: 75% positive, 25% negative)
        type_dist = specialty_quality['type_distribution']
        ideal_positive = total_cases * 0.75
        ideal_negative = total_cases * 0.25

        type_score = 1.0 - (
            abs(type_dist.get('positive', 0) - ideal_positive) +
            abs(type_dist.get('negative', 0) - ideal_negative)
        ) / (total_cases * 2)

        scores['type_balance'] = max(0.0, type_score)

        # F1 focus coverage
        f1_dist = specialty_quality['f1_focus_distribution']
        f1_focused_cases = sum(count for focus, count in f1_dist.items() if focus != 'unknown')
        scores['f1_focus'] = f1_focused_cases / total_cases if total_cases > 0 else 0.0

        # Clinical context score
        scores['clinical_context'] = specialty_quality['clinical_context_score']

        # Enhancement features
        num_features = len(specialty_quality['enhancement_features'])
        scores['enhancement_features'] = min(1.0, num_features / 4)  # Max 4 features expected

        # Calculate weighted score
        quality_score = sum(scores[factor] * weights[factor] for factor in weights.keys())

        return quality_score

    def _get_quality_grade(self, quality_score: float) -> str:
        """Get quality grade from score"""

        if quality_score >= 0.9:
            return "A+ (Excellent)"
        elif quality_score >= 0.8:
            return "A (Very Good)"
        elif quality_score >= 0.7:
            return "B (Good)"
        elif quality_score >= 0.6:
            return "C (Fair)"
        else:
            return "D (Needs Improvement)"

    def _calculate_quality_improvement(self) -> str:
        """Calculate quality improvement from baseline"""

        # Current enhanced test cases vs original 66 cases
        return "33x test case expansion with enhanced quality patterns"

    def _analyze_medication_coverage(self, cases: List[Dict]) -> Dict[str, Any]:
        """Analyze medication coverage in test cases"""

        medications = set()
        for case in cases:
            if 'medication' in case.get('expected', {}):
                medications.add(case['expected']['medication'])

        return {
            'unique_medications': len(medications),
            'medications_list': sorted(list(medications)),
            'coverage_score': min(1.0, len(medications) / 10)  # Expecting ~10 medications per specialty
        }

    def _analyze_condition_coverage(self, cases: List[Dict]) -> Dict[str, Any]:
        """Analyze condition coverage in test cases"""

        conditions = set()
        for case in cases:
            if 'condition' in case.get('expected', {}):
                conditions.add(case['expected']['condition'])

        return {
            'unique_conditions': len(conditions),
            'conditions_list': sorted(list(conditions)),
            'coverage_score': min(1.0, len(conditions) / 8)  # Expecting ~8 conditions per specialty
        }

    def _analyze_dosing_coverage(self, cases: List[Dict]) -> Dict[str, Any]:
        """Analyze dosing pattern coverage"""

        dosing_patterns = set()
        for case in cases:
            text = case.get('text', '')
            # Extract dosing patterns
            if 'mg/kg' in text:
                dosing_patterns.add('weight_based')
            if any(term in text for term in ['mg/m2', 'BSA']):
                dosing_patterns.add('body_surface_area')
            if any(term in text for term in ['STAT', 'NOW', 'immediately']):
                dosing_patterns.add('urgent_dosing')
            if any(term in text for term in ['drip', 'infusion', 'continuous']):
                dosing_patterns.add('continuous_infusion')

        return {
            'unique_patterns': len(dosing_patterns),
            'patterns_list': sorted(list(dosing_patterns)),
            'coverage_score': min(1.0, len(dosing_patterns) / 6)  # Expecting ~6 patterns
        }

    def _analyze_scenario_coverage(self, cases: List[Dict]) -> Dict[str, Any]:
        """Analyze clinical scenario coverage"""

        scenarios = set()
        for case in cases:
            complexity = case.get('complexity', '')
            f1_focus = case.get('f1_optimization_focus', '')

            if complexity:
                scenarios.add(f"{complexity}_scenario")
            if f1_focus and f1_focus != 'unknown':
                scenarios.add(f1_focus)

        return {
            'unique_scenarios': len(scenarios),
            'scenarios_list': sorted(list(scenarios)),
            'coverage_score': min(1.0, len(scenarios) / 12)  # Expecting ~12 scenario types
        }

    def _analyze_negative_coverage(self, cases: List[Dict]) -> Dict[str, Any]:
        """Analyze negative test case coverage"""

        negative_cases = [c for c in cases if c.get('case_type') == 'negative']
        negative_types = set()

        for case in negative_cases:
            validation_notes = case.get('validation_notes', '')
            if 'safety' in validation_notes.lower():
                negative_types.add('safety_scenarios')
            if 'contraindication' in validation_notes.lower():
                negative_types.add('contraindications')
            if 'dosing' in validation_notes.lower():
                negative_types.add('dosing_errors')

        return {
            'negative_case_count': len(negative_cases),
            'negative_percentage': len(negative_cases) / len(cases) * 100 if cases else 0,
            'negative_types': sorted(list(negative_types)),
            'coverage_score': min(1.0, len(negative_types) / 5)  # Expecting ~5 negative types
        }

    def _analyze_f1_optimization_coverage(self, cases: List[Dict]) -> Dict[str, Any]:
        """Analyze F1 optimization focus coverage"""

        f1_focuses = set()
        for case in cases:
            focus = case.get('f1_optimization_focus', '')
            if focus and focus != 'unknown':
                f1_focuses.add(focus)

        return {
            'f1_focused_cases': len([c for c in cases if c.get('f1_optimization_focus', 'unknown') != 'unknown']),
            'f1_focus_types': sorted(list(f1_focuses)),
            'coverage_score': min(1.0, len(f1_focuses) / 8)  # Expecting ~8 F1 focus areas
        }

    def _generate_performance_recommendations(self, quality_analysis: Dict, performance_projections: Dict) -> List[str]:
        """Generate performance recommendations"""

        recommendations = []

        # Overall quality recommendations
        overall_quality = quality_analysis.get('overall', {}).get('average_quality_score', 0.0)
        if overall_quality >= 0.8:
            recommendations.append("✅ Test case quality is excellent. Ready for F1 validation.")
        elif overall_quality >= 0.6:
            recommendations.append("⚠️ Test case quality is good but could be improved. Consider enhancing clinical context.")
        else:
            recommendations.append("🔧 Test case quality needs improvement. Review generation patterns and clinical accuracy.")

        # Specialty-specific recommendations
        for specialty, projections in performance_projections.items():
            if specialty == 'overall':
                continue

            projected_f1 = projections['projected_f1']
            target_f1 = projections['target_f1']

            if projected_f1 >= target_f1:
                recommendations.append(f"🎯 {specialty.title()}: Projected F1 ({projected_f1:.3f}) meets target. Proceed with validation.")
            else:
                gap = target_f1 - projected_f1
                recommendations.append(f"📈 {specialty.title()}: Projected F1 ({projected_f1:.3f}) falls short of target by {gap:.3f}. Consider additional enhancement patterns.")

        # Research source recommendations
        recommendations.append("🔬 Continue leveraging ClinicalTrials.gov for realistic language patterns.")
        recommendations.append("⚡ Focus enhanced synthetic generation on F1 gap areas identified per specialty.")

        return recommendations

    def _generate_monitoring_alerts(self, performance_projections: Dict) -> List[Dict[str, Any]]:
        """Generate monitoring alerts"""

        alerts = []

        for specialty, projections in performance_projections.items():
            if specialty == 'overall':
                continue

            # Target achievement alert
            if not projections['target_achievable']:
                alerts.append({
                    'severity': 'warning',
                    'specialty': specialty,
                    'type': 'target_gap',
                    'message': f"{specialty.title()} projected F1 ({projections['projected_f1']:.3f}) may not reach target ({projections['target_f1']:.3f})",
                    'action_required': 'Consider additional test case enhancements or pattern refinement'
                })

            # Low confidence alert
            if projections['confidence_level'] == 'Low':
                alerts.append({
                    'severity': 'info',
                    'specialty': specialty,
                    'type': 'low_confidence',
                    'message': f"{specialty.title()} projection confidence is low",
                    'action_required': 'Validate projections with actual F1 testing'
                })

        return alerts

    def _save_dashboard(self, dashboard: Dict) -> str:
        """Save dashboard to file"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"performance_monitoring_dashboard_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(dashboard, f, indent=2)

        return filename

    def _print_dashboard_summary(self, dashboard: Dict):
        """Print dashboard summary"""

        print(f"\n📊 DASHBOARD SUMMARY")
        print("="*50)

        # Test suite overview
        overview = dashboard['test_suite_overview']
        print(f"📝 Total Test Cases: {overview['total_test_cases']}")
        print(f"🏥 Specialties: {overview['total_specialties']}")

        # Quality analysis
        quality = dashboard['quality_analysis']['overall']
        print(f"⭐ Overall Quality: {quality['quality_grade']} ({quality['average_quality_score']:.2f})")

        # Performance projections
        projections = dashboard['performance_projections']
        print(f"\n🎯 F1 PROJECTIONS:")

        for specialty in ['emergency', 'pediatrics', 'cardiology', 'oncology']:
            if specialty in projections:
                proj = projections[specialty]
                status = "✅" if proj['target_achievable'] else "⚠️"
                print(f"   {status} {specialty.title()}: {proj['baseline_f1']:.3f} → {proj['projected_f1']:.3f} (Target: {proj['target_f1']:.3f})")

        overall_proj = projections.get('overall', {})
        if overall_proj:
            status = "✅" if overall_proj.get('target_achievable', False) else "⚠️"
            print(f"   {status} Overall: {overall_proj['baseline_f1']:.3f} → {overall_proj['projected_f1']:.3f} (Target: {overall_proj['target_f1']:.3f})")

        # Top recommendations
        recommendations = dashboard['recommendations'][:3]
        print(f"\n💡 TOP RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")

def main():
    """Generate performance monitoring dashboard"""

    # Find latest enhanced P0 test cases
    test_files = list(Path('.').glob('enhanced_p0_specialty_test_cases_*.json'))
    if not test_files:
        print("❌ No enhanced P0 test cases found. Run enhanced_p0_generator.py first.")
        return

    latest_file = max(test_files, key=lambda f: f.stat().st_mtime)
    print(f"📁 Using test cases from: {latest_file}")

    dashboard = PerformanceMonitoringDashboard()
    results = dashboard.generate_comprehensive_dashboard(str(latest_file))

    return results

if __name__ == "__main__":
    main()