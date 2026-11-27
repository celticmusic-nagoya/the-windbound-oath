"""Deterministic foliage-only component selector for V82-D.
Inputs: mesh-local vertex positions, polygon vertex IDs, material indices and
explicit foliage slots. Whole components that touch protected wood are retained.
No geometry modification, topology decimation, scale-up or Blender dependency.
Output is a face-ID selection for an isolated work copy, NOT a silhouette PASS.
"""
from collections import defaultdict
from math import floor, isfinite, dist


def select_cards(vertices, faces, slots, foliage_slots, *, cell_size, keep_per_cell):
    if len(faces) != len(slots) or not isfinite(cell_size) or cell_size <= 0:
        raise ValueError('invalid dimensions')
    if not isinstance(keep_per_cell, int) or keep_per_cell < 1 or not foliage_slots:
        raise ValueError('invalid foliage selection')
    vertices = [tuple(map(float, v)) for v in vertices]
    if any(len(v) != 3 or not all(map(isfinite, v)) for v in vertices):
        raise ValueError('invalid vertex')
    if any(len(f) < 3 or any(not isinstance(i, int) or not 0 <= i < len(vertices) for i in f) for f in faces):
        raise ValueError('invalid face')
    leaf = [i for i, slot in enumerate(slots) if slot in foliage_slots]
    wood = set()
    leaf_set = set(leaf)
    for i, f in enumerate(faces):
        if i not in leaf_set:
            wood.update(f)
    parent = {i:i for i in leaf}
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    owner = {}
    for i in leaf:
        for j in faces[i]:
            if j in owner:
                a,b = root(i),root(owner[j])
                if a != b: parent[max(a,b)] = min(a,b)
            else: owner[j]=i
    groups = defaultdict(list)
    for i in leaf: groups[root(i)].append(i)
    protected = set(range(len(faces))) - leaf_set
    bins = defaultdict(list)
    comp = []
    for ids in groups.values():
        vids = sorted({v for i in ids for v in faces[i]})
        centre = tuple(sum(vertices[v][a] for v in vids)/len(vids) for a in range(3))
        stable = tuple(sorted(tuple(sorted(vertices[v] for v in faces[i])) for i in ids))
        row = (centre, stable, tuple(ids))
        comp.append(row)
        if wood.intersection(vids): protected.update(ids); continue
        key = tuple(floor(x/cell_size) for x in centre)
        bins[key].append(row)
    retained = set(protected)
    for key, rows in sorted(bins.items()):
        # First representative is nearest cell centre. Remaining representatives
        # maximize distance to selected centres, avoiding ordering-dependent runs.
        centre = tuple((x+.5)*cell_size for x in key)
        pool=sorted(rows,key=lambda r:(dist(r[0],centre),r[1]))
        chosen=[pool.pop(0)]
        while pool and len(chosen)<keep_per_cell:
            best=min(range(len(pool)), key=lambda k:(-min(dist(pool[k][0],r[0]) for r in chosen),pool[k][1]))
            chosen.append(pool.pop(best))
        for _,_,ids in chosen: retained.update(ids)
    removed=sorted(leaf_set-retained)
    assert not protected.intersection(removed)
    assert all(set(ids).issubset(retained) or set(ids).isdisjoint(retained) for _,_,ids in comp)
    return {'keep':sorted(retained),'remove':removed,'leaf_components':len(comp),'occupied_cells':len(bins),
            'protected_faces':len(protected),'retained_leaf_faces':len(leaf_set&retained),
            'removed_leaf_faces':len(removed)}
