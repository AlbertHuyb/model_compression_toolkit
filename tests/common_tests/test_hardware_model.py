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

import unittest

import model_compression_toolkit as mct
from model_compression_toolkit.common.target_platform import get_default_quantization_config_options, \
    TargetPlatformCapabilities
from model_compression_toolkit.tpc_models.default_tp_model import get_default_tp_model

hwm = mct.target_platform

TEST_QC = hwm.OpQuantizationConfig(enable_activation_quantization=True,
                                   enable_weights_quantization=True,
                                   activation_n_bits=8,
                                   weights_n_bits=8,
                                   weights_per_channel_threshold=True,
                                   activation_quantization_method=hwm.QuantizationMethod.POWER_OF_TWO,
                                   weights_quantization_method=hwm.QuantizationMethod.POWER_OF_TWO,
                                   quantization_preserving=False,
                                   fixed_scale=None,
                                   fixed_zero_point=None,
                                   weights_multiplier_nbits=None
                                   )
TEST_QCO = hwm.QuantizationConfigOptions([TEST_QC])


class HardwareModelingTest(unittest.TestCase):

    def test_not_initialized_hwm(self):
        with self.assertRaises(Exception) as e:
            mct.target_platform.get_default_quantization_config_options()
        self.assertEqual('Target platform model is not initialized.', str(e.exception))

    def test_get_default_options(self):
        with hwm.TargetPlatformModel(TEST_QCO):
            self.assertEqual(hwm.get_default_quantization_config_options(), TEST_QCO)

    def test_immutable_hwm(self):
        model = hwm.TargetPlatformModel(TEST_QCO)
        with self.assertRaises(Exception) as e:
            with model:
                hwm.OperatorsSet("opset")
            model.operator_set = []
        self.assertEqual('Immutable class. Can\'t edit attributes', str(e.exception))

    def test_default_options_more_than_single_qc(self):
        test_qco = hwm.QuantizationConfigOptions([TEST_QC, TEST_QC], base_config=TEST_QC)
        with self.assertRaises(Exception) as e:
            hwm.TargetPlatformModel(test_qco)
        self.assertEqual('Default QuantizationConfigOptions must contain only one option', str(e.exception))


class OpsetTest(unittest.TestCase):

    def test_opset_qco(self):
        hm = hwm.TargetPlatformModel(TEST_QCO, name='test')
        opset_name = "ops_3bit"
        with hm:
            qco_3bit = get_default_quantization_config_options().clone_and_edit(activation_n_bits=3)
            hwm.OperatorsSet(opset_name, qco_3bit)

        for op_qc in hm.get_config_options_by_operators_set(opset_name).quantization_config_list:
            self.assertEqual(op_qc.activation_n_bits, 3)

        self.assertTrue(hm.is_opset_in_model(opset_name))
        self.assertFalse(hm.is_opset_in_model("ShouldNotBeInModel"))
        self.assertEqual(hm.get_config_options_by_operators_set(opset_name), qco_3bit)

    def test_opset_concat(self):
        hm = hwm.TargetPlatformModel(TEST_QCO, name='test')
        with hm:
            a = hwm.OperatorsSet('opset_A')
            b = hwm.OperatorsSet('opset_B',
                                 get_default_quantization_config_options().clone_and_edit(activation_n_bits=2))
            hwm.OperatorsSet('opset_C')  # Just add it without using it in concat
            hwm.OperatorSetConcat(a, b)
        self.assertEqual(len(hm.operator_set), 4)
        self.assertTrue(hm.is_opset_in_model("opset_A_opset_B"))
        self.assertTrue(hm.get_config_options_by_operators_set('opset_A_opset_B') is None)

    def test_non_unique_opset(self):
        hm = hwm.TargetPlatformModel(hwm.QuantizationConfigOptions([TEST_QC]))
        with self.assertRaises(Exception) as e:
            with hm:
                hwm.OperatorsSet("conv")
                hwm.OperatorsSet("conv")
        self.assertEqual('OperatorsSet must have unique names', str(e.exception))


class QCOptionsTest(unittest.TestCase):

    def test_empty_qc_options(self):
        with self.assertRaises(AssertionError) as e:
            hwm.QuantizationConfigOptions([])
        self.assertEqual('Options list can not be empty', str(e.exception))

    def test_list_of_no_qc(self):
        with self.assertRaises(AssertionError) as e:
            hwm.QuantizationConfigOptions([TEST_QC, 3])
        self.assertEqual(
            'Options should be a list of QuantizationConfig objects, but found an object type: <class \'int\'>',
            str(e.exception))

    def test_clone_and_edit_options(self):
        modified_options = TEST_QCO.clone_and_edit(activation_n_bits=3,
                                                   weights_n_bits=5)

        self.assertEqual(modified_options.quantization_config_list[0].activation_n_bits, 3)
        self.assertEqual(modified_options.quantization_config_list[0].weights_n_bits, 5)

    def test_qco_without_base_config(self):
        hwm.QuantizationConfigOptions([TEST_QC])  # Should work fine as it has only one qc.
        with self.assertRaises(Exception) as e:
            hwm.QuantizationConfigOptions([TEST_QC, TEST_QC])  # Should raise exception as base_config was not passed
        self.assertEqual(
            'When quantization config options contains more than one configuration, a base_config must be passed for '
            'non-mixed-precision optimization process',
            str(e.exception))

    def test_get_qco_for_none(self):
        fw_hwm = TargetPlatformCapabilities(get_default_tp_model())
        with self.assertRaises(Exception) as e:
            fw_hwm.get_qco_by_node(None)
        self.assertEqual('Can not retrieve QC options for None node', str(e.exception))


class FusingTest(unittest.TestCase):

    def test_fusing_single_opset(self):
        hm = hwm.TargetPlatformModel(hwm.QuantizationConfigOptions([TEST_QC]))
        with hm:
            add = hwm.OperatorsSet("add")
            with self.assertRaises(Exception) as e:
                hwm.Fusing([add])
            self.assertEqual('Fusing can not be created for a single operators group', str(e.exception))

    def test_fusing_contains(self):
        hm = hwm.TargetPlatformModel(hwm.QuantizationConfigOptions([TEST_QC]))
        with hm:
            conv = hwm.OperatorsSet("conv")
            add = hwm.OperatorsSet("add")
            tanh = hwm.OperatorsSet("tanh")
            hwm.Fusing([conv, add])
            hwm.Fusing([conv, add, tanh])

        self.assertEqual(len(hm.fusing_patterns), 2)
        f0, f1 = hm.fusing_patterns[0], hm.fusing_patterns[1]
        self.assertTrue(f1.contains(f0))
        self.assertFalse(f0.contains(f1))
        self.assertTrue(f0.contains(f0))
        self.assertTrue(f1.contains(f1))

    def test_fusing_contains_with_opset_concat(self):
        hm = hwm.TargetPlatformModel(hwm.QuantizationConfigOptions([TEST_QC]))
        with hm:
            conv = hwm.OperatorsSet("conv")
            add = hwm.OperatorsSet("add")
            tanh = hwm.OperatorsSet("tanh")
            add_tanh = hwm.OperatorSetConcat(add, tanh)
            hwm.Fusing([conv, add])
            hwm.Fusing([conv, add_tanh])
            hwm.Fusing([conv, add, tanh])

        self.assertEqual(len(hm.fusing_patterns), 3)
        f0, f1, f2 = hm.fusing_patterns[0], hm.fusing_patterns[1], hm.fusing_patterns[2]

        self.assertTrue(f0.contains(f0))
        self.assertTrue(f1.contains(f1))
        self.assertTrue(f2.contains(f2))

        self.assertTrue(f2.contains(f0))
        self.assertTrue(f1.contains(f0))

        self.assertFalse(f0.contains(f1))
        self.assertFalse(f0.contains(f2))

        self.assertFalse(f2.contains(f1))
        self.assertFalse(f1.contains(f2))
