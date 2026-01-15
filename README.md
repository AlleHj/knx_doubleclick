# TEST KNX Dubbelklicksdetektor

![Version](https://img.shields.io/badge/version-0.8.17-blue.svg)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Custom%20Component-orange.svg)
![Type](https://img.shields.io/badge/type-sensor-green.svg)
![Maintainer](https://img.shields.io/badge/maintainer-AlleHj-lightgrey.svg)

**KNX Dubbelklicksdetektor** är en anpassad integration ("Custom Component") för Home Assistant designad för att utöka funktionaliteten i dina fysiska KNX-tryckknappar. Genom att passivt lyssna på KNX-bussen möjliggör integrationen detektering av dubbelklick utan behov av komplexa automationer eller logik i ETS.

Denna integration är byggd för stabilitet och prestanda, med stöd för både direkt exekvering av tjänster och avancerade mallar (templates).

---

## 🌟 Funktioner

* **Passiv Avlyssning:** Reagerar direkt på telegram från KNX-bussen utan "polling".
* **Instans-baserad:** Skapa en unik detektor för varje knapp via UI.
* **Separerade Åtgärder:** Logik definieras i dedikerade YAML-filer för överskådlighet.
* **Template-stöd:** Använd variabler som `{{ time_difference_seconds }}` eller `{{ config_entry_name }}` i dina åtgärder.
* **Smart Exekvering:** Väljer automatiskt mellan snabba direktanrop eller `script`-motorn beroende på komplexitet.

## 🚀 Installation

### Manuell Installation

1.  Ladda ner mappen `knx_doubleclick` från detta repository.
2.  Kopiera mappen till din Home Assistant-katalog under `/config/custom_components/`.
3.  Sökvägen ska vara: `/config/custom_components/knx_doubleclick/`.
4.  Starta om Home Assistant.

## ⚙️ Konfiguration

Integrationen konfigureras uteslutande via **Enheter & Tjänster** i Home Assistant.

1.  Gå till **Inställningar** > **Enheter & Tjänster**.
2.  Klicka på **+ Lägg till integration**.
3.  Sök efter **KNX Dubbelklicksdetektor**.
4.  Ange parametrar:
    * **Namnsuffix:** Identifierare för knappen (t.ex. "Kök Tak").
    * **KNX Gruppadress:** Adressen att lyssna på (t.ex. `1/0/5`).
    * **KNX Värde:** Värdet som skickas vid tryck (oftast `1` eller `0`).
    * **Tidsfönster:** Max tid mellan tryck (standard `0.7` sekunder).

## 📝 Definiera Åtgärder (YAML)

När en integration skapas, genereras en motsvarande YAML-fil i mappen:
`/config/knx_doubleclick_actions/`

Filen öppnas enklast via valfri filredigerare (File Editor, VS Code) eller genom att notera sökvägen i integrationens inställningar.

### Exempel på innehåll

```yaml
# Enkel åtgärd: Tänd en lampa
- service: light.turn_on
  target:
    entity_id: light.koksbord
  data:
    brightness_pct: 80

# Avancerad åtgärd: Skicka notis med dynamisk data
# Notera: Användning av {{ }} tvingar integrationen att använda Script-motorn
- service: persistent_notification.create
  data:
    title: "Dubbelklick registrerat!"
    message: "Detekterades för '{{ config_entry_name }}' med intervall {{ trigger.time_difference_seconds }}s."
