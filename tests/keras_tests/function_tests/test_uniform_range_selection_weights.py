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
import numpy as np
import unittest

from keras import Input, Model
from keras.layers import Conv2D, Conv2DTranspose

import model_compression_toolkit as mct
from model_compression_toolkit import QuantizationConfig, QuantizationErrorMethod
from model_compression_toolkit.common.bias_correction.compute_bias_correction_of_graph import \
    compute_bias_correction_of_graph
from model_compression_toolkit.common.constants import RANGE_MIN, RANGE_MAX
from model_compression_toolkit.common.mixed_precision.bit_width_setter import set_bit_widths
from model_compression_toolkit.common.post_training_quantization import _quantize_fixed_bit_widths_graph
from model_compression_toolkit.common.quantization.quantization_analyzer import analyzer_graph
from model_compression_toolkit.common.quantization.quantization_params_generation.qparams_computation import \
    calculate_quantization_params
from model_compression_toolkit.common.quantization.set_node_quantization_config import \
    set_quantization_configuration_to_graph
from model_compression_toolkit.common.model_collector import ModelCollector
from model_compression_toolkit.tpc_models.keras_tp_models.keras_default import generate_keras_default_tpc
from model_compression_toolkit.keras.default_framework_info import DEFAULT_KERAS_INFO
from model_compression_toolkit.keras.keras_implementation import KerasImplementation
from tests.common_tests.helpers.generate_test_tp_model import generate_test_tp_model


def get_random_weights(kernel, in_channels, out_channels):
    return np.random.normal(size=[kernel, kernel, in_channels, out_channels])


def create_network():
    num_conv_channels = 4
    kernel = 3
    conv_w1 = get_random_weights(kernel, num_conv_channels, num_conv_channels)
    conv_w2 = get_random_weights(kernel, num_conv_channels, num_conv_channels)

    inputs = Input(shape=(16, 16, num_conv_channels))
    x = Conv2D(num_conv_channels, kernel, use_bias=False)(inputs)
    outputs = Conv2DTranspose(num_conv_channels, kernel, use_bias=False)(x)
    model = Model(inputs=inputs, outputs=outputs)

    model.layers[1].set_weights([conv_w1])
    model.layers[2].set_weights([conv_w2])
    return model


class TestUniformRangeSelectionWeights(unittest.TestCase):

    def test_per_channel_weights_uniform_range_selection_no_clipping(self):
        self.run_test_for_threshold_method(QuantizationErrorMethod.NOCLIPPING)

    def test_weights_uniform_range_selection_no_clipping(self):
        self.run_test_for_threshold_method(QuantizationErrorMethod.NOCLIPPING, per_channel=False)

    def test_per_channel_weights_uniform_range_selection_mse(self):
        self.run_test_for_threshold_method(QuantizationErrorMethod.MSE)

    def test_weights_uniform_range_selection_mse(self):
        self.run_test_for_threshold_method(QuantizationErrorMethod.MSE, per_channel=False)

    def test_per_channel_weights_uniform_range_selection_mae(self):
        self.run_test_for_threshold_method(QuantizationErrorMethod.MAE)

    def test_weights_uniform_range_selection_mae(self):
        self.run_test_for_threshold_method(QuantizationErrorMethod.MAE, per_channel=False)

    def test_per_channel_weights_uniform_range_selection_lp(self):
        self.run_test_for_threshold_method(QuantizationErrorMethod.LP)

    def test_weights_uniform_range_selection_lp(self):
        self.run_test_for_threshold_method(QuantizationErrorMethod.LP, per_channel=False)

    def test_per_channel_weights_uniform_range_selection_kl(self):
        self.run_test_for_threshold_method(QuantizationErrorMethod.KL)

    def test_weights_uniform_range_selection_kl(self):
        self.run_test_for_threshold_method(QuantizationErrorMethod.KL, per_channel=False)

    def run_test_for_threshold_method(self, threshold_method, per_channel=True):
        qc = QuantizationConfig(weights_error_method=threshold_method,
                                weights_per_channel_threshold=per_channel)

        tp = generate_test_tp_model({
            'weights_quantization_method': mct.target_platform.QuantizationMethod.UNIFORM})
        tpc = generate_keras_default_tpc(name="uniform_range_selection_test", tp_model=tp)

        fw_info = DEFAULT_KERAS_INFO
        in_model = create_network()
        keras_impl = KerasImplementation()
        graph = keras_impl.model_reader(in_model, None)  # model reading
        graph.set_fw_hw_model(tpc)
        graph.set_fw_info(fw_info)
        graph = set_quantization_configuration_to_graph(graph=graph,
                                                        quant_config=qc)
        for node in graph.nodes:
            node.prior_info = keras_impl.get_node_prior_info(node=node,
                                                             fw_info=fw_info,
                                                             graph=graph)
        analyzer_graph(keras_impl.attach_sc_to_node,
                       graph,
                       fw_info)

        mi = ModelCollector(graph,
                            fw_info=DEFAULT_KERAS_INFO,
                            fw_impl=keras_impl)

        for i in range(10):
            mi.infer([np.random.randn(1, 16, 16, 4)])

        calculate_quantization_params(graph,
                                      fw_info,
                                      fw_impl=keras_impl)

        tg = compute_bias_correction_of_graph(graph,
                                              fw_info,
                                              keras_impl)
        tg = set_bit_widths(qc,
                            tg,
                            fw_info,
                            None)

        quantized_model, user_info = _quantize_fixed_bit_widths_graph(False,
                                                                      fw_info,
                                                                      None,
                                                                      lambda: [np.random.randn(1, 16, 16, 4)],
                                                                      None,
                                                                      tg,
                                                                      keras_impl)

        nodes_list = list(graph.nodes)
        conv1_min = nodes_list[0].candidates_quantization_cfg[0].weights_quantization_cfg.weights_quantization_params[RANGE_MIN].flatten()
        conv2_min = nodes_list[1].candidates_quantization_cfg[0].weights_quantization_cfg.weights_quantization_params[RANGE_MIN].flatten()
        conv1_max = nodes_list[0].candidates_quantization_cfg[0].weights_quantization_cfg.weights_quantization_params[RANGE_MAX].flatten()
        conv2_max = nodes_list[1].candidates_quantization_cfg[0].weights_quantization_cfg.weights_quantization_params[RANGE_MAX].flatten()

        for range_min, range_max in list(zip(conv1_min, conv1_max)):
            self.assertTrue(range_min <= 0 <= range_max,
                            msg=f"First conv layer quantization range ({range_min}, {range_max}) does not include 0")
        for range_min, range_max in list(zip(conv2_min, conv2_max)):
            self.assertTrue(range_min <= 0 <= range_max,
                            msg=f"First conv layer quantization range ({range_min}, {range_max}) does not include 0")


if __name__ == '__main__':
    unittest.main()
