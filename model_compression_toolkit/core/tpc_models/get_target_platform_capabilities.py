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

from model_compression_toolkit.core.common.target_platform import TargetPlatformCapabilities

from model_compression_toolkit.core.tpc_models.default_tpc.target_platform_capabilities import \
    tpc_dict as default_tpc_dict
from model_compression_toolkit.core.tpc_models.tflite_tpc.target_platform_capabilities import \
    tpc_dict as tflite_tpc_dict
from model_compression_toolkit.core.tpc_models.qnnpack_tpc.target_platform_capabilities import \
    tpc_dict as qnnpack_tpc_dict
from model_compression_toolkit.core.keras.constants import DEFAULT_TP_MODEL, TFLITE_TP_MODEL, QNNPACK_TP_MODEL
from model_compression_toolkit.core.common.constants import LATEST

tpc_dict = {DEFAULT_TP_MODEL: default_tpc_dict,
            TFLITE_TP_MODEL: tflite_tpc_dict,
            QNNPACK_TP_MODEL: qnnpack_tpc_dict}


def get_target_platform_capabilities(fw_name: str,
                                     target_platform_name: str,
                                     target_platform_version: str = None) -> TargetPlatformCapabilities:
    """
    Get a TargetPlatformCapabilities by the target platform model name and the framework name.
    For now, it supports frameworks 'tensorflow' and 'pytorch'. For both of them
    the target platform model can be 'default','tflite', or 'qnnpack'.

    Args:
        fw_name: Framework name of the TargetPlatformCapabilities.
        target_platform_name: Target platform model name the model will use for inference.
        target_platform_version: Target platform capabilities version.
    Returns:
        A TargetPlatformCapabilities object that models the hardware and attaches
        a framework information to it.
    """
    assert target_platform_name in tpc_dict, f'Target platform {target_platform_name} is not defined!'
    fw_tpc = tpc_dict.get(target_platform_name)
    assert fw_name in fw_tpc, f'Framework {fw_name} is not supported in {target_platform_name}. Please make sure the relevant ' \
                              f'packages are installed when using MCT for optimizing a {fw_name} model. ' \
                              f'For Tensorflow, please install tensorflow and tensorflow-model-optimization. ' \
                              f'For PyTorch, please install torch.'
    tpc_versions = fw_tpc.get(fw_name)
    if target_platform_version is None:
        target_platform_version = LATEST
    else:
        assert target_platform_version in tpc_versions, f'TPC version {target_platform_version} is not supported for framework {fw_name}'
    return tpc_versions.get(target_platform_version)
