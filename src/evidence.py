"""Conservative official-page funding evidence extraction.

Evidence labels are not eligibility determinations. No inferred amounts, no
automatic open status and no removal of incomplete opportunities.
"""
import re
from bs4 import BeautifulSoup

BENEFICIARY_HEAD=re.compile(r"(?i)^(?:beneficiari|destinatari|soggetti ammissibili|soggetti beneficiari|chi può partecipare|eligible applicants)\s*[:：–-]?\s*$")
BENEFICIARY_INLINE=re.compile(r"(?i)^(?:beneficiari|destinatari|soggetti ammissibili|soggetti beneficiari|chi può partecipare|eligible applicants)\s*[:：–-]\s*(.{12,360})$")
AMOUNT_LABEL=re.compile(r"(?i)\b(contributo massimo|finanziamento massimo|importo massimo|dotazione finanziaria|budget complessivo)\s*[:：–-]?\s*(?:€|euro|eur)?\s*([\d.]+(?:,\d{2})?)\s*(?:€|euro|eur)?")
ROLLING_LABEL=re.compile(r"(?i)\b(?:bando|avviso|domande|candidature|presentazione delle domande|presentazione di domande)\b.{0,75}?\b(?:a sportello|a ciclo continuo|senza scadenza|fino ad esaurimento (?:dei )?fondi)\b|\b(?:procedura a sportello|modalità a sportello)\b")
MAX_TEXT=350

def official_evidence(html,page_url):
    soup=BeautifulSoup(html,"html.parser")
    for x in soup(["script","style","nav","footer","header"]):x.decompose()
    main=soup.select_one("main, article, .entry-content, .node__content") or soup.body or soup
    beneficiary=None
    # Prefer precise, label-adjacent text. Never scan arbitrary body prose for
    # entity types and then assert those entities are eligible.
    for node in main.find_all(["p","li","dt","dd","h2","h3","h4"],limit=160):
        txt=" ".join(node.stripped_strings).strip()
        if not txt:continue
        inline=BENEFICIARY_INLINE.match(txt)
        if inline:
            beneficiary=txt[:MAX_TEXT]
            break
        if BENEFICIARY_HEAD.fullmatch(txt):
            nxt=node.find_next_sibling(["p","div","ul","ol","dd"])
            if nxt:
                value=" ".join(nxt.stripped_strings).strip()
                if 12<=len(value)<=650:
                    beneficiary=(txt.rstrip(":")+" — "+value)[:MAX_TEXT]
                    break
    text=" ".join(main.stripped_strings)[:25000]
    amount=AMOUNT_LABEL.search(text)
    rolling=ROLLING_LABEL.search(text)
    result={
        "beneficiaries_excerpt":beneficiary,
        "beneficiaries_source":page_url if beneficiary else None,
        "amount":("€ "+amount.group(2)+" (da verificare)") if amount else None,
        "amount_kind":amount.group(1).lower() if amount else None,
        "amount_source":page_url if amount else None,
        "rolling_guidance":("Possibile candidatura a sportello; verificare nel bando ufficiale le condizioni di apertura e disponibilità dei fondi.") if rolling else None,
        "rolling_guidance_source":page_url if rolling else None,
    }
    return result
