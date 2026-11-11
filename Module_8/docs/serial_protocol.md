# Module 8 v2 serial protocol

Firmware ID: `module_08_angstrom_v2`. Baud: **115200**. Commands and records use
newline termination. Positive PWM heats D9; negative PWM cools D10. Both direction
outputs are switched off before either is energized. Boot and STOP output zero.

## Commands

Commands are sent one at a time, waiting for `#ACK,<command>` before sending the
next plan command. Long configuration lines are sent in at most 48-byte chunks,
350 ms apart, to respect the Uno UART receive buffer during acquisition. Heartbeats
are not inserted inside a partial command; plan uploads occur with output off.
`PING` is the exception and has no acknowledgement. GUI command
acknowledgement timeout is 3 s; firmware heartbeat/control-gap timeout is 2 s.

| Command | Meaning |
| --- | --- |
| `HELLO` | Replies `#ACK,HELLO,module_08_angstrom_v2` |
| `PING` | Refreshes the firmware link watchdog; GUI sends every 0.4 s |
| `STOP` | Always accepted; immediately zeros both outputs and integral; does not clear a fault |
| `CLEAR` | While stopped, clears plan/calibration/fault; latched faults require safe current sensors |
| `CONFIG ratio pwm_limit anti_windup` | Positive ratio <=20, integer PWM limit 1–255, anti-windup 0/1 |
| `CAL temperature_C signed_pwm` | Append an increasing calibration knot; max 12 knots; no extrapolation |
| `STEP duration_s Ta_C Tb_C period_s mode Kp Ki` | Append a step, max 12; mode OPEN/P/PI; period >=100 s |
| `STEP duration_s 0 0 period_s mode 0 0 Ua_pwm Ub_pwm` | Raw step; mode RAW_ZERO or RAW_POS; period >=100 s |
| `COMMIT step_count point_count` | Independently validates the entire plan and counts; leaves output OFF |
| `START` | Requires committed plan, fresh valid sensors, no fault and recent heartbeat |

A complete plan upload is STOP, CLEAR, CONFIG, zero or more CAL commands, STEP
commands, COMMIT. START is a separate explicit action. No immediate arbitrary-PWM
command is exposed. Total duration is limited to 24 h; minimum step duration is
1 s for rehearsal. Temperature targets remain inside 10–45 C. Raw modes have no
temperature target; measured TEC protection at 10–45 C, T1 protection, link timeout,
physical cutoff, STOP and fail-off remain in force in every mode.

Raw command is `u = Ua_pwm + Ub_pwm*sin(phase)`, without lookup, temperature
feedback, integral action or heating/cooling multiplier. RAW_ZERO requires Ua=0
and Ub>0; RAW_POS requires Ua>Ub>0. Both Python and firmware reject a plan if
`abs(Ua)+Ub > pwm_limit` (or >255), so a +/-100 diagnostic cannot silently clip
at the older 96-count comparison limit. Temperature/gain fields in a raw STEP
are required to be zero, and raw amplitudes are separate PWM-count parameters.

Syntax/range failures return `#ERR,<reason>`. The GUI aborts the upload and requests
STOP on an error or acknowledgement timeout. The firmware independently refuses
START without a valid commit. A line longer than the fixed buffer faults output off.

## Measurement record

Every `DATA,` line has the exact field order in `python/rod_protocol.py:FIELD_NAMES`,
printed as `#DATA,...` at startup. V2 appends `Ua_pwm,Ub_pwm` after `seq`, giving
44 data fields. Records are emitted every approximately 500 ms.
`time_ms` is Arduino unsigned milliseconds, `time_s` is its seconds representation,
and `seq` is the monotonically increasing measurement-record sequence.

All six temperatures are degrees Celsius. Channel order is TEC, T1–T5. The
acquisition scan uses 1000 ADC samples for A0 and 100 each for A1–A5, discarding the
first conversion after each mux switch. Readings are sequential within one scan,
not simultaneous; scan skew is approximately 0.17 s and should be considered in
phase uncertainty if material. The record timestamp follows the scan.

Additional fields include run state, control mode, zero-based step, mean, amplitude,
period, actual setpoint, phase, gains, heating/cooling ratio, raw controller command,
compensated command, applied signed PWM, saturation and anti-windup flags, heartbeat
age and safety/fault information. `feedforward_pwm` is nan outside OPEN;
`controller_pwm` is the uncompensated command in RAW/P/PI and nan in OPEN or when
stopped. Raw modes log nan for Ta_C, Tb_C, setpoint_C, both gains and error_C;
Ua_pwm/Ub_pwm contain the requested PWM parameters. Temperature modes log nan
for Ua_pwm/Ub_pwm. The recorded heating/cooling ratio remains a configuration
value; it is deliberately not applied in raw modes. Unconfigured fields use nan;
step is -1 before a plan is present. The schema never changes with mode.

- `run_state`: IDLE, RUNNING, DONE, FAULT.
- `control_mode`: OFF, OPEN, P, PI, RAW_ZERO, RAW_POS. A retained stopped plan can still show its last mode.
- `safety`: OK or SHUTDOWN; a latched fault has SHUTDOWN and a non-NONE fault code.
- `limit_C`: retained 60 C TEC backup limit; `operating_max_C`: 45 C operational maximum.
- `rod_base_limit_C`: 56 C. Invalid T1 or temperature at/above this limit faults output off.
- Missing downstream channels are nan and reduce `rod_ok`; T1 is required for control.
- `signed_pwm` and `heat_pwm`/`cool_pwm` report the firmware outputs, not physical pin measurements.

Events are `#EVENT,STEP,time_ms,index`, `#EVENT,DONE,time_ms` and
`#EVENT,FAULT,time_ms,fault_code`. STEP is emitted for the initial step and every
transition. Transition events are timestamped when the controller observes the
boundary; the phase integrator splits elapsed time at the scheduled boundary itself.

## Files and identity

The GUI writes parsed DATA fields to CSV without substituting a requested setpoint
for the measured firmware value. It also preserves every incoming byte in a sibling
`.serial.log`, including startup, events and malformed records. Outgoing plan commands
and operator actions are CSV events. Plan snapshots contain source hashes and the
sensor-map snapshot; `plan_sha256` identifies the validated command plan in the CSV.

An interrupted upload or plan edit invalidates Start. An Arduino reset or wrong
firmware version requires a fresh handshake; it cannot silently resume output.
Fault reset is explicit and discards the committed plan, requiring upload again.

The v2 GUI requires a v2 firmware handshake, preventing accidental use of an old
board program without raw support. V1 temperature-plan JSON files remain loadable
and are migrated in memory to v2; originals are unchanged. The record parser can
also read saved 42-field v1 temperature records, but does not accept raw modes in
that older schema. Saved plan snapshots and previous raw files are never rewritten.
