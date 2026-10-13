# KNX Dubbelklicksdetektor

![Version](https://img.shields.io/badge/version-1.2.2-blue.svg)
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
* **Redigera direkt i UI:** Du kan nu redigera dina åtgärdsfiler (YAML) direkt via integrationens inställningar (Options Flow).
* **Template-stöd:** Använd variabler som `{{ time_difference_seconds }}` eller `{{ config_entry_name }}` i dina åtgärder.
* **Smart Exekvering:** Väljer automatiskt mellan snabba direktanrop eller `script`-motorn beroende på komplexitet.
* **Stöd för Labels och Areas:** Styr flera enheter samtidigt genom att använda Home Assistants `label_id` eller `area_id`.

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

Du kan redigera åtgärderna på två sätt:
1.  **Via UI:** Klicka på "Konfigurera" (kugghjulet) på integrationen och välj "Redigera Åtgärder (YAML)".
2.  **Via Fil:** Redigera filen i mappen `/config/knx_doubleclick_actions/`.

### Exempel på innehåll

```yaml
# Enkel åtgärd: Tänd en lampa
- service: light.turn_on
  target:
    entity_id: light.koksbord
  data:
    brightness_pct: 80

# Användning av Labels (Etiketter)
# Tänd alla enheter med etiketten 'mysbelysning'
- service: light.turn_on
  target:
    label_id: mysbelysning

# Användning av Areas (Områden)
# Släck allt i vardagsrummet
- service: light.turn_off
  target:
    area_id: vardagsrum

# Avancerad åtgärd: Skicka notis med dynamisk data
# Notera: Användning av {{ }} tvingar integrationen att använda Script-motorn
- service: persistent_notification.create
  data:
    title: "Dubbelklick registrerat!"
    message: "Detekterades för '{{ config_entry_name }}' med intervall {{ trigger.time_difference_seconds }}s."
```
