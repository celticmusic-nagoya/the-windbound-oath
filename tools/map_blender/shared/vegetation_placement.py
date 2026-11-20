"""Deterministic placement for a scene that supplies terrain and exclusion queries."""
import math
import random


class VegetationPlacement:
    def __init__(self, terrain, excluded, seed):
        self.terrain = terrain
        self.excluded = excluded
        self.rng = random.Random(seed)
        self.instances = []

    def candidate(self, asset, role, xy, *, radius, slope=30, align=0.3, scale=(0.9, 1.15),
                  sink=0.01, yaw=None, cluster=None, datum=None):
        x, y = xy
        scale = self.rng.uniform(*scale)
        radius *= scale
        if self.excluded(x, y, radius, role):
            return None
        center = self.terrain(x, y)
        if center is None:
            return None
        height, normal = center
        offsets = [(radius, 0), (-radius, 0), (0, radius), (0, -radius)]
        samples = [center] + [self.terrain(x + dx, y + dy) for dx, dy in offsets]
        ceiling = math.cos(math.radians(slope))
        if any(sample is None or sample[1][2] < ceiling or abs(sample[0] - height) > radius * 0.5 + 0.10
               for sample in samples):
            return None
        return {"asset": asset, "role": role, "xy": [x, y], "height": height if datum is None else datum,
                "normal": list(normal), "align": align, "radius": radius, "scale": scale, "sink": sink,
                "yaw": self.rng.uniform(0, math.tau) if yaw is None else yaw, "cluster": cluster}

    def patch(self, asset, role, box, step, *, count, jitter=0.24, **rules):
        """A bounded, jittered patch; deterministic per injected seed."""
        rng = self.rng
        (x0, y0), (x1, y1) = box
        cells = [(x0 + i * step, y0 + j * step)
                 for i in range(int((x1 - x0) / step) + 1)
                 for j in range(int((y1 - y0) / step) + 1)]
        rng.shuffle(cells)
        added = []
        for x, y in cells:
            point = self.candidate(asset, role, (x + rng.uniform(-jitter, jitter), y + rng.uniform(-jitter, jitter)), **rules)
            if point is not None:
                added.append(point)
            if len(added) >= count:
                break
        self.instances.extend(added)
        return added

    def cluster(self, asset, role, center, group, *, count=3, spread=0.65, **rules):
        """Commit a group atomically so a clipped patch never leaves a lone flower."""
        phase = self.rng.uniform(0, math.tau)
        points = []
        for index in range(count):
            yaw = phase + index * math.tau / count
            ring = self.rng.uniform(spread * 0.76, spread)
            xy = (center[0] + ring * math.cos(yaw), center[1] + ring * math.sin(yaw))
            point = self.candidate(asset, role, xy, cluster=group, **rules)
            if point is not None:
                points.append(point)
        if len(points) >= 2:
            self.instances.extend(points)
            return points
        return []
