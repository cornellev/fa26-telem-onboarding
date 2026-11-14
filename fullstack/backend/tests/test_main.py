import unittest
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from main import app


SAMPLE = {
    "id": 25,
    "name": "pikachu",
    "height": 4,
    "weight": 60,
    "sprites": {
        "front_default": "https://example.com/sprite.png",
        "other": {"official-artwork": {"front_default": "https://example.com/art.png"}},
    },
    "types": [{"type": {"name": "electric"}}],
    "abilities": [{"ability": {"name": "static"}}],
    "stats": [{"stat": {"name": "hp"}, "base_stat": 35}],
}


class PokemonTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    @patch("main.httpx.get")
    def test_lookup_normalizes_converts_and_fetches_each_time(self, get):
        get.return_value = httpx.Response(200, json=SAMPLE, request=httpx.Request("GET", "https://pokeapi.co"))
        response = self.client.get("/api/pokemon/%20PIKACHU%20")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "pikachu")
        self.assertEqual(data["height_m"], 0.4)
        self.assertEqual(data["weight_kg"], 6.0)
        self.assertEqual(data["types"], ["electric"])
        self.assertEqual(data["image"], "https://example.com/art.png")
        self.assertEqual(data["stats"], [{"name": "hp", "value": 35}])
        self.assertEqual(self.client.get("/api/pokemon/pikachu").json(), data)
        self.assertEqual(get.call_count, 2)
        get.assert_called_with("https://pokeapi.co/api/v2/pokemon/pikachu", timeout=10.0)

    @patch("main.httpx.get")
    def test_upstream_errors(self, get):
        for upstream, expected in [(404, 404), (500, 502), (429, 502)]:
            with self.subTest(upstream=upstream):
                get.return_value = httpx.Response(upstream, request=httpx.Request("GET", "https://pokeapi.co"))
                response = self.client.get("/api/pokemon/pikachu")
                self.assertEqual(response.status_code, expected)
                self.assertIsInstance(response.json()["detail"], str)
        self.assertEqual(get.call_count, 3)

    @patch("main.httpx.get", side_effect=httpx.ReadTimeout("timeout"))
    def test_timeout(self, get):
        self.assertEqual(self.client.get("/api/pokemon/pikachu").status_code, 502)

    @patch("main.httpx.get", side_effect=httpx.ConnectError("offline"))
    def test_connection_failure(self, get):
        self.assertEqual(self.client.get("/api/pokemon/pikachu").status_code, 502)

    @patch("main.httpx.get")
    def test_missing_artwork_uses_sprite(self, get):
        get.return_value = httpx.Response(200, json={**SAMPLE, "sprites": {"front_default": "sprite.png"}}, request=httpx.Request("GET", "https://pokeapi.co"))
        self.assertEqual(self.client.get("/api/pokemon/25").json()["image"], "sprite.png")


if __name__ == "__main__":
    unittest.main()
