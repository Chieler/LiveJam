import math
class Velocity:
    def __init__(self, tau = 0.20):
        self.px= self.py= self.pt  =None
        self.speed = 0.0
        self.angle = 0.0
        self.tau = tau

    def update(self, x, y, t):
        if self.pt is None or t - self.pt > 0.25:
            self.px, self.py, self.pt = x, y, t
            self.speed  = 0.0
            return  self.speed
        dt = t-self.pt
        if dt<=0:
            return self.speed
        vx, vy = (x-self.px)/dt, (y-self.py)/dt
        raw = math.hypot(vx, vy)

        a = 1 - math.exp(-dt / self.tau)                  # dt-aware!
        self.speed += a * (raw - self.speed)
        self.angle = math.degrees(math.atan2(vy, vx))

        self.px, self.py, self.pt = x, y, t
        return self.speed
    def reset(self):
        self.pt = None
        self.speed = 0.0