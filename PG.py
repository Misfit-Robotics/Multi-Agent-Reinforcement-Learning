import numpy as np
import os
import torch
import torch.nn as nn
import torch.optim as optim

class ReinforcePolicy:
    def __init__( self, state_size=None, action_space=None, learning_rate=0.001, gamma=0.99, hidden_layer_sizes=[64, 64], entropy_coef=0.01):

        self.action_space = int(action_space)
        self.state_size = int(state_size)
        self.learning_rate = float(learning_rate)
        self.gamma = float(gamma)
        self.entropy_coef = float(entropy_coef)
        self.hidden_layer_sizes = tuple(int(h) for h in hidden_layer_sizes)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Build policy network
        layers = []
        input_size = self.state_size
        for h in self.hidden_layer_sizes:
            layers.append(nn.Linear(input_size, h))
            layers.append(nn.ReLU())
            input_size = h
        layers.append(nn.Linear(input_size, self.action_space))  # logits
        self.policy = nn.Sequential(*layers).to(self.device)

        self.optimizer = optim.Adam(self.policy.parameters(), lr=self.learning_rate)

        # Storage for one episode
        self.log_probs = []
        self.entropies = []
        self.rewards = []
        self.last_entropy_mean = 0.0

    #*********************************************************************************#
    def _flatten_state(self, state):
        """Convert observations of any shape into a 1D float32 vector."""
        return np.asarray(state, dtype=np.float32).reshape(-1)

    #*********************************************************************************#
    def get_action(self, state):
        """
        Sample an action from the current policy and store its log-prob.
        state: np.ndarray of shape (state_size,)
        """
        
        state_vec = self._flatten_state(state)

        state_tensor = torch.as_tensor(
            np.expand_dims(state_vec, axis=0),
            device=self.device,
            dtype=torch.float32,
        )

        # Forward pass with gradients enabled for proper backprop
        self.policy.eval()
        logits = self.policy(state_tensor)

        # Construct from logits for numerical stability.
        dist = torch.distributions.Categorical(logits=logits)
        action = dist.sample()
        log_prob = dist.log_prob(action)  
        entropy = dist.entropy()

        # Store log_prob for this time step
        self.log_probs.append(log_prob)
        self.entropies.append(entropy)
        return int(action.item())

    #*********************************************************************************#
    def remember_reward(self, reward):
        """Store reward for this time step."""
        self.rewards.append(float(reward))

    #*********************************************************************************#
    def _compute_returns(self):
        """Compute discounted returns G_t for each time step."""
        returns = []
        G = 0.0
        for r in reversed(self.rewards):
            G = r + self.gamma * G
            returns.append(G)
        returns.reverse() # Calculate G from back to front, then reverse to match time steps
        returns = torch.as_tensor(returns, dtype=torch.float32, device=self.device)

        return returns

    #*********************************************************************************#
    def learn(self):
        """
        Perform one REINFORCE update using the stored episode trajectory.
        Returns: (did_learn: bool, loss_value: float)
        """
        if not self.log_probs or not self.rewards:
            self.last_entropy_mean = 0.0
            return False, 0.0

        returns = self._compute_returns()
        advantages = returns - returns.mean()
        advantages = advantages / (advantages.std(unbiased=False) + 1e-8)

        self.policy.train()

        log_probs_tensor = torch.stack(self.log_probs)
        entropy_tensor = torch.stack(self.entropies)
        self.last_entropy_mean = float(entropy_tensor.mean().detach().item())
        policy_loss = -(log_probs_tensor * advantages).sum()
        entropy_bonus = entropy_tensor.sum()
        loss = policy_loss - self.entropy_coef * entropy_bonus

        self.optimizer.zero_grad()
        loss.backward()
        
        # Clip gradients for stability
        torch.nn.utils.clip_grad_norm_(self.policy.parameters(), max_norm=1.0)
        
        self.optimizer.step()

        # Clear episode storage
        self.log_probs.clear()
        self.entropies.clear()
        self.rewards.clear()

        return True, float(loss.item())

    #*********************************************************************************#
    def save(self, path):
        """Save the policy network and optimizer state to disk."""
        checkpoint = {
            "policy_state_dict": self.policy.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
        }
        torch.save(checkpoint, path)

    #*********************************************************************************#
    def load(self, path):
        """Load policy network and optimizer state from disk."""
        checkpoint = torch.load(path, map_location=self.device)

        # Backward compatibility: support plain policy state_dict files.
        if isinstance(checkpoint, dict) and "policy_state_dict" in checkpoint:
            self.policy.load_state_dict(checkpoint["policy_state_dict"])
            optimizer_state = checkpoint.get("optimizer_state_dict")
            if optimizer_state is not None:
                self.optimizer.load_state_dict(optimizer_state)
        else:
            self.policy.load_state_dict(checkpoint)

        self.policy.to(self.device)
