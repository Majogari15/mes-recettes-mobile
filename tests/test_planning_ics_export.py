"""
Export du planning vers un agenda (fichier .ics), repris de l'app Windows
(TESTS_NON_REGRESSION.md, entrée 144).

Vérifie le contenu (RFC 5545) : un événement par repas rempli, placé à la
prochaine occurrence du jour (aujourd'hui compris), horaires de l'app
Windows, pas de répétition hebdomadaire, échappement des caractères
spéciaux, lignes repliées à 75 octets sans couper un caractère, fins de
ligne CRLF, recette supprimée ignorée. Puis le bouton : planning vide ->
message ; partage natif si disponible ; sinon téléchargement ; message
d'explication (import Google Agenda depuis un ordinateur).
"""
import http.server
import re
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = "/home/user/mes-recettes-mobile"
LONG_NAME = "Gâteau " + "très " * 40 + "fin"


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=PROJECT_ROOT, **k)

    def log_message(self, *a):
        pass


def unfold(content):
    return content.replace("\r\n ", "")


def events(content):
    out = []
    for block in re.findall(r"BEGIN:VEVENT\r\n(.*?)END:VEVENT", unfold(content), re.S):
        props = {}
        for line in block.split("\r\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                props[k] = v
        out.append(props)
    return out


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
        page = browser.new_page(viewport={"width": 320, "height": 800}, accept_downloads=True)
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(f"http://127.0.0.1:{port}/index.html", timeout=15000)
        page.evaluate("() => appReady")
        page.evaluate("async () => { await ensureUiTranslationsLoaded('fr'); setLang('fr'); }")
        page.evaluate(
            """async (longName) => {
                const base = { category: 'Plat', ingredients: [], createdAt: '2026-01-01', cookLog: [], defaultPersons: 4 };
                await storePut('recipes', { ...base, id: 'r1', name: 'Poulet, riz; sauce\\\\maison' });
                await storePut('recipes', { ...base, id: 'r2', name: 'Tarte', defaultPersons: 6 });
                await storePut('recipes', { ...base, id: 'r3', name: longName });
                state.recipes = await storeAll('recipes');
                state.weeklyPlan = {};
                await saveWeeklyPlan();
            }""",
            LONG_NAME,
        )

        # --- Planning vide ---
        page.evaluate("() => { state.screen = 'planning'; render(); }")
        page.click(".planning-ics-btn")
        msg = page.locator("#custom-alert-message").inner_text()
        check("planning vide : message, pas de fichier", "vide" in msg, msg)
        page.click("#custom-alert-ok")

        # --- Contenu ---
        content = page.evaluate("""() => {
            const plan = {
                'Lundi': { 'Déjeuner': [{ recipeId: 'r1', persons: 4 }, { recipeId: 'r2', persons: 2 }] },
                'Mercredi': { 'Dîner': [{ recipeId: 'r3', persons: 3 }, { recipeId: 'supprimée', persons: 2 }] },
                'Jeudi': { 'Petit-déjeuner': [{ recipeId: 'supprimée', persons: 2 }] },
            };
            // Mercredi 7 octobre 2026, 10 h (heure locale).
            return buildWeeklyPlanIcs(plan, new Date(2026, 9, 7, 10, 0, 0)).content;
        }""")
        evs = events(content)
        check("fins de ligne CRLF partout", "\n" not in content.replace("\r\n", ""))
        check("en-tête et pied VCALENDAR", content.startswith("BEGIN:VCALENDAR\r\nVERSION:2.0\r\n") and content.endswith("END:VCALENDAR\r\n"))
        check("2 événements (case avec seulement une recette supprimée ignorée)", len(evs) == 2, len(evs))
        lundi = next((e for e in evs if e.get("DTSTART", "").startswith("20261012")), None)
        mercredi = next((e for e in evs if e.get("DTSTART", "").startswith("20261007")), None)
        check("lundi -> prochain lundi (12/10), déjeuner 12 h 30-13 h 30",
              lundi and lundi["DTSTART"] == "20261012T123000" and lundi["DTEND"] == "20261012T133000", lundi)
        check("mercredi = aujourd'hui (07/10), dîner 19 h 30-20 h 30",
              mercredi and mercredi["DTSTART"] == "20261007T193000" and mercredi["DTEND"] == "20261007T203000", mercredi)
        check("aucune répétition hebdomadaire (RRULE)", "RRULE" not in content)
        check("titre : repas + recettes, caractères spéciaux échappés",
              lundi and lundi["SUMMARY"] == "Déjeuner : Poulet\\, riz\\; sauce\\\\maison\\, Tarte", lundi and lundi["SUMMARY"])
        check("description : une ligne par recette avec les personnes",
              lundi and lundi["DESCRIPTION"] == "Poulet\\, riz\\; sauce\\\\maison (4 pers.)\\nTarte (2 pers.)", lundi and lundi["DESCRIPTION"])
        raw_lines = content.split("\r\n")
        too_long = [ln for ln in raw_lines if len(ln.encode("utf-8")) > 75]
        check("aucune ligne de plus de 75 octets", not too_long, too_long[:1])
        check("long titre replié puis reconstitué à l'identique (accents compris)",
              mercredi and LONG_NAME in mercredi["SUMMARY"], mercredi and mercredi["SUMMARY"][:60])
        uids = [e.get("UID") for e in evs]
        check("UID uniques et DTSTAMP en UTC", len(set(uids)) == 2 and all(re.fullmatch(r"\d{8}T\d{6}Z", e.get("DTSTAMP", "")) for e in evs), (uids, [e.get("DTSTAMP") for e in evs]))

        # --- Bouton : téléchargement (pas de partage de fichiers) ---
        page.evaluate("""async () => {
            state.weeklyPlan = { 'Mardi': { 'Dîner': [{ recipeId: 'r2', persons: 6 }] } };
            await saveWeeklyPlan();
            Object.defineProperty(navigator, 'canShare', { value: undefined, configurable: true });
            state.screen = 'planning'; render();
        }""")
        with page.expect_download() as dl:
            page.click(".planning-ics-btn")
        download = dl.value
        check("sans partage : fichier téléchargé « planning-repas.ics »", download.suggested_filename == "planning-repas.ics", download.suggested_filename)
        text = open(download.path(), encoding="utf-8", newline="").read()
        check("fichier téléchargé : 1 événement « Dîner : Tarte »", len(events(text)) == 1 and "SUMMARY:Dîner : Tarte" in unfold(text))
        msg = page.locator("#custom-alert-message").inner_text()
        check("message d'explication (Google Agenda depuis un ordinateur)", "1 repas" in msg and "calendar.google.com" in msg and "Importer et exporter" in msg, msg[:80])
        page.click("#custom-alert-ok")

        # --- Bouton : partage natif ---
        page.evaluate("""() => {
            window.__shared = null;
            Object.defineProperty(navigator, 'canShare', { value: () => true, configurable: true });
            Object.defineProperty(navigator, 'share', { value: (data) => { window.__shared = { name: data.files[0].name, type: data.files[0].type }; return Promise.resolve(); }, configurable: true });
        }""")
        page.click(".planning-ics-btn")
        page.wait_for_selector("#custom-alert-message")
        shared = page.evaluate("() => window.__shared")
        check("partage natif : fichier .ics de type text/calendar", shared == {"name": "planning-repas.ics", "type": "text/calendar"}, shared)
        page.click("#custom-alert-ok")

        # --- Partage annulé : aucun message ---
        page.evaluate("""() => {
            Object.defineProperty(navigator, 'share', { value: () => Promise.reject(Object.assign(new Error('x'), { name: 'AbortError' })), configurable: true });
        }""")
        page.click(".planning-ics-btn")
        page.wait_for_timeout(300)
        check("partage annulé : pas de message", page.locator("#custom-alert-message").count() == 0)

        overflow = page.evaluate("() => document.documentElement.scrollWidth > document.documentElement.clientWidth")
        check("écran planning : pas de débordement à 320 px", not overflow)
        check("aucune erreur JS", not errors, errors)
        browser.close()
    httpd.shutdown()
    ok = all(results)
    print("\n=== Résumé ===")
    print("TOUT CORRECT" if ok else "ÉCHECS DÉTECTÉS")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
