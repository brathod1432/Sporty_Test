#!/usr/bin/env python3.11
"""Array and path helpers built on numpy."""
from __future__ import annotations
__author__ = "Brijesh Rathod [bgrathod00@gmail.com]"

from pathlib import Path
from typing import Sequence

import numpy as np

from libs.logger import ProjectLogger, get_logger

logger = get_logger("GeneralUtils")


def ensure_directory(path_like: str | Path) -> Path:
    """Create a directory (and its parents) if it does not exist.

    Args:
        path_like: directory to create.
    Returns:
        The Path to the directory.
    """
    path = Path(path_like)
    path.mkdir(parents=True, exist_ok=True)
    return path


def as_float_array(
    values: object,
    *,
    name: str = "value",
    ndim: int | None = None,
    shape: tuple[int, ...] | None = None,
) -> np.ndarray:
    """Coerce values to a float ndarray and optionally check its dimensions.

    Args:
        values: anything numpy can coerce to a float array.
        name: label used in the failure message.
        ndim: required number of dimensions, or None to skip the check.
        shape: required shape, or None to skip the check.
    Returns:
        The float ndarray.
    Raises:
        ValueError: when ndim or shape does not match.
    """
    array = np.asarray(values, dtype=float)

    if ndim is not None and array.ndim != ndim:
        msg = f"{name} must have {ndim} dimension(s), got {array.ndim}."
        logger.error(msg)
        raise ValueError(msg)

    if shape is not None and array.shape != shape:
        msg = f"{name} must have shape {shape}, got {array.shape}."
        logger.error(msg)
        raise ValueError(msg)

    return array


def ensure_vector(values: object, *, name: str = "vector", length: int | None = None) -> np.ndarray:
    """Coerce values to a 1-D float array and optionally check its length.

    Args:
        values: anything numpy can coerce to a 1-D float array.
        name: label used in the failure message.
        length: required element count, or None to skip the check.
    Returns:
        The 1-D float ndarray.
    Raises:
        ValueError: when the input is not 1-D or the length does not match.
    """
    vector = as_float_array(values, name=name, ndim=1)

    if length is not None and vector.size != length:
        msg = f"{name} must contain {length} values, got {vector.size}."
        logger.error(msg)
        raise ValueError(msg)

    return vector


def ensure_matrix(values: object, *, name: str = "matrix", shape: tuple[int, int] | None = None) -> np.ndarray:
    """Coerce values to a 2-D float array and optionally check its shape.

    Args:
        values: anything numpy can coerce to a 2-D float array.
        name: label used in the failure message.
        shape: required (rows, cols), or None to skip the check.
    Returns:
        The 2-D float ndarray.
    Raises:
        ValueError: when the input is not 2-D or the shape does not match.
    """
    matrix = as_float_array(values, name=name, ndim=2)

    if shape is not None and matrix.shape != shape:
        msg = f"{name} must have shape {shape}, got {matrix.shape}."
        logger.error(msg)
        raise ValueError(msg)

    return matrix


def describe_array(values: object) -> str:
    """Render an array's shape as a short label, e.g. "1x3" or "2x2x4".

    Args:
        values: the array to describe.
    Returns:
        The shape label; "scalar (1x1)" for a 0-d array.
    """
    array = np.asarray(values)
    if array.ndim == 0:
        return "scalar (1x1)"
    if array.ndim == 1:
        return f"1x{array.shape[0]}"
    return "x".join(str(dim) for dim in array.shape)


def _select_display_slice(array: np.ndarray) -> tuple[np.ndarray, str]:
    """Reduce an n-d array to a 2-D slice for printing, with a shape label.

    Args:
        array: the array to slice.
    Returns:
        The 2-D display slice and the label describing the original shape.
    """
    if array.ndim == 0:
        return array.reshape(1, 1), "scalar (1x1)"
    if array.ndim == 1:
        return array.reshape(1, -1), f"1x{array.shape[0]}"
    if array.ndim == 2:
        return array, f"{array.shape[0]}x{array.shape[1]}"

    selector = (0,) * (array.ndim - 2) + (slice(None), slice(None))
    display = array[selector]
    return display, f"{describe_array(array)} (showing first 2D slice {display.shape})"


def print_matrices(
    arrays: Sequence[object],
    *,
    logger_instance: ProjectLogger | None = None,
    color: str = "cyan",
) -> None:
    """Log each array in turn, labelled with its shape.

    Args:
        arrays: the arrays to render.
        logger_instance: optional logger to write through; defaults to this module's.
        color: colour for the shape and value lines.
    """
    active_logger = logger_instance or logger

    for index, matrix_like in enumerate(arrays, start=1):
        try:
            array = np.asarray(matrix_like)
            display, shape_str = _select_display_slice(array)
        except Exception as exc:
            active_logger(
                f"[{index}] Could not render matrix-like value: {exc}",
                logLevel="ERROR",
                color="red",
            )
            continue

        active_logger(f"# MATRIX [{index}] - shape {shape_str}", color=color)
        active_logger(f"\n{display}", color=color)


__all__ = [
    "as_float_array",
    "describe_array",
    "ensure_directory",
    "ensure_matrix",
    "ensure_vector",
    "print_matrices",
]