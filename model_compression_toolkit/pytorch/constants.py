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


# # Layer type constants:
PLACEHOLDER = 'placeholder'
OUTPUT = 'output'

# # Module operation type
CALL_FUNCTION = 'call_function'
CALL_METHOD = 'call_method'

# # Layers attributes constants:
LAYER_NAME = 'name'
USE_BIAS = 'bias'
PADDING = 'padding'
TENSOR_META = 'tensor_meta'
TYPE = 'type'
PAD = 'pad'
VALUE = 'value'
FUNCTIONAL_OP = 'functional_op'
OP_CALL_ARGS = 'op_call_args'
OP_CALL_KWARGS = 'op_call_kwargs'
INPUTS_AS_LIST = 'inputs_as_list'

# # Layers variables names:
KERNEL = 'weight'
BIAS = 'bias'
GAMMA = 'weight'
BETA = 'bias'
MOVING_MEAN = 'running_mean'
MOVING_VARIANCE = 'running_var'
EPSILON = 'eps'

# torch devices
CUDA = 'cuda'
CPU = 'cpu'
