# visualization_gui.py
"""
Subagent 3: Visualization & GUI
=================================
Tkinter-based GUI with embedded Matplotlib for real-time beamforming visualization.

This subagent orchestrates the entire pipeline:
    User input → Signal Engine (Subagent 1) → Beamforming Core (Subagent 2) → Plot

ECE Concepts:
    - Radiation pattern interpretation (polar & Cartesian)
    - dB scale visualization
    - Real-time signal processing display
"""

import os
from datetime import datetime
import tkinter as tk
from tkinter import ttk
import numpy as np

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from signal_engine import create_signal_params
from beamforming_core import compute_array_factor, compute_pattern_metrics


class BeamformingGUI:
    """
    Main application window for the 5G Beamforming Simulator.

    Layout:
        ┌─────────────┬──────────────────────────────┐
        │  Controls    │   Polar + Cartesian Plots    │
        │  (left)      │   (right, stacked)           │
        ├─────────────┴──────────────────────────────┤
        │  Status Bar                                 │
        └─────────────────────────────────────────────┘

    The GUI calls Subagent 1 and 2 on every slider change for real-time updates.
    """

    # ─── Color Palette ─────────────────────────────────────
    BG_DARK = "#0a0e17"
    BG_PANEL = "#101829"
    BG_INPUT = "#1a2744"
    ACCENT_BLUE = "#4a9eff"
    ACCENT_PINK = "#ff4a8a"
    ACCENT_GREEN = "#00ffaa"
    ACCENT_ORANGE = "#ffaa4a"
    ACCENT_TEAL = "#6abf4b"
    TEXT_DIM = "#8899aa"
    TEXT_BRIGHT = "#ffffff"
    PLOT_BG = "#0d1224"
    GRID_COLOR = "#334455"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("5G Beamforming Simulator — ECE Project")
        self.root.geometry("1150x720")
        self.root.configure(bg=self.BG_DARK)
        self.root.minsize(950, 620)

        # Simulation state
        self.is_running = True

        # ── Configure ttk styles ──
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self._configure_styles()

        # ── Build layout ──
        self._build_control_panel()
        self._build_plot_area()
        self._build_status_bar()

        # ── Initial render ──
        self._update_plot()

    # ═══════════════════════════════════════════════════════
    #  STYLING
    # ═══════════════════════════════════════════════════════

    def _configure_styles(self):
        """Configure ttk widget styles for the dark theme."""
        self.style.configure(
            "Title.TLabel", background=self.BG_PANEL,
            foreground=self.ACCENT_BLUE, font=("Segoe UI", 14, "bold"),
        )
        self.style.configure(
            "Subtitle.TLabel", background=self.BG_PANEL,
            foreground=self.ACCENT_ORANGE, font=("Segoe UI", 9, "italic"),
        )
        self.style.configure(
            "Control.TLabel", background=self.BG_PANEL,
            foreground=self.TEXT_DIM, font=("Segoe UI", 10),
        )
        self.style.configure(
            "Value.TLabel", background=self.BG_PANEL,
            foreground=self.TEXT_BRIGHT, font=("Segoe UI", 11, "bold"),
        )
        self.style.configure(
            "Metric.TLabel", background=self.BG_PANEL,
            foreground=self.ACCENT_TEAL, font=("Consolas", 10),
        )
        self.style.configure(
            "MetricTitle.TLabel", background=self.BG_PANEL,
            foreground=self.ACCENT_BLUE, font=("Segoe UI", 10, "bold"),
        )
        self.style.configure(
            "TCombobox",
            fieldbackground=self.BG_INPUT, background=self.BG_INPUT,
            foreground=self.TEXT_BRIGHT, selectbackground=self.ACCENT_BLUE,
        )

    # ═══════════════════════════════════════════════════════
    #  CONTROL PANEL (Left Side)
    # ═══════════════════════════════════════════════════════

    def _build_control_panel(self):
        """Build the left-side control panel with all user inputs."""
        self.control_frame = tk.Frame(
            self.root, bg=self.BG_PANEL, width=290,
            relief="flat", padx=18, pady=18,
        )
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.control_frame.pack_propagate(False)

        cf = self.control_frame

        # ── Title ──
        ttk.Label(
            cf, text="🔬 Beamforming", style="Title.TLabel",
        ).pack(anchor="w", pady=(0, 0))
        ttk.Label(
            cf, text="     Simulator", style="Title.TLabel",
        ).pack(anchor="w", pady=(0, 2))
        ttk.Label(
            cf, text="  5G/6G Antenna Array Simulation", style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(0, 18))

        # ── Number of Antennas ──
        ttk.Label(cf, text="Number of Antennas", style="Control.TLabel").pack(anchor="w")
        self.antenna_var = tk.IntVar(value=16)
        self.antenna_label = ttk.Label(cf, text="N = 16", style="Value.TLabel")
        self.antenna_label.pack(anchor="w")
        self.antenna_slider = tk.Scale(
            cf, from_=2, to=64, orient=tk.HORIZONTAL,
            variable=self.antenna_var, showvalue=False,
            bg=self.BG_PANEL, fg=self.ACCENT_BLUE, troughcolor=self.BG_INPUT,
            highlightthickness=0, length=240, sliderlength=18,
            activebackground=self.ACCENT_BLUE,
            command=self._on_slider_change,
        )
        self.antenna_slider.pack(pady=(0, 12))
        self.antenna_slider.bind("<MouseWheel>", self._on_mousewheel_antenna)

        # ── Steering Angle ──
        ttk.Label(cf, text="Steering Angle (θ°)", style="Control.TLabel").pack(anchor="w")
        self.angle_var = tk.IntVar(value=0)
        self.angle_label = ttk.Label(cf, text="θ = 0°", style="Value.TLabel")
        self.angle_label.pack(anchor="w")
        self.angle_slider = tk.Scale(
            cf, from_=-90, to=90, orient=tk.HORIZONTAL,
            variable=self.angle_var, showvalue=False,
            bg=self.BG_PANEL, fg=self.ACCENT_PINK, troughcolor=self.BG_INPUT,
            highlightthickness=0, length=240, sliderlength=18,
            activebackground=self.ACCENT_PINK,
            command=self._on_slider_change,
        )
        self.angle_slider.pack(pady=(0, 12))
        self.angle_slider.bind("<MouseWheel>", self._on_mousewheel_angle)

        # ── Frequency ──
        ttk.Label(cf, text="Carrier Frequency", style="Control.TLabel").pack(anchor="w")
        self.freq_var = tk.DoubleVar(value=28.0)
        freq_frame = tk.Frame(cf, bg=self.BG_PANEL)
        freq_frame.pack(anchor="w", pady=(2, 12))
        self.freq_entry = tk.Entry(
            freq_frame, textvariable=self.freq_var, width=8,
            bg=self.BG_INPUT, fg=self.TEXT_BRIGHT,
            insertbackground=self.TEXT_BRIGHT,
            font=("Consolas", 11), relief="flat", bd=2,
        )
        self.freq_entry.pack(side=tk.LEFT, ipady=2)
        self.freq_entry.bind("<Return>", lambda e: self._on_slider_change())
        tk.Label(
            freq_frame, text=" GHz", bg=self.BG_PANEL,
            fg=self.TEXT_DIM, font=("Segoe UI", 10),
        ).pack(side=tk.LEFT)

        # ── Window Type ──
        ttk.Label(cf, text="Amplitude Taper / Window", style="Control.TLabel").pack(anchor="w")
        self.window_var = tk.StringVar(value="uniform")
        self.window_combo = ttk.Combobox(
            cf, textvariable=self.window_var, state="readonly",
            values=["uniform", "hamming", "hanning", "chebyshev"],
            width=18, font=("Consolas", 10),
        )
        self.window_combo.pack(anchor="w", pady=(2, 18))
        self.window_combo.bind("<<ComboboxSelected>>", lambda e: self._on_slider_change())

        # ── Separator ──
        ttk.Separator(cf, orient="horizontal").pack(fill="x", pady=5)

        # ── Metrics Panel ──
        ttk.Label(cf, text="📊 Pattern Metrics", style="MetricTitle.TLabel").pack(
            anchor="w", pady=(10, 6),
        )
        self.metric_beamwidth = ttk.Label(
            cf, text="Beamwidth :  --", style="Metric.TLabel",
        )
        self.metric_beamwidth.pack(anchor="w", pady=1)
        self.metric_peak = ttk.Label(
            cf, text="Peak Angle:  --", style="Metric.TLabel",
        )
        self.metric_peak.pack(anchor="w", pady=1)
        self.metric_sll = ttk.Label(
            cf, text="SLL       :  --", style="Metric.TLabel",
        )
        self.metric_sll.pack(anchor="w", pady=1)

        # ── Separator ──
        ttk.Separator(cf, orient="horizontal").pack(fill="x", pady=12)

        # ── Start / Stop Buttons ──
        btn_frame = tk.Frame(cf, bg=self.BG_PANEL)
        btn_frame.pack(pady=5)
        self.start_btn = tk.Button(
            btn_frame, text="▶  Start", bg="#1a5c2a", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat",
            padx=18, pady=6, cursor="hand2",
            activebackground="#2a8c3a", activeforeground="white",
            command=self._start_simulation,
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = tk.Button(
            btn_frame, text="■  Stop", bg="#8b1a1a", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat",
            padx=18, pady=6, cursor="hand2",
            activebackground="#bb2a2a", activeforeground="white",
            command=self._stop_simulation,
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.download_btn = tk.Button(
            btn_frame, text="💾 Download Plot", bg="#2a5c8a", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat",
            padx=18, pady=6, cursor="hand2",
            activebackground="#4a7cba", activeforeground="white",
            command=self._download_plot,
        )
        self.download_btn.pack(side=tk.LEFT, padx=5)

        # ── Info footer ──
        tk.Label(
            cf, text="Built with NumPy + Matplotlib",
            bg=self.BG_PANEL, fg="#334455", font=("Segoe UI", 8),
        ).pack(side=tk.BOTTOM, pady=(10, 0))

    # ═══════════════════════════════════════════════════════
    #  PLOT AREA (Right Side)
    # ═══════════════════════════════════════════════════════

    def _build_plot_area(self):
        """Build the Matplotlib figure with polar and Cartesian subplots."""
        self.plot_frame = tk.Frame(self.root, bg=self.BG_DARK)
        self.plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Create Matplotlib figure
        self.fig = Figure(figsize=(8, 6.5), dpi=100, facecolor=self.BG_DARK)
        self.fig.subplots_adjust(hspace=0.45, top=0.93, bottom=0.08, left=0.1, right=0.95)

        # ── Polar Plot (top) ──
        self.ax_polar = self.fig.add_subplot(211, polar=True)
        self.ax_polar.set_facecolor(self.PLOT_BG)
        self.ax_polar.tick_params(colors=self.TEXT_DIM, labelsize=8)
        self.ax_polar.set_title(
            "Radiation Pattern (Polar)",
            color=self.ACCENT_BLUE, fontsize=11, fontweight="bold", pad=15,
        )
        self.ax_polar.set_theta_zero_location("N")   # 0° at top (broadside)
        self.ax_polar.set_theta_direction(-1)         # Clockwise
        self.ax_polar.set_rlabel_position(135)
        self.ax_polar.grid(True, alpha=0.2, color=self.GRID_COLOR)

        # Initialize polar line
        self.polar_line, = self.ax_polar.plot(
            [], [], color=self.ACCENT_GREEN, linewidth=1.8, alpha=0.9,
        )
        # Fill under the polar curve
        self.polar_fill = None

        # ── Cartesian Plot (bottom) ──
        self.ax_cart = self.fig.add_subplot(212)
        self.ax_cart.set_facecolor(self.PLOT_BG)
        self.ax_cart.tick_params(colors=self.TEXT_DIM, labelsize=8)
        self.ax_cart.set_xlabel(
            "Observation Angle θ (degrees)",
            color=self.TEXT_DIM, fontsize=9,
        )
        self.ax_cart.set_ylabel(
            "Array Factor (dB)",
            color=self.TEXT_DIM, fontsize=9,
        )
        self.ax_cart.set_title(
            "Array Factor vs. Angle",
            color=self.ACCENT_BLUE, fontsize=11, fontweight="bold",
        )
        self.ax_cart.set_xlim(-90, 90)
        self.ax_cart.set_ylim(-50, 5)
        self.ax_cart.grid(True, alpha=0.15, color=self.GRID_COLOR)

        # Style the spines
        for spine in self.ax_cart.spines.values():
            spine.set_color(self.GRID_COLOR)
            spine.set_linewidth(0.5)

        # Initialize Cartesian line
        self.cart_line, = self.ax_cart.plot(
            [], [], color=self.ACCENT_PINK, linewidth=1.8, alpha=0.9,
        )
        # -3 dB reference line
        self.ax_cart.axhline(
            y=-3, color=self.ACCENT_ORANGE, linestyle=":",
            alpha=0.5, linewidth=1, label="-3 dB level",
        )
        # Steering angle indicator
        self.steering_vline = self.ax_cart.axvline(
            x=0, color=self.ACCENT_ORANGE, linestyle="--",
            alpha=0.7, linewidth=1.2, label="Steering angle",
        )
        self.ax_cart.legend(
            loc="upper right", fontsize=7,
            facecolor=self.BG_PANEL, edgecolor=self.GRID_COLOR,
            labelcolor=self.TEXT_DIM,
        )

        # Embed figure in Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    # ═══════════════════════════════════════════════════════
    #  STATUS BAR
    # ═══════════════════════════════════════════════════════

    def _build_status_bar(self):
        """Build the bottom status bar."""
        self.status_var = tk.StringVar(value="Ready — adjust controls to begin")
        self.status_bar = tk.Label(
            self.root, textvariable=self.status_var,
            bg="#060a12", fg=self.ACCENT_BLUE, anchor="w",
            font=("Consolas", 9), padx=12, pady=5,
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # ═══════════════════════════════════════════════════════
    #  UPDATE LOGIC  (Orchestrates Subagent 1 → 2 → Render)
    # ═══════════════════════════════════════════════════════

    def _on_slider_change(self, *_args):
        """Callback fired on any slider/input change."""
        self.antenna_label.config(text=f"N = {self.antenna_var.get()}")
        self.angle_label.config(text=f"θ = {self.angle_var.get()}°")
        if self.is_running:
            self._update_plot()

    def _update_plot(self):
        """
        Core update pipeline:
            1. Read GUI state
            2. Call Subagent 1: create_signal_params()
            3. Call Subagent 2: compute_array_factor() + compute_pattern_metrics()
            4. Update Matplotlib plots and metric labels
        """
        # ── Read current values ──
        num_antennas = self.antenna_var.get()
        steering_angle = self.angle_var.get()
        window_type = self.window_var.get()

        try:
            freq_ghz = self.freq_var.get()
            if freq_ghz <= 0:
                freq_ghz = 28.0
                self.freq_var.set(28.0)
        except (tk.TclError, ValueError):
            freq_ghz = 28.0
            self.freq_var.set(28.0)

        # ════════════════════════════════════════════════
        #  SUBAGENT 1: Signal Engine
        # ════════════════════════════════════════════════
        params = create_signal_params(num_antennas, freq_ghz)

        # ════════════════════════════════════════════════
        #  SUBAGENT 2: Beamforming Core
        # ════════════════════════════════════════════════
        theta_range, af_db = compute_array_factor(
            params, steering_angle, window_type=window_type,
        )
        metrics = compute_pattern_metrics(af_db, theta_range, steering_angle)

        # ════════════════════════════════════════════════
        #  SUBAGENT 3 (self): Visualization
        # ════════════════════════════════════════════════

        # ── Update Polar Plot ──
        theta_rad = np.radians(theta_range)
        af_linear = 10 ** (af_db / 20)          # dB → linear for polar radius
        af_linear = np.clip(af_linear, 0, 1)
        self.polar_line.set_data(theta_rad, af_linear)
        self.ax_polar.set_rlim(0, 1)

        # Update polar fill (remove old, draw new)
        if self.polar_fill is not None:
            self.polar_fill.remove()
        self.polar_fill = self.ax_polar.fill(
            theta_rad, af_linear,
            alpha=0.15, color=self.ACCENT_GREEN,
        )[0]

        # ── Update Cartesian Plot ──
        self.cart_line.set_data(theta_range, af_db)
        self.steering_vline.set_xdata([steering_angle])

        # ── Update Metrics Labels ──
        self.metric_beamwidth.config(
            text=f"Beamwidth :  {metrics['beamwidth_3db']}°",
        )
        self.metric_peak.config(
            text=f"Peak Angle:  {metrics['peak_angle']}°",
        )
        self.metric_sll.config(
            text=f"SLL       :  {metrics['sidelobe_level_db']} dB",
        )

        # ── Update Status Bar ──
        self.status_var.set(
            f"Simulating  •  {num_antennas} elements  •  "
            f"{freq_ghz} GHz  •  θ = {steering_angle}°  •  "
            f"Window: {window_type}"
        )

        # ── Efficient redraw ──
        self.canvas.draw_idle()

    # ═══════════════════════════════════════════════════════
    #  START / STOP
    # ═══════════════════════════════════════════════════════

    def _start_simulation(self):
        """Resume simulation (enable real-time updates on slider change)."""
        self.is_running = True
        self.status_var.set("▶ Simulation RUNNING")
        self._update_plot()

    def _stop_simulation(self):
        """Pause simulation (freeze current plot, ignore slider changes)."""
        self.is_running = False
        self.status_var.set("■ Simulation PAUSED — plots frozen")

    # ═══════════════════════════════════════════════════════
    #  NEW FEATURES
    # ═══════════════════════════════════════════════════════

    def _on_mousewheel_antenna(self, event):
        """Handle mouse wheel scrolling for the antenna slider."""
        current = self.antenna_var.get()
        # event.delta is > 0 for scrolling up, < 0 for scrolling down
        step = 1 if event.delta > 0 else -1
        new_val = max(2, min(64, current + step))
        if new_val != current:
            self.antenna_var.set(new_val)
            self._on_slider_change()

    def _on_mousewheel_angle(self, event):
        """Handle mouse wheel scrolling for the angle slider."""
        current = self.angle_var.get()
        step = 1 if event.delta > 0 else -1
        new_val = max(-90, min(90, current + step))
        if new_val != current:
            self.angle_var.set(new_val)
            self._on_slider_change()

    def _download_plot(self):
        """Save the current Matplotlib figure to the ./results folder."""
        # 1. Ensure the results directory exists
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)
        
        # 2. Get current state for filename
        N = self.antenna_var.get()
        theta = self.angle_var.get()
        freq = self.freq_var.get()
        window = self.window_var.get()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 3. Create descriptive filename
        filename = f"Beamforming_N{N}_T{theta}_F{freq}GHz_{window}_{timestamp}.png"
        filepath = os.path.join(results_dir, filename)
        
        # 4. Save and update status
        try:
            self.fig.savefig(filepath, dpi=300, facecolor=self.BG_DARK, bbox_inches='tight')
            self.status_var.set(f"✅ Successfully saved plot to {filepath}")
        except Exception as e:
            self.status_var.set(f"❌ Failed to save plot: {str(e)}")
