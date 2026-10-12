def test_frontend_routes_assets_and_api_remain_available(client):
    for path in ["/demo", "/demo/", "/demo/dang-nhap", "/demo/dang-ky", "/demo/doi", "/demo/quan-tri", "/main"]:
        response = client.get(path)
        assert response.status_code == 200
        assert 'lang="vi"' in response.text
        assert "/assets/js/app.js" in response.text
    assert client.get("/", follow_redirects=False).headers["location"] == "/demo"
    assert client.get("/assets/css/style.css").status_code == 200
    assert client.get("/assets/js/app.js").status_code == 200
    assert client.get("/assets/js/api.js").status_code == 200
    assert client.get("/assets/../.env").status_code == 404
    assert client.get("/docs").status_code == 200
    assert client.get("/api/health").json()["status"] == "ok"
