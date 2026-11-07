// FreshnessGuard is an opt-in Bifrost native HTTP transport plugin.
package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"net/url"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/maximhq/bifrost/core/schemas"
)

var serviceURL = "http://127.0.0.1:8765"
var serviceToken string
var configMu sync.RWMutex
var errVerifierRedirect = errors.New("verifier redirect blocked")
var client = newVerifierClient()
var serviceTimeout = 150 * time.Second

func newVerifierClient() *http.Client {
	transport := &http.Transport{}
	if base, ok := http.DefaultTransport.(*http.Transport); ok {
		transport = base.Clone()
	}
	transport.Proxy = nil
	return &http.Client{Timeout: 150 * time.Second, Transport: transport,
		CheckRedirect: func(_ *http.Request, _ []*http.Request) error { return errVerifierRedirect }}
}

func GetName() string { return "freshnessguard" }
func Cleanup() error  { client.CloseIdleConnections(); return nil }

// Configuration is read once before requests. Secrets come only from environment.
func Init(config any) error {
	nextURL := "http://127.0.0.1:8765"
	nextTimeout := 150 * time.Second
	if cfg, ok := config.(map[string]interface{}); ok {
		if value, ok := cfg["service_url"].(string); ok {
			nextURL = strings.TrimRight(value, "/")
		}
		if raw, exists := cfg["timeout_ms"]; exists {
			value, ok := raw.(float64)
			if !ok || value < 100 || value > 150000 || value != float64(int(value)) {
				return errors.New("timeout_ms must be an integer from 100 to 150000")
			}
			nextTimeout = time.Duration(value) * time.Millisecond
		}
	}
	parsed, err := url.Parse(nextURL)
	if err != nil || parsed.Scheme != "http" || parsed.Hostname() != "127.0.0.1" || parsed.Path != "" || parsed.User != nil || parsed.RawQuery != "" || parsed.Fragment != "" {
		return errors.New("freshnessguard service_url must be a loopback http://127.0.0.1 URL")
	}
	nextToken := os.Getenv("FRESHNESSGUARD_TOKEN")
	if len(nextToken) < 24 {
		return errors.New("FRESHNESSGUARD_TOKEN must contain at least 24 characters")
	}
	configMu.Lock()
	serviceURL, serviceToken, serviceTimeout = nextURL, nextToken, nextTimeout
	configMu.Unlock()
	return nil
}

func enabled(req *schemas.HTTPRequest) bool {
	return req != nil && req.Method == "POST" &&
		strings.HasSuffix(req.Path, "/chat/completions") &&
		req.CaseInsensitiveHeaderLookup("x-freshnessguard") == "verify" &&
		req.CaseInsensitiveHeaderLookup("x-freshnessguard-internal") != "1"
}

func HTTPTransportPreHook(_ *schemas.BifrostContext, req *schemas.HTTPRequest) (*schemas.HTTPResponse, error) {
	if !enabled(req) {
		return nil, nil
	}
	var body *struct {
		Stream bool `json:"stream"`
		N      int  `json:"n"`
	}
	if len(req.Body) > 256000 || json.Unmarshal(req.Body, &body) != nil || body == nil || body.Stream || body.N > 1 || body.N < 0 {
		return &schemas.HTTPResponse{StatusCode: 400,
			Headers: map[string]string{"Content-Type": "application/json"},
			Body:    []byte(`{"error":{"message":"FreshnessGuard MVP requires non-streaming JSON chat completion with n=1 and body <=256KB"}}`)}, nil
	}
	return nil, nil
}

func HTTPTransportPostHook(ctx *schemas.BifrostContext, req *schemas.HTTPRequest, resp *schemas.HTTPResponse) error {
	if !enabled(req) || resp == nil || resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil
	}
	if resp.Headers == nil {
		resp.Headers = make(map[string]string)
	}
	var completion map[string]json.RawMessage
	if len(resp.Body) > 256000 || json.Unmarshal(resp.Body, &completion) != nil || completion == nil {
		resp.Headers["x-freshnessguard-status"] = "unavailable"
		resp.Headers["x-freshnessguard-error"] = "invalid_completion"
		return nil
	}
	var report json.RawMessage
	failureCode := "invalid_report_envelope"
	configMu.RLock()
	endpoint, token, timeout := serviceURL, serviceToken, serviceTimeout
	configMu.RUnlock()
	boundedCtx, cancel := context.WithTimeout(contextFor(ctx), timeout)
	defer cancel()
	request, err := http.NewRequestWithContext(boundedCtx, http.MethodPost, endpoint+"/annotate", bytes.NewReader(resp.Body))
	if err == nil {
		request.Header.Set("Content-Type", "application/json")
		request.Header.Set("Authorization", "Bearer "+token)
		var response *http.Response
		response, err = client.Do(request)
		if err == nil {
			defer response.Body.Close()
			raw, readErr := io.ReadAll(io.LimitReader(response.Body, 1000001))
			var annotated map[string]json.RawMessage
			if response.StatusCode != 200 {
				failureCode = "verifier_http_error"
			} else if readErr != nil {
				failureCode = "verifier_read_error"
			} else if len(raw) > 1000000 {
				failureCode = "verifier_response_too_large"
			} else if json.Unmarshal(raw, &annotated) == nil {
				report = annotated["freshnessguard"]
			}
		} else if errors.Is(err, errVerifierRedirect) {
			failureCode = "verifier_redirect_blocked"
		} else if errors.Is(err, context.DeadlineExceeded) {
			failureCode = "verifier_timeout"
		} else {
			failureCode = "verifier_unavailable"
		}
	} else {
		failureCode = "verifier_request_error"
	}
	status := "checked"
	validReport, degraded := validateEnvelope(report, completion)
	if !validReport {
		status = "unavailable"
		report, _ = json.Marshal(map[string]any{"status": "unavailable", "reports": []any{},
			"reason": "Verification service unavailable; original answer is unverified",
			"error":  map[string]string{"stage": "native_verifier", "category": "unavailable", "code": failureCode}})
		resp.Headers["x-freshnessguard-error"] = failureCode
	} else if degraded {
		status = "unavailable"
		resp.Headers["x-freshnessguard-error"] = "verifier_report_unavailable"
	}
	// Only merge the report. The service cannot rewrite the original answer.
	completion["freshnessguard"] = report
	if body, marshalErr := json.Marshal(completion); marshalErr == nil {
		resp.Body = body
		for key := range resp.Headers {
			if strings.EqualFold(key, "Content-Length") {
				delete(resp.Headers, key)
			}
		}
	}
	resp.Headers["x-freshnessguard-status"] = status
	return nil
}

func contextFor(ctx *schemas.BifrostContext) context.Context {
	if ctx == nil {
		return context.Background()
	}
	return ctx
}
