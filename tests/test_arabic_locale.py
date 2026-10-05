"""
Arabe, étape 5 — devise, chiffres saisis, date, voix, fiche Play Store
(TESTS_NON_REGRESSION.md, entrée 168 ; intégration en cours sur une
branche, pas encore sur main).

Vérifie : euro par défaut en arabe, monnaies des pays arabophones
proposées (nom et symbole arabes, 3 décimales pour le dinar koweïtien),
choix conservé ; chiffres arabo-indiens tapés au clavier (« ١٢٫٥ ») acceptés
dans un champ numérique, dans la date de péremption (jour/mois/année) et
le code-barres ; date affichée en chiffres occidentaux, jour avant mois ;
voix de lecture : une voix arabe d'une autre variante (« ar-XA ») choisie
si « ar-SA » manque ; fiche Play Store arabe dans les limites de Google.
"""
import http.server
import re
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = "/home/user/mes-recettes-mobile"
AR = re.compile(r"[ء-ي]")


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
    results = []

    def check(label, ok, detail=""):
        results.append(bool(ok))
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {label}{' — ' + str(detail) if detail != '' else ''}")

    # Fiche Play Store arabe : limites de Google (30 / 80 / 4000 caractères).
    fiche = open(f"{PROJECT_ROOT}/FICHE_PLAY_STORE.md", encoding="utf-8").read()
    part = fiche.split("# Fiche en arabe", 1)[-1] if "# Fiche en arabe" in fiche else ""
    blocks = re.findall(r"```\n(.*?)\n```", part, re.S)
    check("fiche Play Store arabe : titre, description courte et complète", len(blocks) == 3, len(blocks))
    if len(blocks) == 3:
        title, short, full = (b.strip() for b in blocks)
        check("fiche arabe : titre ≤ 30, courte ≤ 80, complète ≤ 4000 caractères",
              len(title) <= 30 and len(short) <= 80 and len(full) <= 4000, (len(title), len(short), len(full)))
        check("fiche arabe : en arabe, même nom que manifest-ar.json",
              all(AR.search(x) for x in (title, short, full)) and f'"name": "{title}"' in open(f"{PROJECT_ROOT}/manifest-ar.json", encoding="utf-8").read(),
              title)

    port = find_free_port()
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(locale="ar")
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(f"http://127.0.0.1:{port}/index.html", timeout=15000)
        page.evaluate("() => appReady")
        page.evaluate("async () => { await ensureUiTranslationsLoaded('ar'); setLang('ar'); state.currency = null; }")

        r = page.evaluate("""() => ({ cur: currentCurrency(), price: formatPrice(2.5),
            labels: ['MAD', 'DZD', 'TND', 'EGP', 'SAR', 'AED', 'KWD', 'IQD'].map((c) => [CURRENCY_OPTIONS.includes(c), currencyOptionLabel(c)]) })""")
        check("arabe : euro par défaut", r["cur"] == "EUR" and "€" in r["price"], r["price"])
        check("monnaies arabes proposées (dirham, dinar, livre, riyal…), nom en arabe",
              all(x[0] and AR.search(x[1]) for x in r["labels"]), r["labels"][:3])
        r = page.evaluate("""async () => { await setCurrency('KWD'); const kwd = formatPrice(1.25);
            await setCurrency('MAD'); const mad = formatPrice(12.5); const kept = currentCurrency(); await setCurrency(null);
            return { kwd, mad, kept, back: currentCurrency() }; }""")
        check("dinar koweïtien à 3 décimales, dirham marocain, chiffres occidentaux",
              "1.250" in r["kwd"] and "12.50" in r["mad"] and not re.search(r"[٠-٩]", r["kwd"] + r["mad"]), (r["kwd"], r["mad"]))
        check("choix de la devise conservé, retour à l'euro sans choix", r["kept"] == "MAD" and r["back"] == "EUR", r)

        # Chiffres d'un clavier arabe dans les champs.
        page.evaluate("""() => { const d = document.createElement('div'); d.id = 'probe';
            d.innerHTML = '<input type="number" step="any" id="pn"><input type="number" id="pm"><input type="text" inputmode="numeric" id="pt">';
            document.body.appendChild(d); }""")
        page.click("#pn"); page.keyboard.type("١٢٫٥")
        page.click("#pm"); page.keyboard.type("٣"); page.keyboard.type("4"); page.keyboard.type("٥")
        page.click("#pt"); page.keyboard.type("٠٥١٠٢٦")
        r = page.evaluate("() => [document.querySelector('#pn').value, document.querySelector('#pm').value, document.querySelector('#pt').value]")
        check("champ numérique : « ١٢٫٥ » -> 12.5, chiffres mélangés « ٣4٥ » -> 345", r[:2] == ["12.5", "345"], r)
        check("champ texte numérique : chiffres convertis", r[2] == "051026", r[2])
        r = page.evaluate("""() => ({ qty: parseQtyOrNull('٢٫٥'), fmt: formatShortDateInput('٠٥١٠٢٦'), iso: parseShortDateToIso('٠٥/١٠/٢٦').iso,
                                     back: isoDateToShortInput('2026-10-05'), date: localeDateStr(new Date(2026, 9, 5)) })""")
        check("quantité « ٢٫٥ » -> 2.5", r["qty"] == 2.5, r["qty"])
        check("date de péremption : jour/mois/année, chiffres arabes acceptés",
              r["fmt"] == "05/10/26" and r["iso"] == "2026-10-05" and r["back"] == "05/10/26", r)
        check("date affichée : chiffres occidentaux, jour avant mois (5/10/2026)",
              re.sub(r"[‎‏]", "", r["date"]) == "5/10/2026", r["date"])

        # Voix : « ar-SA » absente, une voix « ar-XA » présente.
        r = page.evaluate("""() => {
            const real = window.speechSynthesis; let spoken = null;
            const fake = { cancel() {}, speak(u) { spoken = { lang: u.lang, voice: u.voice && u.voice.name }; },
                getVoices() { return [{ name: 'English', lang: 'en-US' }, { name: 'Arabic', lang: 'ar-XA' }]; } };
            Object.defineProperty(window, 'speechSynthesis', { value: fake, configurable: true });
            const fakeU = window.SpeechSynthesisUtterance;
            window.SpeechSynthesisUtterance = function (text) { this.text = text; };
            speakText('مرحبا');
            setLang('fr'); speakText('Bonjour'); const fr = spoken; setLang('ar');
            Object.defineProperty(window, 'speechSynthesis', { value: real, configurable: true });
            window.SpeechSynthesisUtterance = fakeU;
            return { fr };
        }""")
        r2 = page.evaluate("""() => {
            const real = window.speechSynthesis; let spoken = null;
            Object.defineProperty(window, 'speechSynthesis', { value: { cancel() {}, speak(u) { spoken = { lang: u.lang, voice: u.voice && u.voice.name }; },
                getVoices() { return [{ name: 'English', lang: 'en-US' }, { name: 'Arabic', lang: 'ar-XA' }]; } }, configurable: true });
            const fakeU = window.SpeechSynthesisUtterance;
            window.SpeechSynthesisUtterance = function (text) { this.text = text; };
            speakText('مرحبا');
            Object.defineProperty(window, 'speechSynthesis', { value: real, configurable: true });
            window.SpeechSynthesisUtterance = fakeU;
            return spoken;
        }""")
        check("voix : « ar-SA » absente -> voix arabe « ar-XA » choisie", r2 == {"lang": "ar-XA", "voice": "Arabic"}, r2)
        check("voix : français sans voix française -> pas de voix d'une autre langue imposée",
              r["fr"] == {"lang": "fr-FR", "voice": None}, r["fr"])

        page.evaluate("() => { document.querySelector('#probe').remove(); setLang('fr'); }")
        check("aucune erreur JS", not errors, errors)
        browser.close()
    httpd.shutdown()
    ok = all(results)
    print("\n=== Résumé ===")
    print("TOUT CORRECT" if ok else "ÉCHECS DÉTECTÉS")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
