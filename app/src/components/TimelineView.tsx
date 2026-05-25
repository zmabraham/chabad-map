import { useMemo, useState } from 'react';
import { datedPersons, undatedPersons } from '../data';
import { GENERATIONS, ALL_GENERATIONS } from '../types';
import type { Generation, Person } from '../types';

const START_YEAR = 1690;
const END_YEAR = 2030;
const TOTAL_YEARS = END_YEAR - START_YEAR;
const PX_PER_YEAR = 5;
const ROW_HEIGHT = 22;
const TIMELINE_WIDTH = TOTAL_YEARS * PX_PER_YEAR;

interface TimelineViewProps {
  onSelectPerson: (person: Person) => void;
}

function sortKey(p: Person): number {
  return p.birth_year ?? p.death_year ?? Number.MAX_SAFE_INTEGER;
}

export function TimelineView({ onSelectPerson }: TimelineViewProps) {
  const [activeGens, setActiveGens] = useState<Set<Generation>>(new Set(ALL_GENERATIONS));

  const visible = useMemo(
    () => datedPersons.filter((p) => activeGens.has(p.generation)).sort((a, b) => sortKey(a) - sortKey(b)),
    [activeGens],
  );

  const decades = useMemo(() => {
    const out: number[] = [];
    for (let y = Math.ceil(START_YEAR / 10) * 10; y <= END_YEAR; y += 10) out.push(y);
    return out;
  }, []);

  function toggleGen(g: Generation) {
    setActiveGens((prev) => {
      const next = new Set(prev);
      if (next.has(g)) next.delete(g);
      else next.add(g);
      return next;
    });
  }

  return (
    <div className="flex h-full w-full">
      <div className="flex-1 overflow-auto bg-white">
        <div className="sticky top-0 z-20 flex items-center gap-1 border-b border-slate-200 bg-white/95 px-3 py-2 text-xs backdrop-blur">
          <span className="mr-2 text-slate-500">Filter:</span>
          {ALL_GENERATIONS.map((g) => {
            const active = activeGens.has(g);
            return (
              <button
                key={g}
                type="button"
                onClick={() => toggleGen(g)}
                className={`flex items-center gap-1 rounded-full border px-2 py-0.5 transition-opacity ${
                  active ? 'border-slate-300' : 'border-slate-200 opacity-40'
                }`}
                style={active ? { borderColor: GENERATIONS[g].color } : undefined}
              >
                <span className="inline-block size-2 rounded-full" style={{ backgroundColor: GENERATIONS[g].color }} />
                <span className="text-slate-700">{GENERATIONS[g].label}</span>
              </button>
            );
          })}
          <span className="ml-auto text-slate-400">
            Showing {visible.length} of {datedPersons.length} dated · {undatedPersons.length} undated in sidebar →
          </span>
        </div>

        <div style={{ width: TIMELINE_WIDTH + 200, paddingLeft: 200 }} className="relative">
          {/* Year axis (sticky under filter row) */}
          <div className="sticky top-[42px] z-10 h-7 border-b border-slate-200 bg-white" style={{ width: TIMELINE_WIDTH }}>
            {decades.map((y) => {
              const left = (y - START_YEAR) * PX_PER_YEAR;
              const major = y % 50 === 0;
              return (
                <div
                  key={y}
                  className="absolute top-0 h-full"
                  style={{ left, borderLeft: major ? '1px solid #cbd5e1' : '1px dashed #e2e8f0' }}
                >
                  {major && (
                    <span className="absolute left-1 top-1 text-[10px] font-medium text-slate-500">{y}</span>
                  )}
                </div>
              );
            })}
          </div>

          {/* Decade gridlines through the whole list */}
          <div className="pointer-events-none absolute top-[42px] bottom-0" style={{ left: 200, width: TIMELINE_WIDTH }}>
            {decades.map((y) => {
              const left = (y - START_YEAR) * PX_PER_YEAR;
              const major = y % 50 === 0;
              return (
                <div
                  key={y}
                  className="absolute top-0 bottom-0"
                  style={{ left, borderLeft: major ? '1px solid #e2e8f0' : '1px dashed #f1f5f9' }}
                />
              );
            })}
          </div>

          {/* Rows */}
          <div className="relative" style={{ width: TIMELINE_WIDTH }}>
            {visible.map((p, i) => (
              <TimelineRow key={p.id} person={p} y={i} onSelect={onSelectPerson} />
            ))}
          </div>
        </div>
      </div>

      <UndatedSidebar onSelectPerson={onSelectPerson} />
    </div>
  );
}

function TimelineRow({
  person,
  y,
  onSelect,
}: {
  person: Person;
  y: number;
  onSelect: (person: Person) => void;
}) {
  const color = GENERATIONS[person.generation].color;
  const birth = person.birth_year;
  const death = person.death_year;

  let left: number;
  let width: number;
  let isTick = false;

  if (birth !== null && death !== null) {
    left = (birth - START_YEAR) * PX_PER_YEAR;
    width = (death - birth) * PX_PER_YEAR;
  } else if (birth !== null) {
    left = (birth - START_YEAR) * PX_PER_YEAR;
    width = 6;
    isTick = true;
  } else if (death !== null) {
    left = (death - START_YEAR) * PX_PER_YEAR - 3;
    width = 6;
    isTick = true;
  } else {
    return null;
  }

  return (
    <div
      className="group absolute"
      style={{ top: y * ROW_HEIGHT, left: 0, width: '100%', height: ROW_HEIGHT }}
    >
      <button
        type="button"
        onClick={() => onSelect(person)}
        className="absolute -left-[200px] flex h-full w-[196px] items-center justify-end gap-1 truncate pr-2 text-right text-[11px] text-slate-600 hover:text-slate-900"
        title={person.common_name}
      >
        <span className="truncate">{person.common_name}</span>
      </button>
      <button
        type="button"
        onClick={() => onSelect(person)}
        title={`${person.common_name} (${birth ?? '?'}–${death ?? '?'})`}
        className={`absolute top-1/2 -translate-y-1/2 rounded-sm transition-all hover:brightness-110 ${
          isTick ? 'h-3' : 'h-3.5'
        }`}
        style={{
          left,
          width: Math.max(width, isTick ? 6 : 4),
          backgroundColor: color,
        }}
      />
    </div>
  );
}

function UndatedSidebar({ onSelectPerson }: { onSelectPerson: (person: Person) => void }) {
  return (
    <aside className="hidden h-full w-64 shrink-0 overflow-y-auto border-l border-slate-200 bg-slate-50 lg:block">
      <h3 className="sticky top-0 border-b border-slate-200 bg-slate-50/95 px-3 py-2 text-xs font-semibold uppercase tracking-wider text-slate-500 backdrop-blur">
        Undated figures ({undatedPersons.length})
      </h3>
      <ul className="px-1 py-1">
        {undatedPersons.map((p) => (
          <li key={p.id}>
            <button
              type="button"
              onClick={() => onSelectPerson(p)}
              className="flex w-full items-start gap-2 rounded px-2 py-1.5 text-left text-xs hover:bg-white"
            >
              <span
                className="mt-1 inline-block size-2 shrink-0 rounded-full"
                style={{ backgroundColor: GENERATIONS[p.generation].color }}
              />
              <span className="min-w-0 flex-1">
                <span className="block truncate font-medium text-slate-800">{p.common_name}</span>
                <span className="block truncate text-slate-500">{p.role}</span>
              </span>
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
}
