"""Small, explicit source policies; a domain match is provenance, not truth."""
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit


def policy_for(text):
    if re.search(r"\bpython\b", text, re.I):
        return {"entity": "Python", "domains": ["python.org"],
                "release_indexes":["https://www.python.org/downloads/", "https://devguide.python.org/versions/"],
                "retrieval_rules":[{"host":"www.python.org", "path":r"/downloads/(?:release/[a-zA-Z0-9-]+/)?"},
                                   {"host":"devguide.python.org", "path":r"/versions/"}],
                "exclude_domains":["planet.python.org", "discuss.python.org"]}
    if re.search(r"\bnode\.?js\b", text, re.I):
        return {"entity": "Node.js", "domains": ["nodejs.org"],
                "release_indexes":["https://nodejs.org/en/download/"],
                "retrieval_rules":[{"host":"nodejs.org", "path":r"/en/(?:download/|blog/release/[a-zA-Z0-9.-]+/?)"}]}
    if re.search(r"\b(?:java|openjdk|jdk)\b", text, re.I):
        return {"entity":"Java", "domains":["jdk.java.net", "openjdk.org", "oracle.com"],
                "official_paths":{"jdk.java.net":("/",), "openjdk.org":("/projects/jdk/",),
                                  "www.oracle.com":("/java/", "/news/announcement/oracle-releases-java-")},
                "release_indexes":["https://jdk.java.net/", "https://www.oracle.com/java/technologies/java-se-support-roadmap.html"],
                "retrieval_rules":[{"host":"jdk.java.net", "path":r"/(?:[0-9]{1,2}/)?"},
                                   {"host":"www.oracle.com", "path":r"/java/technologies/java-se-support-roadmap\.html"}]}
    if re.search(r"\bbifrost\b", text, re.I):
        return {"entity": "Bifrost", "domains": ["getbifrost.ai", "github.com"],
                "release_indexes":["https://github.com/maximhq/bifrost/releases"],
                "github_prefix": "/maximhq/bifrost"}
    if re.search(r"\b(?:openai|chatgpt)\b|\bgpt[- ]?\d", text, re.I):
        return {"entity":"OpenAI", "domains":["openai.com"], "exclude_domains":["community.openai.com"]}
    if re.search(r"\b(?:iphone|ipad|macbook)\b", text, re.I):
        return {"entity":"Apple", "domains":["apple.com"], "exclude_domains":["discussions.apple.com"]}
    if re.search(r"\bReact(?:\.js|JS)?\b", text):
        return {"entity":"React", "domains":["react.dev", "github.com"], "github_prefix":"/facebook/react"}
    return {"entity": None, "domains": []}


def is_primary(url, policy):
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port not in (None, 443):
            return False
        # An official site's community forum is not an authoritative release
        # statement. Hosting and authorship are different properties.
        if source_role(url) in ("community", "aggregator"):
            return False
        if "official_paths" in policy:
            return any(parsed.path.startswith(prefix) for prefix in policy["official_paths"].get(host, ()))
        for domain in policy["domains"]:
            if host == domain or host.endswith("." + domain):
                if domain == "github.com":
                    prefix = policy["github_prefix"].lower()
                    path = parsed.path.lower()
                    return path == prefix or path.startswith(prefix + "/")
                return True
    except ValueError:
        pass
    return False


def source_role(url):
    try:
        parsed = urlsplit(url)
        host, path = (parsed.hostname or "").lower(), parsed.path.lower()
        if host == "jdk.java.net" and re.fullmatch(r"/\d{1,2}/?", path):
            return "version_snapshot"
        if (host == "jdk.java.net" and path == "/"
                or host == "www.oracle.com" and path == "/java/technologies/java-se-support-roadmap.html"):
            return "release_index"
        if re.search(r"(^|\.)(discuss|discussions|forum|forums|community)\.", host) or re.search(r"/(discussions|forum|forums)/", path):
            return "community"
        if re.search(r"(^|\.)(planet|feed|feeds)\.", host):
            return "aggregator"
        if re.search(r"/(archive|archives|history)(/|$)|/releases/tag/|/(?:downloads/)?release/[^/]+|/releases/v?\d", path):
            return "version_snapshot"
        if re.search(r"/(downloads(?:/source)?|versions|releases|(?:en/)?download(?:/current)?)/?$", path):
            return "release_index"
        return "unclassified"
    except ValueError:
        return "unclassified"


def canonical_source(url):
    """Collapse obvious URL aliases for evidence diversity, not fetching."""
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower().removeprefix("www.")
    return host + parsed.path.rstrip("/") + ("?" + parsed.query if parsed.query else "")


def release_source_rank(url, policy):
    """Order bounded search results; a priority is not evidence of truth."""
    indexes = {canonical_source(u) for u in policy.get("release_indexes", [])}
    role = source_role(url)
    priority = 0 if canonical_source(url) in indexes else {
        "release_index":1, "version_snapshot":2, "unclassified":3, "aggregator":4, "community":5}.get(role, 3)
    return (0 if is_primary(url, policy) else 1, priority)


def publication_date(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            result = parsedate_to_datetime(value)
        except (ValueError, TypeError, OverflowError):
            return None
    return (result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result).astimezone(timezone.utc)
