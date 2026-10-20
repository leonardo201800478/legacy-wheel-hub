# Legacy Wheel Hub

[![release](https://img.shields.io/github/v/release/leonardo201800478/legacy-wheel-hub)](https://github.com/leonardo201800478/legacy-wheel-hub/releases)
[![downloads](https://img.shields.io/github/downloads/leonardo201800478/legacy-wheel-hub/total)](https://github.com/leonardo201800478/legacy-wheel-hub/releases)
[![license](https://img.shields.io/badge/license-GPLv3-blue)](LICENSE)
![platform](https://img.shields.io/badge/platform-Windows%2010%2F11-blue)

Control panel for the Logitech Driving Force GT and G27 on Windows 10/11.
Replaces what Logitech Gaming Software used to do: rotation range, force
feedback strength, spring and damper, per-game profiles, and a LUT curve in
games that have no LUT of their own.

## Setup

Install the wheel drivers first. Nothing here ships Logitech drivers:

> https://github.com/Mysli0210/Legacy-Logitech-wheels-for-W11

**Release status:** there is currently no published GitHub Release or verified
`LegacyWheelHub_Setup.exe` available in this repository. Do not download an
installer from an unverified mirror.

The DirectInput proxy is built by GitHub Actions for x86 and x64, with SHA-256
provenance manifests. Those CI artifacts are development outputs, not a signed
installer or a complete application release. See
[the packaging/provenance audit](docs/PACKAGING_PROVENANCE_AUDIT_20261020.md).

**Security:** do not disable Microsoft Defender, Kaspersky, SmartScreen, Memory
Integrity, or other protections to install or run this software. If an antivirus
detects a file, do not restore it or add an exclusion just to make the app work.
Preserve the detection name and file hash and submit the file to the vendor for
analysis through its official false-positive/malware-reporting process.

## What it does

- Rotation range, 40–900°, with presets
- Overall strength, spring, damper, centering spring, centering ramp
- Profiles per game: settings, rotation and LUT all switch when the game starts
- LUT support in games that don't have it
- Telemetry and input monitor for checking buttons, axes and pedals
- FFB test bench: push, spring, sweep, pulse, vibration
- Auto-load on connect, start with Windows, tray minimize
- EN / TR / DE, light and dark

Settings go to `%APPDATA%\\Legacy Wheel Hub\\settings.json`.

## LUT

Gear-driven wheels lose small forces to friction, so the wheel feels dead
around center. A LUT remaps the game's output to compensate.

Import a `.lut` in the LUT tab, tick Enable FFB post-processing, and assign
the game in the profile. Build your own curve with WheelCheck + LUT Generator,
or reuse one per profile.

Skip this in Assetto Corsa, ACC and iRacing. They already apply their own LUT
and you'd get the curve twice.

**Online games:** this drops a `dinput8.dll` next to the game executable.
Anti-cheat may not like that. Your call, your risk.

## Direção do projeto

Este fork amplia as funções do projeto de origem e busca reproduzir, para o G27, recursos úteis do Logitech Gaming Software 5 sem depender do LGS. A inversão efetiva dos pedais e o mapeamento de botões do volante para teclas do teclado são objetivos em desenvolvimento, não funções que devam ser consideradas concluídas apenas porque aparecem nas configurações. A implementação deve usar componentes compatíveis com Windows 11 e preservar o Force Feedback e as proteções de segurança do sistema.

- [Objetivos e roteiro de paridade com LGS 5 para G27 no Windows 11](docs/ROADMAP_LGS5_PARITY_G27_WINDOWS11.md)
- [Implementação da inversão de pedais: contrato, estado e integração pendente](docs/PEDAL_INVERSION_IMPLEMENTATION.md)

## Documentação técnica

- [Arquitetura dos drivers do G27 no Windows, HID, DirectInput, LGS e plano de investigação](docs/LOGITECH_G27_WINDOWS_DRIVER_ARCHITECTURE.md)
- [Ferramentas manuais de diagnóstico de eixos e pedais do G27](docs/G27_INPUT_DIAGNOSTICS.md)
- [Captura avançada de relatórios HID via Windows Raw Input](tools/g27_windows_raw_input_diagnostics.py)

## License

GPL-3.0, because PySide6-Fluent-Widgets is. Full text in `LICENSE`, or
https://www.gnu.org/licenses/gpl-3.0.txt

## Disclaimer

Not affiliated with Logitech. "Logitech", "Driving Force" and "G27" are their
trademarks, used here to say what hardware this works with. Talks to the wheel
over USB HID and the driver's own registry settings. No Logitech code or files
are redistributed. Use at your own risk.

## Acknowledgments

Developed with assistance from [Claude](https://claude.ai).
