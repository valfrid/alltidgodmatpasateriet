# Receptformat

Alla recept i samlingen lagras som Markdown-filer i `recipes/`.

## Filnamn

Använd ett kort, stabilt filnamn med gemener och bindestreck, utan åäö.

Exempel:

`lammfarsbullar-med-rosmarinpommes.md`

## Front matter

Varje recept börjar med YAML:

```yaml
---
title: "Receptets namn"
category: "Huvudrätter"
portions: 4
time_minutes: 45
source: "Källa eller ursprung"
source_type: "photo"
tried: true
tried_date: 2026-09-12
occasion: ""
contributor: ""
---
```

### Fält

- `title` – obligatoriskt.
- `category` – en av: `Förrätter`, `Huvudrätter`, `Desserter`, `Vardagsmat`, `Säsongens smaker`, `Teman`.
- `portions` – antal portioner om källan anger det.
- `time_minutes` – total tid om källan anger det.
- `source` – ursprung, bok, person, webbplats eller annan källa.
- `source_type` – t.ex. `photo`, `pdf`, `web`, `text`, `family`.
- `tried` – `true` eller `false`.
- `tried_date` – datum om det är känt.
- `occasion` – valfri händelse, t.ex. `Nyårsafton 2025`.
- `contributor` – valfritt namn på den som lagt in eller bidragit med receptet.

Utelämna hellre ett okänt fält än att gissa.

## Innehåll

Normal struktur:

```md
# Receptets namn

Kort beskrivning om sådan finns eller om den uttryckligen lagts till som samlingens egen introduktion.

## Ingredienser

### Delkomponent, vid behov

- ingrediens
- ingrediens

## Gör så här

1. Steg ett.
2. Steg två.

## Anteckning

Valfria egna erfarenheter, ändringar, serveringstillfällen eller kommentarer.
```

## Regler

1. Ingredienser och instruktioner ska i första hand följa källan.
2. Stavfel kan rättas när innebörden är uppenbar, men mängder, temperaturer och tider får inte ändras utan stöd.
3. Om text i ett foto är oläslig ska den inte gissas fram.
4. Egna förbättringar eller tolkningar ska anges tydligt som anteckning eller anpassning.
5. Originalets portionsantal, tider och namn ska bevaras om de går att läsa.
6. Familjeminnen och serveringstillfällen får läggas till när användaren uppger dem.
7. Ett recept kan vara oprövat; då används `tried: false`.
