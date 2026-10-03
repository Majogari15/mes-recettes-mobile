"""
Étiquettes libres et recherche par ingrédient, reprises de l'app Windows
(TESTS_NON_REGRESSION.md, entrée 142).

Étiquettes : dédoublonnage (casse/accents), saisie dans le formulaire avec
suggestions, affichage dans la fiche (appui -> liste filtrée), recherche
par étiquette dans la barre de recherche et le filtre, aller-retour du
champ « tags » avec l'app Windows (avant : exporté vide, ignoré à
l'import), réparation à la restauration d'une sauvegarde.

Recherche par ingrédient : « avec » (tous) / « sans » (aucun), début de
mot (« riz » ne trouve pas « Chorizo »), pluriel simple, œ, nom traduit ;
« Utilisé dans N recette(s) » dans la fenêtre d'un ingrédient (nom
exact). Aucun débordement à 320 px.
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
    const base = { category: 'Plat', difficulty: 'Facile', description: '', notes: '', photo: null, createdAt: '2026-01-01T00:00:00.000Z', cookLog: [], timesCooked: 0, defaultPersons: 4, allergens: [] };
    const ing = (name) => ({ name, quantity: 100, unit: 'g' });
    await storePut('recipes', { ...base, id: 'r1', name: 'Poulet basquaise', tags: ['Rapide', 'familial'], ingredients: [ing('Blanc de poulet'), ing('Tomate'), ing('Poivre')] });
    await storePut('recipes', { ...base, id: 'r2', name: 'Gratin', tags: ['familial'], ingredients: [ing('Crème fraîche'), ing('Pomme de terre'), ing('Œuf')] });
    await storePut('recipes', { ...base, id: 'r3', name: 'Paella', ingredients: [ing('Chorizo'), ing('Farine de riz'), ing('Petits pois')] });
    await storePut('recipes', { ...base, id: 'r4', name: 'Curry coco', tags: ['épicé'], ingredients: [ing('Lait de coco'), ing('Poulet'), ing('Riz')] });
    await storePut('recipes', { ...base, id: 'r5', name: 'Crêpes', ingredients: [ing('Farine'), ing('Lait'), ing('Oeufs')] });
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
        page = browser.new_page(viewport={"width": 320, "height": 800})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(f"http://127.0.0.1:{port}/index.html", timeout=15000)
        page.evaluate("() => appReady")
        page.evaluate("async () => { await ensureUiTranslationsLoaded('fr'); await ensureIngredientTranslationsLoaded('fr'); setLang('fr'); }")
        page.evaluate(SEED)
        page.evaluate("async () => { state.recipes = await storeAll('recipes'); }")

        # --- Normalisation des étiquettes ---
        r = page.evaluate("""() => ({
            arr: normalizeRecipeTags(['Rapide', ' rapide ', 'Économique', 'economique', '', 42, null, '  sans   gluten ']),
            str: normalizeRecipeTags('a, b ,A,, c'),
            bad: normalizeRecipeTags({ x: 1 }),
            long: normalizeRecipeTags(['x'.repeat(100)])[0].length,
            many: normalizeRecipeTags(Array.from({ length: 50 }, (_, i) => 't' + i)).length,
        })""")
        check("dédoublonnage casse/accents, espaces, non-textes ignorés", r["arr"] == ["Rapide", "Économique", "sans gluten"], r["arr"])
        check("texte séparé par des virgules", r["str"] == ["a", "b", "c"], r["str"])
        check("valeur invalide -> liste vide", r["bad"] == [], r["bad"])
        check("longueur et nombre limités", r["long"] == 40 and r["many"] == 20, (r["long"], r["many"]))

        # --- Recherche par ingrédient ---
        def ids(with_="", without=""):
            return page.evaluate(
                "([w, wo]) => { state.recipeIngredientWith = w; state.recipeIngredientWithout = wo; state.search = ''; state.recipeTagFilter = null; return filteredRecipes().map(r => r.id).sort(); }",
                [with_, without],
            )

        cases = [
            ("« poulet » trouve « Blanc de poulet » et « Poulet »", "poulet", "", ["r1", "r4"]),
            ("début de mot : « poul »", "poul", "", ["r1", "r4"]),
            ("« riz » ne trouve pas « Chorizo » (milieu de mot)", "riz", "", ["r3", "r4"]),
            ("« oeufs » trouve « Œuf » et « Oeufs »", "oeufs", "", ["r2", "r5"]),
            ("« pois » ne trouve pas « Poivre »", "pois", "", ["r3"]),
            ("plusieurs mots : « lait de coco »", "lait de coco", "", ["r4"]),
            ("« avec » exige tous les ingrédients", "poulet, riz", "", ["r4"]),
            ("« sans » exclut chacun", "", "crème; chorizo", ["r1", "r4", "r5"]),
            ("avec + sans combinés", "poulet", "coco", ["r1"]),
            ("majuscules et accents ignorés", "CREME", "", ["r2"]),
            ("terme inconnu -> aucune recette", "zzz", "", []),
            ("champs vides -> toutes les recettes", "", "", ["r1", "r2", "r3", "r4", "r5"]),
        ]
        for label, w, wo, expected in cases:
            got = ids(w, wo)
            check(label, got == expected, got)

        page.evaluate("async () => { await ensureUiTranslationsLoaded('en'); await ensureIngredientTranslationsLoaded('en'); setLang('en'); }")
        got = ids("chicken")
        check("nom traduit : « chicken » (interface en anglais)", got == ["r1", "r4"], got)
        page.evaluate("async () => { setLang('fr'); }")

        # --- Recherche et filtre par étiquette ---
        got = page.evaluate("() => { state.recipeIngredientWith = ''; state.recipeIngredientWithout = ''; state.search = 'famil'; return filteredRecipes().map(r => r.id).sort(); }")
        check("barre de recherche : trouve aussi par étiquette", got == ["r1", "r2"], got)
        got = page.evaluate("() => { state.search = ''; state.recipeTagFilter = 'RAPIDE'; return filteredRecipes().map(r => r.id); }")
        check("filtre par étiquette (casse ignorée)", got == ["r1"], got)

        # --- Écran liste : panneau de filtres ---
        page.evaluate("() => { state.recipeTagFilter = null; state.screen = 'recipes'; render(); }")
        check("panneau replié sans filtre actif", page.evaluate("() => !document.querySelector('.recipe-filters-panel').open"))
        page.click(".recipe-filters-panel > summary")
        page.fill("#recipe-filter-with", "poulet")
        n = page.evaluate("() => document.querySelectorAll('#recipe-list-holder .recipe-row').length")
        check("saisie « avec » : liste mise à jour sans perdre le champ", n == 2 and page.evaluate("() => document.activeElement.id") == "recipe-filter-with", n)
        cnt = page.evaluate("() => document.querySelector('.recipe-filters-count').textContent")
        check("compteur de filtres actifs", "1" in cnt, cnt)
        opts = page.evaluate("() => [...document.querySelectorAll('#recipe-filter-tag option')].map(o => o.value)")
        check("liste des étiquettes (une graphie, triée)", opts == ["", "épicé", "familial", "Rapide"], opts)
        page.select_option("#recipe-filter-tag", "familial")
        n = page.evaluate("() => document.querySelectorAll('#recipe-list-holder .recipe-row').length")
        check("étiquette + ingrédient combinés", n == 1, n)
        overflow = page.evaluate("() => document.documentElement.scrollWidth > document.documentElement.clientWidth")
        check("liste + panneau : pas de débordement à 320 px", not overflow)
        page.click(".recipe-filters-reset")
        r = page.evaluate("() => ({ w: state.recipeIngredientWith, t: state.recipeTagFilter, n: document.querySelectorAll('#recipe-list-holder .recipe-row').length })")
        check("« Effacer ces filtres »", r == {"w": "", "t": None, "n": 5}, r)
        page.fill("#recipe-filter-without", "crème")
        page.evaluate("() => document.querySelector('.bottom-nav .nav-item').click()")
        r = page.evaluate("() => ({ wo: state.recipeIngredientWithout, t: state.recipeTagFilter })")
        check("barre de navigation : filtres remis à zéro", r == {"wo": "", "t": None}, r)

        # --- Fiche recette : étiquettes cliquables ---
        page.evaluate("() => { state.search = 'xyz'; state.currentRecipeId = 'r1'; state.screen = 'recipe'; render(); }")
        chips = page.evaluate("() => [...document.querySelectorAll('.recipe-tags .chip')].map(c => c.textContent.trim())")
        check("étiquettes affichées dans la fiche", chips == ["Rapide", "familial"], chips)
        page.click(".recipe-tags .chip >> text=familial")
        r = page.evaluate("() => ({ screen: state.screen, tag: state.recipeTagFilter, search: state.search, n: document.querySelectorAll('#recipe-list-holder .recipe-row').length, open: document.querySelector('.recipe-filters-panel').open })")
        check("appui sur une étiquette -> liste filtrée (recherche effacée, panneau ouvert)", r == {"screen": "recipes", "tag": "familial", "search": "", "n": 2, "open": True}, r)
        rowtags = page.evaluate("() => [...document.querySelectorAll('.recipe-row-tags')].map(d => d.textContent)")
        check("étiquettes visibles sur les cartes de la liste", len(rowtags) == 2, rowtags)

        # --- Formulaire ---
        page.evaluate("async () => { await openRecipeForm('r3'); }")
        page.wait_for_selector("#f-tags")
        sugg = page.evaluate("() => [...document.querySelectorAll('.tag-suggestions .chip')].map(c => c.textContent.trim())")
        check("suggestions des étiquettes existantes", sugg == ["+ épicé", "+ familial", "+ Rapide"], sugg)
        page.fill("#f-tags", "végé, Végé ,  rapide")
        sugg = page.evaluate("() => [...document.querySelectorAll('.tag-suggestions .chip')].map(c => c.textContent.trim())")
        check("suggestion masquée si déjà saisie (casse ignorée)", sugg == ["+ épicé", "+ familial"], sugg)
        page.click(".tag-suggestions .chip >> text=familial")
        val = page.input_value("#f-tags")
        check("appui sur une suggestion -> ajoutée au champ", val == "végé, rapide, familial", val)
        page.evaluate("() => document.querySelector('form').requestSubmit()")
        try:
            page.wait_for_function("() => state.screen !== 'form'", timeout=8000)
        except Exception:
            print("   écran après enregistrement :", page.evaluate("() => ({ screen: state.screen, modal: document.querySelector('.modal-overlay') && document.querySelector('.modal-overlay').innerText.slice(0, 300) })"))
        tags = page.evaluate("async () => (await storeAll('recipes')).find(r => r.id === 'r3').tags")
        check("enregistrement : étiquettes dédoublonnées", tags == ["végé", "rapide", "familial"], tags)

        # --- Format partagé (app Windows) ---
        r = page.evaluate("""async () => {
            const src = state.recipes.find(r => r.id === 'r1');
            const { json } = await recipeToSharedFormat(src);
            const fromWindows = recipeFromSharedFormat({ name: 'W', tags: ['sans gluten', 'Sans Gluten', 'rapide'], ingredients: [] }, new Map());
            const noTags = recipeFromSharedFormat({ name: 'X', ingredients: [] }, new Map());
            return { exported: json.tags, imported: fromWindows.tags, none: noTags.tags };
        }""")
        check("export : étiquettes envoyées (avant : toujours vide)", r["exported"] == ["Rapide", "familial"], r["exported"])
        check("import Windows : étiquettes gardées et dédoublonnées", r["imported"] == ["sans gluten", "rapide"], r["imported"])
        check("import sans champ tags -> liste vide", r["none"] == [], r["none"])

        # --- Sauvegarde : réparation ---
        r = page.evaluate("""() => {
            const report = { structuralFixes: 0, numbersFixed: 0, photosRemoved: 0 };
            const a = sanitizeBackupItem({ id: 'x', name: 'A', tags: 'rapide, Rapide', ingredients: [] }, 'recipes', report);
            const b = sanitizeBackupItem({ id: 'y', name: 'B', tags: [1, {}, 'ok'], ingredients: [] }, 'recipes', report);
            const c = sanitizeBackupItem({ id: 'z', name: 'C', tags: ['bon'], ingredients: [] }, 'recipes', report);
            return { a: a.tags, b: b.tags, c: c.tags, fixes: report.structuralFixes };
        }""")
        check("sauvegarde : étiquettes invalides réparées, valides intactes", r == {"a": ["rapide"], "b": ["ok"], "c": ["bon"], "fixes": 2}, r)

        # --- Fenêtre d'un ingrédient : recettes qui l'utilisent ---
        page.evaluate("() => { state.screen = 'home'; render(); openIngredientNameModal('Farine'); }")
        r = page.evaluate("() => ({ text: document.querySelector('.ingredient-used-in p').textContent, chips: [...document.querySelectorAll('.ingredient-used-in .chip')].map(c => c.textContent) })")
        check("« Farine » : nom exact (pas « Farine de riz »)", r["chips"] == ["Crêpes"] and "1" in r["text"], r)
        overflow = page.evaluate("() => document.documentElement.scrollWidth > document.documentElement.clientWidth")
        check("fenêtre ingrédient : pas de débordement à 320 px", not overflow)
        page.click(".ingredient-used-in .chip")
        r = page.evaluate("() => ({ screen: state.screen, id: state.currentRecipeId, modal: !!document.querySelector('.modal-overlay') })")
        check("appui sur la recette -> fiche ouverte, fenêtre fermée", r == {"screen": "recipe", "id": "r5", "modal": False}, r)
        page.evaluate("() => { openIngredientNameModal('Safran'); }")
        txt = page.evaluate("() => document.querySelector('.ingredient-used-in p').textContent")
        check("ingrédient inutilisé : message dédié", "aucune" in txt, txt)

        check("aucune erreur JS", not errors, errors)
        browser.close()
    httpd.shutdown()
    ok = all(results)
    print("\n=== Résumé ===")
    print("TOUT CORRECT" if ok else "ÉCHECS DÉTECTÉS")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
