# DevOTime

A Windows-only productivity tool for accurately tracking time spent working in specific programs with idle detection and customizable alerts.

<div align="center">
  <img src="assets/timericon.ico" alt="Work Timer Icon" width="64" height="64">
</div>

## Background

This program is inspired by the AutoHotkey script by Lemon Demon (Neil Cicierega) found [here](https://web.archive.org/web/20160422221339/http://neilblr.com/post/58757345346). It originally started as modifications to that script, but grew into a complete Python rewrite to better suit evolving needs.
## Features

- **Automatic Time Tracking**: Only tracks time when you're actively working in designated programs
- **Idle Detection**: Pauses tracking when the system is idle beyond a configurable timeout
- **Pause Anytime**: Quick pause button on the bar (and in menu/tray) when you don't want to track
- **Visual Indicators**: Color-coded interface (cyan for active, red for inactive) with optional border alerts
- **Edge Dock**: Collapse the timer to a slim tab on either screen edge, click the chevron to bring it back
- **System Tray**: X hides to the tray with the timer still running; double-click the icon to restore.
  While hidden, the tray icon itself displays the live timer like a clock (wider icon, color shows
  state: cyan counting, red inactive, amber paused). If the icon lands in the hidden-icons overflow,
  enable it under Settings → Personalization → Taskbar → "Other system tray icons".
- **Taskbar Timer**: Live HH:MM:SS in the taskbar with status marks (● counting, ⏸ paused, ○ idle)
- **Goal Setting**: Set daily work goals with notifications when reached
- **Customizable Shortcuts**: Configure global hotkeys for adding/removing programs
- **Audio Alerts**: Optional sound notifications for idle states
- **Time Management**: Save, restore, and manually adjust tracked time
- **Persistent Settings**: Remembers window position, dock state, tracked programs, and preferences

## Installation

An exe made using `pyinstaller` is in the Releases section, but Windows Defender thinks its malware, which seems to be a common issue. I tried signing it with a self-generated certificate, but to no avail.

If you'd like to build it from source, you can follow these steps:
1. Create a virtual environment: `python -m venv .venv`
2. Activate the virtual environment: `.\.venv\Scripts\activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Run the application: `pyinstaller main.spec`
5. The generated exe will be in the dist folder

## Usage

### Interface Overview

The application displays as a compact timer window that stays on top of other windows. The interface shows:
- **Dock Chevron (❯/❮)**: Collapse the window to the nearest screen edge / restore it
- **Pause Button (⏸)**: Pause or resume time tracking instantly
- **Add Button (+)**: Click it, then click the program window you want to track
- **Time Display**: Current tracked time in HH:MM:SS format
- **MENU Button**: Access to all settings and options
- **Hide Toggle (◉)**: Toggle to hide/show the time display
- **Color Coding**: Cyan background when actively tracking, red when inactive

The X button hides the app to the system tray (timer keeps running) — quit from the tray icon's
menu. Double-click the tray icon to show the window again. Use the "Close button hides to tray"
menu option if you'd rather X quit the app.

### Default Global Hotkeys

- **Add program**: Win+Shift+=
- **Remove program**: Win+Shift+-

### Menu Options

- **Add/Remove Programs**: Manage which programs are tracked
- **Pause Timer**: Pause/resume time tracking when you don't want to use it
- **Close Button Hides to Tray**: Toggle X behavior (tray vs quit)
- **Timeout Settings**: Configure idle timeout
- **Goal Time**: Set daily work goals with HH:MM:SS format
- **Hotkey Configuration**: Customize global shortcuts
- **Audio Settings**: Toggle idle indicator sound
- **Border Alerts**: Show screen borders when not working
- **Time Management**: Reset, resume, or manually adjust current time

## How It Works

### Program Tracking

The timer automatically detects when you're working in tracked programs by:
1. Polling the active window at a set interval
2. Checking if the current program is in your tracked list
3. Starting/stopping the timer based on program focus
4. Pausing when the system is idle beyond the configured timeout

## Important Notes

- **Program Detection**: Tracks programs by executable path, updating programs can require re-adding them sometimes
- **System Integration**: Alt+Tab, Win+Tab, desktop, and taskbar are considered part of File Explorer (explorer.exe), so it is set as tracked by default
- **Data Persistence**: Settings, window position, and previous time are automatically saved
