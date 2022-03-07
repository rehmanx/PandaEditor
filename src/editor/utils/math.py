
def convert_to_range(old_min, old_max, new_min, new_max, value):
    """convert from one range to another"""
    oldRange = old_max - old_min
    if oldRange == 0:
        newValue = new_min
        return newValue
    else:
        newRange = new_max - new_min
        newValue = (((value - old_min) * newRange) / oldRange) + new_min
        return newValue


def clamp(val, min, max):
    """clamps a value between min and max"""
    n = (val - min) / (max - min)
    return n


def clamp_angle(angle, min_val, max_val):
    """clamp angle to pi, -pi range"""
    if angle < -360:
        angle += 360
    if angle > 360:
        angle -= 360
    clamp = max(min(angle, max_val), min_val)
    return clamp

