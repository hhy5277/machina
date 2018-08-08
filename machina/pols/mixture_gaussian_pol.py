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

import numpy as np
import torch
from torch.distributions import Categorical
from machina.pols import BasePol
from machina.pds.mixture_gaussian_pd import MixtureGaussianPd
from machina.utils import get_device

class MixtureGaussianPol(BasePol):
    def __init__(self, ob_space, ac_space, net, normalize_ac=True):
        BasePol.__init__(self, ob_space, ac_space, normalize_ac)
        self.net = net
        self.pd = MixtureGaussianPd(ob_space, ac_space)
        self.to(get_device())

    def forward(self, obs):
        pi, mean, log_std = self.net(obs)
        log_std = log_std.expand_as(mean)
        ac = self.pd.sample(dict(pi=pi, mean=mean, log_std=log_std))
        ac_real = self.convert_ac_for_real(ac.detach().numpy())
        return ac_real, ac, dict(pi=pi, mean=mean, log_std=log_std)

    def deterministic_ac_real(self, obs):
        """
        action for deployment
        """
        pi, mean, _ = self.net(obs)
        _, i = torch.max(pi, 1)
        onehot = torch.zeros_like(mean)
        onehot = onehot.scatter_(-1, i.unsqueeze(-1), 1)
        mean_real = self.convert_ac_for_real(torch.sum(mean * onehot.unsqueeze(-1), 1).detach().numpy())
        return mean_real
