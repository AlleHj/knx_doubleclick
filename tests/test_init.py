"""
Grundläggande tester för att verifiera att komponenten kan laddas.
Detta fungerar som ett "smoke test" för testmiljön.
"""

from custom_components.knx_doubleclick.const import DOMAIN


def test_domain_constant():
    """
    Testar att DOMAIN-konstanten är korrekt inställd.

    Varför: Detta säkerställer att vi kan importera från komponenten och att
    grundläggande konstanter är korrekta.
    """
    assert DOMAIN == "knx_doubleclick"
