import * as T from 'three';

const vertex = `
varying vec3 point;
void main() {
  vec4 world = modelMatrix * vec4(position, 1.);
  point = world.xyz;
  gl_Position = projectionMatrix * viewMatrix * world;
}
`;

// Provisional non-traversable offshore silhouettes. No world placement claim.
function distantCoast(scene) {
  const positions=[], indices=[], colors=[];
  const islands=[
    {x:-49,z:47,w:24,d:9,h:5.8,phase:1.2},
    {x:-8,z:78,w:31,d:12,h:7.2,phase:3.7},
    {x:39,z:65,w:18,d:8,h:4.6,phase:5.1}
  ];
  const n=48, m=8;
  for (const island of islands) {
    const start=positions.length/3;
    for (let j=0;j<=m;j++) for(let i=0;i<=n;i++){
      const u=2*i/n-1, v=2*j/m-1;
      const envelope=Math.max(0,1-u*u-v*v);
      const profile=.72+.17*Math.sin(u*9+island.phase)+.11*Math.cos(u*21+v*4);
      const y=-.18+island.h*Math.pow(envelope,.72)*profile;
      positions.push(island.x+u*island.w,y,island.z+v*island.d);
      const coastal=new T.Color(0x536374);
      const ridge=new T.Color(0x77818a);
      coastal.lerp(ridge,T.MathUtils.clamp(y/island.h,0,1));
      colors.push(coastal.r,coastal.g,coastal.b);
      if(i<n&&j<m){const k=start+j*(n+1)+i;indices.push(k,k+n+1,k+1,k+1,k+n+1,k+n+2);}
    }
  }
  const geometry=new T.BufferGeometry();
  geometry.setAttribute('position',new T.Float32BufferAttribute(positions,3));
  geometry.setIndex(indices);
  geometry.setAttribute('color',new T.Float32BufferAttribute(colors,3));
  geometry.computeVertexNormals();
  const material=new T.MeshBasicMaterial({vertexColors:true});
  const mesh=new T.Mesh(geometry,material);
  mesh.name='PROVISIONAL distant coastal silhouettes';
  scene.add(mesh);
}

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
  if (new URLSearchParams(location.search).get('vista') === '1') distantCoast(scene);
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
