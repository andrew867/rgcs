// Safety state machine (Agent A19) — the C++ mirror of the tested
// Python twin (fkey_instrument/device.py). Behavioral contract:
//
//  - output off at boot, off in every state except RUNNING;
//  - only a fresh, unexpired, single-use arm lease reaches ARMED;
//  - only explicit start before expiry reaches RUNNING;
//  - every fault forces output off IMMEDIATELY and latches;
//  - faults acknowledge only while off; no override, no auto-arm.
//
// STATUS: NOT compiled in this repository (no toolchain); the Python
// twin carries the executable tests for every transition below.
#pragma once
#include <cstdint>

namespace fkey {

enum class State : uint8_t {
  BOOT_SAFE, SELF_TEST, SAFE_OFF, RECIPE_VALID,
  ARMED, RUNNING, COOLDOWN, FAULT_LATCHED,
};

enum class Fault : uint8_t {
  NONE, ARM_EXPIRY, INVALID_RECIPE, WATCHDOG, OVERTEMP,
  OVERCURRENT, SUPPLY_FAULT, SENSOR_SATURATION, RECIPE_TIMEOUT,
  QUEUE_OVERFLOW, PIN_CONFLICT, BOARD_PROFILE_MISMATCH,
  EMERGENCY_STOP, FIRMWARE_EXCEPTION, BROWNOUT,
};

// The output-enable is a single function so every code path funnels
// through one place; there is no second way to drive the pin.
void hw_output_disable();   // board HAL; no-op unless BOARD_VERIFIED

class SafetyFsm {
 public:
  SafetyFsm() { enter_boot(); }

  State state() const { return state_; }
  bool output_on() const { return state_ == State::RUNNING; }

  void enter_boot() {
    hw_output_disable();
    state_ = State::BOOT_SAFE;
    // explicit init order (A15): boot -> self test -> safe off
    state_ = State::SELF_TEST;
    state_ = State::SAFE_OFF;
  }

  bool load_recipe_valid(bool validator_passed) {
    if (state_ != State::SAFE_OFF && state_ != State::RECIPE_VALID)
      return false;
    if (!validator_passed) { fault(Fault::INVALID_RECIPE); return false; }
    state_ = State::RECIPE_VALID;
    return true;
  }

  // lease: token issued by request_arm, expires at expiry_ms; the
  // caller must present the same token to start() before expiry
  uint32_t request_arm(uint32_t now_ms, uint32_t ttl_ms) {
    if (state_ != State::RECIPE_VALID) return 0;
    arm_expiry_ms_ = now_ms + ttl_ms;
    arm_token_ = next_token_++;
    state_ = State::ARMED;
    return arm_token_;
  }

  bool start(uint32_t token, uint32_t now_ms) {
    if (state_ != State::ARMED) return false;
    if (token != arm_token_) { fault(Fault::INVALID_RECIPE); return false; }
    if (now_ms > arm_expiry_ms_) { fault(Fault::ARM_EXPIRY); return false; }
    arm_token_ = 0;                      // single use
    state_ = State::RUNNING;             // ONLY here is output legal
    return true;
  }

  void stop() {
    if (state_ == State::RUNNING) {
      hw_output_disable();
      state_ = State::COOLDOWN;
      state_ = State::SAFE_OFF;
    }
  }

  void fault(Fault f) {
    hw_output_disable();                 // FIRST, unconditionally
    last_fault_ = f;
    state_ = State::FAULT_LATCHED;
  }

  bool acknowledge() {
    if (state_ != State::FAULT_LATCHED) return false;
    last_fault_ = Fault::NONE;
    state_ = State::SAFE_OFF;
    return true;
  }

  Fault last_fault() const { return last_fault_; }

 private:
  State state_ = State::BOOT_SAFE;
  Fault last_fault_ = Fault::NONE;
  uint32_t arm_token_ = 0, next_token_ = 1, arm_expiry_ms_ = 0;
};

}  // namespace fkey
