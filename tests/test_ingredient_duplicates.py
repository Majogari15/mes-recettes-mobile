#!/usr/bin/env python3
"""Test permanent : détection des doublons d'ingrédients
(findSimilarIngredientPairs) — voir TESTS_NON_REGRESSION.md, point 131.

Un second avis externe, après avoir validé la migration du catalogue
d'ingrédients (points 129-130), a testé l'algorithme de détection de
doublons lui-même sur des cas ciblés et trouvé 3 angles morts réels,
tous vérifiés en exécutant le vrai code avant correction :

1. Regroupement par les 2 premières lettres avant comparaison : un nom
   mal orthographié dès la 2e lettre ("Mozzarella"/"Mzzarella", ratio
   réel 94,7%, largement au-dessus du seuil 90%) tombait dans un groupe
   différent et n'était donc jamais comparé. Élargi à la seule première
   lettre.
2. Deux noms strictement identiques après normalisation
   ("Crème fraîche"/"Creme fraiche") étaient silencieusement ignorés
   (`if (keyA === keyB) continue`) — en usage normal `addIngredientName`
   empêche déjà ce cas, mais une ancienne sauvegarde ou un import
   pourrait en contenir deux malgré tout. Signalés maintenant comme
   doublon exact (ratio 1.0) plutôt qu'ignorés.
3. Le pluriel irrégulier français ("Bocal"/"Bocaux", "-al" -> "-aux")
   n'était pas reconnu, contrairement au pluriel simple +s/+x. Nouvelle
   fonction dédiée `isIrregularPluralVariant`.

Couvre aussi le vrai négatif (deux ingrédients différents ne devant
jamais être signalés) et les cas déjà correctement détectés avant ces
3 corrections, pour s'assurer qu'elles ne les cassent pas.

Un quatrième correctif, distinct, a suivi après un essai avec un vrai
jeu de 10 000 ingrédients (catalogue candidat non retenu tel quel,
voir la conversation) : `findSimilarIngredientPairs` mettait plus de
4 MINUTES (254 s) et gelait complètement l'écran à ce volume — la
fenêtre de longueur seule (déjà présente ci-dessus) ne suffisait pas,
la majorité du temps étant passée à calculer `sequenceMatcherRatio`
(coûteux) sur des paires qui n'avaient de toute façon aucune chance
d'atteindre le seuil. Un filtre rapide par coefficient de Dice sur les
bigrammes de caractères (bien moins coûteux, une simple intersection de
compteurs) est maintenant appliqué avant ce calcul — mais seulement sur
les noms d'au moins 15 caractères : sur des mots courts, quelques
bigrammes suffisent à fausser le score (repéré avant correction :
"Pêche"/"Perche" perdu à tort par ce filtre). Résultat mesuré sur les
10 000 vrais noms : 254 s -> 19 s, EXACTEMENT les mêmes 8900 paires
qu'un calcul de référence sans le filtre rapide (zéro perte, zéro faux
positif introduit). Le test de performance ci-dessous est synthétique
(généré, ne dépend d'aucun fichier externe) pour rester exécutable par
quiconque clone le dépôt, mais reproduit la même forme de données
(nombreux noms longs et très proches les uns des autres) qui faisait
échouer l'ancienne version.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_ingredient_duplicates.py

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

    def pair_found(pairs, a, b):
        for name_a, name_b, ratio in pairs:
            if {name_a, name_b} == {a, b}:
                return ratio
        return None

    with sync_playwright() as p:
        browser = p.chromium.launch()
        errors = []
        page = browser.new_page()
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(base_url, timeout=8000)
        page.evaluate("() => appReady")
        page.wait_for_timeout(1500)

        def find(a, b):
            pairs = page.evaluate("([a, b]) => findSimilarIngredientPairs([a, b], 0.9)", [a, b])
            return pair_found(pairs, a, b)

        print("=== Cas déjà correctement détectés avant ces corrections (non-régression) ===\n")
        check("'Tomate'/'Tomates' détecté (pluriel simple)", find("Tomate", "Tomates") is not None)
        check("'Échalote'/'Echalotte' détecté (faute + accent)", find("Échalote", "Echalotte") is not None)
        check("'Arachide'/'Cacahuète' JAMAIS considéré comme doublon (vrai négatif)", find("Arachide", "Cacahuète") is None)

        print("\n=== Correction 1 : regroupement élargi (1ère lettre, pas les 2 premières) ===\n")
        ratio = find("Mozzarella", "Mzzarella")
        check(
            "'Mozzarella'/'Mzzarella' maintenant détecté malgré la faute dès la 2e lettre",
            ratio is not None and ratio >= 0.9,
            f"ratio={ratio}",
        )

        print("\n=== Correction 2 : doublon exact après normalisation, signalé plutôt qu'ignoré ===\n")
        ratio = find("Crème fraîche", "Creme fraiche")
        check(
            "'Crème fraîche'/'Creme fraiche' signalé comme doublon exact (ratio 1.0)",
            ratio == 1,
            f"ratio={ratio}",
        )

        print("\n=== Correction 3 : pluriel irrégulier français (-al -> -aux) ===\n")
        ratio = find("Bocal", "Bocaux")
        check("'Bocal'/'Bocaux' maintenant détecté (pluriel irrégulier)", ratio is not None, f"ratio={ratio}")
        ratio2 = find("Cheval", "Chevaux")
        check("'Cheval'/'Chevaux' aussi détecté (même règle)", ratio2 is not None, f"ratio={ratio2}")

        print("\n=== Écran dédié : une paire ignorée disparaît, une fusion retire bien le doublon ===\n")
        page.evaluate(
            """async () => {
                if (!state.ingredientNames.includes('Testinga')) await addIngredientName('Testinga');
                if (!state.ingredientNames.includes('Testingaz')) await addIngredientName('Testingaz');
                state.screen = 'ingredientDuplicates';
                render();
            }"""
        )
        # Le calcul (findSimilarIngredientPairs sur tout le catalogue) est
        # désormais différé d'un tick pour laisser peindre l'état de
        # chargement (voir renderIngredientDuplicates) : sur le catalogue
        # réel (~10 000 ingrédients), il peut prendre plusieurs secondes,
        # donc on attend le résultat plutôt qu'un délai fixe trop court.
        # Plafond large : ~6 s sur une machine de dev, ~27 s avec un
        # processeur 4 fois plus lent (ordre de grandeur d'un téléphone).
        page.wait_for_function(
            "() => !document.getElementById('dup-list-holder').innerText.includes('…')", timeout=90000
        )
        # Affichage par lots de 50 : "Afficher plus" jusqu'à la paire de test.
        first_batch = page.evaluate("() => document.querySelectorAll('#dup-list-holder .card').length")
        check("Premier lot limité à 50 paires", first_batch == 50, str(first_batch))
        clicks = 0
        while not page.evaluate("() => document.body.innerText.includes('Testinga')") and clicks < 200:
            more = page.query_selector("#dup-list-holder > button.btn-outline")
            if not more:
                break
            more.click()
            clicks += 1
        after_more = page.evaluate("() => document.querySelectorAll('#dup-list-holder .card').length")
        check("'Afficher plus' ajoute bien des paires", clicks == 0 or after_more == 50 * (clicks + 1) or not page.query_selector("#dup-list-holder > button.btn-outline"), f"{clicks} clics, {after_more} cartes")
        before = page.evaluate("() => document.body.innerText.includes('Testinga')")
        check("La paire de test apparaît bien dans l'écran de vérification", before)
        page.evaluate(
            """async () => {
                const idx = Array.from(document.querySelectorAll('.card')).findIndex((c) => c.textContent.includes('Testinga'));
                if (idx >= 0) document.querySelectorAll('.card')[idx].querySelector('.dismiss-btn').click();
            }"""
        )
        page.wait_for_function(
            "() => !document.getElementById('dup-list-holder').innerText.includes('…')", timeout=90000
        )
        after_dismiss = page.evaluate("() => document.body.innerText.includes('Testinga')")
        check("Ignorer la paire la fait disparaître de l'écran", not after_dismiss)

        # Fusion depuis l'écran : la liste est mise à jour en retirant les
        # paires du nom supprimé, sans relancer le calcul complet.
        page.evaluate(
            """async () => {
                if (!state.ingredientNames.includes('Fusiontesta')) await addIngredientName('Fusiontesta');
                if (!state.ingredientNames.includes('Fusiontestaz')) await addIngredientName('Fusiontestaz');
                state.screen = 'home'; render();
                state.screen = 'ingredientDuplicates'; render();
            }"""
        )
        page.wait_for_function(
            "() => !document.getElementById('dup-list-holder').innerText.includes('…')", timeout=90000
        )
        clicks = 0
        while not page.evaluate("() => document.body.innerText.includes('Fusiontesta ↔')") and clicks < 400:
            more = page.query_selector("#dup-list-holder > button.btn-outline")
            if not more:
                break
            more.click()
            clicks += 1
        cards_before = page.evaluate("() => document.querySelectorAll('#dup-list-holder .card').length")
        page.evaluate(
            """() => {
                const card = Array.from(document.querySelectorAll('#dup-list-holder .card')).find((c) => c.textContent.includes('Fusiontesta ↔'));
                card.querySelector('.merge-btn').click();
            }"""
        )
        page.click(".modal-sheet button:has-text('Fusiontesta'):not(:has-text('Fusiontestaz'))")
        page.wait_for_function("() => !state.ingredientNames.includes('Fusiontestaz')", timeout=10000)
        merged = page.evaluate(
            """() => ({
                pairGone: !document.body.innerText.includes('Fusiontestaz'),
                loading: document.getElementById('dup-list-holder').innerText.includes('…'),
                cards: document.querySelectorAll('#dup-list-holder .card').length,
            })"""
        )
        check(
            "Fusion : la paire disparaît, sans repasser par le calcul complet",
            merged["pairGone"] and not merged["loading"] and merged["cards"] >= cards_before - 1,
            str(merged),
        )

        print("\n=== Performance : gros volume de noms longs et très proches (forme USDA-like) ===\n")
        # Génère un jeu synthétique reproduisant la forme qui faisait
        # échouer l'ancienne version : de nombreux noms longs partageant
        # la même racine (variantes "cru"/"cuit"), plutôt que les noms
        # courts habituels de la liste française actuelle. Ne dépend
        # d'aucun fichier externe — reproductible par quiconque clone le
        # dépôt. Le nombre de racines (150) correspond au pire cas
        # RÉELLEMENT observé sur un vrai jeu de 10 000 ingrédients d'un
        # bundle candidat (variantes "Poulet, poulets de chair, ..." :
        # 118 entrées quasi identiques dans le même préfixe) — pas un
        # cas pathologique arbitraire, mais la vraie taille de groupe la
        # plus défavorable rencontrée en pratique.
        perf_result = page.evaluate(
            """() => {
                const bases = [];
                for (let i = 0; i < 150; i++) {
                    bases.push(
                        `Ingrédient synthétique numéro ${i}, catégorie test, préparation détaillée avec plusieurs qualificatifs`
                    );
                }
                const names = [];
                bases.forEach((b) => { names.push(b + ', cru'); names.push(b + ', cuit'); });
                const t0 = performance.now();
                const pairs = findSimilarIngredientPairs(names, 0.9);
                const t1 = performance.now();
                return { ms: t1 - t0, count: names.length, pairsFound: pairs.length };
            }"""
        )
        check(
            "300 noms longs et proches (pire groupe réel observé) traités en moins de 20 s",
            perf_result["ms"] < 20000,
            f"{perf_result['ms']:.0f} ms pour {perf_result['count']} noms, {perf_result['pairsFound']} paires trouvées",
        )

        browser.close()

    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "AU MOINS UN ÉCHEC — voir le détail ci-dessus")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
