"""
Story 4.1: Template-based Bundle Summarization
Deterministic, fast plain-English summaries for FHIR Bundles
"""

from typing import Any, Dict, List
from collections import Counter


class SummarizationService:
    """Deterministic summarization for FHIR Bundles"""

    def summarize(self, bundle: Dict[str, Any], role: str = "clinician", context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Generate a plain-English summary and bundle stats.

        - Counts resources by type
        - Produces concise English lines per recognized resource
        - Returns summary text, stats, and confidence placeholders
        """
        entries = bundle.get("entry", []) or []
        resource_types = [e.get("resource", {}).get("resourceType") for e in entries if isinstance(e, dict)]
        counts = Counter([rt for rt in resource_types if rt])

        lines: List[str] = []

        for e in entries:
            r = e.get("resource", {}) if isinstance(e, dict) else {}
            rt = r.get("resourceType")
            if rt == "MedicationRequest":
                med = self._get_med_name(r)
                dose = self._get_dose(r)
                freq = self._get_frequency(r)
                line = f"Medication order: {med}{(' ' + dose) if dose else ''}{(' ' + freq) if freq else ''}."
                lines.append(line)
            elif rt == "ServiceRequest":
                code = self._get_code_text(r)
                line = f"Service request: {code}."
                lines.append(line)
            elif rt == "Condition":
                cond = self._get_code_text(r)
                line = f"Condition noted: {cond}."
                lines.append(line)
            elif rt == "Observation":
                code = self._get_code_text(r)
                value = self._get_obs_value(r)
                interp = self._get_obs_interpretation(r)
                part = f"Observation: {code}"
                if value:
                    part += f" = {value}"
                if interp:
                    part += f" ({interp})"
                lines.append(part + ".")
            elif rt == "DiagnosticReport":
                code = self._get_code_text(r)
                concl = r.get("conclusion")
                line = f"Diagnostic report: {code}"
                if concl:
                    line += f" — {concl}"
                lines.append(line + ".")
            elif rt == "Procedure":
                code = self._get_code_text(r)
                lines.append(f"Procedure: {code}.")
            elif rt == "ImagingStudy":
                mods = r.get("series", []) or []
                modality = None
                if mods and isinstance(mods, list):
                    first = mods[0]
                    modality = (first.get("modality", {}) or {}).get("code") or (first.get("modality", {}) or {}).get("display")
                detail = f" modality {modality}" if modality else ""
                lines.append(f"Imaging study:{detail} detected.")
            elif rt in {"Patient", "Practitioner"}:
                # Keep minimal to avoid PHI; context only
                lines.append(f"{rt} present for context.")

        if not lines:
            lines.append("No actionable clinical orders detected in bundle.")

        # Simple role-based tweak (non-PHI):
        if role == "administrator":
            lines.insert(0, "Summary for administrator: focus on completeness and compliance.")
        elif role == "technical":
            lines.insert(0, "Technical summary: includes resource counts and types.")

        human = " ".join(lines)

        bundle_summary = {
            "total_entries": len(entries),
            "resource_counts": dict(counts),
            "recognized_types": sorted(list(counts.keys())),
        }

        confidence = {
            "method": "template",
            "deterministic": True,
            "role": role,
            "quality": {
                "coverage_score": 1.0 if len(entries) == sum(counts.values()) else 0.9,
                "coherence_score": 0.9,
            },
        }

        return {
            "human_readable_summary": human,
            "bundle_summary": bundle_summary,
            "confidence_indicators": confidence,
        }

    def _get_med_name(self, r: Dict[str, Any]) -> str:
        cc = r.get("medicationCodeableConcept", {})
        if "text" in cc and cc["text"]:
            return cc["text"]
        codings = cc.get("coding", [])
        if codings and isinstance(codings, list):
            return codings[0].get("display") or codings[0].get("code") or "Medication"
        return "Medication"

    def _get_dose(self, r: Dict[str, Any]) -> str | None:
        di = r.get("dosageInstruction", [])
        if not di:
            return None
        dose = di[0].get("doseAndRate", [])
        if dose:
            dr = dose[0].get("doseQuantity") or {}
            val, unit = dr.get("value"), dr.get("unit")
            if val and unit:
                return f"{val} {unit}"
        text = di[0].get("text")
        return text

    def _get_frequency(self, r: Dict[str, Any]) -> str | None:
        di = r.get("dosageInstruction", [])
        if not di:
            return None
        timing = di[0].get("timing", {})
        repeat = timing.get("repeat", {})
        if "frequency" in repeat and "period" in repeat and "periodUnit" in repeat:
            return f"{repeat['frequency']}/{repeat['period']}{repeat['periodUnit']}"
        return None

    def _get_code_text(self, r: Dict[str, Any]) -> str:
        code = r.get("code", {})
        if isinstance(code, dict):
            if code.get("text"):
                return code["text"]
            codings = code.get("coding", [])
            if codings:
                return codings[0].get("display") or codings[0].get("code") or "Item"
        return "Item"

    def _get_obs_value(self, r: Dict[str, Any]) -> str | None:
        vq = r.get("valueQuantity")
        if isinstance(vq, dict):
            val = vq.get("value")
            unit = vq.get("unit") or vq.get("code")
            if val is not None:
                return f"{val} {unit}".strip()
        vs = r.get("valueString")
        if vs:
            return str(vs)
        return None

    def _get_obs_interpretation(self, r: Dict[str, Any]) -> str | None:
        interp = r.get("interpretation")
        if isinstance(interp, dict):
            if interp.get("text"):
                return interp["text"]
            codings = interp.get("coding", [])
            if codings:
                return codings[0].get("display") or codings[0].get("code")
        elif isinstance(interp, list) and interp:
            first = interp[0]
            if first.get("text"):
                return first["text"]
            codings = first.get("coding", [])
            if codings:
                return codings[0].get("display") or codings[0].get("code")
        return None
