"""
Vérifie l'ajout automatique des nouveaux ingrédients du catalogue aux
installations existantes (addNewCatalogueEntries dans app.js) : une
installation faite avant l'extension du catalogue (~1030 -> ~10 000
entrées) restait bloquée sur sa liste d'origine.

Simule une ancienne installation (liste d'origine avec suppressions
volontaires, ingrédient renommé, ingrédient personnel, aucun suivi des ids
connus) puis recharge l'application, et vérifie :
1. Les ingrédients apparus depuis dans le catalogue sont ajoutés.
2. Un ingrédient d'origine supprimé volontairement n'est PAS réajouté.
3. Un ingrédient renommé n'est pas dupliqué sous son nom d'origine.
4. Un ingrédient personnel est conservé ; s'il porte le nom d'une
   nouvelle entrée du catalogue, il y est relié au lieu d'être dupliqué.
5. Un ingrédient ajouté par la synchro puis supprimé ne revient pas au
   rechargement suivant.
6. Une installation neuve reçoit tout le catalogue et le suivi.
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


def start_local_server(port):
    handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=PROJECT_ROOT, **k)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def main():
    port = find_free_port()
    httpd = start_local_server(port)
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

        print("=== Installation neuve ===\n")
        page.goto(base_url, timeout=15000)
        page.evaluate("() => appReady")
        fresh = page.evaluate(
            """async () => ({
                names: state.ingredientNames.length,
                catalogue: INGREDIENT_CATALOGUE.length,
                known: (await kvGet(KNOWN_CATALOGUE_IDS_KEY) || []).length,
            })"""
        )
        check("installation neuve : tout le catalogue + suivi des ids", fresh["names"] == fresh["catalogue"] and fresh["known"] == fresh["catalogue"], str(fresh))

        print("\n=== Simulation d'une ancienne installation ===\n")
        setup = page.evaluate(
            """async () => {
                const original = INGREDIENT_CATALOGUE.filter((e) => Number(e.id.slice(4)) <= ORIGINAL_CATALOGUE_MAX_ID);
                const deleted = original[5];
                const renamed = original[10];
                const newEntry = INGREDIENT_CATALOGUE.find((e) => Number(e.id.slice(4)) > ORIGINAL_CATALOGUE_MAX_ID);
                const records = original
                    .filter((e) => e !== deleted && e !== renamed)
                    .map((e) => ({ name: e.fr }));  // sans catalogId : installation d'avant la migration
                records.push({ name: renamed.fr + ' maison' });
                records.push({ name: 'Ingrédient perso test' });
                records.push({ name: newEntry.fr.toLowerCase() });  // même nom qu'une future entrée, saisi à la main
                for (const r of await storeAll('ingredients')) await storeDelete('ingredients', r.name);
                await storePutAndDeleteMany('ingredients', records, []);
                await storeDelete('kv', KNOWN_CATALOGUE_IDS_KEY);
                return { deleted: deleted.fr, renamed: renamed.fr, newEntry: newEntry.fr, count: records.length };
            }"""
        )
        print(f"liste simulée : {setup['count']} ingrédients")

        page.reload()
        page.evaluate("() => appReady")
        r = page.evaluate(
            """async (s) => {
                const names = state.ingredientNames;
                const norm = (x) => normalize(x);
                const count = (n) => names.filter((x) => norm(x) === norm(n)).length;
                const added = INGREDIENT_CATALOGUE.filter((e) => Number(e.id.slice(4)) > ORIGINAL_CATALOGUE_MAX_ID);
                return {
                    total: names.length,
                    stored: (await storeAll('ingredients')).length,
                    newAddedCount: added.filter((e) => count(e.fr) === 1).length,
                    newExpected: added.length,
                    deletedBack: count(s.deleted),
                    renamedOriginalBack: count(s.renamed),
                    renamedKept: count(s.renamed + ' maison'),
                    personalKept: count('Ingrédient perso test'),
                    collisionCount: count(s.newEntry),
                    collisionLinked: !!state.ingredientCatalogIds[norm(s.newEntry)],
                    known: (await kvGet(KNOWN_CATALOGUE_IDS_KEY) || []).length,
                };
            }""",
            setup,
        )
        check("nouvelles entrées du catalogue ajoutées", r["newAddedCount"] == r["newExpected"], f"{r['newAddedCount']}/{r['newExpected']}")
        check("ingrédient d'origine supprimé non réajouté", r["deletedBack"] == 0, setup["deleted"])
        check("ingrédient renommé non dupliqué sous son nom d'origine", r["renamedOriginalBack"] == 0 and r["renamedKept"] == 1, str(r))
        check("ingrédient personnel conservé", r["personalKept"] == 1)
        check("même nom qu'une nouvelle entrée : relié, pas dupliqué", r["collisionCount"] == 1 and r["collisionLinked"], str(r))
        check("état mémoire et base cohérents", r["total"] == r["stored"], f"{r['total']} / {r['stored']}")
        check("suivi des ids enregistré", r["known"] >= r["newExpected"], str(r["known"]))

        print("\n=== Suppression d'un ingrédient ajouté par la synchro, puis rechargement ===\n")
        victim = page.evaluate(
            """async () => {
                const e = INGREDIENT_CATALOGUE.filter((x) => Number(x.id.slice(4)) > ORIGINAL_CATALOGUE_MAX_ID)[3];
                const name = state.ingredientNameByCatalogId[e.id];
                await deleteIngredientName(name);
                return { name, total: state.ingredientNames.length };
            }"""
        )
        page.reload()
        page.evaluate("() => appReady")
        after = page.evaluate(
            "(n) => ({ back: state.ingredientNames.some((x) => normalize(x) === normalize(n)), total: state.ingredientNames.length })",
            victim["name"],
        )
        check("ingrédient supprimé après synchro non réajouté", not after["back"] and after["total"] == victim["total"], str(after))

        check("Aucune erreur JS pendant tout le parcours", not errors, "; ".join(errors))
        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    return all_ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
