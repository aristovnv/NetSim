from env import NetSim, get_base_environment
import numpy as np
import os
from sb3_contrib import MaskablePPO
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.results_plotter import plot_results

def dummy_test():
    env: NetSim = get_base_environment()
    obs, info = env.reset()
    terminated, truncated = False, False
    episode_reward = 0
    while not terminated or truncated:
        mask = info['action_mask']
        action = np.random.choice(env.action_space.n, p = mask/ np.sum(mask))
        obs, reward, terminated, truncated, info = env.step(action)
        episode_reward += reward
        env.render()
    print(f"Episode return: {episode_reward}")

def ppo_train(model_name):
    log_dir = "tmp/"
    os.makedirs(log_dir, exist_ok=True)
    env = get_base_environment()
    env = Monitor(env, log_dir)
    model = MaskablePPO("MlpPolicy", env, tensorboard_log=log_dir)
    try:
        model.learn(total_timesteps=100000, tb_log_name= model_name)
        model.save(model_name)
    except KeyboardInterrupt:
        print("Interrupted. Saving model...")
        model.save(f"{model_name}_interrupt")

def ppo_test(model_name):
    env = get_base_environment()
    model = MaskablePPO.load(model_name, env=env)
    obs, info = env.reset()
    terminated, truncated = False, False
    episode_reward = 0
    while not terminated or truncated:
        action_mask = env.action_masks()
        action, _states = model.predict(obs, deterministic=True, action_masks=action_mask)
        obs, reward, terminated, truncated, info = env.step(action)
        episode_reward += reward
        env.render()
    print(f"Episode return: {episode_reward}")

if __name__ == "__main__":
    # ppo_train("ppo_test")
    ppo_test("ppo_test")