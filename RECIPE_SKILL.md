# Recipe ingestion skill

Detta dokument beskriver hur en AI-assistent ska lägga in recept i **Alltid bra mat på Säteriet**.

## Uppdrag

När användaren skickar ett foto, skärmbild, PDF, länk eller text med ett recept och ber att få det tillagt i samlingen ska assistenten:

1. läsa källan noggrant,
2. extrahera receptets faktiska innehåll,
3. strukturera det enligt `RECIPE_FORMAT.md`,
4. bevara källans mängder, temperaturer, tider och ordningsföljd,
5. lägga till endast sådan metadata eller familjeinformation som användaren faktiskt uppger,
6. spara receptet som en ny Markdown-fil i `recipes/`,
7. kontrollera att receptet inte redan finns innan en ny fil skapas.

## Från foto eller skärmbild

- Läs receptnamn, portionsantal, tid, ingredienser och instruktioner direkt från bilden.
- Bevara delrubriker och komponenter när de finns.
- Normalisera layouten, men inte innehållet.
- Gissa inte text som inte går att läsa säkert.
- Om en viktig mängd eller instruktion är oklar: fråga användaren eller markera den som oklar innan publicering.

## Från PDF

- Bevara dokumentets struktur och detaljer när de hör till receptet.
- Om PDF:en innehåller bakgrundshistoria, tekniska kommentarer eller serveringsanvisningar får dessa behållas i separata avsnitt.
- Lös inte motsägelser i källan i smyg. Markera dem eller fråga användaren.

## Från webblänk

- Ange webbplats eller upphovsperson som källa.
- Sammanfatta och strukturera receptet; kopiera inte onödigt redaktionellt material.
- Bevara receptets sakuppgifter.

## Från fri text eller muntlig beskrivning

- Strukturera användarens egna recept utan att göra det mer exakt än underlaget medger.
- Fråga bara när en saknad uppgift är viktig för att receptet ska fungera.

## Metadata

Följ `RECIPE_FORMAT.md`.

Särskilt:

- `tried: true` endast när användaren säger att rätten är lagad/provad eller det redan är känt i projektet.
- `tried_date` endast när datum kan härledas säkert.
- `occasion` används för exempelvis jul, nyår, födelsedag eller en särskild middag.
- `contributor` är valfritt och kan användas när flera familjer och vänner bidrar.

## Ton och redigering

Samlingen ska kännas som en levande gemensam kokbok, inte en anonym receptdatabas. Små personliga anteckningar och serveringsminnen är värdefulla, men de ska hållas tydligt åtskilda från källreceptets instruktioner.

Assistenten får:

- rätta uppenbara OCR- och stavfel,
- göra rubriker och listor konsekventa,
- omvandla löptext till numrerade steg,
- skriva en mycket kort introduktion när den tydligt bygger på receptet.

Assistenten får inte utan uttrycklig begäran:

- ändra ingrediensmängder,
- byta råvaror,
- ändra temperatur eller tid,
- modernisera tekniken,
- lägga till ingredienser som inte finns i underlaget,
- påstå att receptet är provlagat.

## Publiceringsprincip

Markdown-filen i `recipes/` är receptets källversion. Webbplatsen ska ses som en presentation av dessa data, inte som en separat receptdatabas.

När webbplatsens generator stödjer automatisk publicering ska nya recept därför kunna publiceras utan att samma recept behöver skrivas in en andra gång i HTML.
