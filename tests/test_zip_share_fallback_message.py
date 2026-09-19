"""
Vérifie le message affiché quand le partage natif (Web Share API) échoue
pour la sauvegarde partagée au format .zip (compatible app Windows),
demandé par l'utilisateur suite à un signalement avec capture d'écran
(voir TESTS_NON_REGRESSION.md point 124) : sur son appareil,
`navigator.canShare()` répond "oui" pour le fichier .zip (le bouton
"Partager la sauvegarde" s'affiche donc), mais `navigator.share()`
lui-même échoue ensuite avec une "NotAllowedError" — reproduit ici en
simulant exactement ce même comportement (canShare accepte, share
rejette).

Le fichier est bien tout de même enregistré via téléchargement classique
(comportement déjà correct, vérifié aussi ici) — seul le MESSAGE affiché
change : un texte dédié (`backup_shared_share_fallback_notice`) explique
que c'est une limitation connue de nombreux navigateurs pour les
fichiers .zip, pas un bug de l'application — distinct du message
générique (`backup_share_fallback_notice`) resté inchangé pour le bouton
de partage de la sauvegarde JSON classique, vérifié en parallèle pour
confirmer qu'il n'a pas été affecté par ce changement.
"""
import http.server
import socket
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

    def check(label, condition, detail):
        nonlocal all_ok
        mark = "✅ OK " if condition else "❌ ECHEC"
        print(f"{mark} {label} — {detail}")
        if not condition:
            all_ok = False

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 900})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(base_url, timeout=8000)
        page.wait_for_timeout(600)
        page.evaluate("() => setLang('fr')")

        print("=== 1. Échec du partage ZIP (canShare accepte, share rejette en NotAllowedError) : message dédié ===")
        r1 = page.evaluate(
            """
            async () => {
                navigator.canShare = () => true;
                navigator.share = () => {
                    const err = new Error('Permission denied');
                    err.name = 'NotAllowedError';
                    return Promise.reject(err);
                };
                state.screen = 'backup';
                render();
                for (let i = 0; i < 40 && document.querySelector('#shared-share-btn')?.disabled; i++) {
                    await new Promise((r) => setTimeout(r, 100));
                }
                const btn = document.querySelector('#shared-share-btn');
                if (!btn || btn.disabled) return { buttonReady: false };
                btn.click();
                for (let i = 0; i < 30 && !document.getElementById('custom-alert-message'); i++) {
                    await new Promise((r) => setTimeout(r, 100));
                }
                const alertEl = document.getElementById('custom-alert-message');
                const text = alertEl ? alertEl.textContent : null;
                document.getElementById('custom-alert-ok')?.click();
                return {
                    buttonReady: true,
                    alertShown: !!alertEl,
                    text,
                    mentionsZipLimitation: text ? text.includes(t('backup_shared_share_fallback_notice')) : false,
                    mentionsGenericNotice: text ? text.includes(t('backup_share_fallback_notice')) && !text.includes(t('backup_shared_share_fallback_notice')) : false,
                    mentionsErrorDetail: text ? text.includes('NotAllowedError') : false,
                };
            }
            """
        )
        check(
            "message dédié au ZIP affiché (limitation connue, pas backup_share_fallback_notice générique), avec le détail de l'erreur",
            r1.get("buttonReady") and r1.get("alertShown") and r1.get("mentionsZipLimitation")
            and not r1.get("mentionsGenericNotice") and r1.get("mentionsErrorDetail"),
            str(r1),
        )

        print("\n=== 2. Le bouton de partage JSON classique garde son message générique inchangé (non affecté) ===")
        r2 = page.evaluate(
            """
            async () => {
                navigator.canShare = () => true;
                navigator.share = () => {
                    const err = new Error('Permission denied');
                    err.name = 'NotAllowedError';
                    return Promise.reject(err);
                };
                state.screen = 'backup';
                render();
                for (let i = 0; i < 40 && document.querySelector('#share-btn')?.disabled; i++) {
                    await new Promise((r) => setTimeout(r, 100));
                }
                const btn = document.querySelector('#share-btn');
                if (!btn || btn.disabled) return { buttonReady: false };
                btn.click();
                for (let i = 0; i < 30 && !document.getElementById('custom-alert-message'); i++) {
                    await new Promise((r) => setTimeout(r, 100));
                }
                const alertEl = document.getElementById('custom-alert-message');
                const text = alertEl ? alertEl.textContent : null;
                document.getElementById('custom-alert-ok')?.click();
                return {
                    buttonReady: true,
                    alertShown: !!alertEl,
                    matchesGenericNotice: text ? text.startsWith(t('backup_share_fallback_notice')) : false,
                };
            }
            """
        )
        check(
            "bouton JSON classique : message générique inchangé (pas le nouveau texte spécifique au ZIP)",
            r2.get("buttonReady") and r2.get("alertShown") and r2.get("matchesGenericNotice"),
            str(r2),
        )

        check("Aucune erreur JS pendant tout le parcours", not errors, str(errors))

        print("\n=== Résumé ===")
        print("TOUT CORRECT" if all_ok else "AU MOINS UN ECHEC")
        browser.close()
    httpd.shutdown()
    return all_ok


if __name__ == "__main__":
    import sys

    sys.exit(0 if main() else 1)
