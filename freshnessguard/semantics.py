"""Conservative version-superlative guard. No product/version answer database.

This does not solve general natural-language entailment. It refuses decisive
latest-version verdicts unless the bounded evidence proves the right predicate,
channel, entity, version granularity and recent effective time.
"""
import re
from datetime import datetime, timedelta

from .evidence import is_primary, policy_for, publication_date, source_role

MAX_CURRENT_AGE_DAYS = 30
VERSION = re.compile(r"(?<![\w.])v?(\d+\.\d+(?:\.\d+){0,2})(?!\d|\.\d)", re.I)
LATEST = re.compile(r"\b(latest|current|newest|most recent)\b", re.I)
JAVA_FEATURE = re.compile(r"\b(?:java(?: se)?|(?:open)?jdk)\s+(?:version\s+)?(\d{1,2})(?!\w|\.\d)", re.I)


def release_versions(claim, text):
    values = {tuple(map(int, m[1].split("."))) for m in VERSION.finditer(text)}
    if policy_for(claim["text"])["entity"] == "Java":
        values.update((int(m[1]),) for m in JAVA_FEATURE.finditer(text))
    return values


def version_scope(claim, version):
    if policy_for(claim["text"])["entity"] == "Java" and not VERSION.search(claim["text"]):
        return version[:1]
    return version[:2] if re.search(r"\b(series|branch)\b", claim["text"], re.I) else version


def latest_version_claim(text):
    return bool(LATEST.search(text) and re.search(r"\b(version|release|series|branch)\b", text, re.I))


def version_retrieval_claim(text):
    if latest_version_claim(text):
        return True
    if JAVA_FEATURE.search(text) and re.search(r"\b(?:lts|long.term support)\b", text, re.I):
        return True
    return bool(release_versions({"text":text}, text) and re.search(
        r"\b(newer than|older than|later than|earlier than|compared (?:to|with)|versus|vs\.?|superseded)\b", text, re.I))


def latest_query(text, subject, fallback, checked_at):
    if not version_retrieval_claim(text):
        return fallback
    policy = policy_for(text)
    entity = policy["entity"] or subject
    entity = VERSION.sub("", entity).strip(" ,.;:-")
    channel = " LTS" if re.search(r"\blts\b|long.term support", text, re.I) else " stable" if re.search(r"\bstable\b", text, re.I) else ""
    versions = [m[1] for m in VERSION.finditer(text)]
    if policy["entity"] == "Java" and not versions:
        versions = [m[1] for m in JAVA_FEATURE.finditer(text)]
    intent = "latest" if latest_version_claim(text) else "release history " + " ".join(versions)
    indexes = " ".join(policy.get("release_indexes", []))
    # Target release indexes, not dated news/feed matches. Check time remains in
    # verification metadata; do not bias latest searches toward the alleged value.
    return f"{entity} {intent}{channel} releases downloads versions release dates {indexes}".strip()[:500]


def effective_dates(text):
    """Only explicit dated effective/as-of context, never retrieval/pub metadata."""
    pattern = r"\b(?:as of|effective(?: date)?|release date)\s*[:=]?\s*(\d{4}-\d{2}-\d{2})\b"
    dates = []
    for raw in re.findall(pattern, text, re.I):
        parsed = publication_date(raw)
        if parsed:
            dates.append(parsed.date())
    return dates


def current_assertion(text, checked):
    dates = effective_dates(text)
    return bool(dates) and all(checked - timedelta(days=MAX_CURRENT_AGE_DAYS) <= d <= checked for d in dates)


def entity_matches(claim, text):
    entity = policy_for(claim["text"])["entity"]
    if entity == "Java":
        return bool(re.search(r"\b(?:java|(?:open)?jdk)\b", text, re.I))
    subject = entity or claim.get("subject", "")
    subject = VERSION.sub("", subject)
    tokens = [t for t in re.findall(r"[\w]+", subject.casefold())
              if t not in {"release", "series", "version", "branch", "the", "stable", "latest"}]
    words = set(re.findall(r"[\w]+", text.casefold()))
    return bool(tokens) and all(t in words for t in tokens)


def version_assertions(claim, text, checked):
    """Bound comparisons to a single sentence/line, not a whole release history."""
    stable = bool(re.search(r"\bstable\b", claim["text"], re.I))
    lts = bool(re.search(r"\blts\b|long.term support", claim["text"], re.I))
    assertions = []
    for sentence in re.split(r"(?<=[.!?])\s+(?!\d)", " ".join(text.split())):
        if not LATEST.search(sentence) or not entity_matches(claim, sentence):
            continue
        if re.search(r"\b(?:not|never|no longer|formerly|previously|used to|was|withdrawn|yanked|retracted)\b", sentence, re.I):
            continue
        if "?" in sentence or re.search(r"\b(?:cannot|can't|isn't|unclear|uncertain|unknown|whether|might|may|could|possibly)\b", sentence, re.I):
            continue
        if stable and not re.search(r"\bstable\b", sentence, re.I):
            continue
        if bool(re.search(r"\blts\b|long.term support", sentence, re.I)) != lts:
            continue
        narrow = r"maintenance|\bpatch\b|(?:within|for|in) .*?(?:branch|series)|\d+\.\d+(?:\.x)?\s+(?:branch|series)"
        if re.search(narrow, sentence, re.I) and not re.search(narrow, claim["text"], re.I):
            continue
        if re.search(r"\b(alpha|beta|preview|early[- ]access|prerelease|pre-release|release candidate|rc\d*)\b|\d(?:(?:a|b|rc)\d|[-.]ea\b)", sentence, re.I):
            continue
        values = release_versions(claim, sentence)
        # Multiple version values in one passage need richer scope interpretation.
        if len(values) != 1 or not current_assertion(sentence, checked):
            continue
        version = next(iter(values))
        number = re.escape(".".join(map(str, version)))
        # Require an affirmative relation, not mere co-occurrence of latest,
        # stable and a version somewhere in the same passage.
        word = r"(?:latest|current|newest|most recent)"
        relation = (rf"\b{word}\b.{{0,120}}?\b(?:is|are)\s+v?{number}(?!\d|\.\d)"
                    rf"|\b{word}\b.{{0,120}}?[:=]\s*.{{0,40}}?v?{number}(?!\d|\.\d)"
                    rf"|(?<![\w.])v?{number}\s+(?:is|remains)\s+(?:now\s+)?(?:the\s+)?{word}\b")
        if not re.search(relation, sentence, re.I):
            continue
        assertions.append({"version":version_scope(claim, version), "text":sentence})
    return assertions


DATE_LITERAL = r"(?:\d{4}-\d{2}-\d{2}|[A-Za-z]{3,9}\.?\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})"


def release_date_literal(raw):
    parsed = publication_date(raw)
    if parsed:
        return parsed.date()
    cleaned = raw.replace(",", "").replace(".", "")
    for fmt in ("%B %d %Y", "%b %d %Y", "%d %B %Y", "%d %b %Y"):
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            pass
    return None


def dated_release_facts(claim, text, checked, diagnostics=None):
    """Extract bounded, literal stable-release counterexamples, not newest claims.

    A dated newer stable release refutes an older maximum even when its release
    happened more than 30 days ago. No publication/retrieval date is substituted.
    """
    boundaries = [0] + [m.end() for m in re.finditer(r"\n\s*\n", text)][:32] + [len(text)]
    spans = [text] if len(text) <= 800 else []
    for i in range(len(boundaries)-1):
        for width in (1, 2, 3):
            end = boundaries[min(i+width, len(boundaries)-1)]
            passage = text[boundaries[i]:end].strip()
            if 12 <= len(passage) <= 800 and passage not in spans:
                spans.append(passage)
    facts = []
    def rejected(reason):
        if diagnostics is not None:
            counts = diagnostics.setdefault("rejected_passage_counts", {})
            counts[reason] = counts.get(reason, 0) + 1

    if diagnostics is not None:
        diagnostics["examined_passages"] = len(spans)
        diagnostics["accepted_passages"] = 0
        if not spans:
            rejected("no_passage_within_800_character_bound")
    for passage in spans:
        if not entity_matches(claim, passage):
            rejected("entity_not_matched")
            continue
        if not re.search(r"\b(stable|final)\b|general availability", passage, re.I):
            rejected("explicit_stable_or_final_channel_missing")
            continue
        if re.search(r"\b(alpha|beta|preview|early[- ]access|prerelease|pre-release|release candidate|rc\d*|withdrawn|yanked|retracted|unreleased|scheduled|planned)\b|\d(?:(?:a|b|rc)\d|[-.]ea\b)|\bnot (?:a |yet )?(?:stable|released|final)", passage, re.I):
            rejected("preview_planned_negated_or_withdrawn_release")
            continue
        if "?" in passage or re.search(r"\b(might|may|could|possibly|will be|would be|expected to|not|never|cannot|isn't|hasn't|won't)\b",
                                      re.sub(DATE_LITERAL, "", passage), re.I):
            rejected("speculative_negated_or_question_passage")
            continue
        lts = bool(re.search(r"\blts\b|long.term support", claim["text"], re.I))
        if bool(re.search(r"\blts\b|long.term support", passage, re.I)) != lts:
            rejected("lts_scope_mismatch")
            continue
        values = release_versions(claim, passage)
        if len(values) != 1:
            rejected("version_not_unique_in_passage")
            continue
        full_version = next(iter(values))
        entity = policy_for(claim["text"])["entity"] or VERSION.sub("", claim.get("subject", "")).strip()
        entity = re.sub(r"\b(release|series|version|branch)\b", "", entity, flags=re.I).strip()
        number = re.escape(".".join(map(str, full_version)))
        entity_pattern = r"(?:java(?: se)?|(?:open)?jdk)" if entity == "Java" else re.escape(entity)
        binding = (rf"\b{entity_pattern}\s+(?:(?:version|release|series|is|was)\s+){{0,4}}v?{number}(?!\w|\.\d)"
                   rf"|\b(?:version|release)\s+v?{number}\s+(?:of|for)\s+{entity_pattern}\b")
        if not entity or not re.search(binding, passage, re.I):
            rejected("entity_version_relation_missing")
            continue
        dates = []
        for match in re.finditer(rf"\b(release date|released(?: on)?|as of|effective(?: date)?)\s*[:=]?\s*({DATE_LITERAL})", passage, re.I):
            date = release_date_literal(match[2])
            if date:
                label = match[1].lower()
                dates.append((date, "as_of" if label == "as of" else "effective_date" if label.startswith("effective") else "release_date"))
        for match in re.finditer(rf"\bOn\s+({DATE_LITERAL})[^\n]{{0,80}}?\b(?:was |has been )?released\b", passage, re.I):
            date = release_date_literal(match[1])
            if date:
                dates.append((date, "release_date"))
        if not dates or any(date > checked for date, _ in dates):
            rejected("explicit_release_or_effective_date_missing" if not dates else "future_release_or_effective_date")
            continue
        # An as-of date is not called a release date, and still-supported wording
        # alone cannot certify that a stable release occurred.
        if not re.search(r"\b(?:release date|released|stable release|final release|latest|current|newest|most recent)\b", passage, re.I):
            rejected("release_assertion_missing")
            continue
        version = version_scope(claim, full_version)
        date, kind = min(dates, key=lambda item:item[0])
        fact = {"version":version, "full_version":full_version, "date":date.isoformat(), "date_kind":kind, "text":passage}
        if fact not in facts:
            facts.append(fact)
        if diagnostics is not None:
            diagnostics["accepted_passages"] += 1
    return facts


def eligible_release_source(source, policy):
    return (bool(policy["domains"]) and is_primary(source["url"], policy)
            and source_role(source["url"]) not in ("community", "aggregator"))


def adjacent_release_window(claim, passage):
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", passage) if p.strip()]
    if len(paragraphs) == 1:
        # A single affirmative sentence may bind release and date. Do not
        # borrow a date from another sentence about a different subject.
        return len(re.split(r"(?<=[.!?])\s+(?!\d)", passage)) == 1
    date_only = rf"(?:release date|released(?: on)?|as of|effective(?: date)?)\s*[:=]?\s*{DATE_LITERAL}\.?"
    return (len(paragraphs) <= 3 and any(re.fullmatch(date_only, p, re.I) for p in paragraphs)
                and all(re.fullmatch(date_only, p, re.I) or (entity_matches(claim, p) and release_versions(claim, p)) for p in paragraphs))


def release_evidence_window(claim, source, checked_at):
    """Suggest one exact newer-release quote to the judge; confer no verdict."""
    checked = publication_date(checked_at)
    if (not checked or source.get("future_dated")
            or not eligible_release_source(source, claim["source_policy"])):
        return None
    targets = {version_scope(claim, v) for v in release_versions(claim, claim["text"])}
    if len(targets) != 1:
        return None
    target = next(iter(targets))
    passages = (fact["text"] for fact in dated_release_facts(claim, source["content"], checked.date())
                if fact["version"] > target and adjacent_release_window(claim, fact["text"]))
    window = min(passages, key=len, default=None)
    return {"source_id":source["id"], "text":window} if window else None


def complete_release_quotes(claim, quotes, checked_at):
    """Select original adjacent source spans; never concatenate or infer dates.

    Only an already grounded, entity/version-bearing quote may anchor a window.
    Ambiguous dates/occurrences are refused. Acceptance still belongs to the
    unchanged final semantic validator, including withdrawal/conflict checks.
    """
    checked = publication_date(checked_at)
    if not checked or not latest_version_claim(claim["text"]):
        return quotes, []
    policy = claim.get("source_policy") or policy_for(claim["text"])
    sources = {s["id"]:s for s in claim["sources"]}
    result, audit = [], []
    for quote in quotes:
        source = sources[quote["source_id"]]
        text = quote["text"]
        values = release_versions(claim, text)
        if (source.get("future_dated") or not eligible_release_source(source, policy)
                or not entity_matches(claim, text) or len(values) != 1
                or dated_release_facts(claim, text, checked.date())):
            result.append(quote)
            continue
        candidates = [fact for fact in dated_release_facts(claim, source["content"], checked.date())
                      if text in fact["text"] and fact["full_version"] in values and adjacent_release_window(claim, fact["text"])]
        identities = {(f["full_version"], f["date"], f["date_kind"]) for f in candidates}
        # Repeated anchors can attach a date to the wrong occurrence.
        if len(identities) != 1 or source["content"].count(text) != 1:
            result.append(quote)
            continue
        window = min(candidates, key=lambda f:(len(f["text"]), source["content"].find(f["text"])))
        start = source["content"].find(window["text"])
        result.append({"source_id":quote["source_id"], "text":window["text"]})
        audit.append({"source_id":quote["source_id"], "method":"adjacent_dated_release_span_v1",
                      "original_quote":text, "selected_quote":window["text"],
                      "start":start, "end":start+len(window["text"])})
    return result, audit


def release_disputed(claim, fact, sources, policy):
    number = re.escape(".".join(map(str, fact["full_version"])))
    for source in sources.values():
        if not eligible_release_source(source, policy):
            continue
        for passage in re.split(r"\n+|(?<=[.!?])\s+(?!\d)", source["content"]):
            if not entity_matches(claim, passage) or not re.search(rf"(?<![\w.])v?{number}(?!\w|\.\d)", passage):
                continue
            if not re.search(r"\b(withdrawn|yanked|retracted|unreleased)\b|\b(?:not|never).{0,24}\b(?:stable|released|final)\b", passage, re.I):
                continue
            dates = effective_dates(passage)
            if dates and max(dates).isoformat() < fact["date"]:
                continue
            return True
    return False


def validate_latest_decision(claim, verdict, ids, quotes, checked_at):
    if not latest_version_claim(claim["text"]):
        return None
    checked_time = publication_date(checked_at)
    if checked_time is None:
        return {"status":"rejected", "reasons":["Latest-version evidence has no valid check time"]}
    checked = checked_time.date()
    if not re.search(r"\bstable\b|\blts\b|long.term support", claim["text"], re.I):
        return {"status":"rejected", "reasons":["Latest-version channel is unspecified"]}
    targets = {version_scope(claim, v) for v in release_versions(claim, claim["text"])}
    if len(targets) != 1:
        return {"status":"rejected", "reasons":["Latest-version target or granularity is ambiguous"]}
    target = next(iter(targets))
    sources = {s["id"]:s for s in claim["sources"]}
    policy = claim.get("source_policy") or policy_for(claim["text"])
    usable, observed, release_observed, release_usable = [], [], [], []
    release_checks = []
    def release_facts(source, text, scope):
        check = {"source_id":source["id"], "scope":scope,
                 "eligible_authority":eligible_release_source(source, policy)}
        release_checks.append(check)
        if not check["eligible_authority"]:
            check["reason"] = "ineligible_release_authority"
            return []
        rows = dated_release_facts(claim, text, checked, check)
        check["parsed_facts"] = len(rows)
        return rows
    for source in sources.values():
        release_observed.extend((source["id"], row) for row in release_facts(source, source["content"], "source"))
        # Recompute authority; never trust a saved/source-provided primary flag.
        if policy["domains"] and not is_primary(source["url"], policy):
            continue
        if source_role(source["url"]) in ("community", "aggregator", "version_snapshot"):
            continue
        rows = version_assertions(claim, source["content"], checked)
        observed.extend((source["id"], row) for row in rows)
    for q in quotes:
        if q["source_id"] not in ids:
            continue
        source = sources[q["source_id"]]
        release_usable.extend((q["source_id"], row) for row in release_facts(source, q["text"], "quote"))
        if (policy["domains"] and not is_primary(source["url"], policy)) or source_role(source["url"]) in ("community", "aggregator", "version_snapshot"):
            continue
        usable.extend((q["source_id"], row) for row in version_assertions(claim, q["text"], checked))
    disputed = [(sid, row) for sid,row in release_usable if release_disputed(claim,row,sources,policy)]
    release_observed = [(sid,row) for sid,row in release_observed if not release_disputed(claim,row,sources,policy)]
    release_usable = [(sid,row) for sid,row in release_usable if not release_disputed(claim,row,sources,policy)]
    reasons = []
    candidates = {row["version"] for _, row in observed}
    if len(candidates) > 1 and verdict == "supported":
        reasons.append("Unresolved contradictory current latest-version assertions")
    if verdict == "supported":
        if any(v > target for v in candidates) or any(row["version"] > target for _, row in release_observed):
            reasons.append("Current eligible evidence identifies a newer stable version")
        if not any(row["version"] == target for _, row in usable):
            reasons.append("No current dated eligible quote entails this exact latest-version claim; stable/supported is insufficient")
    elif not any(row["version"] > target for _, row in usable + release_usable):
        reasons.append("No eligible cited current assertion or dated stable release establishes a newer version in the claimed scope")
        if disputed:
            reasons.append("Dated release counterexample is disputed by official withdrawal/status evidence")
    return {"status":"rejected" if reasons else "passed", "reasons":reasons,
            "max_evidence_age_days":MAX_CURRENT_AGE_DAYS,
            "authority_policy":"official_required" if policy["domains"] else "unassessed",
            "proof_kind":"newer_dated_stable_release" if verdict == "outdated" and any(row["version"] > target for _, row in release_usable) else "current_latest_assertion",
            "release_witnesses":[{"source_id":sid,"version":".".join(map(str,row["version"])),"date":row["date"],"date_kind":row["date_kind"]} for sid,row in release_usable if row["version"] > target],
            "release_evidence_checks":release_checks,
            "observed_release_witnesses":[{"source_id":sid,"version":".".join(map(str,row["version"])),"date":row["date"],"date_kind":row["date_kind"]} for sid,row in release_observed],
            "observed_versions":[".".join(map(str, v)) for v in sorted(candidates)]}
