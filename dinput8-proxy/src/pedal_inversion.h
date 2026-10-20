#pragma once
// Per-game DirectInput axis inversion. This layer is deliberately inert until
// the profile has an explicit byte offset for a pedal; never guess offsets from
// SDL axis numbers. Values are applied to the state buffer returned by the
// real DirectInput device, before the game receives it.

#define NOMINMAX
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdint>
#include <cstring>
#include <limits>
#include <string>

inline bool LwhReadDwordForThisGame(const wchar_t* name, DWORD* value)
{
    if (!name || !value) return false;
    const std::wstring path = L"Software\\LegacyWheelHub\\Games\\" + LwhGameKey();
    HKEY key = nullptr;
    if (RegOpenKeyExW(HKEY_CURRENT_USER, path.c_str(), 0, KEY_READ, &key) != ERROR_SUCCESS)
        return false;
    DWORD type = 0;
    DWORD size = sizeof(DWORD);
    const LONG result = RegQueryValueExW(key, name, nullptr, &type,
                                         reinterpret_cast<LPBYTE>(value), &size);
    RegCloseKey(key);
    return result == ERROR_SUCCESS && type == REG_DWORD && size == sizeof(DWORD);
}

inline bool LwhReadBoolDword(const wchar_t* name)
{
    DWORD value = 0;
    return LwhReadDwordForThisGame(name, &value) && value != 0;
}

inline void LwhInvertConfiguredAxis(BYTE* state, DWORD stateSize,
                                    const LONG* axisOffsets,
                                    const wchar_t* enabledName,
                                    const wchar_t* axisName,
                                    const wchar_t* minName,
                                    const wchar_t* maxName)
{
    if (!state || !axisOffsets || !LwhReadBoolDword(enabledName)) return;

    DWORD rawAxis = 0xFFFFFFFFu, rawMin = 0, rawMax = 65535;
    if (!LwhReadDwordForThisGame(axisName, &rawAxis) || rawAxis > 7) return;
    (void)LwhReadDwordForThisGame(minName, &rawMin);
    (void)LwhReadDwordForThisGame(maxName, &rawMax);

    const LONG minimum = static_cast<LONG>(rawMin);
    const LONG maximum = static_cast<LONG>(rawMax);
    const LONG signedOffset = axisOffsets[rawAxis];
    if (signedOffset < 0 || maximum <= minimum) return;
    const size_t offset = static_cast<size_t>(signedOffset);
    if (offset % alignof(LONG) != 0 || offset > stateSize ||
        sizeof(LONG) > stateSize - offset) return;

    LONG current = 0;
    std::memcpy(&current, state + offset, sizeof(current));
    if (current < minimum || current > maximum) return;

    const int64_t inverted = static_cast<int64_t>(minimum) +
                             static_cast<int64_t>(maximum) - current;
    if (inverted < std::numeric_limits<LONG>::min() ||
        inverted > std::numeric_limits<LONG>::max()) return;
    const LONG result = static_cast<LONG>(inverted);
    std::memcpy(state + offset, &result, sizeof(result));
}

inline int LwhAxisIndexFromGuid(REFGUID guid, DWORD objectType)
{
    if (IsEqualGUID(guid, GUID_XAxis)) return 0;
    if (IsEqualGUID(guid, GUID_YAxis)) return 1;
    if (IsEqualGUID(guid, GUID_ZAxis)) return 2;
    if (IsEqualGUID(guid, GUID_RxAxis)) return 3;
    if (IsEqualGUID(guid, GUID_RyAxis)) return 4;
    if (IsEqualGUID(guid, GUID_RzAxis)) return 5;
    if (IsEqualGUID(guid, GUID_Slider)) {
        const DWORD instance = DIDFT_GETINSTANCE(objectType);
        return instance < 2 ? static_cast<int>(6 + instance) : -1;
    }
    return -1;
}

inline void LwhApplyPedalInversion(void* buffer, DWORD stateSize,
                                   const LONG* axisOffsets)
{
    BYTE* state = static_cast<BYTE*>(buffer);
    LwhInvertConfiguredAxis(state, stateSize, axisOffsets, L"InvertThrottle",
                            L"ThrottleAxis", L"ThrottleMin", L"ThrottleMax");
    LwhInvertConfiguredAxis(state, stateSize, axisOffsets, L"InvertBrake",
                            L"BrakeAxis", L"BrakeMin", L"BrakeMax");
    LwhInvertConfiguredAxis(state, stateSize, axisOffsets, L"InvertClutch",
                            L"ClutchAxis", L"ClutchMin", L"ClutchMax");
}
