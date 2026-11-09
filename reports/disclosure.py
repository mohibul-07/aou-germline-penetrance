"""Conservative small-cell helpers for internal report preparation.
Inputs: numeric counts. Outputs: safe/unsafe flag, never participant data.
Decision: suppress inclusive 1–20, including complements. This is not a release
approval: overlapping margins and linked outputs require additional review.
"""
import math

def safe_counts(values):
    return all(v is not None and math.isfinite(float(v)) and float(v)>=0 and
               float(v).is_integer() and not 1<=float(v)<=20 for v in values)
