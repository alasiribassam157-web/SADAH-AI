"""The real FastAPI app (app.py) end to end, through its test client. Skipped where FastAPI is not installed.

Run:  python -m tests.app_test
"""
import unittest

try:
    from fastapi.testclient import TestClient

    import app as server
except ImportError:  # the offline dev box has no FastAPI; CI does
    TestClient = None


@unittest.skipIf(TestClient is None, "fastapi / httpx not installed")
class Server(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = TestClient(server.app)

    def test_the_home_page_is_the_builder_and_static_assets_load(self):
        r = self.c.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("app.js", r.text)
        self.assertEqual(r.headers["cache-control"], "no-cache")
        for path in ("/ui/app.js", "/ui/app.css", "/ui/hero.js", "/ui/style.css", "/ui/logo.svg"):
            self.assertEqual(self.c.get(path).status_code, 200, path)

    def test_the_old_builder_link_goes_home_and_the_old_endpoints_are_gone(self):
        self.assertEqual(self.c.get("/builder", follow_redirects=False).headers["location"], "/")
        for path in ("/api/home", "/dev"):
            self.assertIn(self.c.post(path, json={}).status_code, (404, 405), path)

    def test_a_project_can_be_published_to_a_link_and_opened(self):
        built = self.c.post("/api/build", json={"request": "موقع فخم لمطعم باسم السفرة"}).json()
        url = self.c.post("/api/share", json={"spec": built["spec"]}).json()["url"]
        self.assertTrue(url.startswith("/s/") and url.endswith("/"))
        page = self.c.get(url)
        self.assertEqual(page.status_code, 200)
        self.assertIn("السفرة", page.text)
        self.assertIn("صُنع بأداة", page.text)
        self.assertIn("default-src 'none'", page.headers["content-security-policy"])
        self.assertEqual(self.c.get(url + "style.css").status_code, 200)
        self.assertEqual(self.c.get(url.rstrip("/"), follow_redirects=False).headers["location"], url)
        self.assertEqual(self.c.get(url + "app.js").status_code, 404)   # a landing page has no script
        self.assertEqual(self.c.get("/s/not-a-token/").status_code, 404)
        self.assertEqual(self.c.post("/api/share", json={"spec": {"kind": "x"}}).status_code, 400)

    def test_health(self):
        self.assertEqual(self.c.get("/api/health").json(), {"status": "ok"})

    def test_build_edit_and_zip_work_over_http(self):
        built = self.c.post("/api/build", json={"request": "لعبة ثعبان باسم الافعى"}).json()
        self.assertTrue(built["ok"])
        self.assertEqual((built["kind"], built["name"]), ("game", "الافعى"))
        edited = self.c.post("/api/build/edit", json={"spec": built["spec"], "instruction": "غير اللون الى احمر"}).json()
        self.assertTrue(edited["changed"])
        z = self.c.post("/api/build/zip", json={"spec": edited["spec"]})
        self.assertEqual((z.status_code, z.headers["content-type"]), (200, "application/zip"))

    def test_the_chat_talks_and_builds_over_http(self):
        self.assertEqual(self.c.get("/api/chat/status").json(), {"engine": "rules"})
        r = self.c.post("/api/chat", json={"messages": [{"role": "user", "content": "ابغى موقع لمطعم باسم السفرة"}]}).json()
        self.assertEqual(r["engine"], "rules")
        self.assertTrue(r["build"]["ok"])
        self.assertEqual(self.c.post("/api/chat", json={"messages": "x"}).status_code, 422)
        r = self.c.post("/api/chat", json={"messages": [{"role": "user", "content": "هلا"}], "spec": None}).json()
        self.assertIsNone(r["build"])

    def test_bad_input_is_a_clean_error_not_a_crash(self):
        self.assertEqual(self.c.post("/api/build", json={"request": "   "}).status_code, 400)
        self.assertEqual(self.c.post("/api/build/zip", json={"request": "ابغى لعبة"}).status_code, 400)
        bad = self.c.post("/api/build/edit", json={"spec": {"kind": 5}, "instruction": "غير اللون"}).json()
        self.assertFalse(bad["ok"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
