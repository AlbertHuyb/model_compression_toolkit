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

import tensorflow as tf

from tests.keras_tests.fw_hw_model_keras import get_quantization_disabled_keras_hw_model

if tf.__version__ < "2.6":
    from tensorflow.python.keras.engine.functional import Functional
    from tensorflow.python.keras.engine.sequential import Sequential
else:
    from keras.models import Functional, Sequential
import model_compression_toolkit as mct
import tensorflow as tf
from tests.keras_tests.feature_networks_tests.base_keras_feature_test import BaseKerasFeatureNetworkTest


import numpy as np
from tests.common_tests.helpers.tensors_compare import cosine_similarity

keras = tf.keras
layers = keras.layers


class NestedTest(BaseKerasFeatureNetworkTest):
    def __init__(self, unit_test, is_inner_functional=True):
        self.is_inner_functional = is_inner_functional
        super().__init__(unit_test,
                         input_shape=(16,16,3))

    def get_fw_hw_model(self):
        return get_quantization_disabled_keras_hw_model("nested_test")

    # Dummy model to test reader's recursively model parsing
    def dummy_model(self, input_shape):
        inputs = layers.Input(shape=input_shape[1:])
        x = layers.Conv2D(3, 4)(inputs)
        x = layers.BatchNormalization()(x)
        outputs = layers.Activation('swish')(x)
        return keras.Model(inputs=inputs, outputs=outputs)

    def inner_functional_model(self, input_shape):
        inputs = layers.Input(shape=input_shape[1:])
        x = layers.Conv2D(3, 4)(inputs)
        x = self.dummy_model(x.shape)(x)
        x = layers.BatchNormalization()(x)
        outputs = layers.Activation('swish')(x)
        return keras.Model(inputs=inputs, outputs=outputs)

    def inner_sequential_model(self, input_shape):
        model = keras.models.Sequential()
        model.add(layers.Conv2D(3, 4, input_shape=input_shape[1:]))
        model.add(layers.BatchNormalization())
        model.add(layers.Activation('swish'))
        return model

    def create_networks(self):
        inputs = layers.Input(shape=self.get_input_shapes()[0][1:])
        x = layers.Conv2D(3, 4)(inputs)
        x = layers.BatchNormalization()(x)
        x = layers.Activation('relu')(x)
        if self.is_inner_functional:
            x = self.inner_functional_model(x.shape)(x)
        else:
            x = self.inner_sequential_model(x.shape)(x)
        model = keras.Model(inputs=inputs, outputs=x)
        return model

    def compare(self, quantized_model, float_model, input_x=None, quantization_info=None):
        for l in quantized_model.layers:
            if hasattr(l, 'layer'):
                self.unit_test.assertFalse(isinstance(l.layer, Functional) or isinstance(l.layer, Sequential))
            else:
                self.unit_test.assertFalse(isinstance(l, Functional) or isinstance(l, Sequential))
        if self.is_inner_functional:
            num_layers = 8
        else:
            num_layers = 5
        self.unit_test.assertTrue(len(quantized_model.layers) == num_layers)
        y = float_model.predict(input_x)
        y_hat = quantized_model.predict(input_x)
        cs = cosine_similarity(y, y_hat)
        self.unit_test.assertTrue(np.isclose(cs, 1), msg=f'fail cosine similarity check:{cs}')
