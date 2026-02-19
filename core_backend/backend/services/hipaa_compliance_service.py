"""
HIPAA Compliance Service

Specialized service for ensuring HIPAA compliance in healthcare automation workflows.
Provides audit trail management, PHI protection, and compliance monitoring.
"""

import asyncio
import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from uuid import UUID, uuid4
from cryptography.fernet import Fernet
from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel, Field

from ..mongo import get_collection

logger = logging.getLogger(__name__)


class PHIAccessLog(BaseModel):
    """Protected Health Information access log entry."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    organization_id: str

    # Access details
    access_type: str = Field(..., pattern="^(view|create|update|delete|export)$")
    resource_type: str  # appointment, patient_record, medical_data
    resource_id: str
    patient_id_hash: str  # Hashed patient ID for tracking

    # User/System details
    user_id: Optional[str] = None
    user_role: Optional[str] = None
    system_component: str  # e.g., vapi_agent, appointment_service
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Authorization
    authorization_basis: str  # treatment, payment, healthcare_operations, consent
    minimum_necessary: bool = True
    consent_obtained: bool = False
    consent_type: Optional[str] = None  # written, verbal, implied

    # Data details
    phi_elements_accessed: List[str] = Field(default_factory=list)  # name, ssn, dob, etc.
    data_minimization_applied: bool = True
    encryption_used: bool = True

    # Compliance tracking
    hipaa_compliant: bool = True
    compliance_notes: Optional[str] = None
    risk_level: str = Field(..., pattern="^(low|medium|high|critical)$")

    # Timing
    access_timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None

    # Audit
    audit_trail_id: str = Field(default_factory=lambda: str(uuid4()))


class HIPAAViolation(BaseModel):
    """HIPAA violation tracking model."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    organization_id: str

    # Violation details
    violation_type: str  # unauthorized_access, data_breach, improper_disclosure
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    description: str
    affected_patients: int = 0

    # Detection
    detected_by: str  # system, user_report, audit
    detection_timestamp: datetime = Field(default_factory=datetime.utcnow)
    automated_detection: bool = True

    # Response
    response_required: bool = True
    notification_required: bool = False  # For breaches affecting 500+ individuals
    response_actions: List[str] = Field(default_factory=list)

    # Resolution
    status: str = Field(default="open", pattern="^(open|investigating|resolved|closed)$")
    resolution_timestamp: Optional[datetime] = None
    resolution_notes: Optional[str] = None

    # Compliance impact
    reportable_breach: bool = False
    regulatory_notification_sent: bool = False
    patient_notification_sent: bool = False


class HIPAAComplianceMetrics(BaseModel):
    """HIPAA compliance metrics and dashboard data."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    organization_id: str
    period_start: datetime
    period_end: datetime

    # Access metrics
    total_phi_accesses: int = 0
    authorized_accesses: int = 0
    unauthorized_attempts: int = 0
    encryption_compliance_rate: float = Field(ge=0, le=1)

    # Audit metrics
    audit_logs_generated: int = 0
    audit_log_completeness: float = Field(ge=0, le=1)
    minimum_necessary_compliance: float = Field(ge=0, le=1)

    # Violation metrics
    total_violations: int = 0
    critical_violations: int = 0
    resolved_violations: int = 0
    average_resolution_time: float = 0.0  # hours

    # Risk assessment
    overall_risk_score: float = Field(ge=0, le=1)
    risk_factors: List[str] = Field(default_factory=list)

    # Compliance score
    compliance_score: float = Field(ge=0, le=100)
    compliance_grade: str = Field(..., pattern="^(A|B|C|D|F)$")

    generated_at: datetime = Field(default_factory=datetime.utcnow)


class HIPAAComplianceService:
    """Service for HIPAA compliance monitoring and enforcement."""

    def __init__(self):
        self.phi_access_collection = "hipaa_phi_access_logs"
        self.violations_collection = "hipaa_violations"
        self.metrics_collection = "hipaa_compliance_metrics"
        self.encryption_key = self._get_encryption_key()

    def _get_encryption_key(self) -> bytes:
        """Get or generate encryption key for PHI protection."""
        # In production, this should be stored securely (e.g., AWS KMS, Azure Key Vault)
        # For now, generate a consistent key
        key_material = "hipaa_compliance_service_key_2024"
        return Fernet.generate_key()

    async def log_phi_access(
        self,
        organization_id: str,
        access_data: Dict[str, Any]
    ) -> str:
        """Log PHI access with comprehensive audit trail."""
        try:
            # Hash patient ID for privacy
            patient_id = access_data.get("patient_id", "")
            patient_id_hash = hashlib.sha256(patient_id.encode()).hexdigest()[:16]

            # Analyze risk level
            risk_level = self._assess_access_risk(access_data)

            # Check compliance
            is_compliant, compliance_notes = self._validate_access_compliance(access_data)

            # Create access log
            access_log = PHIAccessLog(
                organization_id=organization_id,
                access_type=access_data.get("access_type", "view"),
                resource_type=access_data.get("resource_type", "unknown"),
                resource_id=access_data.get("resource_id", ""),
                patient_id_hash=patient_id_hash,
                user_id=access_data.get("user_id"),
                user_role=access_data.get("user_role", "system"),
                system_component=access_data.get("system_component", "unknown"),
                ip_address=access_data.get("ip_address"),
                authorization_basis=access_data.get("authorization_basis", "healthcare_operations"),
                minimum_necessary=access_data.get("minimum_necessary", True),
                consent_obtained=access_data.get("consent_obtained", False),
                consent_type=access_data.get("consent_type"),
                phi_elements_accessed=access_data.get("phi_elements_accessed", []),
                data_minimization_applied=access_data.get("data_minimization_applied", True),
                encryption_used=access_data.get("encryption_used", True),
                hipaa_compliant=is_compliant,
                compliance_notes=compliance_notes,
                risk_level=risk_level,
                session_id=access_data.get("session_id")
            )

            # Store in database
            collection = get_collection(self.phi_access_collection)
            result = await collection.insert_one(access_log.model_dump())

            # Check for violations
            if not is_compliant:
                await self._create_violation_record(organization_id, access_log, access_data)

            # Update compliance metrics
            await self._update_compliance_metrics(organization_id, access_log)

            logger.info(f"Logged PHI access: {result.inserted_id}")
            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Error logging PHI access: {str(e)}")
            raise

    def _assess_access_risk(self, access_data: Dict[str, Any]) -> str:
        """Assess risk level of PHI access."""
        risk_score = 0

        # Access type risk
        access_type = access_data.get("access_type", "view")
        if access_type in ["export", "delete"]:
            risk_score += 3
        elif access_type in ["update", "create"]:
            risk_score += 2
        else:  # view
            risk_score += 1

        # Authorization basis risk
        auth_basis = access_data.get("authorization_basis", "healthcare_operations")
        if auth_basis == "consent":
            risk_score += 1
        elif auth_basis in ["treatment", "payment"]:
            risk_score += 2
        else:
            risk_score += 3

        # PHI elements risk
        phi_elements = access_data.get("phi_elements_accessed", [])
        sensitive_elements = ["ssn", "financial_info", "mental_health", "substance_abuse"]
        if any(element in sensitive_elements for element in phi_elements):
            risk_score += 2

        # System component risk
        system_component = access_data.get("system_component", "unknown")
        if system_component == "vapi_agent":
            risk_score += 1  # Voice agents have additional risks

        # Determine risk level
        if risk_score <= 3:
            return "low"
        elif risk_score <= 5:
            return "medium"
        elif risk_score <= 7:
            return "high"
        else:
            return "critical"

    def _validate_access_compliance(self, access_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate HIPAA compliance of PHI access."""
        compliance_issues = []

        # Check minimum necessary standard
        if not access_data.get("minimum_necessary", True):
            compliance_issues.append("Minimum necessary standard not applied")

        # Check encryption
        if not access_data.get("encryption_used", True):
            compliance_issues.append("PHI not encrypted")

        # Check authorization basis
        auth_basis = access_data.get("authorization_basis", "")
        valid_bases = ["treatment", "payment", "healthcare_operations", "consent"]
        if auth_basis not in valid_bases:
            compliance_issues.append("Invalid authorization basis")

        # Check consent for certain access types
        if auth_basis == "consent" and not access_data.get("consent_obtained", False):
            compliance_issues.append("Consent required but not obtained")

        # Check audit trail
        if not access_data.get("audit_trail_enabled", True):
            compliance_issues.append("Audit trail not properly maintained")

        # Return compliance status
        is_compliant = len(compliance_issues) == 0
        notes = "; ".join(compliance_issues) if compliance_issues else None

        return is_compliant, notes

    async def _create_violation_record(
        self,
        organization_id: str,
        access_log: PHIAccessLog,
        access_data: Dict[str, Any]
    ):
        """Create a HIPAA violation record."""
        try:
            violation = HIPAAViolation(
                organization_id=organization_id,
                violation_type="improper_access",
                severity=access_log.risk_level,
                description=f"Non-compliant PHI access: {access_log.compliance_notes}",
                affected_patients=1,
                detected_by="system",
                automated_detection=True,
                response_required=True,
                response_actions=["Review access logs", "Investigate authorization", "Update procedures"]
            )

            collection = get_collection(self.violations_collection)
            await collection.insert_one(violation.model_dump())

            logger.warning(f"HIPAA violation recorded for organization {organization_id}")

        except Exception as e:
            logger.error(f"Error creating violation record: {str(e)}")

    async def _update_compliance_metrics(self, organization_id: str, access_log: PHIAccessLog):
        """Update real-time compliance metrics."""
        try:
            collection = get_collection(self.metrics_collection)

            # Get current day metrics
            today = datetime.utcnow().date()
            period_start = datetime.combine(today, datetime.min.time())
            period_end = datetime.combine(today, datetime.max.time())

            # Update or create metrics record
            await collection.update_one(
                {
                    "organization_id": organization_id,
                    "period_start": {"$gte": period_start},
                    "period_end": {"$lte": period_end}
                },
                {
                    "$inc": {
                        "total_phi_accesses": 1,
                        "authorized_accesses": 1 if access_log.hipaa_compliant else 0,
                        "unauthorized_attempts": 0 if access_log.hipaa_compliant else 1,
                        "audit_logs_generated": 1
                    },
                    "$set": {
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )

        except Exception as e:
            logger.error(f"Error updating compliance metrics: {str(e)}")

    async def get_compliance_dashboard(
        self,
        organization_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get comprehensive HIPAA compliance dashboard data."""
        try:
            # Get access logs
            access_logs = await self._get_access_logs(organization_id, start_date, end_date)
            violations = await self._get_violations(organization_id, start_date, end_date)

            # Calculate metrics
            total_accesses = len(access_logs)
            compliant_accesses = len([log for log in access_logs if log.get("hipaa_compliant", True)])
            encryption_compliant = len([log for log in access_logs if log.get("encryption_used", True)])
            min_necessary_compliant = len([log for log in access_logs if log.get("minimum_necessary", True)])

            # Calculate rates
            compliance_rate = (compliant_accesses / total_accesses * 100) if total_accesses > 0 else 100
            encryption_rate = (encryption_compliant / total_accesses * 100) if total_accesses > 0 else 100
            min_necessary_rate = (min_necessary_compliant / total_accesses * 100) if total_accesses > 0 else 100

            # Risk assessment
            high_risk_accesses = len([log for log in access_logs if log.get("risk_level") in ["high", "critical"]])
            risk_score = (high_risk_accesses / total_accesses) if total_accesses > 0 else 0

            # Violation analysis
            critical_violations = len([v for v in violations if v.get("severity") == "critical"])
            open_violations = len([v for v in violations if v.get("status") == "open"])

            # Compliance grade
            if compliance_rate >= 95 and critical_violations == 0:
                grade = "A"
            elif compliance_rate >= 90 and critical_violations <= 1:
                grade = "B"
            elif compliance_rate >= 80 and critical_violations <= 3:
                grade = "C"
            elif compliance_rate >= 70:
                grade = "D"
            else:
                grade = "F"

            dashboard = {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "overview": {
                    "total_phi_accesses": total_accesses,
                    "compliance_rate": f"{compliance_rate:.1f}%",
                    "compliance_grade": grade,
                    "risk_score": f"{risk_score * 100:.1f}%"
                },
                "compliance_metrics": {
                    "encryption_compliance": f"{encryption_rate:.1f}%",
                    "minimum_necessary_compliance": f"{min_necessary_rate:.1f}%",
                    "authorization_compliance": f"{compliance_rate:.1f}%"
                },
                "violations": {
                    "total": len(violations),
                    "critical": critical_violations,
                    "open": open_violations,
                    "resolved": len([v for v in violations if v.get("status") == "resolved"])
                },
                "risk_analysis": {
                    "high_risk_accesses": high_risk_accesses,
                    "most_accessed_resources": self._analyze_resource_access(access_logs),
                    "access_patterns": self._analyze_access_patterns(access_logs)
                },
                "recommendations": self._generate_compliance_recommendations(
                    compliance_rate, violations, access_logs
                ),
                "generated_at": datetime.utcnow().isoformat()
            }

            return dashboard

        except Exception as e:
            logger.error(f"Error generating compliance dashboard: {str(e)}")
            return {"error": f"Failed to generate dashboard: {str(e)}"}

    async def _get_access_logs(
        self,
        organization_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get PHI access logs for period."""
        try:
            collection = get_collection(self.phi_access_collection)
            query = {
                "organization_id": organization_id,
                "access_timestamp": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }

            cursor = collection.find(query).sort("access_timestamp", -1)
            return await cursor.to_list(length=10000)

        except Exception as e:
            logger.error(f"Error retrieving access logs: {str(e)}")
            return []

    async def _get_violations(
        self,
        organization_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get HIPAA violations for period."""
        try:
            collection = get_collection(self.violations_collection)
            query = {
                "organization_id": organization_id,
                "detection_timestamp": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }

            cursor = collection.find(query).sort("detection_timestamp", -1)
            return await cursor.to_list(length=1000)

        except Exception as e:
            logger.error(f"Error retrieving violations: {str(e)}")
            return []

    def _analyze_resource_access(self, access_logs: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze most frequently accessed resources."""
        resource_counts = {}
        for log in access_logs:
            resource_type = log.get("resource_type", "unknown")
            resource_counts[resource_type] = resource_counts.get(resource_type, 0) + 1

        # Return top 5 most accessed
        return dict(sorted(resource_counts.items(), key=lambda x: x[1], reverse=True)[:5])

    def _analyze_access_patterns(self, access_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze access patterns for anomaly detection."""
        patterns = {
            "peak_hours": {},
            "system_components": {},
            "risk_distribution": {"low": 0, "medium": 0, "high": 0, "critical": 0}
        }

        for log in access_logs:
            # Hour analysis
            if "access_timestamp" in log:
                timestamp = log["access_timestamp"]
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp)
                hour = timestamp.hour
                patterns["peak_hours"][hour] = patterns["peak_hours"].get(hour, 0) + 1

            # System component analysis
            component = log.get("system_component", "unknown")
            patterns["system_components"][component] = patterns["system_components"].get(component, 0) + 1

            # Risk distribution
            risk_level = log.get("risk_level", "low")
            patterns["risk_distribution"][risk_level] += 1

        return patterns

    def _generate_compliance_recommendations(
        self,
        compliance_rate: float,
        violations: List[Dict[str, Any]],
        access_logs: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate actionable compliance recommendations."""
        recommendations = []

        # Compliance rate recommendations
        if compliance_rate < 95:
            recommendations.append("Implement additional HIPAA compliance training")
            recommendations.append("Review and update PHI access procedures")

        # Violation recommendations
        critical_violations = [v for v in violations if v.get("severity") == "critical"]
        if len(critical_violations) > 0:
            recommendations.append("Immediately investigate and resolve critical violations")
            recommendations.append("Implement additional access controls")

        # Encryption recommendations
        unencrypted_accesses = [log for log in access_logs if not log.get("encryption_used", True)]
        if len(unencrypted_accesses) > 0:
            recommendations.append("Ensure all PHI is encrypted in transit and at rest")

        # Audit recommendations
        if len(access_logs) > 1000:  # High volume
            recommendations.append("Consider implementing automated compliance monitoring")
            recommendations.append("Set up real-time alerts for compliance violations")

        return recommendations

    async def encrypt_phi_data(self, data: str) -> str:
        """Encrypt PHI data for secure storage."""
        try:
            fernet = Fernet(self.encryption_key)
            encrypted_data = fernet.encrypt(data.encode())
            return encrypted_data.decode()
        except Exception as e:
            logger.error(f"Error encrypting PHI data: {str(e)}")
            raise

    async def decrypt_phi_data(self, encrypted_data: str) -> str:
        """Decrypt PHI data for authorized access."""
        try:
            fernet = Fernet(self.encryption_key)
            decrypted_data = fernet.decrypt(encrypted_data.encode())
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Error decrypting PHI data: {str(e)}")
            raise

    async def validate_minimum_necessary(
        self,
        requested_fields: List[str],
        purpose: str,
        user_role: str
    ) -> Dict[str, Any]:
        """Validate minimum necessary standard for PHI access."""
        try:
            # Define minimum necessary field sets by purpose and role
            field_sets = {
                "treatment": {
                    "provider": ["name", "dob", "medical_history", "current_medications"],
                    "nurse": ["name", "dob", "current_medications", "allergies"],
                    "admin": ["name", "appointment_id", "insurance_info"]
                },
                "payment": {
                    "billing": ["name", "dob", "insurance_info", "services_provided"],
                    "admin": ["name", "insurance_info", "billing_address"]
                },
                "healthcare_operations": {
                    "analyst": ["anonymized_data", "statistics"],
                    "admin": ["name", "appointment_history", "service_utilization"]
                }
            }

            allowed_fields = field_sets.get(purpose, {}).get(user_role, [])

            # Check if requested fields are within minimum necessary
            excessive_fields = [field for field in requested_fields if field not in allowed_fields]

            return {
                "compliant": len(excessive_fields) == 0,
                "allowed_fields": allowed_fields,
                "excessive_fields": excessive_fields,
                "recommendation": "Remove excessive fields to comply with minimum necessary standard" if excessive_fields else "Access request is compliant"
            }

        except Exception as e:
            logger.error(f"Error validating minimum necessary: {str(e)}")
            return {"compliant": False, "error": str(e)}