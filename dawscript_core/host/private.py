# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

import math
from typing import Callable, Dict

# Step size for dB increments in lookup tables (in dB)
DB_STEP = 0.1

# Lookup tables for normalized volume to dB and dB to normalized volume
_norm_to_db_table: Dict[float, float] = {}
_db_to_norm_table: Dict[float, float] = {}


def build_vol_lookup(
    db_to_norm_func: Callable[[float], float],
    min_db: float,
    max_db: float
) -> None:
    """
    Build lookup tables for converting between dB and normalized volume.

    Creates two tables: one mapping dB to normalized volume (0 to max norm) and
    another mapping normalized volume to dB, using the provided conversion function.
    The tables cover dB values from min_db to max_db in steps of DB_STEP (0.1 dB).

    Args:
        db_to_norm_func: Function that converts a dB value to normalized volume.
        min_db: Minimum finite dB value for the table (default: -150.0).
        max_db: Maximum dB value for the table (default: 0.0).

    Raises:
        ValueError: If max_db < min_db or if min_db/max_db are not finite.
    """
    if max_db < min_db:
        raise ValueError("max_db must be greater than or equal to min_db")
    if not math.isfinite(min_db) or not math.isfinite(max_db):
        raise ValueError("min_db and max_db must be finite")

    global _norm_to_db_table, _db_to_norm_table
    _norm_to_db_table = {}
    _db_to_norm_table = {}

    # Map zero volume (0.0) to -inf dB and vice versa
    _norm_to_db_table[0.0] = -math.inf
    _db_to_norm_table[-math.inf] = 0.0

    # Round max_db to nearest DB_STEP to ensure inclusion in table
    max_db_rounded = round(max_db / DB_STEP) * DB_STEP
    max_db_rounded = round(max_db_rounded, 6)

    db = min_db
    while db <= max_db_rounded + 1e-8:  # Small tolerance for floating-point precision
        norm = db_to_norm_func(db)
        norm_rounded = round(norm, 6)  # Round to 6 decimals for table consistency
        db_rounded = round(db, 6)
        _db_to_norm_table[db_rounded] = norm_rounded
        _norm_to_db_table[norm_rounded] = db_rounded
        db += DB_STEP


def nearest_db_to_norm(db: float) -> float:
    """
    Convert dB to normalized volume using the closest table entry.

    Rounds the input dB to the nearest 0.1 dB step (DB_STEP) to match table keys.
    Clamps inputs to the table's range (min_db to max_db) to handle out-of-bounds values.

    Args:
        db: dB value to convert (can be -inf).

    Returns:
        float: Normalized volume (0.0 to max norm, e.g., 1.0 for max_db=0.0).

    Raises:
        ValueError: If the lookup table is not initialized.
    """
    if not _db_to_norm_table:
        raise ValueError("Lookup table is not initialized. Call build_vol_lookup first.")
    if db == -math.inf:
        return 0.0
    # Clamp to table range to handle out-of-bounds inputs
    max_db_key = max(_db_to_norm_table.keys())
    min_db_key = min((k for k in _db_to_norm_table.keys() if k != -math.inf))
    if db > max_db_key:
        return _db_to_norm_table[max_db_key]
    if db < min_db_key:
        return _db_to_norm_table[min_db_key]
    # Round to nearest 0.1 dB step to match table keys
    quant_db = round(db / DB_STEP) * DB_STEP
    quant_db = round(quant_db, 6)  # Ensure 6-decimal precision
    return _db_to_norm_table.get(quant_db, _db_to_norm_table[max_db_key])


def nearest_norm_to_db(vol: float) -> float:
    """
    Convert normalized volume to dB using the closest table entry.

    Checks for an exact match in the table; if none, finds the closest normalized
    volume key. Clamps inputs to the table's range (0.0 to max norm).

    Args:
        vol: Normalized volume to convert (typically 0.0 to max norm, e.g., 1.0).

    Returns:
        float: dB value (can be -inf for vol=0.0).

    Raises:
        ValueError: If the lookup table is not initialized.
    """
    if not _norm_to_db_table:
        raise ValueError("Lookup table is not initialized. Call build_vol_lookup first.")
    if vol == 0.0:
        return -math.inf
    # Clamp to table range to handle out-of-bounds inputs
    max_norm_key = max(_norm_to_db_table.keys())
    if vol > max_norm_key:
        return _norm_to_db_table[max_norm_key]
    if vol < 0.0:
        return -math.inf
    quant_vol = round(vol, 6)  # Round to 6 decimals to match table keys
    if quant_vol in _norm_to_db_table:
        return _norm_to_db_table[quant_vol]
    # Find the closest normalized volume in the table
    closest_norm = min(_norm_to_db_table.keys(), key=lambda x: abs(x - quant_vol))
    return _norm_to_db_table[closest_norm]
