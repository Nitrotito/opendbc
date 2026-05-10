# Tesla HW1 (Model S/X 2014-16) - Improvement TODO List

## Overview

Tesla HW1 (Model S/X 2014-16) is the least capable Tesla variant for openpilot integration. This document tracks all known missing features, signals, and improvements needed to bring HW1 to parity with better-supported platforms.

**Current Status:** Legacy safety model (`teslaLegacy`), 25 Hz EPS, no checksum/counter validation, single-panda only, no external panda support.

---

## Critical Missing Signals

### 1. APS_eacMonitor (0x27d) - Steering Permission
- **Priority:** HIGH
- **Files:** `carcontroller.py:58`, `tesla_legacy.h:218-226`
- **Issue:** HW1 does not send `APS_eacMonitor` message. HW2/HW3 use this to validate steering permission. HW1 is excluded from `steering_allowed` messages entirely.
- **TODO:**
  - [ ] Investigate if APS_eacMonitor exists on HW1 at a different address or on a different bus
  - [ ] If unavailable, document the fallback steering permission mechanism
  - [ ] Add HW1-specific steering permission validation in safety layer
  - [ ] Update `carcontroller.py` to handle HW1 steering enable path

### 2. ESP_private1 (0x155) - Brake System Data
- **Priority:** MEDIUM
- **Files:** `tesla_legacy.h:259-265`
- **Issue:** HW3 receives `ESP_private1` on bus 1. HW1 chassis bus (0) does not expose this message.
- **TODO:**
  - [ ] Search HW1 DBC (`tesla_can.dbc`) for equivalent brake system signals
  - [ ] Map ESP_private1 signals to HW1 equivalents if they exist
  - [ ] Update `carstate.py` to parse HW1 brake data

### 3. BrakeMessage (0x20a) - Brake Status
- **Priority:** MEDIUM
- **Files:** `tesla_legacy.h:259-265`
- **Issue:** HW3 receives `BrakeMessage` on bus 1. Not available on HW1.
- **TODO:**
  - [ ] Find HW1 brake status message location
  - [ ] Map brake pressure, brake applied, and brake hold signals
  - [ ] Add to `carstate.py` parsing

### 4. DI_state (0x368) - Drive Inverter State
- **Priority:** MEDIUM
- **Files:** `tesla_legacy.h:259-265`
- **Issue:** HW3 receives `DI_state` on bus 1. Not available on HW1.
- **TODO:**
  - [ ] Find HW1 drive inverter state signals
  - [ ] Map gear selection, inverter status, and motor torque signals
  - [ ] Add to `carstate.py` parsing

### 5. VCRIGHT_silla2 (0x39f) - Right Seat Data
- **Priority:** LOW
- **Files:** `tesla_legacy.h`
- **Issue:** HW3 receives right seat data. Not available on HW1.
- **TODO:**
  - [ ] Determine if this signal is needed for safety features
  - [ ] If needed, find HW1 equivalent

---

## Performance Improvements

### 6. EPS Update Rate - 25 Hz to Higher
- **Priority:** HIGH
- **Files:** `carstate.py:185-188`, `tesla_legacy.h:241-249`
- **Issue:** HW1 EPAS runs at 25 Hz vs 100 Hz on HW3. This limits lateral control responsiveness.
- **TODO:**
  - [ ] Investigate if HW1 EPS can be polled at higher rate
  - [ ] If not, tune lateral controller for 25 Hz constraints
  - [ ] Add EPS rate warning in UI if below threshold
  - [ ] Consider interpolation/extrapolation for smoother control

### 7. CAN Message Address Differences
- **Priority:** MEDIUM
- **Files:** `carstate.py`, `tesla_legacy.h`, `tesla_can.dbc`
- **Issue:** DI_torque1 is at 0x108 on HW1 vs 0x106 on HW2/HW3. Requires separate parsing paths.
- **TODO:**
  - [ ] Audit all CAN message address differences between HW1 and HW2/HW3
  - [ ] Create a comprehensive address mapping table
  - [ ] Consolidate parsing logic where possible
  - [ ] Document all HW1-specific message addresses

---

## Safety Layer Improvements

### 8. Checksum and Counter Validation
- **Priority:** HIGH
- **Files:** `tesla_legacy.h:241-249`
- **Issue:** All HW1 messages have `ignore_checksum=true, ignore_counter=true`. No message integrity validation.
- **TODO:**
  - [ ] Investigate if HW1 messages have checksums at different bit positions
  - [ ] If checksums exist, implement validation in safety layer
  - [ ] If no checksums, document the risk and add runtime signal plausibility checks
  - [ ] Add counter validation where possible
  - [ ] Implement signal range checks as fallback validation

### 9. External Panda Support
- **Priority:** HIGH
- **Files:** `values.py:43-118`, `tesla_legacy.h:277-279`
- **Issue:** HW1 does not support external panda for longitudinal control. Single-panda architecture only.
- **TODO:**
  - [ ] Investigate if external panda can be added to HW1 architecture
  - [ ] If possible, implement external panda TX path for HW1
  - [ ] Update safety flags to allow `FLAG_EXTERNAL_PANDA` for HW1
  - [ ] Document hardware modifications required

### 10. TX Message Expansion
- **Priority:** MEDIUM
- **Files:** `tesla_legacy.h:228-231`
- **Issue:** HW1 only transmits `DAS_steeringControl` (0x488) and `DAS_control` (0x2b9). Missing `APS_eacMonitor` and other permission messages.
- **TODO:**
  - [ ] Identify all TX messages needed for full feature parity
  - [ ] Add missing TX messages to HW1 safety config
  - [ ] Test each TX message on HW1 hardware

---

## UI and Driver Feedback

### 11. Gap Adjust Button
- **Priority:** HIGH
- **Files:** `carstate.py:158`, `carstate.py:249`
- **Issue:** No gap adjust button detection. TODO noted in code.
- **TODO:**
  - [ ] Find gap adjust button signal in HW1 DBC
  - [ ] Add button event parsing in `carstate.py`
  - [ ] Map to `buttonEvents` in car state
  - [ ] Test button functionality on HW1 hardware

### 12. HUD Control
- **Priority:** HIGH
- **Files:** `carcontroller.py:76`
- **Issue:** HUD control not implemented. TODO noted in code.
- **TODO:**
  - [ ] Find HUD/cluster display messages in HW1 DBC
  - [ ] Implement HUD message packing in `teslacan_legacy.py`
  - [ ] Add lane lines, lead car, and speed display to HUD
  - [ ] Test on HW1 hardware

### 13. Lane Departure Warning (LDW)
- **Priority:** MEDIUM
- **Files:** `carstate.py`, `carcontroller.py`
- **Issue:** No LDW signal detection or display.
- **TODO:**
  - [ ] Find LDW signals in HW1 DBC
  - [ ] Add LDW state parsing
  - [ ] Implement LDW alert display in UI

### 14. Forward Collision Warning (FCW)
- **Priority:** MEDIUM
- **Files:** `carstate.py`, `carcontroller.py`
- **Issue:** No FCW signal detection or display.
- **TODO:**
  - [ ] Find FCW signals in HW1 DBC
  - [ ] Add FCW state parsing
  - [ ] Implement FCW alert in UI

### 15. Lead Distance Display
- **Priority:** MEDIUM
- **Files:** `carstate.py`, `carcontroller.py`
- **Issue:** No following distance bars displayed to driver.
- **TODO:**
  - [ ] Find lead distance signals in HW1 DBC
  - [ ] Map to UI display
  - [ ] Test on HW1 hardware

### 16. Invalid LKAS Setting Detection
- **Priority:** MEDIUM
- **Files:** `carstate.py:141`
- **Issue:** `invalidLkasSetting` detection not implemented for HW1/Model X. TODO: find signal for TESLA_MODEL_X and HW2.5 vehicles.
- **TODO:**
  - [ ] Find DAS_settings equivalent on HW1
  - [ ] Implement `invalidLkasSetting` detection
  - [ ] Add to `carstate.py` parsing

---

## Longitudinal Control

### 17. Native Stop-and-Go Support
- **Priority:** HIGH
- **Files:** `carstate.py`, `carcontroller.py`
- **Issue:** Tesla uses workaround (standstill check) instead of native SNG. No `autoResumeSng` flag.
- **TODO:**
  - [ ] Investigate if HW1 supports native SNG
  - [ ] If yes, implement `autoResumeSng` flag
  - [ ] If no, improve current workaround for smoother operation
  - [ ] Test SNG behavior on HW1 hardware

### 18. Longitudinal PID Tuning
- **Priority:** MEDIUM
- **Files:** `interface.py`, `carcontroller.py`
- **Issue:** Tesla uses direct accel control without per-platform PID gains.
- **TODO:**
  - [ ] Characterize HW1 longitudinal response
  - [ ] Implement per-platform PID tuning for HW1
  - [ ] Tune for smooth acceleration and deceleration
  - [ ] Test across speed range

### 19. Longitudinal Actuator Delay
- **Priority:** MEDIUM
- **Files:** `interface.py`
- **Issue:** No actuator delay tuning for HW1.
- **TODO:**
  - [ ] Measure HW1 longitudinal actuator delay
  - [ ] Add `longitudinalActuatorDelay` to HW1 params
  - [ ] Tune for optimal response

### 20. Radar Integration
- **Priority:** LOW
- **Files:** `radar_interface.py`
- **Issue:** HW1 uses Bosch radar (older generation). No radar disable option.
- **TODO:**
  - [ ] Characterize Bosch radar performance on HW1
  - [ ] Implement radar disable flag if needed
  - [ ] Fuse radar and camera data optimally
  - [ ] Test in various conditions

---

## Lateral Control

### 21. Per-Platform Lateral Tuning
- **Priority:** MEDIUM
- **Files:** `interface.py`, `values.py`
- **Issue:** All Teslas use same lateral limits. No per-platform torque tuning.
- **TODO:**
  - [ ] Characterize HW1 steering response
  - [ ] Implement HW1-specific lateral tuning
  - [ ] Tune steering rate and max torque for HW1
  - [ ] Test on winding roads

### 22. Wheel Speed Factor
- **Priority:** LOW
- **Files:** `interface.py`
- **Issue:** Wheel speed factor not set for Tesla.
- **TODO:**
  - [ ] Measure HW1 wheel speed accuracy
  - [ ] Calculate wheel speed factor
  - [ ] Add to HW1 params

### 23. Steer Ratio
- **Priority:** LOW
- **Files:** `interface.py`
- **Issue:** Steer ratio uses fixed estimate, not measured per-car.
- **TODO:**
  - [ ] Measure HW1 steering ratio
  - [ ] Add accurate steer ratio to HW1 params
  - [ ] Test lateral controller with corrected ratio

### 24. Lateral Jerk Limits
- **Priority:** LOW
- **Files:** `interface.py`
- **Issue:** Fixed lateral jerk limits, not per-platform.
- **TODO:**
  - [ ] Characterize HW1 lateral jerk limits
  - [ ] Implement HW1-specific jerk limits
  - [ ] Test for comfort and safety

---

## Vehicle State Detection

### 25. Transmission Type Detection
- **Priority:** LOW
- **Files:** `interface.py`, `carstate.py`
- **Issue:** Transmission type not detected for Tesla.
- **TODO:**
  - [ ] Determine if transmission type is relevant for Tesla (single-speed)
  - [ ] If not relevant, document why
  - [ ] If relevant, add detection logic

### 26. Hybrid/EV Detection
- **Priority:** LOW
- **Files:** `interface.py`
- **Issue:** No hybrid/EV flag for Tesla (all Teslas are EV).
- **TODO:**
  - [ ] Add `EV` flag to Tesla safety model
  - [ ] Implement EV-specific behaviors if needed (regen braking handling)

### 27. Blind Spot Detection Enhancement
- **Priority:** MEDIUM
- **Files:** `carstate.py`, `values.py`
- **Issue:** Tesla only has basic `DAS_blindSpotRearLeft/Right` detection. No BSM mirror control.
- **TODO:**
  - [ ] Find BSM mirror control messages in HW1 DBC
  - [ ] Implement BSM mirror alert control
  - [ ] Add `enableBsm` flag for HW1
  - [ ] Test blind spot detection accuracy

---

## Architecture and Code Quality

### 28. DBC Consolidation
- **Priority:** MEDIUM
- **Files:** `tesla_can.dbc`, `tesla_powertrain.dbc`
- **Issue:** HW1 uses legacy DBC files with different message addresses than HW2/HW3.
- **TODO:**
  - [ ] Audit all message differences between HW1 and HW2/HW3 DBCs
  - [ ] Create unified DBC with HW1-specific variants where needed
  - [ ] Document all HW1-specific message definitions

### 29. Code Path Consolidation
- **Priority:** MEDIUM
- **Files:** `carstate.py`, `carcontroller.py`, `teslacan_legacy.py`
- **Issue:** Separate parsing paths for HW1 vs HW2/HW3. Code duplication.
- **TODO:**
  - [ ] Identify common code paths between HW variants
  - [ ] Consolidate where possible
  - [ ] Add clear HW1-specific sections with documentation

### 30. Test Coverage
- **Priority:** HIGH
- **Files:** `tests/test_tesla.py`, `safety/tests/test_tesla_hw1.py`
- **Issue:** Limited test coverage for HW1-specific functionality.
- **TODO:**
  - [ ] Add HW1-specific unit tests for signal parsing
  - [ ] Add HW1 safety layer tests
  - [ ] Add integration tests for HW1 CAN messages
  - [ ] Test all HW1 TX messages

### 31. Documentation
- **Priority:** HIGH
- **Files:** README, comments
- **Issue:** Limited documentation of HW1-specific quirks and limitations.
- **TODO:**
  - [ ] Document all HW1 CAN message addresses
  - [ ] Document HW1 architecture limitations
  - [ ] Create hardware installation guide for HW1
  - [ ] Document known issues and workarounds

---

## Safety and Validation

### 32. Signal Plausibility Checks
- **Priority:** HIGH
- **Files:** `carstate.py`, `tesla_legacy.h`
- **Issue:** No checksum/counter validation on HW1. Need fallback signal validation.
- **TODO:**
  - [ ] Implement range checks for all critical signals
  - [ ] Implement rate-of-change checks
  - [ ] Implement cross-signal validation (e.g., speed vs wheel speed)
  - [ ] Add fault detection and fallback behavior

### 33. LKAS Passthrough Limitation
- **Priority:** MEDIUM
- **Files:** `tesla_legacy.h:17`
- **Issue:** TODO: Only LKAS (non-emergency) is currently supported since we've only seen it.
- **TODO:**
  - [ ] Investigate emergency steering messages on HW1
  - [ ] Implement emergency steering passthrough if needed
  - [ ] Test emergency scenarios

### 34. FSD 14 Support
- **Priority:** LOW
- **Files:** `values.py`, `tesla_legacy.h`
- **Issue:** FSD 14 flag not available for HW1.
- **TODO:**
  - [ ] Determine if FSD 14 is relevant for HW1
  - [ ] If yes, implement support
  - [ ] If no, document why

---

## HW1 Fixes - User Experience & Behavior

### 35. Restore TACC Behavior - 1 Pull vs 2 Pull Stalk
- **Priority:** HIGH
- **Issue:** Currently, pulling the cruise stalk once activates openpilot. On stock Tesla, 1 pull = TACC (Traffic Aware Cruise Control only), 2 pulls = TACC + Autosteer (LKAS). This change breaks user muscle memory and removes the ability to use TACC-only mode.
- **Current:** 1 stalk pull → openpilot (lat + long)
- **Stock:** 1 stalk pull → TACC (long only), 2 stalk pulls → TACC + Autosteer (lat + long)
- **Files:** `carstate.py`, `carcontroller.py`
- **Proposed Fix:**
  - [ ] Detect single stalk pull and pass through to stock Tesla for TACC activation
  - [ ] Trigger openpilot lateral control only on double pull (2nd pull within time window)
  - [ ] Maintain openpilot longitudinal when stock TACC is active (intercept accel commands)
  - [ ] Add UI indicator showing TACC-only vs TACC+LKAS state
  - [ ] Test stalk behavior matches stock Tesla timing (~0.5s window between pulls)

### 36. Fix Autopark Not Working
- **Priority:** HIGH
- **Issue:** Autopark functionality does not work at all on HW1. openpilot likely intercepts steering/accel commands that autopark needs, or autopark state detection is broken.
- **Files:** `carstate.py:autopark`, `carcontroller.py`, `values.py`
- **Current:** Autopark state detected but not functional
- **Proposed Fix:**
  - [ ] Verify `DI_autoparkState` signal is parsed correctly on HW1 bus routing
  - [ ] Add autopark passthrough mode — release all steering/long control when autopark is active
  - [ ] Ensure `ret.cruiseState.enabled = False` during autopark
  - [ ] Test autopark activation from stock UI without openpilot interference
  - [ ] Add autopark fault handling (disable OP if autopark fails mid-sequence)

### 37. Fix Summon Disconnecting Randomly
- **Priority:** MEDIUM
- **Issue:** Summon stops working randomly during use. Likely caused by openpilot CAN traffic interfering with the Tesla app's summon commands, or CAN bus arbitration conflicts.
- **Files:** `carstate.py`, `carcontroller.py`, `teslacan_legacy.py`
- **Proposed Fix:**
  - [ ] Detect summon active state (`DI_summon` or equivalent signal)
  - [ ] Suspend all openpilot CAN TX when summon is active
  - [ ] Do not rely on Tesla app for summon trigger — use native stalk/button input instead
  - [ ] Add summon state machine with clean entry/exit transitions
  - [ ] Test summon reliability with openpilot running in background
  - [ ] Consider rate-limiting openpilot CAN messages during summon to reduce bus load

### 38. Fix Speed Display Mismatch (Real vs Display Speed)
- **Priority:** MEDIUM
- **Issue:** openpilot uses raw CAN speed (`DI_vehicleSpeed`) which is the true vehicle speed. The Tesla dashboard displays a slightly lower "display speed" (typically 1-3 km/h lower for regulatory reasons). This causes openpilot's target speed to never match what the driver sees on the dash.
- **Files:** `carstate.py` (speed parsing), `carcontroller.py` (longitudinal control), `values.py` (speed calibration)
- **Current:** `ret.vEgoRaw = cp_chassis.vl["ESP_B"]["ESP_vehicleSpeed"] * CV.KPH_TO_MS`
- **Proposed Fix:**
  - [ ] Find the display speed signal in HW1 DBC (likely `GTW_speed` or similar)
  - [ ] If no display speed signal exists, apply a calibration factor (typically -1 to -3 km/h offset or ~2-3% scaling)
  - [ ] Create per-platform speed calibration table for HW1
  - [ ] Use display speed for cruise target setting and UI display
  - [ ] Keep real speed for safety-critical calculations (AEB, stopping distance)
  - [ ] Add `SP_SPEED_OFFSET` environment variable for user fine-tuning
  - [ ] Test across speed range (30-130 km/h) to verify consistent offset

---

## Quick Reference: File Locations

| File | Purpose | Key Lines |
|------|---------|-----------|
| `values.py` | Platform configs, safety flags | 43-118, 213-219, 232 |
| `carstate.py` | CAN state parsing | 18-24, 141, 158, 185-188, 249 |
| `carcontroller.py` | Steering/longitudinal control | 58, 76 |
| `interface.py` | Car interface, params setup | 54, 95 |
| `teslacan_legacy.py` | CAN packing for legacy | All |
| `tesla_legacy.h` | Legacy Tesla safety hooks | 17, 218-231, 241-249, 259-265, 277-279 |
| `tesla_can.dbc` | Legacy CAN messages | All |

---

## Priority Summary

| Priority | Count | Key Items |
|----------|-------|-----------|
| **HIGH** | 12 | APS_eacMonitor, EPS rate, checksums, external panda, gap adjust, HUD, SNG, tests, signal plausibility, docs, TACC stalk behavior, autopark |
| **MEDIUM** | 15 | ESP/Brake/DI_state signals, message addresses, TX expansion, LDW/FCW/lead display, invalid LKAS, PID tuning, actuator delay, lateral tuning, BSM, DBC consolidation, code consolidation, LKAS passthrough, summon, speed display mismatch |
| **LOW** | 11 | VCRIGHT_silla2, radar integration, wheel speed, steer ratio, jerk limits, transmission type, EV detection, FSD 14 |

---

## Comparison to Reference Platforms

### Toyota Has That Tesla HW1 Doesn't:
- Blind spot enable via fingerprint (`enableBsm`)
- Per-platform lateral torque tuning
- Per-platform longitudinal tuning (PID gains)
- Hybrid-specific actuator delays
- SmartDSU detection for longitudinal
- Radar-based vs camera-based ACC detection
- SECOC authentication
- Gap adjust button
- HUD control
- Lane departure warning
- Lead distance display
- FCW alert
- Auto resume SNG

### Honda Has That Tesla HW1 Doesn't:
- Per-platform lateral torque tuning
- Per-platform longitudinal PID tuning
- Manual transmission detection
- Hybrid detection
- Nidec vs Bosch architecture detection
- CANFD support
- Alt brake message detection
- Longitudinal actuator delay tuning
- Gap adjust button
- HUD control

---

## Notes

- HW1 uses `teslaLegacy` safety model with `FLAG_HW1`
- HW1 does NOT support `FLAG_EXTERNAL_PANDA`
- HW1 does NOT support `FSD_14` flag
- All HW1 messages have `ignore_checksum=true, ignore_counter=true`
- HW1 EPAS runs at 25 Hz (vs 100 Hz on HW3)
- HW1 chassis bus is 0 (HW3 uses bus 1)
- HW1 uses Bosch radar (HW3 uses Continental)
