<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const props = defineProps({
  selections: { type: Object, required: true },
  isDark: { type: Boolean, default: false }
});

const canvasContainer = ref(null);
const isModelLoading = ref(true);
const loadProgress = ref(0);
const webglError = ref(false);

let renderer, scene, camera, controls, animationId;
const dracoLoader = new DRACOLoader();
dracoLoader.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.7/');
const loader = new GLTFLoader();
loader.setDRACOLoader(dracoLoader);

// Material name -> category mapping (all 70 materials classified)
// Only "5643" and "78969" are left as case/structure
const materialToCategory = {
  // RAM
  'RAM_cAge.006': 'ram', 'RAM_moth.001': 'ram', 'RAM_cAge.001': 'ram',
  'RAM_Gols.001': 'ram', 'Rgb_Lights_RAM': 'ram', 'RAM_cAge.004': 'ram',
  'Corsair.002': 'ram', 'Platinum_RGB.003': 'ram',
  // GPU
  'Rog.003': 'gpu', '5643_4': 'gpu',
  // Motherboard
  'material': 'motherboard', 'material_0': 'motherboard', 'material_13': 'motherboard',
  '5643_2': 'motherboard', '354648': 'motherboard', '2345267': 'motherboard',
  '5436487': 'motherboard', '54737456': 'motherboard', 'Material.003': 'motherboard',
  'Material.005': 'motherboard', '5643_1': 'motherboard', '5643_3': 'motherboard',
  '2345784623': 'motherboard', 'material_34': 'motherboard', 'Material.023': 'motherboard',
  'Material.024': 'motherboard', '4534595': 'motherboard', 'material_43': 'motherboard',
  'Material.006': 'motherboard', 'Material.007': 'motherboard',
  '625341234': 'motherboard', '5643_0': 'motherboard', '63542': 'motherboard',
  // Fan
  '345895': 'fan', '.001': 'fan', 'Material.008': 'fan', '3764487': 'fan',
  '3245637': 'fan', '38579': 'fan', '234964': 'fan', '3546487': 'fan',
  'material_60': 'fan', '65433564': 'fan', '43576453': 'fan',
  '85678': 'fan', '453646798': 'fan', '3452065': 'fan', '1234': 'fan',
  '345.003': 'fan', '34753': 'fan', '254638': 'fan',
  '264524': 'fan', '423526': 'fan', '435273': 'fan',
  '1234512': 'fan', '23453795': 'fan', '25634784': 'fan',
  '456783': 'fan',
  // Cable
  '56234': 'cable', '23458': 'cable', '.016': 'cable', '.019': 'cable',
  '234573': 'cable', 'material_15': 'cable', '65433': 'cable', '26345': 'cable',
  'material_63': 'cable', '1234628': 'cable',
};

// category -> [mesh objects]
const categoryMeshes = {};
let modelLoaded = false;

const initScene = () => {
  const container = canvasContainer.value;
  if (!container) return;

  // WebGL desteğini kontrol et
  const testCanvas = document.createElement('canvas');
  const gl = testCanvas.getContext('webgl2') || testCanvas.getContext('webgl') || testCanvas.getContext('experimental-webgl');
  if (!gl) {
    webglError.value = true;
    isModelLoading.value = false;
    return;
  }

  try {
    renderer = new THREE.WebGLRenderer({ antialias: true });
  } catch (e) {
    webglError.value = true;
    isModelLoading.value = false;
    return;
  }
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.8;
  container.appendChild(renderer.domElement);

  scene = new THREE.Scene();
  updateBackground();

  camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.001, 50000);

  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.update();

  // Lights
  scene.add(new THREE.AmbientLight(0xffffff, 1.5));
  const d1 = new THREE.DirectionalLight(0xffffff, 1.0);
  d1.position.set(5, 10, 5);
  scene.add(d1);
  const d2 = new THREE.DirectionalLight(0xffffff, 0.6);
  d2.position.set(-5, 5, -3);
  scene.add(d2);
  const d3 = new THREE.DirectionalLight(0xffffff, 0.5);
  d3.position.set(0, 3, 8);
  scene.add(d3);

  loadGamingComputer();

  const animate = () => {
    animationId = requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
  };
  animate();

  const resizeObserver = new ResizeObserver(() => {
    if (!container || !renderer) return;
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
  });
  resizeObserver.observe(container);
};

const updateBackground = () => {
  if (!scene) return;
  scene.background = new THREE.Color(props.isDark ? '#1a1d24' : '#f0ede6');
};

const classifyMesh = (mesh) => {
  const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
  for (const mat of mats) {
    if (mat && mat.name && materialToCategory[mat.name]) {
      return materialToCategory[mat.name];
    }
  }
  return null; // unclassified = case structure (5643, 78969)
};

const loadGamingComputer = () => {
  loader.load(
    '/models/gaming_computer_opt.glb',
    (gltf) => {
      const model = gltf.scene;
      scene.add(model);

      for (const cat of ['motherboard', 'gpu', 'ram', 'fan', 'cable', 'case']) {
        categoryMeshes[cat] = [];
      }

      // Classify every mesh
      model.traverse((child) => {
        if (child.isMesh) {
          const category = classifyMesh(child);
          if (category) {
            categoryMeshes[category].push(child);
          } else {
            categoryMeshes.case.push(child);
          }
        }
      });

      console.log('Mesh categories:', Object.fromEntries(
        Object.entries(categoryMeshes).map(([k, v]) => [k, v.length])
      ));

      // Hide all non-case meshes initially
      for (const [cat, meshes] of Object.entries(categoryMeshes)) {
        if (cat === 'case') continue;
        for (const mesh of meshes) {
          mesh.visible = false;
        }
      }

      // Fit camera (use full model bounds, then re-hide)
      fitCameraToModel(model);

      modelLoaded = true;
      isModelLoading.value = false;
    },
    (progress) => {
      if (progress.total > 0) {
        loadProgress.value = Math.round((progress.loaded / progress.total) * 100);
      }
    },
    (err) => {
      console.error('Model load error:', err);
      isModelLoading.value = false;
    }
  );
};

const fitCameraToModel = (model) => {
  // Show all temporarily for bounding box
  model.traverse((c) => { if (c.isMesh) c.visible = true; });

  const box = new THREE.Box3().setFromObject(model);
  const size = new THREE.Vector3();
  const center = new THREE.Vector3();
  box.getSize(size);
  box.getCenter(center);

  const maxDim = Math.max(size.x, size.y, size.z);
  const fov = camera.fov * (Math.PI / 180);
  let dist = (maxDim / 2) / Math.tan(fov / 2);
  dist *= 1.5;

  camera.position.set(
    center.x + dist * 0.6,
    center.y + dist * 0.4,
    center.z + dist * 0.8
  );
  controls.target.copy(center);
  camera.near = maxDim * 0.001;
  camera.far = maxDim * 100;
  camera.updateProjectionMatrix();
  controls.update();

  // Re-hide non-case (all selections are null at start)
  for (const [cat, meshes] of Object.entries(categoryMeshes)) {
    if (cat === 'case') continue;
    for (const mesh of meshes) {
      mesh.visible = false;
    }
  }

  // Grid
  scene.children.forEach(c => { if (c.isGridHelper) scene.remove(c); });
  const grid = new THREE.GridHelper(maxDim * 3, 30, 0x888888, 0x555555);
  grid.material.opacity = 0.15;
  grid.material.transparent = true;
  grid.position.y = box.min.y;
  scene.add(grid);
};

const syncVisibility = () => {
  if (!modelLoaded) return;

  const show = (cat, selected) => {
    const meshes = categoryMeshes[cat] || [];
    meshes.forEach(m => m.visible = selected);
  };

  show('motherboard', !!props.selections.motherboard);
  show('gpu', !!props.selections.gpu);
  show('ram', !!props.selections.ram);
  show('fan', !!props.selections.fan);
  show('cable', !!props.selections.psu || !!props.selections.cable);

  // Case always visible
  (categoryMeshes.case || []).forEach(m => m.visible = true);
};

watch(() => props.selections.motherboard, syncVisibility);
watch(() => props.selections.cpu, syncVisibility);
watch(() => props.selections.gpu, syncVisibility);
watch(() => props.selections.ram, syncVisibility);
watch(() => props.selections.fan, syncVisibility);
watch(() => props.selections.psu, syncVisibility);
watch(() => props.selections.cable, syncVisibility);
watch(() => props.isDark, updateBackground);

onMounted(initScene);

onUnmounted(() => {
  if (animationId) cancelAnimationFrame(animationId);
  if (renderer) { renderer.dispose(); renderer.domElement.remove(); }
  if (controls) controls.dispose();
});
</script>

<template>
  <div class="pc-scene-wrapper">
    <div ref="canvasContainer" class="pc-scene"></div>
    <div v-if="webglError" class="loading-overlay center error-overlay">
      <span>3D görüntüleme kullanılamıyor. Tarayıcınızda donanım hızlandırmayı etkinleştirin.</span>
      <span class="error-hint">Chrome: Ayarlar → Sistem → "Donanım hızlandırmayı kullan"</span>
    </div>
    <div v-else-if="isModelLoading" class="loading-overlay center">
      <div class="loading-spinner large"></div>
      <span>Model yükleniyor...</span>
    </div>
    <div class="scene-controls-hint">
      Fare ile dondur, kaydir ve yakinlastir
    </div>
  </div>
</template>

<style scoped>
.pc-scene-wrapper { flex: 1; position: relative; min-height: 0; }
.pc-scene { width: 100%; height: 100%; }
.loading-overlay {
  position: absolute; display: flex; align-items: center; gap: 12px;
  background: var(--bg-card); border: 1px solid var(--border);
  padding: 16px 24px; border-radius: 16px; font-size: 0.95rem;
  color: var(--text-main); box-shadow: 0 4px 24px var(--shadow-md);
}
.loading-overlay.center { top: 50%; left: 50%; transform: translate(-50%, -50%); }
.error-overlay { flex-direction: column; text-align: center; max-width: 320px; }
.error-hint { font-size: 0.78rem; color: var(--text-muted); margin-top: 4px; }
.loading-spinner {
  border: 3px solid var(--border); border-top-color: var(--accent);
  border-radius: 50%; animation: spin 0.8s linear infinite;
}
.loading-spinner.large { width: 28px; height: 28px; }
@keyframes spin { to { transform: rotate(360deg); } }
.scene-controls-hint {
  position: absolute; bottom: 16px; left: 50%; transform: translateX(-50%);
  background: var(--bg-card); border: 1px solid var(--border);
  padding: 6px 16px; border-radius: 20px; font-size: 0.75rem;
  color: var(--text-muted); opacity: 0.8;
}
</style>
