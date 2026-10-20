"""Pure axis transforms for Legacy Wheel Hub pedal inversion.

This module deliberately has no HID, SDL, Qt, DirectInput, or Windows dependency.
It defines the numerical behavior that an input adapter must apply before an
application receives the pedal axis. Calling this helper only changes the
value passed to it; the game-facing adapter must still invoke it on the actual
input path for inversion to be effective in a game.
"""

from __future__ import annotations

import math
from typing import SupportsFloat


PEDALS = ("throttle", "brake", "clutch")


def invert_axis_value(
    value: SupportsFloat,
    minimum: SupportsFloat,
    maximum: SupportsFloat,
    inverted: bool,
) -> float:
    """Return an axis value, optionally reflected around its range midpoint.

    Examples:
      * normalized DirectInput axis [-1, +1]:  -0.25 -> +0.25
      * unipolar pedal [0, 1]:                  0.20 -> 0.80
      * byte pedal [0, 255]:                    32 -> 223

    The transform is an identity when `inverted` is false. Values outside the
    reported range are preserved by the identity path and reflected
    mathematically by the inversion path; callers should normally supply the
    range reported by their input API.
    """
    x = float(value)
    lo = float(minimum)
    hi = float(maximum)
    if not all(math.isfinite(n) for n in (x, lo, hi)):
        raise ValueError("axis value and bounds must be finite numbers")
    if hi <= lo:
        raise ValueError("axis maximum must be greater than minimum")
    if not inverted:
        return x
    return lo + hi - x


def pedal_inversion_settings(profile: object) -> dict[str, bool]:
    """Read a profile's inversion flags, treating missing/invalid values as off."""
    source = profile if isinstance(profile, dict) else {}
    return {
        pedal: bool(source.get(f"invert_{pedal}", False))
        for pedal in PEDALS
    }


def apply_pedal_inversion(
    pedal: str,
    value: SupportsFloat,
    minimum: SupportsFloat,
    maximum: SupportsFloat,
    profile: object,
) -> float:
    """Transform one pedal value using the flags saved in a Hub profile."""
    if pedal not in PEDALS:
        raise ValueError(f"unsupported pedal: {pedal}")
    enabled = pedal_inversion_settings(profile)[pedal]
    return invert_axis_value(value, minimum, maximum, enabled)
