# MCP Registry publication

This document is for maintainers who publish this server to the official MCP Registry.
User-facing setup instructions stay in the root `README.md`.

## Registry metadata

The root `server.json` publishes this server as `io.github.RikitoNoto/gmocoin-fx-mcp`.
It points to the versioned GHCR image `ghcr.io/rikitonoto/gmocoin-fx-mcp:1.0.0` and uses `stdio` transport.

## Authentication setup

GitHub OIDC is the recommended authentication method for publishing from GitHub Actions.
No dedicated MCP Registry secret is required, but the workflow must grant `id-token: write` so `mcp-publisher login github-oidc` can request a GitHub Actions OIDC token.
The namespace also needs to match the GitHub repository owner; this server uses the `io.github.RikitoNoto/gmocoin-fx-mcp` namespace.

## Release checklist

The `.github/workflows/release.yaml` workflow publishes releases from the version in `pyproject.toml`.
When it runs, the workflow:

1. Updates the root `server.json` `version` and OCI image tag to match `pyproject.toml`.
2. Commits the updated `server.json` when a change is needed.
3. Creates the matching Git tag and GitHub release.
4. Builds and publishes the versioned GHCR image.
5. Authenticates to the MCP Registry with GitHub OIDC and publishes the server metadata.

Before publishing a new registry version, keep the Docker image label
`io.modelcontextprotocol.server.name=io.github.RikitoNoto/gmocoin-fx-mcp` in the image so the MCP Registry can verify OCI ownership.

For local validation or manual recovery, use the official CLI:

```bash
mcp-publisher validate
mcp-publisher login github
mcp-publisher publish
```
