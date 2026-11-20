export function makeNavigation(data) {
  const { origin, stride, width, height, levels } = data;
  const cell = (x, z) => {
    const col = Math.round((x - origin[0]) / stride);
    const row = Math.round((z - origin[1]) / stride);
    return col < 0 || row < 0 || col >= width || row >= height ? -1 : row * width + col;
  };
  const open = (id) => id >= 0 && id < levels.length && levels[id] !== null;
  const point = (id) => [origin[0] + id % width * stride, origin[1] + Math.floor(id / width) * stride];
  const around = (id) => {
    const [x, z] = point(id);
    return [[stride, 0], [-stride, 0], [0, stride], [0, -stride]]
      .map(([dx, dz]) => cell(x + dx, z + dz))
      .filter((next) => open(next) && Math.abs(levels[id] - levels[next]) <= data.maxStep);
  };
  function path(x, z, tx, tz) {
    const start = cell(x, z);
    const goal = cell(tx, tz);
    if (!open(start) || !open(goal)) return [];
    const parents = new Map([[start, -1]]);
    const queue = [start];
    for (let i = 0; i < queue.length && !parents.has(goal); i++) {
      for (const next of around(queue[i])) {
        if (parents.has(next)) continue;
        parents.set(next, queue[i]);
        queue.push(next);
      }
    }
    if (!parents.has(goal)) return [];
    const route = [];
    for (let id = goal; id !== -1; id = parents.get(id)) route.push(point(id));
    return route.reverse();
  }
  return { cell, open, point, around, path, levels };
}

export function groundStep(position, x, z, nav, cast, maxStep) {
  const oldCell = nav.cell(position.x, position.z);
  const next = nav.cell(x, z);
  if (!nav.open(next)) return null;
  if (next !== oldCell && !nav.around(oldCell).includes(next)) return null;
  const hit = cast(x, z);
  if (hit === null || Math.abs(hit - position.y) > maxStep) return null;
  return { x, y: hit, z };
}
