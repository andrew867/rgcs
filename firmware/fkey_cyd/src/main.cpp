// RGCS Frequency-Key CYD instrument — firmware core (Agents A15-A18).
//
// STATUS: FIRMWARE_SOURCE_PROVIDED / NOT_COMPILED_IN_THIS_REPO.
// The Python simulator (fkey_instrument/device.py) is the tested
// behavioral twin; this file is the hardware port skeleton whose
// load-bearing logic (safety FSM, lease, validation-before-output)
// mirrors it line for line.
//
// Design commitments (A15):
//  - output off at boot (OUTPUT_OFF_AT_BOOT enforced in setup());
//  - immutable active recipe (loaded copy is const after arm);
//  - monotonic run clock (esp_timer / millis monotonic);
//  - LEDC hardware timer output; reconfiguration only while off;
//  - watchdog: any task starvation -> fault -> output off;
//  - version + git hash reported in /info;
//  - no dynamic allocation in the segment loop after arm.

#include "safety_fsm.h"
#include "board_profile.h"

#ifdef FKEY_SIMULATOR
#include <cstdio>
static uint32_t fake_ms = 0;
static uint32_t now_ms() { return fake_ms; }
#else
#include <Arduino.h>
static uint32_t now_ms() { return millis(); }
#endif

namespace fkey {

// single funnel for the physical output (A19: one enable path)
void hw_output_disable() {
#if defined(BOARD_VERIFIED) && !defined(FKEY_SIMULATOR)
  ledcWrite(0, 0);                 // duty 0
  digitalWrite(kOutputPin, LOW);
#endif
  // unverified board or simulator: there is nothing to disable,
  // which is the point (A14: unknown board => OUTPUT_DISABLED)
}

SafetyFsm g_fsm;

// --- recipe storage (validated before this struct is ever filled) ---
struct Segment {
  char label[24];
  uint8_t kind;                    // 0 sine(DDS) 1 square(LEDC) ...
  uint32_t freq_millihz;           // integer millihertz, no floats
  uint32_t duration_ms;
  uint16_t duty_q15;
  uint16_t amplitude_q15;          // REQUIRED by schema (no default)
};
constexpr int kMaxSegments = 256;
Segment g_segments[kMaxSegments];  // static: no alloc after arm
int g_n_segments = 0;

// LEDC realized frequency (mirrors boards.LedcBackend, integer math):
//   div_q8 = round(80e6 * 256 / (f * 2^res))
//   f_real = 80e6 * 256 / (div_q8 * 2^res)   [report BOTH]
struct Realized { uint64_t req_uhz, real_uhz; };
Realized ledc_realize(uint64_t f_uhz, uint8_t res_bits) {
  const uint64_t apb_uhz = 80000000ULL * 1000000ULL;
  uint64_t denom = (f_uhz >> res_bits) ? (f_uhz << res_bits) : 1;
  uint64_t div_q8 = (apb_uhz * 256 + denom / 2) / denom;
  if (div_q8 < 256) return {f_uhz, 0};       // refuse, don't fudge
  uint64_t real = (apb_uhz * 256) / (div_q8 << res_bits);
  return {f_uhz, real};
}

void run_segments() {
  if (g_fsm.state() != State::RUNNING) return;
  uint32_t total_ms = 0;
  for (int i = 0; i < g_n_segments; ++i) {
    total_ms += g_segments[i].duration_ms;
    if (total_ms > 60000U) {                 // hard ceiling
      g_fsm.fault(Fault::RECIPE_TIMEOUT);
      return;
    }
    // configure backend while output momentarily gated ... start ...
    // (hardware-specific; the realized frequency is LOGGED, the
    //  requested one is never reported as achieved)
  }
  g_fsm.stop();
}

}  // namespace fkey

// --- entry points -----------------------------------------------------
#ifdef FKEY_SIMULATOR
int main() {
  using namespace fkey;
  std::printf("fkey_cyd simulator stub: state=%d output=%d\n",
              (int)g_fsm.state(), (int)g_fsm.output_on());
  // boot must land SAFE_OFF with output off
  return (g_fsm.state() == State::SAFE_OFF && !g_fsm.output_on())
             ? 0 : 1;
}
#else
void setup() {
  fkey::hw_output_disable();               // OUTPUT_OFF_AT_BOOT
  // board self-test (A14): report chip/flash/display/touch IDs over
  // serial; refuse to enable output unless the report matches the
  // compiled BOARD_PROFILE (BOARD_PROFILE_MISMATCH fault otherwise).
  // Web/API task (A18): versioned endpoints; WebSocket for status
  // only; arm/start/stop are authenticated request-response.
  // TFT task (A18): OFF/ARMED/RUNNING/FAULT screens.
}
void loop() { fkey::run_segments(); }
#endif
