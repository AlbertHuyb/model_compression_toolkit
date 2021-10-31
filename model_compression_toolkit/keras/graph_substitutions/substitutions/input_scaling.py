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


from tensorflow.keras.layers import InputLayer, Dense, DepthwiseConv2D, Conv2D, Conv2DTranspose, ZeroPadding2D
from typing import List

from model_compression_toolkit import common
from model_compression_toolkit.common.framework_info import FrameworkInfo
from model_compression_toolkit.common.graph.base_graph import Graph
from model_compression_toolkit.common.graph.graph_matchers import NodeOperationMatcher, EdgeMatcher, WalkMatcher
from model_compression_toolkit.common.graph.node import Node
from model_compression_toolkit.common.quantization.quantization_config import QuantizationConfig
from model_compression_toolkit.common.constants import THRESHOLD
from model_compression_toolkit.keras.constants import KERNEL

input_node = NodeOperationMatcher(InputLayer)
zeropad_node = NodeOperationMatcher(ZeroPadding2D)
op2d_node = NodeOperationMatcher(Dense) | \
            NodeOperationMatcher(Conv2D) | \
            NodeOperationMatcher(DepthwiseConv2D) | \
            NodeOperationMatcher(Conv2DTranspose)

INPUT_MATCHER = WalkMatcher([input_node, op2d_node])
INPUT_MATCHER_WITH_PAD = WalkMatcher([input_node, zeropad_node, op2d_node])


class BaseInputScaling(common.BaseSubstitution):
    """
    General scale activation threshold for input layers, if they are followed by linear nodes. We first
    scale their thresholds to a constrained threshold, and then fix it by scaling the linear op weights
    correspondingly.
    The matcher instance of type WalkMatcher may include intermediate nodes that don't affect scaling
    (such as ZeroPadding), but only the first and last nodes are used for scaling
    """

    def __init__(self,
                 quantization_config: QuantizationConfig,
                 fw_info: FrameworkInfo,
                 matcher_instance):
        """
        Matches: InputLayer -> (optional nodes) -> (Dense,Conv2D,DepthwiseConv2D,Conv2DTranspose)
        note: the optional nodes are nodes that don't affect the scaling (such as ZeroPadding)

        Create a substitution using different params which may affect the way this substitution is made.
        The substitution is looking for edges in the graph which are input layers connected to linear layers.
        Args:
            quantization_config: QuantizationConfig containing parameters of how the model should be quantized.
            fw_info: Information needed for quantization about the specific framework (e.g., kernel channels indices,
            groups of layers by how they should be quantized, etc.)
            matcher_instance: matcher instance of type WalkMatcher

        """

        self.fw_info = fw_info
        self.qc = quantization_config

        super().__init__(matcher_instance=matcher_instance)

    def substitute(self,
                   graph: Graph,
                   nodes_list: List[Node]) -> Graph:
        """
        Scale activation threshold for input layers, if they are followed by linear nodes. We first
        scale their thresholds to a constrained threshold, and then fix it by scaling the linear op weights
        correspondingly.

        Args:
            graph: Graph to apply the substitution on.
            edge_nodes: Edge (tuple of nodes) that matches the pattern the substitution can be applied on.

        Returns:
            Graph after applying the substitution.
        """

        input_layer = nodes_list[0]
        linear_layer = nodes_list[-1]

        threshold = input_layer.activation_quantization_cfg.activation_quantization_params.get(THRESHOLD)
        if threshold is None:
            return graph

        min_value, max_value = graph.get_out_stats_collector(input_layer).get_min_max_values()
        threshold_float = max(abs(min_value), max_value)

        if threshold > threshold_float:
            scale_factor = threshold_float / threshold
            graph.user_info.set_input_scale(1 / scale_factor)

            w1_fixed = linear_layer.get_weights_by_keys(KERNEL) * scale_factor
            linear_layer.set_weights_by_keys(KERNEL, w1_fixed)

            graph.scale_stats_collector(input_layer, 1/scale_factor)

            # After scaling weights may have different thresholds so it needs to be recalculated
            linear_layer.weights_quantization_cfg.calculate_and_set_weights_params(w1_fixed)

        return graph


class InputScaling(BaseInputScaling):
    """
    Substitution extends BaseInputScaling to the case of Input-->Linear
    """

    def __init__(self,
                 quant_config: QuantizationConfig,
                 fw_info: FrameworkInfo):
        """
        Initialize a ScaleEqualization object.
        Args:
            quant_config: QuantizationConfig containing parameters of how the model should be quantized.
            fw_info: Information needed for quantization about the specific framework (e.g., kernel channels indices,
            groups of layers by how they should be quantized, etc.)
        """

        super().__init__(quantization_config=quant_config, fw_info=fw_info, matcher_instance=INPUT_MATCHER)


class InputScalingWithPad(BaseInputScaling):
    """
    Substitution extends BaseInputScaling to the case of Input-->ZeroPadding-->Linear
    """

    def __init__(self,
                 quant_config: QuantizationConfig,
                 fw_info: FrameworkInfo):
        """
        Initialize a ScaleEqualization object.
        Args:
            quant_config: QuantizationConfig containing parameters of how the model should be quantized.
            fw_info: Information needed for quantization about the specific framework (e.g., kernel channels indices,
            groups of layers by how they should be quantized, etc.)
        """

        super().__init__(quantization_config=quant_config, fw_info=fw_info, matcher_instance=INPUT_MATCHER_WITH_PAD)
