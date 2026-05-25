import type { Person } from '../types';
import { GENERATIONS } from '../types';

interface SearchPanelProps {
  query: string;
  results: Person[];
  onSelectPerson: (person: Person) => void;
  onClose: () => void;
}

export function SearchPanel({ query, results, onSelectPerson, onClose }: SearchPanelProps) {
  return (
    <aside className="absolute right-4 top-4 z-40 w-80 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-2xl">
      <header className="flex items-center justify-between gap-2 border-b border-slate-100 px-3 py-2">
        <p className="text-xs text-slate-500">
          {results.length === 0
            ? `No matches for "${query}"`
            : `${results.length} match${results.length === 1 ? '' : 'es'} for "${query}"`}
        </p>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close search"
          className="rounded p-0.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
        >
          ✕
        </button>
      </header>
      <ul className="max-h-[60vh] overflow-y-auto py-1">
        {results.map((p) => (
          <li key={p.id}>
            <button
              type="button"
              onClick={() => onSelectPerson(p)}
              className="flex w-full items-start gap-3 px-3 py-2 text-left hover:bg-slate-50"
            >
              <span
                className="mt-1.5 inline-block size-2.5 shrink-0 rounded-full"
                style={{ backgroundColor: GENERATIONS[p.generation].color }}
              />
              <span className="min-w-0 flex-1">
                <span className="block truncate text-sm font-medium text-slate-900">{p.common_name}</span>
                <span className="hebrew block truncate text-xs text-slate-500">{p.name_he}</span>
                <span className="block text-xs text-slate-400">
                  {p.role}
                  {(p.birth_year || p.death_year) && ' · '}
                  {p.birth_year ?? '?'}{(p.birth_year || p.death_year) && '–'}{p.death_year ?? '?'}
                </span>
              </span>
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
}
