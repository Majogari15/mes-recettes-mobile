"""
Écran « Vérifier les doublons » sur une installation neuve
(TESTS_NON_REGRESSION.md, entrée 171).

Avant : plus de 4 300 « doublons possibles » avant même que l'utilisateur
ait créé un seul ingrédient — presque tous des variantes réellement
différentes du catalogue (coupes de viande « paré à 1/4 po » / « 1/8 po »,
cru / cuit, avec / sans sel, catégories USDA…). Ces paires, vérifiées une
à une par catégorie, sont listées par id dans
data/catalogue_not_duplicates.json et ne sont plus proposées.

Les 30 vrais doublons du catalogue (même produit deux fois : « Beurre
salé » / « Beurre, salé », « Noisette » / « Noisettes »…) sont retirés
(« doublonDe » dans ingredients_catalogue.json) : plus proposés aux
nouvelles installations, gardés dans les données pour qui les a déjà.

Vérifie : le fichier (ids existants, paires distinctes, aucune paire où
les deux noms ne diffèrent que par une virgule ou un pluriel) ; les 30
entrées retirées (chacune vers une entrée gardée, active) ; dans les 11
langues, l'écran n'affiche aucun doublon sur une installation neuve ; un
ingrédient créé par l'utilisateur, proche d'un ingrédient du catalogue,
reste signalé ; « Pas un doublon » choisi par l'utilisateur fonctionne
toujours ; entrée retirée gardée par un utilisateur actuel : données
(allergènes, nutrition) intactes ; substitutions de l'entrée retirée
reportées sur l'entrée gardée ; saisie du nom traduit d'une entrée retirée
-> entrée gardée.
"""
import http.server
import json
import re
import socket
import sys
import threading
import unicodedata

from playwright.sync_api import sync_playwright

PROJECT_ROOT = "/home/user/mes-recettes-mobile"
LANGS = ["fr", "en", "es", "de", "id", "pt", "it", "sv", "no", "zh", "ar"]


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=PROJECT_ROOT, **k)

    def log_message(self, *a):
        pass


def words(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").replace("œ", "oe")
    return [w[:-1] if len(w) > 3 and w[-1] in "sx" else w for w in re.findall(r"[a-z0-9/%.]+", s)]


def main():
    results = []

    def check(label, ok, detail=""):
        results.append(bool(ok))
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {label}{' — ' + str(detail) if detail != '' else ''}")

    data = json.load(open(f"{PROJECT_ROOT}/data/catalogue_not_duplicates.json", encoding="utf-8"))
    catalogue = {int(e["id"][4:]): e["fr"] for e in json.load(open(f"{PROJECT_ROOT}/data/ingredients_catalogue.json", encoding="utf-8"))}
    pairs = data["pairs"]
    check("fichier : plus de 4 000 paires", len(pairs) > 4000, len(pairs))
    check("fichier : ids existants, paires de deux ingrédients différents, sans répétition",
          all(a in catalogue and b in catalogue and a < b for a, b in pairs) and len({tuple(p) for p in pairs}) == len(pairs))
    same = [(catalogue[a], catalogue[b]) for a, b in pairs if words(catalogue[a]) == words(catalogue[b])]
    check("fichier : aucun vrai doublon masqué (noms ne différant que par une virgule ou un pluriel)", not same, same[:3])
    entries = json.load(open(f"{PROJECT_ROOT}/data/ingredients_catalogue.json", encoding="utf-8"))
    by_id = {e["id"]: e for e in entries}
    retired = [e for e in entries if e.get("doublonDe")]
    check("catalogue : 30 entrées retirées, chacune vers une entrée gardée active de même produit",
          len(retired) == 30 and all(e["doublonDe"] in by_id and not by_id[e["doublonDe"]].get("doublonDe")
                                     for e in retired), len(retired))

    port = find_free_port()
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        errors = []

        def open_screen(page):
            page.evaluate("() => { state.screen = 'ingredientDuplicates'; render(); }")
            page.wait_for_function("() => !document.querySelector('.dup-loading') && document.querySelectorAll('main .dismiss-btn, main .empty-state').length",
                                   timeout=120000)
            return page.evaluate("() => [...document.querySelectorAll('main .dismiss-btn')].map((b) => b.closest('.card').innerText.split('\\n')[0])")

        counts = {}
        for lang in LANGS:
            page = browser.new_page()
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            page.goto(f"http://127.0.0.1:{port}/index.html", timeout=15000)
            page.evaluate("() => appReady")
            page.evaluate("async (l) => { await ensureUiTranslationsLoaded(l); await ensureIngredientTranslationsLoaded(l); setLang(l); }", lang)
            counts[lang] = len(open_screen(page))
            if lang != "fr":
                page.close()
                continue
            fr_page = page
        check("installation neuve : aucun doublon affiché dans les 11 langues (avant : plus de 4 300)",
              all(n == 0 for n in counts.values()), counts)

        page = fr_page
        r = page.evaluate("""() => ({ beurre: state.ingredientNames.includes('Beurre salé'), virgule: state.ingredientNames.includes('Beurre, salé'),
            noisettes: state.ingredientNames.includes('Noisettes'), subs: getDisplaySubstitutes('Beurre salé').length,
            // Substitut proposé = entrée retirée « Beurre, salé » : affiché sous le nom gardé.
            target: (() => { const rel = SUBSTITUTIONS_DB.find((x) => x.targetIngredientId === 'ing_005961');
              const src = CATALOGUE_BY_ID[rel.ingredientId]; return getDisplaySubstitutes(src).map((d) => d.nom); })() })""")
        check("installation neuve : entrée gardée présente, entrée retirée absente (« Beurre salé » oui, « Beurre, salé » / « Noisettes » non)",
              r["beurre"] and not r["virgule"] and not r["noisettes"], r)
        check("substitutions de l'entrée retirée reportées sur l'entrée gardée (« Beurre salé » : 0 -> 1)", r["subs"] >= 1, r)
        check("substitut proposé = entrée retirée : affiché sous le nom gardé (« Beurre salé »)",
              "Beurre salé" in r["target"] and "Beurre, salé" not in r["target"], r["target"])
        # Utilisateur actuel ayant encore « Beurre, salé » (entrée retirée).
        r = page.evaluate("""async () => { await storePut('ingredients', { name: 'Beurre, salé', catalogId: 'ing_005961' });
            state.ingredientNames.push('Beurre, salé'); state.ingredientCatalogIds[normalize('Beurre, salé')] = 'ing_005961';
            state.ingredientNameByCatalogId['ing_005961'] = 'Beurre, salé';
            return { id: getIngredientCatalogId('Beurre, salé'), nutrition: !!NUTRITION_DB['ing_005961'], allergens: !!ALLERGEN_DB['ing_005961'] }; }""")
        check("utilisateur actuel : entrée retirée toujours reliée à ses données", r == {"id": "ing_005961", "nutrition": True, "allergens": True}, r)
        rows = open_screen(page)
        check("utilisateur actuel : la paire « Beurre salé ↔ Beurre, salé » lui est proposée (fusion possible)",
              any("Beurre salé" in x and "Beurre, salé" in x for x in rows), rows[:3])
        page.evaluate("""async () => { await storeDelete('ingredients', 'Beurre, salé'); state.ingredientNames = state.ingredientNames.filter((n) => n !== 'Beurre, salé');
            delete state.ingredientNameByCatalogId['ing_005961']; delete state.ingredientCatalogIds[normalize('Beurre, salé')]; }""")
        # Nom traduit d'une entrée retirée saisi (ex. import en anglais) -> entrée gardée.
        r = page.evaluate("""async () => { await ensureIngredientTranslationsLoaded('en'); setLang('en');
            const out = resolveIngredientInput(INGREDIENT_TRANSLATIONS.en['ing_005141']); setLang('fr'); return out; }""")
        check("nom traduit d'une entrée retirée (« Noisettes » en anglais) -> entrée gardée « Noisette »", r == "Noisette", r)
        # Ingrédient créé par l'utilisateur, très proche d'un ingrédient du
        # catalogue : toujours signalé.
        page.evaluate("async () => { await addIngredientName('Agneau, épaule entière (bras et palette), maigre et gras séparables, paré à 1/4 po de gras, catégorie Choix, cuit, grilé au four'); }")
        rows = open_screen(page)
        check("ingrédient créé par l'utilisateur proche du catalogue : toujours signalé",
              any("grilé au four" in r for r in rows), len(rows))
        # « Pas un doublon » choisi par l'utilisateur : toujours retenu.
        before = len(rows)
        page.click("main .dismiss-btn")
        page.wait_for_function(f"() => document.querySelectorAll('main .dismiss-btn').length === {before - 1}", timeout=10000)
        check("« Pas un doublon » de l'utilisateur toujours retenu", True)
        page.close()
        check("aucune erreur JS", not errors, errors)
        browser.close()
    httpd.shutdown()
    ok = all(results)
    print("\n=== Résumé ===")
    print("TOUT CORRECT" if ok else "ÉCHECS DÉTECTÉS")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
