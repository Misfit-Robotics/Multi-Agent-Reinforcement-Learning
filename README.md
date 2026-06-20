# ReinforcePolicy Documentation

The `ReinforcePolicy` class implements a clean, production-ready version of the classic **REINFORCE (Policy Gradient)** algorithm with an **entropy bonus** for exploration and **advantage normalization** for training stability. It is built using PyTorch and accommodates discrete action spaces.

---

## 1. Overview
REINFORCE is a model-free, policy-gradient method in Reinforcement Learning. It directly updates a neural network policy based on the total discounted return accumulated across an entire episode (Monte Carlo sampling). 

This implementation includes two vital modern stability enhancements:
1. **Advantage Tracking & Normalization:** Subtracts the mean return and divides by the standard deviation across the episode trajectory to reduce policy variance.
2. **Entropy Regularization:** Introduces an entropy bonus ($H(\pi)$) to the objective function, preventing the policy from collapsing prematurely into deterministic actions and encouraging early-stage exploration.

---

## 2. Mathematical Foundation

The loss function optimized during the `learn()` phase combines the policy gradient loss and an exploration-promoting entropy term:

$$L = L_{\text{policy}} - \beta \cdot L_{\text{entropy}}$$

### Policy Loss
The policy gradient loss utilizes baseline-subtracted and normalized returns (advantages, $A_t$) calculated across an episode trajectory of length $T$:

$$L_{\text{policy}} = - \sum_{t=1}^{T} \log \pi_\theta(a_t | s_t) \cdot A_t$$

Where the normalized advantage $A_t$ for a discounted return $G_t = \sum_{k=t}^{T} \gamma^{k-t} R_k$ is computed as:

$$A_t = \frac{G_t - \mu_G}{\sigma_G + \epsilon}$$

### Entropy Bonus
To sustain exploration, the categorical distribution entropy is maximized (subtracted from loss, scaled by $\beta$ / `entropy_coef`):

$$L_{\text{entropy}} = \sum_{t=1}^{T} H\left(\pi_\theta(\cdot | s_t)\right)$$

---

## 3. API Reference & Parameters

### Initialization Matrix
| Parameter / Method | Type / Signature | Default / Return | Description |
| :--- | :--- | :--- | :--- |
| `state_size` | `int` | *Required* | Dimensionality of the incoming observation space. |
| `action_space` | `int` | *Required* | Total number of discrete actions available. |
| `learning_rate` | `float` | `0.001` | Learning rate parameter for the Adam optimizer. |
| `gamma` | `float` | `0.99` | Discount factor ($\gamma$) for future tracking rewards. |
| `hidden_layer_sizes` | `list` | `[64, 64]` | Architecture array representing sequential fully-connected layers. |
| `entropy_coef` | `float` | `0.01` | Scaling factor ($\beta$) balancing exploration vs. exploitation. |
| `get_action(state)` | Method | `int` | Samples an action from the policy using the current observation context. |
