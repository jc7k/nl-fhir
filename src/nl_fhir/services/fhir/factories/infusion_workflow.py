"""
Infusion Workflow Orchestration (Epic IW-001, Story IW-005)

Builds a complete FHIR R4 transaction Bundle for an infusion therapy workflow:

    Patient -> MedicationRequest -> Device -> MedicationAdministration
            -> DeviceUseStatement -> Observation (monitoring)

Every resource is created through the FactoryAdapter so construction stays in
the specialized factories. This module only (1) extracts the deterministic,
keyword-level workflow data the narrative carries, (2) wires the references
between the resources, (3) orders the entries so referenced resources precede
their dependents and (4) hands the resolved list to the shared bundle assembler.

HIPAA: log lines carry request ids and counts only, never names or narrative text.
"""

from __future__ import annotations

import copy
import logging
import re
import uuid
from typing import TYPE_CHECKING, Any

from ..bundle_assembler import FHIRBundleAssembler

if TYPE_CHECKING:
    from ..factory_adapter import FactoryAdapter

logger = logging.getLogger(__name__)

# Transaction entry order: lower rank is created first, so a resource always
# precedes the resources that reference it (stable sort keeps creation order
# inside a rank).
DEPENDENCY_ORDER: dict[str, int] = {
    "Patient": 1,
    "Practitioner": 1,
    "Organization": 1,
    "Location": 1,
    "Encounter": 2,
    "EpisodeOfCare": 2,
    "MedicationRequest": 3,
    "ServiceRequest": 3,
    "Device": 4,
    "MedicationAdministration": 5,
    "Procedure": 5,
    "Observation": 5,
    "DeviceUseStatement": 6,
}

# Medications commonly given by infusion/injection; matched as whole words.
INFUSION_MEDICATIONS: tuple[str, ...] = (
    "morphine",
    "vancomycin",
    "epinephrine",
    "diphenhydramine",
    "saline",
    "heparin",
    "insulin",
    "norepinephrine",
    "fentanyl",
    "propofol",
    "dopamine",
    "potassium chloride",
    "magnesium sulfate",
)

# Infusion equipment; the device factory infers SNOMED CT type from the name.
INFUSION_DEVICES: dict[str, str] = {
    "iv pump": "IV pump",
    "pca pump": "PCA pump",
    "syringe pump": "syringe pump",
    "infusion pump": "infusion pump",
}

# Route mentions -> values the medication factory maps to SNOMED CT routes.
ROUTE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b(?:iv|intravenous(?:ly)?)\b"), "IV"),
    (re.compile(r"\b(?:im|intramuscular(?:ly)?)\b"), "IM"),
    (re.compile(r"\b(?:po|oral(?:ly)?|by mouth)\b"), "PO"),
    (re.compile(r"\b(?:sc|sq|subq|subcut|subcutaneous(?:ly)?)\b"), "SC"),
)
DEFAULT_ROUTE = "IV"

DOSE_UNITS = r"(?:mcg|mg|g|ml|units?|meq|mmol)"
FREQUENCY_PATTERN = re.compile(
    r"\b(every\s+\d+\s+(?:hours?|minutes?|hrs?)|q\d+h|once|daily|twice daily|bid|tid|qid|prn|continuous(?:ly)?)\b"
)

# Indication keywords per medication (legacy table, extended for saline).
INDICATION_KEYWORDS: dict[str, tuple[str, ...]] = {
    "morphine": ("pain", "post-operative", "trauma", "surgical"),
    "vancomycin": ("mrsa", "infection", "bacteremia", "sepsis"),
    "epinephrine": ("anaphylaxis", "allergic reaction", "emergency"),
    "diphenhydramine": ("red man syndrome", "allergic reaction", "antihistamine"),
    "saline": ("stabilization", "hydration", "dehydration", "hypotension", "resuscitation"),
}
DEFAULT_INDICATION = "Clinical indication"

# Vital-sign value patterns: label, regex (lowercased text), unit.
VITAL_SIGN_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("heart rate", re.compile(r"\b(?:hr|heart rate)\b\D{0,20}?(\d{2,3})\b"), "bpm"),
    ("temperature", re.compile(r"\b(?:temp|temperature)\b\D{0,20}?(\d{2,3}(?:\.\d)?)\b"), "°F"),
    ("oxygen saturation", re.compile(r"\b(?:spo2|o2 sat|oxygen saturation)\b\D{0,20}?(\d{2,3})\s*%"), "%"),
    ("pain scale", re.compile(r"\bpain\s+(?:scale|score)\b\D{0,10}?(\d{1,2})\s*/\s*10\b"), "/10"),
)
BLOOD_PRESSURE_PATTERN = re.compile(r"\b(?:bp|blood pressure)\b\D{0,40}?(\d{2,3})\s*/\s*(\d{2,3})\b")

MONITORING_KEYWORDS: tuple[str, ...] = (
    "blood pressure monitoring",
    "heart rate monitoring",
    "vital signs monitoring",
    "cardiac monitoring",
    "respiratory monitoring",
    "temperature monitoring",
)

# "Patient Emma Garcia ..." - capitalized given/family name right after "Patient"
PATIENT_NAME_PATTERN = re.compile(r"\bPatient\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b")

# Sentence boundary: '.', ';' or newline, but not the '.' inside "0.3mg"
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<!\d)\.(?!\d)|[;\n]+")


def _short_id() -> str:
    return uuid.uuid4().hex[:8]


class InfusionWorkflowOrchestrator:
    """Assemble complete infusion-therapy transaction bundles from clinical narratives"""

    def __init__(self, adapter: FactoryAdapter, bundle_assembler: FHIRBundleAssembler | None = None):
        self.adapter = adapter
        self.bundle_assembler = bundle_assembler or FHIRBundleAssembler()
        if not self.bundle_assembler.initialized:
            self.bundle_assembler.initialize()

    # ------------------------------------------------------------------ public API

    def create_complete_infusion_bundle(
        self,
        clinical_text: str,
        patient_ref: str | None = None,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Create the complete infusion workflow bundle for a single clinical narrative.

        Args:
            clinical_text: Natural language clinical narrative
            patient_ref: Optional patient id/reference to use for the Patient resource
            request_id: Optional request tracking id

        Returns:
            FHIR transaction Bundle whose entries carry fullUrl + request and whose
            internal references resolve to the entries' urn:uuid fullUrls
        """
        request_id = request_id or f"bundle-{_short_id()}"
        logger.info(f"[{request_id}] Creating complete infusion workflow bundle")

        workflow_data = self.parse_clinical_narrative(clinical_text, request_id)
        if patient_ref:
            workflow_data["patient_data"]["patient_ref"] = patient_ref

        resources = self._build_workflow_resources(workflow_data, request_id)
        return self._assemble_bundle(resources, request_id)

    def create_enhanced_infusion_workflow(
        self,
        clinical_scenarios: list[str],
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Create one bundle spanning several clinical scenarios for the same patient
        (multi-drug infusions, adverse reactions, equipment changes, monitoring escalation).

        Medications and devices named in more than one scenario become a single
        resource; monitoring observations are kept per scenario.
        """
        request_id = request_id or f"enhanced-workflow-{_short_id()}"
        logger.info(
            f"[{request_id}] Creating enhanced infusion workflow for {len(clinical_scenarios)} scenarios"
        )

        parsed = [
            self.parse_clinical_narrative(scenario, f"{request_id}-scenario-{index}")
            for index, scenario in enumerate(clinical_scenarios, start=1)
        ]
        workflow_data = self._merge_workflow_data(parsed)

        resources = self._build_workflow_resources(workflow_data, request_id)
        return self._assemble_bundle(resources, request_id)

    # ------------------------------------------------------------------ narrative parsing

    def parse_clinical_narrative(self, clinical_text: str, request_id: str) -> dict[str, Any]:
        """
        Extract structured workflow data from a clinical narrative.

        Deterministic keyword/regex extraction only (no model calls); the full NLP
        pipeline handles free-form orders elsewhere. Returns:
            patient_data: {"name"?: str} - caller may add "patient_ref"
            practitioner_data / encounter_data: accepted by the builder, not parsed
            medications: [{medication_name, dosage, route, indication, device_names}]
            devices: [{name, identifier}]
            observations: factory-ready observation dicts
        """
        text_lower = clinical_text.lower()
        sentences = [s for s in SENTENCE_SPLIT_PATTERN.split(text_lower) if s.strip()]

        devices = self._extract_devices(text_lower)
        device_names = [device["name"].lower() for device in devices]

        workflow_data: dict[str, Any] = {
            "patient_data": self._extract_patient(clinical_text),
            "practitioner_data": [],
            "encounter_data": None,
            "medications": self._extract_medications(text_lower, sentences, device_names),
            "devices": devices,
            "observations": self._extract_observations(text_lower),
        }

        logger.info(
            f"[{request_id}] Parsed clinical narrative: {len(workflow_data['medications'])} medications, "
            f"{len(devices)} devices, {len(workflow_data['observations'])} observations"
        )
        return workflow_data

    def _extract_patient(self, clinical_text: str) -> dict[str, Any]:
        match = PATIENT_NAME_PATTERN.search(clinical_text)
        return {"name": match.group(1)} if match else {}

    def _extract_medications(
        self, text_lower: str, sentences: list[str], device_names: list[str]
    ) -> list[dict[str, Any]]:
        medications: list[dict[str, Any]] = []
        for medication in INFUSION_MEDICATIONS:
            if not re.search(rf"\b{re.escape(medication)}\b", text_lower):
                continue

            sentence = next((s for s in sentences if medication in s), text_lower)
            med_pos = sentence.find(medication)
            after = sentence[med_pos + len(medication) :]
            before = sentence[:med_pos]

            dose_match = re.match(rf"\s+(\d+(?:\.\d+)?\s*{DOSE_UNITS})\b", after)
            dosage = dose_match.group(1).replace(" ", "") if dose_match else "dose not specified"
            frequency_match = FREQUENCY_PATTERN.search(after)
            if frequency_match:
                dosage = f"{dosage} {frequency_match.group(1)}"

            medications.append(
                {
                    "medication_name": medication,
                    "dosage": dosage,
                    "route": self._extract_route(after, before),
                    "indication": self._extract_indication(sentence, text_lower, medication),
                    # devices named alongside the drug are linked to its administration
                    "device_names": [name for name in device_names if name in sentence],
                }
            )
        return medications

    def _extract_route(self, after: str, before: str) -> str:
        """Nearest route mention after the drug name, else before it in the same sentence"""
        for segment in (after, before):
            best: tuple[int, str] | None = None
            for pattern, route in ROUTE_PATTERNS:
                match = pattern.search(segment)
                if match and (best is None or match.start() < best[0]):
                    best = (match.start(), route)
            if best:
                return best[1]
        return DEFAULT_ROUTE

    def _extract_indication(self, sentence: str, text_lower: str, medication: str) -> str:
        """Indication keyword for the drug, preferring the sentence it appears in"""
        for keyword in INDICATION_KEYWORDS.get(medication, ()):
            if keyword in sentence:
                return f"{keyword.title()} management"
        for keyword in INDICATION_KEYWORDS.get(medication, ()):
            if keyword in text_lower:
                return f"{keyword.title()} management"
        return DEFAULT_INDICATION

    def _extract_devices(self, text_lower: str) -> list[dict[str, Any]]:
        return [
            {
                "name": display_name,
                "identifier": f"{keyword.upper().replace(' ', '-')}-{_short_id()[:6].upper()}",
            }
            for keyword, display_name in INFUSION_DEVICES.items()
            if keyword in text_lower
        ]

    def _extract_observations(self, text_lower: str) -> list[dict[str, Any]]:
        observations: list[dict[str, Any]] = []
        measured: set[str] = set()

        bp_match = BLOOD_PRESSURE_PATTERN.search(text_lower)
        if bp_match:
            measured.add("blood pressure")
            observations.append(
                {
                    "name": "blood pressure",
                    "type": "vital-signs",
                    "components": [
                        {
                            "name": "systolic blood pressure",
                            "value_quantity": {"value": int(bp_match.group(1)), "unit": "mmHg"},
                        },
                        {
                            "name": "diastolic blood pressure",
                            "value_quantity": {"value": int(bp_match.group(2)), "unit": "mmHg"},
                        },
                    ],
                }
            )

        for name, pattern, unit in VITAL_SIGN_PATTERNS:
            match = pattern.search(text_lower)
            if not match:
                continue
            raw = match.group(1)
            value: float | int = float(raw) if "." in raw else int(raw)
            measured.add(name)
            observations.append(
                {
                    "name": name,
                    "type": "vital-signs",
                    "value_quantity": {"value": value, "unit": unit},
                }
            )

        if "iv site" in text_lower:
            if "clear" in text_lower:
                assessment = "IV site clear, no signs of redness or swelling"
            elif "redness" in text_lower or "swelling" in text_lower or "infiltration" in text_lower:
                assessment = "IV site shows signs of irritation"
            else:
                assessment = "IV site assessed, no complications documented"
            observations.append(
                {
                    "name": "iv site assessment",
                    "type": "assessment",
                    "value_string": assessment,
                    "notes": "Regular IV site monitoring during infusion",
                }
            )

        # Monitoring mentioned without a value (skip when the value was captured above)
        for keyword in MONITORING_KEYWORDS:
            monitoring_type = keyword.removesuffix(" monitoring")
            if keyword in text_lower and monitoring_type not in measured:
                observations.append(
                    {
                        "name": keyword,
                        "type": "monitoring",
                        "value_string": f"Continuous {monitoring_type} monitoring during infusion therapy",
                        "notes": f"Patient monitored for {monitoring_type} changes during treatment",
                    }
                )

        return observations

    def _merge_workflow_data(self, scenarios: list[dict[str, Any]]) -> dict[str, Any]:
        """Combine per-scenario data for one patient: first mention of a drug/device wins"""
        merged: dict[str, Any] = {
            "patient_data": {},
            "practitioner_data": [],
            "encounter_data": None,
            "medications": [],
            "devices": [],
            "observations": [],
        }
        medications: dict[str, dict[str, Any]] = {}
        devices: dict[str, dict[str, Any]] = {}

        for scenario in scenarios:
            if not merged["patient_data"] and scenario.get("patient_data"):
                merged["patient_data"] = dict(scenario["patient_data"])
            merged["practitioner_data"].extend(scenario.get("practitioner_data") or [])
            if merged["encounter_data"] is None and scenario.get("encounter_data"):
                merged["encounter_data"] = scenario["encounter_data"]

            for medication in scenario.get("medications", []):
                existing = medications.get(medication["medication_name"])
                if existing is None:
                    medications[medication["medication_name"]] = dict(medication)
                else:
                    for device_name in medication.get("device_names", []):
                        if device_name not in existing["device_names"]:
                            existing["device_names"].append(device_name)

            for device in scenario.get("devices", []):
                devices.setdefault(device["name"].lower(), device)

            merged["observations"].extend(scenario.get("observations", []))

        merged["medications"] = list(medications.values())
        merged["devices"] = list(devices.values())
        return merged

    # ------------------------------------------------------------------ resource creation

    def _build_workflow_resources(self, workflow_data: dict[str, Any], request_id: str) -> list[dict[str, Any]]:
        """Create every workflow resource through the adapter, in dependency phases"""
        adapter = self.adapter
        resources: list[dict[str, Any]] = []
        medications: list[dict[str, Any]] = workflow_data.get("medications") or []
        devices: list[dict[str, Any]] = workflow_data.get("devices") or []

        # Phase 1: identity resources
        patient_data = dict(workflow_data.get("patient_data") or {})
        patient_data.setdefault("patient_ref", f"patient-{_short_id()}")
        patient = adapter.create_patient_resource(patient_data, request_id)
        resources.append(patient)
        patient_id: str = patient["id"]

        practitioner_refs: dict[str, str] = {}
        for practitioner_data in workflow_data.get("practitioner_data") or []:
            practitioner = adapter.create_practitioner_resource(practitioner_data, request_id)
            resources.append(practitioner)
            role = practitioner_data.get("role", "unknown")
            practitioner_refs[role] = f"Practitioner/{practitioner['id']}"

        encounter_ref: str | None = None
        if workflow_data.get("encounter_data"):
            encounter = adapter.create_encounter_resource(workflow_data["encounter_data"], patient_id, request_id)
            resources.append(encounter)
            encounter_ref = f"Encounter/{encounter['id']}"

        # Phase 2: clinical orders
        med_request_ids: dict[str, str] = {}
        for medication in medications:
            med_request = adapter.create_medication_request(
                self._medication_request_data(medication),
                patient_id,
                request_id,
                practitioner_ref=practitioner_refs.get("ordering"),
                encounter_ref=encounter_ref,
            )
            resources.append(med_request)
            med_request_ids[medication["medication_name"]] = med_request["id"]

        # Phase 3: infusion equipment
        device_ids: dict[str, str] = {}
        for device_data in devices:
            device = adapter.create_device_resource(device_data, request_id)
            resources.append(device)
            device_ids[device_data["name"].lower()] = device["id"]

        # Phase 4: administration events (reference the order and the device used)
        for medication in medications:
            med_admin = adapter.create_medication_administration(
                self._medication_administration_data(medication, device_ids),
                patient_id,
                request_id,
                practitioner_ref=practitioner_refs.get("administering"),
                encounter_ref=encounter_ref,
                medication_request_ref=med_request_ids.get(medication["medication_name"]),
            )
            resources.append(med_admin)

        # Phase 5: device-patient linking
        for device_data in devices:
            device_name = device_data["name"].lower()
            administered = [
                medication["medication_name"]
                for medication in medications
                if device_name in medication.get("device_names", [])
            ]
            usage_data = {
                "indication": "Infusion therapy",
                "notes": (
                    f"{device_data['name']} used for {', '.join(administered)} administration"
                    if administered
                    else f"{device_data['name']} used for medication administration"
                ),
            }
            device_use = adapter.create_device_use_statement(
                patient_id, device_ids[device_name], usage_data=usage_data, request_id=request_id
            )
            resources.append(device_use)

        # Phase 6: monitoring observations
        for observation_data in workflow_data.get("observations") or []:
            observation = adapter.create_observation_resource(
                observation_data, patient_id, request_id, encounter_ref=encounter_ref
            )
            resources.append(observation)

        logger.info(f"[{request_id}] Created {len(resources)} infusion workflow resources")
        return resources

    @staticmethod
    def _medication_request_data(medication: dict[str, Any]) -> dict[str, Any]:
        return {
            "medication_name": medication["medication_name"],
            "dosage": medication["dosage"],
            "route": medication["route"],
        }

    @staticmethod
    def _medication_administration_data(
        medication: dict[str, Any], device_ids: dict[str, str]
    ) -> dict[str, Any]:
        data = {
            "medication_name": medication["medication_name"],
            "dosage": medication["dosage"],
            "route": medication["route"],
            "reason": medication.get("indication", DEFAULT_INDICATION),
        }
        device_id = next(
            (device_ids[name] for name in medication.get("device_names", []) if name in device_ids),
            None,
        )
        if device_id:
            data["device"] = device_id
        return data

    # ------------------------------------------------------------------ bundle assembly

    def _assemble_bundle(self, resources: list[dict[str, Any]], request_id: str) -> dict[str, Any]:
        ordered = self._order_resources_by_dependencies(resources, request_id)
        resolved = self._resolve_bundle_references(ordered, request_id)
        bundle = self.bundle_assembler.create_transaction_bundle(resolved, request_id)
        logger.info(f"[{request_id}] Infusion workflow bundle created with {len(bundle.get('entry', []))} entries")
        return bundle

    def _order_resources_by_dependencies(
        self, resources: list[dict[str, Any]], request_id: str
    ) -> list[dict[str, Any]]:
        """Sort by DEPENDENCY_ORDER (stable), so referenced resources precede dependents"""
        ordered = sorted(resources, key=lambda resource: DEPENDENCY_ORDER.get(resource["resourceType"], 99))
        logger.debug(f"[{request_id}] Ordered {len(ordered)} resources by dependencies")
        return ordered

    def _resolve_bundle_references(
        self, resources: list[dict[str, Any]], request_id: str
    ) -> list[dict[str, Any]]:
        """
        Rewrite every 'Type/id' reference that points at a bundle member to that
        member's fullUrl (urn:uuid:<id>), the form the assembler gives each entry.
        Resources are deep-copied; the factory outputs are left untouched.
        """
        mapping = {
            f"{resource['resourceType']}/{resource['id']}": f"urn:uuid:{resource['id']}" for resource in resources
        }

        def rewrite(obj: Any) -> None:
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == "reference" and isinstance(value, str) and value in mapping:
                        obj[key] = mapping[value]
                    else:
                        rewrite(value)
            elif isinstance(obj, list):
                for item in obj:
                    rewrite(item)

        resolved = [copy.deepcopy(resource) for resource in resources]
        for resource in resolved:
            rewrite(resource)
        logger.debug(f"[{request_id}] Resolved references for {len(resolved)} resources")
        return resolved
