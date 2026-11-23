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

    def test_the_old_builder_link_goes_home_and_the_chat_is_gone(self):
        self.assertEqual(self.c.get("/builder", follow_redirects=False).headers["location"], "/")
        for path in ("/api/chat", "/api/home", "/dev"):
            self.assertIn(self.c.post(path, json={}).status_code, (404, 405), path)

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

    def test_bad_input_is_a_clean_error_not_a_crash(self):
        self.assertEqual(self.c.post("/api/build", json={"request": "   "}).status_code, 400)
        self.assertEqual(self.c.post("/api/build/zip", json={"request": "ابغى لعبة"}).status_code, 400)
        bad = self.c.post("/api/build/edit", json={"spec": {"kind": 5}, "instruction": "غير اللون"}).json()
        self.assertFalse(bad["ok"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
