"""python3 -m unittest discover -s tests"""
import pathlib, sys, unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
import build  # noqa: E402
from check_dist import alt_name_dupes  # noqa: E402


def data(nicks):
    return {"advisories": [{"id": "CVE-2026-111497", "aliases": {"nicknames": nicks}}]}


class Names(unittest.TestCase):
    def test_uniq_keeps_order_case_insensitive(self):
        self.assertEqual(build.uniq(["A", "b", "a", "B ", "c"]), ["A", "b", "c"])

    def test_extra_without_lead_and_duplicates(self):
        main, extra = build.names(data(["Node2Shell", "Python2Shell", "HTTP2Shell", "Broccoli2Shell"]),
                                  {"CVE-2026-111497": {"extraNicknames": ["python2shell", "node2shell", "New2Shell"]}})
        self.assertEqual(main, "Node2Shell / HTTP2Shell")
        self.assertEqual(extra, ["Python2Shell", "Broccoli2Shell", "New2Shell"])

    def test_alternate_name_has_no_duplicates(self):
        nicks = ["Node2Shell", "Python2Shell", "HTTP2Shell", "Broccoli2Shell"]
        _, extra = build.names(data(nicks), {})
        alt = build.uniq(nicks + extra)
        self.assertEqual(alt, nicks)
        self.assertEqual(alt_name_dupes({"about": {"alternateName": alt}}), [])

    def test_check_finds_duplicates(self):
        self.assertTrue(alt_name_dupes({"about": {"alternateName": ["X", "x"]}}))


if __name__ == "__main__":
    unittest.main()
