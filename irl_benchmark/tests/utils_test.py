import gym
from gym.envs.toy_text.discrete import DiscreteEnv
from gym.wrappers.time_limit import TimeLimit
import numpy as np

from irl_benchmark.irl.feature.feature_wrapper import FrozenLakeFeatureWrapper
from irl_benchmark.irl.feature import feature_wrapper
from irl_benchmark.irl.reward.reward_function import TabularRewardFunction, FeatureBasedRewardFunction
from irl_benchmark.irl.reward.reward_wrapper import RewardWrapper
from irl_benchmark.utils.utils import (is_unwrappable_to, unwrap_env, to_one_hot,
                                       get_transition_matrix, get_reward_matrix)



def test_unwrap():
    env = gym.make('FrozenLake-v0')
    assert env.env is unwrap_env(env, DiscreteEnv)

    # No unwrapping needed:
    assert env is unwrap_env(env, gym.Env)

    # Unwrap all the way:
    assert env.env is unwrap_env(env)

    env = FrozenLakeFeatureWrapper(env)
    assert env.env.env is unwrap_env(env, DiscreteEnv)

    # No unwrapping needed:
    assert env is unwrap_env(env, FrozenLakeFeatureWrapper)

    # Unwrap all the way:
    assert env.env.env is unwrap_env(env)


def test_get_transition_matrix():
    env = gym.make('FrozenLake-v0')
    table = get_transition_matrix(env)

    # Assert probability sums to 1.0 (or zero if impossible to escape)
    for s in range(table.shape[0]):
        for a in range(table.shape[1]):
            assert table[s, a].sum() == 1.0 or table[s, a].sum() == 0.0

    env = FrozenLakeFeatureWrapper(env)
    table = get_transition_matrix(env)

    # Assert probability sums to 1.0 (or zero if impossible to escape)
    for s in range(table.shape[0]):
        for a in range(table.shape[1]):
            assert table[s, a].sum() == 1.0 or table[s, a].sum() == 0.0


def test_get_reward_matrix():
    env = gym.make('FrozenLake8x8-v0')
    transition_matrix = get_transition_matrix(env, with_absorbing_state=True)
    reward_matrix = get_reward_matrix(env, with_absorbing_state=True)
    true_rews = np.zeros(64 + 1)
    # [-2] since [-1] is the added absorbing state
    true_rews[-2] = 1.0
    for s in range(64 + 1):
        for a in range(4):
            assert np.isclose(reward_matrix[s, a], transition_matrix[s, a, :].dot(true_rews))

def test_get_reward_matrix_wrapped_tabular():
    env = gym.make('FrozenLake8x8-v0')
    true_rews = np.random.randn(65)
    true_rews[-1] = 0
    reward_function = TabularRewardFunction(env, true_rews[:-1])
    env = RewardWrapper(env, reward_function=reward_function)
    transition_matrix = get_transition_matrix(env, with_absorbing_state=True)
    reward_matrix = get_reward_matrix(env, with_absorbing_state=True)
    for s in range(64 + 1):
        for a in range(4):
            assert np.isclose(reward_matrix[s, a], transition_matrix[s, a, :].dot(true_rews))

def test_get_reward_matrix_wrapped_feature():
    env = feature_wrapper.make('FrozenLake8x8-v0')
    true_rews = np.random.randn(65)
    true_rews[-1] = 0
    reward_function = FeatureBasedRewardFunction(env, true_rews[:-1])
    env = RewardWrapper(env, reward_function=reward_function)
    transition_matrix = get_transition_matrix(env, with_absorbing_state=True)
    reward_matrix = get_reward_matrix(env, with_absorbing_state=True)
    for s in range(64 + 1):
        for a in range(4):
            assert np.isclose(reward_matrix[s, a], transition_matrix[s, a, :].dot(true_rews))


def test_is_unwrappable_to():
    assert is_unwrappable_to(gym.make('FrozenLake-v0'), TimeLimit)
    assert is_unwrappable_to(gym.make('FrozenLake-v0'), DiscreteEnv)
    assert is_unwrappable_to(feature_wrapper.make('FrozenLake-v0'), FrozenLakeFeatureWrapper)
    assert is_unwrappable_to(feature_wrapper.make('FrozenLake8x8-v0'), FrozenLakeFeatureWrapper)

