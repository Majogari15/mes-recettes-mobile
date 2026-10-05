"""
Arabe (arabe standard moderne) — catalogue d'ingrédients et substitutions
(TESTS_NON_REGRESSION.md, entrée 165 ; intégration en cours sur une
branche, pas encore sur main).

Vérifie : les ~10 000 noms du catalogue traduits (mêmes ids, dans le même
ordre que l'anglais, aucun vide, chacun contient de l'arabe, aucune
traduction en double, même une fois voyelles brèves et chadda retirées —
sinon deux ingrédients s'afficheraient pareil), toutes les notes de
substitution traduites (mêmes substitutionId, nom traduit présent
exactement quand le français en a un), nombres des notes conservés ; dans
l'application : chargement à la demande, nom traduit, recherche par un mot
arabe (avec ou sans chadda, hamza), recherche inverse arabe -> id,
substitutions affichées en arabe, recettes « avec / sans » (virgule arabe
« ، », article « ال » collé), écran Ingrédients de droite à gauche sans
débordement à 320 px.
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
AR = re.compile(r"[\u0600-\u06ff]")
AR_MARKS = re.compile(r"[\u064b-\u065f\u0670\u0640]")


def ar_key(v):
    v = AR_MARKS.sub("", unicodedata.normalize("NFD", v.lower()))
    return re.sub(r"[\u0300-\u036f]", "", v).replace("\u0649", "\u064a")


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=PROJECT_ROOT, **k)

    def log_message(self, *a):
        pass


def load(name):
    return json.load(open(f"{PROJECT_ROOT}/data/{name}", encoding="utf-8"))


def main():
    results = []

    def check(label, ok, detail=""):
        results.append(bool(ok))
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {label}{' — ' + str(detail) if detail != '' else ''}")

    catalogue = load("ingredients_catalogue.json")
    ar = load("ingredient_translations_ar.json")
    en = load("ingredient_translations_en.json")
    ids = [e["id"] for e in catalogue]
    check("catalogue : tous les ids traduits, rien en trop", set(ar) == set(ids), (len(ar), len(ids)))
    check("même ordre de clés que l'anglais", list(ar) == list(en))
    empty = [k for k, v in ar.items() if not v.strip()]
    check("aucun nom vide", not empty, empty[:5])
    no_ar = [(k, v) for k, v in ar.items() if not AR.search(v)]
    check("chaque nom contient de l'arabe", not no_ar, no_ar[:5])
    seen, dups = {}, []
    for k, v in ar.items():
        if ar_key(v) in seen:
            dups.append((seen[ar_key(v)], k, v))
        seen.setdefault(ar_key(v), k)
    check("aucune traduction en double (voyelles brèves, chadda, hamza ignorées)", not dups, dups[:5])
    latin_comma = [(k, v) for k, v in ar.items() if re.search(r"[\u0600-\u06ff],", v)]
    check("virgule arabe « ، » (pas de « , » latine après un mot arabe)", not latin_comma, latin_comma[:5])
    stray = [(k, v) for k, v in ar.items() if re.search(r"[\u0400-\u04ff]|[\u0621-\u064a][A-Za-z]{2,}|[A-Za-z]{2,}[\u0621-\u064a]", v)]
    check("aucun fragment cyrillique ou latin collé à un mot arabe", not stray, stray[:5])

    base = load("ingredient_substitutions.json")
    sub_ar = load("ingredient_substitutions_ar.json")
    sub_en = load("ingredient_substitutions_en.json")
    check("substitutions : mêmes substitutionId, même ordre que l'anglais",
          list(sub_ar) == list(sub_en) and set(sub_ar) == {r["substitutionId"] for r in base}, (len(sub_ar), len(base)))
    bad_note = [k for k, v in sub_ar.items() if not AR.search(v.get("note", ""))]
    check("chaque note traduite en arabe", not bad_note, bad_note[:5])
    bad_name = [r["substitutionId"] for r in base if bool(r.get("name")) != ("name" in sub_ar[r["substitutionId"]])
                or ("name" in sub_ar[r["substitutionId"]] and not AR.search(sub_ar[r["substitutionId"]]["name"]))]
    check("nom de substitut traduit exactement quand le français en a un", not bad_name, bad_name[:5])
    lost = []
    for r in base:
        for num in re.findall(r"\d+(?:[.,]\d+)?", r["note"]):
            if num != "50" and num.replace(",", ".") not in sub_ar[r["substitutionId"]]["note"]:
                lost.append((r["substitutionId"], num))
    check("nombres des notes conservés (quantités, durées, pourcentages)", not lost, lost[:5])

    port = find_free_port()
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 320, "height": 800})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(f"http://127.0.0.1:{port}/index.html", timeout=15000)
        page.evaluate("() => appReady")
        r = page.evaluate("""async () => {
            await ensureUiTranslationsLoaded('ar');
            await ensureIngredientTranslationsLoaded('ar');
            setLang('ar');
            const subs = getDisplaySubstitutes('Beurre');
            const tr = (q) => searchIngredientNames(q, 50).map(n => translateIngredientName(n));
            return {
                loaded: Object.keys(INGREDIENT_TRANSLATIONS.ar || {}).length,
                abricot: translateIngredientName('Abricot'),
                collisions: getIngredientTranslationCollisions('ar').size,
                search: tr('طماطم'),
                noShadda: tr('لوز محمص'),
                hamza: tr('ارز'),
                reverse: INGREDIENT_REVERSE_TRANSLATIONS.ar[normalize('مشمش')] || [],
                dir: document.documentElement.dir,
                subs,
            };
        }""")
        check("traductions arabes chargées à la demande", r["loaded"] == len(ids), r["loaded"])
        check("« Abricot » affiché « مشمش »", r["abricot"] == "مشمش", r["abricot"])
        check("aucune collision détectée par l'application (pas de nom français ajouté)", r["collisions"] == 0, r["collisions"])
        check("recherche « طماطم » : résultats contenant طماطم (y compris « الطماطم »)",
              r["search"] and all("طماطم" in s for s in r["search"]) and any("الطماطم" in s for s in r["search"]), r["search"][:5])
        check("recherche sans chadda « لوز محمص » trouve « لوز محمّص »", "لوز محمّص" in r["noShadda"], r["noShadda"][:5])
        check("recherche sans hamza « ارز » trouve « أرز »", "أرز" in r["hamza"], r["hamza"][:5])
        check("recherche inverse : « مشمش » -> ing_000001", "ing_000001" in r["reverse"], r["reverse"])
        check("interface de droite à gauche", r["dir"] == "rtl", r["dir"])
        subs = r["subs"]
        check("substitutions du beurre affichées en arabe (nom et note)",
              subs and all(AR.search(s["nom"]) and AR.search(s["note"]) for s in subs), subs[:3])

        r = page.evaluate("""() => {
            state.screen = 'ingredients'; render();
            return { text: document.querySelector('main').innerText.slice(0, 4000),
                     overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth };
        }""")
        check("écran Ingrédients : noms arabes affichés", AR.search(r["text"]) and "Abricot" not in r["text"], r["text"][:120])
        check("écran Ingrédients : pas de débordement à 320 px", not r["overflow"])

        def screen_search(screen, query):
            return page.evaluate("""([screen, query]) => {
                state.screen = screen; render();
                const input = document.querySelector('main input[type=search]');
                input.value = query; input.dispatchEvent(new Event('input'));
                return [...document.querySelectorAll('.ingredient-manage-row .name')].map(e => e.textContent);
            }""", [screen, query])

        rows = screen_search("ingredients", "لحم بقر")
        check("écran Ingrédients : recherche « لحم بقر » dans les noms arabes", rows and all("لحم بقر" in x for x in rows), rows[:5])
        rows = screen_search("ingredients", "Abricot")
        check("écran Ingrédients : recherche par le nom français toujours possible", "مشمش" in rows, rows[:5])
        rows = screen_search("manageSubstitutions", "زبدة")
        check("écran Substituts : recherche « زبدة » dans les noms arabes", rows and any("زبدة" in x for x in rows), rows[:5])
        # Recherche de recettes par ingrédient (« avec / sans ») : virgule
        # arabe « ، », article « ال » collé au mot (« صلصة الطماطم »).
        r = page.evaluate("""() => {
            const saved = state.recipes;
            const mk = (id, names) => ({ id, name: id, category: 'Plat', ingredients: names.map((n) => ({ name: n, quantity: 1, unit: 'pièce' })) });
            state.recipes = [mk('R1', ['Tomate', 'Oeufs']), mk('R2', ['Boeuf braisé']), mk('R3', ['Sauce tomate'])];
            const run = (withT, withoutT) => {
                state.search = ''; state.recipeTagFilter = ''; state.activeFilter = 'all'; state.recipeCategoryFilter = '';
                state.recipeIngredientWith = withT; state.recipeIngredientWithout = withoutT;
                return filteredRecipes().map((x) => x.id).sort();
            };
            const out = { beef: run('لحم بقر', ''), tomatoEgg: run('طماطم، بيض', ''), tomato: run('طماطم', ''),
                          withArticle: run('الطماطم', ''), noEgg: run('', 'بيض'), fr: run('boeuf', ''),
                          tags: normalizeRecipeTags('سريع، نباتي') };
            state.recipes = saved; state.recipeIngredientWith = ''; state.recipeIngredientWithout = '';
            return out;
        }""")
        check("recettes « avec لحم بقر »", r["beef"] == ["R2"], r["beef"])
        check("recettes « avec طماطم، بيض » (virgule arabe)", r["tomatoEgg"] == ["R1"], r["tomatoEgg"])
        check("recettes « avec طماطم » : trouve aussi « صلصة الطماطم » (article collé)", r["tomato"] == ["R1", "R3"], r["tomato"])
        check("recettes « avec الطماطم » : trouve aussi « طماطم »", r["withArticle"] == ["R1", "R3"], r["withArticle"])
        check("recettes « sans بيض »", r["noEgg"] == ["R2", "R3"], r["noEgg"])
        check("recettes : nom français toujours reconnu (« boeuf »)", r["fr"] == ["R2"], r["fr"])
        check("étiquettes séparées par la virgule arabe", r["tags"] == ["سريع", "نباتي"], r["tags"])

        # Fenêtre de modification : nom affiché en arabe ; enregistrer sans
        # le modifier ne renomme pas l'ingrédient.
        page.evaluate("() => { state.screen = 'ingredients'; render(); openIngredientNameModal('Sucre'); }")
        shown = page.input_value("#modal-ing-rename")
        check("fenêtre d'ingrédient : nom affiché en arabe (« Sucre » -> « سكر »)", shown == "سكر", shown)
        page.click("#modal-confirm")
        page.wait_for_function("() => !document.querySelector('#modal-ing-rename')")
        r = page.evaluate("() => ({ sucre: state.ingredientNames.includes('Sucre'), ar: state.ingredientNames.includes('سكر') })")
        check("enregistrer sans modifier : pas de renommage", r == {"sucre": True, "ar": False}, r)

        page.evaluate("async () => { await ensureIngredientTranslationsLoaded('en'); setLang('en'); }")
        rows = screen_search("ingredients", "beef")
        check("écran Ingrédients en anglais : « beef » trouvé (même correction)", rows and all("beef" in x.lower() for x in rows), rows[:3])

        r = page.evaluate("() => { setLang('fr'); return translateIngredientName('Abricot'); }")
        check("retour au français : « Abricot »", r == "Abricot", r)
        check("aucune erreur JS", not errors, errors)
        browser.close()
    httpd.shutdown()
    ok = all(results)
    print("\n=== Résumé ===")
    print("TOUT CORRECT" if ok else "ÉCHECS DÉTECTÉS")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
