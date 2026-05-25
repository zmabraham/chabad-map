import { useCallback, useEffect, useRef, useState } from 'react';

interface YearRangeSliderProps {
  min: number;
  max: number;
  value: [number, number];
  onChange: (value: [number, number]) => void;
}

export function YearRangeSlider({ min, max, value, onChange }: YearRangeSliderProps) {
  const trackRef = useRef<HTMLDivElement>(null);
  const [dragging, setDragging] = useState<'start' | 'end' | null>(null);

  const [start, end] = value;
  const range = max - min;
  const startPct = ((start - min) / range) * 100;
  const endPct = ((end - min) / range) * 100;

  const yearFromClientX = useCallback(
    (clientX: number): number => {
      const track = trackRef.current;
      if (!track) return start;
      const rect = track.getBoundingClientRect();
      const ratio = Math.min(1, Math.max(0, (clientX - rect.left) / rect.width));
      return Math.round(min + ratio * range);
    },
    [min, range, start],
  );

  useEffect(() => {
    if (!dragging) return;
    function onMove(e: PointerEvent) {
      const year = yearFromClientX(e.clientX);
      if (dragging === 'start') {
        onChange([Math.min(year, end), end]);
      } else {
        onChange([start, Math.max(year, start)]);
      }
    }
    function onUp() {
      setDragging(null);
    }
    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', onUp);
    window.addEventListener('pointercancel', onUp);
    return () => {
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
      window.removeEventListener('pointercancel', onUp);
    };
  }, [dragging, end, start, onChange, yearFromClientX]);

  function startDrag(handle: 'start' | 'end') {
    return (e: React.PointerEvent) => {
      e.preventDefault();
      (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
      setDragging(handle);
    };
  }

  function onTrackClick(e: React.PointerEvent) {
    if (dragging) return;
    const year = yearFromClientX(e.clientX);
    const distStart = Math.abs(year - start);
    const distEnd = Math.abs(year - end);
    if (distStart < distEnd) onChange([Math.min(year, end), end]);
    else onChange([start, Math.max(year, start)]);
  }

  const isFullRange = start === min && end === max;

  return (
    <div className="flex w-full items-center gap-3 px-4 py-3">
      <div className="flex flex-col items-end" style={{ minWidth: 56 }}>
        <span className="text-[10px] uppercase tracking-wider text-slate-500">From</span>
        <span className="font-mono text-sm font-semibold text-slate-800">{start}</span>
      </div>
      <div className="relative flex-1">
        <div
          ref={trackRef}
          className="relative h-2 cursor-pointer rounded-full bg-slate-200"
          onPointerDown={onTrackClick}
        >
          <div
            className="absolute h-full rounded-full bg-indigo-500"
            style={{ left: `${startPct}%`, right: `${100 - endPct}%` }}
          />
          <Handle pct={startPct} onPointerDown={startDrag('start')} active={dragging === 'start'} />
          <Handle pct={endPct} onPointerDown={startDrag('end')} active={dragging === 'end'} />
        </div>
        <div className="mt-1 flex justify-between text-[10px] text-slate-400">
          <span>{min}</span>
          <span>{Math.round((min + max) / 2)}</span>
          <span>{max}</span>
        </div>
      </div>
      <div className="flex flex-col items-start" style={{ minWidth: 56 }}>
        <span className="text-[10px] uppercase tracking-wider text-slate-500">To</span>
        <span className="font-mono text-sm font-semibold text-slate-800">{end}</span>
      </div>
      <button
        type="button"
        disabled={isFullRange}
        onClick={() => onChange([min, max])}
        className="ml-1 rounded border border-slate-300 px-2 py-1 text-xs text-slate-600 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-40"
      >
        All years
      </button>
    </div>
  );
}

function Handle({
  pct,
  onPointerDown,
  active,
}: {
  pct: number;
  onPointerDown: (e: React.PointerEvent) => void;
  active: boolean;
}) {
  return (
    <button
      type="button"
      onPointerDown={(e) => {
        e.stopPropagation();
        onPointerDown(e);
      }}
      aria-label="Year handle"
      className={`absolute top-1/2 -translate-x-1/2 -translate-y-1/2 cursor-grab touch-none rounded-full border-2 border-white bg-indigo-600 shadow ${
        active ? 'h-5 w-5 cursor-grabbing ring-2 ring-indigo-300' : 'h-4 w-4'
      }`}
      style={{ left: `${pct}%` }}
    />
  );
}
