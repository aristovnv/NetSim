import numpy as np
import gymnasium as gym
from gymnasium import spaces
import constants as c
from .vars import Port, Cargo, Vessel
from typing import Optional
from gymnasium.utils.env_checker import check_env

class NetSim(gym.Env):
    def __init__(self, vessel: Vessel, ports: list[Port], cargos: list[Cargo]):
        super(NetSim, self).__init__()
        self.vessel = vessel
        self.ports = ports
        self.cargos = cargos
        self.num_ports = len(ports)
        self.num_cargos = len(cargos)
        self.action_space: spaces.Discrete = spaces.Discrete(self.num_cargos)
        
    def _get_obs(self):
        return None
    
    def _get_info(self):
        return {'action_mask': np.ones(self.action_space.n, dtype=np.uint8)}
    
    def _action_mask(self):
        return np.ones(self.action_space.n, dtype=np.uint8)
    
    def reset(self, seed: Optional[int] = None, options: Optional[dict] = None):
        super().reset(seed=seed)
        observation = self._get_obs()
        info = self._get_info()
        return observation, info
    
    def step(self, action):
        terminated = False
        truncated = False
        mask = self._action_mask()
        observation = self._get_obs()
        info = self._get_info()
        return observation, reward, terminated, truncated, info
    
    def render(self, mode='human'):
        if mode == 'human':
            print("Rendering environment...")
        else:
            raise NotImplementedError(f"Render mode {mode} not implemented.")
        

if __name__ == "__main__":
    
    env = NetSim(c.PORTS, )
    check_env(env)
    obs, info = env.reset()
    done = False
    episode_reward = 0
    while not done:
        mask = info.get('action_mask', np.ones(env.action_space.n, dtype=np.uint8))
        action = np.random.choice(env.action_space.n, p=mask/np.sum(mask))
        obs, reward, terminated, truncated, info = env.step(action)
        episode_reward += reward
        env.render()
        done = terminated or truncated
    print(f"Episode return: {episode_reward}")
