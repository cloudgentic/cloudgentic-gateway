"""Skill security scanner — pattern-based analysis of OpenClaw skills."""
import re
from datetime import datetime, timezone

from app.schemas.security import SkillScanResponse, SkillScanConcern

# Pattern rules: (category, severity, regex_pattern, description)
SCAN_RULES = [
    # Data exfiltration
    ("data_exfiltration", "critical", r"(?i)(send|post|upload|transmit|exfiltrate).{0,40}(\.env|environment|token|secret|key|password|credential|api.?key)", "Attempts to exfiltrate environment variables or credentials"),
    ("data_exfiltration", "critical", r"(?i)(curl|wget|fetch|http|request).{0,60}(\.env|/etc/passwd|/etc/shadow|\.ssh|\.aws|\.config)", "Attempts to read and send sensitive system files"),
    ("data_exfiltration", "high", r"(?i)send.{0,30}(to|via).{0,30}(external|remote|http|url|server|webhook)", "Sends data to external server"),

    # Shell execution
    ("shell_execution", "high", r"(?i)(exec|eval|system|popen|subprocess|child_process|spawn)\s*\(", "Executes shell commands programmatically"),
    ("shell_execution", "high", r"(?i)(bash|sh|cmd|powershell)\s+(-c|/c|command)", "Direct shell command execution"),
    ("shell_execution", "critical", r"(?i)(rm\s+-rf|del\s+/[sfq]|format\s+c:)", "Destructive file system operations"),

    # Network access
    ("network_access", "high", r"(?i)(fetch|axios|request|http\.get|http\.post|urllib)\s*\(.{0,20}(http|https|ftp)", "Makes HTTP requests to external services"),
    ("network_access", "high", r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "Contains hardcoded IP addresses"),

    # Credential access
    ("credential_access", "critical", r"(?i)(read|open|load|parse|access).{0,30}(\.env|config\.json|secrets|keychain|ssh.?key|id_rsa)", "Reads credential or configuration files"),
    ("credential_access", "critical", r"(?i)(process\.env|os\.environ|getenv)\[?.{0,30}(key|token|secret|password)", "Accesses environment variable credentials"),

    # Persistence
    ("persistence", "high", r"(?i)(crontab|systemd|launchd|startup|autorun|init\.d|rc\.local)", "Modifies system startup or scheduling"),
    ("persistence", "high", r"(?i)(chmod\s+777|chown\s+root|setuid)", "Changes file permissions dangerously"),

    # Obfuscation
    ("obfuscation", "critical", r"(?i)(atob|btoa|base64\.decode|base64\.b64decode|Buffer\.from)\s*\(", "Decodes base64 content (potential hidden payload)"),
    ("obfuscation", "critical", r"(?i)eval\s*\(\s*(atob|decode|unescape|Buffer)", "Evaluates decoded/obfuscated content"),
    ("obfuscation", "high", r"\\x[0-9a-fA-F]{2}(\\x[0-9a-fA-F]{2}){5,}", "Contains hex-encoded strings"),

    # Privilege escalation
    ("privilege_escalation", "high", r"(?i)(sudo|doas|runas)\s+", "Attempts privilege escalation"),
    ("privilege_escalation", "critical", r"(?i)(docker\.sock|/var/run/docker)", "Accesses Docker socket"),

    # Social engineering
    ("social_engineering", "medium", r"(?i)(ignore|disable|skip|bypass).{0,20}(security|warning|verification|check|validation)", "Instructions to disable security features"),
    ("social_engineering", "medium", r"(?i)(don'?t|do not).{0,20}(tell|inform|warn|alert).{0,20}(user|admin|owner)", "Attempts to hide actions from the user"),
]

# Known malicious patterns from community reports
BLOCKLIST_PATTERNS = [
    ("known_malware", "critical", r"(?i)solana.?wallet.?tracker", "Known malicious skill: wallet tracker keylogger"),
]


def scan_skill(
    skill_name: str,
    skill_md_content: str | None = None,
    files: list[dict] | None = None,
) -> SkillScanResponse:
    """Scan a skill for security concerns using pattern matching."""
    concerns: list[SkillScanConcern] = []

    # Check blocklist
    for category, severity, pattern, description in BLOCKLIST_PATTERNS:
        if re.search(pattern, skill_name):
            concerns.append(SkillScanConcern(
                severity=severity, category=category,
                description=description, evidence=f"Skill name: {skill_name}",
            ))

    # Scan SKILL.md content (limit to 500KB to prevent ReDoS)
    MAX_CONTENT_SIZE = 512_000
    if skill_md_content:
        _scan_content(skill_md_content[:MAX_CONTENT_SIZE], "SKILL.md", concerns)

    # Scan code files
    if files:
        for file_info in files:
            path = file_info.get("path", "unknown")
            content = file_info.get("content", "")
            if content:
                _scan_content(content[:MAX_CONTENT_SIZE], path, concerns)

    # Calculate risk score
    risk_score = _calculate_risk_score(concerns)
    risk_level = _risk_level(risk_score)

    # Generate recommendations
    recommendations = _generate_recommendations(risk_level, concerns)

    return SkillScanResponse(
        risk_score=risk_score,
        risk_level=risk_level,
        concerns=concerns,
        recommendations=recommendations,
        scanned_at=datetime.now(timezone.utc),
    )


def _scan_content(content: str, filename: str, concerns: list[SkillScanConcern]):
    """Scan a single file's content against all rules."""
    lines = content.split("\n")
    for line_num, line in enumerate(lines, 1):
        for category, severity, pattern, description in SCAN_RULES:
            match = re.search(pattern, line)
            if match:
                concerns.append(SkillScanConcern(
                    severity=severity,
                    category=category,
                    description=description,
                    evidence=f"{filename}:{line_num}: {line.strip()[:200]}",
                    line_number=line_num,
                ))


def _calculate_risk_score(concerns: list[SkillScanConcern]) -> int:
    """Calculate aggregate risk score 0-100."""
    if not concerns:
        return 0

    severity_weights = {"critical": 30, "high": 15, "medium": 5, "low": 2}
    score = sum(severity_weights.get(c.severity, 1) for c in concerns)
    return min(score, 100)


def _risk_level(score: int) -> str:
    if score == 0:
        return "safe"
    elif score < 15:
        return "low"
    elif score < 35:
        return "medium"
    elif score < 65:
        return "high"
    else:
        return "critical"


def _generate_recommendations(risk_level: str, concerns: list[SkillScanConcern]) -> list[str]:
    if risk_level == "safe":
        return ["No concerns found. Skill appears safe to install."]
    elif risk_level == "low":
        return ["Low risk detected. Review the concerns before installing."]
    elif risk_level == "medium":
        return ["Medium risk detected. Carefully review each concern.", "Consider running in dry-run mode first."]
    elif risk_level == "high":
        return ["High risk detected. Do NOT install without thorough review.", "Consider reporting to ClawHub maintainers."]
    else:
        return ["CRITICAL risk detected. Do NOT install this skill.", "Report to ClawHub maintainers immediately.", "This skill may be malicious."]
