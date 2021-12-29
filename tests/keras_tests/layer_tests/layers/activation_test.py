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


from keras.layers import Conv2D, Activation

from tests.keras_tests.layer_tests.base_keras_layer_test import BaseKerasLayerTest


class ActivationTest(BaseKerasLayerTest):
    def __init__(self, unit_test):
        super(ActivationTest, self).__init__(unit_test)

    def get_layers(self):
        return [Activation('softmax'),
                Activation('sigmoid'),
                Activation('linear'),
                Activation('tanh'),
                Activation('relu'),
                Activation('swish')]
