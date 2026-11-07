#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UPSTREAM="${1:-$ROOT/work/bifrost}"
UPSTREAM="$(cd "$UPSTREAM" && pwd)"
export GOWORK=off CGO_ENABLED=1
cd "$ROOT/integrations/loader"
go mod edit "-replace=github.com/maximhq/bifrost/core=$UPSTREAM/core"
go mod edit "-replace=github.com/maximhq/bifrost/framework=$UPSTREAM/framework"
go mod tidy
# Shared workspace ensures matching transitive dependency versions for plugin and host.
mkdir -p "$ROOT/work/loader-build"
cd "$ROOT/work/loader-build"
unset GOWORK
if [[ ! -f go.work ]]; then go work init; fi
go work use "$ROOT/integrations/bifrost" "$ROOT/integrations/loader" "$UPSTREAM/core" "$UPSTREAM/framework"
export GOWORK="$PWD/go.work"
go work sync
cd "$ROOT/integrations/bifrost"
go build -buildmode=plugin -o "$ROOT/work/build/freshnessguard.so" .
cd "$ROOT/integrations/loader"
go run . "$ROOT/work/build/freshnessguard.so"
