# beamforming_core.py
"""
Subagent 2: Beamforming & Simulation Core
==========================================
Computes phase-shift weights and Array Factor radiation patterns.

ECE Concepts:
    - Beam steering via progressive phase shift
    - Array Factor: AF(θ) = Σ wₙ · exp(j·2π·d·n·sin(θ)/λ)
    - Constructive/destructive interference
    - Sidelobe suppression via amplitude tapering (windowing)
    - Spatial filtering
    - 5G/6G Massive MIMO foundations
"""

import numpy as np
from signal_engine import SignalParams


def compute_steering_weights(
    params: SignalParams,
    steering_angle_deg: float,
) -> np.ndarray:
    """
    Compute complex phase-shift weights for beam steering.

    Each antenna element n gets weight:
        w_n = exp(-j · 2π · d · n · sin(θ₀) / λ)

    This creates a progressive phase shift across the array such that
    signals from all elements arrive in-phase at the desired angle θ₀,
    producing constructive interference (maximum radiation) there.

    Args:
        params:             SignalParams from the Signal Engine
        steering_angle_deg: Desired beam direction in degrees (-90 to +90)

    Returns:
        Complex numpy array of shape (num_antennas,) with unit-magnitude weights
    """
    theta_0 = np.radians(steering_angle_deg)
    n = np.arange(params.num_antennas)
    phase = 2 * np.pi * params.element_spacing * n * np.sin(theta_0) / params.wavelength
    return np.exp(-1j * phase)


def apply_window(weights: np.ndarray, window_type: str = "uniform") -> np.ndarray:
    """
    Apply amplitude tapering (windowing) to the steering weights.

    Amplitude tapering reduces sidelobe levels at the cost of a wider main beam.
    This is a fundamental trade-off in array signal processing.

    Supported windows:
        - 'uniform'   : No tapering (default). First SLL ≈ -13.2 dB
        - 'hamming'    : Good sidelobe suppression. First SLL ≈ -42 dB
        - 'hanning'    : Smooth roll-off. First SLL ≈ -31 dB
        - 'chebyshev'  : Equi-ripple sidelobes (approximated via Kaiser, β=6)

    Args:
        weights:     Complex steering weights array
        window_type: Name of the windowing function

    Returns:
        Tapered complex weights (element-wise multiplication)
    """
    n = len(weights)
    if window_type == "uniform":
        taper = np.ones(n)
    elif window_type == "hamming":
        taper = np.hamming(n)
    elif window_type == "hanning":
        taper = np.hanning(n)
    elif window_type == "chebyshev":
        taper = np.kaiser(n, beta=6)  # Kaiser approximation of Chebyshev
    else:
        taper = np.ones(n)

    return weights * taper


def compute_array_factor(
    params: SignalParams,
    steering_angle_deg: float,
    theta_range: np.ndarray | None = None,
    window_type: str = "uniform",
) -> tuple[np.ndarray, np.ndarray]:
    """
    Compute the Array Factor across all observation angles.

    The Array Factor for a ULA is:
        AF(θ) = Σ_{n=0}^{N-1}  w_n · exp(j · 2π · d · n · sin(θ) / λ)

    This uses vectorized NumPy operations (outer product + matrix multiply)
    for efficient computation across 1000 angle samples simultaneously.

    Args:
        params:             SignalParams from the Signal Engine
        steering_angle_deg: Desired beam direction in degrees
        theta_range:        Array of observation angles in degrees (default: -90 to +90)
        window_type:        Amplitude tapering window name

    Returns:
        Tuple of:
            - theta_range: 1D array of angles in degrees, shape (M,)
            - af_db:       1D array of normalized AF magnitude in dB, shape (M,)
    """
    if theta_range is None:
        theta_range = np.linspace(-90, 90, 1000)

    theta_rad = np.radians(theta_range)

    # Step 1: Compute steering weights
    weights = compute_steering_weights(params, steering_angle_deg)

    # Step 2: Apply amplitude taper
    weights = apply_window(weights, window_type)

    # Step 3: Element indices
    n = np.arange(params.num_antennas)

    # Step 4: Phase matrix — shape (num_angles, num_antennas)
    #   Each entry [i, n] = 2π·d·n·sin(θ_i)/λ
    phase_matrix = (
        2 * np.pi * params.element_spacing
        * np.outer(np.sin(theta_rad), n)
        / params.wavelength
    )

    # Step 5: Array Factor = sum of weighted phase contributions
    #   AF(θ_i) = Σ_n  w_n · exp(j · phase[i,n])
    af = np.dot(np.exp(1j * phase_matrix), weights)

    # Step 6: Normalize to dB scale
    af_magnitude = np.abs(af)
    af_magnitude = af_magnitude / np.max(af_magnitude)       # Normalize peak to 1
    af_db = 20 * np.log10(af_magnitude + 1e-12)              # Avoid log(0)

    return theta_range, af_db


def compute_3db_beamwidth(af_db: np.ndarray, theta_range: np.ndarray) -> float:
    """
    Calculate the -3 dB beamwidth (angular width of main lobe at half-power).

    The -3 dB point is where the power drops to half of the peak value.
    In dB: 10·log₁₀(0.5) ≈ -3.01 dB.

    Args:
        af_db:       Normalized AF magnitude in dB
        theta_range: Corresponding angles in degrees

    Returns:
        Beamwidth in degrees (0.0 if cannot be determined)
    """
    above_3db = theta_range[af_db >= -3.0]
    if len(above_3db) < 2:
        return 0.0
    return float(above_3db[-1] - above_3db[0])


def compute_pattern_metrics(
    af_db: np.ndarray,
    theta_range: np.ndarray,
    steering_angle_deg: float,
) -> dict:
    """
    Compute key radiation pattern metrics for display in the GUI.

    Metrics computed:
        - beamwidth_3db:      Half-power beamwidth in degrees
        - peak_angle:         Angle of maximum radiation in degrees
        - sidelobe_level_db:  Highest sidelobe level relative to main beam (dB)
        - steering_angle:     The requested steering angle (for reference)

    Args:
        af_db:               Normalized AF magnitude in dB
        theta_range:         Angles in degrees
        steering_angle_deg:  Requested steering angle

    Returns:
        Dictionary with metric names and values
    """
    # Find peak
    peak_idx = np.argmax(af_db)
    peak_angle = theta_range[peak_idx]

    # 3 dB beamwidth
    beamwidth = compute_3db_beamwidth(af_db, theta_range)

    # Sidelobe level: maximum outside the main lobe (-3 dB region)
    main_lobe_mask = af_db >= -3.0
    sidelobe_region = af_db.copy()
    sidelobe_region[main_lobe_mask] = -100  # Exclude main lobe
    sll = float(np.max(sidelobe_region)) if np.any(~main_lobe_mask) else -100.0

    return {
        "beamwidth_3db": round(beamwidth, 2),
        "peak_angle": round(peak_angle, 2),
        "sidelobe_level_db": round(sll, 2),
        "steering_angle": steering_angle_deg,
    }
