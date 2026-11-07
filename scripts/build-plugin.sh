#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UPSTREAM="${1:-$ROOT/work/bifrost}"
PIN=afdce01b50a78199f59e38117cd4d5952d038b07
if [[ ! -d "$UPSTREAM/.git" ]]; then
  mkdir -p "$(dirname "$UPSTREAM")"
  git init "$UPSTREAM"
  git -C "$UPSTREAM" remote add origin https://github.com/maximhq/bifrost.git
  git -C "$UPSTREAM" fetch --depth 1 origin "$PIN"
  git -C "$UPSTREAM" checkout --detach FETCH_HEAD
fi
UPSTREAM="$(cd "$UPSTREAM" && pwd)"
ACTUAL="$(git -C "$UPSTREAM" rev-parse HEAD)"
[[ "$ACTUAL" == "$PIN" ]] || { echo "Expected upstream $PIN; got $ACTUAL"; exit 1; }
export GOWORK=off CGO_ENABLED=1
mkdir -p "$ROOT/work/build"
cd "$ROOT/integrations/bifrost"
go mod edit "-replace=github.com/maximhq/bifrost/core=$UPSTREAM/core"
go mod tidy
go test ./... -count=1
go test -run '^$' -bench BenchmarkDisabledHook -benchmem ./...
go build -buildmode=plugin -o "$ROOT/work/build/freshnessguard.so" .
echo "Built $ROOT/work/build/freshnessguard.so against $PIN"
