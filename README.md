# 🏹 Knights, Archers, Zombies (KAZ) Multi-Agent RL Training Framework

This repository provides an interactive multi-agent reinforcement learning (MARL) training orchestration pipeline. It utilizes [PettingZoo's Butterfly library](https://pettingzoo.farama.org/environments/butterfly/knights_archers_zombies/) to simulate the **Knights, Archers, Zombies (v10)** parallel environment, allowing you to train multi-agent groups using value-based or policy-gradient approaches.

---

## 🗺️ System Overview

The framework orchestrates decentralized training with centralized execution hooks across custom reinforcement learning agents:
* **DQN (`DQN_Logic`):** Deep Q-Network with Experience Replay buffers and decoupled Target Networks.
* **PG (`ReinforcePolicy`):** REINFORCE Policy Gradient with baseline-subtracted advantage normalization and explicit exploration tracking via entropy.

### Architecture Workflow
1. **Instantiation:** Detects baseline environment dimensions (`state_size`, `action_space`) per agent dynamically.
2. **Interactive Handshake:** Prompts the user to select the algorithm type, deployment settings, runtime hyperparameters, and headless states.
3. **Training Loop:** Executes decentralized operations, tracking individual metrics inside parallelized environment steps.
4. **Data Aggregation:** Automatically serializes weights, exports historical tables (.CSV), and builds trend plots (.PNG) upon completion or cancellation.

---

## 🛠️ Script Features & API Core Functions

| Function / Method | Type / Signature | Return Profile | Description |
| :--- | :--- | :--- | :--- |
| `run_DQN(...)` | Core Loop | `None` | Manages the primary interactive step loop using Deep Q-Learning rules, handling epsilon decay steps globally. |
| `run_PG(...)` | Core Loop | `None` | Manages the single-trajectory Monte Carlo collection loop using Policy Gradient criteria, stepping updates at episode boundaries. |
| `get_action(state)` | Method | `int` | Samples an action from the policy using the current observation context. |
| `_plot_combined_reward_history(...)` | Utility | `None` | Uses Matplotlib to generate a 4-panel grid tracking Overall Reward, Losses, Per-Agent Profiles, and Exploitation Metrics. |
| `_export_training_history_csv(...)` | Utility | `None` | Compiles raw metric data arrays directly into structured tables for post-process evaluation. |
| `_load_agent_checkpoints(...)` | Disk I/O | `None` | Restores neural network states relative to specific agent name indexes. |
| `_save_agent_checkpoints(...)` | Disk I/O | `None` | Handles state serialization dynamically across unique sub-directories. |

---

## 🚀 Getting Started

### Prerequisites

Ensure you have your custom `DQN.py` (housing `DQN_Logic`) and `PG.py` (housing `ReinforcePolicy`) within the execution path. Install dependencies:

```bash
pip install torch numpy matplotlib pettingzoo[butterfly]

```

### Execution Pipeline

Launch the main orchestration script from your terminal:

```bash
python main.py

```

Upon launching, the interactive CLI will guide you through setup configuration profiles:

```text
Select algorithm [dqn/pg] (default dqn): dqn

Load saved model on start? [y/N]: n

Enter number of episodes (default 200): 150

Run headless? [Y/n]: y

Verbose printing? [y/N]: n

Set initial epsilon for DQN (default 1.0): 1.0

```

---

## 📊 Analytics & Training Outputs

When training concludes (or if interrupted by a `KeyboardInterrupt` / `Ctrl+C`), the system executes a graceful shutdown routine to prevent data loss. The following artifacts are written to your local working directory:

### 1. File Artifact Generation Matrix

* **`checkpoints/`**: A directory containing independent PyTorch state modules separated by naming metrics (e.g., `dqn_archer_0.pt`, `dqn_knight_0.pt`).
* **`training_history_[algo]_[timestamp].csv`**: Tabular dataset detailing overall reward histories, mean step-level losses, and per-agent returns across each episode index.
* **`reward_history_[algo]_[timestamp].png`**: High-resolution 4-subplot visualization displaying moving window metrics.

### 2. Output Panel Breakdown

The generated graph provides a vertical overview tracking:

* **Overall Reward:** Aggregated group returns alongside an $N$-episode rolling average trend line.
* **Training Loss:** Mean optimization costs highlighting model convergence or gradient spikes.
* **Per-Agent Rewards:** Individual returns tracking behavioral discrepancies between sub-classes (e.g., *Knights* vs. *Archers*).
* **Algorithmic Metric Tracking:** Dynamic tracking mapping parameter transitions over time (**Epsilon** for DQN loops or **Entropy** for PG environments).

```

```
