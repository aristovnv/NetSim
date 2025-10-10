import gymnasium as gym
from gymnasium import spaces
import numpy as np
import ray
from ray import tune
from ray.rllib.algorithms.ppo import PPOConfig


# ---------- SIMPLE ENVIRONMENT ----------
class MaritimeEnv(gym.Env):
    def __init__(self, config=None):
        self.max_steps = config.get("max_steps", 50)
        self.num_nodes = 5
        self.current_step = 0
        self.action_space = spaces.Discrete(2)
        self.observation_space = spaces.Box(low=0, high=1, shape=(self.num_nodes,), dtype=np.float32)
        self.state = None

    def reset(self, *, seed=None, options=None):
        self.current_step = 0
        self.state = np.random.rand(self.num_nodes).astype(np.float32)
        return self.state, {}

    def step(self, action):
        reward = np.random.randn() * 0.1
        self.state = np.random.rand(self.num_nodes).astype(np.float32)
        self.current_step += 1
        terminated = self.current_step >= self.max_steps
        return self.state, reward, terminated, False, {}

    def render(self):
        print(f"Step {self.current_step}, state={self.state}")


# ---------- RAY RLlib TRAINING ----------
if __name__ == "__main__":
    ray.init(ignore_reinit_error=True)

    config = (
        PPOConfig()
        .environment(env=MaritimeEnv, env_config={"max_steps": 50})
        .rollouts(num_rollout_workers=2)
        .training(model={"fcnet_hiddens": [64, 64]}, train_batch_size=4000)
    )

    algo = config.build()

    for i in range(5):
        result = algo.train()
        print(f"Iteration {i}: reward_mean={result['episode_reward_mean']:.3f}")

    # Save checkpoint
    checkpoint = algo.save("rllib_checkpoints")
    print("Checkpoint saved:", checkpoint)

    # ---------- INFERENCE ----------
    env = MaritimeEnv({"max_steps": 10})
    obs, _ = env.reset()
    terminated = False
    while not terminated:
        action = algo.compute_single_action(obs)
        obs, reward, terminated, truncated, _ = env.step(action)
        env.render()
