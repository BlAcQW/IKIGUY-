

# End-to-End (E2E) Tests for AI Services

E2E tests verify complete user journeys from frontend through backend to external services and back. These tests ensure the entire system works together as users would interact with it.

## What are E2E Tests?

E2E tests validate:
- **Complete User Flows**: From user action → API → database → external service → response
- **Cross-Component Integration**: Frontend, backend, database, external services working together
- **Real-World Scenarios**: Actual user workflows and edge cases
- **Error Recovery**: How the system handles failures and recovers
- **Performance**: Response times and degradation detection

## Test Coverage

### TTS E2E Tests (`test_tts_e2e.py`)
Tests complete TTS user workflows:
- **TTS Synthesis Flow** - Load providers → select → synthesize → receive audio
- **Voice Cloning Flow** - Upload audio → validate → clone → synthesize
- **Provider Switching** - Switch between providers mid-session
- **Error Recovery** - Handle failures with retry and fallback
- **Offline Provider Fallback** - Automatic fallback to secondary provider

**Coverage:** 10+ tests covering critical TTS user journeys

### LLM E2E Tests (`test_llm_e2e.py`)
Tests complete LLM user workflows:
- **Generation Flow** - Select model → submit prompt → generate → display
- **Streaming Generation** - Real-time token streaming to frontend
- **Function Calling** - LLM triggers functions → execute → return result
- **Context Management** - Multi-turn conversations with context
- **Model Auto-Loading** - Automatic model loading when not available
- **Context Length Handling** - Automatic prompt truncation

**Coverage:** 10+ tests covering critical LLM user journeys

### ASR & Health Monitoring E2E Tests (`test_asr_health_e2e.py`)
Tests ASR transcription and health monitoring:
- **Transcription Flow** - Upload audio → validate → transcribe → display
- **Word Timestamps** - Interactive transcript with playback sync
- **Speaker Diarization** - Identify and label different speakers
- **Health Monitoring** - Periodic checks → detect offline → alert
- **Performance Degradation** - Detect slow responses → mark degraded
- **Auto-Recovery** - Detect recovery → update status
- **Load Balancing** - Distribute requests across providers

**Coverage:** 10+ tests covering ASR and monitoring flows

## Running E2E Tests

### Run All E2E Tests

```bash
pytest apps/shared/integration/ai_services/tests/e2e/ -v
```

### Run Specific Test Module

```bash
# TTS E2E tests
pytest apps/shared/integration/ai_services/tests/e2e/test_tts_e2e.py -v

# LLM E2E tests
pytest apps/shared/integration/ai_services/tests/e2e/test_llm_e2e.py -v

# ASR & Health E2E tests
pytest apps/shared/integration/ai_services/tests/e2e/test_asr_health_e2e.py -v
```

### Run Specific Test Class

```bash
pytest apps/shared/integration/ai_services/tests/e2e/test_tts_e2e.py::TestTTSSynthesisE2E -v
```

### Run with Detailed Output

```bash
pytest apps/shared/integration/ai_services/tests/e2e/ -vv -s
```

## Test Structure

### TTS E2E Tests

```
TestTTSSynthesisE2E
├── test_complete_tts_synthesis_flow
│   └── Load providers → Select → Synthesize → Receive audio
└── test_tts_synthesis_with_offline_provider_fallback
    └── Primary offline → Fallback to secondary → Success

TestTTSVoiceCloningE2E
└── test_complete_voice_cloning_flow
    └── Upload → Validate → Save → Clone → Synthesize

TestTTSProviderSwitchingE2E
└── test_switch_provider_mid_session
    └── Use provider A → Switch to B → Both work

TestTTSErrorRecoveryE2E
├── test_synthesis_error_with_retry
│   └── Fail → Retry → Success
└── test_invalid_request_with_clear_error_message
    └── Invalid → Error → Correct → Success
```

### LLM E2E Tests

```
TestLLMGenerationE2E
├── test_complete_llm_generation_flow
│   └── Load models → Select → Generate → Display
└── test_llm_streaming_generation_flow
    └── Enable streaming → Stream chunks → Complete

TestLLMFunctionCallingE2E
└── test_function_calling_flow
    └── Prompt → Function call → Execute → Final response

TestLLMContextManagementE2E
└── test_multi_turn_conversation_flow
    └── Message 1 → Response 1 → Message 2 (with context) → Response 2

TestLLMErrorHandlingE2E
├── test_model_not_loaded_with_auto_load
│   └── Not loaded → Auto-load → Retry → Success
└── test_context_length_exceeded_with_truncation
    └── Too long → Truncate → Retry → Success with warning
```

### ASR & Health E2E Tests

```
TestASRTranscriptionE2E
├── test_complete_asr_transcription_flow
│   └── Upload → Validate → Transcribe → Display
├── test_asr_with_word_timestamps_flow
│   └── Enable timestamps → Transcribe → Sync playback
└── test_asr_with_speaker_diarization_flow
    └── Enable diarization → Identify speakers → Label

TestHealthMonitoringE2E
├── test_provider_health_monitoring_flow
│   └── Check all → Detect offline → Alert → Display
├── test_provider_performance_degradation_detection
│   └── Monitor → Detect slow → Mark degraded → Warn
└── test_provider_auto_recovery_flow
    └── Offline → Keep checking → Recover → Notify

TestMultiProviderE2E
└── test_load_balancing_across_providers
    └── Multiple requests → Balance load → All succeed
```

## E2E Test Patterns

### Pattern 1: Complete User Flow

Test the entire journey from start to finish:

```python
@pytest.mark.asyncio
async def test_complete_flow(self):
    """
    1. Frontend: User action
    2. Backend: Validation
    3. Backend: Process
    4. Database: Save
    5. External Service: Call
    6. Backend: Response
    7. Frontend: Display
    """
    # Step 1: User action
    user_input = {"text": "Hello"}

    # Step 2-3: Backend validation and processing
    validated = validate(user_input)

    # Step 4: Database save (simulated)
    record = save_to_db(validated)

    # Step 5: External service call
    result = await call_external_service(validated)

    # Step 6-7: Return and display
    assert result["success"] is True
```

### Pattern 2: Error Recovery

Test how the system recovers from failures:

```python
@pytest.mark.asyncio
async def test_error_recovery(self):
    """
    1. First attempt fails
    2. Detect failure
    3. Retry with backoff
    4. Success on retry
    """
    call_count = 0

    async def mock_with_retry():
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            raise Exception("Transient error")
        return {"success": True}

    # Simulate retry logic
    try:
        result = await mock_with_retry()
    except Exception:
        await asyncio.sleep(0.1)
        result = await mock_with_retry()

    assert result["success"] is True
    assert call_count == 2
```

### Pattern 3: Provider Fallback

Test fallback to alternative providers:

```python
@pytest.mark.asyncio
async def test_provider_fallback(self):
    """
    1. Try primary provider
    2. Primary offline
    3. Fallback to secondary
    4. Success with secondary
    """
    # Check primary
    primary_status = await check_provider("primary")

    if primary_status == "offline":
        # Fallback to secondary
        result = await use_provider("secondary")
    else:
        result = await use_provider("primary")

    assert result["success"] is True
```

### Pattern 4: Multi-Step Workflow

Test complex multi-step workflows:

```python
@pytest.mark.asyncio
async def test_multi_step_workflow(self):
    """
    1. Step 1: Upload file
    2. Step 2: Process file
    3. Step 3: Generate output
    4. Step 4: Save result
    5. Step 5: Notify user
    """
    # Step 1
    upload_result = await upload_file()
    assert upload_result["success"] is True

    # Step 2
    process_result = await process_file(upload_result["file_id"])
    assert process_result["status"] == "completed"

    # Step 3-5
    # ... continue through all steps
```

## Critical User Flows Tested

### ✅ TTS Flows
1. **Basic Synthesis** - Text → Audio (happy path)
2. **Voice Cloning** - Audio sample → Cloned voice → Synthesis
3. **Provider Fallback** - Primary offline → Secondary success
4. **Error Recovery** - Transient error → Retry → Success
5. **Invalid Input** - Bad request → Clear error → Correction → Success

### ✅ LLM Flows
1. **Basic Generation** - Prompt → Response (happy path)
2. **Streaming** - Prompt → Real-time chunks → Complete
3. **Function Calling** - Prompt → Function → Execute → Final response
4. **Multi-Turn** - Message 1 → Response 1 → Message 2 (context) → Response 2
5. **Model Loading** - Not loaded → Auto-load → Generate
6. **Context Management** - Long prompt → Truncate → Generate with warning

### ✅ ASR Flows
1. **Basic Transcription** - Audio → Text (happy path)
2. **Word Timestamps** - Audio → Text with word-level timing
3. **Diarization** - Audio → Text with speaker labels
4. **Large Files** - Upload → Validate → Process → Result

### ✅ Health Monitoring Flows
1. **Status Monitoring** - Check all → Update statuses → Display
2. **Degradation Detection** - Slow response → Mark degraded → Warn
3. **Offline Detection** - Check → Offline → Alert
4. **Auto-Recovery** - Offline → Keep checking → Online → Notify
5. **Load Balancing** - Multiple requests → Balance → All succeed

## E2E Test Best Practices

### 1. Test Real User Journeys

Test how users actually use the system:

```python
# ✅ Good - Tests actual user workflow
async def test_user_creates_voiceover_for_video(self):
    # User writes script
    script = "Welcome to my video"

    # User selects voice
    voice = "professional_male"

    # User generates audio
    audio = await generate_audio(script, voice)

    # User downloads
    assert audio["url"].endswith(".mp3")
```

### 2. Test Error Paths

Test how the system handles failures:

```python
# ✅ Good - Tests error recovery
async def test_synthesis_fails_then_succeeds(self):
    # First attempt fails
    with pytest.raises(ServiceUnavailable):
        await synthesize("text", provider="offline_provider")

    # Retry with different provider succeeds
    result = await synthesize("text", provider="backup_provider")
    assert result["success"] is True
```

### 3. Test Cross-Component Integration

Test multiple components working together:

```python
# ✅ Good - Tests frontend → backend → external service
async def test_complete_integration(self):
    # Frontend submits request
    request = {"text": "Hello"}

    # Backend validates
    validated = backend.validate(request)

    # Backend calls external service
    result = await backend.call_tts_service(validated)

    # Frontend receives response
    assert result["audio_url"] is not None
```

### 4. Use Realistic Data

Use data that reflects real usage:

```python
# ✅ Good - Realistic test data
test_data = {
    "text": "Welcome to our product demo. In this video, we'll show you...",
    "language": "en",
    "voice": "professional_female",
    "speed": 1.0,
}
```

### 5. Test Performance Scenarios

Test system behavior under load:

```python
# ✅ Good - Tests load balancing
async def test_load_balancing_with_multiple_requests(self):
    # Submit 10 requests
    requests = [create_request(i) for i in range(10)]

    # Process all
    results = await asyncio.gather(*[process(r) for r in requests])

    # All succeed
    assert all(r["success"] for r in results)

    # Load was balanced
    assert provider_load_is_balanced()
```

## Debugging E2E Tests

### View Detailed Output

```bash
pytest apps/shared/integration/ai_services/tests/e2e/ -vv -s
```

### Run Single Test with Debugging

```bash
pytest apps/shared/integration/ai_services/tests/e2e/test_tts_e2e.py::TestTTSSynthesisE2E::test_complete_tts_synthesis_flow -vv -s --pdb
```

### Check Test Logs

```bash
pytest apps/shared/integration/ai_services/tests/e2e/ -v --log-cli-level=DEBUG
```

## CI/CD Integration

E2E tests should run:
- ✅ Before major releases
- ✅ On staging environment
- ✅ After significant changes
- ⚠️ Can be slow - consider running subset on PRs

### CI/CD Example

```yaml
# .github/workflows/e2e-tests.yml
- name: Run E2E Tests
  run: |
    pytest apps/shared/integration/ai_services/tests/e2e/ \
      --maxfail=5 \
      --tb=short \
      -v
```

## Performance Considerations

E2E tests can be slow because they test complete flows:

### Optimization Strategies

1. **Run in Parallel**
   ```bash
   pytest apps/shared/integration/ai_services/tests/e2e/ -n auto
   ```

2. **Run Critical Tests Only on PRs**
   ```bash
   pytest apps/shared/integration/ai_services/tests/e2e/ -m critical
   ```

3. **Run Full Suite Nightly**
   - Critical tests: On every PR
   - Full suite: Nightly builds

4. **Use Mocking for External Services**
   - Mock external AI services (Ollama, Whisper, etc.)
   - Test actual HTTP calls but mock external responses

## Test Data Management

### Use Fixtures for Common Data

```python
@pytest.fixture
def sample_audio_file():
    return {
        "filename": "test.mp3",
        "content_type": "audio/mp3",
        "size": 1024000,
    }

@pytest.fixture
def sample_user():
    return {"id": "user_123", "email": "test@example.com"}
```

### Clean Up Test Data

```python
@pytest.fixture
async def test_user(db):
    # Create test user
    user = await db.users.create({"email": "test@example.com"})

    yield user

    # Cleanup
    await db.users.delete(user.id)
```

## Related Documentation

- [QA Strategy](../../../../../architecture/QA_STRATEGY.md) - Overall testing strategy
- [Integration Tests](../integration/README.md) - Component integration tests
- [Contract Tests](../contract/README.md) - API contract tests
- [Unit Tests](../README.md) - Unit testing guidelines

## E2E Test Checklist

When adding new E2E tests:

- [ ] Test complete user journey from start to finish
- [ ] Test happy path
- [ ] Test error scenarios and recovery
- [ ] Test provider fallback
- [ ] Test performance degradation
- [ ] Use realistic test data
- [ ] Mock external services appropriately
- [ ] Add cleanup for test data
- [ ] Document what user flow is being tested
- [ ] Add to CI/CD pipeline

## Summary

E2E tests are critical for:
- ✅ **Confidence**: Ensure the system works as users expect
- ✅ **Integration**: Verify all components work together
- ✅ **Regression**: Catch issues before users do
- ✅ **Documentation**: Serve as examples of user workflows
- ✅ **Quality**: Ensure production-ready features

Run E2E tests regularly on staging environments before deploying to production. They provide the highest confidence that the system works correctly from a user's perspective.

**Total E2E Tests:** 30+ tests covering critical user journeys across TTS, LLM, ASR, and Health Monitoring.
