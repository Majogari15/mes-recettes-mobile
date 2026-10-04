"""
Chinois simplifié — interface et mise en page (TESTS_NON_REGRESSION.md,
entrée 153 ; intégration en cours sur une branche, pas encore sur main).

Vérifie : traduction complète (mêmes clés et mêmes {variables} que le
français, aucun texte vide, pas de « (s) » à la française), langue
déclarée (html lang « zh-CN », manifeste chinois chargé, en cache hors
ligne), détection automatique d'un téléphone réglé en chinois,
allergènes et rayons traduits, ponctuation chinoise (« ： », « （） »,
« ， »), virgules chinoises acceptées dans les étiquettes et la recherche
par ingrédient, polices chinoises du système et pas d'espacement de
lettres, grand titre sur une seule ligne qui tient à 320 px, synthèse
vocale en zh-CN.
"""
import http.server
import json
import re
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


def main():
    port = find_free_port()
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{port}/index.html"
    results = []

    def check(label, ok, detail=""):
        results.append(bool(ok))
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {label}{' — ' + str(detail) if detail != '' else ''}")

    zh = json.load(open(f"{PROJECT_ROOT}/i18n/zh.json", encoding="utf-8"))
    sw = open(f"{PROJECT_ROOT}/sw.js", encoding="utf-8").read()
    loader = open(f"{PROJECT_ROOT}/manifest-loader.js", encoding="utf-8").read()
    manifest = json.load(open(f"{PROJECT_ROOT}/manifest-zh.json", encoding="utf-8"))
    check("manifeste chinois valide, déclaré zh-CN, en cache et choisi par le chargeur",
          manifest["lang"] == "zh-CN" and manifest["short_name"] == "我的食谱" and '"./manifest-zh.json"' in sw and '"zh"' in loader)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 320, "height": 700})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(url, timeout=15000)
        page.evaluate("() => appReady")

        fr = page.evaluate("() => TRANSLATIONS.fr")
        missing = [k for k in fr if k not in zh]
        extra = [k for k in zh if k not in fr]
        check("mêmes clés que le français", not missing and not extra, (missing[:5], extra[:5]))
        bad_ph = [k for k in fr if k in zh and set(re.findall(r"\{\w+\}", fr[k])) != set(re.findall(r"\{\w+\}", zh[k]))]
        check("mêmes {variables} que le français", not bad_ph, bad_ph[:5])
        empty = [k for k, v in zh.items() if not v.strip() and fr.get(k, "").strip()]
        check("aucun texte vide", not empty, empty)
        plural = [k for k, v in zh.items() if "(s)" in v]
        check("aucun « (s) » à la française", not plural, plural)
        latin_only = [k for k, v in zh.items() if re.search(r"[A-Za-zÀ-ÿ]{4,}", v) and not re.search(r"[一-鿿]", v)]
        # Formats et exemples sans mot à traduire : adresse d'exemple,
        # « {size} MB », résultat de conversion, « {meal}：{names} ».
        allowed = {"import_url_placeholder", "unitconv_result", "diagnostic_storage_used_value", "planning_ics_summary"}
        check("chaque texte contient du chinois (sauf formats et exemples)", set(latin_only) <= allowed, latin_only)

        page.evaluate("async () => { await ensureUiTranslationsLoaded('zh'); setLang('zh'); state.screen = 'home'; render(); }")
        r = page.evaluate("""() => ({
            lang: document.documentElement.lang,
            title: document.title,
            meta: SUPPORTED_LANGUAGES.find(l => l.code === 'zh'),
            allergens: ALLERGEN_OPTIONS.map(translateAllergen),
            rayons: RAYON_ORDER.map(r => RAYON_TRANSLATIONS.zh[r.toLowerCase()]),
            lv: labelValue('估计总额', '3 €'), pr: paren(2), sep: listSeparator(),
            tags: normalizeRecipeTags('快手，家常、省钱,素食'),
            terms: parseIngredientTerms('鸡肉，番茄、蘑菇；牛奶').length,
        })""")
        check("attribut lang « zh-CN » (caractères simplifiés), titre de page chinois", r["lang"] == "zh-CN" and r["title"] == "我的食谱", (r["lang"], r["title"]))
        check("langue proposée : 简体中文", r["meta"] and r["meta"]["nativeName"] == "简体中文", r["meta"])
        check("14 allergènes traduits", all(re.search(r"[一-鿿]", a) for a in r["allergens"]), r["allergens"])
        check("8 rayons traduits", all(x and re.search(r"[一-鿿]", x) for x in r["rayons"]), r["rayons"])
        check("ponctuation chinoise : « ： », « （） », « ， »", r["lv"] == "估计总额：3 €" and r["pr"] == "（2）" and r["sep"] == "，", (r["lv"], r["pr"], r["sep"]))
        check("virgules chinoises acceptées (étiquettes)", r["tags"] == ["快手", "家常", "省钱", "素食"], r["tags"])
        check("virgules chinoises acceptées (recherche par ingrédient)", r["terms"] == 4, r["terms"])

        styles = page.evaluate("""() => {
            const label = document.createElement('div'); label.className = 'section-label'; label.textContent = '标签'; document.body.appendChild(label);
            const out = { body: getComputedStyle(document.body).fontFamily, spacing: getComputedStyle(label).letterSpacing };
            label.remove(); return out;
        }""")
        check("polices chinoises du système dans la pile", "PingFang SC" in styles["body"] and "Noto Sans CJK SC" in styles["body"], styles["body"])
        check("pas d'espacement de lettres sur les petits titres", styles["spacing"] in ("0px", "normal"), styles["spacing"])

        for screen in ("home", "pantry", "recipes", "shopping"):
            t = page.evaluate("""(sc) => { state.screen = sc; render(); const h = document.querySelector('.topbar-title h1:not(.subtitle)');
                return { text: h.textContent, fits: h.scrollWidth <= h.clientWidth, size: parseFloat(getComputedStyle(h).fontSize) }; }""", screen)
            check(f"titre « {t['text']} » ({screen}) : une ligne, entier, ≥ 20 px", t["fits"] and t["size"] >= 20, t)

        spoken = page.evaluate("""() => {
            let lang = null;
            const orig = window.speechSynthesis;
            window.SpeechSynthesisUtterance = function (text) { this.text = text; };
            Object.defineProperty(window, 'speechSynthesis', { value: { cancel() {}, speak(u) { lang = u.lang; } }, configurable: true });
            speakText('你好');
            return lang;
        }""")
        check("lecture à voix haute en zh-CN", spoken == "zh-CN", spoken)

        # Retour au français : ponctuation française inchangée.
        r = page.evaluate("async () => { setLang('fr'); return { lv: labelValue('Total estimé', '3 €'), pr: paren(2), sep: listSeparator(), lang: document.documentElement.lang }; }")
        check("français inchangé : « Total estimé : 3 € », « (2) », « , »", r == {"lv": "Total estimé : 3 €", "pr": " (2)", "sep": ", ", "lang": "fr"}, r)
        check("aucune erreur JS", not errors, errors)

        # Téléphone réglé en chinois, premier lancement : interface en chinois.
        ctx = browser.new_context(locale="zh-CN", viewport={"width": 320, "height": 700})
        p2 = ctx.new_page()
        p2.goto(url, timeout=15000)
        p2.evaluate("() => appReady")
        r = p2.evaluate("() => ({ lang: CURRENT_LANG, html: document.documentElement.lang, manifest: document.getElementById('app-manifest') && document.getElementById('app-manifest').getAttribute('href') })")
        check("téléphone en zh-CN : interface et manifeste chinois dès le premier lancement",
              r["lang"] == "zh" and r["html"] == "zh-CN" and r["manifest"] == "manifest-zh.json", r)
        ctx.close()
        browser.close()
    httpd.shutdown()
    ok = all(results)
    print("\n=== Résumé ===")
    print("TOUT CORRECT" if ok else "ÉCHECS DÉTECTÉS")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
