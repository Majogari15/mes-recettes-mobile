"""
Premier lancement : les ~10 000 ingrédients du catalogue sont écrits dans
IndexedDB en arrière-plan (writeIngredientSeed dans app.js), sans retarder
l'affichage de l'accueil. Vérifie :
1. L'accueil s'affiche avant la fin de cette écriture.
2. Un ajout, un renommage et une suppression faits PENDANT l'écriture sont
   conservés après rechargement (IndexedDB exécute les transactions d'un
   même magasin dans leur ordre de création : l'écriture initiale, créée
   en premier, ne peut pas les écraser).
3. Un premier lancement interrompu avant la fin de l'écriture (marqueur
   localStorage catalogueSeedIncomplete resté posé) est réparé au lancement suivant :
   catalogue complet restauré, marqueur retiré.
"""
import http.server
import socket
import sys
import threading
import time

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


def wait_until(page, js, timeout_s=30.0):
    """page.wait_for_function n'attend pas une fonction async : boucle Python."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if page.evaluate(js):
            return True
        time.sleep(0.1)
    raise TimeoutError(f"condition jamais remplie : {js}")


def main():
    port = find_free_port()
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base_url = f"http://127.0.0.1:{port}/index.html"
    all_ok = True

    def check(label, ok, detail=""):
        nonlocal all_ok
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {label}" + (f" — {detail}" if detail else ""))
        if not ok:
            all_ok = False

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))

        print("=== Modifications faites pendant l'écriture initiale ===\n")
        page.goto(base_url, wait_until="commit", timeout=15000)
        page.wait_for_function("() => document.querySelector('.bottom-nav')", timeout=60000, polling=20)
        during = page.evaluate(
            """async () => {
                let seedDone = false;
                ingredientSeedWrite.then(() => { seedDone = true; });
                await Promise.resolve();
                const pendingAtStart = !seedDone;
                const [toRename, toDelete] = INGREDIENT_CATALOGUE.slice(0, 2).map((e) => e.fr);
                await addIngredientName('Ingrédient ajouté pendant écriture');
                await renameIngredientName(toRename, toRename + ' renommé');
                await deleteIngredientName(toDelete);
                return { pendingAtStart, toRename, toDelete };
            }"""
        )
        check("l'accueil s'affiche avant la fin de l'écriture initiale", during["pendingAtStart"])
        page.evaluate("() => appReady")
        page.reload()
        page.evaluate("() => appReady")
        after = page.evaluate(
            """async (d) => {
                const stored = (await storeAll('ingredients')).map((r) => r.name);
                const has = (n) => stored.includes(n);
                return {
                    added: has('Ingrédient ajouté pendant écriture'),
                    renamedNew: has(d.toRename + ' renommé'),
                    renamedOldGone: !has(d.toRename),
                    deletedGone: !has(d.toDelete),
                    stored: stored.length,
                    inMemory: state.ingredientNames.length,
                    flag: isSeedIncomplete(),
                    known: (await kvGet(KNOWN_CATALOGUE_IDS_KEY) || []).length,
                    catalogue: INGREDIENT_CATALOGUE.length,
                };
            }""",
            during,
        )
        check("ajout fait pendant l'écriture conservé", after["added"], str(after))
        check("renommage fait pendant l'écriture conservé (ancien nom absent)", after["renamedNew"] and after["renamedOldGone"], str(after))
        check("suppression faite pendant l'écriture conservée (pas réécrite)", after["deletedGone"], str(after))
        check("base et mémoire cohérentes, marqueur retiré, suivi complet",
              after["stored"] == after["inMemory"] == after["catalogue"] and not after["flag"] and after["known"] == after["catalogue"], str(after))

        print("\n=== Premier lancement interrompu avant la fin de l'écriture ===\n")
        page.evaluate(
            """async () => {
                await new Promise((res, rej) => { const tx = dbInstance.transaction('ingredients', 'readwrite'); tx.objectStore('ingredients').clear(); tx.oncomplete = res; tx.onerror = rej; });
                await storePutAndDeleteMany('ingredients', INGREDIENT_CATALOGUE.slice(0, 300).map((e) => ({ name: e.fr, catalogId: e.id })), []);
                await storeDelete('kv', KNOWN_CATALOGUE_IDS_KEY);
                setSeedIncompleteFlag(true);
            }"""
        )
        page.reload()
        page.evaluate("() => appReady")
        repaired = page.evaluate(
            """async () => ({
                stored: (await storeAll('ingredients')).length,
                inMemory: state.ingredientNames.length,
                catalogue: INGREDIENT_CATALOGUE.length,
                flag: isSeedIncomplete(),
            })"""
        )
        check("catalogue complet restauré et marqueur retiré",
              repaired["stored"] == repaired["inMemory"] == repaired["catalogue"] and not repaired["flag"], str(repaired))

        check("Aucune erreur JS pendant tout le parcours", not errors, "; ".join(errors))
        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    return all_ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
