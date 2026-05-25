import { useMemo, useState } from 'react';
import {
  YEAR_MAX,
  YEAR_MIN,
  isAliveInRange,
  mappablePersons,
  matchesQuery,
  persons,
  placeGroupsFor,
  primaryPlaceOf,
} from './data';
import type { Person, Place } from './types';
import { ALL_GENERATIONS, GENERATIONS } from './types';
import { MapView } from './components/MapView';
import { TimelineView } from './components/TimelineView';
import { PersonPanel } from './components/PersonPanel';
import { PlacePanel } from './components/PlacePanel';
import { SearchPanel } from './components/SearchPanel';
import { YearRangeSlider } from './components/YearRangeSlider';

type ViewName = 'map' | 'lifespans';

export default function App() {
  const [view, setView] = useState<ViewName>('map');
  const [yearRange, setYearRange] = useState<[number, number]>([YEAR_MIN, YEAR_MAX]);
  const [selectedPlace, setSelectedPlace] = useState<Place | null>(null);
  const [selectedPerson, setSelectedPerson] = useState<Person | null>(null);
  const [query, setQuery] = useState('');

  const [start, end] = yearRange;

  const visiblePersons = useMemo(
    () => mappablePersons.filter((p) => isAliveInRange(p, start, end)),
    [start, end],
  );

  const placeGroups = useMemo(() => placeGroupsFor(visiblePersons), [visiblePersons]);

  const personsAtSelectedPlace = useMemo(() => {
    if (!selectedPlace) return [];
    const group = placeGroups.find((g) => g.place.id === selectedPlace.id);
    return group?.persons ?? [];
  }, [placeGroups, selectedPlace]);

  const searchResults = useMemo(() => {
    const q = query.trim();
    if (!q) return [] as Person[];
    return persons.filter((p) => matchesQuery(p, q)).slice(0, 25);
  }, [query]);

  function selectPerson(person: Person) {
    setSelectedPerson(person);
    setQuery('');
  }

  function selectPlace(place: Place) {
    setSelectedPerson(null);
    if (view !== 'map') setView('map');
    setSelectedPlace(place);
  }

  function jumpToPersonOnMap(person: Person) {
    const place = primaryPlaceOf(person);
    setSelectedPerson(person);
    setQuery('');
    if (place && view !== 'map') setView('map');
    if (place) setSelectedPlace(place);
  }

  return (
    <div className="flex h-full w-full flex-col bg-slate-50 text-slate-900">
      <header className="flex shrink-0 items-center gap-4 border-b border-slate-200 bg-white px-4 py-2 shadow-sm">
        <div className="flex items-baseline gap-2">
          <h1 className="text-lg font-semibold text-slate-900">Chabad Historical Map</h1>
          <span className="text-xs text-slate-500">
            {persons.length} figures · {mappablePersons.length} placed
          </span>
        </div>
        <nav className="ml-4 flex items-center gap-1 rounded-md bg-slate-100 p-1 text-sm">
          <button
            type="button"
            onClick={() => setView('map')}
            className={`rounded px-3 py-1 transition-colors ${
              view === 'map' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Map
          </button>
          <button
            type="button"
            onClick={() => setView('lifespans')}
            className={`rounded px-3 py-1 transition-colors ${
              view === 'lifespans' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Lifespans
          </button>
        </nav>
        <div className="ml-auto w-72">
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by name (English or עברית)"
            className="w-full rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm shadow-sm outline-none placeholder:text-slate-400 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-200"
          />
        </div>
      </header>

      <div className="relative flex-1 overflow-hidden">
        {view === 'map' ? (
          <MapView
            yearRange={yearRange}
            selectedPlace={selectedPlace}
            onSelectPlace={(place) => {
              setSelectedPerson(null);
              setSelectedPlace(place);
            }}
          />
        ) : (
          <TimelineView onSelectPerson={jumpToPersonOnMap} />
        )}

        {query.trim().length > 0 && (
          <SearchPanel
            query={query}
            results={searchResults}
            onSelectPerson={(p) => {
              jumpToPersonOnMap(p);
            }}
            onClose={() => setQuery('')}
          />
        )}

        {view === 'map' && selectedPlace && (
          <PlacePanel
            place={selectedPlace}
            persons={personsAtSelectedPlace}
            onClose={() => setSelectedPlace(null)}
            onSelectPerson={selectPerson}
          />
        )}

        {selectedPerson && (
          <PersonPanel
            person={selectedPerson}
            onClose={() => setSelectedPerson(null)}
            onSelectPlace={selectPlace}
          />
        )}
      </div>

      {view === 'map' && (
        <div className="shrink-0 border-t border-slate-200 bg-white">
          <YearRangeSlider min={YEAR_MIN} max={YEAR_MAX} value={yearRange} onChange={setYearRange} />
          <div className="flex items-center gap-3 border-t border-slate-100 px-4 py-1.5 text-[10px] text-slate-500">
            <span className="font-medium text-slate-600">
              {visiblePersons.length} alive · {placeGroups.length} places
            </span>
            <span className="text-slate-300">|</span>
            <div className="flex items-center gap-3 overflow-x-auto">
              {ALL_GENERATIONS.map((g) => (
                <div key={g} className="flex items-center gap-1 whitespace-nowrap">
                  <span
                    className="inline-block size-2 rounded-full"
                    style={{ backgroundColor: GENERATIONS[g].color }}
                  />
                  <span className="text-slate-600">{GENERATIONS[g].label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
