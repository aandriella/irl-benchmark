import gym
import numpy as np
import pickle

from irl.algorithms.appr.appr_irl import ApprIRL
from irl.feature.feature_wrapper import FrozenFeatureWrapper
from irl.collect import collect_trajs
from irl.reward.reward_function import FeatureBasedRewardFunction
from irl.reward.reward_wrapper import RewardWrapper
from rl.algorithms import TabularQ

# #
# Define important script constants here:
store_to = 'data/frozen/expert/'
no_episodes = 1000
max_steps_per_episode = 100
#
# #

env = gym.make('FrozenLake-v0')
env = FrozenFeatureWrapper(env)

# expert_agent = TabularQ(env)
# print('Training expert agent...')
# expert_agent.train(15)
# print('Done training expert')
# expert_trajs = collect_trajs(env, expert_agent, no_episodes,
#                              max_steps_per_episode, store_to)

with open(store_to + 'trajs.pkl', 'rb') as f:
    expert_trajs = pickle.load(f)

reward_function = FeatureBasedRewardFunction(env, np.random.normal(size=16))
env = RewardWrapper(env, reward_function)

appr_irl = ApprIRL(env, expert_trajs, proj=True)

appr_irl.train(600, verbose=True)
