import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

class A2C_Logic:
    def __init__(
        self,
        state_size,
        action_space,
        learning_rate=0.0005,
        gamma=0.99,
        entropy_coef=0.01,
        hidden_layer_sizes=(128, 128),
    ):
        self.state_size = int(state_size)
        self.action_space = int(action_space)
        self.gamma = float(gamma)
        self.entropy_coef = float(entropy_coef)
        self.hidden_layer_sizes = hidden_layer_sizes

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # -------------------------
        # Actor network
        # -------------------------
        actor_layers = []
        input_size = self.state_size
        for h in hidden_layer_sizes:
            actor_layers.append(nn.Linear(input_size, h))
            actor_layers.append(nn.ReLU())
            input_size = h
        actor_layers.append(nn.Linear(input_size, self.action_space))
        self.actor = nn.Sequential(*actor_layers).to(self.device)

        # -------------------------
        # Critic network
        # -------------------------
        critic_layers = []
        input_size = self.state_size
        for h in hidden_layer_sizes:
            critic_layers.append(nn.Linear(input_size, h))
            critic_layers.append(nn.ReLU())
            input_size = h
        critic_layers.append(nn.Linear(input_size, 1))
        self.critic = nn.Sequential(*critic_layers).to(self.device)

        # Optimizers
        self.actor_optimizer = optim.Adam(self.actor.parameters(), lr=learning_rate)
        self.critic_optimizer = optim.Adam(self.critic.parameters(), lr=learning_rate)

    # -------------------------------------------------------------------------
    def _flatten_state(self, state):
        return np.asarray(state, dtype=np.float32).reshape(-1)

    # -------------------------------------------------------------------------
    def get_action(self, state):
        """Select an action using the actor network."""
        state_vec = self._flatten_state(state)
        state_tensor = torch.as_tensor(state_vec, dtype=torch.float32, device=self.device).unsqueeze(0)

        logits = self.actor(state_tensor)
        dist = torch.distributions.Categorical(logits=logits)

        action = dist.sample()
        log_prob = dist.log_prob(action)
        entropy = dist.entropy()

        return int(action.item()), log_prob, entropy

    # -------------------------------------------------------------------------
    def learn(self, state, action, reward, next_state, done):
        """
        Perform one A2C update using a single transition.
        Returns: (did_learn: bool, loss_value: float)
        """

        # Convert to tensors
        state_tensor = torch.as_tensor(self._flatten_state(state), dtype=torch.float32, device=self.device).unsqueeze(0)
        next_state_tensor = torch.as_tensor(self._flatten_state(next_state), dtype=torch.float32, device=self.device).unsqueeze(0)
        action_tensor = torch.as_tensor([action], dtype=torch.int64, device=self.device)
        reward_tensor = torch.as_tensor([reward], dtype=torch.float32, device=self.device)
        done_tensor = torch.as_tensor([done], dtype=torch.float32, device=self.device)

        # ---- Forward pass ----
        logits = self.actor(state_tensor)
        dist = torch.distributions.Categorical(logits=logits)
        log_prob = dist.log_prob(action_tensor)
        entropy = dist.entropy().mean()

        value = self.critic(state_tensor).squeeze(1)
        next_value = self.critic(next_state_tensor).squeeze(1)

        # ---- TD target ----
        target = reward_tensor + self.gamma * next_value * (1 - done_tensor)

        # ---- Advantage ----
        advantage = target.detach() - value

        # ---- Actor loss ----
        actor_loss = -(log_prob * advantage.detach())

        # ---- Critic loss ----
        critic_loss = advantage.pow(2)

        # ---- Total loss ----
        loss = actor_loss + 0.5 * critic_loss - self.entropy_coef * entropy

        # ---- Backprop ----
        self.actor_optimizer.zero_grad()
        self.critic_optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.actor.parameters(), 1.0)
        torch.nn.utils.clip_grad_norm_(self.critic.parameters(), 1.0)
        self.actor_optimizer.step()
        self.critic_optimizer.step()

        return True, float(loss.item())

    # -------------------------------------------------------------------------
    def save(self, path):
        checkpoint = {
            "actor": self.actor.state_dict(),
            "critic": self.critic.state_dict(),
            "actor_opt": self.actor_optimizer.state_dict(),
            "critic_opt": self.critic_optimizer.state_dict(),
        }
        torch.save(checkpoint, path)

    # -------------------------------------------------------------------------
    def load(self, path):
        checkpoint = torch.load(path, map_location=self.device)
        self.actor.load_state_dict(checkpoint["actor"])
        self.critic.load_state_dict(checkpoint["critic"])
        self.actor_optimizer.load_state_dict(checkpoint["actor_opt"])
        self.critic_optimizer.load_state_dict(checkpoint["critic_opt"])
        self.actor.to(self.device)
        self.critic.to(self.device)
