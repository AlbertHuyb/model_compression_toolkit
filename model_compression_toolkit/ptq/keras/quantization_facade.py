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

from typing import Callable, List

from model_compression_toolkit.core import common
from model_compression_toolkit.core.common import Logger
from model_compression_toolkit.core.common.constants import TENSORFLOW
from model_compression_toolkit.core.common.mixed_precision.kpi import KPI
from model_compression_toolkit.core.common.framework_info import FrameworkInfo
from model_compression_toolkit.core.common.mixed_precision.mixed_precision_quantization_config import \
    MixedPrecisionQuantizationConfigV2
from model_compression_toolkit.core.common.post_training_quantization import post_training_quantization
from model_compression_toolkit import CoreConfig

import importlib

from model_compression_toolkit.core.common.target_platform.targetplatform2framework import TargetPlatformCapabilities


if importlib.util.find_spec("tensorflow") is not None\
        and importlib.util.find_spec("tensorflow_model_optimization") is not None:
    import tensorflow as tf
    from model_compression_toolkit.core.keras.default_framework_info import DEFAULT_KERAS_INFO
    from model_compression_toolkit.core.keras.keras_implementation import KerasImplementation
    from model_compression_toolkit.core.keras.keras_model_validation import KerasModelValidation
    from tensorflow.keras.models import Model
    from model_compression_toolkit.core.keras.constants import DEFAULT_TP_MODEL

    from model_compression_toolkit import get_target_platform_capabilities
    DEFAULT_KERAS_TPC = get_target_platform_capabilities(TENSORFLOW, DEFAULT_TP_MODEL)


    def keras_post_training_quantization_experimental(in_model: Model,
                                                      representative_data_gen: Callable,
                                                      target_kpi: KPI = None,
                                                      core_config: CoreConfig = CoreConfig(),
                                                      fw_info: FrameworkInfo = DEFAULT_KERAS_INFO,
                                                      target_platform_capabilities: TargetPlatformCapabilities = DEFAULT_KERAS_TPC):
        """
         Quantize a trained Keras model using post-training quantization. The model is quantized using a
         symmetric constraint quantization thresholds (power of two).
         The model is first optimized using several transformations (e.g. BatchNormalization folding to
         preceding layers). Then, using a given dataset, statistics (e.g. min/max, histogram, etc.) are
         being collected for each layer's output (and input, depends on the quantization configuration).
         For each possible bit width (per layer) a threshold is then being calculated using the collected
         statistics. Then, if given a mixed precision config in the core_config, using an ILP solver we find
         a mixed-precision configuration, and set a bit-width for each layer. The model is then quantized
         (both coefficients and activations by default).
         In order to limit the maximal model's size, a target KPI need to be passed after weights_memory
         is set (in bytes).

         Args:
             in_model (Model): Keras model to quantize.
             representative_data_gen (Callable): Dataset used for calibration.
             target_kpi (KPI): KPI object to limit the search of the mixed-precision configuration as desired.
             core_config (CoreConfig): Configuration object containing parameters of how the model should be quantized, including mixed precision parameters.
             fw_info (FrameworkInfo): Information needed for quantization about the specific framework (e.g., kernel channels indices, groups of layers by how they should be quantized, etc.).  `Default Keras info <https://github.com/sony/model_optimization/blob/main/model_compression_toolkit/core/keras/default_framework_info.py>`_
             target_platform_capabilities (TargetPlatformCapabilities): TargetPlatformCapabilities to optimize the Keras model according to.

         Returns:

             A quantized model and information the user may need to handle the quantized model.

         Examples:

             Import MCT:

             >>> import model_compression_toolkit as mct

             Import a Keras model:

             >>> from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2
             >>> model = MobileNetV2()

             Create a random dataset generator:

             >>> import numpy as np
             >>> def repr_datagen(): return [np.random.random((1,224,224,3))]

             Create a MCT core config, containing the quantization configuration:

             >>> config = mct.CoreConfig()

             If mixed precision is desired, create a MCT core config with a mixed-precision configuration, to quantize a model with different bitwidths for different layers.
             The candidates bitwidth for quantization should be defined in the target platform model:

             >>> config = mct.CoreConfig(mixed_precision_config=MixedPrecisionQuantizationConfigV2())

             For mixed-precision set a target KPI object:
             Create a KPI object to limit our returned model's size. Note that this value affects only coefficients
             that should be quantized (for example, the kernel of Conv2D in Keras will be affected by this value,
             while the bias will not):

             >>> kpi = mct.KPI(model.count_params() * 0.75)  # About 0.75 of the model size when quantized with 8 bits.

             Pass the model, the representative dataset generator, the configuration and the target KPI to get a
             quantized model:

             >>> quantized_model, quantization_info = mct.keras_post_training_quantization_experimental(model, repr_datagen, kpi, core_config=config)

             For more configuration options, please take a look at our `API documentation <https://sony.github.io/model_optimization/api/api_docs/modules/mixed_precision_quantization_config.html>`_.

         """
        KerasModelValidation(model=in_model,
                             fw_info=fw_info).validate()

        if core_config.mixed_precision_enable:
            if not isinstance(core_config.mixed_precision_config, MixedPrecisionQuantizationConfigV2):
                common.Logger.error("Given quantization config to mixed-precision facade is not of type "
                                    "MixedPrecisionQuantizationConfigV2. Please use keras_post_training_quantization API,"
                                    "or pass a valid mixed precision configuration.")

            common.Logger.info("Using experimental mixed-precision quantization. "
                               "If you encounter an issue please file a bug.")

        return post_training_quantization(in_model=in_model,
                                          representative_data_gen=representative_data_gen,
                                          core_config=core_config,
                                          fw_info=fw_info,
                                          fw_impl=KerasImplementation(),
                                          tpc=target_platform_capabilities,
                                          target_kpi=target_kpi)

else:
    # If tensorflow or tensorflow_model_optimization are not installed,
    # we raise an exception when trying to use these functions.
    def keras_post_training_quantization_experimental(*args, **kwargs):
        Logger.critical('Installing tensorflow and tensorflow_model_optimization is mandatory '
                        'when using keras_post_training_quantization_experimental. '
                        'Could not find Tensorflow package.')
