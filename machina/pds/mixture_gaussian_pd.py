# Copyright 2018 DeepX Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

import torch
from torch.distributions import OneHotCategorical
import numpy as np

from machina.pds.base import BasePd
from machina.pds.gaussian_pd import GaussianPd

class MixtureGaussianPd(BasePd):
    def __init__(self, ob_space, ac_space):
        BasePd.__init__(self, ob_space, ac_space)
        self.gaussian_pd = GaussianPd(ob_space, ac_space)

    def sample(self, params):
        pi, mean, log_std = params['pi'], params['mean'], params['log_std']
        pi_onehot = OneHotCategorical(pi).sample()
        ac = torch.sum((mean + torch.randn_like(mean) * torch.exp(log_std)) * pi_onehot.unsqueeze(-1), 1)
        return ac

    def llh(self, x, params):
        pis = params['pi']
        means = params['mean']
        log_stds = params['log_std']
        llh = 0
        for i in range(pis.shape[1]):
            pi = pis[:, i]
            mean = means[:, i, :]
            log_std = log_stds[:, i, :]
            llh = llh + pi * torch.exp(self.gaussian_pd.llh(x, dict(mean=mean, log_std=log_std)))
        return torch.log(llh)

    def kl_pq(self, p_params, q_params):
        p_pis = p_params['pi']
        p_means = p_params['mean']
        p_log_stds = p_params['log_std']
        q_pis = q_params['pi']
        q_means = q_params['mean']
        q_log_stds = q_params['log_std']
        kl = 0
        for i in range(p_pis.shape[1]):
            p_pi = p_pis[:, i]
            p_mean = p_means[:, i, :]
            p_log_std = p_log_stds[:, i, :]
            q_pi = q_pis[:, i]
            q_mean = q_means[:, i, :]
            q_log_std = q_log_stds[:, i, :]
            numerator = 0
            for ii in range(p_pis.shape[1]):
                numerator = numerator + p_pis[:, ii] * torch.exp(
                    -self.gaussian_pd.kl_pq(
                        dict(mean=p_mean, log_std=p_log_std),
                        dict(mean=p_means[:, ii, :], log_std=p_log_stds[:, ii, :])
                    )
                )
            denominator = 0
            for ii in range(p_pis.shape[1]):
                denominator = denominator + p_pis[:, ii] * torch.exp(
                    -self.gaussian_pd.kl_pq(
                        dict(mean=p_mean, log_std=p_log_std),
                        dict(mean=q_means[:, ii, :], log_std=q_log_stds[:, ii, :])
                    )
                )
            kl = kl + p_pi * torch.log(numerator / denominator)
        return kl

