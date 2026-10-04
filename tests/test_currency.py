"""
Devise configurable (TESTS_NON_REGRESSION.md, entrée 157 ; intégration du
chinois en cours sur une branche, pas encore sur main).

Devise par défaut sans choix de l'utilisateur : yuan en chinois, euro
dans les autres langues (choix du 4 octobre 2026).

Le symbole « € » était écrit en dur dans les textes de coût (recette,
comparaison, statistiques, total des courses). Vérifie : euro par défaut,
format inchangé en français (« 1,20 € ») ; aucun « € » restant dans les
textes de coût des 10 langues (hors clause juridique) ; choix de la
devise dans la fenêtre d'un ingrédient (liste, enregistrement immédiat
dans IndexedDB, conservé après rechargement) ; montants affichés avec le
symbole et sa place selon la langue (« $1.20 » en anglais, « ¥1.20 » en
chinois) sur les écrans recette, courses, comparaison et statistiques ;
montants non convertis ; fenêtre sans débordement à 320 px en chinois.
"""
import http.server
import json
import re
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = "/home/user/mes-recettes-mobile"
LANGS = ["fr", "en", "es", "de", "id", "pt", "it", "sv", "no", "zh"]
COST_KEYS = ["stats_avg_cost_line", "recipe_cost_line", "compare_cost_value"]


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=PROJECT_ROOT, **k)

    def log_message(self, *a):
        pass


SEED = """async () => {
    const base = { category: 'Plat', description: '', notes: '', photo: null, createdAt: '2026-01-01T00:00:00.000Z', cookLog: [], allergens: [] };
    await storePut('recipes', { ...base, id: 'ra', name: 'Alpha', defaultPersons: 4, timesCooked: 1,
        ingredients: [{ name: 'Farine', quantity: 100, unit: 'g' }, { name: 'Lait', quantity: 10, unit: 'cl' }] });
    await storePut('recipes', { ...base, id: 'rb', name: 'Bravo', defaultPersons: 2, timesCooked: 1,
        ingredients: [{ name: 'Farine', quantity: 50, unit: 'g' }] });
    // Farine 2 /kg, lait 1 /L : Alpha pour 4 = 1,20, soit 0,30 par personne.
    await setIngredientOverride('Farine', [], null, { amount: 2, unit: 'kg' }, []);
    await setIngredientOverride('Lait', [], null, { amount: 1, unit: 'L' }, []);
    await storePut('shopping', { id: 's1', name: 'Farine', quantity: 1, unit: 'kg', checked: false });
}"""

SCREENS = """() => {
    const out = {};
    const text = () => document.querySelector('main').innerText.replace(/\\s+/g, ' ');
    state.currentRecipeId = 'ra'; state.viewPersons = 4; state.screen = 'recipe'; render();
    const card = document.querySelector('.recipe-cost-card');
    out.recipe = card ? card.textContent.replace(/\\s+/g, ' ').trim() : '';
    state.screen = 'shopping'; render(); out.shopping = text();
    state.screen = 'statistics'; render(); out.stats = text();
    out.compare = t('compare_cost_value', { total: formatPrice(1.2), persons: '4' });
    return out;
}"""


def main():
    results = []

    def check(label, ok, detail=""):
        results.append(bool(ok))
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {label}{' — ' + str(detail) if detail != '' else ''}")

    # Textes : plus aucun « € » écrit en dur dans les textes de coût.
    fr_src = open(f"{PROJECT_ROOT}/i18n.js", encoding="utf-8").read()
    left = []
    for lang in LANGS:
        for key in COST_KEYS + ["currency_label", "currency_hint"]:
            if lang == "fr":
                m = re.search(r'\n    %s: ("(?:[^"\\]|\\.)*")' % key, fr_src)
                value = json.loads(m.group(1)) if m else None
            else:
                value = json.load(open(f"{PROJECT_ROOT}/i18n/{lang}.json", encoding="utf-8")).get(key)
            if value is None or (key in COST_KEYS and re.search(r"€|\bkr\b", value)):
                left.append((lang, key, value))
    check("textes de coût sans symbole écrit en dur, libellés de devise dans les 10 langues", not left, left[:5])
    app = open(f"{PROJECT_ROOT}/app.js", encoding="utf-8").read()
    check("app.js : plus de « € » collé à un montant", not re.search(r"\} €|€\$\{", app))

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
        page.evaluate(SEED)
        page.reload()
        page.evaluate("() => appReady")
        page.evaluate("() => setLang('fr')")

        r = page.evaluate("""async () => {
            const fr = currentCurrency();
            await ensureUiTranslationsLoaded('zh'); setLang('zh');
            const zh = currentCurrency(), zhText = formatPrice(1.2);
            setLang('fr');
            return { saved: state.currency, fr, zh, zhText };
        }""")
        check("sans choix : euro en français", r["saved"] is None and r["fr"] == "EUR", r)
        check("sans choix : yuan en chinois (« ¥1.20 »)", r["zh"] == "CNY" and r["zhText"] == "¥1.20", r)
        r = page.evaluate(SCREENS)
        nb = lambda s: s.replace(" ", " ").replace(" ", " ")
        check("français, euro : recette « 1,20 € … 0,30 € »", "1,20 €" in nb(r["recipe"]) and "0,30 €" in nb(r["recipe"]), r["recipe"])
        check("français, euro : total des courses « 2,00 € »", "2,00 €" in nb(r["shopping"]), nb(r["shopping"])[:200])
        # Moyenne par personne : Alpha 0,30, Bravo 0,10 -> 0,20.
        check("français, euro : statistiques « 0,20 € (sur 2 recette(s)… »", "0,20 € (sur 2 recette" in nb(r["stats"]),
              re.findall(r".{0,20}€.{0,30}", nb(r["stats"])))
        check("français, euro : comparaison « 1,20 € (4 pers.) »", nb(r["compare"]) == "1,20 € (4 pers.)", r["compare"])

        # Choix dans la fenêtre d'un ingrédient.
        page.evaluate("() => { state.screen = 'ingredients'; render(); openIngredientNameModal('Farine'); }")
        opts = page.evaluate("() => [...document.querySelectorAll('#modal-price-currency option')].map(o => [o.value, o.textContent, o.selected])")
        check("liste des devises dans la fenêtre de prix (euro sélectionné)",
              len(opts) >= 10 and [o for o in opts if o[2]][0][0] == "EUR" and any("$" in o[1] for o in opts), opts[:3])
        page.select_option("#modal-price-currency", "USD")
        page.wait_for_function("() => state.currency === 'USD'")
        page.click("#modal-cancel")
        saved = None
        for _ in range(50):
            saved = page.evaluate("() => kvGet('currency')")
            if saved == "USD":
                break
            page.wait_for_timeout(100)
        check("devise enregistrée tout de suite (même si la fenêtre est annulée)", saved == "USD", saved)
        page.reload()
        page.evaluate("() => appReady")
        page.evaluate("() => setLang('fr')")
        check("devise conservée après rechargement", page.evaluate("() => state.currency") == "USD")
        r = page.evaluate(SCREENS)
        check("français, dollar : « 1,20 $US » ou « 1,20 $ », plus d'euro",
              "1,20" in r["recipe"] and "$" in r["recipe"] and "€" not in r["recipe"] + r["shopping"] + r["compare"], r["recipe"])

        page.evaluate("async () => { await ensureUiTranslationsLoaded('en'); setLang('en'); }")
        r = page.evaluate(SCREENS)
        check("anglais, dollar : « $1.20 … $0.30 »", "$1.20" in r["recipe"] and "$0.30" in r["recipe"], r["recipe"])
        check("anglais, dollar : total des courses « $2.00 »", "$2.00" in r["shopping"], "")

        page.evaluate("async () => { await setCurrency('CNY'); await ensureUiTranslationsLoaded('zh'); await ensureIngredientTranslationsLoaded('zh'); setLang('zh'); }")
        r = page.evaluate(SCREENS)
        check("chinois, yuan : « ¥1.20 … ¥0.30 », montants non convertis", "¥1.20" in r["recipe"] and "¥0.30" in r["recipe"], r["recipe"])
        check("chinois, yuan : comparaison « ¥1.20（4 人份） »", r["compare"] == "¥1.20（4 人份）", r["compare"])
        check("chinois : aucun « € » sur les écrans de coût", "€" not in r["recipe"] + r["shopping"] + r["stats"], "")
        page.evaluate("() => { state.screen = 'ingredients'; render(); openIngredientNameModal('Farine'); }")
        r = page.evaluate("""() => ({
            label: document.querySelector('label[for=modal-price-currency]').textContent,
            selected: document.querySelector('#modal-price-currency').value,
            sample: document.querySelector('#modal-price-currency option[value=CNY]').textContent,
            overflow: document.querySelector('.modal-sheet').scrollWidth > document.querySelector('.modal-sheet').clientWidth,
        })""")
        check("chinois : libellé « 货币 », yuan sélectionné, nom de devise en chinois",
              r["label"] == "货币" and r["selected"] == "CNY" and "人民币" in r["sample"], r)
        check("chinois : fenêtre sans débordement à 320 px", not r["overflow"])
        page.click("#modal-cancel")

        r = page.evaluate("async () => { await setCurrency('EUR'); return [currentCurrency(), formatPrice(1.2)]; }")
        check("euro choisi explicitement : reste l'euro en chinois", r == ["EUR", "€1.20"], r)
        r = page.evaluate("async () => { await setCurrency('XXX'); const zh = currentCurrency(); setLang('fr'); return [state.currency, zh, currentCurrency()]; }")
        check("code inconnu : devise par défaut de la langue", r == [None, "CNY", "EUR"], r)
        page.evaluate("() => setLang('fr')")
        check("aucune erreur JS", not errors, errors)
        browser.close()
    httpd.shutdown()
    ok = all(results)
    print("\n=== Résumé ===")
    print("TOUT CORRECT" if ok else "ÉCHECS DÉTECTÉS")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
