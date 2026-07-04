import dns.resolver
import structlog

logger = structlog.get_logger()


async def check_dkim(domain: str, selector: str = "resend") -> dict:
    """Check DKIM DNS record for a domain."""
    dkim_domain = f"{selector}._domainkey.{domain}"
    try:
        answers = dns.resolver.resolve(dkim_domain, "TXT")
        record = " ".join([rdata.to_text() for rdata in answers])
        return {"has_dkim": True, "selector": selector, "record": record}
    except Exception:
        return {"has_dkim": False, "selector": selector, "record": None}


async def check_spf(domain: str) -> dict:
    """Check SPF TXT record for a domain."""
    try:
        answers = dns.resolver.resolve(domain, "TXT")
        for rdata in answers:
            txt = rdata.to_text().strip('"')
            if txt.startswith("v=spf1"):
                includes_resend = "include:amazonses.com" in txt or "include:_spf.resend.com" in txt
                return {"has_spf": True, "record": txt, "includes_resend": includes_resend}
        return {"has_spf": False, "record": None, "includes_resend": False}
    except Exception:
        return {"has_spf": False, "record": None, "includes_resend": False}


async def check_dmarc(domain: str) -> dict:
    """Check DMARC record for a domain."""
    try:
        answers = dns.resolver.resolve(f"_dmarc.{domain}", "TXT")
        for rdata in answers:
            txt = rdata.to_text().strip('"')
            if txt.startswith("v=DMARC1"):
                policy = "none"
                for part in txt.split(";"):
                    part = part.strip()
                    if part.startswith("p="):
                        policy = part[2:]
                return {"has_dmarc": True, "policy": policy, "record": txt}
        return {"has_dmarc": False, "policy": None, "record": None}
    except Exception:
        return {"has_dmarc": False, "policy": None, "record": None}


async def full_domain_check(domain: str) -> dict:
    """Run DKIM, SPF, and DMARC checks."""
    dkim = await check_dkim(domain)
    spf = await check_spf(domain)
    dmarc = await check_dmarc(domain)
    return {"dkim": dkim, "spf": spf, "dmarc": dmarc, "domain": domain}
