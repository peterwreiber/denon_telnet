# Denon Telnet

En Home Assistant-integration som styr inställningar på Denon-receivers via telnet (port 23). Den täcker det som den inbyggda integrationen `denonavr` inte visar: Audyssey, tonkontroll, kanalnivåer, ljudläge, insignal med mera.

Testad på en **Denon AVR-2113**. Andra Denon- och Marantz-modeller med samma telnet-protokoll fungerar troligen, men det är inte provat.

## Installation

**Via HACS/Marketplace:** lägg till `https://github.com/peterwreiber/denon_telnet` som eget repo (typ *Integration*), installera och starta om Home Assistant.

**Manuellt:** kopiera `custom_components/denon_telnet` till `/config/custom_components/` och starta om Home Assistant.

Lägg sedan till integrationen under *Inställningar → Enheter och tjänster → Lägg till integration → Denon Telnet* och ange receiverns IP-adress.

### Viktigt: bara en telnet-session

Receivern tillåter bara en telnet-anslutning åt gången. Om du även kör `denonavr` måste telnet vara avstängt där (alternativet *Använd telnet* av), annars får Denon Telnet ingen anslutning. `denonavr` fungerar fortfarande via HTTP för volym, källa och ström.

## Entiteter

| Typ | Entiteter |
|---|---|
| Switch | Ström, Dynamic EQ, Tonkontroll, Cinema EQ, Subwoofer |
| Select | Ljudläge, Audyssey MultEQ, Dynamic Volume, Reference Level Offset, Dynamikkompression, Restorer |
| Number | Bas, Diskant, LFE, Ljudfördröjning, PLII Music Dimension, PLII Music Center Width, kanalnivåer (de kanaler receivern rapporterar) |
| Sensor | Ingångsläge, Samplingsfrekvens, Insignal (kod), Pro Logic-läge, Loudness Management, Dolby-kompression, Radiofrekvens |

Värdena uppdateras direkt när receivern skickar ändringar (även från fjärrkontrollen). Dessutom frågar integrationen efter status var 30:e sekund och efter alla inställningar var femte minut.

## Bra att veta

- **Receivern måste vara på.** I standby svarar den inte på inställningar, så de visas som otillgängliga.
- **Ändringar kan nekas.** Receivern accepterar inte alla inställningar i alla lägen. Till exempel kräver bas och diskant att tonkontrollen är på, och Audyssey-inställningar kan vara låsta utan insignal eller kalibrering. Då visar Home Assistant ett felmeddelande i stället för att låtsas att ändringen gick igenom.
- **Ljudläge MUSIC** återkallar det senast använda musikläget, som kan vara STEREO. MOVIE, MUSIC och GAME rapporteras av receivern som den avkodare som används (t.ex. `DOLBY PL2 MUSIC`); det råa värdet finns i attributet `rapporterat`.
- **Höjdkanaler** är borttagna, eftersom AVR-2113 gav olika värden vid varje läsning.
- **Insignal (kod)** är receiverns råa kod. Vad koderna betyder är inte kartlagt.

Entitetsnamnen är på svenska.

## Licens

MIT
