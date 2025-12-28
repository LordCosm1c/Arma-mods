"""
CLI assistant for guiding Arma 3 custom rifle mod creation with RHS dependency.
"""

from __future__ import annotations

import argparse
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from string import Template


STEP_OVERVIEW: List[str] = [
    "Prepare and convert your model (Blender/Object Builder, LODs, proxies, textures).",
    "Set up the mod folder (@MyWeaponMod/addons/your_addon) with model, textures, config.cpp, and model.cfg.",
    "Write config.cpp (CfgPatches, CfgWeapons, optional CfgMagazines/Ammo) with RHS dependencies.",
    "Define model.cfg animations (bolt, trigger, magazine hide) tied to animation sources.",
    "Wire modular attachments (optics, suppressor, lasers, bipod) using RHS slot classes.",
    "Verify animations, sounds, muzzle and ejection memory points in-game.",
    "Package as a PBO, sign it, and publish with RHS listed as a dependency."
]


CONFIG_TEMPLATE = Template(
    textwrap.dedent(
        r"""
        #include "basicDefines_A3.hpp"

        class CfgPatches {
            class ${addon_folder} {
                author = "${author}";
                name = "${weapon_name} (RHS Mod)";
                url = "";
                units[] = {};
                weapons[] = {"${weapon_class}"};
                requiredVersion = 1.0;
                requiredAddons[] = {${required_addons}};
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
            class ${weapon_class}: Rifle_Base_F {
                author = "${author}";
                displayName = "${weapon_name}";
                descriptionShort = "DMR (7.62x51) using RHS attachments";
                model = "\\${addon_prefix}\\addons\\${addon_folder}\\${model_filename}";
                picture = "\\${addon_prefix}\\addons\\${addon_folder}\\data\\UI\\${weapon_icon}";
                modes[] = {"Single"};
                magazineWell[] = {${magazine_wells}};
                magazines[] = {${magazines}};
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

            class ${optic_class}: ItemCore {
                scope = 2; scopeCurator = 2;
                displayName = "${optic_name}";
                model = "\\${addon_prefix}\\addons\\${addon_folder}\\${optic_model}";
                picture = "\\${addon_prefix}\\addons\\${addon_folder}\\data\\UI\\${optic_icon}";
                descriptionShort = "Optical sight for the ${weapon_name}";
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
        """
    )
)


MODEL_CFG_TEMPLATE = Template(
    textwrap.dedent(
        r"""
        class CfgSkeletons {
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
            class ${model_class}: Default {
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
        """
    )
)


@dataclass
class ScaffoldContext:
    addon_prefix: str = "my_mod"
    addon_folder: str = "steyr_dmr_rhs"
    author: str = "YourName"
    weapon_class: str = "Steyr_DMR_762"
    weapon_name: str = "Steyr Arms DMR 7.62"
    model_filename: str = "Rifle_SteyrArms_DMR_762_v01.p3d"
    weapon_icon: str = "steyr_dmr_icon_ca.paa"
    optic_class: str = "Steyr_DMR_Scope"
    optic_name: str = "Steyr DMR Scope 6-24x"
    optic_model: str = "steyr_scope.p3d"
    optic_icon: str = "scope_icon_ca.paa"
    magazine_wells: str = "SR25"
    magazines: str = "rhs_mag_20Rnd_762x51_M118_special_Mag"
    required_addons: List[str] = None

    def __post_init__(self) -> None:
        if self.required_addons is None:
            self.required_addons = ["A3_Weapons_F", "rhsusf_main", "rhs_c_weapons"]

    def to_format_kwargs(self) -> Dict[str, str]:
        return {
            "addon_prefix": self.addon_prefix,
            "addon_folder": self.addon_folder,
            "author": self.author,
            "weapon_class": self.weapon_class,
            "weapon_name": self.weapon_name,
            "model_filename": self.model_filename,
            "weapon_icon": self.weapon_icon,
            "optic_class": self.optic_class,
            "optic_name": self.optic_name,
            "optic_model": self.optic_model,
            "optic_icon": self.optic_icon,
            "magazine_wells": ", ".join(
                f'"{item.strip()}"' for item in self.magazine_wells.split(",") if item.strip()
            ),
            "magazines": ", ".join(
                f'"{item.strip()}"' for item in self.magazines.split(",") if item.strip()
            ),
            "required_addons": ", ".join(f'"{item.strip()}"' for item in self.required_addons),
            "model_class": Path(self.model_filename).stem,
        }


def write_template(path: Path, content: str) -> None:
    path.write_text(content.strip() + "\n", encoding="utf-8")
    resolved = path.resolve()
    try:
        display_path = resolved.relative_to(Path.cwd())
    except ValueError:
        display_path = resolved
    print(f"Created {display_path}")


def action_plan() -> None:
    print("\nGuided checklist for building the RHS-based Steyr DMR mod:\n")
    for idx, step in enumerate(STEP_OVERVIEW, start=1):
        print(f" {idx}. {step}")
    print("\nTips:\n - Keep texture paths relative (avoid pink textures).\n"
          " - Use RHS attachment slots for instant suppressor/scope/bipod compatibility.\n"
          " - Test in Virtual Arsenal with RHS loaded; inspect RPT if something is missing.\n")


def action_scaffold(base: Path, context: ScaffoldContext | None = None) -> None:
    ctx = context or ScaffoldContext()
    addon_dir = base / "@MyWeaponMod" / "addons" / ctx.addon_folder
    data_dir = addon_dir / "data" / "UI"
    addon_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    format_kwargs = ctx.to_format_kwargs()
    write_template(addon_dir / "config.cpp", CONFIG_TEMPLATE.substitute(**format_kwargs))
    write_template(addon_dir / "model.cfg", MODEL_CFG_TEMPLATE.substitute(**format_kwargs))

    placeholder_files = [
        addon_dir / ctx.model_filename,
        addon_dir / ctx.optic_model,
        addon_dir / "data" / "rifle_dmr_co.paa",
        addon_dir / "data" / "rifle_dmr_nohq.paa",
        addon_dir / "data" / "rifle_dmr_smdi.paa",
        addon_dir / "data" / "rifle_dmr.rvmat",
        data_dir / ctx.weapon_icon,
        data_dir / ctx.optic_icon,
    ]
    for placeholder in placeholder_files:
        placeholder.parent.mkdir(parents=True, exist_ok=True)
        if not placeholder.exists():
            placeholder.touch()
    print(f"\nScaffold ready in: {addon_dir}")
    print("Replace placeholder .p3d and .paa files with your converted assets before packing.")


def action_guide(topic: str) -> None:
    sections = {
        "model": "Prepare geometry LODs, memory points (usti hlavne, konec hlavne, nabojnicestart, nabojniceend) and proxies for TOP/SIDE/MUZZLE/UNDERBARREL in Object Builder.",
        "textures": "Convert textures to .paa (_co, _nohq, _smdi) and reference them via an RVMAT with relative paths to avoid pink materials.",
        "attachments": "Use rhs_western_rifle_muzzle_slot, rhs_western_rifle_scopes_slot_short, rhs_western_rifle_laser_slot, and rhs_western_rifle_underbarrel_slot for plug-and-play RHS suppressors, optics, lasers, and bipods.",
        "packaging": "Pack steyr_dmr_rhs into a PBO (Addon Builder or Mikero), binarize models, sign the PBO, and include the .bikey in a keys folder before publishing.",
    }
    if topic == "all":
        for key, text in sections.items():
            print(f"\n[{key}]\n{text}")
    else:
        print(sections.get(topic, "Unknown guide topic. Choose from: all, model, textures, attachments, packaging."))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Walk through creating a custom Arma 3 rifle mod with RHS dependency."
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("plan", help="Print the high-level checklist.")

    scaffold_parser = subparsers.add_parser("scaffold", help="Create a ready-to-fill mod folder and config templates.")
    scaffold_parser.add_argument(
        "--output",
        type=Path,
        default=Path.cwd() / "output_mod",
        help="Base directory where the @MyWeaponMod scaffold will be created.",
    )
    scaffold_parser.add_argument("--addon-prefix", default="my_mod")
    scaffold_parser.add_argument("--addon-folder", default="steyr_dmr_rhs")
    scaffold_parser.add_argument("--weapon-class", default="Steyr_DMR_762")
    scaffold_parser.add_argument("--weapon-name", default="Steyr Arms DMR 7.62")
    scaffold_parser.add_argument("--author", default="YourName")
    scaffold_parser.add_argument("--magazine-wells", default="SR25")
    scaffold_parser.add_argument(
        "--magazines",
        default="rhs_mag_20Rnd_762x51_M118_special_Mag",
        help="Comma-separated list of magazine classnames.",
    )

    guide_parser = subparsers.add_parser("guide", help="Show focused tips (model, textures, attachments, packaging, all).")
    guide_parser.add_argument("topic", type=str, default="all", nargs="?")

    web_parser = subparsers.add_parser("web", help="Run the browser-based helper UI.")
    web_parser.add_argument("--host", default="127.0.0.1")
    web_parser.add_argument("--port", type=int, default=8000)
    web_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the start URL without running the server (useful for quick checks).",
    )

    return parser


def main(argv: List[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "plan":
        action_plan()
    elif args.command == "scaffold":
        context = ScaffoldContext(
            addon_prefix=args.addon_prefix,
            addon_folder=args.addon_folder,
            weapon_class=args.weapon_class,
            weapon_name=args.weapon_name,
            author=args.author,
            magazine_wells=args.magazine_wells,
            magazines=args.magazines,
        )
        action_scaffold(Path(args.output), context)
    elif args.command == "guide":
        action_guide(args.topic)
    elif args.command == "web":
        from app.web import create_app

        app = create_app()
        start_url = f"http://{args.host}:{args.port}"
        if args.dry_run:
            print(f"Web UI ready to run at {start_url} (dry run, server not started).")
            return
        print(f"Starting web UI at {start_url} ...")
        app.run(host=args.host, port=args.port, debug=False)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
