"""
Vérifie qu'une nouvelle version du service worker enregistre le app.js À
JOUR, même quand le serveur autorise le navigateur à garder une copie en
cache HTTP (GitHub Pages : Cache-Control max-age=600).

Défaut corrigé : la pré-installation (cache.addAll) et le chargement
"réseau d'abord" des fichiers critiques passaient par le cache HTTP du
navigateur. Une nouvelle version pouvait ainsi enregistrer le app.js de la
version précédente — constaté : écran Diagnostic affichant "version de
l'application v275" avec "version du cache v292".

Le serveur de test sert app.js et sw.js modifiés à la volée (marqueur de
version dans app.js, CACHE_NAME dans sw.js), avec max-age=600 sur tout.
"""
import http.server
import re
import socket
import sys
import threading
import time

from playwright.sync_api import sync_playwright

PROJECT_ROOT = "/home/user/mes-recettes-mobile"
CURRENT = {"tag": "A"}


def wait_until(page, js, timeout_s=20.0):
    """Attend qu'une expression JS (asynchrone possible) renvoie une valeur
    vraie — page.wait_for_function juge une fonction async vraie
    immédiatement, sans attendre la promesse."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if page.evaluate(js):
            return True
        time.sleep(0.1)
    raise TimeoutError(f"condition jamais remplie : {js}")


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=PROJECT_ROOT, **k)

    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "max-age=600")
        super().end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path.endswith("/app.js") or path.endswith("/sw.js"):
            name = "app.js" if path.endswith("/app.js") else "sw.js"
            body = open(f"{PROJECT_ROOT}/{name}", encoding="utf-8").read()
            if name == "app.js":
                body += f"\nconst __TEST_BUILD_TAG = '{CURRENT['tag']}';\n"
            else:
                body = re.sub(r"\}v\d+`;", "}vtest" + CURRENT["tag"] + "`;", body, count=1)
            data = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        super().do_GET()


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

    read_cached_app = """async (cacheName) => {
        const cache = await caches.open(cacheName);
        const res = await cache.match(new URL('app.js', location.href).href);
        if (!res) return null;
        const m = (await res.text()).match(/__TEST_BUILD_TAG = '(\\w+)'/);
        return m ? m[1] : null;
    }"""

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(base_url, timeout=15000)
        page.evaluate("() => appReady")
        wait_until(page, "async () => !!(await (await caches.open('mes-recettes-cache-vtestA')).match(new URL('app.js', location.href).href))")
        check("version A installée avec le app.js A", page.evaluate(read_cached_app, "mes-recettes-cache-vtestA") == "A")

        print("\n=== Nouvelle version publiée moins de 10 min après (app.js A encore dans le cache HTTP) ===\n")
        CURRENT["tag"] = "B"
        page.evaluate("async () => { const r = await navigator.serviceWorker.getRegistration(); await r.update(); }")
        wait_until(page, "async () => (await caches.keys()).includes('mes-recettes-cache-vtestB') && !!(await (await caches.open('mes-recettes-cache-vtestB')).match(new URL('app.js', location.href).href))")
        tag = page.evaluate(read_cached_app, "mes-recettes-cache-vtestB")
        check("la nouvelle version enregistre le app.js B, pas la copie A du cache HTTP", tag == "B", f"app.js en cache : {tag}")

        page.reload()
        page.evaluate("() => appReady")
        live = page.evaluate("() => __TEST_BUILD_TAG")
        check("après rechargement, le code exécuté est bien B", live == "B", f"code exécuté : {live}")

        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    return all_ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
