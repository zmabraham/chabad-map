import { useMemo } from 'react';
import { Map as MapGL, Marker, NavigationControl, AttributionControl } from 'react-map-gl/maplibre';
import type { StyleSpecification } from 'maplibre-gl';
import { isAliveInRange, mappablePersons, placeGroupsFor, type PersonsAtPlace } from '../data';
import { GENERATIONS } from '../types';
import type { Generation, Place } from '../types';

const MAP_STYLE: StyleSpecification = {
  version: 8,
  sources: {
    base: {
      type: 'raster',
      tiles: [
        'https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
        'https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
        'https://c.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
      ],
      tileSize: 256,
      attribution:
        '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, © <a href="https://carto.com/attributions">CARTO</a>',
    },
  },
  layers: [{ id: 'base', type: 'raster', source: 'base' }],
};

function predominantGeneration(group: PersonsAtPlace): Generation {
  const counts = new Map<Generation, number>();
  for (const p of group.persons) counts.set(p.generation, (counts.get(p.generation) ?? 0) + 1);
  let bestGen: Generation = group.persons[0]?.generation ?? 0;
  let bestCount = -1;
  for (const [g, c] of counts) {
    if (c > bestCount || (c === bestCount && g < bestGen)) {
      bestGen = g;
      bestCount = c;
    }
  }
  return bestGen;
}

interface MapViewProps {
  yearRange: [number, number];
  selectedPlace: Place | null;
  onSelectPlace: (place: Place) => void;
}

export function MapView({ yearRange, selectedPlace, onSelectPlace }: MapViewProps) {
  const [start, end] = yearRange;

  const groups = useMemo(() => {
    const alive = mappablePersons.filter((p) => isAliveInRange(p, start, end));
    return placeGroupsFor(alive);
  }, [start, end]);

  const markers = useMemo(
    () =>
      groups.map((group) => ({
        place: group.place,
        count: group.persons.length,
        color: GENERATIONS[predominantGeneration(group)].color,
      })),
    [groups],
  );

  return (
    <div className="absolute inset-0">
      <MapGL
        initialViewState={{
          bounds: [
            [-75, 30],
            [37, 60],
          ],
          fitBoundsOptions: { padding: 60 },
        }}
        mapStyle={MAP_STYLE}
        attributionControl={false}
      >
        <NavigationControl position="top-right" showCompass={false} />
        <AttributionControl position="bottom-right" compact />
        {markers.map(({ place, count, color }) => {
          const isSelected = selectedPlace?.id === place.id;
          const size = Math.min(32, 14 + Math.sqrt(count) * 4);
          return (
            <Marker
              key={place.id}
              longitude={place.lng}
              latitude={place.lat}
              anchor="center"
              onClick={(e) => {
                e.originalEvent.stopPropagation();
                onSelectPlace(place);
              }}
            >
              <button
                type="button"
                aria-label={`${place.name_en} — ${count} ${count === 1 ? 'person' : 'people'}`}
                className={`block cursor-pointer rounded-full border-2 border-white shadow transition-transform hover:scale-110 ${
                  isSelected ? 'ring-4 ring-indigo-300' : ''
                }`}
                style={{
                  width: size,
                  height: size,
                  backgroundColor: color,
                }}
              >
                {count > 1 && (
                  <span
                    className="block text-center text-[11px] font-bold leading-none text-white"
                    style={{ lineHeight: `${size}px` }}
                  >
                    {count}
                  </span>
                )}
              </button>
            </Marker>
          );
        })}
        {groups.length === 0 && (
          <div className="pointer-events-none absolute left-1/2 top-12 -translate-x-1/2 rounded-md bg-white/90 px-3 py-1.5 text-sm text-slate-600 shadow">
            No one in the dataset was alive between {start} and {end}.
          </div>
        )}
      </MapGL>
    </div>
  );
}
