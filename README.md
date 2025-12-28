# Arma 3 RHS DMR Mod Helper

This repository provides a small helper (CLI + web UI) that walks you through creating a custom Arma 3 rifle mod that depends on RHS. It bundles:

- A step-by-step checklist for model preparation, config authoring, attachments, and packaging.
- A scaffold generator that builds config.cpp/model.cfg templates and placeholder asset files.
- Quick guides for specific topics like model setup, texture pipelines, RHS attachment slots, and publishing.
- A browser-based UI so you can fill out form fields and download a ready-made scaffold zip without touching the CLI.

## Requirements
- Python 3.10+ (for running the helper).
- Flask 3.x (install with `pip install -r requirements.txt`).

## Usage (CLI)

```bash
python -m app plan               # Show the top-level checklist
python -m app guide all          # Show focused reminders for every stage
python -m app guide attachments  # Only show attachment slot notes
python -m app scaffold --output ./my_build  # Create @MyWeaponMod/addons/steyr_dmr_rhs skeleton
python -m app web --dry-run      # Show the URL for the web UI without starting the server
```

After scaffolding, replace the placeholder `.p3d` and `.paa` files with your converted assets, then pack the `steyr_dmr_rhs` folder into a PBO (and sign it) before publishing. The config templates already reference RHS dependencies and attachment slots so you can jump straight to in-game testing with Virtual Arsenal.

## Usage (web UI)

```bash
python -m app web --host 0.0.0.0 --port 8000
```

Then open the printed URL in your browser. The web helper lets you:

- Review the checklist and topic-specific guides.
- Fill out mod metadata (author, weapon classname/display name, addon prefix/folder, magazine wells, etc.).
- Download a zip containing config.cpp, model.cfg, and placeholder assets under `@MyWeaponMod/addons/<your folder>`.
