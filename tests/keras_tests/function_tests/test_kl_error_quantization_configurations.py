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
from model_compression_toolkit.core.tpc_models.keras_tp_models.keras_default import generate_keras_default_tpc
from model_compression_toolkit.core.keras.default_framework_info import DEFAULT_KERAS_INFO
import unittest
import numpy as np
import model_compression_toolkit as mct
import tensorflow as tf
from tensorflow.keras import layers
import itertools
from tests.common_tests.helpers.generate_test_tp_model import generate_test_tp_model


def model_gen():
    inputs = layers.Input(shape=[4, 4, 3])
    x = layers.Conv2D(2, 2, padding='same')(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.Activation('relu')(x)
    return tf.keras.models.Model(inputs=inputs, outputs=x)


class TestQuantizationConfigurations(unittest.TestCase):
    def test_run_quantization_config_mbv1(self):
        x = np.random.randn(1, 4, 4, 3)

        def representative_data_gen():
            return [x]

        quantizer_methods = [mct.target_platform.QuantizationMethod.POWER_OF_TWO,
                             mct.target_platform.QuantizationMethod.SYMMETRIC,
                             mct.target_platform.QuantizationMethod.UNIFORM]

        quantization_error_methods = [mct.QuantizationErrorMethod.KL]
        relu_bound_to_power_of_2 = [True, False]
        weights_per_channel = [True, False]

        weights_config_list = [quantizer_methods, quantization_error_methods, weights_per_channel]
        weights_test_combinations = list(itertools.product(*weights_config_list))

        activation_config_list = [quantizer_methods, quantization_error_methods, relu_bound_to_power_of_2]
        activation_test_combinations = list(itertools.product(*activation_config_list))

        model = model_gen()
        for quantize_method, error_method, per_channel in weights_test_combinations:

            tp_model = generate_test_tp_model({
                'weights_quantization_method': quantize_method,
                'weights_n_bits': 8,
                'activation_n_bits': 8})
            tpc = generate_keras_default_tpc(name="kl_quant_config_weights_test", tp_model=tp_model)

            qc = mct.QuantizationConfig(activation_error_method=mct.QuantizationErrorMethod.NOCLIPPING,
                                        weights_error_method=error_method,
                                        relu_bound_to_power_of_2=False,
                                        weights_bias_correction=True,
                                        weights_per_channel_threshold=per_channel,
                                        input_scaling=False)

            q_model, quantization_info = mct.keras_post_training_quantization(model,
                                                                              representative_data_gen,
                                                                              n_iter=1,
                                                                              quant_config=qc,
                                                                              fw_info=DEFAULT_KERAS_INFO,
                                                                              target_platform_capabilities=tpc)

        model = model_gen()
        for quantize_method, error_method, relu_bound_to_power_of_2 in activation_test_combinations:
            tp = generate_test_tp_model({
                'activation_quantization_method': quantize_method,
                'weights_n_bits': 8,
                'activation_n_bits': 8,
                'enable_weights_quantization': False})
            tpc = generate_keras_default_tpc(name="kl_quant_config_activation_test", tp_model=tp)

            qc = mct.QuantizationConfig(activation_error_method=error_method,
                                        relu_bound_to_power_of_2=relu_bound_to_power_of_2,
                                        shift_negative_activation_correction=False)

            q_model, quantization_info = mct.keras_post_training_quantization(model,
                                                                              representative_data_gen,
                                                                              n_iter=1,
                                                                              quant_config=qc,
                                                                              fw_info=DEFAULT_KERAS_INFO,
                                                                              target_platform_capabilities=tpc)


if __name__ == '__main__':
    unittest.main()
