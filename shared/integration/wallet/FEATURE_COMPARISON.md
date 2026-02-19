# Wallet Implementation Feature Comparison

**Date**: 2025-10-27
**Purpose**: Identify best features from both implementations for consolidation

---

## Data Models Comparison

### Wallet Model

| Feature | Shared | Core | Winner | Reason |
|---------|--------|------|--------|--------|
| **Basic Fields** |
| id, user_id, balance, currency | ✅ | ✅ | Tie | Both have |
| Decimal precision for balance | ✅ | ⚠️ | **Shared** | Core converts to float |
| tenant_id for multi-tenancy | ❌ | ✅ | **Core** | Needed for multi-app |
| **Advanced Balance Tracking** |
| pending_balance | ❌ | ✅ | **Core** | Track processing funds |
| reserved_balance | ❌ | ✅ | **Core** | Hold for pending ops |
| available_balance property | ❌ | ✅ | **Core** | Computed balance |
| total_balance property | ❌ | ✅ | **Core** | Include pending |
| **Alerts** |
| low_balance_threshold | ✅ | ✅ | Tie | Both have |
| low_balance_alert_enabled | ✅ | ❌ | **Shared** | Toggle alerts |
| is_low_balance property | ✅ | ❌ | **Shared** | Computed check |
| **Status Management** |
| WalletStatus enum | ✅ | ✅ | Tie | Both have |
| Suspend/activate methods | ✅ | ❌ | **Shared** | Built-in |
| **Timestamps** |
| created_at, updated_at | ✅ | ✅ | Tie | Both have |
| last_transaction_at | ❌ | ✅ | **Core** | Track activity |

**Winner**: **Hybrid** - Combine Core's advanced balance tracking with Shared's alerting

---

### Transaction Model

| Feature | Shared | Core | Winner | Reason |
|---------|--------|------|--------|--------|
| **Basic Fields** |
| id, wallet_id, amount, currency | ✅ | ✅ | Tie | Both have |
| Decimal precision | ✅ | ⚠️ | **Shared** | Core converts to float |
| user_id denormalized | ❌ | ✅ | **Core** | Faster queries |
| tenant_id | ❌ | ✅ | **Core** | Multi-tenancy |
| **Transaction Details** |
| TransactionType enum | ✅ | ✅ | Tie | Both have |
| TransactionStatus enum | ✅ | ✅ | Tie | Both have |
| description field | ✅ | ✅ | Tie | Both have |
| **Fees** |
| processing_fee field | ❌ | ✅ | **Core** | Track provider fees |
| total_amount field | ❌ | ✅ | **Core** | Include fees |
| **Balance Reconciliation** |
| balance_before field | ✅ | ✅ | Tie | Both have |
| balance_after field | ✅ | ✅ | Tie | Both have |
| **Provider Integration** |
| payment_method_id | ❌ | ✅ | **Core** | Link to payment method |
| payment_provider | ❌ | ✅ | **Core** | Track provider |
| provider_transaction_id | ✅ | ✅ | Tie | Both have |
| provider_response | ❌ | ✅ | **Core** | Full provider data |
| **Idempotency** |
| idempotency_key | ✅ | ❌ | **Shared** | Prevent duplicates |
| reference field | ✅ | ✅ | Tie | Both have |
| **Failure Tracking** |
| failure_reason | ✅ | ✅ | Tie | Both have |
| failed_at timestamp | ✅ | ✅ | Tie | Both have |
| retry_count | ❌ | ❌ | **Add New** | Track retries |
| **Timestamps** |
| created_at, updated_at | ✅ | ✅ | Tie | Both have |
| completed_at | ✅ | ✅ | Tie | Both have |

**Winner**: **Hybrid** - Core's fields + Shared's idempotency

---

### Payment Method Model

| Feature | Shared | Core | Winner | Reason |
|---------|--------|------|--------|--------|
| **Basic Structure** |
| Exists | ❌ | ✅ | **Core** | Shared doesn't have |
| id, user_id, provider | N/A | ✅ | **Core** | Essential |
| tenant_id | N/A | ✅ | **Core** | Multi-tenancy |
| **Provider Integration** |
| provider_payment_method_id | N/A | ✅ | **Core** | Stripe pm_xxx |
| provider_customer_id | N/A | ✅ | **Core** | Stripe cus_xxx |
| **Card Details** |
| card_last4, card_brand | N/A | ✅ | **Core** | Display info |
| card_exp_month, card_exp_year | N/A | ✅ | **Core** | Expiry tracking |
| **Mobile Money** |
| phone_number | N/A | ✅ | **Core** | MoMo number |
| phone_number_masked | N/A | ⚠️ | **Add** | Security |
| network (MTN, Vodafone) | N/A | ✅ | **Core** | Provider type |
| **Bank Account** |
| bank_name, account_last4 | N/A | ✅ | **Core** | Bank transfers |
| **Status** |
| is_active, is_default | N/A | ✅ | **Core** | Management |
| is_verified | N/A | ✅ | **Core** | Verification status |
| **Timestamps** |
| created_at, updated_at | N/A | ✅ | **Core** | Tracking |
| last_used_at | N/A | ✅ | **Core** | Activity tracking |

**Winner**: **Core** - Shared doesn't have payment method model

---

### Provider Config Model

| Feature | Shared | Core | Winner | Reason |
|---------|--------|------|--------|--------|
| **Basic Structure** |
| Exists | ❌ | ✅ | **Core** | Shared has hardcoded |
| id, provider enum | N/A | ✅ | **Core** | Essential |
| **Credentials** |
| api_key, secret_key | N/A | ✅ | **Core** | API auth |
| webhook_secret | N/A | ✅ | **Core** | Verification |
| **URLs** |
| webhook_url | N/A | ✅ | **Core** | Callback URL |
| redirect_url | N/A | ✅ | **Core** | User redirect |
| **Fee Configuration** |
| fee_config dict | N/A | ✅ | **Core** | Database fees |
| Hardcoded fees | ✅ | ❌ | **Bad** | Shared uses hardcode |
| **Settings** |
| is_active flag | N/A | ✅ | **Core** | Enable/disable |
| is_test_mode flag | N/A | ✅ | **Core** | Sandbox mode |
| settings dict | N/A | ✅ | **Core** | Flexible config |

**Winner**: **Core** - Shared doesn't have provider config model

---

### Webhook Event Model

| Feature | Shared | Core | Winner | Reason |
|---------|--------|------|--------|--------|
| **Basic Structure** |
| Exists | ❌ | ✅ | **Core** | Shared doesn't have |
| id, provider, event_type | N/A | ✅ | **Core** | Essential |
| **Payload** |
| raw_payload | N/A | ✅ | **Core** | Full webhook data |
| headers | N/A | ✅ | **Core** | Debug info |
| **Verification** |
| verification_signature | N/A | ✅ | **Core** | Signature check |
| is_verified | N/A | ✅ | **Core** | Verification status |
| **Processing** |
| is_processed | N/A | ✅ | **Core** | Processing status |
| processing_attempts | N/A | ✅ | **Core** | Retry tracking |
| processing_error | N/A | ✅ | **Core** | Error logging |
| transaction_id | N/A | ✅ | **Core** | Link to txn |
| **Timestamps** |
| created_at, processed_at | N/A | ✅ | **Core** | Tracking |

**Winner**: **Core** - Shared doesn't have webhook event model

---

## Service Features Comparison

### Payment Provider Integration

| Provider | Shared | Core | Winner | Notes |
|----------|--------|------|--------|-------|
| **Stripe** | ❌ | ✅ | **Core** | Full implementation with stripe_client.py |
| **Flutterwave** | ❌ | ✅ | **Core** | Cards + mobile money |
| **Paystack** | ✅ | ❌ | **Shared** | Complete implementation |
| **MTN Mobile Money** | ❌ | ⚠️ | **Partial** | Core has via Flutterwave only |
| **Vodafone Cash** | ❌ | ⚠️ | **Partial** | Core has via Flutterwave only |
| **AirtelTigo Money** | ❌ | ⚠️ | **Partial** | Core has via Flutterwave only |
| **M-Pesa** | ❌ | ⚠️ | **Partial** | Core has basic implementation |

**Winner**: **Core** for architecture, **Shared** for Paystack

---

### Wallet Operations

| Operation | Shared | Core | Winner | Reason |
|-----------|--------|------|--------|--------|
| **Create Wallet** |
| Create wallet | ✅ | ✅ | Tie | Both have |
| Get or create | ❌ | ✅ | **Core** | Better pattern |
| Initial balance support | ✅ | ❌ | **Shared** | Can start with balance |
| **Balance Operations** |
| Credit (add money) | ✅ | ❌ | **Shared** | Explicit method |
| Debit (subtract money) | ✅ | ❌ | **Shared** | Explicit method |
| Update balance | ❌ | ✅ | **Core** | Generic method |
| Allow negative balance | ✅ | ❌ | **Shared** | Optional feature |
| **Refunds** |
| Full refund | ✅ | ❌ | **Shared** | Complete implementation |
| Partial refund | ✅ | ❌ | **Shared** | Flexible refunds |
| **Status Management** |
| Suspend wallet | ✅ | ❌ | **Shared** | Built-in |
| Activate wallet | ✅ | ❌ | **Shared** | Built-in |
| **Transaction History** |
| Get transactions | ✅ | ✅ | Tie | Both have |
| Filter by type | ✅ | ❌ | **Shared** | Better filtering |
| Filter by date range | ✅ | ❌ | **Shared** | Date filtering |
| Filter by status | ✅ | ❌ | **Shared** | Status filtering |
| Pagination | ✅ | ✅ | Tie | Both have |

**Winner**: **Hybrid** - Shared has better operations, Core has better patterns

---

### Transaction Safety

| Feature | Shared | Core | Winner | Reason |
|---------|--------|------|--------|--------|
| **Idempotency** |
| Idempotency keys | ✅ | ❌ | **Shared** | Prevent duplicates |
| Duplicate detection | ✅ | ❌ | **Shared** | Check before insert |
| Return existing | ✅ | ❌ | **Shared** | Safe retry |
| **Atomicity** |
| MongoDB transactions | ❌ | ❌ | **Add New** | Neither has |
| Balance reconciliation | ✅ | ✅ | Tie | Both track |
| **Validation** |
| Amount validation | ✅ | ⚠️ | **Shared** | Pydantic validators |
| Balance validation | ✅ | ✅ | Tie | Both check |
| Currency validation | ✅ | ✅ | Tie | Both have enum |

**Winner**: **Shared** for safety, but need to add atomicity

---

### Webhook Handling

| Feature | Shared | Core | Winner | Reason |
|---------|--------|------|--------|--------|
| **Verification** |
| Stripe signature | ❌ | ✅ | **Core** | Real Stripe SDK |
| Flutterwave signature | ❌ | ✅ | **Core** | Hash validation |
| Paystack signature | ✅ | ❌ | **Shared** | HMAC verification |
| Generic verification | ❌ | ❌ | **Add New** | Need fallback |
| **Processing** |
| Event logging | ❌ | ✅ | **Core** | WebhookEvent model |
| Process webhooks | ❌ | ✅ | **Core** | Full system |
| Provider routing | ❌ | ✅ | **Core** | Switch by provider |
| **Error Handling** |
| Retry logic | ❌ | ❌ | **Add New** | Neither has |
| Error logging | ❌ | ✅ | **Core** | processing_error field |
| Manual retry | ❌ | ❌ | **Add New** | Need admin tool |

**Winner**: **Core** - much more comprehensive

---

### Payment Method Management

| Feature | Shared | Core | Winner | Reason |
|---------|--------|------|--------|--------|
| **CRUD Operations** |
| Add payment method | ❌ | ✅ | **Core** | Full implementation |
| Get payment methods | ❌ | ✅ | **Core** | List methods |
| Set default | ❌ | ✅ | **Core** | Default selection |
| Delete/deactivate | ❌ | ✅ | **Core** | Soft delete |
| **Auto-Default** |
| First method default | ❌ | ✅ | **Core** | Good UX |
| **Validation** |
| Provider validation | ❌ | ✅ | **Core** | Enum validation |
| Type validation | ❌ | ✅ | **Core** | Card/MoMo/Bank |

**Winner**: **Core** - Shared doesn't have this feature

---

### Notifications

| Feature | Shared | Core | Winner | Reason |
|---------|--------|------|--------|--------|
| **Email Notifications** |
| Deposit success email | ❌ | ✅ | **Core** | HTML template |
| Low balance alert | ❌ | ✅ | **Core** | Email template |
| Notification service | ❌ | ✅ | **Core** | Dedicated service |
| **SMS Notifications** |
| Mobile money SMS | ❌ | ✅ | **Core** | SMS support |
| SMS service | ❌ | ✅ | **Core** | Twilio integration |
| **Templates** |
| HTML email templates | ❌ | ✅ | **Core** | Professional design |
| SMS templates | ❌ | ✅ | **Core** | Text templates |

**Winner**: **Core** - Shared has no notifications

---

### Provider Configuration

| Feature | Shared | Core | Winner | Reason |
|---------|--------|------|--------|--------|
| **Storage** |
| Database config | ❌ | ✅ | **Core** | provider_configs table |
| Environment vars | ✅ | ✅ | Tie | Both support |
| Hardcoded config | ✅ | ❌ | **Bad** | Shared has hardcode |
| **Management** |
| Enable/disable provider | ❌ | ✅ | **Core** | is_active flag |
| Test mode | ❌ | ✅ | **Core** | Sandbox support |
| Dynamic config | ❌ | ✅ | **Core** | No code changes |
| **Fee Configuration** |
| Database fees | ❌ | ⚠️ | **Partial** | Core has field but uses hardcode |
| Per-provider fees | ❌ | ✅ | **Core** | In provider_configs |
| Fee caps | ❌ | ❌ | **Add New** | Neither has |

**Winner**: **Core** - much better architecture

---

## Code Quality Comparison

| Aspect | Shared | Core | Winner | Reason |
|--------|--------|------|--------|--------|
| **Type Safety** |
| Type hints | ✅ | ✅ | Tie | Both have |
| Pydantic models | ✅ | ✅ | Tie | Both use |
| Enum types | ✅ | ✅ | Tie | Both use |
| **Error Handling** |
| Custom exceptions | ❌ | ⚠️ | **Add New** | Use ValueError |
| Error messages | ✅ | ✅ | Tie | Both good |
| Try/except blocks | ✅ | ✅ | Tie | Both have |
| **Logging** |
| Structured logging | ✅ | ✅ | Tie | Both use logger |
| Log levels | ✅ | ✅ | Tie | Info/warning/error |
| Context in logs | ⚠️ | ✅ | **Core** | More context |
| **Documentation** |
| Docstrings | ✅ | ✅ | Tie | Both have |
| Type annotations | ✅ | ✅ | Tie | Both have |
| Usage examples | ✅ | ⚠️ | **Shared** | Better examples |
| **Code Organization** |
| Single file | ✅ | ❌ | **Bad** | 990 lines |
| Multiple files | ❌ | ✅ | **Core** | Better structure |
| Service separation | ❌ | ✅ | **Core** | Clean separation |

**Winner**: **Core** for structure, **Shared** for examples

---

## Missing Features (Neither Implementation Has)

### Critical Missing Features

1. **Transaction Atomicity**
   - Neither uses MongoDB transactions
   - Race condition risk on balance updates
   - Need to implement with `start_session()` and `start_transaction()`

2. **Webhook Retry Logic**
   - No automatic retry on failure
   - Transient errors cause permanent failures
   - Need exponential backoff retry queue

3. **Fraud Detection**
   - No velocity checks (deposits/hour)
   - No amount limits
   - No card testing detection
   - No geographic anomaly detection

4. **Rate Limiting**
   - No rate limits on API endpoints
   - Could be abused for card testing
   - Need slowapi or similar

5. **Monitoring & Metrics**
   - No Prometheus metrics
   - No transaction success rate tracking
   - No performance monitoring
   - No alerting

6. **Health Checks**
   - No health check endpoint
   - No provider connectivity tests
   - No service status monitoring

7. **Direct Mobile Money APIs**
   - Both rely on aggregators (Flutterwave)
   - No direct MTN MoMo API integration
   - No direct Vodafone Cash API
   - No direct AirtelTigo API

8. **Admin Tools**
   - No admin dashboard
   - No manual transaction retry
   - No fraud review interface
   - No failed webhook review

---

## Consolidation Strategy

### Phase 1: Models (Use Core + Enhancements)

```python
# Keep from Core:
- Wallet model + pending/reserved balances
- Transaction model + fees + provider details
- PaymentMethod model (complete)
- ProviderConfig model
- WebhookEvent model

# Add from Shared:
- Idempotency support in Transaction
- Low balance alerting in Wallet
- Refund tracking in Transaction

# Add New:
- retry_count in Transaction
- Custom exceptions module
```

### Phase 2: Providers (Plugin Architecture)

```python
# Create base interface:
BasePaymentProvider (abstract class)

# Implement providers:
- StripeProvider (from Core, enhanced)
- FlutterwaveProvider (from Core)
- PaystackProvider (from Shared, enhanced)
- MTNMoMoProvider (new, direct API)
- VodafoneProvider (new, direct API)
- AirtelTigoProvider (new, direct API)
- MPesaProvider (from Core, enhanced)
```

### Phase 3: Core Service (Hybrid)

```python
# Use Core's architecture:
- Payment method management
- Provider configuration system
- Webhook handling system
- Notification system

# Add Shared's features:
- Idempotency handling
- Better transaction filtering
- Refund system
- Suspend/activate methods

# Add new features:
- Transaction atomicity (MongoDB transactions)
- Fraud detection service
- Webhook retry queue
- Rate limiting
- Monitoring/metrics
```

### Phase 4: Migration Path

```python
# For core_backend:
1. Install new shared library
2. Update imports
3. Migrate data if schemas changed
4. Test all endpoints
5. Deploy

# For other apps:
1. Import from shared
2. Configure providers
3. Use WalletService
```

---

## Recommendation

**Use Core as Base Architecture + Shared's Best Features + New Enhancements**

### Why Core as Base:
1. ✅ Better code organization (multiple files)
2. ✅ More complete models (payment methods, provider configs)
3. ✅ Production-ready webhook system
4. ✅ Notification system
5. ✅ Multi-tenancy support

### What to Add from Shared:
1. ✅ Idempotency system (critical for safety)
2. ✅ Better transaction filtering
3. ✅ Refund functionality
4. ✅ Suspend/activate wallet methods
5. ✅ Paystack integration
6. ✅ Better documentation/examples

### What to Build New:
1. ✅ Transaction atomicity (MongoDB transactions)
2. ✅ Webhook retry queue
3. ✅ Fraud detection service
4. ✅ Rate limiting
5. ✅ Monitoring/metrics
6. ✅ Direct mobile money APIs
7. ✅ Health check endpoint
8. ✅ Custom exceptions

---

**Next Step**: Start building enhanced shared library with this plan.
