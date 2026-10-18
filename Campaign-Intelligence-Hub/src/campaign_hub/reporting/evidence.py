import re


def numbers(text):
    return set(re.findall(r'(?<![A-Za-z])\d+(?:\.\d+)?',text.replace(',','')))


def valid_claim(claim, evidence):
    if not claim.citations or any(cid not in evidence for cid in claim.citations):
        return False
    source=' '.join(evidence[cid].text for cid in claim.citations)
    return numbers(claim.text).issubset(numbers(source))


def citation_coverage(claims,evidence):
    return sum(valid_claim(c,evidence) for c in claims)/len(claims) if claims else 0.0


def supported_claims(claims,evidence):
    return [c for c in claims if valid_claim(c,evidence) and any(c.text.strip() in evidence[cid].text for cid in c.citations)]
