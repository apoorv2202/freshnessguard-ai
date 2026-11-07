#!/usr/bin/env bash
# API-only Bifrost build for the end-to-end fixture test. Production UI is separate.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UPSTREAM="${1:-$ROOT/work/bifrost}"
UPSTREAM="$(cd "$UPSTREAM" && pwd)"
[[ "$(git -C "$UPSTREAM" rev-parse HEAD)" == afdce01b50a78199f59e38117cd4d5952d038b07 ]] || { echo "Unexpected upstream commit"; exit 1; }
mkdir -p "$ROOT/work/gateway-build" "$ROOT/work/build"
# The upstream executable embeds a built UI. An explicit API-only placeholder
# lets the unmodified HTTP backend be tested without a separate npm/UI build.
mkdir -p "$UPSTREAM/transports/bifrost-http/ui"
if [[ ! -f "$UPSTREAM/transports/bifrost-http/ui/index.html" ]]; then
  printf '%s\n' '<!doctype html><title>Bifrost API-only test build</title><p>API-only test build. Build the upstream UI for the dashboard.</p>' > "$UPSTREAM/transports/bifrost-http/ui/index.html"
fi
cd "$ROOT/work/gateway-build"
unset GOWORK
if [[ ! -f go.work ]]; then go work init; fi
go work use "$ROOT/integrations/bifrost" "$UPSTREAM/core" "$UPSTREAM/framework" "$UPSTREAM/transports"
for module in "$UPSTREAM"/plugins/*/go.mod; do go work use "$(dirname "$module")"; done
export GOWORK="$PWD/go.work" CGO_ENABLED=1
# Workspace-level replacement overrides the bootstrap relative path in the
# example plugin module without changing repository go.mod or credentials.
go work edit "-dropreplace=github.com/maximhq/bifrost/core"
go work edit "-replace=github.com/maximhq/bifrost/core@v0.0.0=$UPSTREAM/core"
# The pinned upstream framework/transports require this version in their graph.
go work edit "-replace=github.com/maximhq/bifrost/core@v1.14.1=$UPSTREAM/core"
cd "$ROOT/integrations/bifrost"
go build -p 2 -buildmode=plugin -o "$ROOT/work/build/freshnessguard.so" .
cd "$UPSTREAM/transports"
go build -p 2 -o "$ROOT/work/build/bifrost-http" ./bifrost-http
echo "Built matching API-only gateway and FreshnessGuard plugin"
