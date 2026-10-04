"""
Chinois simplifié — catalogue d'ingrédients et substitutions
(TESTS_NON_REGRESSION.md, entrée 154 ; intégration en cours sur une
branche, pas encore sur main).

Vérifie : les ~10 000 noms du catalogue traduits (mêmes ids, dans le même
ordre que l'anglais, aucun vide, chacun contient du chinois, aucune
traduction en double — sinon l'application ajouterait le nom français
entre parenthèses), toutes les notes de substitution traduites (mêmes
substitutionId, nom traduit présent exactement quand le français en a un),
nombres des notes conservés ; dans l'application : chargement à la
demande, nom traduit, recherche par un mot chinois (sans espace entre les
mots), recherche inverse chinois -> id, substitutions affichées en
chinois, écran Ingrédients sans débordement à 320 px.
"""
import http.server
import json
import re
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = "/home/user/mes-recettes-mobile"
CJK = re.compile(r"[一-鿿]")


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
    zh = load("ingredient_translations_zh.json")
    en = load("ingredient_translations_en.json")
    ids = [e["id"] for e in catalogue]
    check("catalogue : tous les ids traduits, rien en trop", set(zh) == set(ids), (len(zh), len(ids)))
    check("même ordre de clés que l'anglais", list(zh) == list(en))
    empty = [k for k, v in zh.items() if not v.strip()]
    check("aucun nom vide", not empty, empty[:5])
    no_cjk = [(k, v) for k, v in zh.items() if not CJK.search(v)]
    check("chaque nom contient du chinois", not no_cjk, no_cjk[:5])
    seen = {}
    dups = [(seen.setdefault(v, k), k, v) for k, v in zh.items() if v in seen or seen.setdefault(v, k) is None]
    check("aucune traduction en double", not dups, dups[:5])
    half_width = [(k, v) for k, v in zh.items() if re.search(r"[一-鿿], |[一-鿿] \(", v)]
    check("ponctuation chinoise (pas de « , » ni « ( » à l'anglaise après un caractère chinois)", not half_width, half_width[:5])

    base = load("ingredient_substitutions.json")
    sub_zh = load("ingredient_substitutions_zh.json")
    sub_en = load("ingredient_substitutions_en.json")
    check("substitutions : mêmes substitutionId, même ordre que l'anglais",
          list(sub_zh) == list(sub_en) and set(sub_zh) == {r["substitutionId"] for r in base}, (len(sub_zh), len(base)))
    bad_note = [k for k, v in sub_zh.items() if not CJK.search(v.get("note", ""))]
    check("chaque note traduite en chinois", not bad_note, bad_note[:5])
    bad_name = [r["substitutionId"] for r in base if bool(r.get("name")) != ("name" in sub_zh[r["substitutionId"]])
                or ("name" in sub_zh[r["substitutionId"]] and not CJK.search(sub_zh[r["substitutionId"]]["name"]))]
    check("nom de substitut traduit exactement quand le français en a un", not bad_name, bad_name[:5])
    lost = []
    for r in base:
        for num in re.findall(r"\d+(?:[.,]\d+)?", r["note"]):
            if num != "50" and num.replace(",", ".") not in sub_zh[r["substitutionId"]]["note"]:
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
            await ensureUiTranslationsLoaded('zh');
            await ensureIngredientTranslationsLoaded('zh');
            setLang('zh');
            const subs = getDisplaySubstitutes('Beurre');
            return {
                loaded: Object.keys(INGREDIENT_TRANSLATIONS.zh || {}).length,
                abricot: translateIngredientName('Abricot'),
                collisions: getIngredientTranslationCollisions('zh').size,
                search: searchIngredientNames('番茄', 50).map(n => translateIngredientName(n)),
                reverse: INGREDIENT_REVERSE_TRANSLATIONS.zh[normalize('杏')] || [],
                subs,
            };
        }""")
        check("traductions chinoises chargées à la demande", r["loaded"] == len(ids), r["loaded"])
        check("« Abricot » affiché « 杏 »", r["abricot"] == "杏", r["abricot"])
        check("aucune collision détectée par l'application (pas de nom français ajouté)", r["collisions"] == 0, r["collisions"])
        check("recherche « 番茄 » (sans espace) : résultats contenant 番茄",
              r["search"] and all("番茄" in s for s in r["search"]), r["search"][:5])
        check("recherche inverse : « 杏 » -> ing_000001", "ing_000001" in r["reverse"], r["reverse"])
        subs = r["subs"]
        check("substitutions du beurre affichées en chinois (nom et note)",
              subs and all(CJK.search(s["nom"]) and CJK.search(s["note"]) for s in subs), subs[:3])

        r = page.evaluate("""() => {
            state.screen = 'ingredients'; render();
            return { text: document.querySelector('main').innerText.slice(0, 4000),
                     overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth };
        }""")
        check("écran Ingrédients : noms chinois affichés", CJK.search(r["text"]) and "Abricot" not in r["text"], r["text"][:120])
        check("écran Ingrédients : pas de débordement à 320 px", not r["overflow"])

        def screen_search(screen, query):
            return page.evaluate("""([screen, query]) => {
                state.screen = screen; render();
                const input = document.querySelector('main input[type=search]');
                input.value = query; input.dispatchEvent(new Event('input'));
                return [...document.querySelectorAll('.ingredient-manage-row .name')].map(e => e.textContent);
            }""", [screen, query])

        rows = screen_search("ingredients", "牛肉")
        check("écran Ingrédients : recherche « 牛肉 » dans les noms chinois", rows and all("牛肉" in x for x in rows), rows[:5])
        rows = screen_search("ingredients", "Abricot")
        check("écran Ingrédients : recherche par le nom français toujours possible", "杏" in rows, rows[:5])
        rows = screen_search("manageSubstitutions", "黄油")
        check("écran Substituts : recherche « 黄油 » dans les noms chinois", rows and any("黄油" in x for x in rows), rows[:5])
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
