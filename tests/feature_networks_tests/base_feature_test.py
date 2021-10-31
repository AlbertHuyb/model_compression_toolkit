# Copyright 2021 Sony Semiconductors Israel, Inc. All rights reserved.
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

import model_compression_toolkit as mct
from model_compression_toolkit.common.quantization.quantization_config import DEFAULTCONFIG
from model_compression_toolkit.keras.default_framework_info import DEFAULT_KERAS_INFO


class BaseFeatureNetworkTest:
    def __init__(self, unit_test, num_calibration_iter=1, val_batch_size=50):
        self.unit_test = unit_test
        self.val_batch_size = val_batch_size
        self.num_calibration_iter = num_calibration_iter

    def get_quantization_config(self):
        return DEFAULTCONFIG

    def get_kd_config(self):
        return None

    def get_network_editor(self):
        return []

    def create_inputs_shape(self):
        raise NotImplementedError(f'{self.__class__} did not implement create_feature_network')

    def create_feature_network(self, input_shape):
        raise NotImplementedError(f'{self.__class__} did not implement create_feature_network')

    def compare(self, ptq_model, model_float, input_x=None):
        raise NotImplementedError(f'{self.__class__} did not implement compare')

    @staticmethod
    def generate_inputs(input_shapes):
        return [np.random.randn(*in_shape) for in_shape in input_shapes]

    def run_test(self):
        input_shapes = self.create_inputs_shape()
        x = self.generate_inputs(input_shapes)

        def representative_data_gen():
            return x

        model_float = self.create_feature_network(input_shapes)
        ptq_model, quantization_info = mct.keras_post_training_quantization(model_float, representative_data_gen,
                                                                             n_iter=self.num_calibration_iter,
                                                                             quant_config=self.get_quantization_config(),
                                                                             fw_info=DEFAULT_KERAS_INFO,
                                                                             network_editor=self.get_network_editor(),
                                                                             knowledge_distillation_config=self.get_kd_config())
        self.compare(ptq_model, model_float, input_x=x, quantization_info=quantization_info)
