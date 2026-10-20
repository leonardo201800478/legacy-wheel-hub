#!/usr/bin/env python3
"""Windows Raw Input/HID recorder for steering wheels; read-only diagnostics.

Captures HID input reports delivered by Windows Raw Input for Generic Desktop
Joystick and Game Pad top-level collections. It does not send output reports,
write registry values, change drivers, or issue force-feedback commands.
Requires Windows; run as a normal user.
"""
from __future__ import annotations

import argparse
import ctypes
import csv
import datetime as dt
import json
import os
import sys
import time
from ctypes import wintypes
from pathlib import Path

if os.name != "nt":
    raise SystemExit("Esta ferramenta requer Windows.")

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

UINT = wintypes.UINT
DWORD = wintypes.DWORD
HANDLE = wintypes.HANDLE
ULONG_PTR = ctypes.c_size_t
LRESULT = ctypes.c_ssize_t
WPARAM = wintypes.WPARAM
LPARAM = wintypes.LPARAM
ATOM = wintypes.WORD

RID_INPUT = 0x10000003
RIDI_DEVICENAME = 0x20000007
RIDI_DEVICEINFO = 0x2000000B
RIM_TYPEHID = 2
WM_INPUT = 0x00FF
WM_DESTROY = 0x0002
PM_REMOVE = 0x0001
RIDEV_INPUTSINK = 0x00000100
RIDEV_DEVNOTIFY = 0x00002000
HWND_MESSAGE = wintypes.HWND(-3)
GENERIC_DESKTOP_PAGE = 0x01
USAGE_JOYSTICK = 0x04
USAGE_GAMEPAD = 0x05


class RAWINPUTDEVICELIST(ctypes.Structure):
    _fields_ = [("hDevice", HANDLE), ("dwType", DWORD)]


class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [
        ("usUsagePage", wintypes.USHORT),
        ("usUsage", wintypes.USHORT),
        ("dwFlags", DWORD),
        ("hwndTarget", wintypes.HWND),
    ]


class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [
        ("dwType", DWORD),
        ("dwSize", DWORD),
        ("hDevice", HANDLE),
        ("wParam", WPARAM),
    ]


class RID_DEVICE_INFO_HID(ctypes.Structure):
    _fields_ = [
        ("dwVendorId", DWORD),
        ("dwProductId", DWORD),
        ("dwVersionNumber", DWORD),
        ("usUsagePage", wintypes.USHORT),
        ("usUsage", wintypes.USHORT),
    ]


class RID_DEVICE_INFO_UNION(ctypes.Union):
    _fields_ = [
        ("hid", RID_DEVICE_INFO_HID),
        ("padding", ctypes.c_byte * 16),
    ]


class RID_DEVICE_INFO(ctypes.Structure):
    _anonymous_ = ("data",)
    _fields_ = [("cbSize", DWORD), ("dwType", DWORD), ("data", RID_DEVICE_INFO_UNION)]


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", UINT),
        ("wParam", WPARAM),
        ("lParam", LPARAM),
        ("time", DWORD),
        ("pt", POINT),
        ("lPrivate", DWORD),
    ]


WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, UINT, WPARAM, LPARAM)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


def win_error(message: str) -> OSError:
    return ctypes.WinError(ctypes.get_last_error(), message)


def get_device_name(handle: HANDLE) -> str:
    size = UINT(0)
    user32.GetRawInputDeviceInfoW(handle, RIDI_DEVICENAME, None, ctypes.byref(size))
    if not size.value:
        return ""
    buf = ctypes.create_unicode_buffer(size.value + 1)
    if user32.GetRawInputDeviceInfoW(handle, RIDI_DEVICENAME, buf, ctypes.byref(size)) == UINT(-1).value:
        return ""
    return buf.value


def enumerate_raw_devices() -> list[dict]:
    count = UINT(0)
    result = user32.GetRawInputDeviceList(None, ctypes.byref(count), ctypes.sizeof(RAWINPUTDEVICELIST))
    if result == UINT(-1).value:
        raise win_error("GetRawInputDeviceList (count)")
    devices = (RAWINPUTDEVICELIST * max(1, count.value))()
    result = user32.GetRawInputDeviceList(devices, ctypes.byref(count), ctypes.sizeof(RAWINPUTDEVICELIST))
    if result == UINT(-1).value:
        raise win_error("GetRawInputDeviceList")
    output = []
    for item in devices[:count.value]:
        info = RID_DEVICE_INFO()
        info.cbSize = ctypes.sizeof(info)
        info_size = UINT(ctypes.sizeof(info))
        ok = user32.GetRawInputDeviceInfoW(
            item.hDevice, RIDI_DEVICEINFO, ctypes.byref(info), ctypes.byref(info_size)
        )
        record = {
            "handle": hex(item.hDevice or 0),
            "type_code": int(item.dwType),
            "type": {0: "mouse", 1: "keyboard", 2: "hid"}.get(int(item.dwType), "unknown"),
            "device_path": get_device_name(item.hDevice),
        }
        if ok != UINT(-1).value and item.dwType == RIM_TYPEHID:
            record["vendor_id"] = f"0x{info.hid.dwVendorId:04X}"
            record["product_id"] = f"0x{info.hid.dwProductId:04X}"
            record["version_number"] = int(info.hid.dwVersionNumber)
            record["usage_page"] = f"0x{info.hid.usUsagePage:04X}"
            record["usage"] = f"0x{info.hid.usUsage:04X}"
        output.append(record)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Registra relatórios HID recebidos via Windows Raw Input; somente leitura."
    )
    parser.add_argument("--output-dir", default="g27-diagnostics", help="pasta de saída")
    parser.add_argument("--seconds", type=float, default=0, help="duração; 0 = até Ctrl+C")
    parser.add_argument("--foreground-only", action="store_true",
                        help="não solicitar entrada em segundo plano")
    args = parser.parse_args()

    outdir = Path(args.output_dir).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = outdir / f"g27_raw_hid_{stamp}.csv"
    json_path = outdir / f"g27_raw_hid_{stamp}.json"
    devices = enumerate_raw_devices()
    print(f"Dispositivos Raw Input encontrados: {len(devices)}")
    for dev in devices:
        print(f"  {dev['type']}: {dev.get('device_path', '')} "
              f"VID={dev.get('vendor_id', '-')} PID={dev.get('product_id', '-')} "
              f"usage={dev.get('usage_page', '-')}/{dev.get('usage', '-')}")

    started = dt.datetime.now().astimezone().isoformat()
    start_clock = time.monotonic()
    count = 0
    errors: list[str] = []
    active_devices: dict[str, dict] = {d["handle"]: d for d in devices}

    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "timestamp", "elapsed_seconds", "device_handle", "device_path",
            "report_count", "report_size_bytes", "report_index", "report_hex",
        ])

        def window_proc(hwnd, message, wparam, lparam):
            nonlocal count
            if message == WM_INPUT:
                try:
                    needed = UINT(0)
                    result = user32.GetRawInputData(
                        wintypes.HANDLE(lparam), RID_INPUT, None, ctypes.byref(needed),
                        ctypes.sizeof(RAWINPUTHEADER)
                    )
                    if result == UINT(-1).value or needed.value < ctypes.sizeof(RAWINPUTHEADER):
                        errors.append(f"GetRawInputData(size) failed: {ctypes.get_last_error()}")
                        return user32.DefWindowProcW(hwnd, message, wparam, lparam)
                    buffer = ctypes.create_string_buffer(needed.value)
                    result = user32.GetRawInputData(
                        wintypes.HANDLE(lparam), RID_INPUT, buffer, ctypes.byref(needed),
                        ctypes.sizeof(RAWINPUTHEADER)
                    )
                    if result == UINT(-1).value:
                        errors.append(f"GetRawInputData(data) failed: {ctypes.get_last_error()}")
                    else:
                        header = RAWINPUTHEADER.from_buffer_copy(buffer.raw[:ctypes.sizeof(RAWINPUTHEADER)])
                        if header.dwType == RIM_TYPEHID:
                            offset = ctypes.sizeof(RAWINPUTHEADER)
                            if len(buffer.raw) >= offset + 8:
                                report_size = int.from_bytes(buffer.raw[offset:offset + 4], "little")
                                report_count = int.from_bytes(buffer.raw[offset + 4:offset + 8], "little")
                                payload = buffer.raw[offset + 8:needed.value]
                                path = get_device_name(header.hDevice)
                                key = hex(header.hDevice or 0)
                                if key not in active_devices:
                                    active_devices[key] = {
                                        "handle": key, "type": "hid", "device_path": path,
                                        "note": "device first observed during capture",
                                    }
                                if report_size > 0:
                                    for index in range(min(report_count, len(payload) // report_size)):
                                        report = payload[index * report_size:(index + 1) * report_size]
                                        writer.writerow([
                                            dt.datetime.now().astimezone().isoformat(timespec="milliseconds"),
                                            round(time.monotonic() - start_clock, 6),
                                            key, path, report_count, report_size, index, report.hex(" "),
                                        ])
                                        count += 1
                                    if count % 100 == 0:
                                        handle.flush()
                except Exception as exc:
                    errors.append(f"{type(exc).__name__}: {exc}")
                # DefWindowProc is required for foreground WM_INPUT cleanup.
                return user32.DefWindowProcW(hwnd, message, wparam, lparam)
            if message == WM_DESTROY:
                user32.PostQuitMessage(0)
                return 0
            return user32.DefWindowProcW(hwnd, message, wparam, lparam)

        callback = WNDPROC(window_proc)
        class_name = f"LegacyWheelHubRawInput_{os.getpid()}"
        instance = kernel32.GetModuleHandleW(None)
        wc = WNDCLASSW()
        wc.lpfnWndProc = callback
        wc.hInstance = instance
        wc.lpszClassName = class_name
        atom = user32.RegisterClassW(ctypes.byref(wc))
        if not atom:
            raise win_error("RegisterClassW")

        hwnd = user32.CreateWindowExW(
            0, class_name, class_name, 0, 0, 0, 0, 0,
            None, None, instance, None
        )
        if not hwnd:
            raise win_error("CreateWindowExW")

        flags = RIDEV_DEVNOTIFY
        if not args.foreground_only:
            flags |= RIDEV_INPUTSINK
        registrations = (RAWINPUTDEVICE * 2)(
            RAWINPUTDEVICE(GENERIC_DESKTOP_PAGE, USAGE_JOYSTICK, flags, hwnd),
            RAWINPUTDEVICE(GENERIC_DESKTOP_PAGE, USAGE_GAMEPAD, flags, hwnd),
        )
        if not user32.RegisterRawInputDevices(
            registrations, 2, ctypes.sizeof(RAWINPUTDEVICE)
        ):
            user32.DestroyWindow(hwnd)
            raise win_error("RegisterRawInputDevices")

        print(f"\nCapturando relatórios HID em: {csv_path}")
        print("Mova o volante, gire-o de batente a batente, pressione cada pedal, "
              "todos os botões, direcional e controles auxiliares.")
        print("A captura não decodifica os bytes em eixos; CTRL+C encerra.")
        try:
            msg = MSG()
            while True:
                while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_REMOVE):
                    if msg.message == 0x0012:  # WM_QUIT
                        raise KeyboardInterrupt
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))
                if args.seconds > 0 and time.monotonic() - start_clock >= args.seconds:
                    break
                time.sleep(0.001)
        except KeyboardInterrupt:
            print("\nCaptura encerrada pelo usuário.")
        finally:
            # Remove only this process's Raw Input registrations.
            removals = (RAWINPUTDEVICE * 2)(
                RAWINPUTDEVICE(GENERIC_DESKTOP_PAGE, USAGE_JOYSTICK, 0x00000001, None),
                RAWINPUTDEVICE(GENERIC_DESKTOP_PAGE, USAGE_GAMEPAD, 0x00000001, None),
            )
            user32.RegisterRawInputDevices(removals, 2, ctypes.sizeof(RAWINPUTDEVICE))
            user32.DestroyWindow(hwnd)
            user32.UnregisterClassW(class_name, instance)
            handle.flush()

    report = {
        "tool": "g27_windows_raw_input_diagnostics",
        "started_at": started,
        "ended_at": dt.datetime.now().astimezone().isoformat(),
        "capture_seconds": round(time.monotonic() - start_clock, 6),
        "report_records_written": count,
        "devices_at_start": devices,
        "devices_observed": list(active_devices.values()),
        "registered_top_level_collections": [
            {"usage_page": "0x0001", "usage": "0x0004", "name": "Joystick"},
            {"usage_page": "0x0001", "usage": "0x0005", "name": "Game Pad"},
        ],
        "csv_file": str(csv_path),
        "errors": errors,
        "limitations": [
            "Raw Input delivers HID reports for registered top-level collections; a wheel may expose other collections.",
            "Report bytes are raw payloads as delivered by Windows, not guaranteed electrical USB bus captures.",
            "The script does not parse the HID report descriptor or decode logical axes/buttons.",
            "No reports may mean the wheel uses a different usage collection or driver/API path; it does not prove the device is inactive.",
            "No output reports, registry writes, driver changes, or force-feedback commands are issued.",
        ],
    }
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Relatórios gravados: {count}\nCSV: {csv_path}\nJSON: {json_path}")
    if errors:
        print(f"Avisos/erros durante captura: {len(errors)} (consulte o JSON)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
