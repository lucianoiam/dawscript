# SPDX-FileCopyrightText: 2025 Luciano Iam <oss@lucianoiam.com>
# SPDX-License-Identifier: MIT

def map_interp(n, x_val, y_val):
    """
    Maps a value n from one set of values (x_val) to another (y_val) using linear interpolation.
    
    Args:
        n (float): The value to map, typically between 0 and 1.
        x_val (list): List of source values in ascending order.
        y_val (list): List of target values corresponding to x_val.
    
    Returns:
        float: The interpolated value from y_val, rounded to 3 decimal places.
        None: If n is out of range (< 0 or > 1) or if interpolation fails.
    """
    # Validate input
    if not isinstance(n, (int, float)) or n < 0 or n > 1:
        return None

    # Check for exact match in x_val
    if n in x_val:
        return y_val[x_val.index(n)]
    
    # Iterate through x_val to find bracketing points
    for i in range(len(x_val) - 1):
        x1, x2 = x_val[i], x_val[i + 1]
        y1, y2 = y_val[i], y_val[i + 1]
        
        # Check if n lies between x1 and x2 (ascending order)
        if x1 <= n <= x2:
            # Perform linear interpolation: y = y1 + (y2 - y1) * (n - x1) / (x2 - x1)
            fraction = (n - x1) / (x2 - x1)
            result = y1 + (y2 - y1) * fraction
            return round(result, 3)
    
    return None  # Return None if n is outside the interpolation range
