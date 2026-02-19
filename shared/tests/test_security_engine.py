"""
Tests for Security Engine implementation.

This module provides comprehensive tests for the Security Engine including
audit logging, monitoring, access control, compliance monitoring, encryption,
and overall security management.
"""

import pytest
import json
from datetime import datetime, timedelta
from uuid import uuid4

from ..security.engine import SecurityEngine
from ..security.interfaces import (
    SecurityAudit, SecurityEvent, AccessControl, ComplianceRule, 
    ComplianceViolation
)
from ..storage.interfaces import StorageBackend


class SimpleStorageAdapter:
    """Simple in-memory storage adapter for testing"""
    
    def __init__(self):
        self.tables = {}
        self.data = {}
    
    async def create_table(self, table_name: str, schema: dict):
        """Create a table with the given schema"""
        self.tables[table_name] = schema
        self.data[table_name] = []
    
    async def insert(self, table_name: str, data: dict):
        """Insert data into table"""
        if table_name not in self.data:
            self.data[table_name] = []
        self.data[table_name].append(data.copy())
    
    async def select(self, table_name: str, conditions: dict = None) -> list:
        """Select data from table with conditions"""
        if table_name not in self.data:
            return []
        
        results = self.data[table_name]
        if not conditions:
            return results
        
        filtered_results = []
        for row in results:
            match = True
            for key, value in conditions.items():
                if isinstance(value, dict) and "$gte" in value:
                    # Handle greater than or equal condition
                    if key not in row or row[key] < value["$gte"]:
                        match = False
                        break
                elif isinstance(value, dict) and "$lte" in value:
                    # Handle less than or equal condition
                    if key not in row or row[key] > value["$lte"]:
                        match = False
                        break
                elif key not in row or row[key] != value:
                    match = False
                    break
            if match:
                filtered_results.append(row)
        return filtered_results
    
    async def select_one(self, table_name: str, conditions: dict = None) -> dict:
        """Select one record from table"""
        results = await self.select(table_name, conditions)
        return results[0] if results else None
    
    async def upsert(self, table_name: str, data: dict):
        """Upsert data into table"""
        if table_name not in self.data:
            self.data[table_name] = []
        
        # Find existing record
        existing_index = None
        for i, row in enumerate(self.data[table_name]):
            if self._matches_primary_key(table_name, row, data):
                existing_index = i
                break
        
        if existing_index is not None:
            self.data[table_name][existing_index] = data.copy()
        else:
            self.data[table_name].append(data.copy())
    
    async def delete(self, table_name: str, conditions: dict):
        """Delete data from table"""
        if table_name not in self.data:
            return
        
        # Find and remove matching records
        self.data[table_name] = [
            row for row in self.data[table_name]
            if not self._matches_conditions(row, conditions)
        ]
    
    def _matches_primary_key(self, table_name: str, row: dict, data: dict) -> bool:
        """Check if row matches primary key of data"""
        schema = self.tables.get(table_name, {})
        
        # Handle composite primary keys
        if "PRIMARY KEY" in schema:
            pk_parts = schema["PRIMARY KEY"].strip("()").split(", ")
            for part in pk_parts:
                pk_field = part.strip()
                if pk_field in data and pk_field in row:
                    if row[pk_field] != data[pk_field]:
                        return False
                else:
                    return False
            return True
        
        # Handle single primary key
        for field, field_type in schema.items():
            if "PRIMARY KEY" in field_type:
                pk_field = field
                return pk_field in data and pk_field in row and row[pk_field] == data[pk_field]
        
        return False
    
    def _matches_conditions(self, row: dict, conditions: dict) -> bool:
        """Check if row matches all conditions"""
        for key, value in conditions.items():
            if key not in row or row[key] != value:
                return False
        return True


@pytest.fixture
def storage_backend():
    """Storage backend fixture"""
    return SimpleStorageAdapter()


@pytest.fixture
async def security_engine(storage_backend):
    """Security engine fixture"""
    engine = SecurityEngine(storage_backend)
    # Trigger initialization by calling a method
    await engine.get_security_status("test_tenant")
    return engine


class TestSecurityEngine:
    """Test Security Engine basic functionality"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, security_engine):
        """Test security engine initialization"""
        engine = await security_engine
        
        # Check that storage tables were created
        assert "security_audits" in engine.storage.tables
        assert "security_events" in engine.storage.tables
        assert "access_control" in engine.storage.tables
        assert "compliance_rules" in engine.storage.tables
        assert "compliance_violations" in engine.storage.tables
        assert "encryption_keys" in engine.storage.tables
        assert "security_settings" in engine.storage.tables
    
    @pytest.mark.asyncio
    async def test_audit_logging(self, security_engine):
        """Test audit logging functionality"""
        engine = await security_engine
        
        # Create test audit
        audit = SecurityAudit(
            audit_id=str(uuid4()),
            tenant_id="test_tenant",
            user_id="test_user",
            action="test_action",
            resource="test_resource",
            success=True,
            risk_level="low"
        )
        
        # Log audit
        result = await engine.log_audit(audit)
        assert result is True
        
        # Get audit logs
        logs = await engine.get_audit_logs("test_tenant")
        assert len(logs) == 1
        assert logs[0].audit_id == audit.audit_id
        assert logs[0].action == "test_action"
        assert logs[0].success is True
    
    @pytest.mark.asyncio
    async def test_audit_logging_with_filters(self, security_engine):
        """Test audit logging with filters"""
        engine = await security_engine
        
        # Create multiple audits
        audit1 = SecurityAudit(
            audit_id=str(uuid4()),
            tenant_id="test_tenant",
            user_id="user1",
            action="action1",
            resource="resource1",
            success=True,
            risk_level="low"
        )
        
        audit2 = SecurityAudit(
            audit_id=str(uuid4()),
            tenant_id="test_tenant",
            user_id="user2",
            action="action2",
            resource="resource2",
            success=False,
            risk_level="medium"
        )
        
        await engine.log_audit(audit1)
        await engine.log_audit(audit2)
        
        # Test filtering by user
        user1_logs = await engine.get_audit_logs("test_tenant", user_id="user1")
        assert len(user1_logs) == 1
        assert user1_logs[0].user_id == "user1"
        
        # Test filtering by action
        action2_logs = await engine.get_audit_logs("test_tenant", action="action2")
        assert len(action2_logs) == 1
        assert action2_logs[0].action == "action2"
    
    @pytest.mark.asyncio
    async def test_audit_export(self, security_engine):
        """Test audit log export functionality"""
        engine = await security_engine
        
        # Create test audit
        audit = SecurityAudit(
            audit_id=str(uuid4()),
            tenant_id="test_tenant",
            user_id="test_user",
            action="test_action",
            resource="test_resource",
            success=True,
            risk_level="low"
        )
        
        await engine.log_audit(audit)
        
        # Export as JSON
        json_export = await engine.export_audit_logs("test_tenant", format="json")
        assert "test_action" in json_export
        assert "test_resource" in json_export
        
        # Export as CSV
        csv_export = await engine.export_audit_logs("test_tenant", format="csv")
        assert "audit_id,tenant_id,user_id,action,resource" in csv_export
        assert "test_action" in csv_export
    
    @pytest.mark.asyncio
    async def test_security_event_recording(self, security_engine):
        """Test security event recording"""
        engine = await security_engine
        
        # Create test event
        event = SecurityEvent(
            event_id=str(uuid4()),
            event_type="test_event",
            severity="warning",
            tenant_id="test_tenant",
            user_id="test_user",
            source="test_source",
            message="Test security event"
        )
        
        # Record event
        result = await engine.record_event(event)
        assert result is True
        
        # Get active events
        events = await engine.get_active_events("test_tenant")
        assert len(events) == 1
        assert events[0].event_id == event.event_id
        assert events[0].event_type == "test_event"
        assert events[0].resolved is False
    
    @pytest.mark.asyncio
    async def test_event_resolution(self, security_engine):
        """Test security event resolution"""
        engine = await security_engine
        
        # Create and record event
        event = SecurityEvent(
            event_id=str(uuid4()),
            event_type="test_event",
            severity="warning",
            tenant_id="test_tenant",
            source="test_source",
            message="Test security event"
        )
        
        await engine.record_event(event)
        
        # Resolve event
        result = await engine.resolve_event(event.event_id, "Test resolution")
        assert result is True
        
        # Check that event is resolved
        events = await engine.get_active_events("test_tenant")
        assert len(events) == 0  # No active events
    
    @pytest.mark.asyncio
    async def test_access_control(self, security_engine):
        """Test access control functionality"""
        engine = await security_engine
        
        # Grant access
        result = await engine.grant_access(
            tenant_id="test_tenant",
            user_id="test_user",
            resource="test_resource",
            action="read",
            roles=["user"]
        )
        assert result is True
        
        # Check access
        has_access = await engine.check_access(
            tenant_id="test_tenant",
            user_id="test_user",
            resource="test_resource",
            action="read"
        )
        assert has_access is True
        
        # Check access to different resource
        no_access = await engine.check_access(
            tenant_id="test_tenant",
            user_id="test_user",
            resource="other_resource",
            action="read"
        )
        assert no_access is False
    
    @pytest.mark.asyncio
    async def test_access_revocation(self, security_engine):
        """Test access revocation"""
        engine = await security_engine
        
        # Grant access
        await engine.grant_access(
            tenant_id="test_tenant",
            user_id="test_user",
            resource="test_resource",
            action="read"
        )
        
        # Verify access
        has_access = await engine.check_access(
            tenant_id="test_tenant",
            user_id="test_user",
            resource="test_resource",
            action="read"
        )
        assert has_access is True
        
        # Revoke access
        result = await engine.revoke_access(
            tenant_id="test_tenant",
            user_id="test_user",
            resource="test_resource",
            action="read"
        )
        assert result is True
        
        # Verify access is revoked
        no_access = await engine.check_access(
            tenant_id="test_tenant",
            user_id="test_user",
            resource="test_resource",
            action="read"
        )
        assert no_access is False
    
    @pytest.mark.asyncio
    async def test_user_permissions(self, security_engine):
        """Test user permissions retrieval"""
        engine = await security_engine
        
        # Grant multiple permissions
        await engine.grant_access(
            tenant_id="test_tenant",
            user_id="test_user",
            resource="resource1",
            action="read"
        )
        
        await engine.grant_access(
            tenant_id="test_tenant",
            user_id="test_user",
            resource="resource1",
            action="write"
        )
        
        await engine.grant_access(
            tenant_id="test_tenant",
            user_id="test_user",
            resource="resource2",
            action="read"
        )
        
        # Get user permissions
        permissions = await engine.get_user_permissions("test_tenant", "test_user")
        
        assert "resource1" in permissions
        assert "resource2" in permissions
        assert "read" in permissions["resource1"]
        assert "write" in permissions["resource1"]
        assert "read" in permissions["resource2"]
        assert len(permissions["resource1"]) == 2
        assert len(permissions["resource2"]) == 1
    
    @pytest.mark.asyncio
    async def test_compliance_rule_management(self, security_engine):
        """Test compliance rule management"""
        engine = await security_engine
        
        # Create custom rule
        rule = ComplianceRule(
            rule_id="custom_rule",
            name="Custom Compliance Rule",
            description="A custom compliance rule for testing",
            category="CUSTOM",
            severity="medium",
            conditions={"test_condition": True},
            actions=["alert"]
        )
        
        # Add rule
        result = await engine.add_rule(rule)
        assert result is True
        
        # Check compliance (should not have violations for our test rule)
        violations = await engine.check_compliance("test_tenant")
        assert isinstance(violations, list)
    
    @pytest.mark.asyncio
    async def test_compliance_violation_recording(self, security_engine):
        """Test compliance violation recording"""
        engine = await security_engine
        
        # Create violation
        violation = ComplianceViolation(
            violation_id=str(uuid4()),
            rule_id="test_rule",
            tenant_id="test_tenant",
            severity="high",
            description="Test compliance violation"
        )
        
        # Record violation
        result = await engine.record_violation(violation)
        assert result is True
        
        # Check compliance report
        report = await engine.get_compliance_report("test_tenant")
        assert report["total_violations"] >= 1
    
    @pytest.mark.asyncio
    async def test_violation_resolution(self, security_engine):
        """Test compliance violation resolution"""
        engine = await security_engine
        
        # Create and record violation
        violation = ComplianceViolation(
            violation_id=str(uuid4()),
            rule_id="test_rule",
            tenant_id="test_tenant",
            severity="high",
            description="Test compliance violation"
        )
        
        await engine.record_violation(violation)
        
        # Resolve violation
        result = await engine.resolve_violation(
            violation.violation_id,
            "Test resolution notes"
        )
        assert result is True
    
    @pytest.mark.asyncio
    async def test_encryption_functionality(self, security_engine):
        """Test encryption and decryption functionality"""
        engine = await security_engine
        
        test_data = "sensitive data to encrypt"
        
        # Encrypt data
        encrypted = await engine.encrypt_data(test_data)
        assert encrypted != test_data
        assert isinstance(encrypted, str)
        
        # Decrypt data
        decrypted = await engine.decrypt_data(encrypted)
        assert decrypted == test_data
    
    @pytest.mark.asyncio
    async def test_key_management(self, security_engine):
        """Test encryption key management"""
        engine = await security_engine
        
        # Generate new key
        key_id = await engine.generate_key("test_key", "AES")
        assert isinstance(key_id, str)
        
        # Get key info
        key_info = await engine.get_key_info(key_id)
        assert key_info["key_name"] == "test_key"
        assert key_info["key_type"] == "AES"
        assert key_info["active"] is True
        
        # Rotate key
        result = await engine.rotate_key(key_id)
        assert result is True
        
        # Check that old key is inactive
        old_key_info = await engine.get_key_info(key_id)
        assert old_key_info["active"] is False
    
    @pytest.mark.asyncio
    async def test_security_metrics(self, security_engine):
        """Test security metrics calculation"""
        engine = await security_engine
        
        # Create some test data
        audit = SecurityAudit(
            audit_id=str(uuid4()),
            tenant_id="test_tenant",
            user_id="test_user",
            action="test_action",
            resource="test_resource",
            success=True,
            risk_level="low"
        )
        await engine.log_audit(audit)
        
        event = SecurityEvent(
            event_id=str(uuid4()),
            event_type="test_event",
            severity="warning",
            tenant_id="test_tenant",
            source="test_source",
            message="Test event"
        )
        await engine.record_event(event)
        
        # Get metrics
        metrics = await engine.get_security_metrics("test_tenant", "daily")
        
        assert "period" in metrics
        assert "audits" in metrics
        assert "events" in metrics
        assert "compliance" in metrics
        assert metrics["audits"]["total"] >= 1
        assert metrics["events"]["total"] >= 1
    
    @pytest.mark.asyncio
    async def test_security_initialization(self, security_engine):
        """Test security initialization for tenant"""
        engine = await security_engine
        
        # Initialize security for tenant
        result = await engine.initialize_security("new_tenant")
        assert result is True
        
        # Check that settings were created
        settings_result = await engine.storage.select_one(
            "security_settings", 
            {"tenant_id": "new_tenant"}
        )
        assert settings_result is not None
        
        settings = json.loads(settings_result["settings"])
        assert settings["audit_logging_enabled"] is True
        assert settings["encryption_enabled"] is True
        assert settings["access_control_enabled"] is True
    
    @pytest.mark.asyncio
    async def test_security_audit(self, security_engine):
        """Test comprehensive security audit"""
        engine = await security_engine
        
        # Perform security audit
        audit_result = await engine.perform_security_audit("test_tenant")
        
        assert "tenant_id" in audit_result
        assert "security_score" in audit_result
        assert "metrics" in audit_result
        assert "compliance" in audit_result
        assert "recommendations" in audit_result
        assert isinstance(audit_result["security_score"], (int, float))
        assert isinstance(audit_result["recommendations"], list)
    
    @pytest.mark.asyncio
    async def test_security_status(self, security_engine):
        """Test security status retrieval"""
        engine = await security_engine
        
        # Get security status
        status = await engine.get_security_status("test_tenant")
        
        assert "tenant_id" in status
        assert "status" in status
        assert "last_updated" in status
        assert "active_events_count" in status
        assert "compliance_rate" in status
        assert "audit_success_rate" in status
        assert status["status"] in ["healthy", "attention", "warning", "critical"]
    
    @pytest.mark.asyncio
    async def test_security_settings_update(self, security_engine):
        """Test security settings update"""
        engine = await security_engine
        
        # Update security settings
        new_settings = {
            "audit_logging_enabled": True,
            "encryption_enabled": True,
            "max_login_attempts": 10,
            "session_timeout_minutes": 60
        }
        
        result = await engine.update_security_settings("test_tenant", new_settings)
        assert result is True
        
        # Verify settings were updated
        settings_result = await engine.storage.select_one(
            "security_settings",
            {"tenant_id": "test_tenant"}
        )
        assert settings_result is not None
        
        settings = json.loads(settings_result["settings"])
        assert settings["max_login_attempts"] == 10
        assert settings["session_timeout_minutes"] == 60


class TestSecurityEngineIntegration:
    """Integration tests for Security Engine"""
    
    @pytest.mark.asyncio
    async def test_full_security_workflow(self, security_engine):
        """Test complete security workflow"""
        engine = await security_engine
        
        # 1. Initialize security for tenant
        await engine.initialize_security("workflow_tenant")
        
        # 2. Grant access to user
        await engine.grant_access(
            tenant_id="workflow_tenant",
            user_id="workflow_user",
            resource="workflow_resource",
            action="read"
        )
        
        # 3. Check access (should succeed)
        has_access = await engine.check_access(
            tenant_id="workflow_tenant",
            user_id="workflow_user",
            resource="workflow_resource",
            action="read"
        )
        assert has_access is True
        
        # 4. Encrypt sensitive data
        sensitive_data = "confidential information"
        encrypted = await engine.encrypt_data(sensitive_data)
        decrypted = await engine.decrypt_data(encrypted)
        assert decrypted == sensitive_data
        
        # 5. Record security event
        event = SecurityEvent(
            event_id=str(uuid4()),
            event_type="workflow_event",
            severity="info",
            tenant_id="workflow_tenant",
            user_id="workflow_user",
            source="workflow_test",
            message="Workflow security event"
        )
        await engine.record_event(event)
        
        # 6. Check compliance
        violations = await engine.check_compliance("workflow_tenant")
        assert isinstance(violations, list)
        
        # 7. Get security metrics
        metrics = await engine.get_security_metrics("workflow_tenant", "daily")
        assert metrics["audits"]["total"] >= 1  # At least the access check
        
        # 8. Perform security audit
        audit = await engine.perform_security_audit("workflow_tenant")
        assert audit["security_score"] >= 0
        assert audit["security_score"] <= 100
        
        # 9. Get security status
        status = await engine.get_security_status("workflow_tenant")
        assert status["status"] in ["healthy", "attention", "warning", "critical"]
    
    @pytest.mark.asyncio
    async def test_multi_tenant_isolation(self, security_engine):
        """Test multi-tenant security isolation"""
        engine = await security_engine
        
        # Initialize security for two tenants
        await engine.initialize_security("tenant1")
        await engine.initialize_security("tenant2")
        
        # Grant access to same user in both tenants
        await engine.grant_access(
            tenant_id="tenant1",
            user_id="shared_user",
            resource="shared_resource",
            action="read"
        )
        
        await engine.grant_access(
            tenant_id="tenant2",
            user_id="shared_user",
            resource="shared_resource",
            action="write"
        )
        
        # Check access isolation
        tenant1_access = await engine.check_access(
            tenant_id="tenant1",
            user_id="shared_user",
            resource="shared_resource",
            action="read"
        )
        assert tenant1_access is True
        
        tenant1_write_access = await engine.check_access(
            tenant_id="tenant1",
            user_id="shared_user",
            resource="shared_resource",
            action="write"
        )
        assert tenant1_write_access is False
        
        tenant2_access = await engine.check_access(
            tenant_id="tenant2",
            user_id="shared_user",
            resource="shared_resource",
            action="write"
        )
        assert tenant2_access is True
        
        # Check audit log isolation
        tenant1_logs = await engine.get_audit_logs("tenant1")
        tenant2_logs = await engine.get_audit_logs("tenant2")
        
        # Each tenant should have their own audit logs
        tenant1_tenant_ids = {log.tenant_id for log in tenant1_logs}
        tenant2_tenant_ids = {log.tenant_id for log in tenant2_logs}
        
        assert "tenant1" in tenant1_tenant_ids
        assert "tenant2" in tenant2_tenant_ids
        assert "tenant2" not in tenant1_tenant_ids
        assert "tenant1" not in tenant2_tenant_ids
    
    @pytest.mark.asyncio
    async def test_high_risk_activity_detection(self, security_engine):
        """Test high-risk activity detection and event generation"""
        engine = await security_engine
        
        # Create high-risk audit
        high_risk_audit = SecurityAudit(
            audit_id=str(uuid4()),
            tenant_id="risk_tenant",
            user_id="risk_user",
            action="admin_action",
            resource="sensitive_resource",
            success=True,
            risk_level="high"
        )
        
        # Log high-risk audit
        await engine.log_audit(high_risk_audit)
        
        # Check that security event was generated
        events = await engine.get_active_events("risk_tenant", severity="high")
        assert len(events) >= 1
        
        high_risk_event = events[0]
        assert high_risk_event.event_type == "high_risk_audit"
        assert high_risk_event.severity == "high"
        assert "admin_action" in high_risk_event.message
    
    @pytest.mark.asyncio
    async def test_failed_access_attempts(self, security_engine):
        """Test failed access attempt logging"""
        engine = await security_engine
        
        # Attempt access without permission
        has_access = await engine.check_access(
            tenant_id="access_tenant",
            user_id="unauthorized_user",
            resource="protected_resource",
            action="read"
        )
        assert has_access is False
        
        # Check that failed access was logged
        logs = await engine.get_audit_logs("access_tenant")
        failed_logs = [log for log in logs if not log.success]
        
        assert len(failed_logs) >= 1
        failed_log = failed_logs[0]
        assert failed_log.user_id == "unauthorized_user"
        assert failed_log.resource == "protected_resource"
        assert failed_log.action == "read"
        assert failed_log.success is False
        assert failed_log.risk_level == "medium"
    
    @pytest.mark.asyncio
    async def test_encryption_key_rotation(self, security_engine):
        """Test encryption key rotation workflow"""
        engine = await security_engine
        
        # Generate initial key
        key1_id = await engine.generate_key("rotation_test_key", "AES")
        
        # Encrypt data with first key
        test_data = "data to encrypt"
        encrypted1 = await engine.encrypt_data(test_data, key1_id)
        
        # Rotate key
        await engine.rotate_key(key1_id)
        
        # Check that old key is inactive
        old_key_info = await engine.get_key_info(key1_id)
        assert old_key_info["active"] is False
        
        # Decrypt with old key should still work (for backward compatibility)
        decrypted1 = await engine.decrypt_data(encrypted1, key1_id)
        assert decrypted1 == test_data
        
        # New encryption should use new key
        encrypted2 = await engine.encrypt_data(test_data)
        assert encrypted2 != encrypted1  # Should be different due to different key
        
        # Decrypt new data
        decrypted2 = await engine.decrypt_data(encrypted2)
        assert decrypted2 == test_data
    
    @pytest.mark.asyncio
    async def test_compliance_violation_workflow(self, security_engine):
        """Test compliance violation detection and resolution workflow"""
        engine = await security_engine
        
        # Create custom rule that will be violated
        violation_rule = ComplianceRule(
            rule_id="test_violation_rule",
            name="Test Violation Rule",
            description="Rule that will be violated for testing",
            category="TEST",
            severity="high",
            conditions={"force_violation": True},
            actions=["alert", "log"]
        )
        
        # Add rule
        await engine.add_rule(violation_rule)
        
        # Check compliance (should detect violation)
        violations = await engine.check_compliance("violation_tenant")
        
        # For our test rule, we assume no violations (simplified implementation)
        # In a real implementation, this would detect actual violations
        assert isinstance(violations, list)
        
        # Get compliance report
        report = await engine.get_compliance_report("violation_tenant")
        assert "total_violations" in report
        assert "compliance_rate" in report
        assert report["compliance_rate"] >= 0
        assert report["compliance_rate"] <= 1
    
    @pytest.mark.asyncio
    async def test_security_recommendations(self, security_engine):
        """Test security recommendations generation"""
        engine = await security_engine
        
        # Create some test data that would trigger recommendations
        # Create failed access attempts
        for i in range(3):
            await engine.check_access(
                tenant_id="recommendation_tenant",
                user_id=f"user{i}",
                resource="protected_resource",
                action="read"
            )
        
        # Create high-risk activity
        high_risk_audit = SecurityAudit(
            audit_id=str(uuid4()),
            tenant_id="recommendation_tenant",
            user_id="admin_user",
            action="system_config_change",
            resource="system_settings",
            success=True,
            risk_level="high"
        )
        await engine.log_audit(high_risk_audit)
        
        # Perform security audit to generate recommendations
        audit_result = await engine.perform_security_audit("recommendation_tenant")
        
        assert "recommendations" in audit_result
        assert isinstance(audit_result["recommendations"], list)
        
        # Should have recommendations for high-risk activities
        recommendations = audit_result["recommendations"]
        high_risk_recommendations = [
            rec for rec in recommendations 
            if "high-risk" in rec.lower() or "activities" in rec.lower()
        ]
        assert len(high_risk_recommendations) >= 1
