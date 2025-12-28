"""Flask web UI for the Arma 3 RHS rifle mod helper."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Dict
from zipfile import ZipFile

from flask import Flask, render_template_string, request, send_file, url_for

from app.main import MODEL_CFG_TEMPLATE, CONFIG_TEMPLATE, ScaffoldContext, STEP_OVERVIEW


PAGE_BASE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Arma 3 RHS DMR Helper</title>
  <style>
    body { font-family: Inter, system-ui, -apple-system, sans-serif; margin: 0; padding: 0; background: #0f172a; color: #e2e8f0; }
    header { padding: 1.5rem 2rem; background: #111827; border-bottom: 1px solid #1f2937; }
    main { padding: 2rem; max-width: 1080px; margin: 0 auto; }
    a { color: #38bdf8; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .card { background: #1f2937; border: 1px solid #334155; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1rem; }
    .button { background: #2563eb; border: none; border-radius: 8px; color: #fff; padding: 0.75rem 1.1rem; cursor: pointer; font-weight: 600; }
    .button.secondary { background: #0ea5e9; }
    input, textarea, select { width: 100%; padding: 0.65rem 0.75rem; border-radius: 8px; border: 1px solid #334155; background: #0b1325; color: #e2e8f0; }
    label { display: block; margin-bottom: 0.35rem; font-weight: 600; }
    form .row { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; }
    ul { padding-left: 1.1rem; }
    code { background: #0b1325; padding: 0.2rem 0.4rem; border-radius: 6px; }
  </style>
</head>
<body>
  <header>
    <div style="max-width:1080px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;gap:1rem;flex-wrap:wrap;">
      <div>
        <div style="font-size:1.4rem;font-weight:800;">Arma 3 RHS DMR Helper</div>
        <div style="color:#9ca3af;">Walkthrough, guides, and scaffold download</div>
      </div>
      <div style="display:flex;gap:0.75rem;flex-wrap:wrap;">
        <a class="button secondary" href="{{ url_for('plan') }}">Checklist</a>
        <a class="button secondary" href="{{ url_for('guides') }}">Guides</a>
        <a class="button" href="{{ url_for('scaffold') }}">Generate Scaffold</a>
      </div>
    </div>
  </header>
  <main>
    {{ body|safe }}
  </main>
</body>
</html>
"""


INDEX_BODY = """
<div class="grid">
  <div class="card">
    <h2>1) Checklist</h2>
    <p>Follow the high-level steps to convert your model, set up config.cpp/model.cfg, and test in-game with RHS.</p>
    <a href="{{ url_for('plan') }}">Open the checklist →</a>
  </div>
  <div class="card">
    <h2>2) Focused Guides</h2>
    <p>Concise reminders for model prep, textures/RVMATs, attachment slots, and packaging/signing.</p>
    <a href="{{ url_for('guides') }}">Browse guide topics →</a>
  </div>
  <div class="card">
    <h2>3) Downloadable Scaffold</h2>
    <p>Fill in your mod name, weapon class, and dependencies, then download a zip containing config.cpp, model.cfg, and placeholder assets.</p>
    <a href="{{ url_for('scaffold') }}">Generate scaffold →</a>
  </div>
</div>
"""


GUIDE_BODY = """
<div class="card">
  <h2>Guides</h2>
  <ul>
    <li><strong>Model:</strong> Prepare geometry LODs, memory points (usti hlavne, konec hlavne, nabojnicestart, nabojniceend) and proxies for TOP/SIDE/MUZZLE/UNDERBARREL in Object Builder.</li>
    <li><strong>Textures:</strong> Convert textures to .paa (_co, _nohq, _smdi) and reference them via an RVMAT with relative paths to avoid pink materials.</li>
    <li><strong>Attachments:</strong> Use rhs_western_rifle_muzzle_slot, rhs_western_rifle_scopes_slot_short, rhs_western_rifle_laser_slot, and rhs_western_rifle_underbarrel_slot for plug-and-play RHS suppressors, optics, lasers, and bipods.</li>
    <li><strong>Packaging:</strong> Pack your addon into a PBO (Addon Builder or Mikero), binarize models, sign the PBO, and include the .bikey in a keys folder before publishing.</li>
  </ul>
</div>
"""


PLAN_BODY = """
<div class="card">
  <h2>Checklist</h2>
  <ol>
    {% for step in steps %}
    <li>{{ step }}</li>
    {% endfor %}
  </ol>
  <p style="margin-top:1rem;color:#9ca3af;">Tip: keep texture paths relative, use RHS slots for instant attachment compatibility, and test in Virtual Arsenal with RHS loaded.</p>
</div>
"""


SCAFFOLD_FORM = """
<div class="card">
  <h2>Scaffold generator</h2>
  <p>Provide the names you want baked into config.cpp/model.cfg. The download includes placeholders for the model, optic, textures, and UI icons.</p>
  <form method="post">
    <div class="row">
      <div>
        <label for="addon_prefix">Mod prefix (folder)</label>
        <input id="addon_prefix" name="addon_prefix" value="{{ defaults.addon_prefix }}" required>
      </div>
      <div>
        <label for="addon_folder">Addon PBO folder</label>
        <input id="addon_folder" name="addon_folder" value="{{ defaults.addon_folder }}" required>
      </div>
    </div>
    <div class="row" style="margin-top:1rem;">
      <div>
        <label for="weapon_class">Weapon classname</label>
        <input id="weapon_class" name="weapon_class" value="{{ defaults.weapon_class }}" required>
      </div>
      <div>
        <label for="weapon_name">Weapon display name</label>
        <input id="weapon_name" name="weapon_name" value="{{ defaults.weapon_name }}" required>
      </div>
      <div>
        <label for="author">Author</label>
        <input id="author" name="author" value="{{ defaults.author }}" required>
      </div>
    </div>
    <div class="row" style="margin-top:1rem;">
      <div>
        <label for="magazine_wells">Magazine wells (comma-separated)</label>
        <input id="magazine_wells" name="magazine_wells" value="{{ defaults.magazine_wells }}">
      </div>
      <div>
        <label for="magazines">Magazines (comma-separated classnames)</label>
        <input id="magazines" name="magazines" value="{{ defaults.magazines }}">
      </div>
    </div>
    <div class="row" style="margin-top:1rem;">
      <div>
        <label for="model_filename">Model filename</label>
        <input id="model_filename" name="model_filename" value="{{ defaults.model_filename }}">
      </div>
      <div>
        <label for="weapon_icon">Weapon icon filename</label>
        <input id="weapon_icon" name="weapon_icon" value="{{ defaults.weapon_icon }}">
      </div>
    </div>
    <div class="row" style="margin-top:1rem;">
      <div>
        <label for="optic_class">Optic classname</label>
        <input id="optic_class" name="optic_class" value="{{ defaults.optic_class }}">
      </div>
      <div>
        <label for="optic_name">Optic display name</label>
        <input id="optic_name" name="optic_name" value="{{ defaults.optic_name }}">
      </div>
    </div>
    <div class="row" style="margin-top:1rem;">
      <div>
        <label for="optic_model">Optic model filename</label>
        <input id="optic_model" name="optic_model" value="{{ defaults.optic_model }}">
      </div>
      <div>
        <label for="optic_icon">Optic icon filename</label>
        <input id="optic_icon" name="optic_icon" value="{{ defaults.optic_icon }}">
      </div>
    </div>
    <div style="margin-top:1rem;">
      <label for="required_addons">Required addons (comma-separated)</label>
      <input id="required_addons" name="required_addons" value="{{ defaults.required_addons }}">
    </div>
    <div style="margin-top:1.5rem;display:flex;gap:0.75rem;align-items:center;">
      <button class="button" type="submit">Download scaffold zip</button>
      <p style="color:#9ca3af;margin:0;">Includes config.cpp, model.cfg, placeholder .p3d/.paa/.rvmat files.</p>
    </div>
  </form>
</div>
"""


def create_app() -> Flask:
    app = Flask(__name__)

    def render_page(body: str, **context: Dict[str, str]):
        return render_template_string(PAGE_BASE, body=body, **context)

    @app.get("/")
    def index():
        return render_page(INDEX_BODY)

    @app.get("/guides")
    def guides():
        return render_page(GUIDE_BODY)

    @app.get("/plan")
    def plan():  # type: ignore[override]
        return render_page(PLAN_BODY, steps=STEP_OVERVIEW)

    @app.route("/scaffold", methods=["GET", "POST"])
    def scaffold():  # type: ignore[override]
        defaults = ScaffoldContext()
        if request.method == "GET":
            return render_page(
                SCAFFOLD_FORM,
                defaults={
                    "addon_prefix": defaults.addon_prefix,
                    "addon_folder": defaults.addon_folder,
                    "author": defaults.author,
                    "weapon_class": defaults.weapon_class,
                    "weapon_name": defaults.weapon_name,
                    "magazine_wells": defaults.magazine_wells,
                    "magazines": defaults.magazines,
                    "model_filename": defaults.model_filename,
                    "weapon_icon": defaults.weapon_icon,
                    "optic_class": defaults.optic_class,
                    "optic_name": defaults.optic_name,
                    "optic_model": defaults.optic_model,
                    "optic_icon": defaults.optic_icon,
                    "required_addons": ",".join(defaults.required_addons),
                },
            )

        ctx = ScaffoldContext(
            addon_prefix=request.form.get("addon_prefix", defaults.addon_prefix),
            addon_folder=request.form.get("addon_folder", defaults.addon_folder),
            author=request.form.get("author", defaults.author),
            weapon_class=request.form.get("weapon_class", defaults.weapon_class),
            weapon_name=request.form.get("weapon_name", defaults.weapon_name),
            magazine_wells=request.form.get("magazine_wells", defaults.magazine_wells),
            magazines=request.form.get("magazines", defaults.magazines),
            model_filename=request.form.get("model_filename", defaults.model_filename),
            weapon_icon=request.form.get("weapon_icon", defaults.weapon_icon),
            optic_class=request.form.get("optic_class", defaults.optic_class),
            optic_name=request.form.get("optic_name", defaults.optic_name),
            optic_model=request.form.get("optic_model", defaults.optic_model),
            optic_icon=request.form.get("optic_icon", defaults.optic_icon),
            required_addons=[addon.strip() for addon in request.form.get("required_addons", ",".join(defaults.required_addons)).split(",") if addon.strip()],
        )

        zip_bytes = io.BytesIO()
        addon_root = f"@MyWeaponMod/addons/{ctx.addon_folder}"
        kwargs = ctx.to_format_kwargs()
        with ZipFile(zip_bytes, "w") as bundle:
            bundle.writestr(f"{addon_root}/config.cpp", CONFIG_TEMPLATE.substitute(**kwargs))
            bundle.writestr(f"{addon_root}/model.cfg", MODEL_CFG_TEMPLATE.substitute(**kwargs))
            placeholder_paths = [
                f"{addon_root}/{ctx.model_filename}",
                f"{addon_root}/{ctx.optic_model}",
                f"{addon_root}/data/rifle_dmr_co.paa",
                f"{addon_root}/data/rifle_dmr_nohq.paa",
                f"{addon_root}/data/rifle_dmr_smdi.paa",
                f"{addon_root}/data/rifle_dmr.rvmat",
                f"{addon_root}/data/UI/{ctx.weapon_icon}",
                f"{addon_root}/data/UI/{ctx.optic_icon}",
            ]
            for path in placeholder_paths:
                bundle.writestr(path, "")
        zip_bytes.seek(0)

        download_name = f"{ctx.addon_folder}_scaffold.zip"
        return send_file(zip_bytes, as_attachment=True, download_name=download_name, mimetype="application/zip")

    return app


__all__ = ["create_app"]
