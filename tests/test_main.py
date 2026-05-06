import importlib
import sys


def import_main(monkeypatch):
    monkeypatch.setenv("GMO_API_KEY", "test-key")
    monkeypatch.setenv("GMO_SECRET_KEY", "test-secret")
    sys.modules.pop("main", None)
    return importlib.import_module("main")


def test_get_run_config_defaults_to_stdio(monkeypatch):
    main = import_main(monkeypatch)
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)

    assert main.get_run_config() == {"transport": "stdio"}


def test_get_run_config_supports_http_transport(monkeypatch):
    main = import_main(monkeypatch)
    monkeypatch.setenv("MCP_TRANSPORT", "http")
    monkeypatch.setenv("MCP_HTTP_HOST", "127.0.0.1")
    monkeypatch.setenv("MCP_HTTP_PORT", "9000")
    monkeypatch.setenv("MCP_HTTP_PATH", "/mcp")

    assert main.get_run_config() == {
        "transport": "http",
        "host": "127.0.0.1",
        "port": 9000,
        "path": "/mcp",
    }


def test_run_server_uses_configured_transport(monkeypatch):
    main = import_main(monkeypatch)
    monkeypatch.setenv("MCP_TRANSPORT", "http")
    monkeypatch.setenv("MCP_HTTP_HOST", "127.0.0.1")
    monkeypatch.setenv("MCP_HTTP_PORT", "9000")

    class FakeServer:
        def __init__(self):
            self.run_kwargs = None

        def run(self, **kwargs):
            self.run_kwargs = kwargs

    server = FakeServer()
    main.run_server(server)

    assert server.run_kwargs == {
        "transport": "http",
        "host": "127.0.0.1",
        "port": 9000,
    }


def test_get_run_config_rejects_unknown_transport(monkeypatch):
    main = import_main(monkeypatch)
    monkeypatch.setenv("MCP_TRANSPORT", "websocket")

    try:
        main.get_run_config()
    except ValueError as exc:
        assert "MCP_TRANSPORT" in str(exc)
    else:
        raise AssertionError("expected ValueError")
