import * as T from 'three';
import { GLTFLoader } from './vendor/GLTFLoader.js';
import { sunset } from './sunset.mjs';
import { adaptSurfaces } from './surface.mjs';
import { makeNavigation, groundStep } from './navigation.mjs';

const canvas = document.querySelector('canvas');
const status = document.querySelector('#status');
const asset = new URL('../../assets/candidates/lind/windwaiting-cliff-playable/', import.meta.url);
const ray = new T.Raycaster();
const down = new T.Vector3(0, -1, 0);

function batchMeadow(root, nodes) {
  const meadow = new Map();
  root.updateMatrixWorld(true);
  for (const [name, object] of nodes) {
    if (!name.startsWith('eco_')) continue;
    object.traverse((mesh) => {
      if (!mesh.isMesh) return;
      const key = mesh.geometry.uuid + mesh.material.uuid;
      if (!meadow.has(key)) meadow.set(key, []);
      meadow.get(key).push(mesh);
    });
  }
  const inverse = root.matrixWorld.clone().invert();
  for (const meshes of meadow.values()) {
    if (meshes.length < 2) continue;
    const batch = new T.InstancedMesh(meshes[0].geometry, meshes[0].material, meshes.length);
    batch.name = 'Meadow instances';
    meshes.forEach((mesh, index) => {
      batch.setMatrixAt(index, inverse.clone().multiply(mesh.matrixWorld));
      mesh.visible = false;
    });
    batch.computeBoundingSphere();
    root.add(batch);
  }
}

async function play() {
  const [gltf, data] = await Promise.all([
    new GLTFLoader().loadAsync(new URL('cliff.glb', asset).href),
    fetch(new URL('navigation.json', asset)).then((response) => {
      if (!response.ok) throw new Error('Navigation HTTP ' + response.status);
      return response.json();
    }),
  ]);
  const nav = makeNavigation(data);
  const renderer = new T.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
  renderer.toneMapping = T.ACESFilmicToneMapping;
  const scene = new T.Scene();
  scene.background = new T.Color(0xc2a1a1);
  scene.fog = new T.FogExp2(0xa79bae, 0.010);
  scene.add(gltf.scene);
  adaptSurfaces(gltf.scene, renderer);
  scene.add(new T.HemisphereLight(0xffddd1, 0x616c75, 2.15));
  const sun = new T.DirectionalLight(0xffbb78, 2.2);
  sun.position.fromArray(data.sun);
  scene.add(sun);
  const nodes = new Map();
  gltf.scene.traverse((object) => { if (object.userData.name) nodes.set(object.userData.name, object); });
  const sea = nodes.get('Provisional sea at Z=0');
  const updateSunset = sunset(scene, sea, sun.position);
  function meshes(name) {
    const list = [];
    nodes.get(name)?.traverse((object) => {
      if (object.isMesh) list.push(object);
    });
    return list;
  }
  const ground = data.ground.flatMap(meshes);
  if (data.ground.some((name) => meshes(name).length === 0)) throw new Error('Missing ground mesh');
  const blockers = ground.concat(data.cameraBlockers.flatMap(meshes));
  batchMeadow(gltf.scene, nodes);
  const camera = new T.PerspectiveCamera(49, 1, 0.08, 200);
  const player = new T.Group();
  const cloak = new T.Mesh(new T.CylinderGeometry(0.17, 0.28, 0.61, 12), new T.MeshStandardMaterial({ color: 0x284f41 }));
  cloak.position.y = 0.48;
  const head = new T.Mesh(new T.SphereGeometry(0.13, 12, 8), new T.MeshStandardMaterial({ color: 0xe6cb9b }));
  head.position.y = 0.92;
  const boots = new T.Mesh(new T.CylinderGeometry(0.17, 0.19, 0.19, 10), new T.MeshStandardMaterial({ color: 0x3a2d27 }));
  boots.position.y = 0.095;
  player.add(cloak, head, boots);
  scene.add(player);
  scene.updateMatrixWorld(true);
  const position = player.position;
  const start = new T.Vector3().fromArray(data.spawn);
  const keys = new Set();
  const directions = new Set(['KeyW', 'KeyA', 'KeyS', 'KeyD', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight']);
  let yaw = data.cameraYaw;
  let pitch = 0.33;
  let route = [];
  let drag;
  function reset() {
    position.copy(start);
    yaw = data.cameraYaw;
    pitch = 0.33;
    route = [];
    keys.clear();
  }
  function cast(x, z) {
    ray.set(new T.Vector3(x, data.rayTop, z), down);
    return ray.intersectObjects(ground, false)[0]?.point.y ?? null;
  }
  document.querySelector('button').addEventListener('click', () => {
    reset();
    canvas.focus();
  });
  addEventListener('keydown', (event) => {
    if (!directions.has(event.code) || event.altKey || event.ctrlKey || event.metaKey) return;
    keys.add(event.code);
    route = [];
    event.preventDefault();
  });
  addEventListener('keyup', (event) => keys.delete(event.code));
  addEventListener('blur', () => { keys.clear(); drag = undefined; });
  canvas.addEventListener('pointerdown', (event) => {
    if (drag || event.button !== 0) return;
    canvas.setPointerCapture(event.pointerId);
    drag = { id: event.pointerId, x: event.clientX, y: event.clientY, moved: false };
  });
  canvas.addEventListener('pointermove', (event) => {
    if (event.pointerId !== drag?.id) return;
    const dx = event.clientX - drag.x;
    const dy = event.clientY - drag.y;
    if (!drag.moved && Math.hypot(dx, dy) < 6) return;
    drag = { id: drag.id, x: event.clientX, y: event.clientY, moved: true };
    yaw -= dx * 0.009;
    pitch = T.MathUtils.clamp(pitch + dy * 0.006, 0.23, 1.13);
  });
  canvas.addEventListener('pointerup', (event) => {
    if (event.pointerId !== drag?.id) return;
    if (!drag.moved) {
      ray.setFromCamera(new T.Vector2(2 * event.clientX / canvas.clientWidth - 1, 1 - 2 * event.clientY / canvas.clientHeight), camera);
      const hit = ray.intersectObjects(ground, false)[0];
      route = hit ? nav.path(position.x, position.z, hit.point.x, hit.point.z) : [];
    }
    drag = undefined;
  });
  canvas.addEventListener('lostpointercapture', () => { drag = undefined; });

  function tryStep(x, z) {
    if (data.obstacles.some(([bx, bz, radius]) => Math.hypot(x - bx, z - bz) < radius)) return;
    const next = groundStep(position, x, z, nav, cast, data.maxStep);
    if (next) position.set(next.x, next.y, next.z);
  }
  function move(dx, dz) {
    if (dx) tryStep(position.x + dx, position.z);
    if (dz) tryStep(position.x, position.z + dz);
  }
  const aim = new T.Vector3();
  const arm = new T.Vector3();
  function follow() {
    aim.copy(position);
    aim.y += 0.85;
    arm.set(Math.sin(yaw) * Math.cos(pitch), Math.sin(pitch), Math.cos(yaw) * Math.cos(pitch));
    const distance = 6.8;
    ray.set(aim, arm);
    const obstacle = ray.intersectObjects(blockers, false)[0];
    const clear = obstacle ? T.MathUtils.clamp(obstacle.distance - 0.35, 0.15, distance) : distance;
    camera.position.copy(aim).addScaledVector(arm, clear);
    camera.lookAt(aim);
  }
  const measure = new URLSearchParams(location.search).has('qa');
  const connectedCells = data.levels.filter((value) => value !== null).length;
  let previous = performance.now();
  const frameTimes = [];
  let capture;
  function frame(now) {
    const milliseconds = now - previous;
    const dt = Math.min(0.045, milliseconds / 1000);
    previous = now;
    const forward = Number(keys.has('KeyW') || keys.has('ArrowUp')) - Number(keys.has('KeyS') || keys.has('ArrowDown'));
    const right = Number(keys.has('KeyD') || keys.has('ArrowRight')) - Number(keys.has('KeyA') || keys.has('ArrowLeft'));
    if (forward || right) {
      const step = 3.0 * dt / Math.hypot(forward, right);
      move((right * Math.cos(yaw) - forward * Math.sin(yaw)) * step, (-right * Math.sin(yaw) - forward * Math.cos(yaw)) * step);
    } else if (route.length) {
      const [x, z] = route[0];
      const dx = x - position.x;
      const dz = z - position.z;
      const distance = Math.hypot(dx, dz);
      if (distance < 0.012) route.shift();
      else {
        const factor = Math.min(1, dt * 3.0 / distance);
        move(dx * factor, dz * factor);
      }
    }
    follow();
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    if (camera.aspect !== width / height) {
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    }
    updateSunset(camera, now);
    renderer.render(scene, camera);
    if (capture) {
      capture(canvas.toDataURL('image/png'));
      capture = undefined;
    }
    if (measure) {
      if (frameTimes.length >= 180) frameTimes.shift();
      frameTimes.push(milliseconds);
      window.cliffQA = { position: position.toArray(), yaw, camera: camera.position.toArray(),
        connectedCells, remainingWaypoints: route.length, groundHeight: cast(position.x, position.z),
        drawCalls: renderer.info.render.calls, triangles: renderer.info.render.triangles, frameTimes };
    }
    requestAnimationFrame(frame);
  }
  if (measure) {
    window.cliffCapture = () => new Promise((resolve) => { capture = resolve; });
    window.cliffProject = (coordinates) => {
      const point = new T.Vector3().fromArray(coordinates).project(camera);
      return [(point.x + 1) * canvas.clientWidth / 2, (1 - point.y) * canvas.clientHeight / 2];
    };
  }
  reset();
  status.textContent = '試験版　・　夕景の見晴らしへ';
  requestAnimationFrame(frame);
}

play().catch((error) => {
  status.textContent = '試遊シーンを読み込めませんでした';
  console.error(error);
});
