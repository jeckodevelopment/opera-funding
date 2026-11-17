#!/usr/bin/env python3
"""One-time redacted Resend diagnostic. Never disclose API keys or addresses."""
import hashlib
import json
import os
import re
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from notify import FROM_ADDRESS,parse_recipients

def classify_response(error):
    raw=error.read(8192)
    content_type=error.headers.get("content-type","").split(";")[0].lower()
    edge=bool(error.headers.get("cf-mitigated"))
    try:
        obj=json.loads(raw)
    except (ValueError,UnicodeDecodeError):
        obj={}
    if not isinstance(obj,dict):
        obj={}
    name=obj.get("name",obj.get("code",""))
    # Only bounded machine-readable tokens, not free-text messages.
    name=name if isinstance(name,str) and re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]{0,63}",name) else "unavailable"
    message=obj.get("message","")
    message=message.lower() if isinstance(message,str) else ""
    patterns=[
        ("domain_verification","not verified"),
        ("domain_mismatch","domain"),
        ("restricted_api_key","restricted"),
        ("account_restricted","account"),
        ("invalid_credentials","api key"),
        ("test_domain","resend.dev"),
        ("recipient_restricted","recipient"),
        ("sending_denied","not allowed"),
    ]
    category=next((label for label,needle in patterns if needle in message),"unknown")
    print(f"HTTP_STATUS={error.code}")
    print(f"RESPONSE_CONTENT_TYPE={content_type if content_type in ('application/json','text/html','text/plain') else 'other'}")
    print(f"EDGE_CHALLENGE={edge}")
    print(f"PROVIDER_ERROR_CODE={name}")
    print(f"PROVIDER_MESSAGE_CATEGORY={category}")

def main():
    key=os.getenv("RESEND_API_KEY") or ""
    recipients=parse_recipients(os.getenv("FUNDING_ALERT_RECIPIENT"))
    if not key or not recipients:
        raise RuntimeError("Secret mancante o lista destinatari vuota")
    address=recipients[0]
    # Only ONE test request, no retries, no impact on catalog or alert ledger.
    payload=json.dumps({
        "from":FROM_ADDRESS,"to":[address],
        "subject":"Opera+ Funding — prova diagnostica email",
        "text":"Test di configurazione dell'invio automatico. Non segnala un nuovo bando.",
    }).encode("utf-8")
    nonce=hashlib.sha256(payload).hexdigest()[:24]
    request=Request("https://api.resend.com/emails",data=payload,method="POST",headers={
        "Authorization":"Bearer "+key,"Content-Type":"application/json",
        "User-Agent":"OperaFunding/1.0 (https://github.com/jeckodevelopment/opera-funding)",
        "Idempotency-Key":"opera-diagnostic-"+nonce,
    })
    try:
        with urlopen(request,timeout=20) as response:
            data=json.load(response)
            print("RESULT=ACCEPTED" if isinstance(data,dict) and data.get("id") else "RESULT=UNCONFIRMED")
    except HTTPError as e:
        classify_response(e)
        raise SystemExit(1)
    except URLError:
        print("RESULT=NETWORK_FAILURE")
        raise SystemExit(1)

if __name__=="__main__":
    main()
