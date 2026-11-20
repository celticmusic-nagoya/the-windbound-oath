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
      float hash21(vec2 p) { return fract(sin(dot(p, vec2(127.1,311.7))) * 43758.5453); }
      float noise21(vec2 p) {
        vec2 i = floor(p), f = fract(p);
        f = f*f*(3.-2.*f);
        return mix(mix(hash21(i),hash21(i+vec2(1.,0.)),f.x),
                   mix(hash21(i+vec2(0.,1.)),hash21(i+vec2(1.)),f.x),f.y);
      }
      void main() {
        vec3 d = normalize(point - cameraPosition);
        float s = max(dot(d, sun), 0.);
        float up = clamp(d.y, 0., 1.);
        vec3 base = mix(vec3(.62,.24,.17), vec3(.045,.104,.31), smoothstep(0., .68, up));
        base += vec3(.48,.20,.031) * pow(s, 18.);
        // Static world-direction clouds preserve deterministic zero-wind captures.
        vec2 uv = d.xz / max(d.y + .22, .22);
        vec2 q = uv * vec2(1.8, 4.4);
        float n = .57*noise21(q) + .28*noise21(q*2.1+13.) + .15*noise21(q*4.3);
        float cloud = smoothstep(.48,.72,n) * smoothstep(.025,.14,d.y) * (1.-smoothstep(.65,.95,d.y));
        vec3 cloudTint = mix(vec3(.22,.18,.28),vec3(.95,.49,.24),pow(s,4.));
        base = mix(base, cloudTint, cloud*.75);
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
