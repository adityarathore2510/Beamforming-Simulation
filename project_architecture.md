# 📡 5G/6G Beamforming Simulation System Architecture

## 1. Subagent Architecture Overview
To keep the system modular, scalable, and easy to explain in an interview, the project is divided into **three subagents** with equal complexity.

### 🧠 Subagent 1: Signal & Math Engine
**Role**: The foundational physical layer. It is responsible for generating the RF/baseband signals, modeling the physical space, and handling time-domain metrics.
**ECE Concepts**: Carrier wave synthesis, Wavelength/Frequency relations ($\lambda = c/f$), and Additive White Gaussian Noise (AWGN).
**Modules/Functions** (`signal_engine.py`):
- `calculate_wavelength(frequency)`
- `generate_carrier(frequency, duration, sample_rate)`
- `add_awgn_noise(signal, snr_db)`
**I/O Interface**:
- **Inputs**: Frequency (e.g., 28 GHz for 5G mmWave), Time duration, Target SNR.
- **Outputs**: Time array, raw un-steered signal arrays. Passed downstream to Subagent 2.

### ⚙️ Subagent 2: Beamforming & Simulation Core
**Role**: The "Brain" of the spatial filtering system. It controls the Uniform Linear Array (ULA) geometry and applies complex weight algorithms to electronically steer the signal.
**ECE Concepts**: Array Factor (AF), steering vectors, spatial phase shifting ($\Delta \phi = \frac{2\pi d}{\lambda} \sin(\theta)$), constructive/destructive interference.
**Modules/Functions** (`beamformer.py`):
- `compute_steering_vector(num_antennas, spacing, target_angle, wavelength)`
- `calculate_array_factor(weights, angles_grid, spacing)`
**I/O Interface**:
- **Inputs**: Number of antennas ($N$), Desired Steering Angle ($\theta$), Wavelength ($\lambda$) from Subagent 1.
- **Outputs**: Computed Array Factor (magnitude across a 180° spatial grid) ready to be plotted.

### 🖥️ Subagent 3: Visualization & GUI
**Role**: The user-facing controller. It wraps the mathematical data from Subagent 2 into a real-time reactive interface.
**ECE Concepts**: Radiation Pattern analysis (Polar coordinates), Main Lobe vs. Sidelobe visual monitoring.
**Modules/Functions** (`gui_main.py`):
- `init_gui()` (Layout constraints and widgets)
- `update_plot_canvas(array_factor_data)` (Redrawing logic)
- `on_slider_changed(value)` (Event loop call to Subagent 2)
**I/O Interface**:
- **Inputs**: Array Factor magnitude array, user UI interactions.
- **Outputs**: Visual polar plot rendering, updated parameter requests to backend.

---

## 2. Tech Stack & GUI Selection
- **Core Language**: Python 3.x
- **Data/Math**: `numpy` (crucial for fast vectorized complex math)
- **Plotting**: `matplotlib`

**GUI Recommendation: PyQt (PyQt6 / PySide6)**
*Why not Tkinter?* Tkinter is easy, but **PyQt is the industry standard for engineering tools**. For a placement project, PyQt looks instantly more impressive and native. PyQt also provides a powerful widget called `FigureCanvasQTAgg`, allowing you to embed Matplotlib polar plots right into the window. It handles real-time UI threading natively, preventing the app from freezing while recalculating complex math arrays.

---

## 3. System Data Flow
1. **App Launch**: Subagent 3 (GUI) initializes Matplotlib canvas and default variables ($N=4$, $\theta=0°$).
2. **User Input / Event**: User drags the "Target Angle" slider to 45°.
3. **Data Request**: GUI calls the update function.
4. **Parameter Fetch**: Subagent 1 confirms base Frequency/Wavelength ($\lambda$).
5. **Phase Computation**: Subagent 2 calculates the specific complex phase shifts (`w = exp(-j * ...)`) needed for each antenna to target 45°. It computes the resulting `Array Factor` across all possible angles.
6. **UI Render**: Subagent 2 drops the magnitude of the Array Factor matrix back into Subagent 3. Subagent 3 redraws the Polar Plot immediately.

---

## 4. Code Snippets Format

#### Subagent 1 snippet
```python
class SignalEngine:
    def __init__(self, frequency=28e9):
        self.wavelength = 3e8 / frequency
        
    def generate_signal(self, time):
        return np.exp(1j * 2 * np.pi * self.freq * time)
```

#### Subagent 2 snippet 
```python
def calc_array_factor(num_antennas, angle_deg, d, lam):
    theta_grid = np.linspace(-np.pi/2, np.pi/2, 500) # Angles to plot (-90 to +90)
    steer_rad = np.radians(angle_deg)
    k = 2 * np.pi / lam
    
    AF = np.zeros_like(theta_grid, dtype=complex)
    for n in range(num_antennas):
        # Calculate Phase for Steering vs Physics
        steer_phase = k * d * n * np.sin(steer_rad)
        spatial_phase = k * d * n * np.sin(theta_grid)
        AF += np.exp(1j * (spatial_phase - steer_phase))
        
    return theta_grid, np.abs(AF) / num_antennas # Normalized magnitude
```

#### Subagent 3 snippet
```python
def update_plot(self):
    angle = self.angle_slider.value()
    N = self.antenna_slider.value()
    # Ping Subagent 2
    theta, af_mag = self.beamformer.calc_array_factor(N, angle, lam/2, lam)
    
    # Update Matplotlib Polar Plot
    self.polar_line.set_ydata(af_mag)
    self.canvas.draw()
```

---

## 5. ECE Placement Interview Question Bank

1. **Q: What is Beamforming, and why is it critical for 5G mmWave?**
   *A:* Beamforming is a spatial filtering technique that uses multiple antennas to focus signal energy toward a specific receiver. It is critical for 5G mmWave because high-frequency signals suffer from severe path loss; beamforming overcomes this by massively increasing targeted signal gain.

2. **Q: How does phase-shifting actually "steer" a beam?**
   *A:* By applying calculated progressive time delays (or phase shifts) to the signal at each antenna element, the separate electromagnetic waves constructively interfere in the desired angle direction and destructively interfere in others.

3. **Q: What is the "Array Factor" (AF)?**
   *A:* The Array Factor is a mathematical function representing the radiation pattern of an array of isotropic (omnidirectional) antennas. The total radiation pattern is simply the Element Pattern multiplied by the Array Factor.

4. **Q: Why do we typically set antenna spacing ($d$) to $\lambda/2$?**
   *A:* If the spacing is larger than $\lambda/2$, unwanted secondary major beams called "Grating Lobes" appear, sending power in the wrong directions. If spaced too closely, mutual coupling decreases antenna efficiency.

5. **Q: What is the difference between Analog, Digital, and Hybrid Beamforming?**
   *A:* Analog uses hardware phase shifters in the RF chain (creating one beam). Digital computes weights in baseband processing (allowing multiple simultaneous beams). Hybrid mixes both, offering a balance of performance minus the hardware cost of fully digital Massive MIMO.

6. **Q: How does adding more antennas ($N$) change the plot you built?**
   *A:* Increasing the number of antennas increases array directivity. The Main Lobe becomes much narrower (higher resolution), the gain increases, and more nulls/sidelobes appear in the pattern.

7. **Q: What are Sidelobes, and why are they a problem?**
   *A:* Sidelobes are smaller unintended peaks of radiation. They represent wasted energy and cause signal interference for other devices in the cellular network.

8. **Q: How would you reduce these Sidelobes in your code?**
   *A:* By applying "amplitude tapering" (like Dolph-Chebyshev or Binomial windows). Instead of feeding all antennas the exact same power, the central antennas get more power and the edge antennas get less. This widens the main beam slightly but drastically crushes sidelobes.

9. **Q: What is AWGN, and why include it in a 5G simulation?**
   *A:* Additive White Gaussian Noise simulates thermal background noise and generalized interference. We use it to calculate the Signal-to-Noise Ratio (SNR) improvements our array provides over a single antenna.

10. **Q: How did you ensure your Python simulation could run in "real-time" without lagging?**
    *A:* By substituting python `for-loops` with NumPy's vectorized operations and array broadcasting. This pushes the complex matrix multiplication down to highly optimized C-layer code, allowing for sub-millisecond calculation times perfect for GUI responsiveness.
