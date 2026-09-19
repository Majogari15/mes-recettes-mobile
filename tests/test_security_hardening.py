#!/usr/bin/env python3
"""Test permanent pour le durcissement de sécurité trouvé lors de l'audit
complet (voir TESTS_NON_REGRESSION.md point 82) :

1. `escapeHtml()` n'échappait jamais les guillemets (`"`/`'`) — seulement
   &, < et > (limite de l'astuce textContent → innerHTML utilisée
   auparavant). Comme cette fonction est très souvent appelée À
   L'INTÉRIEUR d'attributs HTML entre guillemets (ex.
   value="${escapeHtml(...)}"), un texte contenant un guillemet double
   (nom de recette, d'ingrédient, note...) pouvait terminer prématurément
   l'attribut et permettre d'injecter du HTML/JS arbitraire juste après.
2. `isValidPhotoField()` ne vérifiait que le PRÉFIXE d'une data URL
   ("data:image/png;base64,"), laissant passer n'importe quelle suite de
   caractères ensuite — combiné au défaut 1, un champ photo dans une
   sauvegarde restaurée pouvait ainsi injecter du HTML. Depuis le passage
   du stockage des photos en Blob (voir TESTS_NON_REGRESSION.md point
   121), cette validation stricte vit dans `dataUrlToBlob()` (même regex
   ancrée qu'avant, mais qui retourne désormais un Blob ou null plutôt
   qu'un booléen) et `sanitizePhotoField()`, qui l'utilise à la frontière
   de restauration d'une sauvegarde — testées ci-dessous à la place de
   l'ancienne `isValidPhotoField()`, supprimée.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_security_hardening.py

Code de sortie : 0 si tous les cas passent, 1 sinon.
"""
import http.server
import os
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def start_local_server(port):
    handler = lambda *args, **kwargs: http.server.SimpleHTTPRequestHandler(
        *args, directory=PROJECT_ROOT, **kwargs
    )
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
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
        page = browser.new_page(viewport={"width": 390, "height": 844})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(base_url, timeout=8000)
        page.wait_for_timeout(1000)

        print("=== escapeHtml() échappe désormais les guillemets doubles ET simples ===\n")
        result_quotes = page.evaluate(
            """
            () => ({
                double: escapeHtml('a"b'),
                single: escapeHtml("a'b"),
                stillEscapesBasics: escapeHtml('<b>&amp;</b>'),
                nullSafe: escapeHtml(null),
            })
            """
        )
        check(
            'le guillemet double devient "&quot;"',
            result_quotes["double"] == "a&quot;b",
            str(result_quotes),
        )
        check(
            "le guillemet simple devient \"&#39;\"",
            result_quotes["single"] == "a&#39;b",
            str(result_quotes),
        )
        check(
            "&, < et > restent bien échappés comme avant",
            result_quotes["stillEscapesBasics"] == "&lt;b&gt;&amp;amp;&lt;/b&gt;",
            str(result_quotes),
        )
        check("null/undefined ne fait jamais planter (chaîne vide)", result_quotes["nullSafe"] == "", str(result_quotes))
        print()

        print("=== Un guillemet dans un nom/valeur ne casse plus l'attribut HTML qui le contient ===\n")
        result_attr = page.evaluate(
            """
            () => {
                const div = document.createElement('div');
                const malicious = 'Crème \\"maison\\" onmouseover=\\"window.__pwned=true\\"';
                div.innerHTML = `<input value="${escapeHtml(malicious)}">`;
                const input = div.querySelector('input');
                return {
                    displayedValue: input.value,
                    attributeCount: input.attributes.length,
                    hasInjectedHandler: input.hasAttribute('onmouseover'),
                };
            }
            """
        )
        check(
            "la valeur affichée est fidèle au texte d'origine",
            result_attr["displayedValue"] == 'Crème "maison" onmouseover="window.__pwned=true"',
            str(result_attr),
        )
        check(
            "aucun attribut supplémentaire n'a été injecté (un seul : value)",
            result_attr["attributeCount"] == 1,
            str(result_attr),
        )
        check(
            "aucun gestionnaire d'événement injecté",
            result_attr["hasInjectedHandler"] is False,
            str(result_attr),
        )
        print()

        print("=== dataUrlToBlob()/sanitizePhotoField() rejettent désormais une charge qui ne respecte pas le format base64 jusqu'au bout ===\n")
        result_photo = page.evaluate(
            """
            () => {
                const report = () => ({ structuralFixes: 0, numbersFixed: 0, photosRemoved: 0 });
                const prefixOnlyReport = report();
                const realImageReport = report();
                const nullReport = report();
                const nonStringReport = report();
                return {
                    prefixOnlyIsBlob: dataUrlToBlob('data:image/png;base64,X" onload="window.__pwned=true') instanceof Blob,
                    realImageIsBlob: dataUrlToBlob('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=') instanceof Blob,
                    sanitizedPrefixOnly: sanitizePhotoField('data:image/png;base64,X" onload="window.__pwned=true', prefixOnlyReport),
                    prefixOnlyRemoved: prefixOnlyReport.photosRemoved,
                    sanitizedRealImageIsBlob: sanitizePhotoField('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=', realImageReport) instanceof Blob,
                    realImageRemoved: realImageReport.photosRemoved,
                    sanitizedNull: sanitizePhotoField(null, nullReport),
                    nullRemoved: nullReport.photosRemoved,
                    sanitizedNonString: sanitizePhotoField(42, nonStringReport),
                    nonStringRemoved: nonStringReport.photosRemoved,
                };
            }
            """
        )
        check(
            "une charge avec un préfixe correct mais un guillemet ensuite est rejetée par dataUrlToBlob (pas de Blob)",
            result_photo["prefixOnlyIsBlob"] is False,
            str(result_photo),
        )
        check(
            "une vraie image base64 valide est convertie en Blob par dataUrlToBlob",
            result_photo["realImageIsBlob"] is True,
            str(result_photo),
        )
        check(
            "sanitizePhotoField rejette la même charge malveillante (null, comptée dans photosRemoved)",
            result_photo["sanitizedPrefixOnly"] is None and result_photo["prefixOnlyRemoved"] == 1,
            str(result_photo),
        )
        check(
            "sanitizePhotoField accepte la vraie image (Blob, non comptée dans photosRemoved)",
            result_photo["sanitizedRealImageIsBlob"] is True and result_photo["realImageRemoved"] == 0,
            str(result_photo),
        )
        check(
            "null reste accepté (photo absente, non comptée dans photosRemoved)",
            result_photo["sanitizedNull"] is None and result_photo["nullRemoved"] == 0,
            str(result_photo),
        )
        check(
            "une valeur non textuelle est rejetée (comptée dans photosRemoved)",
            result_photo["sanitizedNonString"] is None and result_photo["nonStringRemoved"] == 1,
            str(result_photo),
        )
        print()

        print("=== Bout en bout : une photo malveillante dans une recette n'injecte plus rien à l'affichage ===\n")
        result_e2e = page.evaluate(
            """
            () => {
                const payload = 'data:image/png;base64,X" onload="window.__pwned=true';
                const hero = document.createElement('div');
                // Reproduit exactement le motif utilisé par renderRecipeView (hero.innerHTML = `<img src="${escapeHtml(r.photo)}" alt="">`).
                hero.innerHTML = `<img src="${escapeHtml(payload)}" alt="">`;
                const img = hero.querySelector('img');
                return { hasOnload: img ? img.hasAttribute('onload') : null, srcPreserved: img ? img.getAttribute('src') === payload : null };
            }
            """
        )
        check(
            "aucun attribut onload injecté sur l'image affichée",
            result_e2e["hasOnload"] is False,
            str(result_e2e),
        )
        check(
            "l'attribut src contient la charge complète, telle quelle (pas de coupure ni de perte)",
            result_e2e["srcPreserved"] is True,
            str(result_e2e),
        )
        print()

        print("Erreurs JS sur tout le parcours:", "AUCUNE" if not errors else "; ".join(errors))
        if errors:
            all_ok = False
        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "DES ÉCHECS SUBSISTENT")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
