const STEP_OVERVIEW = [
  "Prepare and convert your model (Blender/Object Builder, LODs, proxies, textures).",
  "Set up the mod folder (@MyWeaponMod/addons/your_addon) with model, textures, config.cpp, and model.cfg.",
  "Write config.cpp (CfgPatches, CfgWeapons, optional CfgMagazines/Ammo) with RHS dependencies.",
  "Define model.cfg animations (bolt, trigger, magazine hide) tied to animation sources.",
  "Wire modular attachments (optics, suppressor, lasers, bipod) using RHS slot classes.",
  "Verify animations, sounds, muzzle and ejection memory points in-game.",
  "Package as a PBO, sign it, and publish with RHS listed as a dependency.",
];

const DEFAULTS = {
  addon_prefix: "my_mod",
  addon_folder: "steyr_dmr_rhs",
  author: "YourName",
  weapon_class: "Steyr_DMR_762",
  weapon_name: "Steyr Arms DMR 7.62",
  model_filename: "Rifle_SteyrArms_DMR_762_v01.p3d",
  weapon_icon: "steyr_dmr_icon_ca.paa",
  optic_class: "Steyr_DMR_Scope",
  optic_name: "Steyr DMR Scope 6-24x",
  optic_model: "steyr_scope.p3d",
  optic_icon: "scope_icon_ca.paa",
  magazine_wells: "SR25",
  magazines: "rhs_mag_20Rnd_762x51_M118_special_Mag",
  required_addons: "A3_Weapons_F, rhsusf_main, rhs_c_weapons",
};

function quoteList(value) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean)
    .map((item) => `"${item}"`)
    .join(", ");
}

function buildConfig(ctx) {
  return `#include "basicDefines_A3.hpp"

class CfgPatches {
    class ${ctx.addon_folder} {
        author = "${ctx.author}";
        name = "${ctx.weapon_name} (RHS Mod)";
        url = "";
        units[] = {};
        weapons[] = {"${ctx.weapon_class}"};
        requiredVersion = 1.0;
        requiredAddons[] = {${quoteList(ctx.required_addons)}};
    };
};

class Mode_SemiAuto;
class Mode_FullAuto;
class SlotInfo;
class MuzzleSlot;
class CowsSlot;
class PointerSlot;
class UnderBarrelSlot;
class InventoryOpticsItem_Base_F;
class InventoryMuzzleItem_Base_F;
class InventoryUnderItem_Base_F;

class CfgWeapons {
    class Rifle_Base_F;
    class ${ctx.weapon_class}: Rifle_Base_F {
        author = "${ctx.author}";
        displayName = "${ctx.weapon_name}";
        descriptionShort = "DMR (7.62x51) using RHS attachments";
        model = "\\${ctx.addon_prefix}\\addons\\${ctx.addon_folder}\\${ctx.model_filename}";
        picture = "\\${ctx.addon_prefix}\\addons\\${ctx.addon_folder}\\data\\UI\\${ctx.weapon_icon}";
        modes[] = {"Single"};
        magazineWell[] = {${quoteList(ctx.magazine_wells)}};
        magazines[] = {${quoteList(ctx.magazines)}};
        reloadAction = "GestureReloadDMR";
        reloadTime = 0.1;
        recoil = "recoil_dmr_06";
        discreteDistance[] = {100, 200, 300, 400};
        maxZeroing = 1200;

        drySound[] = {"\\A3\\Sounds_F\\arsenal\\weapons\\LongRangeRifles\\DMR_06\\dry_DMR_06", db-5, 1, 10};
        reloadMagazineSound[] = {"\\A3\\Sounds_F\\arsenal\\weapons\\LongRangeRifles\\DMR_06\\reload_DMR_06", 1, 1, 10};

        class WeaponSlotsInfo: WeaponSlotsInfo {
            mass = 120;
            allowedSlots[] = {901};
            class MuzzleSlot: rhs_western_rifle_muzzle_slot {};
            class CowsSlot: rhs_western_rifle_scopes_slot_short {};
            class PointerSlot: rhs_western_rifle_laser_slot {};
            class UnderBarrelSlot: rhs_western_rifle_underbarrel_slot {};
        };

        handAnim[] = {"OFP2_ManSkeleton", "\\A3\\Weapons_F_Mark\\LongRangeRifles\\GM6\\handanim_GM6.rtm"};

        class Single: Mode_SemiAuto {
            sounds[] = {"StandardSound", "SilencedSound"};
            reloadTime = 0.1;
            dispersion = 0.00087;
        };
    };

    class ${ctx.optic_class}: ItemCore {
        scope = 2; scopeCurator = 2;
        displayName = "${ctx.optic_name}";
        model = "\\${ctx.addon_prefix}\\addons\\${ctx.addon_folder}\\${ctx.optic_model}";
        picture = "\\${ctx.addon_prefix}\\addons\\${ctx.addon_folder}\\data\\UI\\${ctx.optic_icon}";
        descriptionShort = "Optical sight for the ${ctx.weapon_name}";
        weaponInfoType = "RscWeaponZeroing";
        class ItemInfo: InventoryOpticsItem_Base_F {
            mass = 10;
            opticType = 2;
            optics = 1;
            modelOptics = "\\A3\\Weapons_F\\acc\\reticle_sniper_F.p3d";
            class OpticsModes {
                class Snip {
                    opticsZoomMin = 0.041; opticsZoomMax = 0.125; opticsZoomInit = 0.125;
                    distanceZoomMin = 100; distanceZoomMax = 1000;
                    memoryPointCamera = "eye";
                    opticsID = 1;
                    useModelOptics = 1;
                    opticsPPEffects[] = {"OpticsCHAbera1", "OpticsBlur1"};
                    opticsDisablePeripherialVision = 1;
                    visionMode[] = {"Normal"};
                };
            };
        };
    };
};
`;
}

function buildModelCfg(ctx) {
  const modelClass = ctx.model_filename.replace(/\.p3d$/i, "");
  return `class CfgSkeletons {
    class WeaponSkeleton {
        isDiscrete = 1;
        skeletonInherit = "";
        skeletonBones[] = {};
    };
};

class CfgModels {
    class Default {
        sections[] = {};
        skeletonName = "";
    };
    class ${modelClass}: Default {
        skeletonName = "WeaponSkeleton";
        sections[] = {"bolt", "magazine"};
        class Animations {
            class BoltMovement {
                source = "reload";
                selection = "bolt";
                axis = "bolt_axis";
                type = "translation";
                minValue = 0; maxValue = 1;
                offset0 = 0; offset1 = -0.1;
            };
            class MagHide {
                source = "reloadMagazine";
                selection = "magazine";
                type = "hide";
                minValue = 0; maxValue = 1;
            };
            class TriggerPull {
                source = "trigger";
                selection = "trigger";
                axis = "trigger_axis";
                type = "rotation";
                angle0 = 0; angle1 = -0.1;
            };
        };
    };
};
`;
}

function getFormData(form) {
  const data = new FormData(form);
  const ctx = { ...DEFAULTS };
  for (const [key, value] of data.entries()) {
    ctx[key] = value.toString();
  }
  return ctx;
}

async function readFileBytes(inputId) {
  const input = document.getElementById(inputId);
  if (!input || !input.files || input.files.length === 0) return null;
  const file = input.files[0];
  const buffer = await file.arrayBuffer();
  return { name: file.name, bytes: new Uint8Array(buffer) };
}

// --- Minimal ZIP (store) builder ------------------------------------------------------------
function crc32(buf) {
  const table = crc32.table || (crc32.table = (() => {
    const t = new Uint32Array(256);
    for (let i = 0; i < 256; i++) {
      let c = i;
      for (let k = 0; k < 8; k++) {
        c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
      }
      t[i] = c >>> 0;
    }
    return t;
  })());
  let crc = 0 ^ -1;
  for (let i = 0; i < buf.length; i++) {
    crc = (crc >>> 8) ^ table[(crc ^ buf[i]) & 0xff];
  }
  return (crc ^ -1) >>> 0;
}

function writeUint32(arr, offset, value) {
  arr[offset] = value & 0xff;
  arr[offset + 1] = (value >>> 8) & 0xff;
  arr[offset + 2] = (value >>> 16) & 0xff;
  arr[offset + 3] = (value >>> 24) & 0xff;
}

function writeUint16(arr, offset, value) {
  arr[offset] = value & 0xff;
  arr[offset + 1] = (value >>> 8) & 0xff;
}

function buildZip(files) {
  const encoder = new TextEncoder();
  const localParts = [];
  const centralParts = [];
  let offset = 0;

  for (const file of files) {
    const nameBytes = encoder.encode(file.path);
    const dataBytes = typeof file.content === "string" ? encoder.encode(file.content) : file.content;
    const crc = crc32(dataBytes);
    const local = new Uint8Array(30 + nameBytes.length);
    writeUint32(local, 0, 0x04034b50);
    writeUint16(local, 4, 20); // version needed
    writeUint16(local, 6, 0); // flags
    writeUint16(local, 8, 0); // store
    writeUint16(local, 10, 0); // mod time
    writeUint16(local, 12, 0); // mod date
    writeUint32(local, 14, crc);
    writeUint32(local, 18, dataBytes.length);
    writeUint32(local, 22, dataBytes.length);
    writeUint16(local, 26, nameBytes.length);
    writeUint16(local, 28, 0); // extra length
    local.set(nameBytes, 30);

    localParts.push(local, dataBytes);

    const central = new Uint8Array(46 + nameBytes.length);
    writeUint32(central, 0, 0x02014b50);
    writeUint16(central, 4, 20); // version made by
    writeUint16(central, 6, 20); // version needed
    writeUint16(central, 8, 0); // flags
    writeUint16(central, 10, 0); // compression
    writeUint16(central, 12, 0); // mod time
    writeUint16(central, 14, 0); // mod date
    writeUint32(central, 16, crc);
    writeUint32(central, 20, dataBytes.length);
    writeUint32(central, 24, dataBytes.length);
    writeUint16(central, 28, nameBytes.length);
    writeUint16(central, 30, 0); // extra
    writeUint16(central, 32, 0); // comment
    writeUint16(central, 34, 0); // disk number
    writeUint16(central, 36, 0); // internal attrs
    writeUint32(central, 38, 0); // external attrs
    writeUint32(central, 42, offset); // local header offset
    central.set(nameBytes, 46);

    centralParts.push(central);

    offset += local.length + dataBytes.length;
  }

  const centralSize = centralParts.reduce((sum, part) => sum + part.length, 0);
  const centralOffset = offset;

  const end = new Uint8Array(22);
  writeUint32(end, 0, 0x06054b50);
  writeUint16(end, 4, 0); // disk number
  writeUint16(end, 6, 0); // start disk
  writeUint16(end, 8, files.length);
  writeUint16(end, 10, files.length);
  writeUint32(end, 12, centralSize);
  writeUint32(end, 16, centralOffset);
  writeUint16(end, 20, 0); // comment length

  const blob = new Blob([...localParts, ...centralParts, end], { type: "application/zip" });
  return blob;
}

function renderList(id, items) {
  const el = document.getElementById(id);
  if (!el) return;
  el.innerHTML = "";
  for (const item of items) {
    const li = document.createElement("li");
    li.textContent = item;
    el.appendChild(li);
  }
}

function populateForm(form) {
  for (const [key, value] of Object.entries(DEFAULTS)) {
    const input = form.querySelector(`[name="${key}"]`);
    if (input) {
      input.value = value;
    }
  }
}

function handleSubmit(event) {
  event.preventDefault();
  const form = event.target;
  const ctx = getFormData(form);
  const basePath = `@MyWeaponMod/addons/${ctx.addon_folder}`;

  Promise.all([
    readFileBytes("model_file"),
    readFileBytes("optic_file"),
    readFileBytes("color_file"),
    readFileBytes("normal_file"),
    readFileBytes("roughness_file"),
    readFileBytes("metalness_file"),
    readFileBytes("ao_file"),
    readFileBytes("icon_weapon_file"),
    readFileBytes("icon_optic_file"),
  ]).then((uploads) => {
    const [model, optic, color, normal, roughness, metalness, ao, iconWeapon, iconOptic] = uploads;
    const resolvedIcons = {
      weapon: iconWeapon ? iconWeapon.name : ctx.weapon_icon,
      optic: iconOptic ? iconOptic.name : ctx.optic_icon,
    };
    const configCtx = { ...ctx, weapon_icon: resolvedIcons.weapon, optic_icon: resolvedIcons.optic };

    const files = [
      { path: `${basePath}/config.cpp`, content: buildConfig(configCtx) },
      { path: `${basePath}/model.cfg`, content: buildModelCfg(configCtx) },
      { path: `${basePath}/${ctx.model_filename}`, content: model ? model.bytes : new Uint8Array() },
      { path: `${basePath}/${ctx.optic_model}`, content: optic ? optic.bytes : new Uint8Array() },
      { path: `${basePath}/data/${color ? color.name : "rifle_dmr_co.paa"}`, content: color ? color.bytes : new Uint8Array() },
      { path: `${basePath}/data/${normal ? normal.name : "rifle_dmr_nohq.paa"}`, content: normal ? normal.bytes : new Uint8Array() },
      { path: `${basePath}/data/${roughness || metalness ? (roughness ? roughness.name : metalness.name) : "rifle_dmr_smdi.paa"}`, content: roughness || metalness ? (roughness ? roughness.bytes : metalness.bytes) : new Uint8Array() },
      { path: `${basePath}/data/rifle_dmr.rvmat`, content: new Uint8Array() },
      { path: `${basePath}/data/UI/${iconWeapon ? iconWeapon.name : ctx.weapon_icon}`, content: iconWeapon ? iconWeapon.bytes : new Uint8Array() },
      { path: `${basePath}/data/UI/${iconOptic ? iconOptic.name : ctx.optic_icon}`, content: iconOptic ? iconOptic.bytes : new Uint8Array() },
    ];

    // Also bundle extra inputs using their original filenames so users keep source PNGs/TGAs alongside PAAs.
    const extras = [
      { folder: `${basePath}/data/src`, file: color },
      { folder: `${basePath}/data/src`, file: normal },
      { folder: `${basePath}/data/src`, file: roughness },
      { folder: `${basePath}/data/src`, file: metalness },
      { folder: `${basePath}/data/src`, file: ao },
    ];
    for (const extra of extras) {
      if (extra.file) {
        files.push({ path: `${extra.folder}/${extra.file.name}`, content: extra.file.bytes });
      }
    }

    const zip = buildZip(files);
    const name = `${ctx.addon_folder}_scaffold.zip`;
    const link = document.createElement("a");
    link.href = URL.createObjectURL(zip);
    link.download = name;
    link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  });
}

function main() {
  renderList("steps", STEP_OVERVIEW);
  const form = document.getElementById("scaffold-form");
  if (form) {
    populateForm(form);
    form.addEventListener("submit", handleSubmit);
  }
}

document.addEventListener("DOMContentLoaded", main);
