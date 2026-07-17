// Board profiles (Agent A14). Pin data provenance: community CYD
// documentation; verified=false until the physical self-test matches.
// The Python authority is fkey_instrument/boards.py — this header is
// generated-by-hand from it and must be kept in sync (checked by the
// coverage tool's doc pointer, and by eye until a generator exists).
#pragma once
#include <cstdint>

namespace fkey {

#if defined(BOARD_PROFILE_2432S028R)
// ESP32-2432S028R "classic CYD": ILI9341 SPI display, XPT2046 touch.
// display: MOSI 13, CLK 14, CS 15, DC 2, BL 21
// touch:   MOSI 32, MISO 39, CLK 25, CS 33, IRQ 36
// sd:      MOSI 23, MISO 19, CLK 18, CS 5
// rgb led: R4 G16 B17; ldr 34; speaker 26
// boot-strap (never drive): 0, 2, 5, 12, 15
// input-only: 34, 35, 36, 39
constexpr int kOutputPin = 22;       // candidate; VERIFY before use
constexpr int kAdcPin = 35;          // input-only, candidate pickup
#elif defined(BOARD_PROFILE_2432S024C)
constexpr int kOutputPin = 22;
constexpr int kAdcPin = 35;
#else
// UNKNOWN BOARD => OUTPUT_DISABLED (A14 gate). kOutputPin = -1 makes
// every hardware write a no-op in hw_output_disable()'s guard.
constexpr int kOutputPin = -1;
constexpr int kAdcPin = -1;
#endif

}  // namespace fkey
