import re

import dns.resolver
import structlog

logger = structlog.get_logger()

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def validate_email_format(email: str) -> bool:
    """Check if an email address has a valid format."""
    if not email or len(email) > 320:
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


async def check_mx_record(domain: str) -> bool:
    """Check if a domain has valid MX records."""
    try:
        dns.resolver.resolve(domain, "MX")
        return True
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers, Exception):
        return False


async def validate_email_full(email: str) -> tuple[bool, str]:
    """Full email validation: format check + MX record check."""
    if not validate_email_format(email):
        return False, "Invalid email format"

    domain = email.split("@")[1]
    if not await check_mx_record(domain):
        return False, f"No MX records found for {domain}"

    return True, "Valid"
