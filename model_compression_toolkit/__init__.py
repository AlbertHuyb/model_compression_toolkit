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


from model_compression_toolkit.common.gptq.gptq_config import GradientPTQConfig
from model_compression_toolkit.common.quantization import quantization_config
from model_compression_toolkit.common.mixed_precision import mixed_precision_quantization_config
from model_compression_toolkit.common.quantization.quantization_config import QuantizationConfig, \
    QuantizationErrorMethod, DEFAULTCONFIG
from model_compression_toolkit.common.quantization.core_config import CoreConfig
from model_compression_toolkit.common import target_platform
from model_compression_toolkit.tpc_models.get_target_platform_capabilities import get_target_platform_capabilities
from model_compression_toolkit.common.mixed_precision.kpi import KPI
from model_compression_toolkit.common.mixed_precision.mixed_precision_quantization_config import MixedPrecisionQuantizationConfig, MixedPrecisionQuantizationConfigV2
from model_compression_toolkit.common.logger import set_log_folder
from model_compression_toolkit.common.data_loader import FolderImageLoader
from model_compression_toolkit.common.framework_info import FrameworkInfo, ChannelAxis
from model_compression_toolkit.common.defaultdict import DefaultDict
from model_compression_toolkit.common import network_editors as network_editor

from model_compression_toolkit.keras.quantization_facade import keras_post_training_quantization, \
    keras_post_training_quantization_mixed_precision
from model_compression_toolkit.keras.quantization_facade import keras_post_training_quantization_experimental, \
    keras_gradient_post_training_quantization_experimental
from model_compression_toolkit.keras.quantization_facade import get_keras_gptq_config
from model_compression_toolkit.pytorch.quantization_facade import pytorch_post_training_quantization, \
    pytorch_post_training_quantization_mixed_precision
from model_compression_toolkit.pytorch.quantization_facade import pytorch_post_training_quantization_experimental, \
    pytorch_gradient_post_training_quantization_experimental

from model_compression_toolkit.keras.kpi_data_facade import keras_kpi_data, keras_kpi_data_experimental
from model_compression_toolkit.pytorch.kpi_data_facade import pytorch_kpi_data, pytorch_kpi_data_experimental

__version__ = "1.4.0"
