# Home Assistant acoGo!

English version [below](#english)

## Integracja acoGo!

Niniejsze repozytorium zawiera niestandardowy komponent "acoGo!" dla Home Assistant, który umożliwia integrację z urządzeniami ekosystemu acoGo!.

Do korzystania z komponentu wymagane jest posiadanie tokenu API, który można uzyskać w [portalu acoGo!](https://portal.acogo.pl/).

Szczegółowe instrukcje dotyczące instalacji i konfiguracji komponentu znajdują się w [portau integratora acoGo!](https://integrator.acogo.pl/).

### Instalacja (Custom component)

#### HACS

[![Dodaj do HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=acoGO&repository=HomeAssistant-acoGO&category=integration)

1. Kliknij przycisk "Dodaj do HACS" powyżej.
2. W Home Assistant wybierz HACS -> Integrations -> Download.
3. Zrestartuj Home Assistant.
4. Dodaj integrację "acoGo!" w Ustawienia -> Integracje.

#### Ręcznie

1. Skopiuj katalog `custom_components/acogo` do `<config>/custom_components/acogo`.
2. Zrestartuj Home Assistant.
3. Dodaj integrację "acoGo!" w Ustawienia -> Integracje.

## English

This repository contains the custom component "acoGo!" for Home Assistant, which enables integration with devices from the acoGo! ecosystem.

Using this component requires an API token, which can be obtained from the [acoGo! portal](https://portal.acogo.pl/).

Detailed installation and configuration instructions are available on the acoGo! [integrator portal](https://integrator.acogo.pl/).

### Installation (Custom component)

#### HACS

[![Add to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=acoGO&repository=HomeAssistant-acoGO&category=integration)

1. Click the "Add to HACS" button above.
2. In Home Assistant go to HACS -> Integrations -> Download.
3. Restart Home Assistant.
4. Add the "acoGo!" integration in Settings -> Devices & Services.

#### Manual

1. Copy `custom_components/acogo` to `<config>/custom_components/acogo`.
2. Restart Home Assistant.
3. Add the "acoGo!" integration in Settings -> Devices & Services.
