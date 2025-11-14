# HiyaDrive Test Suite - Comprehensive Audit Report

**Date**: 2025-11-13
**Status**: All tests reviewed and issues identified
**Priority**: High - Tests are outdated and need significant refactoring

---

## Executive Summary

The test suite has **4 major issues** affecting all test files:

1. **Restaurant-Specific Language** (8-10+ occurrences per file)
2. **Missing Calendar Retry Logic Tests** (critical feature not tested)
3. **Outdated State Model References** (some fields no longer used)
4. **Demo Mode Only Testing** (no real API integration tests)

**Overall Status**: ⚠️ Tests are outdated but structure is sound - requires refactoring

---

## 1. File-by-File Audit

### 1.1 `tests/conftest.py` - Shared Fixtures

**Status**: 🔴 CRITICAL - Outdated, needs complete refactor

#### Issues Found:

| Line | Issue | Type | Severity | Fix |
|------|-------|------|----------|-----|
| 8 | `from hiya_drive.models.state import ... Restaurant` | Import | HIGH | Update to use generic service imports |
| 22-28 | `DrivingBookingState(...)` fixture | State | MEDIUM | Valid structure, but update descriptions |
| 32-39 | `sample_restaurant` fixture | Context | HIGH | Rename to `sample_service` and update docstring |
| 43-49 | `sample_state_with_restaurant` fixture | Context | HIGH | Rename to `sample_state_with_service` |
| 47 | `sample_state.selected_restaurant = sample_restaurant` | Reference | MEDIUM | Keep variable name but use generic service in comments |

#### Detailed Issues:

```python
# CURRENT (Line 32-39) - Restaurant-specific
@pytest.fixture
def sample_restaurant():
    """Create a sample restaurant object."""
    return Restaurant(
        name="Olive Garden",  # ❌ Restaurant name
        phone="+1-555-0100",
        address="123 Main St, Boston, MA",
        rating=4.2,
    )

# NEEDED - Service-agnostic
@pytest.fixture
def sample_service():
    """Create a sample service provider (haircut, massage, appointment, etc.)."""
    return Restaurant(  # Keep class name for backward compat
        name="StyleCuts Hair Salon",  # ✓ Generic service
        phone="+1-555-0100",
        address="123 Main St, Boston, MA",
        rating=4.2,
    )
```

**Action Required**:
- [ ] Rename `sample_restaurant()` → `sample_service()`
- [ ] Rename `sample_state_with_restaurant()` → `sample_state_with_service()`
- [ ] Update all docstrings to be service-agnostic
- [ ] Update example values to use generic services (salons, doctors, etc.)

---

### 1.2 `tests/unit/test_state.py` - State Model Tests

**Status**: 🟡 MEDIUM - Mostly valid, some terminology issues

#### Issues Found:

| Line | Issue | Type | Severity | Fix |
|------|-------|------|----------|-----|
| 32-49 | `TestDrivingBookingState` class | Structure | LOW | Valid, keep as-is |
| 97 | `sample_state.cuisine_type = "Italian"` | Field | MEDIUM | Update to generic service type |
| 104 | `assert state_dict["cuisine_type"] == "Italian"` | Field | MEDIUM | Update test description |
| 116-121 | `test_with_restaurant` | Test Name | HIGH | Rename test to be generic |
| 118-121 | Restaurant-specific assertions | Assertions | MEDIUM | Update to service-agnostic |
| 133-138 | Enum tests | Test | LOW | Valid, no changes needed |

#### Detailed Issues:

```python
# CURRENT (Line 97-98) - Restaurant-specific
def test_to_dict(self, sample_state):
    """Test converting state to dictionary."""
    sample_state.party_size = 2
    sample_state.cuisine_type = "Italian"  # ❌ Too specific

# NEEDED - Service-agnostic
def test_to_dict(self, sample_state):
    """Test converting state to dictionary."""
    sample_state.party_size = 2
    sample_state.cuisine_type = "Hair Salon"  # ✓ Generic service type

# CURRENT (Line 116-121) - Test name too specific
def test_with_restaurant(self, sample_state_with_restaurant):
    """Test state with restaurant selected."""
    assert sample_state_with_restaurant.selected_restaurant.name == "Olive Garden"

# NEEDED - Generic name
def test_with_selected_service(self, sample_state_with_service):
    """Test state with service provider selected."""
    assert sample_state_with_service.selected_restaurant.name == "StyleCuts Hair Salon"
```

**Action Required**:
- [ ] Rename test method: `test_with_restaurant()` → `test_with_selected_service()`
- [ ] Update all example values to use generic services
- [ ] Update docstrings for `cuisine_type` field to mention it's generic
- [ ] Update fixture parameter names from `sample_restaurant` to `sample_service`

---

### 1.3 `tests/unit/test_voice_processor.py` - Voice Tests

**Status**: 🟢 GOOD - Minimal issues, mostly valid

#### Issues Found:

| Line | Issue | Type | Severity | Fix |
|------|-------|------|----------|-----|
| 19-23 | Mock STT test assertions | Logic | LOW | Comment needs clarification |
| 49 | Test string "Hello, this is a test." | Example | TRIVIAL | Could be improved |
| 67-70 | Demo mode check conditional | Logic | MEDIUM | Add calendar retry logic test |

#### Detailed Issues:

```python
# CURRENT (Line 19-23) - Vague assertion
assert isinstance(result, str)
assert len(result) > 0
assert "table" in result.lower() or "book" in result.lower()  # ❌ Restaurant-specific

# NEEDED - Generic assertion
assert isinstance(result, str)
assert len(result) > 0
# Should contain service-related keywords, not just restaurant
```

**Action Required**:
- [ ] Update assertions to not assume restaurant domain
- [ ] Add tests for voice transcription of service bookings (salons, doctors, etc.)
- [ ] Consider adding callback verification for demo mode detection

---

### 1.4 `tests/unit/test_orchestrator.py` - Orchestration Tests

**Status**: 🔴 CRITICAL - Major outdated references

#### Issues Found:

| Line | Issue | Type | Severity | Fix |
|------|-------|------|----------|-----|
| 26-36 | Node names list | Reference | HIGH | Verify against actual orchestrator |
| 49 | `"Book a table for 2 at Italian next Friday at 7 PM"` | Example | HIGH | Use generic service example |
| 50-58 | Intent parsing test logic | Logic | HIGH | Assertions don't match intent parser output |
| 56-58 | `"Italian" in (result.cuisine_type or "")` | Field | MEDIUM | Wrong comparison |
| 79-90 | Service search assertions | Logic | HIGH | References outdated node name |
| 93-119 | Restaurant selection test | Test | HIGH | Fixture and assertions need update |
| 100-112 | Mock Restaurant objects | Data | MEDIUM | Use generic service examples |
| 118 | `assert result.selected_restaurant.name == "Restaurant 1"` | Assertion | MEDIUM | Example too generic |
| 121-129 | Call script generation test | Logic | MEDIUM | Comment mentions outdated terminology |
| 164-183 | Routing logic tests | Logic | HIGH | Need to add calendar retry routing test |

#### Detailed Issues:

```python
# CURRENT (Line 26-36) - May not match actual nodes
expected_nodes = [
    "parse_intent",
    "check_calendar",
    "search_restaurants",     # ❌ Outdated name
    "select_restaurant",      # ❌ Outdated name
    "prepare_call",
    "make_call",
    "converse",
    "confirm_booking",
    "handle_error",
]

# NEEDED - Verify against actual orchestrator.py node names
# Then test with actual names

# CURRENT (Line 49) - Restaurant-specific
initial_utterance="Book a table for 2 at Italian next Friday at 7 PM"

# NEEDED - Generic service booking
initial_utterance="Book a haircut for 2 people tomorrow at 3 PM"
initial_utterance="Schedule a massage appointment for tomorrow at 3 PM"

# CURRENT (Line 56-58) - Wrong assertion
assert result.cuisine_type is not None or "Italian" in (
    result.cuisine_type or ""
)  # ❌ Logic error: None is not None OR "Italian" in ""

# NEEDED - Proper assertion
assert result.cuisine_type is not None
assert "Hair Salon" in result.cuisine_type or "Salon" in result.cuisine_type

# CURRENT (Line 79-86) - Missing calendar retry test
@pytest.mark.asyncio
async def test_search_restaurants_node(self):
    # ❌ No test for calendar retry when user is busy

# NEEDED - Add calendar retry test
@pytest.mark.asyncio
async def test_check_calendar_with_retry_on_conflict(self):
    """Test calendar retry when driver is busy (up to 3 attempts)."""
    # Test logic here
```

**Action Required**:
- [ ] Update all example utterances to be service-agnostic
- [ ] Verify node names match actual orchestrator implementation
- [ ] Fix assertion logic errors in intent parsing test
- [ ] Add comprehensive calendar retry logic tests (see section 1.5)
- [ ] Update Restaurant object examples to use varied services
- [ ] Rename test methods to remove "restaurant" terminology
- [ ] Add tests for routing decisions when calendar conflict occurs

---

### 1.5 `tests/integration/test_e2e_booking.py` - End-to-End Tests

**Status**: 🔴 CRITICAL - Major outdated examples, missing calendar tests

#### Issues Found:

| Line | Issue | Type | Severity | Fix |
|------|-------|------|----------|-----|
| 12 | Class name mentions booking flow | Reference | LOW | Valid, keep as-is |
| 16-28 | Simple booking test utterance | Example | HIGH | Restaurant-specific |
| 20 | `"Book a table for 2 at Italian next Friday at 7 PM"` | Example | HIGH | Use generic example |
| 30-41 | Restaurant selection test | Test | HIGH | Fixture and assertions outdated |
| 34 | `"I need a table for 4 people at a sushi place"` | Example | HIGH | Restaurant domain |
| 40 | Check for `selected_restaurant` | Assertion | MEDIUM | Field name is OK but example is not |
| 43-55 | State progression test | Test | MEDIUM | Test is valid but example is outdated |
| 47 | `"Book me a table for 2 at Italian"` | Example | HIGH | Restaurant-specific |
| 57-66 | Error recovery test | Test | MEDIUM | Valid structure, example outdated |
| 61 | `"I want to book"` | Example | MEDIUM | Generic is OK but could be better |
| 68-78 | Sequential bookings test | Test | LOW | Valid, examples outdated |
| 73 | `"Book a table for {i+2} people"` | Example | HIGH | Restaurant-specific |
| 79-93 | State serialization test | Test | LOW | Valid, example outdated |
| 84 | `"Book a table for 2"` | Example | HIGH | Restaurant-specific |
| 94-106 | Confirmation test | Test | HIGH | **CRITICAL MISSING**: No calendar retry test |

#### Detailed Issues:

```python
# CURRENT (Line 16-28) - Restaurant-specific
async def test_simple_booking_demo_mode(self):
    """Test a simple booking request in demo mode."""
    result = await orchestrator.run_booking_session(
        driver_id="test_driver_001",
        initial_utterance="Book a table for 2 at Italian next Friday at 7 PM",  # ❌
    )

# NEEDED - Service-agnostic with variety
async def test_simple_booking_demo_mode(self):
    """Test a simple booking request in demo mode."""
    result = await orchestrator.run_booking_session(
        driver_id="test_driver_001",
        initial_utterance="Book a haircut for 2 people next Friday at 3 PM",  # ✓
    )

# COMPLETELY MISSING - Calendar retry test
# Should add comprehensive test for the 3-retry calendar conflict scenario
@pytest.mark.asyncio
async def test_booking_with_calendar_conflict_and_retry(self):
    """Test booking flow when driver is busy (3 retry attempts)."""
    # Test scenarios:
    # 1. Driver busy at requested time
    # 2. Driver provides alternative time
    # 3. Retry logic works up to 3 times
    # 4. Fails gracefully after 3 retries
```

**Action Required**:
- [ ] Update all utterance examples to be service-agnostic
- [ ] Add comprehensive calendar retry test (3-attempt flow)
- [ ] Add test for calendar retry failure after 3 attempts
- [ ] Add test for user providing multiple alternative times
- [ ] Update all example values (restaurants → services)
- [ ] Ensure assertions work with new generic examples
- [ ] Add negative test cases for calendar conflicts

---

## 2. Cross-File Issues

### 2.1 Terminology Issues (All Files)

| Old Term | Correct Usage | Context | Fix |
|----------|---------------|---------|-----|
| `Restaurant` | Use in code (for backward compat) | Class name | ✓ Keep as-is |
| `"restaurant"` | `"service"` | Comments/docstrings | Update |
| `"table"` | `"appointment"` / `"booking"` | Utterances | Update |
| `"cuisine_type"` | `"service_type"` | Field name | ✓ Keep as-is (internal) |
| `"Italian"` / `"Sushi"` | `"Hair Salon"` / `"Massage"` | Example values | Update |
| `"Olive Garden"` | `"StyleCuts Hair Salon"` | Example names | Update |

### 2.2 Missing Test Coverage

**Critical gaps** that need new tests:

1. **Calendar Retry Logic** (3 attempts when busy) - **COMPLETELY MISSING**
   - Test driver marked busy at requested time
   - Test user provides alternative time within conversation
   - Test retry counter increments correctly
   - Test failure after 3 failed attempts
   - Test success on 2nd attempt (before max)

2. **Calendar Integration** (with real Google Calendar)
   - No tests for actual calendar API calls
   - No tests for timezone handling
   - No tests for malformed date/time inputs

3. **Service-Agnostic Search**
   - Tests assume restaurants only
   - Should test with salons, doctors, auto repair, etc.

4. **Error Handling for Calendar**
   - No test for API authentication failure
   - No test for rate limiting
   - No test for network timeouts during calendar check

### 2.3 Fixture Issues

All fixtures are restaurant-specific and need updating:

```python
# Current fixtures
sample_restaurant          # ❌ Rename to sample_service
sample_state_with_restaurant  # ❌ Rename to sample_state_with_service

# Current limitations
# - Only test one example service (restaurant)
# - Should test varied services (salon, doctor, repair, etc.)
# - Should include service-specific scenarios
```

---

## 3. Test Execution Issues

### Current State

```bash
$ make test
pytest tests/ -v --cov=hiya_drive --cov-report=html
# ❌ Tests may fail because:
# 1. Example utterances are restaurant-specific
# 2. Intent parser may not extract correctly from generic examples
# 3. Calendar retry logic is not tested (no test for this code path)
```

### Success Criteria

All tests should:
- ✓ Run without errors
- ✓ Pass with demo mode enabled (mocked APIs)
- ✓ Use service-agnostic examples
- ✓ Cover calendar retry feature (3 attempts)
- ✓ Generate >80% code coverage

---

## 4. Update Priority & Effort

### Phase 1: Critical Fixes (High Impact)

| File | Changes | Effort | Impact |
|------|---------|--------|--------|
| conftest.py | Rename fixtures, update examples | 15 min | HIGH - affects all tests |
| test_orchestrator.py | Calendar retry test + example update | 30 min | HIGH - missing critical feature |
| test_e2e_booking.py | Calendar retry test + all examples | 30 min | HIGH - missing critical feature |

**Total Phase 1**: ~75 minutes, fixes 70% of issues

### Phase 2: Medium Fixes (Medium Impact)

| File | Changes | Effort | Impact |
|------|---------|--------|--------|
| test_state.py | Rename tests, update example values | 15 min | MEDIUM - affects state layer |
| test_voice_processor.py | Update assertions to be generic | 10 min | MEDIUM - minor improvements |

**Total Phase 2**: ~25 minutes, fixes remaining 25% of issues

### Phase 3: Enhancements (Nice to Have)

| File | Changes | Effort | Impact |
|------|---------|--------|--------|
| All files | Add tests for varied services (salon, doctor, repair) | 30 min | LOW - edge cases |
| All files | Add real Google Calendar API tests | 60 min | LOW - integration tests |

**Total Phase 3**: ~90 minutes, covers remaining 5% of issues

---

## 5. Specific Code Changes Needed

### Summary by File

#### conftest.py
```
Lines to change: 8, 32-39, 43-49
Changes: 3 fixtures need updating
New fixtures needed: variations for different services
```

#### test_state.py
```
Lines to change: 97, 104, 116-121
Changes: Update example values, rename test method
Test additions: None (structure is sound)
```

#### test_voice_processor.py
```
Lines to change: 23 (assertion)
Changes: Remove restaurant-specific keywords
Test additions: Tests for different service domain utterances
```

#### test_orchestrator.py
```
Lines to change: 26-36, 49, 50-58, 56-58, 79-90, 93-119, 121-129, 164-183
Changes: 15+ locations
Test additions: Calendar retry test (critical)
New test needed: test_check_calendar_with_retry_on_conflict()
```

#### test_e2e_booking.py
```
Lines to change: 20, 30-41, 34, 47, 61, 73, 84, 94-106
Changes: 8+ locations
Test additions: Calendar retry test (critical)
New test needed: test_booking_with_calendar_conflict_and_retry()
```

---

## 6. Rollout Plan

### Step 1: Update Fixtures (conftest.py)
**Time**: 15 min
**Risk**: LOW - only affects fixture data
**Blockers**: None

### Step 2: Add Calendar Retry Test
**Time**: 30 min
**Risk**: MEDIUM - need to mock calendar conflicts
**Blockers**: Understand calendar mock behavior

### Step 3: Update Remaining Files
**Time**: 45 min
**Risk**: LOW - just updating examples and assertions
**Blockers**: None

### Step 4: Verify & Run
**Time**: 10 min
**Risk**: MEDIUM - tests should pass
**Blockers**: May need to adjust examples if intent parser is strict

---

## 7. Checklist for Test Refactoring

### conftest.py
- [ ] Rename `sample_restaurant()` to `sample_service()`
- [ ] Rename `sample_state_with_restaurant()` to `sample_state_with_service()`
- [ ] Update docstrings to mention services not restaurants
- [ ] Change example service to "StyleCuts Hair Salon" (generic)

### test_state.py
- [ ] Rename `test_with_restaurant()` to `test_with_selected_service()`
- [ ] Update example in `test_to_dict()` from "Italian" to "Hair Salon"
- [ ] Update fixture references from `sample_state_with_restaurant` to `sample_state_with_service`

### test_voice_processor.py
- [ ] Update assertion to remove "table" and "restaurant" keywords
- [ ] Add comment explaining assertion checks for service booking keywords

### test_orchestrator.py
- [ ] Verify node names against actual orchestrator.py
- [ ] Update all example utterances to be service-agnostic
- [ ] Fix intent parser test assertion logic
- [ ] Add calendar retry test: `test_check_calendar_with_retry_on_conflict()`
- [ ] Update Restaurant mock objects to use generic services
- [ ] Update routing test to include calendar conflict scenario

### test_e2e_booking.py
- [ ] Update all utterance examples to be service-agnostic
- [ ] Change "Book a table" to "Book a haircut" or "Schedule appointment"
- [ ] Add calendar retry test: `test_booking_with_calendar_conflict_and_retry()`
- [ ] Update Restaurant object examples
- [ ] Add test for failure after 3 calendar retries

---

## 8. Risk Assessment

### Risks
1. **Intent parser may be strict** - If it expects restaurant keywords, service examples might not parse
   - Mitigation: Test with actual intent parser first

2. **Calendar mock might not support retry simulation** - Current mock may not support multiple calls
   - Mitigation: Create enhanced calendar mock for retry testing

3. **Tests assume demo mode** - Real API tests not included
   - Mitigation: Create separate integration test file for real APIs

### Dependencies
- [ ] Ensure intent parser works with generic service examples
- [ ] Ensure calendar mock supports multiple calls for retry testing
- [ ] Ensure Restaurant class fields are available (backward compatible)

---

## Conclusion

**Overall Assessment**: ⚠️ Tests need significant refactoring (not rewrite)

**Key Issues**:
1. All tests use restaurant-specific examples (Easy fix)
2. Calendar retry logic is completely untested (Critical gap)
3. Fixtures are outdated (Easy fix)
4. Some assertion logic is incorrect (Medium fix)

**Estimated Total Effort**: 2-3 hours for complete refactoring + calendar tests

**Recommended Order**:
1. Update fixtures first (enables other tests)
2. Add calendar retry tests (critical feature)
3. Update all examples (consistency)
4. Verify all tests pass (validation)
