"""
Basic import tests for shared library
"""

import pytest
from datetime import datetime


# Test telephony imports
def test_telephony_imports():
    """Test telephony module imports"""
    from apps.shared.telephony import (
        TelephonyEvent,
        TelephonyEventType,
        TelephonyPort,
        ProviderManager,
        CallContext,
        ProviderHealth,
        ProviderSettings,
    )

    # Test TelephonyEvent creation
    event = TelephonyEvent(
        event_type=TelephonyEventType.CALL_STARTED,
        call_id="test_call_123",
        provider="test_provider",
        data={"test": "data"},
    )

    assert event.event_type == TelephonyEventType.CALL_STARTED
    assert event.call_id == "test_call_123"
    assert event.provider == "test_provider"
    assert event.data["test"] == "data"
    assert isinstance(event.timestamp, datetime)


# Test config imports
def test_config_imports():
    """Test configuration module imports"""
    from apps.shared.config import (
        TenantConfig,
        ProviderConfig,
        BrandingConfig,
        ConfigurationManager,
        FeatureFlags,
        ModuleConfig,
        WorkflowConfig,
    )

    # Test TenantConfig creation
    config = TenantConfig(
        tenant_id="test_tenant",
        name="Test Tenant",
        features={"test_feature": True},
        modules=["test_module"],
    )

    assert config.tenant_id == "test_tenant"
    assert config.name == "Test Tenant"
    assert config.features["test_feature"] is True
    assert "test_module" in config.modules


# Test usage imports
def test_usage_imports():
    """Test usage tracking module imports"""
    from apps.shared.usage import (
        UsageRecord,
        UsageTracker,
        UsageSummary,
        CostBreakdown,
        UsageMetrics,
    )

    # Test UsageRecord creation
    record = UsageRecord(
        tenant_id="test_tenant",
        service="test_service",
        metric="test_metric",
        value=10.5,
        cost=1.25,
    )

    assert record.tenant_id == "test_tenant"
    assert record.service == "test_service"
    assert record.metric == "test_metric"
    assert record.value == 10.5
    assert record.cost == 1.25
    assert isinstance(record.timestamp, datetime)


# Test license imports
def test_license_imports():
    """Test license management module imports"""
    from apps.shared.license import (
        LicenseInfo,
        LicenseValidator,
        LicenseFeatures,
        LicenseLimits,
        LicenseStatus,
    )

    # Test LicenseInfo creation
    license_info = LicenseInfo(
        license_key="test_key_123",
        tenant_id="test_tenant",
        license_type="standard",
        features=["feature1", "feature2"],
        max_users=10,
        max_calls_per_month=1000,
        issued_date=datetime.utcnow(),
    )

    assert license_info.license_key == "test_key_123"
    assert license_info.tenant_id == "test_tenant"
    assert license_info.license_type == "standard"
    assert "feature1" in license_info.features
    assert license_info.max_users == 10
    assert license_info.max_calls_per_month == 1000


# Test events imports
def test_events_imports():
    """Test event system module imports"""
    from apps.shared.events import (
        Event,
        EventBus,
        EventHandler,
        EventFilter,
        EventSubscription,
        EventMetrics,
    )

    # Test Event creation
    event = Event(
        event_id="test_event_123",
        event_type="test_type",
        source="test_source",
        tenant_id="test_tenant",
        data={"test": "data"},
    )

    assert event.event_id == "test_event_123"
    assert event.event_type == "test_type"
    assert event.source == "test_source"
    assert event.tenant_id == "test_tenant"
    assert event.data["test"] == "data"
    assert isinstance(event.timestamp, datetime)


# Test main package import
def test_main_package_import():
    """Test main package import"""
    from shared import (
        TelephonyEvent,
        TelephonyPort,
        ProviderManager,
        TenantConfig,
        ProviderConfig,
        BrandingConfig,
        ConfigurationManager,
        UsageRecord,
        UsageTracker,
        LicenseInfo,
        LicenseValidator,
        Event,
        EventBus,
        EventHandler,
    )

    # Verify all imports work
    assert TelephonyEvent is not None
    assert TelephonyPort is not None
    assert ProviderManager is not None
    assert TenantConfig is not None
    assert ProviderConfig is not None
    assert BrandingConfig is not None
    assert ConfigurationManager is not None
    assert UsageRecord is not None
    assert UsageTracker is not None
    assert LicenseInfo is not None
    assert LicenseValidator is not None
    assert Event is not None
    assert EventBus is not None
    assert EventHandler is not None


if __name__ == "__main__":
    pytest.main([__file__])
