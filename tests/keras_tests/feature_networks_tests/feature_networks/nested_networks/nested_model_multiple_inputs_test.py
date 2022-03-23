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

import model_compression_toolkit as mct
import tensorflow as tf

if tf.__version__ < "2.6":
    from tensorflow.python.keras.engine.functional import Functional
    from tensorflow.python.keras.engine.sequential import Sequential
else:
    from keras.models import Functional, Sequential

from tests.keras_tests.feature_networks_tests.base_keras_feature_test import BaseKerasFeatureNetworkTest

import numpy as np
from tests.common_tests.helpers.tensors_compare import cosine_similarity

keras = tf.keras
layers = keras.layers


class NestedModelMultipleInputsTest(BaseKerasFeatureNetworkTest):
    def __init__(self, unit_test):
        super().__init__(unit_test)

    def get_quantization_config(self):
        return mct.QuantizationConfig(mct.QuantizationErrorMethod.MSE, mct.QuantizationErrorMethod.MSE,16, 16,
                                      True, True, True)

    def get_input_shapes(self):
        return [[self.val_batch_size, 236, 236, 3]]

    def inner_functional_model(self, input_shape):
        inputs = layers.Input(shape=input_shape[1:])
        inputs2 = layers.Input(shape=input_shape[1:])
        x = layers.Conv2D(3, 4, name='conv3')(inputs) #fq
        y = layers.Conv2D(3, 4, name='conv4')(inputs2) #fq
        x = layers.BatchNormalization()(x)
        x = layers.Add()([x, y])
        outputs = layers.Activation('swish')(x) #fq
        return keras.Model(inputs=[inputs, inputs2], outputs=outputs)

    def create_networks(self):
        inputs = layers.Input(shape=self.get_input_shapes()[0][1:])
        x = layers.Conv2D(3, 4, name='conv1')(inputs)
        y = layers.Conv2D(3, 4, name='conv2')(inputs) #fq
        x = layers.BatchNormalization()(x)
        x = layers.Activation('relu')(x) #fq
        x = self.inner_functional_model(x.shape)([x, y])
        model = keras.Model(inputs=inputs, outputs=x)
        return model

    def compare(self, quantized_model, float_model, input_x=None, quantization_info=None):
        for l in quantized_model.layers:
            if hasattr(l, 'layer'):
                self.unit_test.assertFalse(isinstance(l.layer, Functional) or isinstance(l.layer, Sequential))
            else:
                self.unit_test.assertFalse(isinstance(l, Functional) or isinstance(l, Sequential))
        num_layers = 8
        num_fq_layers = 6
        self.unit_test.assertTrue(len(quantized_model.layers) == (num_layers+num_fq_layers))
        y = float_model.predict(input_x)
        y_hat = quantized_model.predict(input_x)
        cs = cosine_similarity(y, y_hat)
        self.unit_test.assertTrue(np.isclose(cs, 1), msg=f'fail cosine similarity check:{cs}')
