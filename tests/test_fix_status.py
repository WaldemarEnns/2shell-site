"""Fix-Status auf Deutsch und die Pill „Fix auf GitHub“ (fixAvailability aus 2shell-data)."""
import pathlib, sys, unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT)]
import build  # noqa: E402

REF = {"url": "https://github.com/kjdev/php-ext-brotli/pull/105", "label": "PR #105 · Update brotli submodule to v1.2.1"}
AVAIL = {"state": "upstream_only", "registry": "PECL", "url": "https://github.com/kjdev/php-ext-brotli/releases/tag/0.21.1",
         "label": "Release 0.21.1 auf GitHub", "note": "Auf GitHub veröffentlicht, auf PECL noch nicht verfügbar."}


class FixStatus(unittest.TestCase):
    def test_pr_states_german(self):
        for st, de in (("open", "offen"), ("merged", "gemergt"), ("closed", "geschlossen")):
            html = build.pill("pending", {**REF, "state": st})
            self.assertIn(f"PR #105 ({de})", html)
            self.assertNotIn(f"({st})", html)

    def test_missing_state(self):
        self.assertIn("(Stand unbekannt)", build.pill("pending", REF))

    def test_upstream_only_pill(self):
        x = {"fixStatus": "fixed", "fixAvailability": AVAIL}
        html = build.pill("fixed", None, build.upstream_only(x))
        self.assertIn('class="pill neu"', html)
        self.assertIn(">Fix auf GitHub<", html)
        self.assertIn(AVAIL["url"], html)

    def test_available_is_plain_fixed(self):
        x = {"fixStatus": "fixed", "fixAvailability": {**AVAIL, "state": "available"}}
        self.assertIsNone(build.upstream_only(x))
        self.assertEqual(build.pill("fixed", None, build.upstream_only(x)), '<span class="pill ok">gepatcht</span>')


if __name__ == "__main__":
    unittest.main()
