import { effectiveJourney, placeById } from '../data';
import { GENERATIONS } from '../types';
import type { JourneyStep, Person, Place } from '../types';

interface PersonPanelProps {
  person: Person;
  onClose: () => void;
  onSelectPlace: (place: Place) => void;
}

export function PersonPanel({ person, onClose, onSelectPlace }: PersonPanelProps) {
  const gen = GENERATIONS[person.generation];
  const journey = effectiveJourney(person);
  const hasExplicitJourney = (person.journey?.length ?? 0) > 0;

  return (
    <div className="absolute inset-0 z-30 flex items-stretch justify-end bg-slate-900/30" onClick={onClose}>
      <article
        className="flex h-full w-[28rem] flex-col bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <header
          className="shrink-0 border-l-4 px-5 pb-4 pt-5"
          style={{ borderLeftColor: gen.color }}
        >
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="mb-1 text-xs font-medium uppercase tracking-wider" style={{ color: gen.color }}>
                {gen.label} era · {person.role}
              </p>
              <h2 className="text-xl font-semibold text-slate-900">{person.common_name}</h2>
              <p className="mt-0.5 text-sm text-slate-600">{person.name_en}</p>
              <p className="hebrew mt-1 text-lg text-slate-700">{person.name_he}</p>
            </div>
            <button
              type="button"
              onClick={onClose}
              aria-label="Close"
              className="shrink-0 rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
            >
              ✕
            </button>
          </div>

          <div className="mt-3 text-sm text-slate-600">
            {(person.birth_year || person.death_year) ? (
              <span>
                {person.birth_year ?? '?'} – {person.death_year ?? '?'}
              </span>
            ) : (
              <span className="italic text-slate-400">Dates unknown</span>
            )}
          </div>
        </header>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          {person.photo_url && (
            <div className="mb-4 overflow-hidden rounded-md border border-slate-200 bg-slate-50">
              <img
                src={person.photo_url}
                alt={person.common_name}
                referrerPolicy="no-referrer"
                className="block max-h-72 w-full object-contain"
                onError={(e) => {
                  (e.currentTarget as HTMLImageElement).style.display = 'none';
                }}
              />
            </div>
          )}

          {journey.length > 0 && (
            <section>
              <div className="flex items-baseline justify-between">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Journey</h3>
                {!hasExplicitJourney && (
                  <span className="text-[10px] italic text-slate-400">birth & death only</span>
                )}
              </div>
              <ol className="mt-2 space-y-2 border-l-2 border-slate-200 pl-4">
                {journey.map((step, idx) => (
                  <JourneyStepRow
                    key={`${idx}-${step.place_id}`}
                    step={step}
                    index={idx + 1}
                    color={gen.color}
                    onSelectPlace={onSelectPlace}
                  />
                ))}
              </ol>
            </section>
          )}

          <h3 className="mt-5 text-xs font-semibold uppercase tracking-wider text-slate-500">Biography</h3>
          <p className="mt-2 text-sm leading-relaxed text-slate-700 whitespace-pre-line">{person.bio}</p>

          {person.chabadpedia_url && (
            <p className="mt-4 text-xs">
              <a
                href={person.chabadpedia_url}
                target="_blank"
                rel="noreferrer noopener"
                className="text-indigo-600 hover:underline"
              >
                More on Chabadpedia →
              </a>
            </p>
          )}
        </div>
      </article>
    </div>
  );
}

function JourneyStepRow({
  step,
  index,
  color,
  onSelectPlace,
}: {
  step: JourneyStep;
  index: number;
  color: string;
  onSelectPlace: (place: Place) => void;
}) {
  const place = placeById[step.place_id];
  return (
    <li className="relative">
      <span
        className="absolute -left-[22px] mt-0.5 flex size-4 items-center justify-center rounded-full border-2 border-white text-[9px] font-bold text-white shadow"
        style={{ backgroundColor: color }}
      >
        {index}
      </span>
      <div className="text-sm">
        <span className="font-medium text-slate-800">{step.event}</span>
        <span className="text-slate-500"> — </span>
        {place ? (
          <button
            type="button"
            onClick={() => onSelectPlace(place)}
            className="text-slate-700 underline-offset-2 hover:text-indigo-700 hover:underline"
          >
            {place.name_en}
          </button>
        ) : (
          <span className="text-slate-500">{step.place_id}</span>
        )}
        {step.year !== null && step.year !== undefined && (
          <span className="ml-2 font-mono text-xs text-slate-400">{step.year}</span>
        )}
      </div>
    </li>
  );
}
