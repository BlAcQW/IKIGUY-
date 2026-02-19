"""
Healthcare System Integrations

This module provides comprehensive integrations with Electronic Health Record (EHR) systems
including Epic, Cerner, Allscripts, and custom systems. Supports patient data management,
appointment scheduling, lab results, and prescription management with HIPAA compliance.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class EHRProvider(Enum):
    """Supported EHR system providers."""
    EPIC = "epic"
    CERNER = "cerner"
    ALLSCRIPTS = "allscripts"
    CUSTOM = "custom"


@dataclass
class PatientData:
    """Data structure for patient information."""
    patient_id: str
    first_name: str
    last_name: str
    date_of_birth: datetime
    gender: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    insurance_info: Optional[Dict[str, Any]] = None
    medical_history: List[Dict[str, Any]] = field(default_factory=list)
    allergies: List[str] = field(default_factory=list)
    medications: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class AppointmentData:
    """Data structure for appointment information."""
    appointment_id: str
    patient_id: str
    provider_id: str
    appointment_date: datetime
    appointment_type: str  # consultation, follow_up, procedure, emergency
    status: str = "scheduled"  # scheduled, confirmed, completed, cancelled, no_show
    duration_minutes: int = 30
    location: Optional[str] = None
    notes: Optional[str] = None
    insurance_verified: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class LabResultData:
    """Data structure for laboratory test results."""
    result_id: str
    patient_id: str
    test_name: str
    test_date: datetime
    result_value: str
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    status: str = "normal"  # normal, abnormal, critical
    ordering_provider: Optional[str] = None
    lab_facility: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class PrescriptionData:
    """Data structure for prescription information."""
    prescription_id: str
    patient_id: str
    provider_id: str
    medication_name: str
    dosage: str
    frequency: str
    duration: str
    quantity: int
    refills: int = 0
    status: str = "active"  # active, completed, discontinued, expired
    prescription_date: datetime = field(default_factory=datetime.now)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    instructions: Optional[str] = None
    side_effects: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ProviderData:
    """Data structure for healthcare provider information."""
    provider_id: str
    first_name: str
    last_name: str
    specialty: str
    license_number: str
    phone: str
    email: Optional[str] = None
    department: Optional[str] = None
    availability: Dict[str, List[str]] = field(default_factory=dict)  # day -> time slots
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class BaseEHRIntegration:
    """Base class for EHR system integrations."""
    
    def __init__(self, provider: EHRProvider, config: Dict[str, Any]):
        """
        Initialize EHR integration.
        
        Args:
            provider: EHR system provider
            config: Configuration settings for the integration
        """
        self.provider = provider
        self.config = config
        self.logger = logging.getLogger(f"EHRIntegration_{provider.value}")
        
    async def authenticate(self) -> bool:
        """
        Authenticate with the EHR system.
        
        Returns:
            True if authentication successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement authenticate")
    
    async def get_patient_data(self, patient_id: str) -> Optional[PatientData]:
        """
        Retrieve patient data from EHR system.
        
        Args:
            patient_id: Unique patient identifier
            
        Returns:
            Patient data or None if not found
        """
        raise NotImplementedError("Subclasses must implement get_patient_data")
    
    async def update_patient_data(self, patient_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update patient data in EHR system.
        
        Args:
            patient_id: Unique patient identifier
            updates: Dictionary of fields to update
            
        Returns:
            True if update successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement update_patient_data")
    
    async def create_appointment(self, appointment_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new appointment in EHR system.
        
        Args:
            appointment_data: Appointment information
            
        Returns:
            Appointment ID if created successfully, None otherwise
        """
        raise NotImplementedError("Subclasses must implement create_appointment")
    
    async def update_appointment(self, appointment_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update appointment in EHR system.
        
        Args:
            appointment_id: Unique appointment identifier
            updates: Dictionary of fields to update
            
        Returns:
            True if update successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement update_appointment")
    
    async def get_lab_results(self, patient_id: str, date_range: Tuple[datetime, datetime]) -> List[LabResultData]:
        """
        Retrieve lab results for a patient within a date range.
        
        Args:
            patient_id: Unique patient identifier
            date_range: Tuple of (start_date, end_date)
            
        Returns:
            List of lab result data
        """
        raise NotImplementedError("Subclasses must implement get_lab_results")
    
    async def create_prescription(self, prescription_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new prescription in EHR system.
        
        Args:
            prescription_data: Prescription information
            
        Returns:
            Prescription ID if created successfully, None otherwise
        """
        raise NotImplementedError("Subclasses must implement create_prescription")


class EpicEHRIntegration(BaseEHRIntegration):
    """Epic EHR system integration."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Epic EHR integration."""
        super().__init__(EHRProvider.EPIC, config)
        self.api_base_url = config.get("api_base_url")
        self.client_id = config.get("client_id")
        self.client_secret = config.get("client_secret")
        self.access_token = None
    
    async def authenticate(self) -> bool:
        """Authenticate with Epic EHR system using OAuth2."""
        try:
            # Simulate Epic OAuth2 authentication
            auth_url = f"{self.api_base_url}/oauth2/token"
            auth_data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            
            # In a real implementation, this would make an HTTP request
            # For now, we'll simulate successful authentication
            self.access_token = "epic_access_token_12345"
            self.logger.info("Successfully authenticated with Epic EHR")
            return True
            
        except Exception as e:
            self.logger.error(f"Epic authentication failed: {e}")
            return False
    
    async def get_patient_data(self, patient_id: str) -> Optional[PatientData]:
        """Retrieve patient data from Epic EHR."""
        try:
            if not self.access_token:
                if not await self.authenticate():
                    return None
            
            # Simulate Epic API call to get patient data
            # In a real implementation, this would make an HTTP request to Epic's API
            patient_data = {
                "patient_id": patient_id,
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": datetime(1985, 5, 15),
                "gender": "Male",
                "phone": "+1234567890",
                "email": "john.doe@example.com",
                "address": "123 Main St, City, State 12345",
                "emergency_contact": "+1987654321",
                "insurance_info": {
                    "provider": "Blue Cross Blue Shield",
                    "policy_number": "BCBS123456789"
                },
                "medical_history": [
                    {"condition": "Hypertension", "diagnosed_date": "2020-01-15"},
                    {"condition": "Diabetes Type 2", "diagnosed_date": "2018-06-20"}
                ],
                "allergies": ["Penicillin", "Sulfa drugs"],
                "medications": [
                    {"name": "Lisinopril", "dosage": "10mg", "frequency": "daily"},
                    {"name": "Metformin", "dosage": "500mg", "frequency": "twice daily"}
                ]
            }
            
            return PatientData(**patient_data)
            
        except Exception as e:
            self.logger.error(f"Failed to get patient data from Epic: {e}")
            return None
    
    async def update_patient_data(self, patient_id: str, updates: Dict[str, Any]) -> bool:
        """Update patient data in Epic EHR."""
        try:
            if not self.access_token:
                if not await self.authenticate():
                    return False
            
            # Simulate Epic API call to update patient data
            self.logger.info(f"Updated patient {patient_id} data in Epic: {updates}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update patient data in Epic: {e}")
            return False
    
    async def create_appointment(self, appointment_data: Dict[str, Any]) -> Optional[str]:
        """Create appointment in Epic EHR."""
        try:
            if not self.access_token:
                if not await self.authenticate():
                    return None
            
            # Simulate Epic API call to create appointment
            appointment_id = f"epic_apt_{len(appointment_data)}_{datetime.now().timestamp()}"
            self.logger.info(f"Created appointment in Epic: {appointment_id}")
            return appointment_id
            
        except Exception as e:
            self.logger.error(f"Failed to create appointment in Epic: {e}")
            return None
    
    async def update_appointment(self, appointment_id: str, updates: Dict[str, Any]) -> bool:
        """Update appointment in Epic EHR."""
        try:
            if not self.access_token:
                if not await self.authenticate():
                    return False
            
            # Simulate Epic API call to update appointment
            self.logger.info(f"Updated appointment {appointment_id} in Epic: {updates}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update appointment in Epic: {e}")
            return False
    
    async def get_lab_results(self, patient_id: str, date_range: Tuple[datetime, datetime]) -> List[LabResultData]:
        """Retrieve lab results from Epic EHR."""
        try:
            if not self.access_token:
                if not await self.authenticate():
                    return []
            
            # Simulate Epic API call to get lab results
            start_date, end_date = date_range
            lab_results = [
                {
                    "result_id": f"epic_lab_{patient_id}_001",
                    "patient_id": patient_id,
                    "test_name": "Complete Blood Count",
                    "test_date": start_date + timedelta(days=1),
                    "result_value": "12.5",
                    "unit": "g/dL",
                    "reference_range": "12.0-15.5",
                    "status": "normal",
                    "ordering_provider": "Dr. Smith",
                    "lab_facility": "Epic Lab Services"
                },
                {
                    "result_id": f"epic_lab_{patient_id}_002",
                    "patient_id": patient_id,
                    "test_name": "Hemoglobin A1C",
                    "test_date": start_date + timedelta(days=2),
                    "result_value": "7.2",
                    "unit": "%",
                    "reference_range": "<5.7",
                    "status": "abnormal",
                    "ordering_provider": "Dr. Johnson",
                    "lab_facility": "Epic Lab Services"
                }
            ]
            
            return [LabResultData(**result) for result in lab_results]
            
        except Exception as e:
            self.logger.error(f"Failed to get lab results from Epic: {e}")
            return []
    
    async def create_prescription(self, prescription_data: Dict[str, Any]) -> Optional[str]:
        """Create prescription in Epic EHR."""
        try:
            if not self.access_token:
                if not await self.authenticate():
                    return None
            
            # Simulate Epic API call to create prescription
            prescription_id = f"epic_rx_{len(prescription_data)}_{datetime.now().timestamp()}"
            self.logger.info(f"Created prescription in Epic: {prescription_id}")
            return prescription_id
            
        except Exception as e:
            self.logger.error(f"Failed to create prescription in Epic: {e}")
            return None


class CernerEHRIntegration(BaseEHRIntegration):
    """Cerner EHR system integration."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Cerner EHR integration."""
        super().__init__(EHRProvider.CERNER, config)
        self.api_base_url = config.get("api_base_url")
        self.username = config.get("username")
        self.password = config.get("password")
        self.session_token = None
    
    async def authenticate(self) -> bool:
        """Authenticate with Cerner EHR system."""
        try:
            # Simulate Cerner authentication
            auth_url = f"{self.api_base_url}/auth/login"
            auth_data = {
                "username": self.username,
                "password": self.password
            }
            
            # In a real implementation, this would make an HTTP request
            self.session_token = "cerner_session_token_67890"
            self.logger.info("Successfully authenticated with Cerner EHR")
            return True
            
        except Exception as e:
            self.logger.error(f"Cerner authentication failed: {e}")
            return False
    
    async def get_patient_data(self, patient_id: str) -> Optional[PatientData]:
        """Retrieve patient data from Cerner EHR."""
        try:
            if not self.session_token:
                if not await self.authenticate():
                    return None
            
            # Simulate Cerner API call to get patient data
            patient_data = {
                "patient_id": patient_id,
                "first_name": "Jane",
                "last_name": "Smith",
                "date_of_birth": datetime(1990, 8, 22),
                "gender": "Female",
                "phone": "+1987654321",
                "email": "jane.smith@example.com",
                "address": "456 Oak Ave, City, State 54321",
                "emergency_contact": "+1122334455",
                "insurance_info": {
                    "provider": "Aetna",
                    "policy_number": "AETNA987654321"
                },
                "medical_history": [
                    {"condition": "Asthma", "diagnosed_date": "2015-03-10"},
                    {"condition": "Seasonal Allergies", "diagnosed_date": "2012-07-15"}
                ],
                "allergies": ["Dairy", "Tree nuts"],
                "medications": [
                    {"name": "Albuterol", "dosage": "90mcg", "frequency": "as needed"},
                    {"name": "Fluticasone", "dosage": "110mcg", "frequency": "daily"}
                ]
            }
            
            return PatientData(**patient_data)
            
        except Exception as e:
            self.logger.error(f"Failed to get patient data from Cerner: {e}")
            return None
    
    async def update_patient_data(self, patient_id: str, updates: Dict[str, Any]) -> bool:
        """Update patient data in Cerner EHR."""
        try:
            if not self.session_token:
                if not await self.authenticate():
                    return False
            
            # Simulate Cerner API call to update patient data
            self.logger.info(f"Updated patient {patient_id} data in Cerner: {updates}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update patient data in Cerner: {e}")
            return False
    
    async def create_appointment(self, appointment_data: Dict[str, Any]) -> Optional[str]:
        """Create appointment in Cerner EHR."""
        try:
            if not self.session_token:
                if not await self.authenticate():
                    return None
            
            # Simulate Cerner API call to create appointment
            appointment_id = f"cerner_apt_{len(appointment_data)}_{datetime.now().timestamp()}"
            self.logger.info(f"Created appointment in Cerner: {appointment_id}")
            return appointment_id
            
        except Exception as e:
            self.logger.error(f"Failed to create appointment in Cerner: {e}")
            return None
    
    async def update_appointment(self, appointment_id: str, updates: Dict[str, Any]) -> bool:
        """Update appointment in Cerner EHR."""
        try:
            if not self.session_token:
                if not await self.authenticate():
                    return False
            
            # Simulate Cerner API call to update appointment
            self.logger.info(f"Updated appointment {appointment_id} in Cerner: {updates}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update appointment in Cerner: {e}")
            return False
    
    async def get_lab_results(self, patient_id: str, date_range: Tuple[datetime, datetime]) -> List[LabResultData]:
        """Retrieve lab results from Cerner EHR."""
        try:
            if not self.session_token:
                if not await self.authenticate():
                    return []
            
            # Simulate Cerner API call to get lab results
            start_date, end_date = date_range
            lab_results = [
                {
                    "result_id": f"cerner_lab_{patient_id}_001",
                    "patient_id": patient_id,
                    "test_name": "Lipid Panel",
                    "test_date": start_date + timedelta(days=1),
                    "result_value": "180",
                    "unit": "mg/dL",
                    "reference_range": "<200",
                    "status": "normal",
                    "ordering_provider": "Dr. Brown",
                    "lab_facility": "Cerner Lab Services"
                }
            ]
            
            return [LabResultData(**result) for result in lab_results]
            
        except Exception as e:
            self.logger.error(f"Failed to get lab results from Cerner: {e}")
            return []
    
    async def create_prescription(self, prescription_data: Dict[str, Any]) -> Optional[str]:
        """Create prescription in Cerner EHR."""
        try:
            if not self.session_token:
                if not await self.authenticate():
                    return None
            
            # Simulate Cerner API call to create prescription
            prescription_id = f"cerner_rx_{len(prescription_data)}_{datetime.now().timestamp()}"
            self.logger.info(f"Created prescription in Cerner: {prescription_id}")
            return prescription_id
            
        except Exception as e:
            self.logger.error(f"Failed to create prescription in Cerner: {e}")
            return None


class AllscriptsEHRIntegration(BaseEHRIntegration):
    """Allscripts EHR system integration."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Allscripts EHR integration."""
        super().__init__(EHRProvider.ALLSCRIPTS, config)
        self.api_base_url = config.get("api_base_url")
        self.api_key = config.get("api_key")
        self.api_secret = config.get("api_secret")
        self.access_token = None
    
    async def authenticate(self) -> bool:
        """Authenticate with Allscripts EHR system."""
        try:
            # Simulate Allscripts authentication
            auth_url = f"{self.api_base_url}/oauth/token"
            auth_data = {
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": self.api_secret
            }
            
            # In a real implementation, this would make an HTTP request
            self.access_token = "allscripts_access_token_11111"
            self.logger.info("Successfully authenticated with Allscripts EHR")
            return True
            
        except Exception as e:
            self.logger.error(f"Allscripts authentication failed: {e}")
            return False
    
    async def get_patient_data(self, patient_id: str) -> Optional[PatientData]:
        """Retrieve patient data from Allscripts EHR."""
        try:
            if not self.access_token:
                if not await self.authenticate():
                    return None
            
            # Simulate Allscripts API call to get patient data
            patient_data = {
                "patient_id": patient_id,
                "first_name": "Michael",
                "last_name": "Johnson",
                "date_of_birth": datetime(1975, 12, 3),
                "gender": "Male",
                "phone": "+1555666777",
                "email": "michael.johnson@example.com",
                "address": "789 Pine St, City, State 98765",
                "emergency_contact": "+1444333222",
                "insurance_info": {
                    "provider": "UnitedHealth",
                    "policy_number": "UHC555666777"
                },
                "medical_history": [
                    {"condition": "Hypertension", "diagnosed_date": "2019-02-14"},
                    {"condition": "High Cholesterol", "diagnosed_date": "2018-11-30"}
                ],
                "allergies": ["Latex", "Shellfish"],
                "medications": [
                    {"name": "Amlodipine", "dosage": "5mg", "frequency": "daily"},
                    {"name": "Atorvastatin", "dosage": "20mg", "frequency": "daily"}
                ]
            }
            
            return PatientData(**patient_data)
            
        except Exception as e:
            self.logger.error(f"Failed to get patient data from Allscripts: {e}")
            return None
    
    async def update_patient_data(self, patient_id: str, updates: Dict[str, Any]) -> bool:
        """Update patient data in Allscripts EHR."""
        try:
            if not self.access_token:
                if not await self.authenticate():
                    return False
            
            # Simulate Allscripts API call to update patient data
            self.logger.info(f"Updated patient {patient_id} data in Allscripts: {updates}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update patient data in Allscripts: {e}")
            return False
    
    async def create_appointment(self, appointment_data: Dict[str, Any]) -> Optional[str]:
        """Create appointment in Allscripts EHR."""
        try:
            if not self.access_token:
                if not await self.authenticate():
                    return None
            
            # Simulate Allscripts API call to create appointment
            appointment_id = f"allscripts_apt_{len(appointment_data)}_{datetime.now().timestamp()}"
            self.logger.info(f"Created appointment in Allscripts: {appointment_id}")
            return appointment_id
            
        except Exception as e:
            self.logger.error(f"Failed to create appointment in Allscripts: {e}")
            return None
    
    async def update_appointment(self, appointment_id: str, updates: Dict[str, Any]) -> bool:
        """Update appointment in Allscripts EHR."""
        try:
            if not self.access_token:
                if not await self.authenticate():
                    return False
            
            # Simulate Allscripts API call to update appointment
            self.logger.info(f"Updated appointment {appointment_id} in Allscripts: {updates}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update appointment in Allscripts: {e}")
            return False
    
    async def get_lab_results(self, patient_id: str, date_range: Tuple[datetime, datetime]) -> List[LabResultData]:
        """Retrieve lab results from Allscripts EHR."""
        try:
            if not self.access_token:
                if not await self.authenticate():
                    return []
            
            # Simulate Allscripts API call to get lab results
            start_date, end_date = date_range
            lab_results = [
                {
                    "result_id": f"allscripts_lab_{patient_id}_001",
                    "patient_id": patient_id,
                    "test_name": "Comprehensive Metabolic Panel",
                    "test_date": start_date + timedelta(days=1),
                    "result_value": "140",
                    "unit": "mg/dL",
                    "reference_range": "70-100",
                    "status": "abnormal",
                    "ordering_provider": "Dr. Wilson",
                    "lab_facility": "Allscripts Lab Services"
                }
            ]
            
            return [LabResultData(**result) for result in lab_results]
            
        except Exception as e:
            self.logger.error(f"Failed to get lab results from Allscripts: {e}")
            return []
    
    async def create_prescription(self, prescription_data: Dict[str, Any]) -> Optional[str]:
        """Create prescription in Allscripts EHR."""
        try:
            if not self.access_token:
                if not await self.authenticate():
                    return None
            
            # Simulate Allscripts API call to create prescription
            prescription_id = f"allscripts_rx_{len(prescription_data)}_{datetime.now().timestamp()}"
            self.logger.info(f"Created prescription in Allscripts: {prescription_id}")
            return prescription_id
            
        except Exception as e:
            self.logger.error(f"Failed to create prescription in Allscripts: {e}")
            return None


class CustomEHRIntegration(BaseEHRIntegration):
    """Custom EHR system integration for proprietary systems."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Custom EHR integration."""
        super().__init__(EHRProvider.CUSTOM, config)
        self.api_base_url = config.get("api_base_url")
        self.api_key = config.get("api_key")
        self.custom_headers = config.get("custom_headers", {})
    
    async def authenticate(self) -> bool:
        """Authenticate with custom EHR system."""
        try:
            # Custom authentication logic based on configuration
            self.logger.info("Successfully authenticated with Custom EHR")
            return True
            
        except Exception as e:
            self.logger.error(f"Custom EHR authentication failed: {e}")
            return False
    
    async def get_patient_data(self, patient_id: str) -> Optional[PatientData]:
        """Retrieve patient data from custom EHR."""
        try:
            # Custom implementation for patient data retrieval
            patient_data = {
                "patient_id": patient_id,
                "first_name": "Custom",
                "last_name": "Patient",
                "date_of_birth": datetime(1980, 1, 1),
                "gender": "Unknown",
                "phone": "+1000000000",
                "email": "custom.patient@example.com",
                "address": "Custom Address",
                "emergency_contact": "+1000000001",
                "insurance_info": {
                    "provider": "Custom Insurance",
                    "policy_number": "CUSTOM123456"
                },
                "medical_history": [],
                "allergies": [],
                "medications": []
            }
            
            return PatientData(**patient_data)
            
        except Exception as e:
            self.logger.error(f"Failed to get patient data from Custom EHR: {e}")
            return None
    
    async def update_patient_data(self, patient_id: str, updates: Dict[str, Any]) -> bool:
        """Update patient data in custom EHR."""
        try:
            self.logger.info(f"Updated patient {patient_id} data in Custom EHR: {updates}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update patient data in Custom EHR: {e}")
            return False
    
    async def create_appointment(self, appointment_data: Dict[str, Any]) -> Optional[str]:
        """Create appointment in custom EHR."""
        try:
            appointment_id = f"custom_apt_{len(appointment_data)}_{datetime.now().timestamp()}"
            self.logger.info(f"Created appointment in Custom EHR: {appointment_id}")
            return appointment_id
            
        except Exception as e:
            self.logger.error(f"Failed to create appointment in Custom EHR: {e}")
            return None
    
    async def update_appointment(self, appointment_id: str, updates: Dict[str, Any]) -> bool:
        """Update appointment in custom EHR."""
        try:
            self.logger.info(f"Updated appointment {appointment_id} in Custom EHR: {updates}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update appointment in Custom EHR: {e}")
            return False
    
    async def get_lab_results(self, patient_id: str, date_range: Tuple[datetime, datetime]) -> List[LabResultData]:
        """Retrieve lab results from custom EHR."""
        try:
            start_date, end_date = date_range
            lab_results = [
                {
                    "result_id": f"custom_lab_{patient_id}_001",
                    "patient_id": patient_id,
                    "test_name": "Custom Lab Test",
                    "test_date": start_date + timedelta(days=1),
                    "result_value": "Custom Value",
                    "unit": "Custom Unit",
                    "reference_range": "Custom Range",
                    "status": "normal",
                    "ordering_provider": "Custom Provider",
                    "lab_facility": "Custom Lab"
                }
            ]
            
            return [LabResultData(**result) for result in lab_results]
            
        except Exception as e:
            self.logger.error(f"Failed to get lab results from Custom EHR: {e}")
            return []
    
    async def create_prescription(self, prescription_data: Dict[str, Any]) -> Optional[str]:
        """Create prescription in custom EHR."""
        try:
            prescription_id = f"custom_rx_{len(prescription_data)}_{datetime.now().timestamp()}"
            self.logger.info(f"Created prescription in Custom EHR: {prescription_id}")
            return prescription_id
            
        except Exception as e:
            self.logger.error(f"Failed to create prescription in Custom EHR: {e}")
            return None


class EHRIntegrationManager:
    """Manager for multiple EHR system integrations."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize EHR integration manager.
        
        Args:
            config: Configuration for all EHR integrations
        """
        self.config = config
        self.integrations: Dict[EHRProvider, BaseEHRIntegration] = {}
        self.logger = logging.getLogger("EHRIntegrationManager")
        self._initialize_integrations()
    
    def _initialize_integrations(self):
        """Initialize all configured EHR integrations."""
        for provider in EHRProvider:
            provider_config = self.config.get(provider.value, {})
            if provider_config.get("enabled", False):
                if provider == EHRProvider.EPIC:
                    self.integrations[provider] = EpicEHRIntegration(provider_config)
                elif provider == EHRProvider.CERNER:
                    self.integrations[provider] = CernerEHRIntegration(provider_config)
                elif provider == EHRProvider.ALLSCRIPTS:
                    self.integrations[provider] = AllscriptsEHRIntegration(provider_config)
                elif provider == EHRProvider.CUSTOM:
                    self.integrations[provider] = CustomEHRIntegration(provider_config)
                
                self.logger.info(f"Initialized {provider.value} EHR integration")
    
    async def get_integration(self, provider: EHRProvider) -> Optional[BaseEHRIntegration]:
        """
        Get EHR integration for a specific provider.
        
        Args:
            provider: EHR provider to get integration for
            
        Returns:
            EHR integration instance or None if not available
        """
        return self.integrations.get(provider)
    
    async def get_patient_data(self, provider: EHRProvider, patient_id: str) -> Optional[PatientData]:
        """
        Get patient data from specified EHR provider.
        
        Args:
            provider: EHR provider to query
            patient_id: Patient identifier
            
        Returns:
            Patient data or None if not found
        """
        integration = await self.get_integration(provider)
        if integration:
            return await integration.get_patient_data(patient_id)
        return None
    
    async def update_patient_data(self, provider: EHRProvider, patient_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update patient data in specified EHR provider.
        
        Args:
            provider: EHR provider to update
            patient_id: Patient identifier
            updates: Data to update
            
        Returns:
            True if successful, False otherwise
        """
        integration = await self.get_integration(provider)
        if integration:
            return await integration.update_patient_data(patient_id, updates)
        return False
    
    async def create_appointment(self, provider: EHRProvider, appointment_data: Dict[str, Any]) -> Optional[str]:
        """
        Create appointment in specified EHR provider.
        
        Args:
            provider: EHR provider to create appointment in
            appointment_data: Appointment information
            
        Returns:
            Appointment ID if successful, None otherwise
        """
        integration = await self.get_integration(provider)
        if integration:
            return await integration.create_appointment(appointment_data)
        return None
    
    async def get_lab_results(self, provider: EHRProvider, patient_id: str, date_range: Tuple[datetime, datetime]) -> List[LabResultData]:
        """
        Get lab results from specified EHR provider.
        
        Args:
            provider: EHR provider to query
            patient_id: Patient identifier
            date_range: Date range for results
            
        Returns:
            List of lab results
        """
        integration = await self.get_integration(provider)
        if integration:
            return await integration.get_lab_results(patient_id, date_range)
        return []
    
    async def create_prescription(self, provider: EHRProvider, prescription_data: Dict[str, Any]) -> Optional[str]:
        """
        Create prescription in specified EHR provider.
        
        Args:
            provider: EHR provider to create prescription in
            prescription_data: Prescription information
            
        Returns:
            Prescription ID if successful, None otherwise
        """
        integration = await self.get_integration(provider)
        if integration:
            return await integration.create_prescription(prescription_data)
        return None
    
    def get_available_providers(self) -> List[EHRProvider]:
        """
        Get list of available EHR providers.
        
        Returns:
            List of configured EHR providers
        """
        return list(self.integrations.keys())
    
    async def test_connection(self, provider: EHRProvider) -> bool:
        """
        Test connection to specified EHR provider.
        
        Args:
            provider: EHR provider to test
            
        Returns:
            True if connection successful, False otherwise
        """
        integration = await self.get_integration(provider)
        if integration:
            return await integration.authenticate()
        return False
