package main

import (
	"encoding/json"
	"strings"
	"time"
)

// Validate the service contract and correspondence, not semantic truth. The
// authenticated Python validator remains responsible for evidence entailment.
func validateEnvelope(raw json.RawMessage, completion map[string]json.RawMessage) (bool, bool) {
	var choices []struct {
		Index   int    `json:"index"`
		Finish  string `json:"finish_reason"`
		Message struct {
			Content *string `json:"content"`
		} `json:"message"`
	}
	if json.Unmarshal(completion["choices"], &choices) != nil || choices == nil {
		return false, false
	}
	type expectedChoice struct {
		text       *string
		incomplete bool
	}
	expected := map[int]expectedChoice{}
	for _, choice := range choices {
		incomplete := choice.Finish == "length" || choice.Finish == "content_filter"
		if incomplete || (choice.Message.Content != nil && strings.TrimSpace(*choice.Message.Content) != "") {
			if _, exists := expected[choice.Index]; exists {
				return false, false
			}
			expected[choice.Index] = expectedChoice{choice.Message.Content, incomplete}
		}
	}
	var envelope struct {
		Status  string `json:"status"`
		Reports []struct {
			Index  *int `json:"choice_index"`
			Report struct {
				Schema   string  `json:"schema_version"`
				Mode     string  `json:"mode"`
				Checked  string  `json:"checked_at"`
				Original *string `json:"original_answer"`
				Status   string  `json:"status"`
				Claims   []struct {
					Text      string `json:"text"`
					Sensitive *bool  `json:"time_sensitive"`
					Verdict   string `json:"verdict"`
					Sources   []struct {
						ID      string `json:"id"`
						URL     string `json:"url"`
						Content string `json:"content"`
					} `json:"sources"`
					IDs    []string `json:"citation_ids"`
					Quotes []struct {
						ID   string `json:"source_id"`
						Text string `json:"text"`
					} `json:"quotes"`
					Correction json.RawMessage `json:"correction"`
				} `json:"claims"`
				Coverage *float64                   `json:"coverage"`
				Score    json.RawMessage            `json:"freshness_score"`
				Metrics  map[string]json.RawMessage `json:"metrics"`
				Errors   []json.RawMessage          `json:"errors"`
			} `json:"report"`
		} `json:"reports"`
	}
	if len(raw) == 0 || json.Unmarshal(raw, &envelope) != nil || envelope.Reports == nil {
		return false, false
	}
	if envelope.Status == "unavailable" {
		return len(envelope.Reports) == 0, true
	}
	if envelope.Status == "no_text_to_check" {
		return len(expected) == 0 && len(envelope.Reports) == 0, false
	}
	if envelope.Status != "checked" || len(expected) == 0 || len(envelope.Reports) != len(expected) {
		return false, false
	}
	degraded := false
	for _, entry := range envelope.Reports {
		if entry.Index == nil {
			return false, false
		}
		choice, ok := expected[*entry.Index]
		if !ok {
			return false, false
		}
		delete(expected, *entry.Index)
		r := entry.Report
		if r.Schema != "1" || r.Mode == "" || r.Claims == nil || r.Metrics == nil || r.Errors == nil || r.Coverage == nil || *r.Coverage < 0 || *r.Coverage > 1 || len(r.Score) == 0 {
			return false, false
		}
		if _, err := time.Parse(time.RFC3339Nano, r.Checked); err != nil {
			return false, false
		}
		if string(r.Score) != "null" {
			var score float64
			if json.Unmarshal(r.Score, &score) != nil || score < 0 || score > 100 {
				return false, false
			}
		}
		if (choice.text == nil) != (r.Original == nil) || (choice.text != nil && *choice.text != *r.Original) {
			return false, false
		}
		switch r.Status {
		case "supported", "review_required", "no_claims_extracted", "no_time_sensitive_claims", "incomplete":
		case "unavailable", "upstream_error":
			degraded = true
		default:
			return false, false
		}
		if choice.incomplete != (r.Status == "incomplete") {
			return false, false
		}
		for _, claim := range r.Claims {
			if strings.TrimSpace(claim.Text) == "" || claim.Sensitive == nil || claim.Sources == nil || claim.IDs == nil || claim.Quotes == nil || len(claim.Correction) == 0 {
				return false, false
			}
			switch claim.Verdict {
			case "supported", "outdated", "uncertain", "not_checked":
			default:
				return false, false
			}
			sources := map[string]string{}
			for _, source := range claim.Sources {
				if source.ID == "" || source.URL == "" || source.Content == "" {
					return false, false
				}
				if _, exists := sources[source.ID]; exists {
					return false, false
				}
				sources[source.ID] = source.Content
			}
			ids, quoted := map[string]bool{}, map[string]bool{}
			for _, id := range claim.IDs {
				if _, exists := sources[id]; !exists {
					return false, false
				}
				ids[id] = true
			}
			for _, quote := range claim.Quotes {
				content, exists := sources[quote.ID]
				if !exists || !ids[quote.ID] || quote.Text == "" || !strings.Contains(content, quote.Text) {
					return false, false
				}
				quoted[quote.ID] = true
			}
			if claim.Verdict == "supported" || claim.Verdict == "outdated" {
				if len(ids) == 0 || len(ids) != len(quoted) {
					return false, false
				}
			}
			if claim.Verdict == "outdated" {
				var correction string
				if json.Unmarshal(claim.Correction, &correction) != nil || correction == "" {
					return false, false
				}
				matched := false
				for _, quote := range claim.Quotes {
					if strings.Contains(quote.Text, correction) {
						matched = true
					}
				}
				if !matched {
					return false, false
				}
			}
		}
		if len(r.Errors) > 0 {
			degraded = true
		}
	}
	return true, degraded
}
