"""
FHIR Administrative Resource Factory
Specialized factory for Practitioner, Specimen and Coverage resources.

These three resource types previously had no registered factory, so the
registry fell back to MockResourceFactory, which emitted placeholder
resources (a Practitioner with a non-R4 ``status`` element and no name, a
Specimen without subject/type, a Coverage without beneficiary). Every
/convert request creates a Practitioner, so the mock output broke typed
bundle assembly on every request.
"""

import logging
import re
import time
import uuid
from datetime import date, datetime, timezone
from typing import Any

from .base import BaseResourceFactory

logger = logging.getLogger(__name__)

SNOMED_SYSTEM = "http://snomed.info/sct"
NPI_SYSTEM = "http://hl7.org/fhir/sid/us-npi"
V2_0203_SYSTEM = "http://terminology.hl7.org/CodeSystem/v2-0203"
V2_0360_SYSTEM = "http://terminology.hl7.org/CodeSystem/v2-0360"
V3_ACT_CODE_SYSTEM = "http://terminology.hl7.org/CodeSystem/v3-ActCode"
COVERAGE_CLASS_SYSTEM = "http://terminology.hl7.org/CodeSystem/coverage-class"
SUBSCRIBER_RELATIONSHIP_SYSTEM = "http://terminology.hl7.org/CodeSystem/subscriber-relationship"
LOCAL_PRACTITIONER_ID_SYSTEM = "http://hospital.local/practitioner-id"
LOCAL_SPECIMEN_ID_SYSTEM = "http://hospital.local/specimen-id"
LOCAL_COVERAGE_ID_SYSTEM = "http://hospital.local/coverage-id"

_FHIR_ID_PATTERN = re.compile(r"^[A-Za-z0-9\-\.]{1,64}$")
_INVALID_ID_CHARS = re.compile(r"[^A-Za-z0-9\-\.]+")
_FHIR_DATETIME_PATTERN = re.compile(
    r"^\d{4}(-\d{2}(-\d{2}(T\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:\d{2}))?)?)?$"
)
_CONTACT_POINT_SYSTEMS = {"phone", "fax", "email", "pager", "url", "sms", "other"}
_CONTACT_POINT_USES = {"home", "work", "temp", "old", "mobile"}


class AdministrativeResourceFactory(BaseResourceFactory):
    """
    Factory for administrative FHIR R4 resources: Practitioner, Specimen, Coverage.

    Accepts the loosely structured input used by the conversion pipeline and the
    FactoryAdapter (``name``/``npi``/``identifier`` for practitioners,
    ``type``/``collection`` plus ``patient_ref``/``patient_id`` for specimens,
    ``payor``/``type``/``member_id`` plus ``patient_ref``/``patient_id`` for
    coverage) and emits resources that validate against fhir.resources R4B.
    """

    SUPPORTED_RESOURCES = {"Practitioner", "Specimen", "Coverage"}

    NAME_PREFIXES = {"dr", "dr.", "mr", "mr.", "mrs", "mrs.", "ms", "ms.", "prof", "prof."}
    NAME_SUFFIXES = {
        "md", "m.d.", "do", "d.o.", "rn", "np", "pa", "pa-c", "phd", "ph.d.", "pharmd",
        "dds", "dmd", "jr", "jr.", "sr", "sr.", "ii", "iii", "iv",
    }  # fmt: skip

    # HL7 v2 table 0360 (degree / license / certificate)
    QUALIFICATION_CODES = {
        "MD": "Doctor of Medicine",
        "DO": "Doctor of Osteopathy",
        "RN": "Registered Nurse",
        "NP": "Nurse Practitioner",
        "PA": "Physician Assistant",
        "PHARMD": "Doctor of Pharmacy",
        "PHD": "Doctor of Philosophy",
        "DDS": "Doctor of Dental Surgery",
        "DMD": "Doctor of Dental Medicine",
        "LPN": "Licensed Practical Nurse",
        "CNM": "Certified Nurse Midwife",
        "CRNA": "Certified Registered Nurse Anesthetist",
        "RPH": "Registered Pharmacist",
        "EMT": "Emergency Medical Technician",
        "PN": "Advanced Practice Nurse",
    }

    # SNOMED CT specimen type codes (hl7 v2-0487 / specimen-type value set)
    SPECIMEN_TYPE_CODES = {
        "blood": ("119297000", "Blood specimen"),
        "whole_blood": ("258580003", "Whole blood sample"),
        "venous_blood": ("122555007", "Venous blood specimen"),
        "arterial_blood": ("122552005", "Arterial blood specimen"),
        "capillary_blood": ("122554006", "Capillary blood specimen"),
        "serum": ("119364003", "Serum specimen"),
        "plasma": ("119361006", "Plasma specimen"),
        "urine": ("122575003", "Urine specimen"),
        "stool": ("119339001", "Stool specimen"),
        "feces": ("119339001", "Stool specimen"),
        "sputum": ("119334006", "Sputum specimen"),
        "saliva": ("119342007", "Saliva specimen"),
        "csf": ("258450006", "Cerebrospinal fluid sample"),
        "cerebrospinal_fluid": ("258450006", "Cerebrospinal fluid sample"),
        "tissue": ("119376003", "Tissue specimen"),
        "swab": ("257261003", "Swab"),
        "nasopharyngeal_swab": ("258500001", "Nasopharyngeal swab"),
        "throat_swab": ("258529004", "Throat swab"),
        "wound": ("258415003", "Biopsy sample"),
        "biopsy": ("258415003", "Biopsy sample"),
        "bone_marrow": ("396997002", "Specimen from bone marrow obtained by aspiration"),
        "hair": ("119326000", "Hair specimen"),
        "nail": ("119327009", "Nail specimen"),
        "semen": ("119347001", "Seminal fluid specimen"),
        "synovial_fluid": ("119332005", "Synovial fluid specimen"),
        "pleural_fluid": ("418564007", "Pleural fluid specimen"),
        "peritoneal_fluid": ("168139001", "Peritoneal fluid sample"),
        "amniotic_fluid": ("119373006", "Amniotic fluid specimen"),
        "breast_milk": ("119345009", "Breast milk specimen"),
    }

    # SNOMED CT specimen collection methods (specimen-collection-method value set)
    COLLECTION_METHOD_CODES = {
        "venipuncture": ("28520004", "Venipuncture"),
        "finger_stick": ("278450005", "Finger-prick sampling"),
        "fingerstick": ("278450005", "Finger-prick sampling"),
        "heel_stick": ("278450005", "Finger-prick sampling"),
        "arterial_puncture": ("129300006", "Puncture"),
        "puncture": ("129300006", "Puncture"),
        "aspiration": ("129316008", "Aspiration"),
        "biopsy": ("129314006", "Biopsy"),
        "excision": ("129304002", "Excision"),
        "scraping": ("129323009", "Scraping"),
        "clean_catch": ("73416001", "Urine specimen collection, clean catch"),
        "catheter": ("70777001", "Urine specimen collection, catheterized"),
        "catheterized": ("70777001", "Urine specimen collection, catheterized"),
        "timed_urine": ("225113003", "Timed urine collection"),
        "coughed_sputum": ("386089008", "Collection of coughed sputum"),
    }

    SPECIMEN_STATUSES = {"available", "unavailable", "unsatisfactory", "entered-in-error"}
    COVERAGE_STATUSES = {"active", "cancelled", "draft", "entered-in-error"}

    # HL7 v3 ActCoverageTypeCode
    COVERAGE_TYPE_CODES = {
        "medical": ("EHCPOL", "extended healthcare"),
        "health": ("EHCPOL", "extended healthcare"),
        "ehcpol": ("EHCPOL", "extended healthcare"),
        "dental": ("DENTPRG", "dental program"),
        "vision": ("VISPOL", "vision care policy"),
        "drug": ("DRUGPOL", "drug policy"),
        "pharmacy": ("DRUGPOL", "drug policy"),
        "mental_health": ("MENTPRG", "mental health program"),
        "disability": ("DISPOL", "disability insurance policy"),
        "auto": ("AUTOPOL", "automobile"),
        "workers_compensation": ("WCBPOL", "worker's compensation"),
        "public": ("PUBLICPOL", "public healthcare"),
        "medicare": ("PUBLICPOL", "public healthcare"),
        "medicaid": ("PUBLICPOL", "public healthcare"),
        "hsa": ("HSAPOL", "health spending account"),
    }

    COVERAGE_CLASS_TYPES = {
        "group", "subgroup", "plan", "subplan", "class", "subclass",
        "sequence", "rxbin", "rxpcn", "rxid", "rxgroup",
    }  # fmt: skip

    SUBSCRIBER_RELATIONSHIPS = {"child", "parent", "spouse", "common", "other", "self", "injured"}

    def __init__(self, validators=None, coders=None, reference_manager=None):
        """Initialize administrative factory with shared components"""
        super().__init__(validators, coders, reference_manager)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(
            "AdministrativeResourceFactory initialized (Practitioner/Specimen/Coverage)"
        )

    def supports(self, resource_type: str) -> bool:
        """Check if factory supports the resource type"""
        return resource_type in self.SUPPORTED_RESOURCES

    def _create_resource(
        self, resource_type: str, data: dict[str, Any], request_id: str | None = None
    ) -> dict[str, Any]:
        """Create administrative resource based on type"""
        start_time = time.time()

        if resource_type == "Practitioner":
            resource = self._create_practitioner(data)
        elif resource_type == "Specimen":
            resource = self._create_specimen(data)
        elif resource_type == "Coverage":
            resource = self._create_coverage(data)
        else:
            raise ValueError(f"Unsupported resource type: {resource_type}")

        duration_ms = (time.time() - start_time) * 1000
        self.logger.debug(f"[{request_id}] Created {resource_type} resource in {duration_ms:.2f}ms")
        return resource

    # ------------------------------------------------------------------
    # Practitioner
    # ------------------------------------------------------------------

    def _create_practitioner(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create Practitioner resource (FHIR R4: no ``status`` element)"""
        practitioner: dict[str, Any] = {
            "resourceType": "Practitioner",
            "id": self._resource_id("practitioner", data),
            "active": bool(data.get("active", True)),
        }

        identifiers = self._practitioner_identifiers(data)
        if identifiers:
            practitioner["identifier"] = identifiers

        names = self._practitioner_names(data)
        if names:
            practitioner["name"] = names

        telecom = self._process_telecom(data)
        if telecom:
            practitioner["telecom"] = telecom

        if data.get("gender"):
            practitioner["gender"] = self._normalize_gender(data["gender"])

        birth_date = data.get("birth_date") or data.get("birthDate")
        if birth_date:
            normalized = self._normalize_datetime(birth_date)
            if normalized:
                practitioner["birthDate"] = normalized[:10]

        qualifications = self._practitioner_qualifications(data)
        if qualifications:
            practitioner["qualification"] = qualifications

        return practitioner

    def _practitioner_identifiers(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        identifiers: list[dict[str, Any]] = []

        npi = data.get("npi") or data.get("NPI")
        if npi:
            identifiers.append(
                {
                    "use": "official",
                    "type": self.create_codeable_concept(
                        V2_0203_SYSTEM, "NPI", "National provider identifier"
                    ),
                    "system": NPI_SYSTEM,
                    "value": str(npi).strip(),
                }
            )

        for key in ("identifier", "identifiers"):
            if key in data:
                identifiers.extend(
                    self._coerce_identifiers(data[key], LOCAL_PRACTITIONER_ID_SYSTEM)
                )

        if data.get("license_number"):
            identifiers.append(
                {
                    "use": "official",
                    "type": self.create_codeable_concept(
                        V2_0203_SYSTEM, "MD", "Medical License number"
                    ),
                    "value": str(data["license_number"]).strip(),
                }
            )

        return identifiers

    def _practitioner_names(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        names: list[dict[str, Any]] = []

        raw_name = data.get("name")
        if isinstance(raw_name, str) and raw_name.strip():
            names.append(self._parse_practitioner_name(raw_name))
        elif isinstance(raw_name, dict):
            structured = self._build_structured_name(raw_name)
            if structured:
                names.append(structured)
        elif isinstance(raw_name, list):
            for item in raw_name:
                if isinstance(item, str) and item.strip():
                    names.append(self._parse_practitioner_name(item))
                elif isinstance(item, dict):
                    structured = self._build_structured_name(item)
                    if structured:
                        names.append(structured)

        if any(key in data for key in ("family", "given", "first_name", "last_name")):
            structured = self._build_structured_name(data)
            if structured:
                names.append(structured)

        return names

    def _parse_practitioner_name(self, name_str: str) -> dict[str, Any]:
        """Parse 'Dr. Jane Q Smith, MD' into a HumanName with prefix/suffix"""
        text = re.sub(r"\s+", " ", name_str.strip())
        name: dict[str, Any] = {"use": "official", "text": text}

        working = text
        suffixes: list[str] = []
        if "," in working:
            head, _, tail = working.partition(",")
            # "Smith, John" (family-first) vs "John Smith, MD" (credential suffix)
            tail_tokens = tail.split()
            if tail_tokens and all(
                t.lower().rstrip(",") in self.NAME_SUFFIXES for t in tail_tokens
            ):
                suffixes = tail_tokens
                working = head
            else:
                family = head.strip()
                given = [t for t in tail_tokens if t.lower() not in self.NAME_PREFIXES]
                if family:
                    name["family"] = family
                if given:
                    name["given"] = given
                return name

        tokens = working.split()
        prefixes = []
        while tokens and tokens[0].lower() in self.NAME_PREFIXES:
            prefixes.append(tokens.pop(0))
        while tokens and tokens[-1].lower() in self.NAME_SUFFIXES:
            suffixes.insert(0, tokens.pop())

        if prefixes:
            name["prefix"] = prefixes
        if suffixes:
            name["suffix"] = suffixes

        if len(tokens) == 1:
            name["family"] = tokens[0]
        elif len(tokens) > 1:
            name["given"] = tokens[:-1]
            name["family"] = tokens[-1]

        return name

    def _build_structured_name(self, data: dict[str, Any]) -> dict[str, Any] | None:
        name: dict[str, Any] = {"use": data.get("use", "official")}

        family = data.get("family") or data.get("last_name")
        if family:
            name["family"] = str(family)

        given: list[str] = []
        raw_given = data.get("given") or data.get("first_name")
        if isinstance(raw_given, list):
            given.extend(str(g) for g in raw_given if g)
        elif raw_given:
            given.append(str(raw_given))
        if data.get("middle_name"):
            given.append(str(data["middle_name"]))
        if given:
            name["given"] = given

        for key in ("prefix", "suffix"):
            if data.get(key):
                value = data[key]
                name[key] = [str(value)] if isinstance(value, str) else [str(v) for v in value]

        if not (family or given):
            return None

        text_parts = name.get("prefix", []) + given + ([str(family)] if family else [])
        name["text"] = data.get("text") or " ".join(text_parts)
        return name

    def _practitioner_qualifications(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        qualifications: list[dict[str, Any]] = []

        raw = data.get("qualification") or data.get("qualifications") or data.get("credentials")
        for item in self._as_list(raw):
            qualification = self._qualification_entry(item)
            if qualification:
                qualifications.append(qualification)

        # Specialties have no home on Practitioner (they belong on PractitionerRole);
        # record them as qualifications so the information is not silently dropped.
        specialties = data.get("specialties") or data.get("specialty")
        for specialty in self._as_list(specialties):
            if isinstance(specialty, str) and specialty.strip():
                qualifications.append({"code": {"text": self._humanize(specialty)}})

        return qualifications

    def _qualification_entry(self, item: Any) -> dict[str, Any] | None:
        if isinstance(item, dict):
            if "code" in item and isinstance(item["code"], dict):
                entry = {"code": item["code"]}
                if isinstance(item.get("period"), dict):
                    entry["period"] = item["period"]
                if item.get("issuer"):
                    entry["issuer"] = self._organization_reference(item["issuer"])
                return entry
            item = item.get("code") or item.get("name") or item.get("text")

        if not isinstance(item, str) or not item.strip():
            return None

        code = item.strip()
        known = self.QUALIFICATION_CODES.get(code.upper().replace(".", ""))
        if known:
            return {
                "code": self.create_codeable_concept(
                    V2_0360_SYSTEM, code.upper().replace(".", ""), known, text=code
                )
            }
        return {"code": {"text": code}}

    # ------------------------------------------------------------------
    # Specimen
    # ------------------------------------------------------------------

    def _create_specimen(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create Specimen resource with subject, type and collection details"""
        specimen: dict[str, Any] = {
            "resourceType": "Specimen",
            "id": self._resource_id("specimen", data),
            "status": self._normalize_specimen_status(data.get("status")),
            "subject": self._patient_reference(data),
        }

        identifiers: list[dict[str, Any]] = []
        if "identifier" in data:
            identifiers.extend(
                self._coerce_identifiers(data["identifier"], LOCAL_SPECIMEN_ID_SYSTEM)
            )
        if identifiers:
            specimen["identifier"] = identifiers
        accession = data.get("accession") or data.get("accession_identifier")
        if accession:
            specimen["accessionIdentifier"] = {
                "system": "http://hospital.local/accession",
                "value": str(accession),
            }

        specimen_type = self._specimen_type(data)
        if specimen_type:
            specimen["type"] = specimen_type

        received = data.get("received_time") or data.get("receivedTime")
        if received:
            normalized = self._normalize_datetime(received)
            if normalized:
                specimen["receivedTime"] = normalized

        request_ref = data.get("request") or data.get("service_request_ref")
        if request_ref:
            specimen["request"] = [
                {"reference": self._typed_reference(request_ref, "ServiceRequest")}
            ]

        collection = self._specimen_collection(data)
        if collection:
            specimen["collection"] = collection

        processing = self._specimen_processing(data)
        if processing:
            specimen["processing"] = processing

        notes = self._annotations(data.get("note") or data.get("notes") or data.get("comment"))
        if notes:
            specimen["note"] = notes

        return specimen

    def _normalize_specimen_status(self, status: Any) -> str:
        if isinstance(status, str):
            normalized = status.strip().lower().replace("_", "-")
            if normalized in self.SPECIMEN_STATUSES:
                return normalized
        return "available"

    def _specimen_type(self, data: dict[str, Any]) -> dict[str, Any] | None:
        raw = data.get("specimen_type") or data.get("type")
        if isinstance(raw, dict):
            return raw if ("coding" in raw or "text" in raw) else None
        if not isinstance(raw, str) or not raw.strip():
            return None

        key = self._key(raw)
        code = self.SPECIMEN_TYPE_CODES.get(key)
        if not code:
            # "venous blood sample" -> "venous_blood"; "blood sample" -> "blood"
            for suffix in ("_specimen", "_sample"):
                if key.endswith(suffix):
                    code = self.SPECIMEN_TYPE_CODES.get(key[: -len(suffix)])
                    break
        if code:
            return self.create_codeable_concept(SNOMED_SYSTEM, code[0], code[1], text=raw.strip())
        return {"text": raw.strip()}

    def _specimen_collection(self, data: dict[str, Any]) -> dict[str, Any] | None:
        collection_data = data.get("collection")
        collection_data = dict(collection_data) if isinstance(collection_data, dict) else {}

        # Flat aliases used by callers
        for key in ("collected_date", "collected_datetime", "collectedDateTime", "collection_date"):
            if key in data and key not in collection_data:
                collection_data[key] = data[key]
        if "collection_method" in data and "method" not in collection_data:
            collection_data["method"] = data["collection_method"]
        if "body_site" in data and "site" not in collection_data:
            collection_data["site"] = data["body_site"]

        collection: dict[str, Any] = {}

        collected = next(
            (
                collection_data[key]
                for key in ("collectedDateTime", "collected_datetime", "collected_date",
                            "collection_date", "collected", "date", "time")
                if collection_data.get(key)
            ),
            None,
        )  # fmt: skip
        if collected:
            normalized = self._normalize_datetime(collected)
            if normalized:
                collection["collectedDateTime"] = normalized

        collector = collection_data.get("collector") or collection_data.get("collector_ref")
        if collector:
            collection["collector"] = {
                "reference": self._typed_reference(collector, "Practitioner")
            }

        method = collection_data.get("method")
        if isinstance(method, dict):
            collection["method"] = method
        elif isinstance(method, str) and method.strip():
            code = self.COLLECTION_METHOD_CODES.get(self._key(method))
            if code:
                collection["method"] = self.create_codeable_concept(
                    SNOMED_SYSTEM, code[0], code[1], text=self._humanize(method)
                )
            else:
                collection["method"] = {"text": self._humanize(method)}

        site = collection_data.get("bodySite") or collection_data.get("site")
        if isinstance(site, dict):
            collection["bodySite"] = site
        elif isinstance(site, str) and site.strip():
            collection["bodySite"] = {"text": self._humanize(site)}

        quantity = collection_data.get("quantity")
        if isinstance(quantity, dict) and "value" in quantity:
            collection["quantity"] = quantity

        return collection or None

    def _specimen_processing(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        processing: list[dict[str, Any]] = []
        for item in self._as_list(data.get("processing")):
            if isinstance(item, str) and item.strip():
                processing.append({"description": item.strip()})
                continue
            if not isinstance(item, dict):
                continue
            entry: dict[str, Any] = {}
            procedure = item.get("procedure")
            if isinstance(procedure, dict):
                entry["procedure"] = procedure
            elif isinstance(procedure, str) and procedure.strip():
                entry["procedure"] = {"text": self._humanize(procedure)}
            description_parts = [
                f"{self._humanize(k)}: {self._humanize(str(v))}"
                for k, v in item.items()
                if k not in ("procedure", "time", "timeDateTime", "additive") and v
            ]
            if item.get("description"):
                entry["description"] = str(item["description"])
            elif description_parts:
                entry["description"] = "; ".join(description_parts)
            when = item.get("timeDateTime") or item.get("time")
            if when:
                normalized = self._normalize_datetime(when)
                if normalized:
                    entry["timeDateTime"] = normalized
            if entry:
                processing.append(entry)
        return processing

    # ------------------------------------------------------------------
    # Coverage
    # ------------------------------------------------------------------

    def _create_coverage(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create Coverage resource with beneficiary and payor"""
        beneficiary = self._patient_reference(data)
        coverage: dict[str, Any] = {
            "resourceType": "Coverage",
            "id": self._resource_id("coverage", data),
            "status": self._normalize_coverage_status(data.get("status")),
            "beneficiary": beneficiary,
            "payor": self._coverage_payors(data),
        }

        identifiers: list[dict[str, Any]] = []
        if "identifier" in data:
            identifiers.extend(
                self._coerce_identifiers(data["identifier"], LOCAL_COVERAGE_ID_SYSTEM)
            )
        policy_number = data.get("policy_number") or data.get("policyNumber")
        if policy_number:
            identifiers.append(
                {
                    "use": "official",
                    "system": LOCAL_COVERAGE_ID_SYSTEM,
                    "value": str(policy_number),
                }
            )
        if identifiers:
            coverage["identifier"] = identifiers

        coverage_type = self._coverage_type(data)
        if coverage_type:
            coverage["type"] = coverage_type

        subscriber_id = (
            data.get("subscriber_id") or data.get("subscriberId") or data.get("member_id")
            or data.get("memberId")
        )  # fmt: skip
        if subscriber_id:
            coverage["subscriberId"] = str(subscriber_id)

        subscriber = data.get("subscriber") or data.get("subscriber_ref")
        if subscriber:
            coverage["subscriber"] = {"reference": self._typed_reference(subscriber, "Patient")}
        elif subscriber_id or data.get("relationship"):
            relationship = self._key(str(data.get("relationship") or "self"))
            if relationship == "self":
                coverage["subscriber"] = dict(beneficiary)

        relationship = data.get("relationship")
        if relationship:
            key = self._key(str(relationship))
            if key in self.SUBSCRIBER_RELATIONSHIPS:
                coverage["relationship"] = self.create_codeable_concept(
                    SUBSCRIBER_RELATIONSHIP_SYSTEM, key, key.capitalize()
                )
            else:
                coverage["relationship"] = {"text": self._humanize(str(relationship))}

        if data.get("dependent"):
            coverage["dependent"] = str(data["dependent"])

        period = self._period(data.get("period") or data.get("effective_period"))
        if period:
            coverage["period"] = period

        classes = self._coverage_classes(data)
        if classes:
            coverage["class"] = classes

        if data.get("network"):
            coverage["network"] = str(data["network"])

        order = data.get("order")
        if isinstance(order, int) and order > 0:
            coverage["order"] = order

        return coverage

    def _normalize_coverage_status(self, status: Any) -> str:
        if isinstance(status, str):
            normalized = status.strip().lower().replace("_", "-")
            if normalized in self.COVERAGE_STATUSES:
                return normalized
            if normalized in ("inactive", "terminated", "expired"):
                return "cancelled"
        return "active"

    def _coverage_type(self, data: dict[str, Any]) -> dict[str, Any] | None:
        raw = data.get("coverage_type") or data.get("type")
        if isinstance(raw, dict):
            return raw if ("coding" in raw or "text" in raw) else None
        if not isinstance(raw, str) or not raw.strip():
            return None
        code = self.COVERAGE_TYPE_CODES.get(self._key(raw))
        if code:
            return self.create_codeable_concept(
                V3_ACT_CODE_SYSTEM, code[0], code[1], text=raw.strip()
            )
        return {"text": raw.strip()}

    def _coverage_payors(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        raw = data.get("payor") or data.get("payer") or data.get("insurer") or data.get("insurance")
        payors = [self._organization_reference(item) for item in self._as_list(raw)]
        payors = [p for p in payors if p]
        if not payors:
            payors.append({"display": "Unknown payor"})
        return payors

    def _coverage_classes(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        classes: list[dict[str, Any]] = []

        def add(class_type: str, value: Any, name: Any = None):
            if value is None or str(value).strip() == "":
                return
            entry = {
                "type": self.create_codeable_concept(
                    COVERAGE_CLASS_SYSTEM, class_type, class_type.capitalize()
                ),
                "value": str(value),
            }
            if name:
                entry["name"] = str(name)
            classes.append(entry)

        add("group", data.get("group_number") or data.get("group_id"), data.get("group_name"))
        add("plan", data.get("plan_id") or data.get("plan"), data.get("plan_name"))
        add("class", data.get("plan_class"))

        for item in self._as_list(data.get("class") or data.get("classes")):
            if not isinstance(item, dict):
                continue
            class_type = item.get("type")
            if isinstance(class_type, dict):
                entry = {"type": class_type, "value": str(item.get("value", ""))}
                if item.get("name"):
                    entry["name"] = str(item["name"])
                if entry["value"]:
                    classes.append(entry)
            elif isinstance(class_type, str) and self._key(class_type) in self.COVERAGE_CLASS_TYPES:
                add(self._key(class_type), item.get("value"), item.get("name"))

        return classes

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _resource_id(self, prefix: str, data: dict[str, Any]) -> str:
        """Use a caller-supplied valid id, otherwise generate one"""
        supplied = data.get("id")
        if isinstance(supplied, str) and _FHIR_ID_PATTERN.match(supplied):
            return supplied
        return f"{prefix}-{uuid.uuid4()}"

    def _patient_reference(self, data: dict[str, Any]) -> dict[str, Any]:
        """Build the Patient reference from patient_ref/patient_id/patient/subject"""
        for key in (
            "patient_ref",
            "patient_id",
            "patient",
            "subject",
            "subject_ref",
            "beneficiary",
        ):
            value = data.get(key)
            if isinstance(value, dict):
                value = value.get("reference") or value.get("id")
            if isinstance(value, str) and value.strip():
                return {"reference": self._typed_reference(value, "Patient")}
        return {"reference": f"Patient/unknown-{uuid.uuid4().hex[:8]}"}

    def _typed_reference(self, value: str, default_type: str) -> str:
        """Normalize 'Type/id' or bare id into a valid relative FHIR reference"""
        value = value.strip()
        if "/" in value:
            resource_type, _, resource_id = value.rpartition("/")
            resource_type = resource_type.rsplit("/", 1)[-1]
            if not re.match(r"^[A-Z][A-Za-z0-9]*$", resource_type):
                resource_type = default_type
        else:
            resource_type, resource_id = default_type, value
        resource_id = _INVALID_ID_CHARS.sub("-", resource_id).strip("-")[:64]
        if not resource_id:
            resource_id = f"unknown-{uuid.uuid4().hex[:8]}"
        return f"{resource_type}/{resource_id}"

    def _organization_reference(self, item: Any) -> dict[str, Any] | None:
        """Reference to a payor/issuer Organization from a dict, string or reference"""
        if isinstance(item, dict):
            if item.get("reference"):
                ref: dict[str, Any] = {
                    "reference": self._typed_reference(str(item["reference"]), "Organization")
                }
                if item.get("display"):
                    ref["display"] = str(item["display"])
                return ref
            org_id = item.get("id")
            name = item.get("name") or item.get("display")
            ref = {}
            if isinstance(org_id, str) and org_id.strip():
                ref["reference"] = self._typed_reference(org_id, "Organization")
            if isinstance(name, str) and name.strip():
                ref["display"] = name.strip()
            return ref or None
        if isinstance(item, str) and item.strip():
            if "/" in item:
                return {"reference": self._typed_reference(item, "Organization")}
            return {"display": item.strip()}
        return None

    def _coerce_identifiers(self, raw: Any, default_system: str) -> list[dict[str, Any]]:
        identifiers: list[dict[str, Any]] = []
        for item in self._as_list(raw):
            if isinstance(item, dict):
                value = item.get("value")
                if value is None or str(value).strip() == "":
                    continue
                identifier: dict[str, Any] = {"value": str(value)}
                for key in ("use", "system", "type", "period"):
                    if item.get(key):
                        identifier[key] = item[key]
                identifiers.append(identifier)
            elif isinstance(item, str) and item.strip():
                identifiers.append({"system": default_system, "value": item.strip()})
            elif isinstance(item, int):
                identifiers.append({"system": default_system, "value": str(item)})
        return identifiers

    def _process_telecom(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        telecom: list[dict[str, Any]] = []
        contact = data.get("contact_info") if isinstance(data.get("contact_info"), dict) else {}

        for key, system, use in (
            ("phone", "phone", "work"),
            ("work_phone", "phone", "work"),
            ("mobile_phone", "phone", "mobile"),
            ("fax", "fax", "work"),
            ("email", "email", "work"),
            ("pager", "pager", "work"),
        ):
            value = data.get(key) or contact.get(key)
            if value and str(value).strip():
                telecom.append({"system": system, "value": str(value).strip(), "use": use})

        for item in self._as_list(data.get("telecom")):
            if not isinstance(item, dict) or not item.get("value"):
                continue
            system = str(item.get("system", "other")).lower()
            entry = {
                "system": system if system in _CONTACT_POINT_SYSTEMS else "other",
                "value": str(item["value"]),
            }
            use = str(item.get("use", "")).lower()
            if use in _CONTACT_POINT_USES:
                entry["use"] = use
            telecom.append(entry)

        return telecom

    def _annotations(self, raw: Any) -> list[dict[str, Any]]:
        notes: list[dict[str, Any]] = []
        for item in self._as_list(raw):
            if isinstance(item, dict) and item.get("text"):
                notes.append({"text": str(item["text"])})
            elif isinstance(item, str) and item.strip():
                notes.append({"text": item.strip()})
        return notes

    def _period(self, raw: Any) -> dict[str, Any] | None:
        if not isinstance(raw, dict):
            return None
        period: dict[str, Any] = {}
        for key in ("start", "end"):
            if raw.get(key):
                normalized = self._normalize_datetime(raw[key])
                if normalized:
                    period[key] = normalized
        return period or None

    def _normalize_datetime(self, value: Any) -> str | None:
        """Normalize to a FHIR date/dateTime string (times carry a timezone)"""
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return value.isoformat(timespec="seconds").replace("+00:00", "Z")
        if isinstance(value, date):
            return value.isoformat()
        if not isinstance(value, str) or not value.strip():
            return None

        text = value.strip()
        if _FHIR_DATETIME_PATTERN.match(text):
            return text
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%B %d, %Y", "%b %d, %Y"):
                try:
                    return datetime.strptime(text, fmt).date().isoformat()
                except ValueError:
                    continue
            self.logger.warning("Unparseable date value dropped from resource")
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.isoformat(timespec="seconds").replace("+00:00", "Z")

    @staticmethod
    def _normalize_gender(gender: Any) -> str:
        mapping = {"m": "male", "male": "male", "f": "female", "female": "female", "other": "other"}
        return mapping.get(str(gender).strip().lower(), "unknown")

    @staticmethod
    def _as_list(raw: Any) -> list[Any]:
        if raw is None:
            return []
        if isinstance(raw, (list, tuple, set)):
            return list(raw)
        return [raw]

    @staticmethod
    def _key(value: str) -> str:
        """Normalize a free-text key: 'Left Antecubital-Fossa' -> 'left_antecubital_fossa'"""
        return re.sub(r"[\s\-]+", "_", value.strip().lower())

    @staticmethod
    def _humanize(value: str) -> str:
        """'left_antecubital_fossa' -> 'Left antecubital fossa'"""
        text = re.sub(r"[_]+", " ", value.strip())
        return text[:1].upper() + text[1:] if text else text
