package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"sync/atomic"
	"testing"
	"time"

	"github.com/maximhq/bifrost/core/schemas"
)

func request() *schemas.HTTPRequest {
	return &schemas.HTTPRequest{Method: "POST", Path: "/openai/v1/chat/completions",
		Headers: map[string]string{"x-freshnessguard": "verify"}, Body: []byte(`{"stream":false}`)}
}

func validTestEnvelope() map[string]any {
	return map[string]any{"status": "checked", "reports": []any{map[string]any{"choice_index": 0,
		"report": map[string]any{"schema_version": "1", "mode": "synthetic_test", "checked_at": "2026-11-06T12:00:00Z",
			"original_answer": "Original", "status": "no_claims_extracted", "claims": []any{}, "coverage": 0,
			"freshness_score": nil, "metrics": map[string]any{}, "errors": []any{}}}}}
}

func TestHookRoundtripPreservesAnswer(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/annotate" || r.Header.Get("Authorization") != "Bearer test-token" {
			t.Error("incorrect service request")
		}
		json.NewEncoder(w).Encode(map[string]any{"choices": []any{map[string]any{"message": map[string]string{"content": "malicious rewrite"}}}, "freshnessguard": validTestEnvelope()})
	}))
	defer server.Close()
	oldURL, oldToken := serviceURL, serviceToken
	serviceURL, serviceToken = server.URL, "test-token"
	defer func() { serviceURL, serviceToken = oldURL, oldToken }()
	response := &schemas.HTTPResponse{StatusCode: 200, Headers: map[string]string{"Content-Length": "1"},
		Body: []byte(`{"choices":[{"message":{"content":"Original"}}],"usage":{"total_tokens":42}}`)}
	if err := HTTPTransportPostHook(nil, request(), response); err != nil {
		t.Fatal(err)
	}
	var result map[string]interface{}
	if err := json.Unmarshal(response.Body, &result); err != nil {
		t.Fatal(err)
	}
	if result["choices"].([]interface{})[0].(map[string]interface{})["message"].(map[string]interface{})["content"] != "Original" {
		t.Fatal("answer changed")
	}
	if result["freshnessguard"] == nil || result["usage"] == nil {
		t.Fatal("lost metadata")
	}
	if _, exists := response.Headers["Content-Length"]; exists {
		t.Fatal("stale content length")
	}
	if response.Headers["x-freshnessguard-status"] != "checked" {
		t.Fatal("valid report rejected")
	}
}

func TestAuthenticatedVerifierRedirectsNeverReachDestination(t *testing.T) {
	var destinationCalls atomic.Int32
	destination := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		destinationCalls.Add(1)
		w.WriteHeader(200)
	}))
	defer destination.Close()
	for _, code := range []int{301, 302, 303, 307, 308} {
		t.Run(http.StatusText(code), func(t *testing.T) {
			redirect := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				w.Header().Set("Location", destination.URL)
				w.WriteHeader(code)
			}))
			defer redirect.Close()
			oldURL, oldToken := serviceURL, serviceToken
			serviceURL, serviceToken = redirect.URL, "synthetic-test-only"
			defer func() { serviceURL, serviceToken = oldURL, oldToken }()
			response := &schemas.HTTPResponse{StatusCode: 200, Body: []byte(`{"choices":[{"message":{"content":"Original"}}],"usage":{"total_tokens":42}}`)}
			HTTPTransportPostHook(nil, request(), response)
			if response.Headers["x-freshnessguard-error"] != "verifier_redirect_blocked" || response.Headers["x-freshnessguard-status"] != "unavailable" {
				t.Fatal("redirect was not explicit")
			}
			var result map[string]json.RawMessage
			json.Unmarshal(response.Body, &result)
			if string(result["usage"]) != `{"total_tokens":42}` {
				t.Fatal("usage changed")
			}
			var failure struct {
				Error struct {
					Code string `json:"code"`
				} `json:"error"`
			}
			json.Unmarshal(result["freshnessguard"], &failure)
			if failure.Error.Code != "verifier_redirect_blocked" {
				t.Fatal("missing structured error")
			}
		})
	}
	if destinationCalls.Load() != 0 {
		t.Fatal("credentials or completion reached redirect target")
	}
}

func TestCheckedEnvelopeShapeAndChoiceCorrespondence(t *testing.T) {
	mutations := []struct {
		name   string
		change func(map[string]any)
	}{
		{"empty reports", func(e map[string]any) { e["reports"] = []any{} }},
		{"null reports", func(e map[string]any) { e["reports"] = nil }},
		{"missing report", func(e map[string]any) { delete(e["reports"].([]any)[0].(map[string]any), "report") }},
		{"wrong choice", func(e map[string]any) { e["reports"].([]any)[0].(map[string]any)["choice_index"] = 1 }},
		{"missing choice", func(e map[string]any) { delete(e["reports"].([]any)[0].(map[string]any), "choice_index") }},
		{"changed answer", func(e map[string]any) { testReport(e)["original_answer"] = "Changed" }},
		{"unknown status", func(e map[string]any) { testReport(e)["status"] = "invented" }},
		{"missing claims", func(e map[string]any) { delete(testReport(e), "claims") }},
		{"bad claim", func(e map[string]any) {
			testReport(e)["claims"] = []any{map[string]any{"text": "x", "verdict": "supported"}}
		}},
		{"missing evidence fields", func(e map[string]any) {
			testReport(e)["claims"] = []any{map[string]any{"text": "x", "verdict": "supported", "time_sensitive": true}}
		}},
		{"fabricated quote", func(e map[string]any) {
			testReport(e)["claims"] = []any{map[string]any{"text": "x", "verdict": "supported", "time_sensitive": true,
				"sources":      []any{map[string]any{"id": "s1", "url": "https://vendor.test/", "content": "Actual source text"}},
				"citation_ids": []string{"s1"}, "quotes": []any{map[string]any{"source_id": "s1", "text": "Invented quote"}}, "correction": nil}}
		}},
		{"bad coverage", func(e map[string]any) { testReport(e)["coverage"] = 2 }},
		{"bad score", func(e map[string]any) { testReport(e)["freshness_score"] = "100" }},
		{"missing metrics", func(e map[string]any) { delete(testReport(e), "metrics") }},
		{"missing errors", func(e map[string]any) { delete(testReport(e), "errors") }},
		{"invalid timestamp", func(e map[string]any) { testReport(e)["checked_at"] = "today" }},
		{"false no text", func(e map[string]any) { e["status"] = "no_text_to_check"; e["reports"] = []any{} }},
	}
	for _, mutation := range mutations {
		t.Run(mutation.name, func(t *testing.T) {
			envelope := validTestEnvelope()
			mutation.change(envelope)
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				json.NewEncoder(w).Encode(map[string]any{"freshnessguard": envelope})
			}))
			defer server.Close()
			old := serviceURL
			serviceURL = server.URL
			defer func() { serviceURL = old }()
			response := &schemas.HTTPResponse{StatusCode: 200, Body: []byte(`{"choices":[{"message":{"content":"Original"}}]}`)}
			HTTPTransportPostHook(nil, request(), response)
			if response.Headers["x-freshnessguard-status"] != "unavailable" || response.Headers["x-freshnessguard-error"] != "invalid_report_envelope" {
				t.Fatal("invalid envelope accepted")
			}
		})
	}
}

func testReport(e map[string]any) map[string]any {
	return e["reports"].([]any)[0].(map[string]any)["report"].(map[string]any)
}

func TestUnavailableNestedReportCannotClaimCheckedHeader(t *testing.T) {
	envelope := validTestEnvelope()
	testReport(envelope)["status"] = "upstream_error"
	raw, _ := json.Marshal(envelope)
	valid, degraded := validateEnvelope(raw, map[string]json.RawMessage{"choices": json.RawMessage(`[{"message":{"content":"Original"}}]`)})
	if !valid || !degraded {
		t.Fatal("nested unavailable status hidden")
	}
}

func TestNoTextCompletionAcceptsOnlyNoTextEnvelope(t *testing.T) {
	completion := map[string]json.RawMessage{"choices": json.RawMessage(`[{"index":0,"message":{"content":null}}]`)}
	valid, degraded := validateEnvelope(json.RawMessage(`{"status":"no_text_to_check","reports":[]}`), completion)
	if !valid || degraded {
		t.Fatal("valid no-text outcome rejected")
	}
}

func TestRejectStreamingAndMultipleChoices(t *testing.T) {
	for _, body := range []string{`{"stream":true}`, `{"n":2}`, `invalid`, `null`, `{"n":-1}`} {
		req := request()
		req.Body = []byte(body)
		resp, err := HTTPTransportPreHook(nil, req)
		if err != nil || resp == nil || resp.StatusCode != 400 {
			t.Fatal("unsupported request accepted")
		}
	}
}

func TestVerifierTimeoutIsExplicitAndPreservesResponse(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(100 * time.Millisecond)
		w.Write([]byte(`{"freshnessguard":{"status":"checked","reports":[]}}`))
	}))
	defer server.Close()
	oldURL, oldTimeout := serviceURL, serviceTimeout
	serviceURL, serviceTimeout = server.URL, 20*time.Millisecond
	defer func() { serviceURL, serviceTimeout = oldURL, oldTimeout }()
	resp := &schemas.HTTPResponse{StatusCode: 200, Body: []byte(`{"choices":[{"message":{"content":"Original"}}]}`)}
	HTTPTransportPostHook(nil, request(), resp)
	if resp.Headers["x-freshnessguard-status"] != "unavailable" {
		t.Fatal("timeout was hidden")
	}
	var body map[string]interface{}
	json.Unmarshal(resp.Body, &body)
	if body["choices"].([]interface{})[0].(map[string]interface{})["message"].(map[string]interface{})["content"] != "Original" {
		t.Fatal("original response changed")
	}
}

func TestMalformedServiceReportCannotClaimChecked(t *testing.T) {
	for _, reply := range []string{`true`, `[]`, `{"status":"checked"}`, `{"status":"invented","reports":[]}`} {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte(`{"freshnessguard":` + reply + `}`))
		}))
		old := serviceURL
		serviceURL = server.URL
		resp := &schemas.HTTPResponse{StatusCode: 200, Body: []byte(`{"choices":[]}`)}
		HTTPTransportPostHook(nil, request(), resp)
		serviceURL = old
		server.Close()
		if resp.Headers["x-freshnessguard-status"] != "unavailable" {
			t.Fatal("malformed report accepted")
		}
	}
}

func TestOptInAndRecursionBypass(t *testing.T) {
	req := request()
	req.Headers["x-freshnessguard-internal"] = "1"
	if enabled(req) {
		t.Fatal("internal call would recurse")
	}
	delete(req.Headers, "x-freshnessguard-internal")
	delete(req.Headers, "x-freshnessguard")
	if enabled(req) {
		t.Fatal("verification must be opt-in")
	}
}

func TestFailOpenExplicitlyUnverified(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(503) }))
	defer server.Close()
	old := serviceURL
	serviceURL = server.URL
	defer func() { serviceURL = old }()
	resp := &schemas.HTTPResponse{StatusCode: 200, Body: []byte(`{"choices":[]}`)}
	HTTPTransportPostHook(nil, request(), resp)
	if resp.Headers["x-freshnessguard-status"] != "unavailable" {
		t.Fatal("failure hidden")
	}
	if !json.Valid(resp.Body) {
		t.Fatal("invalid output")
	}
}

func BenchmarkDisabledHook(b *testing.B) {
	req := &schemas.HTTPRequest{Method: "POST", Path: "/openai/v1/chat/completions"}
	resp := &schemas.HTTPResponse{StatusCode: 200}
	b.ReportAllocs()
	for b.Loop() {
		HTTPTransportPostHook(nil, req, resp)
	}
}
