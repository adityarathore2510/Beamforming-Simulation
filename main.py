# main.py
"""
5G Beamforming Simulator — Entry Point
=======================================
Launches the Tkinter-based GUI for real-time beamforming visualization.

Project Structure:
    main.py                → This file (entry point)
    signal_engine.py       → Subagent 1: Signal & Math Engine
    beamforming_core.py    → Subagent 2: Beamforming & Simulation Core
    visualization_gui.py   → Subagent 3: Visualization & GUI

Usage:
    python main.py
"""

import tkinter as tk
from visualization_gui import BeamformingGUI


def main():
    """Initialize and run the Beamforming Simulator application."""
    root = tk.Tk()

    # Set window icon title (platform-dependent)
    try:
        root.iconbitmap(default="")
    except tk.TclError:
        pass

    # Create the application
    app = BeamformingGUI(root)

    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"+{x}+{y}")

    # Start the Tkinter event loop
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass # Handle user-triggered exit (Ctrl+C) gracefully

if __name__ == "__main__":
    main()
