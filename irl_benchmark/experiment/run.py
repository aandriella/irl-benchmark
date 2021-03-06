"""Module defining a run of an IRL algorithm experiment"""
from typing import Callable, Dict, List

import gym

from irl_benchmark.envs import make_wrapped_env, \
    ENV_IDS_ACTION_IN_DOMAIN, ENV_IDS_NEXT_STATE_IN_DOMAIN
from irl_benchmark.irl.algorithms.base_algorithm import BaseIRLAlgorithm
from irl_benchmark.irl.collect import load_stored_trajs
from irl_benchmark.irl.reward import truth
from irl_benchmark.metrics.base_metric import BaseMetric


class Run:
    """This class corresponds to a single run of an IRL algorithm experiment."""

    def __init__(self, env_id: str, expert_trajs_path: str,
                 irl_alg_factory: Callable[[gym.Env, List[Dict[str, list]]],
                                           BaseIRLAlgorithm],
                 metrics: List[BaseMetric], rl_config: dict, irl_config: dict,
                 run_config: dict):
        """

        Parameters
        ----------
        env_id: str
            The environment id of a gym environment.
        expert_trajs_path: str
            A path to the folder where expert trajectories are stored. The file with
            expert trajectories must be expert_trajs_path/trajs.data.
        irl_alg_factory: Callable[[gym.Env, List[Dict[str, list]]], BaseIRLAlgorithm]
            A factory function which takes a gym environment and expert trajetories and
            returns a subclass of BaseIRLAlgorithm.
        metrics: List[BaseMetric]
            The metrics to be evaluated after running the IRL algorithm.
        run_config: dict
            A dictionary containing the configuration of the run. Required fields are:
            'reward_function': subclass of BaseRewardFunction, e.g. FeatureBasedRewardFunction.
            'no_expert_trajs': int, number of expert trajectories to be used.
            'no_irl_iterations': int, number of iterations the IRL algorithm is run for.
            'no_rl_episodes_per_irl_iteration': int, how many episodes the RL agent
            is allowed to run each iteration.
            'no_irl_episodes_per_irl_iteration': int, how many episodes can be sampled
            for the IRL algorithm each iteration.
        """

        action_in_domain = env_id in ENV_IDS_ACTION_IN_DOMAIN
        next_state_in_domain = env_id in ENV_IDS_NEXT_STATE_IN_DOMAIN

        def reward_function_factory(env):
            return run_config['reward_function'](
                env,
                parameters='random',
                action_in_domain=action_in_domain,
                next_state_in_domain=next_state_in_domain)

        print('Making run environment.')
        self.env = make_wrapped_env(
            env_id,
            with_feature_wrapper=run_config['requires_features'],
            reward_function_factory=reward_function_factory,
            with_model_wrapper=run_config['requires_transitions'])

        # load expert trajs:
        print('Load expert demonstrations from ' + str(expert_trajs_path))
        self.expert_trajs = load_stored_trajs(expert_trajs_path)
        print('Loaded expert demonstrations.')
        # use only specified number of expert trajs
        assert len(self.expert_trajs) >= run_config['no_expert_trajs']
        self.expert_trajs = self.expert_trajs[:run_config['no_expert_trajs']]
        self.irl_alg_factory = irl_alg_factory
        # Metrics are only passed as classes and need to be instantiated
        instantiated_metrics = []
        # collect all information relevant for certain metric __init__s:
        metric_input = {
            'env':
            self.env,
            'expert_trajs':
            self.expert_trajs,
            'true_reward':
            truth.make_true_reward(env_id),
            'no_trajs_for_metrics':
            run_config['no_metric_episodes_per_irl_iteration']
        }
        # instantiate metrics:
        print('Instantiate metrics.')
        for metric in metrics:
            instantiated_metrics.append(metric(metric_input))
        self.metrics = instantiated_metrics

        self.rl_config = rl_config
        self.irl_config = irl_config

        self.run_config = run_config

    def start(self):
        """Start the run."""
        irl_alg = self.irl_alg_factory(self.env, self.expert_trajs,
                                       self.metrics, self.rl_config,
                                       self.irl_config)
        irl_alg.train(self.run_config['no_irl_iterations'],
                      self.run_config['no_rl_episodes_per_irl_iteration'],
                      self.run_config['no_irl_episodes_per_irl_iteration'])
