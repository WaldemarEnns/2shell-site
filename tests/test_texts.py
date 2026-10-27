"""Freigegebene Namens-Texte (texte.md) für CVE-2026-111497.

Fixture-Tests laufen immer. Die Tests gegen die echten Daten laufen nur mit
CHECK_LIVE_TEXTS=1 und vorhandenem data/2shell.json (in CI), damit ein neuer
Spitzname in 2shell-data den Coolify-Build nicht blockiert.
"""
import json, os, pathlib, sys, unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
import build  # noqa: E402
from check_dist import name_dupes  # noqa: E402

NICKS = ["Node2Shell", "Python2Shell", "HTTP2Shell", "Broccoli2Shell"]  # Stand 2shell-data main, 24.10.2026
DESC = ("CVE-2026-111497, bekannt als Node2Shell und HTTP2Shell, auch Python2Shell und Broccoli2Shell: "
        "Fehler im Brotli-Decoder 1.0.3 bis 1.2.0. Betroffene Versionen, Prüfbefehle und Updates für "
        "Node.js, Bun, Python und die PHP-Erweiterung brotli.")
H1_ALIAS = "CVE-2026-111497, auch Python2Shell und Broccoli2Shell"
AKA = "auch Python2Shell, Broccoli2Shell"
OVERVIEW_DESC = ("Aktuelle 2shell-Lücken mit betroffenen Versionen und Fixes: PHP2Shell (CVE-2026-109618, "
                 "CVE-2026-109619) und Node2Shell / HTTP2Shell (CVE-2026-111497). Notfall-Check zum Festpreis "
                 "von Waldemar Enns.")


def fixture(nicks=NICKS):
    return {"advisories": [{"id": "CVE-2026-111497", "aliases": {"nicknames": nicks}}]}


class FixtureTexts(unittest.TestCase):
    def test_exact_texts(self):
        t = build.alias_texts(fixture(), {})
        self.assertEqual(t["desc_advisory"], DESC)
        self.assertEqual(t["h1_alias"], H1_ALIAS)
        self.assertEqual(t["aka"], AKA)
        self.assertEqual(t["desc_overview_names"], "Node2Shell / HTTP2Shell")

    def test_each_name_once(self):
        t = build.alias_texts(fixture(NICKS + ["node2shell", "PYTHON2SHELL"]), {})
        for key in ("desc_advisory", "h1_alias", "aka", "desc_overview_names"):
            self.assertEqual(name_dupes(t[key], key), [], key)
        self.assertEqual(t["desc_advisory"], DESC)

    def test_check_catches_duplicates(self):
        self.assertTrue(name_dupes("bekannt als Node2Shell und Python2Shell, auch Python2Shell", "x"))


@unittest.skipUnless(os.environ.get("CHECK_LIVE_TEXTS") == "1" and (ROOT / "data/2shell.json").is_file(),
                     "nur mit CHECK_LIVE_TEXTS=1 und data/2shell.json")
class LiveTexts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "data/2shell.json").read_text(encoding="utf-8"))
        cls.ov = json.loads((ROOT / "data/overlay.json").read_text(encoding="utf-8"))
        cls.adv_html = build.advisory(cls.data, cls.ov, "")
        cls.ov_html = build.overview(cls.data, cls.ov, "")

    def test_advisory(self):
        self.assertIn(f'<meta name="description" content="{DESC}">', self.adv_html)
        self.assertIn(f'<span class="alias">{H1_ALIAS}</span>', self.adv_html)

    def test_overview(self):
        self.assertIn(f'<p class="aka">{AKA}</p>', self.ov_html)
        self.assertIn(f'<meta name="description" content="{OVERVIEW_DESC}">', self.ov_html)

    def test_no_hours_or_weekday_promises(self):
        # Waldemar, 27.10.2026: kein Hinweis auf Freitag-/Samstagabend und keine 48-Stunden-Zusage
        for html in (self.adv_html, self.ov_html):
            for s in ("Freitagabend", "Samstagabend", "48 Stunden", "48h", "48 h", "Werktagen"):
                self.assertNotIn(s, html)


if __name__ == "__main__":
    unittest.main()
