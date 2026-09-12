from copy import deepcopy
from dataclasses import replace
from datetime import date
from itertools import permutations
import unittest

from models.event import Event
from services.deduplicator import deduplicate_events
from services.digest import format_event_list
from services.event_identity import compare_events, canonical_url


class EventIdentityTest(unittest.TestCase):
    def event(self, **values):
        defaults = dict(title='Vibra Mahou Fest', category='concert',
                        date=date(2026, 9, 12), time='13:00',
                        venue='Cide segovia', municipality='Segovia')
        defaults.update(values)
        return Event(**defaults)

    def test_segovia_festival_variants_and_artist_display(self):
        events = [
            self.event(price='22 €', source='A', url='https://a.test/event', source_priority=90),
            self.event(title='Vibra Mahou Festival Segovia 2026', price='33.0 €', source='B',
                       url='https://b.test/event', source_priority=80),
            self.event(title='Vibra Mahou Fest Segovia 2026 @ Centro de Innovación & Desarrollo Empresarial (CIDE)',
                       artist='Niños Bravos', participants=['Niños Bravos'], time=None,
                       end_date=date(2026, 9, 12),
                       venue='Centro de Innovación & Desarrollo Empresarial (CIDE)',
                       source='Songkick', url='https://songkick.com/festivals/example'),
            self.event(title='Richard Libeton', artist='Richard Libeton', date=date(2026, 9, 11), venue='Segovia'),
            self.event(title='Candlelight: Tributo a Hans Zimmer', venue='Alcázar de Segovia', time='21:00'),
        ]
        originals = deepcopy(events)
        result = deduplicate_events(events)
        self.assertEqual(len(result), 3)
        festival = next(e for e in result if len(e.sources) == 3)
        self.assertEqual(festival.match_level, 'MATCH')
        self.assertEqual(festival.price, '22 €')
        self.assertIn({'field': 'price', 'values': ['22 €', '33.0 €']}, festival.conflicts)
        self.assertEqual(festival.field_sources['price'], ['https://a.test/event'])
        self.assertEqual(events, originals)
        text = format_event_list(result)
        self.assertEqual(text.count('<b>Vibra Mahou Fest</b>'), 1)
        self.assertNotIn('<b>Niños Bravos</b>', text)
        for order in permutations(events[:3]):
            self.assertEqual(deduplicate_events(list(order))[0].canonical_id, festival.canonical_id)

    def test_artist_page_linked_to_festival_is_retained_as_act(self):
        festival = self.event(url='https://example.com/festival?utm_source=search', price='33 €')
        act = self.event(title='Niños Bravos', artist='Niños Bravos',
                         venue='Centro de Innovación & Desarrollo Empresarial (CIDE)',
                         url='https://example.com/festival?utm_source=artist', time=None, price='10 €')
        result = deduplicate_events([act, festival])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].price, '33 €')
        self.assertEqual(result[0].related_events[0].price, '10 €')
        self.assertEqual(result[0].related_events[0].sources[0]['title'], 'Niños Bravos')
        self.assertIn('Incluye: Niños Bravos', format_event_list(result))

    def test_same_place_date_alone_does_not_hide_artist(self):
        festival = self.event()
        act = self.event(title='Niños Bravos', artist='Niños Bravos', time=None)
        self.assertEqual(len(deduplicate_events([festival, act])), 2)

    def test_shared_agenda_page_is_not_a_parent_relationship(self):
        festival = self.event(url='https://example.com/agenda', original_data={'name': 'Vibra Mahou Fest'})
        act = self.event(title='Niños Bravos', artist='Niños Bravos',
                         url='https://example.com/agenda', original_data={'name': 'Niños Bravos'})
        self.assertEqual(len(deduplicate_events([festival, act])), 2)

    def test_conflicting_schema_types_are_not_merged(self):
        first = self.event(title='Espectáculo', event_type='TheaterEvent')
        second = self.event(title='Espectáculo', event_type='DanceEvent')
        self.assertEqual(compare_events(first, second).level, 'DIFFERENT')

    def test_invalid_time_cannot_match_valid_time(self):
        first = self.event(time='25:00')
        second = self.event(time='05:00')
        self.assertNotEqual(compare_events(first, second).level, 'MATCH')

    def test_explicit_lineup_keeps_performance_time_nested(self):
        festival = self.event(participants=['Niños Bravos', 'Sidecars'])
        act = self.event(title='Niños Bravos', artist='Niños Bravos', time='17:15')
        result = deduplicate_events([festival, act])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].time, '13:00')
        self.assertEqual(result[0].related_events[0].time, '17:15')

    def test_explicit_parent_name(self):
        festival = self.event()
        act = self.event(title='Niños Bravos', artist='Niños Bravos',
                         parent_event_name='Vibra Mahou Festival Segovia 2026')
        self.assertEqual(len(deduplicate_events([festival, act])), 1)

    def test_conflicting_parent_does_not_hide_artist(self):
        festival = self.event(participants=['Niños Bravos'])
        act = self.event(title='Niños Bravos', artist='Niños Bravos', parent_event_name='Otro Festival')
        self.assertEqual(len(deduplicate_events([festival, act])), 2)

    def test_multi_day_parent_and_day_pass_stay_separate(self):
        festival = self.event(end_date=date(2026, 9, 14), participants=['Niños Bravos'])
        day_pass = self.event()
        act = self.event(title='Niños Bravos', artist='Niños Bravos', parent_event_name='Vibra Mahou Fest')
        self.assertEqual(compare_events(festival, day_pass).level, 'POSSIBLE_MATCH')
        self.assertEqual(len(deduplicate_events([festival, act])), 2)
        result = deduplicate_events([festival, day_pass])
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].possible_matches[0]['level'], 'POSSIBLE_MATCH')

    def test_hard_conflicts_even_with_identical_title_and_id(self):
        first = self.event(external_ids={'@id': 'https://example.com/event'})
        for change in [dict(date=date(2026, 9, 13)), dict(venue='Otro recinto'),
                       dict(municipality='Madrid'), dict(country='Portugal'), dict(category='fair')]:
            with self.subTest(change=change):
                original = replace(first, country='España')
                second = replace(original, **change)
                self.assertEqual(compare_events(original, second).level, 'DIFFERENT')
                self.assertEqual(len(deduplicate_events([original, second])), 2)

    def test_same_artist_two_sessions(self):
        first = self.event(title='Concierto de Vetusta Morla', artist='Vetusta Morla', time='19:00')
        second = replace(first, time='21:00')
        result = deduplicate_events([first, second])
        self.assertEqual(len(result), 2)
        self.assertEqual(compare_events(first, second).level, 'POSSIBLE_MATCH')
        self.assertNotEqual(result[0].canonical_id, result[1].canonical_id)

    def test_missing_time_cannot_bridge_conflicting_sessions(self):
        events = [self.event(time='19:00'), self.event(time=None, source_priority=100), self.event(time='21:00')]
        for order in permutations(events):
            result = deduplicate_events(list(order))
            self.assertEqual(len(result), 2)
            for event in result:
                self.assertLessEqual(len({s['time'] for s in event.sources if s['time']}), 1)

    def test_missing_city_cannot_bridge_conflicting_cities(self):
        events = [self.event(municipality='Madrid'), self.event(municipality=None), self.event(municipality='Segovia')]
        for order in permutations(events):
            result = deduplicate_events(list(order))
            self.assertGreaterEqual(len(result), 2)
            for event in result:
                self.assertLessEqual(len({s['municipality'] for s in event.sources if s['municipality']}), 1)

    def test_title_normalization_preserves_originals(self):
        first = self.event(title='🎤 VETUSTA MORLA | SEGOVIA', time='9.00')
        second = self.event(title='Concierto de Vetusta Morla en Segovia', time='09:00')
        result = deduplicate_events([first, second])
        self.assertEqual(len(result), 1)
        self.assertEqual({s['title'] for s in result[0].sources}, {first.title, second.title})

    def test_same_artist_different_tributes_are_not_merged(self):
        first = self.event(title='Candlelight: Tributo a Hans Zimmer', artist='Cuarteto Ejemplo')
        second = replace(first, title='Candlelight: Tributo a Queen')
        self.assertNotEqual(compare_events(first, second).level, 'MATCH')

    def test_similar_festival_names_are_not_enough(self):
        self.assertEqual(len(deduplicate_events([self.event(), self.event(title='Vibra Mahou Sunset Fest')])), 2)

    def test_unknown_dates_and_venues_do_not_establish_identity(self):
        for change in [dict(date=None), dict(venue=None)]:
            first = self.event(**change)
            second = self.event(**change)
            self.assertEqual(compare_events(first, second).level, 'POSSIBLE_MATCH')
            result = deduplicate_events([first, second])
            self.assertEqual(len(result), 2)
            self.assertNotEqual(result[0].canonical_id, result[1].canonical_id)

    def test_country_aliases(self):
        self.assertEqual(len(deduplicate_events([self.event(country='ES'), self.event(country='Spain')])), 1)

    def test_tracking_parameters_do_not_remove_session_ids(self):
        self.assertEqual(canonical_url('https://example.com/event?session=1&utm_source=x'),
                         'https://example.com/event?session=1')
        first = self.event(url='https://example.com/event?session=1')
        act = self.event(title='Artista', artist='Artista', url='https://example.com/event?session=2')
        self.assertEqual(len(deduplicate_events([first, act])), 2)

    def test_provenance_of_complementary_fields(self):
        first = self.event(time=None, url='https://a.test/event', source_priority=100)
        second = self.event(time='13:00', url='https://b.test/event')
        result = deduplicate_events([first, second])[0]
        self.assertEqual(result.time, '13:00')
        self.assertEqual(result.field_sources['time'], ['https://b.test/event'])
        self.assertIsNone(first.time)


if __name__ == '__main__':
    unittest.main()
