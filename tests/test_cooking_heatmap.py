"""
Calendrier des cuissons dans les Statistiques, repris de l'app Windows
(TESTS_NON_REGRESSION.md, entrée 152).

Vérifie : comptage par jour (toutes recettes confondues), niveaux 0/1/2/3+,
période de 12 mois (une cuisson plus ancienne et une date invalide
ignorées), lundi en haut de chaque colonne, aujourd'hui en dernière case,
résumé texte, détail au toucher (date, nombre, recettes), libellés
accessibles, défilement positionné sur les semaines récentes, échelle de
couleurs différente en thème sombre, pas de débordement à 320 px.
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


SEED = """async () => {
    const at = (daysAgo) => { const d = new Date(); d.setHours(12, 0, 0, 0); d.setDate(d.getDate() - daysAgo); return d.toISOString(); };
    const e = (daysAgo) => ({ date: at(daysAgo), note: '', photo: null });
    const base = { category: 'Plat', ingredients: [], createdAt: '2026-01-01' };
    await storePut('recipes', { ...base, id: 'a', name: 'Tarte', cookLog: [e(0), e(1), e(3), e(3), e(3), e(400), { date: 'pas une date', note: '' }], timesCooked: 7 });
    await storePut('recipes', { ...base, id: 'b', name: 'Soupe', cookLog: [e(1), e(3)], timesCooked: 2 });
    state.recipes = await storeAll('recipes');
    state.screen = 'statistics'; render();
}"""


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
        page.evaluate(SEED)
        page.wait_for_selector(".heatmap-card")

        r = page.evaluate("""() => {
            const key = (daysAgo) => { const d = new Date(); d.setDate(d.getDate() - daysAgo); return cookingDayKey(d); };
            const cell = (k) => document.querySelector(`.heatmap-grid [data-day="${k}"]`);
            const level = (c) => c ? [...c.classList].find(x => /^heatmap-l\\d$/.test(x)) : null;
            const days = [...document.querySelectorAll('.heatmap-grid [data-day]')];
            const firstCol = document.querySelector('.heatmap-week');
            const firstReal = [...firstCol.children];
            return {
                summary: document.querySelector('.heatmap-summary').textContent,
                l0: level(cell(key(0))), l1: level(cell(key(1))), l3: level(cell(key(3))), l2day: level(cell(key(2))),
                todayLast: days[days.length - 1].dataset.day === key(0),
                count: days.length,
                weeks: document.querySelectorAll('.heatmap-week').length,
                mondayTop: (() => { const col = document.querySelectorAll('.heatmap-week')[10]; const c = col.querySelector('[data-day]'); return c ? new Date(c.dataset.day + 'T12:00:00').getDay() : null; })(),
                buttons: document.querySelectorAll('.heatmap-grid button.heatmap-cell').length,
                label3: cell(key(3)).getAttribute('aria-label'),
            };
        }""")
        check("résumé : 7 cuissons sur 3 jours (plus ancienne que 12 mois et date invalide ignorées)",
              r["summary"].startswith("7 cuisson(s) sur 3 jour(s)"), r["summary"])
        check("niveaux : aujourd'hui 1, hier 2, il y a 3 jours 3+ (4 cuissons), jour vide 0",
              (r["l0"], r["l1"], r["l3"], r["l2day"]) == ("heatmap-l1", "heatmap-l2", "heatmap-l3", "heatmap-l0"), r)
        check("aujourd'hui = dernière case", r["todayLast"])
        check("53 semaines, environ 365 jours affichés", r["weeks"] == 53 and 364 <= r["count"] <= 366, (r["weeks"], r["count"]))
        check("lundi en haut de chaque colonne", r["mondayTop"] == 1, r["mondayTop"])
        check("seuls les jours avec cuisson sont des boutons (clavier)", r["buttons"] == 3, r["buttons"])
        check("libellé accessible : date, nombre et recettes regroupées", "4 cuisson(s) — Tarte ×3, Soupe" in r["label3"], r["label3"])

        page.locator(".heatmap-grid button.heatmap-cell").nth(1).click()
        detail = page.locator(".heatmap-detail").inner_text()
        check("toucher un jour : détail affiché", "2 cuisson(s)" in detail and "Tarte" in detail and "Soupe" in detail, detail)
        check("case touchée mise en évidence", page.locator(".heatmap-selected").count() == 1)

        r = page.evaluate("() => { const s = document.querySelector('.heatmap-scroll'); return { left: s.scrollLeft, cw: s.clientWidth, sw: s.scrollWidth, overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth }; }")
        check("défilement : semaines récentes visibles d'emblée", r["left"] + r["cw"] >= r["sw"] - 2 and r["sw"] > r["cw"], r)
        check("pas de débordement de la page à 320 px", not r["overflow"])

        colors = page.evaluate("""() => {
            const get = () => [0, 1, 2, 3].map(i => getComputedStyle(document.querySelector('.heatmap-legend .heatmap-l' + i)).backgroundColor);
            const light = get();
            document.documentElement.setAttribute('data-theme', 'dark');
            const dark = get();
            document.documentElement.removeAttribute('data-theme');
            return { light, dark };
        }""")
        check("thème sombre : échelle propre (différente du thème clair)", colors["light"] != colors["dark"] and len(set(colors["dark"])) == 4, colors)

        page.evaluate("async () => { for (const r of await storeAll('recipes')) await storeDelete('recipes', r.id); await storePut('recipes', { id: 'z', name: 'Vide', category: 'Plat', ingredients: [], cookLog: [], createdAt: 'x' }); state.recipes = await storeAll('recipes'); render(); }")
        s = page.locator(".heatmap-summary").inner_text()
        check("aucune cuisson : résumé à zéro, pas d'erreur", s.startswith("0 cuisson(s) sur 0 jour(s)"), s)

        check("aucune erreur JS", not errors, errors)
        browser.close()
    httpd.shutdown()
    ok = all(results)
    print("\n=== Résumé ===")
    print("TOUT CORRECT" if ok else "ÉCHECS DÉTECTÉS")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
