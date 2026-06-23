import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Node name mappings from gaming_computer.glb analysis
// Each category maps to an array of node names in the GLB model

export const partNodeNames = {
  case: ["Cube.002_1","Plane_2","Plane.003_3","Plane.002_4","Cube.003_5","Cube.001_6","Cube.004_7","Cube.005_8","Cylinder_9","Plane.007_11","Plane.009_12","Plane.010_13","Plane.011_14","Plane.012_15","Plane.013_16","Plane.014_17","Cube.006_18","Cube.007_19","Cube.008_20","Cube.009_21","Cube.010_22","Cube.011_23","Cube.012_24","Cube.013_25","Plane.015_26","Plane.016_27","Plane.017_28","Plane.018_29","Plane.019_30","Plane.020_31","Plane.021_32","Plane.022_33","Plane.023_34","Plane.024_35","Plane.025_36","Plane.026_37","Plane.027_38","Plane.028_39","Plane.029_40","Plane.030_41","Plane.031_42","Plane.032_43","Plane.033_44","Plane.034_45","Plane.035_46","Plane.036_47","Plane.037_48","Plane.038_49","Plane.039_50","Plane.040_51","Plane.041_52","Plane.042_53","Cube.014_56","Plane.045_57","Plane.046_58","Plane.047_59","Plane.048_60","Cube.015_63","Plane.055_68","Cylinder.001_69","Cylinder.002_70","Plane.056_97","Plane.057_98","Plane.058_99","Plane.059_100","Cube.016_101","Plane.060_102","Plane.061_103","Plane.065_107","Plane.066_108","Plane.067_109","Plane.068_110","Cylinder.029_111","Cylinder.030_112","Cube.017_147","Cylinder.031_148","Cylinder.032_149","Cylinder.033_150","Cylinder.034_151","Cube.018_152","Cylinder.035_153","Cylinder.036_154","Cylinder.037_155","Cylinder.038_156","Cube.019_157","Cylinder.039_158","Cylinder.040_159","Cylinder.041_160","Cylinder.042_161","Cube.020_162","Cylinder.043_163","Cylinder.044_164","Cylinder.045_165","Cylinder.046_166","Cube.021_167","Cube.022_168","Cube.026_184","Cube.027_185","Cube.029_187","Cube.030_188","Cylinder.057_190","Cube.032_191","Cube.033_192","Cube.034_193","Cylinder.058_194","Cylinder.059_195","Cylinder.060_196","Cylinder.061_197","Circle_198","Cylinder.062_200","Cylinder.063_201","Cylinder.064_202","Cube.036_203","Cube.037_204","Cube.038_205","Cube.039_206","Cube.040_207","Cylinder.065_208","Cylinder.066_209","Cylinder.067_210","Cylinder.068_211","Cube.041_212","Cylinder.069_213","Cylinder.070_214","Cylinder.071_215","Cylinder.072_216","Cube.042_217","Cylinder.073_218","Cylinder.074_219","Cylinder.075_220","Cylinder.076_221","Cube.043_222","Cube.044_223","Cube.045_224","Cube.046_225","Cube.047_226","Cube.048_227","Cube.049_228","Cube.050_229","Cube.051_230","Cube.052_231","Cube.053_232","Cylinder.077_233","Cylinder.078_234","Cylinder.079_235","Cylinder.080_236","Cylinder.081_237","Cylinder.082_238","Cylinder.083_239","Cube.054_240","Cube.055_241","Cube.056_242","Cube.057_243","Cube.058_244","Cube.059_245","Cube.060_246","Cube.061_247","Cube.062_248","Cube.063_249","Cube.064_250","Cube.065_251","Cube.066_252","Cube.067_253","Cube.068_254","Cube.069_255","Cube.070_256","Cube.071_257","Cube.072_258","Cube.073_259","Cube.074_260","Cube.075_261","Cube.076_262","Cube.077_263","Cube.078_264","Cube.079_265","Cube.080_266","Cube.081_267","Cube.082_268","Cube.083_269","Cube.084_270","Cube.085_271","Cube.086_272","Cube.087_273","Cube.088_274","Cube.089_275","Cube.090_276","Cube.091_277","Cube.092_278","Cube.093_279","Cube.094_280","Cube.095_281","Cube.096_282","Cube.097_283","Cube.098_284","Cube.099_285","Cube.100_286","Cube.101_287","Cube.102_288","Cube.103_289","Cube.104_290","Cube.105_291","Cube.106_292","Cube.107_293","Cube.108_294","Cube.109_295","Cube.110_296","Cube.111_297","Cube.112_298","Cube.113_299","Cube.114_300","Cube.115_301","Cube.116_302","Cube.117_303","Cube.118_304","Cube.119_305","Cube.120_306","Cube.121_307","Cube.122_308","Cube.123_309","Cube.124_310","Cube.125_311","Cube.126_312","Cube.127_313","Cube.128_314","Cube.129_315","Cube.130_316","Cube.131_317","Cube.132_318","Cube.133_319","Cube.134_320","Cube.135_321","Cube.136_322","Cube.137_323","Curve.029_354","Curve.030_355","Curve.031_356","Curve.032_357","Curve.033_358","Curve.034_359","Curve.035_360","Curve.036_361","Curve.038_362","Curve.039_363","Plane.112_388","Plane.113_396","Plane.128_428","Plane.129_446","Cylinder.131_479","Cylinder.132_480","Cylinder.134_484","Plane.172_485","Plane.173_489","Circle.002_490","Cylinder.135_493","Plane.175_494","Plane.176_499","Circle.004_500","Cylinder.136_503","Plane.178_504","Plane.179_509","Circle.006_510","BezierCurve_511","BezierCurve.001_512","Cylinder.137_513","Cylinder.138_514","Cylinder.139_515","Cylinder.140_516","Cylinder.141_517","Cylinder.142_518","Cylinder.143_519","Cylinder.144_520","Cylinder.145_521","Cylinder.146_522","Cylinder.147_523","Cylinder.148_524","Cylinder.149_525","Cylinder.150_526","Cylinder.151_527","Plane.181_528","Circle.008_531","Cylinder.152_532","Plane.184_533","Circle.010_537","Cylinder.153_538","Plane.187_539","Circle.012_543","Cylinder.166_557","Plane.190_558","Plane.191_563","Circle.014_564","Cylinder.167_566","Plane.193_567","Plane.194_572","Circle.016_573","Cylinder.168_576","Plane.196_577","Plane.197_582","Circle.018_583","Cylinder.169_585","Cylinder.170_586","Cylinder.171_587","Cylinder.172_588","Cylinder.173_589","Cylinder.174_590","Cylinder.175_591","Cylinder.176_592","Cylinder.177_593","Cylinder.178_594","Cylinder.179_595","Cylinder.180_596","Cylinder.192_603","Cylinder.193_604","Cylinder.194_605","Cylinder.195_606","Cylinder.196_607","Cylinder.187_608","Plane.188_609","Cylinder.197_611","Cylinder.198_613","Cylinder.199_614","Cylinder.200_615","Plane.145_624","Plane.148_628","Plane.149_629","Plane.152_638","Plane.153_639","Plane.154_640","Plane.155_641","Plane.156_642","Plane.157_643","Plane.158_644","Plane.159_645","Plane.160_646","Plane.161_647","Curve.073_661","Curve.076_663","Curve.077_664","Curve.078_665","Curve.079_666","Curve.080_667","Curve.081_668","Curve.122_812","Cube.307_816","Cube.321_831","Cube.322_832","Cube.286_847","BezierCurve.002_848","BezierCurve.003_849","Cube.287_850","Cube.288_851","Cube.289_852","BezierCurve.011_855","Cube.291_856","Cube.292_857","BezierCurve.013_859","Plane.004_861","Plane.006_862","Plane.008_863","Cube.280_864","BezierCurve.014_865","Cube.293_875","Cube.294_876","Cube.295_877","BezierCurve.016_885","BezierCurve.017_886","BezierCurve.018_887","BezierCurve.019_888","BezierCurve.020_889","BezierCurve.021_890","Plane.186_891","Cube.257_892","Cube.261_893","Cube.265_894","Cube.298_895","Cube.303_901"],
  motherboard: ["Cube_0","Plane.005_10","Plane.043_54","Plane.044_55","Plane.049_61","Plane.050_62","Plane.051_64","Plane.052_65","Plane.053_66","Plane.054_67","Plane.062_104","Plane.063_105","Plane.064_106","Plane.069_113","Plane.070_114","Plane.071_115","Plane.072_116","Plane.073_117","Plane.074_118","Plane.075_119","Plane.076_120","Plane.077_121","Plane.078_122","Plane.079_123","Plane.080_124","Plane.081_125","Plane.082_126","Plane.083_127","Plane.084_128","Plane.085_129","Plane.086_130","Plane.087_131","Plane.088_132","Plane.089_133","Plane.090_134","Plane.091_135","Plane.092_136","Plane.093_137","Plane.094_138","Plane.095_139","Plane.096_140","Plane.097_141","Plane.098_142","Plane.099_143","Plane.100_144","Plane.101_145","Plane.102_146","Plane.104_170","Cube.028_186","Cube.031_189","Curve_324","Curve.001_325","Curve.002_326","Curve.003_327","Curve.004_328","Curve.005_329","Curve.006_330","Curve.007_331","Curve.008_332","Curve.009_333","Curve.010_334","Curve.011_335","Curve.012_336","Curve.013_337","Curve.014_338","Curve.015_339","Curve.016_340","Curve.017_341","Curve.018_342","Curve.019_343","Curve.020_344","Curve.021_345","Curve.022_346","Curve.023_347","Curve.024_348","Curve.025_349","Curve.026_350","Curve.027_351","Curve.028_352","Text_353","Plane.107_366","Plane.118_401","Plane.123_423","Plane.134_451","Curve.047_464","Curve.044_465","Cube.242_466","Cylinder.133_481","Circle.001_483","Circle.003_492","Circle.005_502","Circle.013_556","Circle.015_565","Circle.017_575","Plane.200_597","Plane.141_619","Plane.142_620","Cylinder.096_627","Plane.150_630","Plane.151_633","BezierCurve.004_799","BezierCurve.005_800","BezierCurve.006_801","BezierCurve.007_802","BezierCurve.008_803","BezierCurve.009_804","Curve.132_813","Plane.189_867","Plane.192_874","BezierCurve.027_902","BezierCurve.028_903","BezierCurve.029_904","BezierCurve.030_905","BezierCurve.031_906"],
  gpu: ["Curve.083_686","Curve.085_688"],
  ram: ["Plane.105_364","Plane.106_365","Plane.108_367","Plane.109_369","Text.001_370","Plane.110_371","Plane.111_372","Curve.037_373","Curve.040_374","Curve.041_375","Curve.042_376","Text.002_377","Text.003_378","Text.004_379","Curve.043_381","Curve.045_382","Curve.046_383","Curve.048_384","Text.005_385","Text.006_386","Text.007_387","Text.008_389","Text.009_390","Text.010_391","Text.011_392","Text.012_393","Text.013_394","Text.014_395","Plane.114_397","Plane.115_398","Plane.116_399","Plane.117_400","Plane.119_402","Plane.120_403","Curve.049_405","Curve.050_406","Curve.051_407","Curve.052_408","Curve.053_409","Curve.054_410","Curve.055_411","Curve.056_412","Text.015_414","Text.016_415","Text.017_416","Text.018_417","Text.019_418","Text.020_419","Text.021_420","Plane.121_421","Plane.122_422","Plane.124_424","Plane.125_425","Plane.126_426","Plane.127_427","Curve.057_430","Curve.058_431","Curve.059_432","Curve.060_433","Curve.061_434","Curve.062_435","Curve.063_436","Curve.064_437","Text.022_439","Text.023_440","Text.024_441","Text.025_442","Text.026_443","Text.027_444","Text.028_445","Plane.130_447","Plane.131_448","Plane.132_449","Plane.133_450","Plane.135_452","Plane.136_453","Curve.065_455","Curve.066_456","Curve.067_457","Curve.068_458","Curve.069_459","Curve.070_460","Curve.071_461","Curve.072_462"],
  fan: ["Cylinder.003_71","Cylinder.004_72","Cylinder.005_73","Cylinder.006_74","Cylinder.007_75","Cylinder.008_76","Cylinder.009_77","Cylinder.010_78","Cylinder.011_79","Cylinder.012_80","Cylinder.013_81","Cylinder.014_82","Cylinder.015_83","Cylinder.016_84","Cylinder.017_85","Cylinder.018_86","Cylinder.019_87","Cylinder.020_88","Cylinder.021_89","Cylinder.022_90","Cylinder.023_91","Cylinder.024_92","Cylinder.025_93","Cylinder.026_94","Cylinder.027_95","Cylinder.028_96","Cylinder.047_173","Cylinder.048_174","Cylinder.049_175","Cylinder.050_176","Cylinder.051_177","Cylinder.052_178","Cylinder.053_179","Cylinder.054_180","Cylinder.055_181","Cylinder.056_182","Cube.035_199","Cylinder.119_467","Cylinder.120_468","Cylinder.121_469","Cylinder.122_470","Cylinder.123_471","Cylinder.124_472","Cylinder.125_473","Cylinder.126_474","Cylinder.127_475","Cylinder.128_476","Cylinder.129_477","Cylinder.130_478","Plane.140_482","Cube.243_486","Cube.245_487","Cube.246_488","Plane.174_491","Cube.247_495","Cube.248_496","Cube.249_497","Cube.250_498","Plane.177_501","Cube.251_505","Cube.252_506","Cube.253_507","Cube.254_508","Cube.255_529","Cube.258_530","Cube.259_534","Cube.260_535","Cube.262_536","Cube.263_540","Cube.264_541","Cube.266_542","Cylinder.154_544","Cylinder.155_545","Cylinder.156_546","Cylinder.157_547","Cylinder.158_548","Cylinder.159_549","Cylinder.160_550","Cylinder.161_551","Cylinder.162_552","Cylinder.163_553","Cylinder.164_554","Cylinder.165_555","Cube.267_559","Cube.268_560","Cube.269_561","Cube.270_562","Cube.271_568","Cube.272_569","Cube.273_570","Cube.274_571","Plane.195_574","Cube.275_578","Cube.276_579","Cube.277_580","Cube.278_581","Plane.202_598","Cube.256_599","Cube.296_600","Cube.297_601","Cube.244_602","Plane.203_610","Cube.299_612","Cube.300_616","Cube.301_617","Cube.302_618","Cylinder.103_669","Cylinder.104_670","Cylinder.105_671","Cylinder.106_672","Curve.084_687","Cylinder.117_703","Cylinder.118_704","Cube.150_707","Cube.151_708","Cube.152_709","Cube.153_710","Cube.154_711","Cube.155_712","Cube.156_713","Cube.157_714","Cube.158_715","Cube.159_716","Cube.160_717","Cube.161_718","Cube.162_719","Cube.163_720","Cube.164_721","Cube.165_722","Cube.166_723","Cube.167_724","Cube.168_725","Cube.169_726","Cube.170_727","Cube.171_728","Cube.172_729","Cube.173_730","Cube.174_731","Cube.175_732","Cube.176_733","Cube.177_734","Cube.178_735","Cube.179_736","Cube.180_737","Cube.181_738","Cube.182_739","Cube.183_740","Cube.184_741","Cube.185_742","Cube.186_743","Cube.187_744","Cube.188_745","Cube.189_746","Cube.190_747","Cube.191_748","Cube.192_749","Cube.193_750","Cube.194_751","Cube.195_752","Cube.196_753","Cube.197_754","Cube.198_755","Cube.199_756","Cube.200_757","Cube.201_758","Cube.202_759","Cube.203_760","Cube.204_761","Cube.205_762","Cube.206_763","Cube.207_764","Cube.208_765","Cube.209_766","Cube.210_767","Cube.211_768","Cube.212_769","Cube.213_770","Cube.214_771","Cube.215_772","Cube.216_773","Cube.217_774","Cube.218_775","Cube.219_776","Cube.220_777","Cube.221_778","Cube.222_779","Cube.223_780","Cube.224_781","Cube.225_782","Cube.226_783","Cube.227_784","Cube.228_785","Cube.229_786","Cube.230_787","Cube.231_788","Cube.232_789","Cube.233_790","Cube.234_791","Cube.235_792","Cube.236_793","Cube.237_794","Cube.238_795","Cube.239_796","Cube.240_797","Curve.099_805","Curve.100_806","Curve.101_807","Curve.102_808","Curve.103_809","Curve.104_810","Curve.105_811","Cube.306_817","Cube.308_818","Cube.309_819","Cube.310_820","Cube.311_821","Cube.312_822","Cube.313_823","Cube.314_824","Cube.315_825","Cube.316_826","Cube.317_827","Cube.318_828","Cube.319_829","Cube.320_830","Cylinder.188_878","Cylinder.189_879","Cylinder.190_880","Cylinder.191_881"],
  cable: ["Cube.023_171","Cube.024_172","Cube.025_183","Cube.138_368","Cylinder.084_380","Cylinder.085_404","Cube.139_413","Cylinder.086_429","Cube.140_438","Cylinder.087_454","Cube.141_463","Plane.143_621","Plane.144_622","Cube.142_623","Plane.146_625","Plane.147_626","Cube.143_631","Cube.144_632","Cube.145_634","Cube.147_635","Cube.148_636","Cube.149_637","BezierCircle_648","BezierCircle.001_649","BezierCircle.002_650","BezierCircle.003_651","Sphere_652","Cylinder.097_653","Cylinder.098_654","Cylinder.099_655","Cylinder.100_656","Sphere.001_659","Sphere.002_660","Curve.075_662","Cylinder.107_673","Cylinder.108_674","Cylinder.109_675","Cylinder.110_676","Plane.162_683","Plane.163_684","Curve.082_685","Plane.164_695","Plane.165_696","Plane.166_697","Plane.167_698","Plane.168_701","Plane.169_702","Plane.170_705","Plane.171_706","Cube.304_814","Cube.305_815","Cube.146_841","Curve.074_842","Cube.282_843","Cube.283_844","Cube.284_845","Cube.285_846","Cube.290_853","BezierCurve.010_854","BezierCurve.012_858","Cube.279_860","BezierCurve.015_866","Cylinder.181_868","Cylinder.182_869","Cylinder.183_870","Cylinder.184_871","Cylinder.185_872","Cylinder.186_873","Plane.182_882","Plane.183_883","Plane.185_884"],
  unknown: ["Plane.103_169","Cube.281_584","Cylinder.101_657","Cylinder.102_658","Cylinder.111_677","Cylinder.112_678","Cylinder.113_679","Cylinder.114_680","Cylinder.115_681","Cylinder.116_682","Curve.086_689","Curve.087_690","Curve.088_691","Curve.089_692","Curve.090_693","Curve.091_694","Text.029_699","Text.030_700","Cube.241_798","Cylinder.088_833","Cylinder.089_834","Cylinder.090_835","Cylinder.091_836","Cylinder.092_837","Cylinder.093_838","Cylinder.094_839","Cylinder.095_840"]
};

// Kategori etiketleri (frontend goruntuleme icin)
export const categoryLabels = {
  motherboard: 'Anakart',
  cpu: 'İşlemci (CPU)',
  gpu: 'Ekran Kartı (GPU)',
  ram: 'RAM',
  fan: 'Fan / Soğutma',
  psu: 'Güç Kaynağı (PSU)',
  cable: 'Kablolar',
  case: 'Kasa'
};

// Backend -> Frontend kategori eslesmesi
const backendToFrontendCategory = {
  cpu: 'cpu',
  gpu: 'gpu',
  motherboard: 'motherboard',
  memory: 'ram',
  psu: 'psu',
  case: 'case'
};

// Frontend -> Backend kategori eslesmesi (API cagrisi icin)
export const frontendToBackendCategory = {
  cpu: 'cpu',
  gpu: 'gpu',
  motherboard: 'motherboard',
  ram: 'memory',
  psu: 'psu',
  case: 'case'
};

// Backend'de karsiligi olmayan kategoriler (statik kalir)
const staticCategories = {
  fan: {
    label: 'Fan / Soğutma',
    options: [
      { id: 'fan-1', name: 'Corsair iCUE H150i Elite', price: 4500, specs: '360mm AIO, RGB' },
      { id: 'fan-2', name: 'Noctua NH-D15', price: 2800, specs: 'Çift kule, sessiz' },
      { id: 'fan-3', name: 'be quiet! Dark Rock Pro 4', price: 2200, specs: '250W TDP, sessiz' },
    ]
  },
  cable: {
    label: 'Kablolar',
    options: [
      { id: 'cable-1', name: 'CableMod Pro Kit', price: 1200, specs: 'Beyaz, sleeved' },
      { id: 'cable-2', name: 'Standart Kablo Seti', price: 0, specs: 'PSU ile birlikte gelir' },
    ]
  }
};

/**
 * Backend parcasini frontend formatina donusturur
 * Backend: {name, price, socket, cores, tdp, ...}
 * Frontend: {id, name, price, specs}
 */
function formatPartForFrontend(part, category, index) {
  const specsMap = {
    cpu: (p) => [
      p.cores ? `${p.cores} Çekirdek` : null,
      p.clock_speed || p.base_clock ? (p.clock_speed || p.base_clock) : null,
      p.tdp ? `${p.tdp}W TDP` : null,
      p.socket ? `Soket: ${p.socket}` : null,
    ],
    gpu: (p) => [
      p.vram ? `${p.vram}GB VRAM` : null,
      p.memory_type || null,
      p.tdp ? `${p.tdp}W` : null,
      p.chipset || null,
    ],
    motherboard: (p) => [
      p.socket ? `Soket: ${p.socket}` : null,
      p.chipset || null,
      p.form_factor || null,
      p.memory_type || null,
    ],
    memory: (p) => [
      p.capacity ? `${p.capacity}` : null,
      p.speed ? `${p.speed}` : null,
      p.type || p.memory_type || null,
      p.modules ? `${p.modules} modül` : null,
    ],
    psu: (p) => [
      p.wattage ? `${p.wattage}W` : null,
      p.efficiency || null,
      p.modular || null,
    ],
    case: (p) => [
      p.form_factor || null,
      p.color || null,
      p.type || null,
    ],
  };

  const specsFn = specsMap[category];
  let specsStr = '';
  if (specsFn) {
    specsStr = specsFn(part).filter(Boolean).join(', ');
  }
  // Eger specs bos kaldiysa, bilinen tum alanlari listele
  if (!specsStr) {
    const excludeKeys = ['name', 'price', '_id', 'category'];
    const entries = Object.entries(part)
      .filter(([k, v]) => !excludeKeys.includes(k) && v != null && v !== '')
      .slice(0, 4);
    specsStr = entries.map(([, v]) => String(v)).join(', ');
  }

  return {
    id: `${category}-api-${index}`,
    name: part.name,
    price: part.price || 0,
    specs: specsStr,
    _raw: part // Backend'in ham verisini sakla (uyumluluk kontrolu icin)
  };
}

/**
 * Backend API'den tum kategorilerin parcalarini ceker.
 * Donen format: { motherboard: { label, options: [...] }, cpu: { ... }, ... }
 */
export async function fetchParts() {
  const backendCategories = ['cpu', 'gpu', 'motherboard', 'memory', 'psu', 'case'];

  const requests = backendCategories.map(cat =>
    axios.get(`${API_BASE_URL}/pc-builder/parts/${cat}`, { timeout: 30000 })
      .then(res => ({ category: cat, data: res.data }))
      .catch(err => {
        console.warn(`[PC Builder] ${cat} kategorisi yüklenemedi:`, err.message);
        return { category: cat, data: null };
      })
  );

  const results = await Promise.all(requests);
  const parts = {};

  // Frontend kategorileri sirasiyla
  const categoryOrder = ['motherboard', 'cpu', 'gpu', 'ram', 'psu', 'case', 'fan', 'cable'];

  for (const cat of categoryOrder) {
    // Statik kategori mi?
    if (staticCategories[cat]) {
      parts[cat] = { ...staticCategories[cat] };
      continue;
    }

    // Backend karsiligi bul
    const backendCat = frontendToBackendCategory[cat];
    if (!backendCat) continue;

    const result = results.find(r => r.category === backendCat);
    if (result && result.data && result.data.parts && result.data.parts.length > 0) {
      parts[cat] = {
        label: categoryLabels[cat] || cat,
        options: result.data.parts.map((p, i) => formatPartForFrontend(p, backendCat, i))
      };
    } else {
      // Backend'den veri gelemediyse bos options
      parts[cat] = {
        label: categoryLabels[cat] || cat,
        options: []
      };
    }
  }

  return parts;
}

/**
 * Otomatik sistem toplama: butce ve kullanim senaryosuna gore en uygun parcalari sec
 */
export async function optimizeBuild(budget, usage) {
  const response = await axios.post(`${API_BASE_URL}/pc-builder/optimize`, {
    budget,
    usage
  }, { timeout: 30000 });
  return response.data;
}

/**
 * Secilen parcalarin uyumluluk kontrolu
 * parts: { cpu: {name, ...}, gpu: {name, ...}, ... } (backend formatinda)
 */
export async function checkCompatibility(parts) {
  const response = await axios.post(`${API_BASE_URL}/pc-builder/compatibility`, {
    parts
  }, { timeout: 30000 });
  return response.data;
}

// Maps sidebar category -> which node groups to show/hide
// CPU doesn't have its own mesh group, it appears with motherboard
export const categoryToNodeGroup = {
  motherboard: 'motherboard',
  cpu: null,           // CPU is visually part of motherboard in this model
  gpu: 'gpu',
  ram: 'ram',
  fan: 'fan',
  psu: 'cable',        // PSU cables represent PSU presence
  cable: 'cable',
  case: 'case',
};
