"""
FHIR Device Resource Factory
Specialized factory for device-related FHIR resources with enhanced functionality
"""

from typing import Dict, Any, List, Optional, Union
import logging
import re
import time
import uuid
from datetime import datetime

from .base import BaseResourceFactory

logger = logging.getLogger(__name__)


class DeviceResourceFactory(BaseResourceFactory):
    """
    Factory for device-related FHIR resources.

    Handles Device, DeviceUseStatement, DeviceMetric resources
    with advanced features:
    - Device type coding with SNOMED CT
    - Identifier generation and validation
    - Usage tracking and status management
    - Patient/device relationship management
    """

    SUPPORTED_RESOURCES = {
        'Device', 'DeviceUseStatement', 'DeviceMetric'
    }

    def __init__(self, validators=None, coders=None, reference_manager=None):
        """Initialize device factory with shared components"""
        super().__init__(validators, coders, reference_manager)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("DeviceResourceFactory initialized with specialized device handling")

    def supports(self, resource_type: str) -> bool:
        """Check if factory supports the resource type"""
        return resource_type in self.SUPPORTED_RESOURCES

    def _get_required_fields(self, resource_type: str) -> List[str]:
        """Get required fields for each resource type"""
        if resource_type == 'Device':
            return ['name']  # Device name is required
        elif resource_type == 'DeviceUseStatement':
            return ['patient_id', 'device_ref']  # Patient and device references required
        elif resource_type == 'DeviceMetric':
            return ['device_ref', 'type']  # Device reference and metric type required
        return []

    def _create_resource(self, resource_type: str, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create device-related resource based on type"""
        self.logger.debug(f"[{request_id}] Creating {resource_type} resource with DeviceResourceFactory")

        start_time = time.time()

        if resource_type == 'Device':
            resource = self._create_device(data, request_id)
        elif resource_type == 'DeviceUseStatement':
            resource = self._create_device_use_statement(data, request_id)
        elif resource_type == 'DeviceMetric':
            resource = self._create_device_metric(data, request_id)
        else:
            raise ValueError(f"Unsupported resource type: {resource_type}")

        duration_ms = (time.time() - start_time) * 1000
        self.logger.debug(f"[{request_id}] Created {resource_type} in {duration_ms:.2f}ms")

        return resource

    def _create_device(self, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a Device resource for medical equipment"""
        device_id = self._generate_resource_id('device')

        # Get device name (required)
        device_name = data.get('name', data.get('device_name', 'Medical Device'))

        # Create base device structure
        device = {
            'resourceType': 'Device',
            'id': device_id,
            'status': data.get('status', 'active')
        }

        # Add device name
        device['deviceName'] = [{
            'name': device_name,
            'type': 'user-friendly-name'
        }]

        # Add identifier if provided
        if data.get('identifier'):
            device['identifier'] = [{
                'use': 'official',
                'value': str(data['identifier'])
            }]

        # Add device type with SNOMED CT coding
        device_type = data.get('type', data.get('device_type'))

        # If no explicit type, try to infer from name
        if not device_type:
            device_type = self._infer_device_type_from_name(device_name)

        if device_type:
            device['type'] = self._create_device_type_coding(device_type)

        # Add manufacturer
        if data.get('manufacturer'):
            device['manufacturer'] = str(data['manufacturer'])

        # Add model number
        if data.get('model', data.get('model_number')):
            device['modelNumber'] = str(data.get('model', data.get('model_number')))

        # Add text narrative
        device['text'] = {
            'status': 'generated',
            'div': f'<div xmlns="http://www.w3.org/1999/xhtml">{device_name} ({device["status"]})</div>'
        }

        return device

    def _create_device_use_statement(self, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a DeviceUseStatement resource tracking device usage"""
        statement_id = self._generate_resource_id('device-use')

        # Create base structure
        statement = {
            'resourceType': 'DeviceUseStatement',
            'id': statement_id,
            'status': data.get('status', 'active')
        }

        # Add patient reference (required)
        patient_ref = data.get('patient_id', data.get('patient_ref'))
        if patient_ref:
            # Ensure proper FHIR reference format
            if not patient_ref.startswith('Patient/'):
                patient_ref = f'Patient/{patient_ref}'
            statement['subject'] = {'reference': patient_ref}

        # Add device reference (required)
        device_ref = data.get('device_ref', data.get('device_id'))
        if device_ref:
            # Ensure proper FHIR reference format
            if not device_ref.startswith('Device/'):
                device_ref = f'Device/{device_ref}'
            statement['device'] = {'reference': device_ref}

        # Add timing information
        if data.get('recorded_on', data.get('timing')):
            statement['recordedOn'] = self._format_datetime(
                data.get('recorded_on', data.get('timing'))
            )

        # Add reason for use
        if data.get('reason', data.get('indication')):
            statement['reasonCode'] = [{
                'text': str(data.get('reason', data.get('indication')))
            }]

        # Add usage period
        if data.get('timing_period'):
            period = data['timing_period']
            statement['timingPeriod'] = {}
            if period.get('start'):
                statement['timingPeriod']['start'] = self._format_datetime(period['start'])
            if period.get('end'):
                statement['timingPeriod']['end'] = self._format_datetime(period['end'])

        # Add text narrative
        subject_text = statement.get('subject', {}).get('reference', 'patient')
        device_text = statement.get('device', {}).get('reference', 'device')
        statement['text'] = {
            'status': 'generated',
            'div': f'<div xmlns="http://www.w3.org/1999/xhtml">{subject_text} uses {device_text}</div>'
        }

        return statement

    def _create_device_metric(self, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a DeviceMetric resource for device measurements"""
        metric_id = self._generate_resource_id('device-metric')

        # Create base structure
        metric = {
            'resourceType': 'DeviceMetric',
            'id': metric_id,
            'category': data.get('category', 'measurement'),
            'operationalStatus': data.get('operational_status', 'on')
        }

        # Add device reference (required)
        device_ref = data.get('device_ref', data.get('device_id'))
        if device_ref:
            if not device_ref.startswith('Device/'):
                device_ref = f'Device/{device_ref}'
            metric['source'] = {'reference': device_ref}

        # Add metric type (required)
        metric_type = data.get('type', data.get('metric_type'))
        if metric_type:
            metric['type'] = self._create_metric_type_coding(metric_type)

        # Add unit if provided
        if data.get('unit'):
            metric['unit'] = self.create_codeable_concept('UCUM', data['unit'], data.get('unit_display', data['unit']))

        return metric

    def _create_device_type_coding(self, device_type: str) -> Dict[str, Any]:
        """Create device type coding with SNOMED CT"""
        # Common device type mappings to SNOMED CT codes
        device_type_mappings = {
            'iv pump': {'code': '257268009', 'display': 'Intravenous infusion pump'},
            'infusion pump': {'code': '257268009', 'display': 'Intravenous infusion pump'},
            'pca pump': {'code': '182707008', 'display': 'Patient controlled analgesia pump'},
            'syringe pump': {'code': '303727007', 'display': 'Syringe pump'},
            'ventilator': {'code': '40617009', 'display': 'Artificial respiration'},
            'defibrillator': {'code': '251832004', 'display': 'Defibrillator'},
            'monitor': {'code': '264957007', 'display': 'Patient monitoring device'}
        }

        device_type_lower = device_type.lower()
        mapping = device_type_mappings.get(device_type_lower)

        if mapping:
            return self.create_codeable_concept('SNOMED-CT', mapping['code'], mapping['display'])
        else:
            # Fallback to text-only coding
            return {'text': device_type}

    def _create_metric_type_coding(self, metric_type: str) -> Dict[str, Any]:
        """Create metric type coding with LOINC"""
        # Common metric type mappings to LOINC codes
        metric_type_mappings = {
            'heart_rate': {'code': '8867-4', 'display': 'Heart rate'},
            'blood_pressure': {'code': '85354-9', 'display': 'Blood pressure panel'},
            'temperature': {'code': '8310-5', 'display': 'Body temperature'},
            'oxygen_saturation': {'code': '2708-6', 'display': 'Oxygen saturation'},
            'flow_rate': {'code': '76282-3', 'display': 'Infusion rate'}
        }

        metric_type_lower = metric_type.lower()
        mapping = metric_type_mappings.get(metric_type_lower)

        if mapping:
            return self.create_codeable_concept('LOINC', mapping['code'], mapping['display'])
        else:
            return {'text': metric_type}

    def _format_datetime(self, dt_input: Union[str, datetime]) -> str:
        """Format datetime for FHIR instant format"""
        if isinstance(dt_input, str):
            return dt_input
        elif isinstance(dt_input, datetime):
            return dt_input.isoformat() + 'Z'
        else:
            return datetime.utcnow().isoformat() + 'Z'

    def _infer_device_type_from_name(self, device_name: str) -> Optional[str]:
        """Infer device type from device name"""
        name_lower = device_name.lower()

        # Check for common device types in name
        if any(term in name_lower for term in ['iv pump', 'infusion pump']):
            return 'iv pump'
        elif 'pca pump' in name_lower:
            return 'pca pump'
        elif 'syringe pump' in name_lower:
            return 'syringe pump'
        elif any(term in name_lower for term in ['ventilator', 'vent']):
            return 'ventilator'
        elif any(term in name_lower for term in ['defibrillator', 'defib']):
            return 'defibrillator'
        elif any(term in name_lower for term in ['monitor', 'monitoring']):
            return 'monitor'

        return None

    def _generate_resource_id(self, prefix: str) -> str:
        """Generate unique resource ID with prefix"""
        unique_id = str(uuid.uuid4())[:8]
        return f"{prefix}-{unique_id}"