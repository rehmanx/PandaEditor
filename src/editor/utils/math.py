from panda3d.core import Vec3


class Math:

    @staticmethod
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

    @staticmethod
    def clamp(val, min, max):
        """clamps a value between min and max"""
        n = (val - min) / (max - min)
        return n

    @staticmethod
    def clamp_angle(angle, min_val, max_val):
        """clamp angle to pi, -pi range"""
        if angle < -360:
            angle += 360
        if angle > 360:
            angle -= 360
        clamp = max(min(angle, max_val), min_val)
        return clamp

    @staticmethod
    def euler_from_hpr(hpr):
        euler = Vec3(hpr.y, hpr.z, hpr.x)
        return euler

    @staticmethod
    def hpr_from_euler(euler):
        hpr = Vec3(euler.z, euler.x, euler.y)
        return hpr
