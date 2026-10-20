#!/usr/bin/env python3
"""Read-only Logitech G27/DFGT joystick diagnostic logger.

Install dependency: py -m pip install pygame-ce
This tool never writes to driver settings, registry, firmware, or LGS XML.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def find_lgs_profiles(exe_name: str | None) -> list[dict]:
    """Read matching LGS XML profiles without modifying them."""
    if not exe_name:
        return []
    roots = []
    for key in ("LOCALAPPDATA", "APPDATA"):
        value = os.environ.get(key)
        if value:
            roots.extend((
                Path(value) / "Logitech" / "Logitech Gaming Software" / "profiles",
                Path(value) / "Logitech" / "Gaming Software" / "profiles",
            ))
    results = []
    for base in dict.fromkeys(roots):
        if not base.is_dir():
            continue
        for path in base.rglob("*.xml"):
            try:
                root = ET.parse(path).getroot()
            except (ET.ParseError, OSError):
                continue
            targets = [
                child.text.strip()
                for node in root.iter() if local_name(node.tag) == "Target"
                for child in node if local_name(child.tag) == "Name" and child.text
            ]
            if exe_name.casefold() not in {
                os.path.basename(item.replace("\\", "/")).casefold() for item in targets
            }:
                continue
            axes = []
            for assignment in root.iter():
                if local_name(assignment.tag) != "Assignments" or assignment.get("DeviceModel") != "57":
                    continue
                for node in assignment.iter():
                    if local_name(node.tag) in ("AxisDynamics", "AxisDef") and node.get("Axis"):
                        axes.append({
                            "element": local_name(node.tag),
                            "axis": node.get("Axis"),
                            "sign": node.get("Sign"),
                            "acceleration": node.get("Acceleration"),
                            "speed": node.get("Speed"),
                            "deadzone": node.get("Deadzone"),
                        })
            results.append({"xml": str(path), "targets": targets, "axes": axes})
    return results


def read_state(joy) -> dict:
    return {
        "axes": [round(float(joy.get_axis(i)), 5) for i in range(joy.get_numaxes())],
        "buttons": [int(joy.get_button(i)) for i in range(joy.get_numbuttons())],
        "hats": [list(joy.get_hat(i)) for i in range(joy.get_numhats())],
    }


def calibrate(pygame, joy, duration: float) -> list[dict]:
    results = []
    print("\nCALIBRAÇÃO GUIADA — mova somente o pedal solicitado.")
    for pedal in ("acelerador", "freio", "embreagem"):
        input(f"Solte todos os pedais e pressione ENTER para medir repouso: {pedal}...")
        idle = []
        end = time.monotonic() + 1.5
        while time.monotonic() < end:
            pygame.event.pump()
            idle.append(read_state(joy)["axes"])
            time.sleep(0.02)
        if not idle:
            continue
        baseline = [sum(row[i] for row in idle) / len(idle)
                    for i in range(joy.get_numaxes())]
        input(f"Pressione ENTER e mantenha {pedal} totalmente pressionado por {duration:.1f}s...")
        mins, maxs = list(baseline), list(baseline)
        end = time.monotonic() + duration
        while time.monotonic() < end:
            pygame.event.pump()
            values = read_state(joy)["axes"]
            for i, value in enumerate(values):
                mins[i] = min(mins[i], value)
                maxs[i] = max(maxs[i], value)
            time.sleep(0.01)
        deltas = [max(abs(mins[i] - baseline[i]), abs(maxs[i] - baseline[i]))
                  for i in range(len(baseline))]
        idx = max(range(len(deltas)), key=deltas.__getitem__) if deltas else -1
        delta = deltas[idx] if idx >= 0 else 0.0
        direction = ("increasing" if maxs[idx] - baseline[idx] >
                     baseline[idx] - mins[idx] else "decreasing") if idx >= 0 else "unknown"
        result = {
            "pedal": pedal,
            "baseline": [round(x, 5) for x in baseline],
            "minimum": [round(x, 5) for x in mins],
            "maximum": [round(x, 5) for x in maxs],
            "axis_index_zero_based": idx,
            "axis_number_one_based": idx + 1 if idx >= 0 else None,
            "delta": round(delta, 5),
            "direction": direction,
            "confidence": "strong" if delta >= 0.35 else "weak — repeat calibration",
        }
        results.append(result)
        print(f"  {pedal}: eixo SDL #{idx + 1}, variação={delta:.3f}, direção={direction}")
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Logger somente leitura para G27/DFGT.")
    parser.add_argument("--device", type=int, default=0, help="índice do joystick (padrão 0)")
    parser.add_argument("--exe", help="nome/caminho do executável cujo XML LGS será lido")
    parser.add_argument("--output-dir", default="g27-diagnostics", help="pasta de saída")
    parser.add_argument("--skip-calibration", action="store_true", help="inicia direto o CSV")
    parser.add_argument("--calibration-seconds", type=float, default=3.0)
    parser.add_argument("--interval", type=float, default=0.02, help="intervalo em segundos (padrão 50 Hz)")
    args = parser.parse_args()

    try:
        import pygame
    except ImportError:
        print("Instale a dependência: py -m pip install pygame-ce", file=sys.stderr)
        return 2

    pygame.init()
    pygame.joystick.init()
    count = pygame.joystick.get_count()
    print(f"Joysticks encontrados: {count}")
    for i in range(count):
        item = pygame.joystick.Joystick(i)
        item.init()
        print(f"[{i}] {item.get_name()} | GUID={item.get_guid()} | axes={item.get_numaxes()} "
              f"buttons={item.get_numbuttons()} hats={item.get_numhats()}")
        item.quit()
    if count == 0 or args.device < 0 or args.device >= count:
        print("Nenhum joystick detectado ou índice inválido. Confira a lista acima.")
        pygame.quit()
        return 1

    joy = pygame.joystick.Joystick(args.device)
    joy.init()
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = Path(args.output_dir).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    csv_path = outdir / f"g27_input_{stamp}.csv"
    json_path = outdir / f"g27_report_{stamp}.json"
    exe_name = os.path.basename(args.exe) if args.exe else None
    lgs = find_lgs_profiles(exe_name)

    print(f"\nDispositivo selecionado: {joy.get_name()}")
    if args.exe:
        print(f"XMLs LGS encontrados para {exe_name}: {len(lgs)}")
        for item in lgs:
            print(f"  {item['xml']}")
            for axis in item["axes"]:
                print(f"    {axis['element']} Axis={axis['axis']} Sign={axis['sign']}")
    print("\nNota: XML indica configuração salva, não prova que o perfil esteja ativo ou aplicado.")
    print("Valores SDL/Pygame não são relatórios USB HID brutos. CTRL+C encerra o log.")
    calibration = [] if args.skip_calibration else calibrate(
        pygame, joy, max(0.5, args.calibration_seconds)
    )
    metadata = {
        "created_at": dt.datetime.now().astimezone().isoformat(),
        "device": {"index": args.device, "name": joy.get_name(), "guid": joy.get_guid(),
                   "axes": joy.get_numaxes(), "buttons": joy.get_numbuttons(),
                   "hats": joy.get_numhats()},
        "target_exe": exe_name, "lgs_profiles_read_only": lgs,
        "calibration": calibration, "csv_file": str(csv_path),
        "interval_seconds": args.interval,
        "limitations": [
            "SDL/Pygame values are not raw USB HID reports.",
            "LGS XML values do not prove runtime profile activation.",
            "The tool does not modify driver, registry, firmware, or LGS profiles.",
            "SDL axis indices are not guaranteed to match LGS Axis names such as R or Z.",
        ],
    }
    rows = 0
    try:
        with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle)
            writer.writerow(["timestamp", "elapsed_seconds"] +
                            [f"axis_{i + 1}" for i in range(joy.get_numaxes())] +
                            [f"button_{i + 1}" for i in range(joy.get_numbuttons())] +
                            [name for i in range(joy.get_numhats())
                             for name in (f"hat_{i + 1}_x", f"hat_{i + 1}_y")])
            start = time.monotonic()
            last_state = None
            while True:
                pygame.event.pump()
                state = read_state(joy)
                now = time.monotonic()
                writer.writerow([dt.datetime.now().astimezone().isoformat(timespec="milliseconds"),
                                 round(now - start, 4)] + state["axes"] + state["buttons"] +
                                [v for hat in state["hats"] for v in hat])
                rows += 1
                if state != last_state and rows % 5 == 0:
                    pressed = [i + 1 for i, value in enumerate(state["buttons"]) if value]
                    print(f"\rAmostras={rows} eixos={state['axes']} botões={pressed}   ",
                          end="", flush=True)
                last_state = state
                if rows % 50 == 0:
                    handle.flush()
                time.sleep(max(0.005, args.interval))
    except KeyboardInterrupt:
        print("\nRegistro encerrado.")
    finally:
        metadata["ended_at"] = dt.datetime.now().astimezone().isoformat()
        metadata["sample_count"] = rows
        json_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        joy.quit()
        pygame.quit()
    print(f"Amostras: {rows}\nCSV: {csv_path}\nJSON: {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
