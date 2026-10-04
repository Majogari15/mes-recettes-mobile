"""
Accueil enrichi, repris de l'app Windows (TESTS_NON_REGRESSION.md, entrée
151) : repas prévus aujourd'hui (seulement si le planning de la semaine
contient au moins une recette), recette du jour (la même toute la
journée, nouveau tirage le lendemain ou si elle est supprimée), recettes
consultées récemment (8 mémorisées, 5 affichées, la plus récente
d'abord, sans doublon). Stockage local indisponible : l'accueil
s'affiche quand même. Pas de débordement à 320 px.
"""
import http.server
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = "/home/user/mes-recettes-mobile"


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=PROJECT_ROOT, **k)

    def log_message(self, *a):
        pass


def main():
    port = find_free_port()
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    results = []

    def check(label, ok, detail=""):
        results.append(bool(ok))
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {label}{' — ' + str(detail) if detail != '' else ''}")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 320, "height": 900})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(f"http://127.0.0.1:{port}/index.html", timeout=15000)
        page.evaluate("() => appReady")
        page.evaluate("async () => { await ensureUiTranslationsLoaded('fr'); setLang('fr'); }")

        def home():
            return page.evaluate("""() => {
                state.screen = 'home'; render();
                const q = (s) => document.querySelector(s);
                return {
                    today: q('.home-today') ? [...document.querySelectorAll('.home-today-row')].map(r => r.innerText.replace(/\\s+/g, ' ').trim()) : null,
                    todayEmpty: !!q('.home-today-empty'),
                    daily: q('.home-daily .name') ? q('.home-daily .name').textContent : null,
                    recent: [...document.querySelectorAll('.home-recent .chip')].map(c => c.textContent),
                    overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
                };
            }""")

        r = home()
        check("aucune recette : rien d'affiché", r["today"] is None and r["daily"] is None and r["recent"] == [], r)

        page.evaluate("""async () => {
            const base = { category: 'Plat', ingredients: [], createdAt: '2026-01-01', cookLog: [], defaultPersons: 4 };
            for (let i = 0; i < 10; i++) await storePut('recipes', { ...base, id: 'r' + i, name: 'Recette ' + i, defaultPersons: 2 + (i % 3) });
            state.recipes = await storeAll('recipes');
            state.weeklyPlan = {};
        }""")
        r = home()
        check("planning vide : pas de bloc « Aujourd'hui »", r["today"] is None, r["today"])
        first = r["daily"]
        check("recette du jour affichée", first and first.startswith("Recette "), first)
        check("même recette du jour au réaffichage", home()["daily"] == first)

        # Nouveau jour -> nouveau tirage mémorisé à la nouvelle date.
        r2 = page.evaluate("""() => {
            const tomorrow = new Date(Date.now() + 86400000);
            const d = getDailyRecipe(tomorrow);
            const saved = JSON.parse(localStorage.getItem('dailyRecipe'));
            return { date: saved.date, expected: localDateKey(tomorrow), id: saved.id, same: d.id === saved.id };
        }""")
        check("lendemain : nouveau tirage mémorisé pour ce jour", r2["date"] == r2["expected"] and r2["same"], r2)
        # Recette du jour imposée (r5) pour un test reproductible : le
        # tirage au hasard pouvait tomber sur une recette utilisée plus bas.
        page.evaluate("() => localStorage.setItem('dailyRecipe', JSON.stringify({ date: localDateKey(), id: 'r5' }))")
        first = home()["daily"]
        check("recette du jour mémorisée relue", first == "Recette 5", first)
        page.evaluate("""async (name) => {
            const r = state.recipes.find(x => x.name === name);
            await storeDelete('recipes', r.id); state.recipes = state.recipes.filter(x => x.id !== r.id);
        }""", first)
        r = home()
        check("recette du jour supprimée : une autre la remplace", r["daily"] and r["daily"] != first, (first, r["daily"]))

        # Planning : une recette un autre jour -> bloc avec « Rien de prévu ».
        page.evaluate("""() => {
            const today = WEEKDAYS[(new Date().getDay() + 6) % 7];
            const other = WEEKDAYS.find(d => d !== today);
            state.weeklyPlan = { [other]: { 'Dîner': [{ recipeId: 'r1', persons: 3 }] } };
        }""")
        r = home()
        check("planning utilisé mais rien aujourd'hui : « Rien de prévu »", r["today"] == [] and r["todayEmpty"], r)
        page.click(".home-today-empty")
        check("appui -> écran Planning", page.evaluate("() => state.screen") == "planning")

        page.evaluate("""() => {
            const today = WEEKDAYS[(new Date().getDay() + 6) % 7];
            state.weeklyPlan = { [today]: {
                'Dîner': [{ recipeId: 'r1', persons: 3 }],
                'Déjeuner': [{ recipeId: 'r2', persons: 6 }, { recipeId: 'supprimée', persons: 2 }],
            } };
        }""")
        r = home()
        check("repas du jour dans l'ordre des repas, recette supprimée ignorée",
              r["today"] == ["Déjeuner Recette 2 6 pers.", "Dîner Recette 1 3 pers."], r["today"])
        page.locator(".home-today-row").nth(0).click()
        r = page.evaluate("() => ({ screen: state.screen, id: state.currentRecipeId, persons: state.viewPersons })")
        check("appui -> fiche avec le nombre de personnes prévu", r == {"screen": "recipe", "id": "r2", "persons": 6}, r)

        # Consultées récemment.
        page.evaluate("""() => {
            localStorage.removeItem('recentRecipeIds');
            for (const id of ['r3', 'r4', 'r5', 'r6', 'r7', 'r8', 'r9', 'r3', 'r1']) {
                state.currentRecipeId = id; state.screen = 'recipe'; render();
            }
        }""")
        stored = page.evaluate("() => JSON.parse(localStorage.getItem('recentRecipeIds'))")
        # r5 a été supprimée plus haut (ancienne recette du jour) : la
        # fiche n'existe plus, elle n'est donc pas mémorisée.
        existing_ids = set(page.evaluate("() => state.recipes.map(r => r.id)"))
        expected = [i for i in ["r1", "r3", "r9", "r8", "r7", "r6", "r5", "r4"] if i in existing_ids]
        check("la plus récente d'abord, sans doublon, recette inexistante ignorée", stored == expected, (stored, expected))
        over = page.evaluate("""() => {
            for (let i = 0; i < 12; i++) recordRecentRecipe('x' + i);
            return JSON.parse(localStorage.getItem('recentRecipeIds')).length;
        }""")
        check("8 mémorisées au plus", over == 8, over)
        page.evaluate("(ids) => { localStorage.setItem('recentRecipeIds', JSON.stringify(ids)); }", expected)
        r = home()
        check("5 affichées sur l'accueil", r["recent"] == ["Recette " + i[1:] for i in expected[:5]], r["recent"])
        page.evaluate("async () => { await storeDelete('recipes', 'r3'); state.recipes = state.recipes.filter(x => x.id !== 'r3'); }")
        r = home()
        check("recette supprimée retirée des récentes", "Recette 3" not in r["recent"] and len(r["recent"]) == 5, r["recent"])
        page.locator(".home-recent .chip").nth(1).click()
        check("appui sur une récente -> sa fiche", page.evaluate("() => state.currentRecipeId") == [i for i in expected if i != "r3"][1])

        r = home()
        check("pas de débordement à 320 px", not r["overflow"])

        # Stockage local indisponible.
        page.evaluate("""() => {
            // Panne limitée aux clés de l'accueil enrichi : d'autres
            // lectures plus anciennes de l'accueil (bandeau d'installation,
            // rappel de sauvegarde) ne sont pas protégées, hors sujet ici.
            const keys = ['recentRecipeIds', 'dailyRecipe'];
            const get = Storage.prototype.getItem, set = Storage.prototype.setItem;
            Storage.prototype.getItem = function (k) { if (keys.includes(k)) throw new Error('bloqué'); return get.call(this, k); };
            Storage.prototype.setItem = function (k, v) { if (keys.includes(k)) throw new Error('bloqué'); return set.call(this, k, v); };
        }""")
        r = page.evaluate("""() => {
            try { state.screen = 'home'; render(); state.currentRecipeId = 'r1'; state.screen = 'recipe'; render(); state.screen = 'home'; render(); return { ok: true, daily: !!document.querySelector('.home-daily') }; }
            catch (e) { return { ok: false, err: String(e) }; }
        }""")
        check("stockage refusé pour ces réglages : accueil et fiche s'affichent quand même", r.get("ok") and r.get("daily"), r)

        check("aucune erreur JS", not errors, errors)
        browser.close()
    httpd.shutdown()
    ok = all(results)
    print("\n=== Résumé ===")
    print("TOUT CORRECT" if ok else "ÉCHECS DÉTECTÉS")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
