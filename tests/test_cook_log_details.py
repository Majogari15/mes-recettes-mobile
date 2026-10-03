"""
Journal de cuisine complet, comme l'app Windows (TESTS_NON_REGRESSION.md,
entrée 143) : nombre de personnes, appréciation en étoiles, note
personnelle et commentaire pour chaque cuisson, affichés dans le journal
avec l'appréciation moyenne. Champs échangés avec Windows (cook_log_full :
date, note, comment, rating, persons, photo) et réparés à l'import ou à la
restauration d'une sauvegarde.
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
        page = browser.new_page(viewport={"width": 320, "height": 800})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(f"http://127.0.0.1:{port}/index.html", timeout=15000)
        page.evaluate("() => appReady")
        page.evaluate("async () => { await ensureUiTranslationsLoaded('fr'); setLang('fr'); }")
        page.evaluate("""async () => {
            await storePut('recipes', { id: 'r1', name: 'Tarte', category: 'Dessert', difficulty: 'Facile', defaultPersons: 4,
                ingredients: [], description: '', notes: '', photo: null, createdAt: '2026-01-01T00:00:00.000Z',
                cookLog: [{ date: '2026-01-02T10:00:00.000Z', note: 'Ancienne entrée', photo: null }], timesCooked: 1 });
            state.recipes = await storeAll('recipes');
            state.currentRecipeId = 'r1'; state.viewPersons = 6; state.screen = 'recipe'; render();
        }""")

        def stored_log():
            return page.evaluate("async () => (await storeAll('recipes')).find(r => r.id === 'r1').cookLog.map(e => ({ note: e.note, comment: e.comment, rating: e.rating, persons: e.persons }))")

        def click_cooked():
            label = page.evaluate("() => t('recipe_cooked_button')")
            page.get_by_role("button", name=label, exact=True).click()
            page.wait_for_selector("#cooklog-persons")

        # --- Ajout complet ---
        click_cooked()
        check("personnes préremplies avec le nombre affiché (6)", page.input_value("#cooklog-persons") == "6", page.input_value("#cooklog-persons"))
        page.click('#cooklog-rating-stars [data-star="3"]')
        page.click('#cooklog-rating-stars [data-star="3"]')
        check("appui sur l'étoile choisie : appréciation effacée", page.evaluate("() => document.querySelector('#cooklog-rating-stars').dataset.value") == "0")
        page.click('#cooklog-rating-stars [data-star="4"]')
        page.fill("#cooklog-note", "Très bonne")
        page.fill("#cooklog-comment", "Un peu trop sucrée")
        overflow = page.evaluate("() => document.documentElement.scrollWidth > document.documentElement.clientWidth")
        check("fenêtre d'ajout : pas de débordement à 320 px", not overflow)
        page.click("#cooklog-save")
        page.wait_for_selector("#cooklog-persons", state="detached")
        log = stored_log()
        check("entrée enregistrée avec tous les détails", log[0] == {"note": "Très bonne", "comment": "Un peu trop sucrée", "rating": 4, "persons": 6}, log[0])
        check("ancienne entrée intacte", log[1]["note"] == "Ancienne entrée" and len(log) == 2, log)

        # --- « Passer » ---
        click_cooked()
        page.fill("#cooklog-persons", "2")
        page.click('#cooklog-rating-stars [data-star="5"]')
        page.fill("#cooklog-comment", "ignoré")
        page.click("#cooklog-skip")
        page.wait_for_selector("#cooklog-persons", state="detached")
        log = stored_log()
        check("« Passer » : personnes gardées, détails ignorés", log[0] == {"note": "", "comment": "", "rating": 0, "persons": 2}, log[0])
        tc = page.evaluate("async () => (await storeAll('recipes')).find(r => r.id === 'r1').timesCooked")
        check("compteur de cuissons incrémenté", tc == 3, tc)

        # --- Journal ---
        label = page.evaluate("() => t('cooklog_view_button')")
        page.get_by_role("button", name=label).click()
        page.wait_for_selector("#cooklog-entries-holder")
        r = page.evaluate("""() => ({
            summary: (document.querySelector('.cooklog-rating-summary') || {}).textContent,
            cards: [...document.querySelectorAll('#cooklog-entries-holder .card')].map(c => c.innerText.replace(/\\s+/g, ' ').trim()),
        })""")
        check("appréciation moyenne (seules les cuissons notées comptent)", r["summary"] and "4/5" in r["summary"] and "(1 " in r["summary"], r["summary"])
        full = r["cards"][1]
        check("carte complète : personnes, étoiles, note et commentaire titrés",
              "Pour 6 personne(s)" in full and "★★★★☆" in full and "Note : Très bonne" in full and "Commentaire : Un peu trop sucrée" in full, full)
        check("carte « Passer » : personnes seules, pas d'étoiles", "Pour 2 personne(s)" in r["cards"][0] and "★" not in r["cards"][0], r["cards"][0])
        check("ancienne entrée : note sans intitulé", "Ancienne entrée" in r["cards"][2] and "Note :" not in r["cards"][2], r["cards"][2])
        overflow = page.evaluate("() => document.documentElement.scrollWidth > document.documentElement.clientWidth")
        check("journal : pas de débordement à 320 px", not overflow)

        # --- Modification ---
        page.locator("#cooklog-entries-holder .card").nth(1).locator(".edit").click()
        page.wait_for_selector("#cooklog-persons")
        r = page.evaluate("() => ({ p: document.querySelector('#cooklog-persons').value, s: document.querySelector('#cooklog-rating-stars').dataset.value, c: document.querySelector('#cooklog-comment').value })")
        check("modification : valeurs reprises", r == {"p": "6", "s": "4", "c": "Un peu trop sucrée"}, r)
        page.fill("#cooklog-persons", "")
        page.click('#cooklog-rating-stars [data-star="2"]')
        page.fill("#cooklog-comment", "Moins de sucre la prochaine fois")
        page.click("#cooklog-save")
        page.wait_for_function("() => !document.querySelector('#cooklog-persons')")
        log = stored_log()
        check("modification enregistrée (personnes vides -> null)", log[1] == {"note": "Très bonne", "comment": "Moins de sucre la prochaine fois", "rating": 2, "persons": None}, log[1])

        # --- Échange avec l'app Windows ---
        r = page.evaluate("""async () => {
            const rec = state.recipes.find(r => r.id === 'r1');
            const { json } = await recipeToSharedFormat(rec);
            const back = recipeFromSharedFormat(json, new Map());
            const fromWin = recipeFromSharedFormat({ name: 'W', ingredients: [], cook_log_full: [
                { date: '2026-03-01T12:00:00', note: 'n', comment: 'c', rating: 4, persons: 3, photo: null, extra: 'gardé' },
                { date: '2026-03-02T12:00:00', note: null, comment: 5, rating: '9', persons: 'x' },
                'pas un objet',
            ] }, new Map());
            const legacy = recipeFromSharedFormat({ name: 'L', ingredients: [], cooked_dates: ['2026-01-01'] }, new Map());
            return { exported: json.cook_log_full[1], sameBack: JSON.stringify(back.cookLog) === JSON.stringify(rec.cookLog.map(normalizeCookLogEntry)), fromWin: fromWin.cookLog, legacy: legacy.cookLog };
        }""")
        e = r["exported"]
        check("export : commentaire, appréciation, personnes envoyés", e["comment"] == "Moins de sucre la prochaine fois" and e["rating"] == 2 and e["persons"] is None, e)
        check("aller-retour sans perte", r["sameBack"])
        w = r["fromWin"]
        check("import Windows : entrée valide gardée telle quelle (champ inconnu inclus)", len(w) == 2 and w[0]["comment"] == "c" and w[0]["rating"] == 4 and w[0]["persons"] == 3 and w[0]["extra"] == "gardé", w[0] if w else w)
        check("import Windows : valeurs invalides réparées", w[1]["note"] == "" and w[1]["comment"] == "" and w[1]["rating"] == 5 and w[1]["persons"] is None, w[1])
        check("ancien format (cooked_dates seules) toujours lu", len(r["legacy"]) == 1 and r["legacy"][0]["date"] == "2026-01-01", r["legacy"])

        # --- Sauvegarde ---
        r = page.evaluate("""() => {
            const report = { structuralFixes: 0, numbersFixed: 0, photosRemoved: 0 };
            const c = sanitizeBackupItem({ id: 'x', name: 'X', ingredients: [], cookLog: [
                { date: 'd1', note: 'a', rating: 9, persons: -2, comment: 3 },
                { date: 'd2', note: 'b', photo: null },
                { date: 'd3', note: 'c', rating: 3, persons: 4, comment: 'ok' },
            ] }, 'recipes', report);
            return { log: c.cookLog, fixes: report.structuralFixes };
        }""")
        log = r["log"]
        check("sauvegarde : valeurs hors limites réparées", log[0]["rating"] == 5 and log[0]["persons"] is None and log[0]["comment"] == "", log[0])
        check("sauvegarde : entrée ancienne non modifiée (aucun champ ajouté)", log[1] == {"date": "d2", "note": "b", "photo": None}, log[1])
        check("sauvegarde : entrée valide intacte, une seule réparation comptée", log[2] == {"date": "d3", "note": "c", "rating": 3, "persons": 4, "comment": "ok"} and r["fixes"] == 1, (log[2], r["fixes"]))

        check("aucune erreur JS", not errors, errors)
        browser.close()
    httpd.shutdown()
    ok = all(results)
    print("\n=== Résumé ===")
    print("TOUT CORRECT" if ok else "ÉCHECS DÉTECTÉS")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
