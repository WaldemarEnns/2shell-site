"""Umami (selbst gehostet): Script nur in der Produktion, Fußzeile und Datenschutzerklärung."""
import json, pathlib, sys, unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
import build  # noqa: E402
from check_dist import umami_problems  # noqa: E402

FOOT = "Gesetzt in Fraunces und IBM Plex. Keine Cookies. Seitenaufrufe zähle ich anonym mit Umami auf meinem eigenen Server."
DATA = {"stand": "2026-10-26T02:30:45Z", "meta": {}, "advisories": [{"id": "CVE-2026-111497", "aliases": {"nicknames": ["Node2Shell", "HTTP2Shell"]}}]}


class Umami(unittest.TestCase):
    def tearDown(self):
        build.PROD[0] = False

    def test_tag_only_in_prod(self):
        build.PROD[0] = False
        self.assertEqual(build.umami_tag(), "")
        build.PROD[0] = True
        tag = build.umami_tag()
        self.assertIn('src="https://umami.alphabyte-solutions.com/script.js"', tag)
        self.assertIn(f'data-website-id="{build.UMAMI_ID}"', tag)
        self.assertEqual(umami_problems(tag), [])

    def test_check_flags_missing_or_double_tag(self):
        self.assertTrue(umami_problems("<html></html>"))
        build.PROD[0] = True
        self.assertTrue(umami_problems(build.umami_tag() * 2))

    def test_footer(self):
        build.PROD[0] = True
        html = build.footer(DATA)
        self.assertIn(f"<p>{FOOT}</p>", html)
        self.assertNotIn("Keine Tracker", html)
        self.assertIn('href="/datenschutz"', html)

    def test_privacy_text(self):
        import re
        t = re.sub(r"^\s*<!--.*?-->", "", (ROOT / "legal/datenschutz.html").read_text(), flags=re.S)
        for want in ("<h3>Umami</h3>", "umami.alphabyte-solutions.com", "auf meinem eigenen Server in Deutschland", "in Deutschland",
                     "Umami setzt keine Cookies", "Deine IP-Adresse wird von Umami nicht gespeichert"):
            self.assertIn(want, t)
        self.assertNotIn("Selbstcheck", t)
        self.assertNotIn("Kurztermin buchen", t)
        for bad in ("Telefax", "Werbung", "Kontaktformular", "Newsletter", "Externes Hosting", "extern gehostet",
                    "Die Einwilligung ist jederzeit widerrufbar", "nach deiner Einwilligung"):
            self.assertNotIn(bad, t)
        for bad in re.findall(r"\b(?:[Ww]ir|uns|[Uu]nser\w*)\b", t):
            self.fail(f"Wir-Form in der Datenschutzerklärung: {bad}")
        self.assertIn("0173 6824410", t)
        self.assertIn("<h2>5. Statistik</h2>", t)

    def test_privacy_footer(self):
        build.PROD[0] = True
        html = build.footer(DATA, "datenschutz")
        self.assertNotIn("Stand", html)
        self.assertIn('href="/datenschutz" aria-current="page"', html)
        self.assertIn(f"<p>{FOOT}</p>", html)
        self.assertIn("Stand", build.footer(DATA))
        self.assertNotIn("aria-current", build.footer(DATA))


if __name__ == "__main__":
    unittest.main()
