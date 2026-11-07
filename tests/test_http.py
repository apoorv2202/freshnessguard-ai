import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from freshnessguard.clients import BifrostLLM, TavilySearch
from freshnessguard.fixtures import ANSWER, demo_verifier
from freshnessguard.server import make_server
from unittest.mock import patch


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = make_server(demo_verifier, "test-token", port=0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join()

    def post(self, path, body, token="test-token"):
        request = Request(self.url + path, data=json.dumps(body).encode(),
                          headers={"Content-Type":"application/json", "Authorization":"Bearer " + token})
        with urlopen(request, timeout=5) as response:
            return json.load(response)

    def test_roundtrip_annotation(self):
        result = self.post("/annotate", {"choices":[{"index":0,"message":{"content":ANSWER}}]})
        self.assertEqual(result["freshnessguard"]["reports"][0]["report"]["freshness_score"], 50)

    def test_authentication(self):
        with self.assertRaises(HTTPError) as error:
            self.post("/verify", {"answer":ANSWER}, token="wrong")
        self.assertEqual(error.exception.code, 401)

    def test_bad_answer_is_400(self):
        with self.assertRaises(HTTPError) as error:
            self.post("/verify", {"answer":None})
        self.assertEqual(error.exception.code, 400)

    def test_real_tavily_wire_contract(self):
        with patch.dict("os.environ", {"TAVILY_API_KEY":"test-only"}), patch("freshnessguard.clients.post_json") as post:
            post.return_value = {"results":[], "usage":{"credits":1}}
            TavilySearch().search("current release")
            args = post.call_args.args
            self.assertEqual(args[0], "https://api.tavily.com/search")
            self.assertEqual(args[1]["search_depth"], "basic")
            self.assertTrue(args[1]["include_usage"])
            self.assertTrue(args[1]["include_published_date"])
            self.assertEqual(args[2]["Authorization"], "Bearer test-only")

    def test_bifrost_request_bypasses_recursive_verification(self):
        with patch.dict("os.environ", {"BIFROST_MODEL":"provider/model"}), patch("freshnessguard.clients.post_json") as post:
            post.return_value = {"choices":[{"message":{"content":'{"claims":[]}'}}]}
            self.assertEqual(BifrostLLM().complete("extract", {}), {"claims":[]})
            self.assertEqual(post.call_args.args[2]["x-freshnessguard-internal"], "1")
            self.assertFalse(post.call_args.args[1]["stream"])
