import personsJson from '../../data/persons.json';
import placesJson from '../../data/places.json';
import type { JourneyStep, Person, Place } from './types';

export const persons: Person[] = personsJson as Person[];
export const places: Place[] = placesJson as Place[];

export const personById: Record<string, Person> = Object.fromEntries(
  persons.map((p) => [p.id, p]),
);

export const placeById: Record<string, Place> = Object.fromEntries(
  places.map((p) => [p.id, p]),
);

export interface PersonsAtPlace {
  place: Place;
  persons: Person[];
}

/** Best-known single location for a person. Honors explicit primary_place_id,
 * else prefers death_place_id (where they finished out their work), else birth. */
export function primaryPlaceOf(person: Person): Place | null {
  const candidates = [person.primary_place_id, person.death_place_id, person.birth_place_id];
  for (const id of candidates) {
    if (id && placeById[id]) return placeById[id];
  }
  return null;
}

/** Lifespan extents used by the year-range filter. Persons missing both years are
 * excluded from time-windowed views entirely. */
export function lifespanBounds(person: Person): { from: number; to: number } | null {
  if (person.birth_year !== null && person.death_year !== null) {
    return { from: person.birth_year, to: person.death_year };
  }
  if (person.birth_year !== null) return { from: person.birth_year, to: person.birth_year };
  if (person.death_year !== null) return { from: person.death_year, to: person.death_year };
  return null;
}

export function isAliveInRange(person: Person, start: number, end: number): boolean {
  const span = lifespanBounds(person);
  if (!span) return false;
  return span.from <= end && span.to >= start;
}

/** All explicit movements a person makes. Falls back to birth → death if no explicit
 * journey is recorded. */
export function effectiveJourney(person: Person): JourneyStep[] {
  if (person.journey && person.journey.length > 0) {
    return person.journey;
  }
  const out: JourneyStep[] = [];
  if (person.birth_place_id && placeById[person.birth_place_id]) {
    out.push({ year: person.birth_year, place_id: person.birth_place_id, event: 'Born' });
  }
  if (
    person.death_place_id &&
    placeById[person.death_place_id] &&
    person.death_place_id !== person.birth_place_id
  ) {
    out.push({ year: person.death_year, place_id: person.death_place_id, event: 'Passed away' });
  } else if (person.death_year && person.death_place_id) {
    out.push({ year: person.death_year, place_id: person.death_place_id, event: 'Passed away' });
  }
  return out;
}

/** Group visible persons by their primary place. Used by the map. */
export function placeGroupsFor(visible: Person[]): PersonsAtPlace[] {
  const groups = new Map<string, PersonsAtPlace>();
  for (const person of visible) {
    const place = primaryPlaceOf(person);
    if (!place) continue;
    let entry = groups.get(place.id);
    if (!entry) {
      entry = { place, persons: [] };
      groups.set(place.id, entry);
    }
    entry.persons.push(person);
  }
  return [...groups.values()];
}

export const datedPersons: Person[] = persons.filter(
  (p) => p.birth_year !== null || p.death_year !== null,
);

export const undatedPersons: Person[] = persons.filter(
  (p) => p.birth_year === null && p.death_year === null,
);

export const mappablePersons: Person[] = persons.filter((p) => primaryPlaceOf(p) !== null);

export const YEAR_MIN = (() => {
  let min = 1700;
  for (const p of persons) {
    if (p.birth_year !== null && p.birth_year < min) min = p.birth_year;
  }
  return Math.floor(min / 10) * 10;
})();

export const YEAR_MAX = (() => {
  let max = 2020;
  for (const p of persons) {
    if (p.death_year !== null && p.death_year > max) max = p.death_year;
  }
  return Math.ceil(max / 10) * 10;
})();

export function matchesQuery(person: Person, q: string): boolean {
  if (!q) return true;
  const needle = q.trim().toLowerCase();
  if (!needle) return true;
  return (
    person.name_en.toLowerCase().includes(needle) ||
    person.common_name.toLowerCase().includes(needle) ||
    person.name_he.includes(needle) ||
    person.role.toLowerCase().includes(needle)
  );
}

if (import.meta.env.DEV) {
  const dated = datedPersons.length;
  const mappable = mappablePersons.length;
  // eslint-disable-next-line no-console
  console.info(
    `[data] persons=${persons.length} places=${places.length} dated=${dated} mappable=${mappable} years=${YEAR_MIN}–${YEAR_MAX}`,
  );
  const unresolved = persons.flatMap((p) => {
    const out: string[] = [];
    for (const field of ['birth_place_id', 'death_place_id', 'primary_place_id'] as const) {
      const v = p[field];
      if (v && !placeById[v]) out.push(`${p.id}.${field}=${v}`);
    }
    return out;
  });
  if (unresolved.length) {
    // eslint-disable-next-line no-console
    console.warn('[data] unresolved place refs:', unresolved);
  }
}
