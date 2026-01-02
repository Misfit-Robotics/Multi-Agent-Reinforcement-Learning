<h1>Robot Operating System</h1>

<p>
  A lightweight, modular robot operating system for real-time limb control, UDP-based command streaming, and
  hardware-agnostic motion execution. This project provides a clean Python interface for controlling multi-joint
  robotic limbs, performing inverse kinematics, and integrating external command sources such as gamepads,
  autonomy modules, or remote controllers.
</p>

<hr>

<h2>Features</h2>

<ul>
  <li><strong>Modular limb controller</strong>
    <ul>
      <li>Coax, femur, and tibia joint control</li>
      <li>Inverse kinematics for 3-DOF legs</li>
      <li>Configurable servo channels and geometry</li>
      <li>Hardware-agnostic design with optional Adafruit ServoKit integration</li>
    </ul>
  </li>
  <li><strong>UDP command interface</strong>
    <ul>
      <li>Low-latency command streaming</li>
      <li>Human-readable command format</li>
      <li>Supports remote shutdown, limb movement, and future extensions</li>
    </ul>
  </li>
  <li><strong>YAML-based configuration</strong>
    <ul>
      <li>Robot-wide settings</li>
      <li>Per-limb geometry and servo mapping</li>
      <li>Workspace limits for safe motion</li>
    </ul>
  </li>
  <li><strong>Testable architecture</strong>
    <ul>
      <li>Mockable hardware interfaces</li>
      <li>pytest-friendly message parsing</li>
      <li>Clear separation of logic and I/O</li>
    </ul>
  </li>
</ul>

<hr>

<h2>System Architecture Overview</h2>

<p>
  The system is designed around a clean separation of responsibilities, enabling safe hardware interaction,
  deterministic behavior, and straightforward testing. The architecture consists of four primary layers:
</p>

<ol>
  <li><strong>Configuration Layer</strong>
    <br>
    Loads robot-wide and limb-specific parameters from <code>config.yml</code>. This includes servo channels,
    geometric lengths, workspace limits, and network settings.
  </li>

  <li><strong>Communication Layer</strong>
    <br>
    A UDP listener receives commands from external sources. Messages are parsed and dispatched to the appropriate
    limb controller. This layer is stateless and easily testable.
  </li>

  <li><strong>Limb Control Layer</strong>
    <br>
    Each limb is represented by a <code>Limb</code> object responsible for:
    <ul>
      <li>Inverse kinematics calculations</li>
      <li>Servo angle computation</li>
      <li>Workspace clamping and safety enforcement</li>
      <li>Hardware output (when connected)</li>
    </ul>
  </li>

  <li><strong>Hardware Abstraction Layer</strong>
    <br>
    Provides a unified interface to servo hardware. When <code>connected = false</code>, all hardware calls are
    replaced with logging, enabling full simulation and testing without physical devices.
  </li>
</ol>

<p>
  This layered approach ensures that motion logic, communication, and hardware access remain independent,
  maintainable, and robust.
</p>

<hr>

<h2>Limb Controller Mathematics</h2>

<p>
  Each limb is modeled as a 3-DOF kinematic chain consisting of:
</p>

<ul>
  <li><strong>Coax joint</strong> – horizontal rotation (yaw)</li>
  <li><strong>Femur joint</strong> – vertical rotation (pitch)</li>
  <li><strong>Tibia joint</strong> – knee extension</li>
</ul>

<p>
  The limb controller computes joint angles from a target Cartesian position <code>(x, y, z)</code> using classical
  trigonometric inverse kinematics.
</p>

<h3>1. Horizontal Shoulder Angle (HSA)</h3>

<p>
  The coax joint rotates the limb around the vertical axis. The horizontal distance <code>h</code> is computed as:
</p>

<pre><code>h = sqrt(x² + y²)</code></pre>

<p>
  The coax angle is then:
</p>

<pre><code>HSA = atan(x / y)</code></pre>

<p>
  Additional adjustments are applied for mirrored limbs using the <code>inverse</code> flag.
</p>

<h3>2. Tibia Angle (TSA)</h3>

<p>
  The tibia angle is computed using the law of cosines. The distance from the shoulder to the foot is:
</p>

<pre><code>l = sqrt(h² + z²)</code></pre>

<p>
  Then:
</p>

<pre><code>TSA = acos((tibia² + femur² - l²) / (2 * tibia * femur))</code></pre>

<p>
  Calibration offsets and safety limits are applied to ensure the servo remains within its mechanical range.
</p>

<h3>3. Femur Angle (FSA)</h3>

<p>
  The femur angle is the sum of two components:
</p>

<ul>
  <li><strong>va</strong> – angle between the horizontal projection and the vertical axis</li>
  <li><strong>vb</strong> – interior angle from the law of cosines</li>
</ul>

<pre><code>va = atan((h - coax_length) / z)
vb = acos((l² + femur² - tibia²) / (2 * l * femur))
FSA = va + vb
</code></pre>

<p>
  The final servo command is adjusted to match the physical orientation of the femur servo horn.
</p>

<p>
  These calculations allow the limb to reach any valid point within its configured workspace while maintaining
  smooth, predictable motion.
</p>

<hr>

<h2>Project Structure</h2>

<pre>
robot_os/
│
├── limb_controller.py       # Limb class with IK and servo control
├── main.py                  # UDP command listener and dispatcher
├── config.yml               # Robot and limb configuration
├── tests/                   # pytest suite
│   ├── test_limb.py
│   └── test_message_handler.py
└── README.md
</pre>

<hr>

<h2>Installation</h2>

<h3>1. Clone the repository</h3>

<pre><code>git clone https://github.com/SWilliams17655/RobotOperatingSystem.git
cd robot-operating-system
</code></pre>

<h3>2. Install dependencies</h3>

<pre><code>pip install -r requirements.txt
</code></pre>

<p>If you are using real hardware with a PCA9685-based servo controller:</p>

<pre><code>pip install adafruit-circuitpython-servokit
</code></pre>

<hr>

<h2>Configuration</h2>

<p>
  All robot parameters are stored in <code>config.yml</code>. This includes robot-level settings, network parameters, and
  per-limb geometry and servo configuration.
</p>

<p>Example configuration:</p>

<pre><code>robot:
  name: "Hexapod"
  connected: true
  UDP_IP: "0.0.0.0"
  UDP_PORT: 5005

BR_Leg:
  coax_loc: 0
  femur_loc: 1
  tibia_loc: 2
  coax_length: 40
  femur_length: 60
  tibia_length: 80
  min_x: -50
  max_x: 50
  min_y: -50
  max_y: 50
  min_z: -80
  max_z: -10
  inverse: false
</code></pre>

<hr>

<h2>Usage</h2>

<h3>Start the robot controller</h3>

<pre><code>python main.py
</code></pre>

<p>
  On startup, the controller will:
</p>

<ul>
  <li>Load configuration values from <code>config.yml</code></li>
  <li>Initialize servos if <code>connected</code> is set to <code>true</code></li>
  <li>Bind to the configured UDP IP and port</li>
  <li>Listen for incoming command messages</li>
</ul>

<hr>

<h2>UDP Command Format</h2>

<p>
  Commands are sent as comma-separated strings over UDP to the configured IP address and port.
</p>

<h3>Move a limb</h3>

<pre><code>move_limb,BR_Leg,10,20,30
</code></pre>

<h3>Shutdown the system</h3>

<pre><code>shutdown
</code></pre>

<hr>

<h2>Testing</h2>

<pre><code>pytest -v
</code></pre>

<hr>

<h2>Development Roadmap</h2>

<ul>
  <li>[ ] Gait engine for multi-limb coordination</li>
  <li>[ ] Higher-level motion primitives (step, walk, turn)</li>
  <li>[ ] WebSocket or HTTP control interface</li>
  <li>[ ] Simulation mode with no hardware dependencies</li>
</ul>

<hr>

<hr>

<h2>License</h2>


<hr>

<h2>About</h2>

<p>
  This robot operating system is intended to provide a clear, extensible, and maintainable foundation for hobby
  robotics, research platforms, and custom autonomous systems. It emphasizes readability, testability, and safe
  operation around hardware.
</p>