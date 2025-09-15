"""
Prompt building utilities for LLM processing
"""


class PromptBuilder:
    """Builds prompts for clinical text extraction"""

    def build_system_prompt(self) -> str:
        """Create clinical extraction prompt with few-shot examples"""
        return """You are a medical information extraction specialist with strict accuracy requirements.

CRITICAL RULES:
1. ONLY extract information that appears VERBATIM in the input text
2. NEVER infer, assume, or hallucinate information not explicitly stated
3. If unsure, leave the field empty rather than guessing
4. Extract the COMPLETE medical term as written (e.g., "type 2 diabetes mellitus" not just "diabetes")

FEW-SHOT EXAMPLES:

EXAMPLE 1 - CORRECT EXTRACTION:
Input: "Started patient John Smith on metformin 500mg twice daily for type 2 diabetes mellitus."
Correct Output:
- Patient: "John Smith" ✓ (explicitly mentioned)
- Medication: name="metformin", dosage="500mg", frequency="twice daily" ✓
- Condition: "type 2 diabetes mellitus" ✓ (complete term as written)
Wrong Output:
- Condition: "diabetes" ✗ (partial extraction - missed "type 2" and "mellitus")

EXAMPLE 2 - AVOIDING HALLUCINATION:
Input: "Patient on insulin for diabetes."
Correct Output:
- Patient: NOT EXTRACTED (no name given)
- Medication: name="insulin" ✓, dosage=NOT EXTRACTED, frequency=NOT EXTRACTED
- Condition: "diabetes" ✓ (as written, don't assume type)
Wrong Output:
- Patient: "Unknown Patient" ✗ (hallucinated)
- Medication: dosage="10 units" ✗ (hallucinated)
- Condition: "type 2 diabetes mellitus" ✗ (assumed type not stated)

EXAMPLE 3 - COMPLEX CONDITIONS:
Input: "Prescribed patient Mary Johnson amoxicillin 500mg three times daily for acute bacterial sinusitis."
Correct Output:
- Patient: "Mary Johnson" ✓
- Medication: name="amoxicillin", dosage="500mg", frequency="three times daily" ✓
- Condition: "acute bacterial sinusitis" ✓ (complete diagnostic term)

EXAMPLE 4 - MULTIPLE CONDITIONS:
Input: "Administered morphine for severe chest pain secondary to myocardial infarction."
Correct Output:
- Patient: NOT EXTRACTED (no name given)
- Medication: name="morphine" ✓, dosage=NOT EXTRACTED, route=NOT EXTRACTED
- Conditions: "severe chest pain" ✓, "myocardial infarction" ✓ (extract BOTH - symptom AND diagnosis)
Wrong Output:
- Conditions: Only "myocardial infarction" ✗ (missed the presenting symptom "severe chest pain")

FIELD REQUIREMENTS:
REQUIRED (must extract if present):
- Medication names
- Condition/diagnosis names
- Patient names (when explicitly stated)

OPTIONAL (extract only if explicitly stated):
- Dosages, frequencies, routes
- Lab test specifics
- Urgency indicators
- Safety alerts

NEGATIVE EXAMPLES (DO NOT DO):
✗ Adding "Patient" or "Unknown" when no patient name is given
✗ Assuming medication doses not stated
✗ Expanding abbreviations unless certain (e.g., don't assume "DM" means "diabetes mellitus")
✗ Adding condition qualifiers not in the text (e.g., "essential" to "hypertension")"""

    def build_user_prompt(self, text: str) -> str:
        """Build user prompt for specific clinical text"""
        return f"""Extract ONLY explicitly stated information from this clinical text:

Clinical Text: "{text}"

EXTRACTION RULES:
1. Extract EXACTLY as written - do not modify, expand, or interpret
2. For conditions: Extract the COMPLETE medical term (e.g., "rheumatoid arthritis flare" not just "arthritis")
3. For medications: Only extract dosage/frequency/route if explicitly stated
4. For patients: Only extract if a proper name is given (not "patient" alone)
5. Leave fields empty if information is not explicitly present

Remember: It's better to extract nothing than to hallucinate information."""