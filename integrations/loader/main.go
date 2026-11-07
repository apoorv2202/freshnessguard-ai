// Execute the plugin via Bifrost's actual OSS loader, against the Python service.
// This is a loader integration smoke test, not the full Bifrost HTTP server.
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"time"

	"github.com/maximhq/bifrost/core/schemas"
	"github.com/maximhq/bifrost/framework/plugins"
)

func main() {
	if len(os.Args) != 2 {
		panic("usage: loader-smoke /absolute/path/freshnessguard.so")
	}
	loader := &plugins.SharedObjectPluginLoader{}
	base, err := loader.LoadPlugin(os.Args[1], map[string]interface{}{"service_url": "http://127.0.0.1:8765"})
	if err != nil {
		panic(err)
	}
	defer base.Cleanup()
	hook, ok := base.(schemas.HTTPTransportPlugin)
	if !ok {
		panic("plugin did not implement HTTP transport interface")
	}
	ctx, cancel := schemas.NewBifrostContextWithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	req := &schemas.HTTPRequest{Method: "POST", Path: "/openai/v1/chat/completions",
		Headers: map[string]string{"x-freshnessguard": "verify"}, Body: []byte(`{"stream":false}`)}
	short, err := hook.HTTPTransportPreHook(ctx, req)
	if err != nil || short != nil {
		panic("pre-hook unexpectedly rejected non-streaming request")
	}
	resp := &schemas.HTTPResponse{StatusCode: 200, Body: []byte(`{"id":"smoke","choices":[{"index":0,"message":{"role":"assistant","content":"The latest stable version of ExampleSDK is 3.0."}}],"usage":{"total_tokens":10}}`)}
	if err := hook.HTTPTransportPostHook(ctx, req, resp); err != nil {
		panic(err)
	}
	var result struct {
		Freshnessguard struct {
			Reports []struct {
				Report struct {
					Mode   string `json:"mode"`
					Claims []struct {
						Verdict string `json:"verdict"`
					} `json:"claims"`
				} `json:"report"`
			} `json:"reports"`
		} `json:"freshnessguard"`
	}
	if err := json.Unmarshal(resp.Body, &result); err != nil {
		panic(err)
	}
	if len(result.Freshnessguard.Reports) != 1 || len(result.Freshnessguard.Reports[0].Report.Claims) != 1 || result.Freshnessguard.Reports[0].Report.Claims[0].Verdict != "outdated" || result.Freshnessguard.Reports[0].Report.Mode != "synthetic_fixture" {
		panic("unexpected verification report (fixture service must be running)")
	}
	fmt.Println(string(resp.Body))
	fmt.Println("PASS: Bifrost OSS loader -> native plugin -> Python verification -> cited fixture report")
}
