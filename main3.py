import gymnasium as gym
import matplotlib.pyplot as plt
from A2C import A2C_Logic   # adjust filename if needed

def main():
    env = gym.make("CartPole-v1")

    state_size = env.observation_space.shape[0]
    action_space = env.action_space.n

    agent = A2C_Logic(
        state_size=state_size,
        action_space=action_space,
        learning_rate=1e-3,
        gamma=0.99,
        entropy_coef=0.001,
        rollout_length=20,
        hidden_layer_sizes=(128, 128)
    )

    episodes = 1000
    rewards_history = []

    for episode in range(episodes):
        state, info = env.reset()
        total_reward = 0
        done = False

        # -------------------------
        # Run one full episode
        # -------------------------
        while not done:
            action = agent.get_action(state)
            next_state, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated

            agent.remember(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward

            # Learn when rollout buffer is full
            if len(agent.memory) >= agent.rollout_length:
                did_learn, loss, entropy = agent.learn()

        # End of episode — flush remaining rollout
        if len(agent.memory) > 0:
            did_learn, loss, entropy = agent.learn()
        else:
            loss, entropy = 0.0, 0.0

        rewards_history.append(total_reward)
        print(
            f"Episode {episode+1}/{episodes} — "
            f"Reward: {total_reward}, Loss: {loss:.4f}, Entropy: {entropy:.4f}"
        )

    env.close()

    # -------------------------
    # Plot training rewards
    # -------------------------
    plt.figure(figsize=(10,5))
    plt.plot(rewards_history, label="Episode Reward")
    plt.xlabel("Episode")
    plt.ylabel("Reward")
    plt.title("A2C Training Performance on CartPole-v1")
    plt.grid(True)
    plt.legend()
    plt.show()


if __name__ == "__main__":
    main()