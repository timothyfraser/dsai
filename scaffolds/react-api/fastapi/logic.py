"""The real work, as plain functions. No web framework is imported here.

Keeping this file free of FastAPI is what lets you test it without a server.
"""


def summarize(values):
    """Count, mean, min and max of a list of numbers.

    Raises ValueError on an empty list or on anything that is not a number,
    so the route can turn the problem into a clean error message.
    """
    if not isinstance(values, list) or len(values) == 0:
        raise ValueError("values must be a non-empty list of numbers")
    nums = []
    for v in values:
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ValueError(f"not a number: {v!r}")
        nums.append(float(v))
    return {
        "n": len(nums),
        "mean": sum(nums) / len(nums),
        "min": min(nums),
        "max": max(nums),
    }
