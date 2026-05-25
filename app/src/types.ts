export type Generation = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7;

export interface JourneyStep {
  year: number | null;
  place_id: string;
  event: string;
}

export interface Person {
  id: string;
  name_en: string;
  name_he: string;
  common_name: string;
  generation: Generation;
  birth_year: number | null;
  death_year: number | null;
  birth_place_id: string | null;
  death_place_id: string | null;
  role: string;
  bio: string;
  chabadpedia_url?: string | null;
  photo_url?: string | null;
  primary_place_id?: string | null;
  journey?: JourneyStep[];
}

export interface Place {
  id: string;
  name_en: string;
  name_he: string;
  lat: number;
  lng: number;
  modern_country: string;
  significance?: string;
}

export interface GenerationMeta {
  label: string;
  era: string;
  color: string;
  ring: string;
  text: string;
}

export const GENERATIONS: Record<Generation, GenerationMeta> = {
  0: { label: 'Pre-Chabad',     era: 'Baal Shem Tov, Maggid', color: '#64748b', ring: 'ring-slate-400',   text: 'text-slate-700' },
  1: { label: 'Alter Rebbe',    era: '1745–1812',              color: '#6366f1', ring: 'ring-indigo-400',  text: 'text-indigo-700' },
  2: { label: 'Mitteler Rebbe', era: '1773–1827',              color: '#3b82f6', ring: 'ring-blue-400',    text: 'text-blue-700' },
  3: { label: 'Tzemach Tzedek', era: '1789–1866',              color: '#14b8a6', ring: 'ring-teal-400',    text: 'text-teal-700' },
  4: { label: 'Maharash',       era: '1834–1882',              color: '#10b981', ring: 'ring-emerald-400', text: 'text-emerald-700' },
  5: { label: 'Rashab',         era: '1860–1920',              color: '#f59e0b', ring: 'ring-amber-400',   text: 'text-amber-700' },
  6: { label: 'Rayatz',         era: '1880–1950',              color: '#f97316', ring: 'ring-orange-400',  text: 'text-orange-700' },
  7: { label: 'The Rebbe',      era: '1902–1994',              color: '#ef4444', ring: 'ring-red-400',     text: 'text-red-700' },
};

export const ALL_GENERATIONS: Generation[] = [0, 1, 2, 3, 4, 5, 6, 7];
