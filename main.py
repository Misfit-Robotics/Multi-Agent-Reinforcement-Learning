import csv
import os
import time
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from pettingzoo.butterfly import knights_archers_zombies_v10
from DQN import DQN_Logic
from PG import ReinforcePolicy
from A2C import A2C_Logic
from PPO import PPOPolicy


#***************************************************************************************************************#
def _prompt_int(prompt_text, default=200):
    """Prompts for an integer value and returns a validated result."""
    raw_value = input(f"\n{prompt_text} (default {default}): ").strip()
    if not raw_value:
        return default

    try:
        value = int(raw_value)
    except ValueError:
        print(f"Invalid value '{raw_value}'. Using default {default}.")
        return default

    return value


#***************************************************************************************************************#
def _prompt_float(prompt_text, default=1.0, min_value=None, max_value=None):
    """Prompts for a float value and returns a validated result."""
    raw_value = input(f"\n{prompt_text} (default {default}): ").strip()
    if not raw_value:
        return default

    try:
        value = float(raw_value)
    except ValueError:
        print(f"Invalid value '{raw_value}'. Using default {default}.")
        return default

    if min_value is not None and value < min_value:
        print(f"Value must be >= {min_value}. Using default {default}.")
        return default

    if max_value is not None and value > max_value:
        print(f"Value must be <= {max_value}. Using default {default}.")
        return default

    return value


#***************************************************************************************************************#
def _prompt_yes_no(prompt_text, default=False):
    """Prompts for a yes/no response and returns a validated boolean result."""
    default_label = "Y/n" if default else "y/N"
    while True:
        response = input(f"\n{prompt_text} [{default_label}]: ").strip().lower()
        if response == "":
            return default
        if response in ("y", "yes"):
            return True
        if response in ("n", "no"):
            return False
        print("Invalid selection. Enter y or n.")


#***************************************************************************************************************#
def _prompt_algorithm(default="dqn"):
    raw_value = input("\nSelect algorithm [dqn/pg/a2c/ppo] (default dqn): ").strip().lower()
    if not raw_value:
        return default

    if raw_value in {"dqn", "pg", "a2c", "ppo"}:
        return raw_value

    print(f"Invalid value '{raw_value}'. Using default {default}.")
    return default


#***************************************************************************************************************#
def _checkpoint_dir():
    """Returns the directory path for saving/loading model checkpoints."""

    return os.path.join(os.path.dirname(__file__), "checkpoints")


#***************************************************************************************************************#
def _checkpoint_path(algorithm, agent_name):
    """Returns the file path for a specific agent's checkpoint."""

    return os.path.join(_checkpoint_dir(), f"{algorithm.lower()}_{agent_name}.pt")


#***************************************************************************************************************#
def _load_agent_checkpoints(agent_policies, algorithm):
    """Loads the checkpoints for all agents."""
    loaded_agents = []
    missing_agents = []

    for agent_name, policy in agent_policies.items():
        checkpoint_path = _checkpoint_path(algorithm, agent_name)
        if os.path.exists(checkpoint_path):
            policy.load(checkpoint_path)
            loaded_agents.append(agent_name)
        else:
            missing_agents.append(agent_name)

    if loaded_agents:
        print(f"Loaded saved {algorithm.upper()} model(s) for agents: {loaded_agents}")
    if missing_agents:
        print(f"No saved {algorithm.upper()} checkpoint found for agents: {missing_agents}")


#***************************************************************************************************************#
def _save_agent_checkpoints(agent_policies, algorithm):
    """Saves the checkpoints for all agents."""

    os.makedirs(_checkpoint_dir(), exist_ok=True)

    for agent_name, policy in agent_policies.items():
        checkpoint_path = _checkpoint_path(algorithm, agent_name)
        policy.save(checkpoint_path)

    print(f"Saved {algorithm.upper()} model checkpoints to {_checkpoint_dir()}")

#***************************************************************************************************************#
def _progress_bar(current, total, bar_length=40):
    """Displays a progress bar."""
    fraction = current / total
    filled = int(fraction * bar_length)
    bar = "#" * filled + "-" * (bar_length - filled)
    print(f"\r[{bar}] {current}/{total} ({fraction*100:5.1f}%)", end="")
    if current == total:
        print()  # newline at end

#***************************************************************************************************************#
def _plot_combined_reward_history(step_rewards, 
    per_agent_rewards,
    loss_history,
    metric_history=None,
    metric_label="Metric",
    moving_avg_window=50,
    output_path="reward_history_combined.png",):

    """Plot and save reward, loss, per-agent reward, and algorithm metric trends."""
    if per_agent_rewards is None:
        per_agent_rewards = {}
    if metric_history is None:
        metric_history = []

    if len(step_rewards) == 0 and not per_agent_rewards and len(loss_history) == 0 and len(metric_history) == 0:
        print("No rewards collected. Skipping reward graph.")
        return

    fig, (ax_overall, ax_loss, ax_agents, ax_metric) = plt.subplots(4, 1, figsize=(12, 18), sharex=True)

    if len(step_rewards) > 0:
        rewards_arr = np.asarray(step_rewards, dtype=np.float32)
        ax_overall.plot(rewards_arr, color="steelblue", linewidth=1.0, alpha=0.8, label="Episode Total Reward")

        if len(rewards_arr) >= moving_avg_window:
            kernel = np.ones(moving_avg_window, dtype=np.float32) / moving_avg_window
            moving_avg = np.convolve(rewards_arr, kernel, mode="valid")
            moving_x = np.arange(moving_avg_window - 1, len(rewards_arr))
            ax_overall.plot(
                moving_x,
                moving_avg,
                color="crimson",
                linewidth=2.0,
                label=f"{moving_avg_window}-Episode Moving Avg",
            )
    else:
        ax_overall.text(0.5, 0.5, "No overall reward data", ha="center", va="center", transform=ax_overall.transAxes)

    ax_overall.legend()
    ax_overall.set_ylabel("Reward")
    ax_overall.grid(alpha=0.3)

    if len(loss_history) > 0:
        loss_arr = np.asarray(loss_history, dtype=np.float32)
        ax_loss.plot(loss_arr, color="darkgreen", linewidth=1.5, alpha=0.9, label="Episode Mean Loss")

        if len(loss_arr) >= moving_avg_window:
            kernel = np.ones(moving_avg_window, dtype=np.float32) / moving_avg_window
            moving_avg_loss = np.convolve(loss_arr, kernel, mode="valid")
            moving_x = np.arange(moving_avg_window - 1, len(loss_arr))
            ax_loss.plot(
                moving_x,
                moving_avg_loss,
                color="goldenrod",
                linewidth=2.0,
                label=f"{moving_avg_window}-Episode Loss Avg",
            )
        ax_loss.legend()
    else:
        ax_loss.text(0.5, 0.5, "No loss data", ha="center", va="center", transform=ax_loss.transAxes)

    ax_loss.set_ylabel("Loss")
    ax_loss.grid(alpha=0.3)

    has_agent_data = False
    for agent_name, rewards in per_agent_rewards.items():
        if len(rewards) > 0:
            has_agent_data = True
            arr = np.asarray(rewards, dtype=np.float32)
            ax_agents.plot(arr, linewidth=1.2, alpha=0.8, label=f"{agent_name} reward")

            if len(arr) >= moving_avg_window:
                kernel = np.ones(moving_avg_window, dtype=np.float32) / moving_avg_window
                moving_avg_agent = np.convolve(arr, kernel, mode="valid")
                moving_x = np.arange(moving_avg_window - 1, len(arr))
                ax_agents.plot(
                    moving_x,
                    moving_avg_agent,
                    linewidth=2.0,
                    alpha=0.9,
                    linestyle="--",
                    label=f"{agent_name} {moving_avg_window}-ep avg",
                )

    if has_agent_data:
        ax_agents.legend(ncol=2)
    else:
        ax_agents.text(0.5, 0.5, "No per-agent reward data", ha="center", va="center", transform=ax_agents.transAxes)

    ax_agents.set_ylabel("Reward")
    ax_agents.grid(alpha=0.3)

    if len(metric_history) > 0:
        metric_arr = np.asarray(metric_history, dtype=np.float32)
        ax_metric.plot(metric_arr, color="purple", linewidth=1.5, alpha=0.9, label=f"Episode {metric_label}")

        if len(metric_arr) >= moving_avg_window:
            kernel = np.ones(moving_avg_window, dtype=np.float32) / moving_avg_window
            moving_avg_metric = np.convolve(metric_arr, kernel, mode="valid")
            moving_x = np.arange(moving_avg_window - 1, len(metric_arr))
            ax_metric.plot(
                moving_x,
                moving_avg_metric,
                color="black",
                linewidth=2.0,
                label=f"{moving_avg_window}-Episode {metric_label} Avg",
            )
        ax_metric.legend()
    else:
        ax_metric.text(0.5, 0.5, f"No {metric_label.lower()} data", ha="center", va="center", transform=ax_metric.transAxes)

    ax_metric.set_xlabel("Episode")
    ax_metric.set_ylabel(metric_label)
    ax_metric.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    print(f"Saved combined reward graph to {output_path}")
    plt.show()

#***************************************************************************************************************#
def _export_training_history_csv(step_rewards, 
                                 per_agent_rewards, 
                                 loss_history, 
                                 output_path="training_history.csv"):
    """Export overall reward, per-agent reward, and loss history to a CSV file."""
    if per_agent_rewards is None:
        per_agent_rewards = {}

    if len(step_rewards) == 0 and not per_agent_rewards and len(loss_history) == 0:
        print("No training history collected. Skipping CSV export.")
        return

    agent_names = sorted(per_agent_rewards.keys())
    max_rows = max(
        len(step_rewards),
        len(loss_history),
        max((len(per_agent_rewards[name]) for name in agent_names), default=0),
    )

    headers = ["episode", "overall_reward", "mean_loss"] + [f"{agent}_reward" for agent in agent_names]

    with open(output_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)

        for episode_idx in range(max_rows):
            row = [episode_idx + 1]
            row.append(step_rewards[episode_idx] if episode_idx < len(step_rewards) else "")
            row.append(loss_history[episode_idx] if episode_idx < len(loss_history) else "")

            for agent_name in agent_names:
                agent_values = per_agent_rewards.get(agent_name, [])
                row.append(agent_values[episode_idx] if episode_idx < len(agent_values) else "")

            writer.writerow(row)

    print(f"Saved training history CSV to {output_path}")


#***************************************************************************************************************#
def run_DQN(num_episodes=100, 
            env = None, 
            max_steps_per_episode=2000, 
            epsilon = 1.0, 
            epsilon_decay=0.9995, 
            epsilon_min=0.1, 
            render=True, 
            render_sleep=0.02, 
            verbose=False, 
            load_saved_model=False):

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = f"training_history_dqn_{timestamp}.csv"
    png_path = f"reward_history_dqn_{timestamp}.png"

    #render_mode = "human" if render else None

    observations, infos = env.reset()

    agent_policies = {}
    for agent, obs in observations.items():
        state_size = obs.size
        action_size = env.action_space(agent).n
        agent_policies[agent] = DQN_Logic(
            state_size=state_size,
            action_space=action_size,
            learning_rate=0.0005,
            gamma=0.99,
            epsilon=epsilon,
            train_set_size=50000,
            batch_size=64,
            target_update_steps=500,
            hidden_layer_sizes=(128, 128),
        )

    print(f"Initialized DQN policies for agents:", list(agent_policies.keys()))

    if load_saved_model:
        _load_agent_checkpoints(agent_policies, "dqn")
        # Keep scheduler state aligned with loaded policies.
        epsilon = agent_policies[next(iter(agent_policies))].epsilon

    episode_reward_history = []
    episode_loss_history = []
    epsilon_history = []
    per_agent_reward_history = {agent: [] for agent in agent_policies}

    try:
        for episode in range(1, num_episodes + 1):
            if not verbose:
                _progress_bar(episode, num_episodes)
            observations, infos = env.reset()
            episode_rewards = {agent: 0.0 for agent in agent_policies}
            episode_losses = []
            episode_steps = 0

            for step in range(1, max_steps_per_episode + 1):
                if not env.agents:
                    break

                actions = {}
                observations_before = {}

                for agent in env.agents:
                    obs = observations[agent]
                    observations_before[agent] = obs
                    action = agent_policies[agent].get_action(obs)
                    actions[agent] = int(np.clip(action, 0, env.action_space(agent).n - 1))

                observations_after, rewards, terminations, truncations, infos = env.step(actions)

                for agent, state in observations_before.items():
                    action = actions[agent]
                    reward = rewards.get(agent, 0.0)
                    done = terminations.get(agent, False) or truncations.get(agent, False)
                    next_state = observations_after.get(agent, np.zeros_like(state))
                    agent_policies[agent].remember(state, action, reward, next_state, done) 
                    episode_rewards[agent] += float(reward)

                
                for agent in observations_before:
                    trained, loss = agent_policies[agent].learn()
                    if trained:
                        episode_losses.append(loss)

                if render:
                    env.render()
                    if render_sleep > 0:
                        time.sleep(render_sleep)

                observations = observations_after
                episode_steps = step

                if all(terminations.get(a, False) or truncations.get(a, False) for a in observations_before):
                    break

            epsilon = max(epsilon_min, epsilon - epsilon_decay)
            for agent in agent_policies.values():
                agent.epsilon = epsilon

            total_reward = sum(episode_rewards.values())
            mean_loss = float(np.mean(episode_losses)) if episode_losses else 0.0

            episode_reward_history.append(total_reward)
            episode_loss_history.append(mean_loss)
            epsilon_history.append(epsilon)

            for agent in per_agent_reward_history:
                per_agent_reward_history[agent].append(episode_rewards.get(agent, 0.0))

            reward_summary = ", ".join(
                f"{agent}={episode_rewards[agent]:.2f}"
                for agent in sorted(episode_rewards)
            )
            metric_text = f"epsilon={epsilon:.4f}"

            if verbose:
                print(
                    f"Episode {episode}/{num_episodes} | steps={episode_steps} | "
                    f"algo=DQN | {metric_text} | "
                    f"total_reward={total_reward:.2f} | mean_loss={mean_loss:.4f}"
                )
                print("  Per-agent rewards:", reward_summary)
                print()
    except KeyboardInterrupt:
        print("\nTraining interrupted by user. Saving progress...")
    
    finally:
        env.close()

        _export_training_history_csv(
            episode_reward_history,
            per_agent_reward_history,
            episode_loss_history,
            output_path=csv_path,
        )
        _plot_combined_reward_history(
            episode_reward_history,
            per_agent_reward_history,
            episode_loss_history,
            metric_history=epsilon_history,
            metric_label="Epsilon",
            output_path=png_path,
        )
        _save_agent_checkpoints(agent_policies, "dqn")

#***************************************************************************************************************#
def run_PG(num_episodes=100, env = None, 
           max_steps_per_episode=2000, 
           render=True, 
           render_sleep=0.02, 
           verbose=False, 
           load_saved_model=False):

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = f"training_history_pg_{timestamp}.csv"
    png_path = f"reward_history_pg_{timestamp}.png"

    observations, infos = env.reset()

    agent_policies = {}
    for agent, obs in observations.items():
        state_size = obs.size
        action_size = env.action_space(agent).n
        
        agent_policies[agent] = ReinforcePolicy(
            state_size=state_size,
            action_space=action_size,
            learning_rate=0.0005,
            gamma=0.99,
            entropy_coef=0.01,
            hidden_layer_sizes=(128, 128),
        )

    print(f"Initialized PG policies for agents:", list(agent_policies.keys()))

    if load_saved_model:
        _load_agent_checkpoints(agent_policies, "pg")

    episode_reward_history = []
    episode_loss_history = []
    entropy_history = []
    per_agent_reward_history = {agent: [] for agent in agent_policies}

    try:
        for episode in range(1, num_episodes + 1):
            if not verbose:
                _progress_bar(episode, num_episodes)
            observations, infos = env.reset()
            episode_rewards = {agent: 0.0 for agent in agent_policies}
            episode_losses = []
            episode_steps = 0

            for step in range(1, max_steps_per_episode + 1):
                if not env.agents:
                    break

                actions = {}
                observations_before = {}

                for agent in env.agents:
                    obs = observations[agent]
                    observations_before[agent] = obs
                    action = agent_policies[agent].get_action(obs)
                    actions[agent] = int(np.clip(action, 0, env.action_space(agent).n - 1))

                observations_after, rewards, terminations, truncations, infos = env.step(actions)

                for agent, state in observations_before.items():
                    reward = rewards.get(agent, 0.0)
                    done = terminations.get(agent, False) or truncations.get(agent, False)
                    agent_policies[agent].remember_reward(reward) 
                    episode_rewards[agent] += float(reward)

                
                if render:
                    env.render()
                    if render_sleep > 0:
                        time.sleep(render_sleep)

                observations = observations_after
                episode_steps = step

                if all(terminations.get(a, False) or truncations.get(a, False) for a in observations_before):
                    break

            # REINFORCE update happens once per episode.
            for agent in agent_policies:
                trained, loss = agent_policies[agent].learn()
                if trained:
                    episode_losses.append(loss)

            total_reward = sum(episode_rewards.values())
            mean_loss = float(np.mean(episode_losses)) if episode_losses else 0.0

            episode_reward_history.append(total_reward)
            episode_loss_history.append(mean_loss)
            entropy_history.append(agent_policies[next(iter(agent_policies))].last_entropy_mean)

            for agent in per_agent_reward_history:
                per_agent_reward_history[agent].append(episode_rewards.get(agent, 0.0))

            reward_summary = ", ".join(
                f"{agent}={episode_rewards[agent]:.2f}"
                for agent in sorted(episode_rewards)
            )
            metric_text = f"entropy={agent_policies[next(iter(agent_policies))].last_entropy_mean:.4f}"

            if verbose:
                print(
                    f"Episode {episode}/{num_episodes} | steps={episode_steps} | "
                    f"algo=PG | {metric_text} | "
                    f"total_reward={total_reward:.2f} | mean_loss={mean_loss:.4f}"
                )
                print("  Per-agent rewards:", reward_summary)
    except KeyboardInterrupt:
        print("\nTraining interrupted by user. Saving progress...")
    
    finally:
        env.close()

        _export_training_history_csv(
            episode_reward_history,
            per_agent_reward_history,
            episode_loss_history,
            output_path=csv_path,
        )
        _plot_combined_reward_history(
            episode_reward_history,
            per_agent_reward_history,
            episode_loss_history,
            metric_history=entropy_history,
            metric_label="Entropy",
            output_path=png_path,
        )
        _save_agent_checkpoints(agent_policies, "pg")

#***************************************************************************************************************#
def run_A2C(num_episodes=100, 
            env=None, 
            max_steps_per_episode=2000, 
            render=True, 
            render_sleep=0.02, 
            verbose=False, 
            load_saved_model=False,):

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = f"training_history_a2c_{timestamp}.csv"
    png_path = f"reward_history_a2c_{timestamp}.png"

    observations, infos = env.reset()

    # Initialize A2C policies
    agent_policies = {}
    for agent, obs in observations.items():
        state_size = obs.size
        action_size = env.action_space(agent).n

        agent_policies[agent] = A2C_Logic(
            state_size=state_size,
            action_space=action_size,
            learning_rate=0.0005,
            gamma=0.99,
            entropy_coef=0.01,
            hidden_layer_sizes=(128, 128),
        )

    print("Initialized A2C policies for agents:", list(agent_policies.keys()))

    if load_saved_model:
        _load_agent_checkpoints(agent_policies, "a2c")

    episode_reward_history = []
    episode_loss_history = []
    entropy_history = []
    per_agent_reward_history = {agent: [] for agent in agent_policies}

    try:
        for episode in range(1, num_episodes + 1):
            if not verbose:
                _progress_bar(episode, num_episodes)

            observations, infos = env.reset()
            episode_rewards = {agent: 0.0 for agent in agent_policies}
            episode_losses = []
            episode_steps = 0

            for step in range(1, max_steps_per_episode + 1):
                if not env.agents:
                    break

                actions = {}
                log_probs = {}
                entropies = {}
                observations_before = {}

                for agent in env.agents:
                    obs = observations[agent]
                    observations_before[agent] = obs

                    action, log_prob, entropy = agent_policies[agent].get_action(obs)
                    actions[agent] = int(action)
                    log_probs[agent] = log_prob
                    entropies[agent] = entropy

                
                observations_after, rewards, terminations, truncations, infos = env.step(actions)

                # ---- A2C LEARNING ----
                for agent, state in observations_before.items():
                    reward = rewards.get(agent, 0.0)
                    done = terminations.get(agent, False) or truncations.get(agent, False)
                    next_state = observations_after.get(agent, np.zeros_like(state))

                    trained, loss = agent_policies[agent].learn(
                        state=state,
                        action=actions[agent],
                        reward=reward,
                        next_state=next_state,
                        done=done,
                    )

                    if trained:
                        episode_losses.append(loss)

                    episode_rewards[agent] += float(reward)

                # ---- RENDER ----
                if render:
                    env.render()
                    if render_sleep > 0:
                        time.sleep(render_sleep)

                observations = observations_after
                episode_steps = step

                # End episode if all agents terminated
                if all(terminations.get(a, False) or truncations.get(a, False) for a in observations_before):
                    break

            # -----------------------------
            # END OF EPISODE
            # -----------------------------
            total_reward = sum(episode_rewards.values())
            mean_loss = float(np.mean(episode_losses)) if episode_losses else 0.0

            episode_reward_history.append(total_reward)
            episode_loss_history.append(mean_loss)
            entropy_history.append(0.0)  # optional: track entropy if desired

            for agent in per_agent_reward_history:
                per_agent_reward_history[agent].append(episode_rewards.get(agent, 0.0))

            if verbose:
                print(
                    f"Episode {episode}/{num_episodes} | steps={episode_steps} | "
                    f"algo=A2C | total_reward={total_reward:.2f} | mean_loss={mean_loss:.4f}"
                )

    except KeyboardInterrupt:
        print("\nTraining interrupted by user. Saving progress...")

    finally:
        env.close()

        _export_training_history_csv(
            episode_reward_history,
            per_agent_reward_history,
            episode_loss_history,
            output_path=csv_path,
        )

        _plot_combined_reward_history(
            episode_reward_history,
            per_agent_reward_history,
            episode_loss_history,
            metric_history=entropy_history,
            metric_label="Entropy",
            output_path=png_path,
        )

        _save_agent_checkpoints(agent_policies, "a2c")


#*********************************************************************************#
def run_PPO(
    num_episodes=100,
    env=None,
    max_steps_per_episode=2000,
    render=True,
    render_sleep=0.02,
    verbose=False,
    load_saved_model=False,
):

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = f"training_history_ppo_{timestamp}.csv"
    png_path = f"reward_history_ppo_{timestamp}.png"

    observations, infos = env.reset()

    agent_policies = {}
    for agent, obs in observations.items():
        state_size = obs.size
        action_size = env.action_space(agent).n

        agent_policies[agent] = PPOPolicy(
            state_size=state_size,
            action_space=action_size,
            learning_rate=0.0003,
            gamma=0.99,
            lam=0.95,
            clip_eps=0.2,
            entropy_coef=0.01,
            value_coef=0.5,
            batch_size=256,
            update_epochs=4,
            hidden_layer_sizes=(128, 128),
        )

    print("Initialized PPO policies for agents:", list(agent_policies.keys()))

    if load_saved_model:
        _load_agent_checkpoints(agent_policies, "ppo")

    episode_reward_history = []
    episode_loss_history = []
    entropy_history = []
    per_agent_reward_history = {agent: [] for agent in agent_policies}

    try:
        for episode in range(1, num_episodes + 1):
            if not verbose:
                _progress_bar(episode, num_episodes)

            observations, infos = env.reset()
            episode_rewards = {agent: 0.0 for agent in agent_policies}
            episode_losses = []
            episode_steps = 0

            for step in range(1, max_steps_per_episode + 1):
                if not env.agents:
                    break

                actions = {}
                observations_before = {}

                for agent in env.agents:
                    obs = observations[agent]
                    observations_before[agent] = obs
                    action = agent_policies[agent].get_action(obs)
                    actions[agent] = int(action)

                observations_after, rewards, terminations, truncations, infos = env.step(actions)

                for agent, state in observations_before.items():
                    reward = rewards.get(agent, 0.0)
                    done = terminations.get(agent, False) or truncations.get(agent, False)
                    agent_policies[agent].remember_reward(reward, done)
                    episode_rewards[agent] += float(reward)

                if render:
                    env.render()
                    if render_sleep > 0:
                        time.sleep(render_sleep)

                observations = observations_after
                episode_steps = step

                if all(terminations.get(a, False) or truncations.get(a, False) for a in observations_before):
                    break

            # PPO update happens once per episode
            for agent in agent_policies:
                trained, loss = agent_policies[agent].learn()
                if trained:
                    episode_losses.append(loss)

            total_reward = sum(episode_rewards.values())
            mean_loss = float(np.mean(episode_losses)) if episode_losses else 0.0

            episode_reward_history.append(total_reward)
            episode_loss_history.append(mean_loss)
            entropy_history.append(0.0)  # PPO entropy is inside loss, but you can track it if you want

            for agent in per_agent_reward_history:
                per_agent_reward_history[agent].append(episode_rewards.get(agent, 0.0))

            if verbose:
                print(
                    f"Episode {episode}/{num_episodes} | steps={episode_steps} | "
                    f"algo=PPO | total_reward={total_reward:.2f} | mean_loss={mean_loss:.4f}"
                )

    except KeyboardInterrupt:
        print("\nTraining interrupted by user. Saving progress...")

    finally:
        env.close()

        _export_training_history_csv(
            episode_reward_history,
            per_agent_reward_history,
            episode_loss_history,
            output_path=csv_path,
        )
        _plot_combined_reward_history(
            episode_reward_history,
            per_agent_reward_history,
            episode_loss_history,
            metric_history=entropy_history,
            metric_label="Entropy",
            output_path=png_path,
        )
        _save_agent_checkpoints(agent_policies, "ppo")

#*********************************************************************************#
if __name__ == "__main__":
    selected_algorithm = _prompt_algorithm(default="dqn")
    load_saved_model = _prompt_yes_no("Load saved model on start?", default=False)
    num_episodes = _prompt_int("Enter number of episodes", default=100)
    headless = _prompt_yes_no("Run headless?", default=True)
    verbose = _prompt_yes_no("Verbose printing?", default=False)

    env = knights_archers_zombies_v10.parallel_env(
        render_mode="human" if not headless else None,
        spawn_rate=5,
        max_cycles=2000
    )

    if selected_algorithm == "dqn":
        initial_epsilon = _prompt_float("Set initial epsilon for DQN", default=1.0, min_value=0.0, max_value=1.0)
        epsilon_min = 0.1  # You can adjust this value as needed
        epsilon_decay = (initial_epsilon - epsilon_min) / (num_episodes / 2) 
        run_DQN(
            num_episodes=num_episodes,
            env=env,
            max_steps_per_episode=2000,
            epsilon=initial_epsilon,
            epsilon_decay=epsilon_decay,
            epsilon_min=epsilon_min,
            render=not headless,
            render_sleep=0.02,
            verbose=verbose,
            load_saved_model=load_saved_model,
        )

    if selected_algorithm == "ppo":
        run_PPO(
            num_episodes=num_episodes,
            env=env,
            max_steps_per_episode=2000,
            render=not headless,
            render_sleep=0.02,
            verbose=verbose,
            load_saved_model=load_saved_model,
        )
    if selected_algorithm == "pg":    
        run_PG(
            num_episodes=num_episodes,
            env=env,
            max_steps_per_episode=2000,
            render=not headless,
            render_sleep=0.02,
            verbose=verbose,
            load_saved_model=load_saved_model,
        )
    
    if selected_algorithm == "a2c":    
        run_A2C(
            num_episodes=num_episodes,
            env=env,
            max_steps_per_episode=2000,
            render=not headless,
            render_sleep=0.02,
            verbose=verbose,
            load_saved_model=load_saved_model,
        )