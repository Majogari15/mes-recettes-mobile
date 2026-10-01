"""
Vérifie que APP_VERSION (app.js, affiché sur les écrans Sauvegarde et
Diagnostic) correspond au numéro de CACHE_NAME (sw.js). Les deux doivent
être incrémentés ensemble à chaque livraison ; APP_VERSION était resté
bloqué à 275 pendant que le cache passait à 291, affichant une version
fausse à l'utilisateur.
"""
import re
import sys

PROJECT_ROOT = "/home/user/mes-recettes-mobile"


def main():
    app = open(f"{PROJECT_ROOT}/app.js", encoding="utf-8").read()
    sw = open(f"{PROJECT_ROOT}/sw.js", encoding="utf-8").read()
    app_version = re.search(r"^const APP_VERSION = (\d+);", app, re.M)
    cache_version = re.search(r"^const CACHE_NAME = `\$\{CACHE_PREFIX\}v(\d+)`;", sw, re.M)
    ok = bool(app_version and cache_version and app_version.group(1) == cache_version.group(1))
    detail = f"APP_VERSION={app_version and app_version.group(1)} / CACHE_NAME=v{cache_version and cache_version.group(1)}"
    print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  APP_VERSION identique au numéro de CACHE_NAME — {detail}")
    print("\n=== Résumé ===")
    print("TOUT CORRECT" if ok else "ÉCHECS DÉTECTÉS")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
