# G27/LGS pedal inversion: comparison of the two MAME XML exports

Date: 2026-10-20

## Files received

Two files were supplied for diagnosis:

- `MAME_LGS_FUNCIONAL.xml`: a Logitech Gaming Software (LGS) `GameProfile`.
- `MAME_HUB.xml`: a `LegacyWheelHubProfile` exported by the Hub.

These files are **different formats and represent different layers**. The Hub export is not the LGS profile after the Hub attempted to apply an inversion, so it cannot by itself prove whether the Hub changed the installed LGS XML.

## What the LGS file proves

The working LGS profile targets `mame.exe` and has `Assignments DeviceModel="57"`. Its `AxisDynamics` element wraps two `AxisDef` entries:

- Axis `R`: `Sign="-1"`
- Axis `Z`: `Sign="-1"`

The profile therefore stores negative direction for both of these axes. This is the known-good reference state reported by the user.

## What the Hub export proves

The Hub profile is named `MAME`, points to `G:/LaunchBox/emulators/mame/mame.exe`, and stores:

- `invert_brake=true`
- `invert_throttle=true`
- `driver_pedal_inversion_configured=true`
- `lgs_axis_brake`, `lgs_axis_throttle`, and `lgs_axis_clutch` are empty.

The empty `lgs_axis_*` fields are not necessarily the cause: the current source code uses a fixed mapping for the G27/LGS profile (`throttle -> Z`, `brake -> R`) rather than reading those fields.

## Source-code behavior relevant to the report

In `LegacyWheelHub.py`, `set_logitech_profile_pedal_inversions()` searches LGS profile directories under `LOCALAPPDATA` and `APPDATA`, finds XML profiles whose target is the same executable basename, selects `Assignments DeviceModel="57"`, and sets the `Sign` attributes for axes `Z` and `R`.

The function explicitly supports the wrapped `AxisDynamics/AxisDef` layout found in the supplied working LGS XML. Therefore, the XML structure shown in the working export is already handled by the current code.

The function edits an installed LGS XML file. It does not directly transform the values delivered to MAME, and editing a profile file alone does not prove that LGS/the driver reloaded the changed settings.

## Current conclusion

The supplied files confirm the desired LGS axis settings and that the Hub has inversion flags enabled. They **do not show the LGS XML as it exists after the Hub applies the settings**. The next diagnostic must inspect that exact file before and after using the Hub; repeating generic HID captures is not the priority yet.

## Next test (needed to isolate the failure)

1. Close MAME.
2. Find the installed LGS XML profile that targets `mame.exe` in the LGS profile directory. Make a backup copy.
3. Record the exact path and copy the XML as `MAME_LGS_BEFORE_HUB.xml`.
4. Open the Hub, toggle one pedal inversion off and then on, and note the Hub's notification.
5. Close the Hub and copy the same installed LGS XML as `MAME_LGS_AFTER_HUB.xml`.
6. Compare the two files, especially the `Assignments DeviceModel="57"` node and `AxisDynamics` entries for `R` and `Z`. Also check whether LGS rewrites the file after the Hub exits or after LGS is restarted.
7. Share both XMLs and their full file paths. Redact unrelated personal paths if desired, but keep the XML structure and target/device identifiers.

Interpretation:
- **No XML difference:** investigate profile discovery/matching, whether the Hub writes to the actual active profile, and whether a toggle results in a write.
- **XML changes but MAME behavior does not:** investigate whether LGS reloads/overwrites the profile and whether the running LGS/driver consumes the changed `Sign` values.
- **XML changes and later reverts:** investigate LGS persistence/rewrite behavior before implementing another inversion mechanism.

Do not disable Windows Memory Integrity/Core Isolation for this investigation.
