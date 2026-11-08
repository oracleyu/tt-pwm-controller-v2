# V2 external-pin verification

`test.py` uses one SPI master and one PWM checker for RTL, generic synthesis, standalone SKY130, final unpowered, and final powered netlists. It checks all 256 duty codes, divider encodings 0/1/7/255, one-entry queue rejection and atomic boundary updates, seven malformed frame cases, 24 deterministic random configurations, asynchronous SPI phase, pause/resume, reset during a frame, and a quiet-window registered-output check.

Each completed run writes coverage.json. The root helper removes old results before starting and explicitly checks Cocotb xUnit results before copying logs/coverage/waves into reports/. These are functional simulations with empty UNIT_DELAY, not SDF timing simulation. Full extracted timing is checked separately by LibreLane/OpenSTA.

Use root make targets rtl, sky-synth, gate and cocotb-gate. The MODE variable also selects rtl/generic/sky/final/powered directly in this directory. GATES=yes remains compatible with the official Tiny Tapeout GL action.
