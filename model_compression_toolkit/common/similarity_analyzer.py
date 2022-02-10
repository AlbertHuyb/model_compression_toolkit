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

from typing import Any

import numpy as np


#########################
#  Helpful functions
#########################


def validate_before_compute_similarity(float_tensor: Any, fxp_tensor: Any):
    """
    Assert different conditions before comparing two tensors (such as dimensionality and type).
    Args:
        float_tensor: First tensor to validate.
        fxp_tensor: Second tensor to validate.

    """
    assert isinstance(float_tensor, np.ndarray)
    assert isinstance(fxp_tensor, np.ndarray)
    assert float_tensor.shape == fxp_tensor.shape


def tensor_norm(x: np.ndarray, p: float = 2.0) -> np.float:
    """
    Compute the Lp-norm of a tensor x.
    Args:
        x: Tensor to compute its norm
        p: P to use for the Lp norm computation

    Returns:
        Lp norm of x.
    """
    return np.power(np.power(np.abs(x.flatten()), p).sum(), 1.0/p)


#########################
# Similarity functions
#########################

def compute_mse(float_tensor: np.ndarray, fxp_tensor: np.ndarray, norm: bool = False, norm_eps: float = 1e-8) -> float:
    """
    Compute the mean square error between two numpy arrays.

    Args:
        float_tensor: First tensor to compare.
        fxp_tensor: Second tensor to compare.
        norm: whether to normalize the error function result.
        norm_eps: epsilon value for error normalization stability.

    Returns:
        The MSE distance between the two tensors.
    """
    validate_before_compute_similarity(float_tensor, fxp_tensor)
    error = np.power(float_tensor - fxp_tensor, 2.0).mean()
    if norm:
        error /= (np.power(float_tensor, 2.0).mean() + norm_eps)
    return error


def compute_nmse(float_tensor: np.ndarray, fxp_tensor: np.ndarray) -> float:
    """
    Compute the normalized mean square error between two numpy arrays.

    Args:
        float_tensor: First tensor to compare.
        fxp_tensor: Second tensor to compare.

    Returns:
        The NMSE distance between the two tensors.
    """
    validate_before_compute_similarity(float_tensor, fxp_tensor)
    normalized_float_tensor = float_tensor / tensor_norm(float_tensor)
    normalized_fxp_tensor = fxp_tensor / tensor_norm(fxp_tensor)
    return np.mean(np.power(normalized_float_tensor - normalized_fxp_tensor, 2.0))


def compute_nmae(float_tensor: np.ndarray, fxp_tensor: np.ndarray) -> float:
    """
    Compute the normalized mean average error between two numpy arrays.

    Args:
        float_tensor: First tensor to compare.
        fxp_tensor: Second tensor to compare.

    Returns:
        The NMAE distance between the two tensors.
    """
    validate_before_compute_similarity(float_tensor, fxp_tensor)
    normalized_float_tensor = float_tensor / tensor_norm(float_tensor, 1.0)
    normalized_fxp_tensor = fxp_tensor / tensor_norm(fxp_tensor, 1.0)
    return np.mean(np.abs(normalized_float_tensor - normalized_fxp_tensor))


def compute_mae(float_tensor: np.ndarray, fxp_tensor: np.ndarray, norm: bool = False, norm_eps: float = 1e-8) -> float:
    """
    Compute the mean average error function between two numpy arrays.

    Args:
        float_tensor: First tensor to compare.
        fxp_tensor: Second tensor to compare.
        norm: whether to normalize the error function result.
        norm_eps: epsilon value for error normalization stability.

    Returns:
        The mean average distance between the two tensors.
    """

    validate_before_compute_similarity(float_tensor, fxp_tensor)
    error = np.abs(float_tensor - fxp_tensor).mean()
    if norm:
        error /= (np.abs(float_tensor).mean() + norm_eps)
    return error


def compute_cs(float_tensor: np.ndarray, fxp_tensor: np.ndarray, eps: float = 1e-8) -> float:
    """
    Compute the similarity between two tensor using cosine similarity.
    The returned values is between 0 to 1: the smaller returned value,
    the greater similarity there is between the two tensors.

    Args:
        float_tensor: First tensor to compare.
        fxp_tensor: Second tensor to compare.
        eps: Small value to avoid zero division.

    Returns:
        The cosine similarity between two tensors.
    """

    validate_before_compute_similarity(float_tensor, fxp_tensor)
    if np.all(fxp_tensor == 0) and np.all(float_tensor == 0):
        return 1.0

    float_flat = float_tensor.flatten()
    fxp_flat = fxp_tensor.flatten()
    float_norm = tensor_norm(float_tensor)
    fxp_norm = tensor_norm(fxp_tensor)

    # -1 <= cs <= 1
    cs = np.sum(float_flat * fxp_flat) / ((float_norm * fxp_norm) + eps)

    # Return a non-negative float (smaller value -> more similarity)
    return (1.0 - cs) / 2.0


def compute_lp_norm(float_tensor: np.ndarray, fxp_tensor: np.ndarray, p: int, norm: bool = False,
                    norm_eps: float = 1e-8) -> float:
    """
    Compute the error function between two numpy arrays.
    The error is computed based on Lp-norm distance of the tensors.

    Args:
        float_tensor: First tensor to compare.
        fxp_tensor: Second tensor to compare.
        p: p-norm to use for the Lp-norm distance.
        norm: whether to normalize the error function result.
        norm_eps: epsilon value for error normalization stability.

    Returns:
        The Lp-norm distance between the two tensors.
    """
    validate_before_compute_similarity(float_tensor, fxp_tensor)
    error = np.power(np.abs(float_tensor - fxp_tensor), p).mean()
    if norm:
        error /= (np.power(np.abs(float_tensor), p).mean() + norm_eps)
    return error
