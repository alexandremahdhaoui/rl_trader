import tensorflow as tf
import numpy as np

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--gamma', type=float, default=0.99)
parser.add_argument('--update_interval', type=int, default=5)
parser.add_argument('--actor_lr', type=float, default=5e-4)
parser.add_argument('--critic_lr', type=float, default=1e-3)
args = parser.parse_args()


class Actor:
    def __init__(self, state_dim, action_dim, action_bound, std_bound):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.action_bound = action_bound
        self.std_bound = std_bound
        self.model = self.create_model()
        self.opt = tf.keras.optimizers.Adam(args.actor_lr)

    def create_model(self):
        state_input = tf.keras.layers.Input((self.state_dim,))
        dense_1 = tf.keras.layers.Dense(32, activation='relu')(state_input)
        dense_2 = tf.keras.layers.Dense(32, activation='relu')(dense_1)
        out_mu = tf.keras.layers.Dense(self.action_dim, activation='tanh')(dense_2)
        mean_output = tf.keras.layers.Lambda(lambda x: x * self.action_bound)(out_mu)
        std_output = tf.keras.layers.Dense(self.action_dim, activation='softplus')(dense_2)
        return tf.keras.models.Model(state_input, [mean_output, std_output])

    def get_action(self, state):
        state = np.reshape(state, [1, self.state_dim])
        mean, std = self.model.predict(state)
        mean, std = mean[0], std[0]
        return np.random.normal(mean, std, size=self.action_dim)

    def log_pdf(self, mean, std, action):
        std = tf.clip_by_value(std, self.std_bound[0], self.std_bound[1])
        variance = std ** 2
        log_policy_pdf = -0.5 * (action - mean) ** 2 / variance - 0.5 * tf.math.log(variance * 2 * np.pi)
        return tf.reduce_sum(log_policy_pdf, 1, keepdims=True)

    def compute_loss(self, mean, std, actions, advantages):
        log_policy_pdf = self.log_pdf(mean, std, actions)
        loss_policy = log_policy_pdf * advantages
        return tf.reduce_sum(-loss_policy)

    def train(self, states, actions, advantages):
        with tf.GradientTape() as tape:
            mean, std = self.model(states, training=True)
            loss = self.compute_loss(mean, std, actions, advantages)
        grads = tape.gradient(loss, self.model.trainable_variables)
        self.opt.apply_gradients(zip(grads, self.model.trainable_variables))
        return loss


class Critic:
    def __init__(self, state_dim):
        self.state_dim = state_dim
        self.model = self.create_model()
        self.opt = tf.keras.optimizers.Adam(args.critic_lr)

    def create_model(self):
        return tf.keras.Sequential([
            tf.keras.layers.Input((self.state_dim,)),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(16, activation='relu'),
            tf.keras.layers.Dense(1, activation='linear')
        ])

    def compute_loss(self, v_pred, td_targets):
        mse = tf.keras.losses.MeanSquaredError()
        return mse(td_targets, v_pred)

    def train(self, states, td_targets):
        with tf.GradientTape() as tape:
            v_pred = self.model(states, training=True)
            assert v_pred.shape == td_targets.shape
            loss = self.compute_loss(v_pred, tf.stop_gradient(td_targets))
        grads = tape.gradient(loss, self.model.trainable_variables)
        self.opt.apply_gradients(zip(grads, self.model.trainable_variables))
        return loss


class Agent:
    def __init__(self, env):
        self.env = env
        self.state_dim = self.env.observation_space.shape[0]
        self.action_dim = self.env.action_space.shape[0]
        self.action_bound = self.env.action_space.high[0]
        self.std_bound = [1e-2, 1.0]

        self.actor = Actor(self.state_dim, self.action_dim,
                           self.action_bound, self.std_bound)
        self.critic = Critic(self.state_dim)

    def td_target(self, reward, next_state, done) -> np.ndarray:
        if done:
            return reward
        v_value = self.critic.model.predict(
            np.reshape(next_state, [1, self.state_dim]))
        return np.reshape(reward + args.gamma * v_value[0], [1, 1])

    def advantage(self, td_targets, baselines):
        return td_targets - baselines

    def list_to_batch(self, list_):
        batch = list_[0]
        for elem in list_[1:]:
            batch = np.append(batch, elem, axis=0)
        return batch

    def train(self, max_episodes=1000):
        for ep in range(max_episodes):
            state_batch = []
            action_batch = []
            td_target_batch = []
            advantage_batch = []
            episode_reward, done = 0, False

            state = self.env.reset()

            while not done:
                # self.env.render()
                action = self.actor.get_action(state)
                action = np.clip(action, -self.action_bound, self.action_bound)

                next_state, reward, done, _ = self.env.step(action)

                state = np.reshape(state, [1, self.state_dim])
                action = np.reshape(action, [1, self.action_dim])
                next_state = np.reshape(next_state, [1, self.state_dim])
                reward = np.reshape(reward, [1, 1])

                td_target = self.td_target((reward + 8) / 8, next_state, done)
                advantage = self.advantage(
                    td_target, self.critic.model.predict(state))

                state_batch.append(state)
                action_batch.append(action)
                td_target_batch.append(td_target)
                advantage_batch.append(advantage)

                if len(state_batch) >= args.update_interval or done:
                    states = self.list_to_batch(state_batch)
                    actions = self.list_to_batch(action_batch)
                    td_targets = self.list_to_batch(td_target_batch)
                    advantages = self.list_to_batch(advantage_batch)

                    actor_loss = self.actor.train(states, actions, advantages)
                    critic_loss = self.critic.train(states, td_targets)

                    state_batch = []
                    action_batch = []
                    td_target_batch = []
                    advantage_batch = []

                episode_reward += reward[0][0]
                state = next_state[0]

            print('EP{} EpisodeReward={}'.format(ep, episode_reward))


