"""
Fiches Play Store (FICHE_PLAY_STORE.md) : une fiche par langue de
l'application (TESTS_NON_REGRESSION.md, entrée 172).

Vérifie, pour le français, l'arabe et les 9 autres langues : titre ≤ 30,
description courte ≤ 80, description complète ≤ 4000 caractères (limites
de Google Play), texte dans la bonne écriture, et que chaque langue de
SUPPORTED_LANGUAGES (i18n.js) a sa fiche.
"""
import re
import sys

PROJECT_ROOT = "/home/user/mes-recettes-mobile"
SCRIPT = {"ar": r"[ء-ي]", "zh": r"[一-鿿]"}


def main():
    results = []

    def check(label, ok, detail=""):
        results.append(bool(ok))
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {label}{' — ' + str(detail) if detail != '' else ''}")

    fiche = open(f"{PROJECT_ROOT}/FICHE_PLAY_STORE.md", encoding="utf-8").read()
    langs = re.findall(r'code: "([a-z]{2})"', open(f"{PROJECT_ROOT}/i18n.js", encoding="utf-8").read().split("SUPPORTED_LANGUAGES = [", 1)[1].split("];", 1)[0])
    check("11 langues dans l'application", len(langs) == 11, langs)

    sections = {"fr": fiche.split("# Fiche en arabe", 1)[0],
                "ar": fiche.split("# Fiche en arabe", 1)[1].split("\n# ", 1)[0]}
    for code, body in re.findall(r"\n## [^\n(]+\(([a-z]{2})\)\n(.*?)(?=\n## |\Z)", fiche.split("# Fiches dans les autres langues", 1)[-1], re.S):
        sections[code] = body
    check("une fiche pour chaque langue de l'application", set(langs) <= set(sections), sorted(set(langs) - set(sections)))

    for code in langs:
        blocks = [b.strip() for b in re.findall(r"```\n(.*?)\n```", sections.get(code, ""), re.S)]
        if code == "fr":
            blocks = blocks[:3]
        if len(blocks) < 3:
            check(f"{code} : titre, description courte, description complète", False, len(blocks))
            continue
        title, short, full = blocks[:3]
        ok = len(title) <= 30 and len(short) <= 80 and len(full) <= 4000 and all(x for x in (title, short, full))
        if code in SCRIPT:
            ok = ok and all(re.search(SCRIPT[code], x) for x in (title, short, full))
        check(f"{code} : limites Google Play (30 / 80 / 4000) et écriture", ok, (len(title), len(short), len(full)))

    ok = all(results)
    print("\n=== Résumé ===")
    print("TOUT CORRECT" if ok else "ÉCHECS DÉTECTÉS")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
