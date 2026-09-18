#!/usr/bin/env python3
"""Test permanent : validité du manifeste PWA et de ses 3 variantes de
langue (icônes existantes aux bonnes dimensions, mode standalone,
cohérence de la couleur de thème avec index.html/styles.css) — voir
TESTS_NON_REGRESSION.md point 92 (vérification des points d'une
checklist PWA spécifique, jamais couverts jusqu'ici : invite
d'installation, manifeste, mode standalone, hors-ligne à froid, accès
caméra réel, Lighthouse).

Ne remplace PAS une vérification visuelle réelle de l'icône/écran de
démarrage une fois l'application effectivement installée sur un
téléphone (impossible à reproduire dans cet environnement) — vérifie
uniquement que les DONNÉES qui déterminent ce rendu sont correctes et
cohérentes entre elles.

Utilisation :

    cd /chemin/vers/recipe_pwa
    python3 tests/test_pwa_manifest.py

Code de sortie : 0 si tous les cas passent, 1 sinon.
"""
import json
import os
import struct
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MANIFEST_FILES = ["manifest.json", "manifest-en.json", "manifest-es.json", "manifest-de.json"]
REQUIRED_KEYS = ["name", "short_name", "start_url", "display", "background_color", "theme_color", "icons"]


def png_dimensions(path):
    with open(path, "rb") as f:
        data = f.read(33)
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w, h = struct.unpack(">II", data[16:24])
    return w, h


def main():
    all_ok = True

    def check(label, ok, detail=""):
        nonlocal all_ok
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {label}" + (f" — {detail}" if detail else ""))
        if not ok:
            all_ok = False

    print("=== index.html : cohérence des balises meta PWA ===\n")
    with open(os.path.join(PROJECT_ROOT, "index.html"), encoding="utf-8") as f:
        html = f.read()
    check("theme-color meta présente", 'name="theme-color"' in html)
    check("Lien manifest avec id=\"app-manifest\" présent (nécessaire à manifest-loader.js)", 'id="app-manifest"' in html)
    check("apple-touch-icon présente (iOS ne lit pas les icônes du manifeste)", 'rel="apple-touch-icon"' in html)
    check("apple-mobile-web-app-capable présente (mode standalone iOS)", 'apple-mobile-web-app-capable' in html)

    # Favicon dédiée 32x32 (point 9 de l'audit externe) : un simple
    # redimensionnement à la volée depuis le 192x192 par le navigateur
    # peut donner un rendu flou dans un onglet/favoris de bureau.
    check("Lien favicon 32x32 dédié présent (pas seulement le 192x192)", 'sizes="32x32"' in html and "icon-32.png" in html)
    favicon32_path = os.path.join(PROJECT_ROOT, "icons", "icon-32.png")
    check("icons/icon-32.png existe", os.path.isfile(favicon32_path))
    if os.path.isfile(favicon32_path):
        dims32 = png_dimensions(favicon32_path)
        check("icons/icon-32.png fait bien 32x32", dims32 == (32, 32), str(dims32))

    manifests = {}
    for name in MANIFEST_FILES:
        path = os.path.join(PROJECT_ROOT, name)
        print(f"\n=== {name} ===\n")
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            manifests[name] = data
        except Exception as e:
            check(f"{name} : JSON valide", False, str(e))
            continue
        check(f"{name} : JSON valide", True)
        for key in REQUIRED_KEYS:
            check(f"{name} : clé '{key}' présente", key in data and data[key], "" if key in data else "manquante")
        check(f"{name} : display = \"standalone\" (condition du mode sans barre d'adresse)", data.get("display") == "standalone")
        # Point 4 de l'audit externe : une orientation forcée empêche
        # tout usage confortable sur tablette/PC ou téléphone posé à
        # plat en mode paysage, alors que l'interface est responsive.
        check(f"{name} : aucune orientation forcée (laisse le choix à l'utilisateur)", "orientation" not in data)

        for icon in data.get("icons", []):
            icon_path = os.path.join(PROJECT_ROOT, icon["src"])
            exists = os.path.isfile(icon_path)
            check(f"{name} : icône '{icon['src']}' existe", exists)
            if exists:
                dims = png_dimensions(icon_path)
                declared = icon["sizes"]
                actual = f"{dims[0]}x{dims[1]}" if dims else None
                check(f"{name} : icône '{icon['src']}' fait bien {declared} (déclaré)", actual == declared, f"réel: {actual}")

    print("\n=== Captures d'écran (manifest.json) : narrow ET wide ===\n")
    # Point 4 de l'audit externe : sans capture "wide", l'invite
    # d'installation sur PC/tablette n'affiche aucun aperçu.
    screenshots = manifests.get("manifest.json", {}).get("screenshots", [])
    form_factors = [s.get("form_factor") for s in screenshots]
    check("Au moins une capture 'narrow' (mobile) déclarée", "narrow" in form_factors, str(form_factors))
    check("Au moins une capture 'wide' (bureau/tablette) déclarée", "wide" in form_factors, str(form_factors))
    for shot in screenshots:
        shot_path = os.path.join(PROJECT_ROOT, shot["src"])
        exists = os.path.isfile(shot_path)
        check(f"Capture '{shot['src']}' ({shot.get('form_factor')}) existe", exists)
        if exists:
            dims = png_dimensions(shot_path)
            declared = shot["sizes"]
            actual = f"{dims[0]}x{dims[1]}" if dims else None
            check(f"Capture '{shot['src']}' fait bien {declared} (déclaré)", actual == declared, f"réel: {actual}")
            if dims:
                ratio = max(dims) / min(dims)
                check(f"Capture '{shot['src']}' : ratio {ratio:.2f}:1 dans la limite de 2:1 imposée par les stores", ratio <= 2.0, f"ratio={ratio:.3f}")

    print("\n=== Cohérence entre les 4 manifestes (branding partagé) ===\n")
    theme_colors = {name: m.get("theme_color") for name, m in manifests.items()}
    check("Même theme_color dans les 4 manifestes", len(set(theme_colors.values())) == 1, str(theme_colors))
    theme_meta = html.split('name="theme-color" content="')[1].split('"')[0] if 'name="theme-color" content="' in html else None
    check("theme-color d'index.html identique à celui des manifestes", theme_meta in theme_colors.values(), f"index.html: {theme_meta}")

    print("\n=== manifest-loader.js : sélection du bon fichier selon la langue ===\n")
    with open(os.path.join(PROJECT_ROOT, "manifest-loader.js"), encoding="utf-8") as f:
        loader = f.read()
    check("Les 4 codes de langue supportés apparaissent dans le sélecteur", all(f'"{lang}"' in loader for lang in ["fr", "en", "es", "de"]))

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
