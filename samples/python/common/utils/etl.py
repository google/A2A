"""
ETL: Extract, Transform, Load

This module contains utility functions for extracting, transforming, and loading data.
"""


def truncate_leaves(obj: dict) -> dict:
    """
    Recursively navigate the json and truncate leaves to maximum 1000 characters

    Args:
        obj: The object to truncate

    Returns:
        Object with truncated leaves
    """

    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, dict):
                truncate_leaves(value)
            elif isinstance(value, str) and len(value) > 1000:
                obj[key] = value[:1000] + '...'
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        truncate_leaves(item)
                    elif isinstance(item, str) and len(item) > 1000:
                        obj[key] = item[:1000] + '...'
                    else:
                        pass
            else:
                pass

    return obj
