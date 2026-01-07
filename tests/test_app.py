import copy
import os
import sys
from pathlib import Path
import urllib.parse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient
import pytest

import app as app_module


@pytest.fixture(autouse=True)
def reset_activities():
    original = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original)


client = TestClient(app_module.app)


def test_root_redirect():
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code in (301, 302, 307)
    assert resp.headers["location"] == "/static/index.html"


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert "Soccer Team" in data
    assert isinstance(data["Soccer Team"]["participants"], list)


def test_signup_and_duplicate():
    name = urllib.parse.quote("Soccer Team", safe="")
    email = "tester@example.com"

    resp = client.post(f"/activities/{name}/signup", params={"email": email})
    assert resp.status_code == 200
    assert email in app_module.activities["Soccer Team"]["participants"]

    # duplicate signup should return 400
    resp2 = client.post(f"/activities/{name}/signup", params={"email": email})
    assert resp2.status_code == 400


def test_unregister_and_notfound():
    name = urllib.parse.quote("Basketball Team", safe="")
    email = "ethan@mergington.edu"  # pre-existing participant

    resp = client.post(f"/activities/{name}/unregister", params={"email": email})
    assert resp.status_code == 200
    assert email not in app_module.activities["Basketball Team"]["participants"]

    # unregister someone not in activity
    resp2 = client.post(f"/activities/{name}/unregister", params={"email": "noone@x.com"})
    assert resp2.status_code == 404
