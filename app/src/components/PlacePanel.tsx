import { GENERATIONS } from '../types';
import type { Person, Place } from '../types';

interface PlacePanelProps {
  place: Place;
  persons: Person[];
  onClose: () => void;
  onSelectPerson: (person: Person) => void;
}

export function PlacePanel({ place, persons, onClose, onSelectPerson }: PlacePanelProps) {
  return (
    <aside className="absolute right-0 top-0 z-20 flex h-full w-96 flex-col border-l border-slate-200 bg-white shadow-xl">
      <header className="flex shrink-0 items-start justify-between gap-2 border-b border-slate-200 px-4 py-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">{place.name_en}</h2>
          <p className="hebrew mt-0.5 text-base text-slate-600">{place.name_he}</p>
          <p className="mt-1 text-xs text-slate-500">{place.modern_country}</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close"
          className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
        >
          ✕
        </button>
      </header>

      {place.significance && (
        <p className="shrink-0 border-b border-slate-100 bg-slate-50 px-4 py-2 text-xs leading-relaxed text-slate-600">
          {place.significance}
        </p>
      )}

      <div className="flex-1 overflow-y-auto px-2 py-2">
        <h3 className="px-2 py-1 text-xs font-semibold uppercase tracking-wider text-slate-500">
          {persons.length} {persons.length === 1 ? 'figure' : 'figures'}
        </h3>
        <ul>
          {persons.map((p) => (
            <li key={p.id}>
              <button
                type="button"
                onClick={() => onSelectPerson(p)}
                className="flex w-full items-start gap-3 rounded-md px-2 py-2 text-left hover:bg-slate-100"
              >
                <span
                  className="mt-1 inline-block size-2.5 shrink-0 rounded-full"
                  style={{ backgroundColor: GENERATIONS[p.generation].color }}
                  aria-hidden
                />
                <span className="min-w-0 flex-1">
                  <span className="block text-sm font-medium text-slate-900">{p.common_name}</span>
                  <span className="block text-xs text-slate-500">
                    {p.role}
                    {(p.birth_year || p.death_year) && ' · '}
                    {formatYears(p.birth_year, p.death_year)}
                  </span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      </div>
    </aside>
  );
}

function formatYears(birth: number | null, death: number | null): string {
  if (birth && death) return `${birth}–${death}`;
  if (birth) return `b. ${birth}`;
  if (death) return `d. ${death}`;
  return '';
}
