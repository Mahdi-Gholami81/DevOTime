<div align="center">

<img src="assets/timericon.ico" alt="DevOTime Icon" width="96" height="96">

# DevOTime

A sleek, Windows-only productivity timer that tracks the time you spend
actually working — with idle detection, screen-edge docking, a live
taskbar timer, and a modern frameless UI.

[Features](#features) · [Installation](#installation) · [Usage](#usage) · [How It Works](#how-it-works)

</div>

---

## Background

Inspired by the AutoHotkey script by Lemon Demon (Neil Cicierega) found
[here](https://web.archive.org/web/20160422221339/http://neilblr.com/post/58757345346).
It originally started as modifications to that script, but grew into a
complete Python rewrite to better suit evolving needs.

## Features

### Time Tracking
- **Automatic Tracking**: Only counts time while you're actively working in designated programs
- **Idle Detection**: Pauses tracking when the system is idle beyond a configurable timeout
- **Pause Anytime**: Quick pause button on the bar (also in menu and tray)
- **Goal Setting**: Daily work goals with notifications when reached
- **Time Management**: Save, resume, and manually adjust tracked time

### Modern Interface
- **Frameless Bar**: Compact, always-on-top timer bar with a soft gradient
  and rounded corners — drag it anywhere on screen
- **Edge Dock**: Slide the timer fully off-screen with a smooth
    `cubic-bezier(0.16, 1, 0.3, 1)` transition. A subtle glassy handle
    stays pinned to the screen edge; hover it to reveal a stylized arrow,
    click to glide the window back to its saved position
- **Color Coding**: Cyan when actively tracking, red when stopped or paused

### System Integration
- **Minimize to Tray (—)**: Hides the window; the timer keeps running.
  Double-click the tray icon to restore
- **Close (×)**: Fully quits the application
- **Taskbar Timer Strip**: A live HH:MM:SS rendered right inside the
  taskbar, left of the notification area — full-size and always readable
  (tray icons are capped at 16px). Cyan = counting, red = stopped/paused.
  Click to bring the window back, right-click for the menu
- **Taskbar Title**: Live HH:MM:SS in the taskbar button with status
  marks (● counting, ⏸ paused, ○ idle)
- **Global Hotkeys**: Customizable shortcuts for adding/removing tracked programs
- **Audio Alerts**: Optional sound notification for idle states
- **Persistent Settings**: Remembers window position, dock state, tracked
  programs, and preferences

## Installation

A prebuilt exe made with `pyinstaller` is in the Releases section, but
Windows Defender tends to flag it as malware — a common issue with
unsigned pyinstaller executables.

To build from source:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
pyinstaller main.spec
```

The generated exe will be in the `dist` folder. To run directly from
source: `python main.py`

## Usage

### Interface Overview

The app shows as a compact, frameless bar that stays on top of other
windows. Drag the bar background to move it.

| Control | Action |
| --- | --- |
| **❯** | Slide the window off the nearest screen edge (dock it) |
| **⏸** | Pause / resume time tracking |
| **+** | Add a program: click, then select the program window to track |
| **HH:MM:SS** | Live time display (drag here moves the window too) |
| **MENU** | Settings and options |
| **◉** | Hide / show the time display |
| **—** | Minimize to the system tray (timer keeps running) |
| **×** | Quit DevOTime |

When docked, look for the small floating handle on the screen edge —
hover it to expand, click it to bring the timer back.

### Default Global Hotkeys

- **Add program**: `Win+Shift+=`
- **Remove program**: `Win+Shift+-`

### Menu Options

- **Add/Remove Programs**: Manage which programs are tracked
- **Pause Timer**: Pause/resume time tracking
- **Timeout Settings**: Configure idle timeout
- **Goal Time**: Set daily work goals in HH:MM:SS format
- **Hotkey Configuration**: Customize global shortcuts
- **Idle Indicator Sound**: Toggle the idle alert sound
- **Border Alerts**: Show screen borders when not working
- **Taskbar Timer Strip**: Toggle the in-taskbar timer display
- **Time Management**: Reset, resume from history, or adjust current time

## How It Works

### Program Tracking

The timer automatically detects when you're working in tracked programs:

1. Polls the active window at a set interval
2. Checks if the current program is in your tracked list
3. Starts/stops the timer based on program focus
4. Pauses when the system is idle beyond the configured timeout

## Important Notes

- **Program Detection**: Programs are tracked by executable path —
  updating a program can require re-adding it
- **System Integration**: Alt+Tab, Win+Tab, the desktop, and the taskbar
  are all part of File Explorer (explorer.exe), which is tracked by default
- **Data Persistence**: Settings, window position, and previous time are
  saved automatically

## License

Released under the [Unlicense](LICENSE.txt) — public domain.
