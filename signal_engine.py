# signal_engine.py
"""
Subagent 1: Signal & Math Engine
=================================
Handles signal generation, antenna geometry, and electromagnetic wave physics.

ECE Concepts:
    - Carrier frequency and wavelength (λ = c/f)
    - Half-wavelength antenna spacing (d = λ/2) to avoid grating lobes
    - Uniform Linear Array (ULA) geometry
    - Complex exponential signal representation
"""

import numpy as np
from dataclasses import dataclass

# Physical constant: speed of light (m/s)
C = 3e8


@dataclass
class SignalParams:
    """
    Bundles all signal and antenna parameters for downstream processing.

    This dataclass serves as the interface between Subagent 1 (Signal Engine)
    and Subagent 2 (Beamforming Core).

    Attributes:
        num_antennas:      Number of antenna elements in the ULA
        frequency_hz:      Carrier frequency in Hz
        wavelength:        Wavelength in meters (λ = c/f)
        element_spacing:   Inter-element spacing in meters (d = λ/2)
        antenna_positions: 1D array of antenna x-positions in meters
    """
    num_antennas: int
    frequency_hz: float
    wavelength: float
    element_spacing: float
    antenna_positions: np.ndarray


def compute_wavelength(freq_hz: float) -> float:
    """
    Calculate wavelength from carrier frequency.

        λ = c / f

    Args:
        freq_hz: Carrier frequency in Hertz (must be positive)

    Returns:
        Wavelength in meters

    Raises:
        ValueError: If frequency is not positive
    """
    if freq_hz <= 0:
        raise ValueError("Frequency must be positive.")
    return C / freq_hz


def compute_element_spacing(wavelength: float) -> float:
    """
    Compute half-wavelength antenna spacing.

        d = λ / 2

    Half-wavelength spacing is the standard for ULAs because:
        - It prevents grating lobes in the visible region
        - It maximizes spatial sampling without aliasing

    Args:
        wavelength: Wavelength in meters

    Returns:
        Element spacing in meters
    """
    return wavelength / 2.0


def generate_antenna_positions(num_elements: int, spacing: float) -> np.ndarray:
    """
    Generate positions of a Uniform Linear Array (ULA).

    Elements are placed along the x-axis starting at origin (0, 0).
    Position of element n:  x_n = n * d,  for n = 0, 1, ..., N-1

    Args:
        num_elements: Number of antenna elements (N >= 1)
        spacing:      Inter-element spacing in meters

    Returns:
        1D numpy array of shape (num_elements,) with x-positions
    """
    return np.arange(num_elements) * spacing


def generate_carrier_signal(
    freq_hz: float,
    duration: float = 1e-9,
    sample_rate: float = 100e9,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate a time-domain carrier signal for visualization.

        s(t) = cos(2π·f·t)

    This is useful for showing the raw waveform in the GUI.

    Args:
        freq_hz:     Carrier frequency in Hz
        duration:    Signal duration in seconds (default: 1 ns)
        sample_rate: Sampling rate in Hz (default: 100 GHz for mmWave)

    Returns:
        Tuple of (time_array, signal_array), both 1D numpy arrays
    """
    t = np.arange(0, duration, 1 / sample_rate)
    signal = np.cos(2 * np.pi * freq_hz * t)
    return t, signal


def create_signal_params(num_antennas: int, freq_ghz: float = 28.0) -> SignalParams:
    """
    Master function — create a complete SignalParams bundle.

    This is the primary interface function called by the GUI (Subagent 3).
    It computes all derived quantities from user inputs.

    Args:
        num_antennas: Number of antenna elements (typically 2–64)
        freq_ghz:     Carrier frequency in GHz (default: 28 GHz for 5G mmWave)

    Returns:
        SignalParams dataclass with all derived quantities

    Example:
        >>> params = create_signal_params(16, 28.0)
        >>> print(f"λ = {params.wavelength*1000:.2f} mm")
        λ = 10.71 mm
    """
    freq_hz = freq_ghz * 1e9
    wavelength = compute_wavelength(freq_hz)
    spacing = compute_element_spacing(wavelength)
    positions = generate_antenna_positions(num_antennas, spacing)

    return SignalParams(
        num_antennas=num_antennas,
        frequency_hz=freq_hz,
        wavelength=wavelength,
        element_spacing=spacing,
        antenna_positions=positions,
    )
