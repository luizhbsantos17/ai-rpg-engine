from app import __version__


def test_health_returns_ok(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "version": __version__, "env": "test"}


def test_unknown_api_route_returns_json_404(client):
    response = client.get("/api/nao-existe")
    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == 404


def test_unexpected_error_returns_json_500_without_details(flask_app):
    @flask_app.get("/api/_falha")
    def falha():
        raise RuntimeError("detalhe-interno-secreto")

    response = flask_app.test_client().get("/api/_falha")
    assert response.status_code == 500
    assert response.get_json()["error"]["code"] == 500
    assert "detalhe-interno-secreto" not in response.get_data(as_text=True)
