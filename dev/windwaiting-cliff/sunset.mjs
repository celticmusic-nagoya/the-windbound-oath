import * as T from 'three';

const vertex = `
varying vec3 point;
void main() {
  vec4 world = modelMatrix * vec4(position, 1.);
  point = world.xyz;
  gl_Position = projectionMatrix * viewMatrix * world;
}
`;

export function sunset(scene, sea, sun) {
  const direction = sun.clone().normalize();
  const sky = new T.Mesh(new T.SphereGeometry(125, 40, 22), new T.ShaderMaterial({
    side: T.BackSide,
    depthWrite: false,
    uniforms: { sun: { value: direction } },
    vertexShader: vertex,
    fragmentShader: `
      uniform vec3 sun;
      varying vec3 point;
      void main() {
        vec3 d = normalize(point - cameraPosition);
        float s = max(dot(d, sun), 0.);
        float up = clamp(d.y, 0., 1.);
        vec3 base = mix(vec3(.62,.24,.17), vec3(.045,.104,.31), smoothstep(0., .68, up));
        base += vec3(.48,.20,.031) * pow(s, 18.);
        float rays = smoothstep(.99989, .99995, s);
        gl_FragColor = vec4(base + rays * vec3(3., 1.35, .36), 1.);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }
    `,
  }));
  sky.renderOrder = -1;
  scene.add(sky);
  if (sea?.isMesh) {
    sea.material = new T.ShaderMaterial({
      uniforms: { sun: { value: direction }, time: { value: 0 } },
      vertexShader: vertex,
      fragmentShader: `
        uniform vec3 sun;
        uniform float time;
        varying vec3 point;
        void main() {
          vec3 d = normalize(point - cameraPosition);
          float u = point.x * .6 + point.z * .35;
          float v = point.z * 4.7 - point.x * 1.9;
          float ripple = sin(v + sin(u) * 1.6 + time * .75) * .5 +
                         sin(v * 1.64 - u * 2.8 - time * .54) * .31;
          vec3 mirror = vec3(d.x, -d.y, d.z);
          float alignment = max(dot(normalize(d.xz), normalize(sun.xz)), 0.);
          float shine = pow(alignment, 95.) * smoothstep(-.25, .79, ripple) *
                        (.28 + .72 * pow(max(dot(mirror, sun), 0.), 47.));
          float horizon = pow(1. - abs(d.y), 12.);
          float detail = 1. - smoothstep(45., 105., distance(point, cameraPosition));
          vec3 tint = mix(vec3(.05,.118,.168), vec3(.168,.17,.24), horizon);
          tint += vec3(.017,.031,.035) * ripple * detail + vec3(1.2,.46,.08) * shine;
          gl_FragColor = vec4(tint, 1.);
          #include <tonemapping_fragment>
          #include <colorspace_fragment>
        }
      `,
    });
  }
  return (camera, now) => {
    sky.position.copy(camera.position);
    if (sea?.material.uniforms) sea.material.uniforms.time.value = now * 0.001;
  };
}
