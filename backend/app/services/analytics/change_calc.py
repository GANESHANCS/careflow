from typing import Optional


def calculate_percentage_change(
    current: Optional[float], 
    previous: Optional[float]
) -> Optional[float]:
    """
    Safely calculates percentage change between current and previous values.
    Returns None if either value is None, or if previous value is 0.0 (prevents ZeroDivisionError).
    Formula: ((current - previous) / previous) * 100
    """
    if current is None or previous is None:
        return None
    if previous == 0.0:
        return None
    
    change = ((current - previous) / abs(previous)) * 100.0
    return round(change, 2)


def calculate_mom_change(
    current: Optional[float], 
    previous: Optional[float]
) -> Optional[float]:
    """Month-over-Month percentage change."""
    return calculate_percentage_change(current, previous)


def calculate_yoy_change(
    current: Optional[float], 
    previous_year: Optional[float]
) -> Optional[float]:
    """Year-over-Year percentage change."""
    return calculate_percentage_change(current, previous_year)
