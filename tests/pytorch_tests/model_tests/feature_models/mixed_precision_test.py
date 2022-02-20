# Copyright 2022 Sony Semiconductors Israel, Inc. All rights reserved.
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
import numpy as np
from torch.nn import Conv2d

from model_compression_toolkit import MixedPrecisionQuantizationConfig, KPI
from model_compression_toolkit.common.user_info import UserInformation
from tests.pytorch_tests.model_tests.base_pytorch_test import BasePytorchTest
import model_compression_toolkit as mct

"""
This test checks the Mixed Precision feature.
"""


class MixedPercisionBaseTest(BasePytorchTest):
    def __init__(self, unit_test):
        super().__init__(unit_test)

    def get_quantization_configs(self):
        qc = mct.QuantizationConfig(mct.QuantizationErrorMethod.MSE,
                                    mct.QuantizationErrorMethod.MSE,
                                    mct.QuantizationMethod.POWER_OF_TWO,
                                    mct.QuantizationMethod.POWER_OF_TWO,
                                    weights_bias_correction=True,
                                    weights_per_channel_threshold=True,
                                    activation_channel_equalization=False,
                                    relu_unbound_correction=False,
                                    input_scaling=False)

        return {"mixed_precision_model": MixedPrecisionQuantizationConfig(qc, weights_n_bits=[2, 8, 4], num_of_images=1)}

    def create_feature_network(self, input_shape):
        return MixedPrecisionNet(input_shape)

    def compare(self, quantized_model, float_model, input_x=None, quantization_info: UserInformation = None):
        # This is a base test, so it does not check a thing. Only actual tests of mixed precision
        # compare things to test.
        raise NotImplementedError

    def compare_results(self, quantization_info, quantized_models, float_model, expected_bitwidth_idx):
        # quantized with the highest precision since KPI==inf
        self.unit_test.assertTrue((quantization_info.mixed_precision_cfg ==
                                   [expected_bitwidth_idx, expected_bitwidth_idx]).all())
        # verify that quantization occurred
        quantized_model = quantized_models['mixed_precision_model']
        conv_layers = list(filter(lambda _layer: type(_layer) == Conv2d, list(quantized_model.children())))
        float_conv_layers = list(filter(lambda _layer: type(_layer) == Conv2d, list(float_model.children())))
        for idx, layer in enumerate(conv_layers):  # quantized per channel
            q_weights = layer.weight.detach().cpu().numpy()
            float_weights = float_conv_layers[idx].weight.detach().cpu().numpy()
            for i in range(3):
                self.unit_test.assertTrue(
                    np.unique(q_weights[i, :, :, :]).flatten().shape[0] <= 2 ** [8, 4, 2][expected_bitwidth_idx])
            # quantized_model and float_model are not equal
            self.unit_test.assertFalse((q_weights == float_weights).all())


class MixedPercisionSearch8Bit(MixedPercisionBaseTest):
    def __init__(self, unit_test):
        super().__init__(unit_test)

    def get_kpi(self):
        return KPI(np.inf)

    def compare(self, quantized_models, float_model, input_x=None, quantization_info=None):
        self.compare_results(quantization_info, quantized_models, float_model, 0)


class MixedPercisionSearch2Bit(MixedPercisionBaseTest):
    def __init__(self, unit_test):
        super().__init__(unit_test)

    def get_kpi(self):
        return KPI(96)

    def compare(self, quantized_models, float_model, input_x=None, quantization_info=None):
        self.compare_results(quantization_info, quantized_models, float_model, 2)


class MixedPrecisionNet(torch.nn.Module):
    def __init__(self, input_shape):
        super(MixedPrecisionNet, self).__init__()
        _, in_channels, _, _ = input_shape[0]
        self.conv1 = torch.nn.Conv2d(in_channels, 3, kernel_size=3)
        self.bn1 = torch.nn.BatchNorm2d(3)
        self.conv2 = torch.nn.Conv2d(3, 4, kernel_size=5)
        self.relu = torch.nn.ReLU()

    def forward(self, inp):
        x = self.conv1(inp)
        x = self.bn1(x)
        x = self.conv2(x)
        output = self.relu(x)
        return output
