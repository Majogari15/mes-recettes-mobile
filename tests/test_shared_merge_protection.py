"""
Import d'une archive Windows en mode « Fusionner » : une recette locale
n'est plus jamais écrasée (TESTS_NON_REGRESSION.md, entrée 150 ; même
règle que l'app Windows depuis sa build 78).

Vérifie :
1. aller-retour sans modification (export puis import) -> tout reconnu
   identique, rien d'ajouté (empreinte stable : photo, journal, étiquettes,
   date de création absente de l'archive) ;
2. recette modifiée localement puis archive plus ancienne importée -> la
   version locale est gardée intacte, l'archive arrive en copie
   « (importée) » sous un nouvel identifiant ;
3. réimporter la même archive ne crée pas de seconde copie ;
4. nouvelle recette de l'archive -> ajoutée ;
5. mode « Remplacer tout » inchangé ;
6. écran Sauvegarde : message indiquant les copies.
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
    for (const r of await storeAll('recipes')) await storeDelete('recipes', r.id);
    const canvas = document.createElement('canvas'); canvas.width = 20; canvas.height = 20;
    canvas.getContext('2d').fillRect(0, 0, 10, 10);
    const photo = await new Promise((res) => canvas.toBlob(res, 'image/jpeg', 0.8));
    const base = { category: 'Plat', difficulty: 'Facile', defaultPersons: 4, createdAt: '2026-01-01T00:00:00.000Z', description: 'Étapes', notes: '' };
    await storePut('recipes', { ...base, id: 'A', name: 'Tarte', photo, tags: ['rapide'], wishlist: true, wishlistSince: '2026-02-01T00:00:00.000Z',
        ingredients: [{ name: 'Farine', quantity: 200, unit: 'g' }, { name: 'Oeufs', quantity: 2, unit: 'pièce' }],
        cookLog: [{ date: '2026-03-01T12:00:00.000Z', note: 'Bonne', comment: 'Un peu sèche', rating: 4, persons: 6, photo: null }], timesCooked: 1 });
    await storePut('recipes', { ...base, id: 'B', name: 'Soupe', photo: null, ingredients: [{ name: 'Carotte', quantity: 3, unit: 'pièce' }], cookLog: [], timesCooked: 0 });
    state.recipes = await storeAll('recipes');
}"""

EXPORT = """async () => {
    const zip = await buildSharedBackupZip();
    window.__zip = new File([zip], 'partage.zip', { type: 'application/zip' });
    return true;
}"""

RESTORE = """async (merge) => {
    const report = await restoreFromSharedZip(window.__zip, merge);
    state.recipes = await storeAll('recipes');
    return { report, recipes: state.recipes.map(r => ({ id: r.id, name: r.name, note: (r.cookLog[0] || {}).note || '', copyOf: r.importCopyOf || null, logs: r.cookLog.length })).sort((a, b) => a.name.localeCompare(b.name)) };
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
        page = browser.new_page(viewport={"width": 390, "height": 800})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(f"http://127.0.0.1:{port}/index.html", timeout=15000)
        page.evaluate("() => appReady")
        page.evaluate("async () => { await ensureUiTranslationsLoaded('fr'); setLang('fr'); }")
        page.evaluate(SEED)
        page.evaluate(EXPORT)

        # 1. Aller-retour sans modification.
        r = page.evaluate(RESTORE, True)
        rep = r["report"]
        check("aller-retour : 2 recettes reconnues identiques, rien d'ajouté ni copié",
              rep["recipesUnchanged"] == 2 and rep["recipesImported"] == 0 and rep["recipesCopied"] == 0 and len(r["recipes"]) == 2, rep)

        # 2. Modification locale (nouvelle cuisson notée) puis archive plus ancienne.
        page.evaluate("""async () => {
            const a = state.recipes.find(r => r.id === 'A');
            a.cookLog.unshift({ date: '2026-10-01T12:00:00.000Z', note: 'Notée sur le téléphone', comment: '', rating: 5, persons: 4, photo: null });
            a.timesCooked = 2;
            await storePut('recipes', a);
        }""")
        r = page.evaluate(RESTORE, True)
        rep = r["report"]
        local = next((x for x in r["recipes"] if x["id"] == "A"), None)
        copy = next((x for x in r["recipes"] if x["copyOf"] == "A"), None)
        check("recette locale modifiée : gardée intacte (cuisson du téléphone conservée)",
              local and local["note"] == "Notée sur le téléphone" and local["logs"] == 2 and local["name"] == "Tarte", local)
        check("version de l'archive ajoutée en copie « (importée) », nouvel identifiant",
              copy and copy["name"] == "Tarte (importée)" and copy["id"] != "A" and copy["logs"] == 1, copy)
        check("rapport : 1 copie, 1 identique (Soupe)", rep["recipesCopied"] == 1 and rep["recipesUnchanged"] == 1 and rep["recipesImported"] == 0, rep)

        # 3. Même archive réimportée : pas de seconde copie.
        r = page.evaluate(RESTORE, True)
        rep = r["report"]
        check("réimport de la même archive : aucune seconde copie",
              rep["recipesCopied"] == 0 and rep["recipesUnchanged"] == 2 and len(r["recipes"]) == 3, (rep, len(r["recipes"])))

        # 4. Nouvelle recette dans l'archive.
        page.evaluate("""async () => {
            const entries = [{ name: 'recipes.json', data: utf8Encode(JSON.stringify([{ id: 'C', name: 'Crêpes', category: 'Dessert', ingredients: [] }])) }];
            window.__zip = new File([await buildZipFile(entries)], 'w.zip', { type: 'application/zip' });
        }""")
        r = page.evaluate(RESTORE, True)
        check("recette inconnue : ajoutée", r["report"]["recipesImported"] == 1 and any(x["id"] == "C" for x in r["recipes"]), r["report"])

        # 5. Archive Windows sans date de création, contenu identique à « Soupe » -> identique.
        page.evaluate("""async () => {
            const b = state.recipes.find(r => r.id === 'B');
            const { json } = await recipeToSharedFormat(b);
            delete json.created_at;
            const entries = [{ name: 'recipes.json', data: utf8Encode(JSON.stringify([json])) }];
            window.__zip = new File([await buildZipFile(entries)], 'w.zip', { type: 'application/zip' });
        }""")
        r = page.evaluate(RESTORE, True)
        check("date de création absente de l'archive : toujours reconnue identique", r["report"]["recipesUnchanged"] == 1 and r["report"]["recipesCopied"] == 0, r["report"])

        # 6. Remplacer tout : comportement inchangé.
        page.evaluate(EXPORT)
        page.evaluate("""async () => {
            const entries = [{ name: 'recipes.json', data: utf8Encode(JSON.stringify([{ id: 'Z', name: 'Seule', category: 'Plat', ingredients: [] }])) }];
            window.__zip = new File([await buildZipFile(entries)], 'w.zip', { type: 'application/zip' });
        }""")
        r = page.evaluate(RESTORE, False)
        check("« Remplacer tout » : remplace toujours l'ensemble", [x["id"] for x in r["recipes"]] == ["Z"] and r["report"]["recipesImported"] == 1, r["recipes"])

        # 7. Écran Sauvegarde : message avec les copies.
        page.evaluate(SEED)
        page.evaluate(EXPORT)
        zip_bytes = page.evaluate("async () => Array.from(new Uint8Array(await window.__zip.arrayBuffer()))")
        page.evaluate("""async () => {
            const a = state.recipes.find(r => r.id === 'A');
            a.notes = 'Modifiée sur le téléphone';
            await storePut('recipes', a);
            state.recipes = await storeAll('recipes');
            state.screen = 'backup'; render();
        }""")
        page.select_option("#import-mode-shared", "merge")
        page.set_input_files("#shared-import-file", files=[{"name": "partage.zip", "mimeType": "application/zip", "buffer": bytes(zip_bytes)}])
        page.wait_for_selector("#custom-alert-message")
        msg = page.locator("#custom-alert-message").inner_text()
        check("message : nouvelles, identiques et copies expliquées", "0 nouvelle(s)" in msg and "1 déjà identique" in msg and "1 recette(s) de l'archive" in msg and "(importée)" in msg, msg)
        page.click("#custom-alert-ok")
        names = page.evaluate("async () => (await storeAll('recipes')).map(r => r.name + '|' + (r.notes || '')).sort()")
        check("après l'écran : version locale gardée + copie", names == ["Soupe|", "Tarte (importée)|", "Tarte|Modifiée sur le téléphone"], names)

        check("aucune erreur JS", not errors, errors)
        browser.close()
    httpd.shutdown()
    ok = all(results)
    print("\n=== Résumé ===")
    print("TOUT CORRECT" if ok else "ÉCHECS DÉTECTÉS")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
