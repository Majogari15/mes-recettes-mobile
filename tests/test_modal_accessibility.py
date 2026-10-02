"""
Accessibilité des fenêtres modales (dialogues), absentes de
test_accessibility_audit.py qui ne parcourt que les écrans. Voir
TESTS_NON_REGRESSION.md, entrée 137.

Pour chaque fenêtre, en thème clair et sombre :
- aucune violation axe-core « serious » ou « critical » ;
- le focus clavier est bien placé DANS la fenêtre à l'ouverture.

Trouvé à l'audit v303 : QR codes sans texte alternatif et focus perdu
(il visait un bouton masqué), fond gris par défaut du navigateur sur
les lignes des fenêtres « choisir une recette » et « langue »
(contraste 4,45:1 en thème sombre).
"""
import http.server
import os
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODALS = {
    "ajout aux courses": "openShoppingAddPrompt()",
    "ajout au garde-manger": "openPantryAddPrompt()",
    "ingrédient existant": "openIngredientNameModal('Beurre')",
    "nouvel ingrédient": "openIngredientNameModal(null)",
    "choix d'une recette": "openRecipePickerModal(() => {})",
    "langue": "openLanguagePickerModal()",
    "QR code de la liste de courses": "openShoppingQrCodeModal()",
    "QR code d'une recette": "openQrCodeModal(state.recipes[0])",
    "substituts": "openSubstitutesModal('Beurre')",
    "journal de cuisine (ajout)": "openCookLogAddModal(state.recipes[0])",
    "journal de cuisine (lecture)": "openCookLogViewModal(state.recipes[0])",
    "collage d'un code-barres": "openBarcodePasteModal()",
    "collage d'un QR code": "openQrPasteModal()",
    "confirmation": "customConfirm('Test ?')",
    "saisie": "customPrompt('Nom ?')",
    "message": "customAlert('Info')",
}


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
    all_ok = True
    with sync_playwright() as p:
        browser = p.chromium.launch()
        # Mouvement réduit : mesure le contraste final, pas un état de
        # l'animation d'ouverture (voir test_accessibility_audit.py).
        ctx = browser.new_context(viewport={"width": 360, "height": 740}, reduced_motion="reduce")
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc).split("\n")[0]))
        page.goto(f"http://127.0.0.1:{port}/index.html", timeout=15000)
        page.evaluate("() => appReady")
        page.evaluate(
            """async () => {
                await storePut('recipes', { id: 'mr1', name: 'Recette test', category: 'Plat', defaultPersons: 4, ingredients: [{ name: 'Beurre', quantity: 40, unit: 'g' }], cookLog: [{ date: new Date().toISOString(), note: 'ok' }], createdAt: new Date().toISOString() });
                await storePut('shopping', { id: 'ms1', name: 'Tomate', quantity: 2, unit: 'pièce', checked: false });
                state.recipes = await storeAll('recipes'); state.shopping = await storeAll('shopping');
                setLang('fr');
            }"""
        )
        page.add_script_tag(url=f"http://127.0.0.1:{port}/tests/vendor/axe.min.js")
        for theme in ("light", "dark"):
            page.evaluate("(t) => document.documentElement.setAttribute('data-theme', t)", theme)
            for name, call in MODALS.items():
                e0 = len(errors)
                page.evaluate(f"() => {{ const r = {call}; if (r && r.catch) r.catch(() => {{}}); }}")
                page.wait_for_timeout(400)
                info = page.evaluate(
                    """async () => {
                        const ov = [...document.querySelectorAll('.modal-overlay')].pop();
                        if (!ov) return null;
                        const res = await axe.run(ov, { resultTypes: ['violations'] });
                        return {
                            focusInside: ov.contains(document.activeElement),
                            axe: res.violations.filter((v) => v.impact === 'serious' || v.impact === 'critical')
                                .map((v) => v.id + ' (' + v.impact + ')'),
                        };
                    }"""
                )
                problems = []
                if info is None:
                    problems.append("fenêtre non ouverte")
                else:
                    if not info["focusInside"]:
                        problems.append("focus hors de la fenêtre")
                    problems += info["axe"]
                problems += errors[e0:]
                ok = not problems
                print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {name} ({theme})" + ("" if ok else " — " + "; ".join(problems)))
                all_ok = all_ok and ok
                page.evaluate("() => document.querySelectorAll('.modal-overlay').forEach((o) => o.remove())")
        browser.close()
    httpd.shutdown()
    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    return all_ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
