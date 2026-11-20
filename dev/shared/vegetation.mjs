import * as T from 'three';

const up = new T.Vector3(0, 1, 0);
const prevailing = new T.Vector2(.959, .282);

// Weight zero anchors the root. The zero-strength branch leaves transformed exactly equal to position.
export function bindVegetationWind(material, profile, wind) {
  material.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, {
      ecoStrength: wind.strength,
      ecoTime: wind.time,
      ecoDirection: { value: prevailing },
      ecoProfile: { value: new T.Vector3(profile.amplitude_m, profile.frequency_hz, profile.flutter) },
    });
    shader.vertexShader = `
      attribute float _wind_weight;
      uniform float ecoStrength, ecoTime;
      uniform vec2 ecoDirection;
      uniform vec3 ecoProfile;
    ` + shader.vertexShader.replace('#include <begin_vertex>', `
      #include <begin_vertex>
      if (ecoStrength > 0.0 && _wind_weight > 0.0) {
        vec3 root = instanceMatrix[3].xyz;
        vec3 direction = vec3(ecoDirection.x, 0.0, ecoDirection.y);
        vec3 local = normalize(vec3(dot(direction, instanceMatrix[0].xyz),
                                     dot(direction, instanceMatrix[1].xyz),
                                     dot(direction, instanceMatrix[2].xyz)));
        float phase = dot(root.xz, vec2(.47, .29)) + 6.2831853 * ecoProfile.y * ecoTime;
        float sway = sin(phase) + ecoProfile.z * sin(phase * 2.31 + position.z * 3.0);
        transformed += local * (ecoProfile.x * ecoStrength * _wind_weight * sway);
      }
    `);
  };
  material.customProgramCacheKey = () => 'windweighted-vegetation-v1';
}

export async function createVegetation({ loader, base, placement, root, initialStrength = 0 }) {
  const wind = { strength: { value: initialStrength }, time: { value: 0 } };
  const overlay = new T.Group();
  overlay.name = 'Vegetation overlays';
  root.add(overlay);
  const prototypes = new Map(await Promise.all(Object.entries(placement.assets).map(async ([asset, record]) => {
    const gltf = await loader.loadAsync(new URL(record.path, base).href);
    const parts = [];
    gltf.scene.traverse((node) => {
      const profile = node.userData.eco_wind;
      if (!profile) return;
      node.traverse((part) => {
        if (!part.isMesh) return;
        if (!part.geometry.hasAttribute('_wind_weight')) throw new Error(`Missing wind weights for ${asset}`);
        const material = part.material.clone();
        bindVegetationWind(material, profile, wind);
        parts.push({ geometry: part.geometry, material });
      });
    });
    if (!parts.length) throw new Error(`Missing vegetation primitives for ${asset}`);
    return [asset, parts];
  })));
  const groups = new Map();
  for (const instance of placement.instances) {
    if (!groups.has(instance.asset)) groups.set(instance.asset, []);
    groups.get(instance.asset).push(instance);
  }
  const batches = [];
  for (const [asset, instances] of groups) {
    const parts = prototypes.get(asset);
    const localBounds = new T.Sphere();
    for (const { geometry } of parts) {
      geometry.computeBoundingSphere();
      localBounds.union(geometry.boundingSphere);
    }
    localBounds.radius += 0.32; // Covers the maximum authored sway and flutter.
    const members = instances.map(({ role, xy, height, sink, normal, align, yaw, scale }) => {
      const tilt = up.clone().lerp(new T.Vector3(normal[0], normal[2], -normal[1]), align).normalize();
      const rotation = new T.Quaternion().setFromUnitVectors(up, tilt)
        .multiply(new T.Quaternion().setFromAxisAngle(up, yaw));
      const transform = new T.Matrix4().compose(new T.Vector3(xy[0], height - sink, -xy[1]),
        rotation, new T.Vector3().setScalar(scale));
      return { transform, bounds: localBounds.clone().applyMatrix4(transform), range: placement.roles[role].range };
    });
    const meshes = parts.map(({ material, geometry }) => {
      const mesh = new T.InstancedMesh(geometry, material, instances.length);
      mesh.instanceMatrix.setUsage(T.DynamicDrawUsage);
      mesh.frustumCulled = false; // The members are individually culled before packing the batch.
      mesh.count = 0;
      overlay.add(mesh);
      return mesh;
    });
    batches.push({ members, meshes, visible: [] });
  }
  const cameraInOverlay = new T.Vector3();
  const frustum = new T.Frustum();
  const clip = new T.Matrix4();
  return {
    setStrength(value) {
      if (Number.isFinite(value)) wind.strength.value = T.MathUtils.clamp(value, 0, 1);
    },
    get strength() { return wind.strength.value; },
    update(camera, time) {
      wind.time.value = time;
      camera.updateMatrixWorld();
      overlay.worldToLocal(camera.getWorldPosition(cameraInOverlay));
      frustum.setFromProjectionMatrix(clip.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse)
        .multiply(overlay.matrixWorld));
      for (const batch of batches) {
        const visible = batch.members.filter(({ bounds, range }) =>
          cameraInOverlay.distanceToSquared(bounds.center) < (range + bounds.radius) ** 2 &&
          frustum.intersectsSphere(bounds));
        if (visible.length === batch.visible.length && visible.every((item, i) => item === batch.visible[i])) continue;
        for (const mesh of batch.meshes) {
          mesh.count = visible.length;
          for (let index = 0; index < visible.length; index++) mesh.setMatrixAt(index, visible[index].transform);
          mesh.instanceMatrix.needsUpdate = true;
        }
        batch.visible = visible;
      }
    },
  };
}
