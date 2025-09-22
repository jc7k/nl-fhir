import sys
sys.path.append('src')

from nl_fhir.services.conversion import ConversionService


def test_extract_vitals_from_text_bp_hr_rr_temp_spo2():
    svc = ConversionService()

    text = (
        "Vitals: BP 150/95, HR 105, RR 22, Temp 38.2 C, SpO2 90%"
    )
    vitals = svc._extract_vitals_from_text(text)

    codes = {v.get('code', {}).get('code'): v for v in vitals}

    # BP systolic and diastolic
    assert '8480-6' in codes and '8462-4' in codes
    assert codes['8480-6']['value'] == 150 and codes['8480-6']['unit'] == 'mmHg'
    assert codes['8462-4']['value'] == 95 and codes['8462-4']['unit'] == 'mmHg'

    # HR
    assert '8867-4' in codes and codes['8867-4']['unit'] == 'beats/min'

    # RR
    assert '9279-1' in codes and codes['9279-1']['unit'] == 'breaths/min'

    # Temp
    assert '8310-5' in codes
    assert codes['8310-5']['unit'] in ('C', 'F')

    # SpO2
    assert '59408-5' in codes and codes['59408-5']['unit'] == '%'


def test_extract_weight_from_text_via_regex_pipeline_path():
    svc = ConversionService()
    # Leverage internal vitals extractor for unit tests; weight extraction happens in convert_advanced
    # Here we ensure helper remains stable and does not raise
    vitals = svc._extract_vitals_from_text("Weight 70kg; BP 120/80")
    # BP present; weight is handled elsewhere
    assert any(v.get('code', {}).get('code') in ('8480-6', '8462-4') for v in vitals)
