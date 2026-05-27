"""Apply enrichment results to persons.json with proper place ID resolution.

Reads:
  scripts/enrichment_results.json  -- per-person data dict
  data/persons.json
  data/places.json

Writes:
  data/persons.json (updated, only fills nulls)
  scripts/place_unmatched.json (collection of Hebrew place names that didn't resolve)
"""
import json, os

ROOT = r"C:\Users\rabbi\OneDrive\Desktop\chabad-map\chabad-map"


def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def save(p, data):
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# Manual Hebrew place variants → place id
PLACE_VARIANTS = {
    "מז'יבוז'": 'mezhibuzh', "מז'יבוז": 'mezhibuzh', "מזיבוז": 'mezhibuzh',
    "מעזיבוז": 'mezhibuzh', "מעזיבוז'": 'mezhibuzh',
    "ליאזנא": 'liozna', "ליאזנע": 'liozna',
    "פיענא": 'piena', "פיענה": 'piena',
    "ניעז'ין": 'niezhin', "ניעזין": 'niezhin', "נעז'ין": 'niezhin',
    "ניז'ין": 'niezhin', "ניזי'ן": 'niezhin', "ניעז'ין": 'niezhin',
    "ניעז\\'ין": 'niezhin',
    "ליובאוויטש": 'lubavitch', "ליובאוויץ'": 'lubavitch',
    "רוסטוב": 'rostov',
    "אניפולי": 'anipoli', "אנופולי": 'anipoli',
    "ניקולייב": 'nikolaev', "ניקלאייב": 'nikolaev', "ניקולאיב": 'nikolaev',
    "ניו יורק": 'new-york',
    "באבינוביטש": 'babinovich', "בינוביץ": 'babinovich', "בינוביץ'": 'babinovich',
    "באבינוביץ": 'babinovich', "באבינאוויטש": 'babinovich',
    "קישינב": 'kishinev', "קישינוב": 'kishinev',
    "ליברפול": 'liverpool',
    "שקלוב": 'shklov',
    "הומיל": 'homel', "האמיל": 'homel', "האמלי": 'homel', "הומל": 'homel',
    "ויטבסק": 'vitebsk', "וויטבסק": 'vitebsk', "וויטעבסק": 'vitebsk', "וויטעבסק": 'vitebsk',
    "ירושלים": 'jerusalem',
    "חברון": 'hebron',
    "טבריה": 'tiberias',
    "פסטוב": 'fastov',
    "ברדיטשוב": 'berditchev', "ברדיצ'ב": 'berditchev', "ברדיטשוב": 'berditchev',
    "ליז'נסק": 'lizhensk', "ליז'ענסק": 'lizhensk', "ליז'ינסק": 'lizhensk',
    "ניקלשבורג": 'nikolsburg', "ניקולסבורג": 'nikolsburg',
    "ליאדי": 'liadi',
    "קאפוסט": 'kapust', "קופוסט": 'kapust',
    "אוורוטש": 'avritch', "אווריטש": 'avritch',
    "חרסון": 'kherson',
    "פראהביטש": 'prohovitch',
    "סדיגורה": 'sadigura', "סדיגורא": 'sadigura',
    "לודמיר": 'ludmir',
    "מעזריטש": 'mezritch', "מעזירטש": 'mezritch', "מזריטש": 'mezritch', "מעזיריטש": 'mezritch',
    "אורשא": 'orsha',
    "סטראשעליע": 'strashelye', "סטראשעלע": 'strashelye',
    "צ'רנוביל": 'chernobyl', "טשערנאביל": 'chernobyl',
    "האדיטש": 'hadiach',
    "אנטבקה": None,  # Annapol/Antopil — not in places
    "טולצ'ין": None,  # Tolchin — not in places
    "פינסק": None,
    "קרמנצ'וג": 'kremenchug',
    "ארצות הברית": 'new-york',  # Default US for Rayatz death
    # negative entries: don't match
    "טלוסט": None, "לוקאטש": None, "ברודי": None, "יאמפולי": None,
    "טשורטקוב": None, "הוסקוב": None, "חומץ": None,
    "גורינסק": None, "שפטיבקה": None, "רומנובקה": None,
    "גרודזיסק": None, "רודמיסל": None, "ואלחאיי": None,
    "אוסבה שברוסיה הלבנה": None, "אוסבה": None,
    "דיסנה": 'disna',
    "ארץ הקודש": None,
    "ליטא": None,
    "פולין": None,
    "ניקולסבורג": 'nikolsburg',
    "קאליסק": 'kalisk',
    "קליסק": 'kalisk',
    "נעוועל": 'nevel',
    "באבינוויטש": 'babinovich',
    "פוילנא": 'polonne',
    "פולנאה": 'polonne',
    "פולנה": 'polonne',
    "סמרקנד": 'samarkand',
    "טשקנט": 'tashkent',
    "ראסטוב": 'rostov',
    "ראסטאוו": 'rostov',
    "יעקאטערינאסלאוו": 'yekaterinoslav',
    "יקטרינוסלב": 'yekaterinoslav',
    "אלמא אטא": 'alma-ata',
    "אלמא אטה": 'alma-ata',
    "טשיאילי": 'chiili',
    "באראניוויטש": None,
    "אודסה": None,
    "פטרבורג": 'petersburg',
    "פטרסבורג": 'petersburg',
    "פעטערבורג": 'petersburg',
    "סנט פטרסבורג": 'petersburg',
    "לעפלי": 'lepli',
    "לעפעל": 'lepli',
    "קרעסלאווא": 'krislava',
    "קרסלבה": 'krislava',
    "האדיטש": 'hadiach',
    "הדיטש": 'hadiach',
    "לונדון": 'london',
    "פריז": 'paris',
    "מרסיי": 'marseille',
    "ברונואה": 'brunoy',
    "אנטוורפן": 'antwerp',
    "אנטוורפ": 'antwerp',
    "סטוקהולם": 'stockholm',
    "בוכרה": 'bukhara',
    "בוכארה": 'bukhara',
    "מאנטרעאל": 'montreal',
    "מונטריאל": 'montreal',
    "ניוארק": 'newark',
    "פיטסבורג": 'pittsburgh',
    "באלטימור": 'baltimore',
    "באלטימאר": 'baltimore',
    "ניו הייווען": 'new-haven',
    "מנצסטר": 'manchester',
    "מאנטשעסטער": 'manchester',
    "ליווערפול": 'liverpool',
    "ליוורפול": 'liverpool',
    "וורשה": 'warsaw',
    "ווארשא": 'warsaw',
    "אוטוואצק": 'otwock',
    "אטוואצק": 'otwock',
    "וינה": 'vienna',
    "ווין": 'vienna',
    "תל אביב": 'tel-aviv',
    "רמת גן": 'ramat-gan',
    "בני ברק": 'bnei-brak',
    "כפר חב\"ד": 'kfar-chabad',
    "לוד": 'lod',
    "צפת": 'tzfat',
    "פתח תקווה": 'petach-tikva',
    "פתח תקוה": 'petach-tikva',
    "נחלת הר חב\"ד": 'nachlat-har-chabad',
    "שטשעדרין": 'shchedrin',
    "שצדרין": 'shchedrin',
    "ריגא": 'riga',
    "ריגה": 'riga',
    "שיקגו": 'chicago',
    "שיקאגא": 'chicago',
    "מוסקבה": 'moscow',
    "מאסקווא": 'moscow',
    "סיביר": 'siberia',
    "סיביריה": 'siberia',
    "טשערניגאוו": 'chernigov',
    "צ'רניגוב": 'chernigov',
    "סורז'": 'surazh',
    "סוראז'": 'surazh',
    "בעשענקאוויטש": 'beshankovich',
    "בעשנקוביטש": 'beshankovich',
    "ביעשנקוביץ": 'beshankovich',
    "בישנקוביץ": 'beshankovich',
    "בעשנקוביץ": 'beshankovich',
    "באבינאוויטש": 'babinovich',
    "באבינוויץ'": 'babinovich',
    "באבינוביץ": 'babinovich',
    "ראגאטשאוו": 'rogatchov',
    "רוגצ'וב": 'rogatchov',
    "פאלאצק": 'polotsk',
    "פולוצק": 'polotsk',
    "סמלוביץ": 'smilovitz',
    "סמילאוויטש": 'smilovitz',
    "סמיליאן": 'smilyan',
    "מינסק": 'minsk',
    "קלעצק": 'kletzk',
    "קלצק": 'kletzk',
    "קלעצקער": 'kletzk',
    "באריסאוו": 'borisov',
    "באריסוב": 'borisov',
    "ראקשיק": 'rakshik',
    "ראקעשיק": 'rakshik',
    "טולא": 'tula',
    "טולה": 'tula',
    "קאזימיראוו": 'kazimirov',
    "קזימירוב": 'kazimirov',
    "באבינאוויטש": 'babinovich',
    "אולא": 'ula',
    "זעמבין": 'zembin',
    "זימבין": 'zembin',
    "קורענעץ": 'kurenets',
    "קורענץ": 'kurenets',
    "קלימאוויטש": 'klimovitch',
    "קלימוביץ": 'klimovitch',
    "קלימוביטש": 'klimovitch',
    "טבריא": 'tiberias',
    "פולטבה": 'poltava',
    "פאלטאווא": 'poltava',
    "כארקאוו": 'kharkov',
    "חרקוב": 'kharkov',
    "כעראסאן": 'kherson',
    "כערסאן": 'kherson',
    "פאהאר": 'pohar',
    "פאר": 'pohar',
    "וועליזש": 'velizh',
    "וליז'": 'velizh',
    "קרעמענטשוג": 'kremenchug',
    "קרמנצ'וג": 'kremenchug',
    "קרעמענטשוק": 'kremenchug',
    "טריסק": 'trisk',
    "וווינא": 'vilna',
    "ווילנא": 'vilna',
    "וילנא": 'vilna',
    "וילנה": 'vilna',
    "שווינציאן": 'shvintzian',
    "בארדיטשוב": 'berditchev',
    "ראגעטשאוו": 'rogatchov',
    "ניעזין": 'niezhin',
    "טרבלינקה": 'treblinka',
    "טרעבלינקא": 'treblinka',
    "לעמבערג": 'lviv',
    "לבוב": 'lviv',
    "פאריז": 'paris',
    "מארסעי": 'marseille',
    "וולאדיוואסטאק": 'vladivostok',
    "ולדיווסטוק": 'vladivostok',
    "טאמבאוו": 'tambov',
    "שאנגחאי": 'shanghai',
    "שנחאי": 'shanghai',
    "באבריסק": 'bobruisk',
    "באברויסק": 'bobruisk',
    "בוברויסק": 'bobruisk',
    "ראגאצ'וב": 'rogatchov',
    "טשעקאוו": None,
    "פראהאוויטש": 'prohovitch',
    "פאדאבראנקא": 'podobranka',
    "פראגה": None,
    "ראדמיסל": None,  # Rodmisel - not in places
    "פראהביצ'": 'prohovitch',
    "פאריטש": 'paritch',
}


def resolve_place(name_he, by_he):
    if not name_he:
        return None, None
    name = name_he.strip()
    if name in by_he:
        return by_he[name], None
    if name in PLACE_VARIANTS:
        v = PLACE_VARIANTS[name]
        return v, (name if v is None else None)
    return None, name


def main():
    persons = load(os.path.join(ROOT, 'data', 'persons.json'))
    places = load(os.path.join(ROOT, 'data', 'places.json'))
    by_he = {p['name_he']: p['id'] for p in places}
    valid_ids = {p['id'] for p in places}

    results = load(os.path.join(ROOT, 'scripts', 'enrichment_results.json'))

    by_id = {p['id']: p for p in persons}
    filled_log = {}  # person_id -> list of fields filled
    unmatched_places = {}  # name_he -> [person_ids]

    for pid, info in results.items():
        if pid not in by_id:
            print(f"WARNING: unknown person id {pid}")
            continue
        if info.get('not_found'):
            filled_log[pid] = 'not_found'
            continue
        person = by_id[pid]
        filled = []

        # chabadpedia_url
        if info.get('chabadpedia_url') and person.get('chabadpedia_url') is None:
            person['chabadpedia_url'] = info['chabadpedia_url']
            filled.append('chabadpedia_url')

        # birth_year, death_year
        for fld in ('birth_year', 'death_year'):
            val = info.get(fld)
            if val is not None and person.get(fld) is None:
                if isinstance(val, int):
                    person[fld] = val
                    filled.append(fld)

        # photo_url
        if info.get('photo_url') and person.get('photo_url') is None:
            person['photo_url'] = info['photo_url']
            filled.append('photo_url')

        # birth_place_id from birth_place_he
        bp_he = info.get('birth_place_he')
        if bp_he and person.get('birth_place_id') is None:
            pid_resolved, um = resolve_place(bp_he, by_he)
            if pid_resolved and pid_resolved in valid_ids:
                person['birth_place_id'] = pid_resolved
                filled.append('birth_place_id')
            elif um:
                unmatched_places.setdefault(um, []).append(pid)

        # death_place_id
        dp_he = info.get('death_place_he')
        if dp_he and person.get('death_place_id') is None:
            pid_resolved, um = resolve_place(dp_he, by_he)
            if pid_resolved and pid_resolved in valid_ids:
                person['death_place_id'] = pid_resolved
                filled.append('death_place_id')
            elif um:
                unmatched_places.setdefault(um, []).append(pid)

        if filled:
            filled_log[pid] = filled

    # Validation before save
    assert len(persons) == 323, f"persons count drifted: {len(persons)}"
    for p in persons:
        for fld in ('birth_year', 'death_year'):
            val = p.get(fld)
            assert val is None or isinstance(val, int), f"{p['id']}.{fld} not int: {val}"
        for fld in ('birth_place_id', 'death_place_id', 'primary_place_id'):
            val = p.get(fld)
            if val is not None:
                assert val in valid_ids, f"{p['id']}.{fld} = {val} not in places.json"

    save(os.path.join(ROOT, 'data', 'persons.json'), persons)
    save(os.path.join(ROOT, 'scripts', 'place_unmatched.json'), unmatched_places)
    save(os.path.join(ROOT, 'scripts', 'fill_log.json'), filled_log)
    print(f"Updated {sum(1 for v in filled_log.values() if isinstance(v, list))} persons")
    print(f"Unmatched places: {len(unmatched_places)}")


if __name__ == '__main__':
    main()
