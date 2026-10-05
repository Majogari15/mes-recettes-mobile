#!/usr/bin/env python3
"""Test permanent : catalogue d'ingrédients à id stable (voir
TESTS_NON_REGRESSION.md, point 128 — migration demandée par
l'utilisateur en préparation d'un futur passage à ~10 000 ingrédients
et une dizaine de langues).

Avant cette migration, les fichiers de référence (allergènes,
nutrition, traductions, substitutions) étaient tous keyés directement
par le nom français exact de l'ingrédient — une comparaison stricte
(pas même insensible à la casse pour allergènes/nutrition). Renommer un
ingrédient dans "Gérer les ingrédients" faisait perdre silencieusement
l'accès à ces données, puisque le nom (la clé) changeait alors que les
fichiers de référence continuaient de chercher l'ancien nom.

Chaque ingrédient du catalogue développeur (data/ingredients_catalogue.json)
a maintenant un id stable ("ing_000123"), jamais recyclé, jamais affecté
par un renommage utilisateur. Les fichiers de référence sont reclés par
cet id. Le lien entre le nom ACTUEL d'un ingrédient (potentiellement
renommé) et son id est conservé dans state.ingredientCatalogIds,
construit au chargement et maintenu par renameIngredientName/
addIngredientName/mergeIngredientNames/deleteIngredientName.

Un second problème, plus subtil, a été corrigé au passage : les
traductions de substitutions (ingredient_substitutions_en/es/de.json)
étaient associées par POSITION dans un tableau (même index que le
fichier français), pas par un identifiant — un réordonnancement ou un
ajout dans le fichier français aurait décalé silencieusement toutes les
traductions suivantes. Chaque relation de substitution a maintenant son
propre "substitutionId" stable, les traductions sont keyées par cet id.

Un troisième problème, repéré par un second avis externe après la
première version de cette migration, a été corrigé dans un second
temps : `INGREDIENT_REVERSE_TRANSLATIONS` (utilisée par
`resolveIngredientInput` pour reconnaître une saisie dans une autre
langue) résolvait vers le nom français D'ORIGINE du catalogue, pas vers
le nom ACTUEL de l'ingrédient dans la liste de l'utilisateur — un
ingrédient renommé ("Tomate" -> "Tomate ronde") redevenait "Tomate" à
la moindre saisie en anglais ("Tomato"), recréant un doublon au lieu de
retrouver le bon ingrédient. Reproduit et corrigé : la résolution passe
maintenant par l'id catalogue puis par `state.ingredientNameByCatalogId`
(nouvelle table, sens inverse de `state.ingredientCatalogIds`). Au
passage, une collision entre deux ingrédients partageant la même
traduction (ex. "Peanut" pour "Arachide" ET "Cacahuète", 24 cas réels
existants en anglais) n'est plus résolue arbitrairement vers le premier
trouvé : `INGREDIENT_REVERSE_TRANSLATIONS` retient tous les ids
concernés, et une saisie ambiguë n'est jamais associée automatiquement.

Couvre :
- Premier lancement : chaque ingrédient du catalogue reçoit son catalogId.
- Renommage : allergènes/nutrition/catalogId survivent au renommage.
- Substitutions : structure {nom, note} correcte, traduction par langue
  fonctionne (comparée au texte français, doit différer).
- Ingrédient personnel (hors catalogue) : jamais de plantage, jamais de
  fausse association.
- Fusion de doublons : le catalogId de l'ingrédient supprimé est
  reporté sur celui conservé, s'il n'en avait pas déjà un.
- Rétrocompatibilité : un enregistrement IndexedDB antérieur à cette
  migration (sans catalogId) est relié à son id au prochain chargement,
  par simple correspondance de nom — sans bloquer le démarrage.
- Saisie bilingue après renommage : résout vers le nom ACTUEL, jamais
  l'ancien nom français du catalogue.
- Collision de traduction inverse : jamais de résolution automatique
  vers l'un des deux ingrédients concernés.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_ingredient_catalog_ids.py

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
        errors = []
        page = browser.new_page()
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(base_url, timeout=8000)
        page.evaluate("() => appReady")
        page.wait_for_timeout(1500)
        page.evaluate("() => setLang('fr')")

        print("=== Premier lancement : catalogId assigné à tous les ingrédients ===\n")
        r = page.evaluate(
            """async () => {
                const all = await storeAll('ingredients');
                return { total: all.length, active: activeCatalogueEntries().length, withId: all.filter((i) => i.catalogId).length };
            }"""
        )
        # 9 992 entrées, dont 30 retirées comme doublons (« doublonDe »).
        check("9962 ingrédients chargés (catalogue sans les doublons retirés)", r["total"] == r["active"] == 9962, str((r["total"], r["active"])))
        check("Tous rattachés au catalogue (catalogId)", r["withId"] == 9962, str(r["withId"]))

        print("\n=== Renommage : allergènes/nutrition/catalogId survivent ===\n")
        before = page.evaluate(
            "() => ({ allerg: getIngredientAllergens('Beurre'), nutri: getIngredientNutrition('Beurre') })"
        )
        page.evaluate("async () => { await renameIngredientName('Beurre', 'Beurre doux'); }")
        after = page.evaluate(
            """() => ({
                allerg: getIngredientAllergens('Beurre doux'),
                nutri: getIngredientNutrition('Beurre doux'),
                catalogId: state.ingredientCatalogIds[normalize('Beurre doux')],
            })"""
        )
        check("Allergènes identiques avant/après renommage", after["allerg"] == before["allerg"], f"{before['allerg']} -> {after['allerg']}")
        check("Nutrition conservée après renommage", after["nutri"] is not None and after["nutri"]["kcal"] == before["nutri"]["kcal"])
        check("catalogId conservé après renommage", bool(after["catalogId"]), str(after["catalogId"]))

        print("\n=== Substitutions : structure correcte et traduction par langue ===\n")
        subs_fr = page.evaluate("() => getDisplaySubstitutes('Beurre doux')")
        check("Au moins un substitut trouvé (via catalogId, pas l'ancien nom 'Beurre')", len(subs_fr) >= 1, str(len(subs_fr)))
        check(
            "Chaque substitut a bien 'nom' et 'note'",
            all("nom" in s and "note" in s for s in subs_fr),
            str(subs_fr),
        )
        # setLang() charge désormais les traductions d'ingrédients/substitutions
        # de la langue À LA DEMANDE (voir ensureIngredientTranslationsLoaded
        # dans app.js) plutôt que toutes au démarrage — attend explicitement
        # ce chargement avant de lire un résultat qui en dépend, sans quoi
        # cette vérification tomberait sur le repli français (pas encore
        # arrivé) plutôt qu'une vraie traduction.
        page.evaluate("async () => { setLang('es'); await ensureIngredientTranslationsLoaded('es'); }")
        subs_es = page.evaluate("() => getDisplaySubstitutes('Beurre doux')")
        page.evaluate("() => setLang('fr')")
        check(
            "La traduction espagnole diffère du texte français (pas un simple repli)",
            len(subs_es) == len(subs_fr) and (subs_es[0]["nom"] != subs_fr[0]["nom"] or subs_es[0]["note"] != subs_fr[0]["note"]),
            f"fr={subs_fr[0] if subs_fr else None} es={subs_es[0] if subs_es else None}",
        )

        print("\n=== Ingrédient personnel (hors catalogue) ===\n")
        page.evaluate("async () => { await addIngredientName('Sauce secrète de Mamie'); }")
        custom = page.evaluate(
            """() => ({
                allerg: getIngredientAllergens('Sauce secrète de Mamie'),
                nutri: getIngredientNutrition('Sauce secrète de Mamie'),
                subs: getDisplaySubstitutes('Sauce secrète de Mamie'),
                catalogId: state.ingredientCatalogIds[normalize('Sauce secrète de Mamie')],
            })"""
        )
        check("Aucun catalogId associé", not custom["catalogId"])
        check("Aucun allergène/nutrition/substitut renvoyé (jamais d'erreur)", custom["allerg"] == [] and custom["nutri"] is None and custom["subs"] == [])

        print("\n=== Fusion de doublons : le catalogId survit au nom supprimé ===\n")
        page.evaluate("async () => { await addIngredientName('Beurre demi-sel bio'); }")
        page.evaluate("async () => { await mergeIngredientNames('Beurre demi-sel bio', 'Beurre doux'); }")
        merged = page.evaluate(
            """() => ({
                catalogId: state.ingredientCatalogIds[normalize('Beurre demi-sel bio')],
                nutri: getIngredientNutrition('Beurre demi-sel bio'),
            })"""
        )
        check("catalogId reporté sur l'ingrédient conservé", bool(merged["catalogId"]))
        check("Nutrition accessible après fusion", merged["nutri"] is not None)

        print("\n=== Rétrocompatibilité : ancien enregistrement sans catalogId, relié au prochain chargement ===\n")
        page.evaluate("async () => { await storePut('ingredients', { name: 'Farine' }); }")
        page.reload()
        page.evaluate("() => appReady")
        page.wait_for_timeout(3000)
        backfilled = page.evaluate("() => state.ingredientCatalogIds[normalize('Farine')]")
        check("catalogId retrouvé par correspondance de nom au chargement", bool(backfilled), str(backfilled))
        persisted = page.evaluate(
            "async () => { const all = await storeAll('ingredients'); const r = all.find((i) => i.name === 'Farine'); return r ? r.catalogId : null; }"
        )
        check("catalogId aussi écrit dans IndexedDB (pas seulement en mémoire)", bool(persisted), str(persisted))

        print("\n=== Saisie bilingue après renommage : résout vers le nom ACTUEL, pas l'ancien nom du catalogue ===\n")
        page.evaluate("() => setLang('fr')")
        page.evaluate("async () => { await renameIngredientName('Tomate', 'Tomate ronde'); }")
        page.evaluate("async () => { setLang('en'); await ensureIngredientTranslationsLoaded('en'); }")
        resolved = page.evaluate("() => resolveIngredientInput('Tomato')")
        page.evaluate("() => setLang('fr')")
        check(
            "'Tomato' résout vers 'Tomate ronde' (le nom actuel), pas 'Tomate' (l'ancien nom du catalogue)",
            resolved == "Tomate ronde",
            f"obtenu={resolved!r}",
        )

        print("\n=== Collision de traduction inverse : jamais de résolution automatique ===\n")
        # "Peanut" est la traduction anglaise à la fois d'Arachide et de
        # Cacahuète (vraie collision du fichier de traduction actuel) —
        # une saisie ambiguë ne doit jamais être associée silencieusement
        # à l'un des deux au hasard.
        page.evaluate("async () => { setLang('en'); await ensureIngredientTranslationsLoaded('en'); }")
        collision_resolved = page.evaluate("() => resolveIngredientInput('Peanut')")
        page.evaluate("() => setLang('fr')")
        check(
            "'Peanut' (collision Arachide/Cacahuète) n'est jamais résolu automatiquement",
            collision_resolved == "Peanut",
            f"obtenu={collision_resolved!r}",
        )

        check("Aucune erreur JS pendant tout le parcours", len(errors) == 0, str(errors))

        browser.close()

    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "AU MOINS UN ÉCHEC — voir le détail ci-dessus")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
