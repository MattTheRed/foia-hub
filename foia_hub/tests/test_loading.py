from django.test import TestCase

from foia_hub.models import Agency
from foia_hub.scripts.load_agency_contacts import \
    add_reading_rooms, add_request_time_statistics


class LoadingTest(TestCase):
    fixtures = ['agencies_test.json']

    def test_add_reading_rooms(self):
        reading_room_links = [[
            'Electronic Reading Room', 'http://agency.gov/err/'],
            ['Pre-2000 Reading Room', 'http://agency.gov/pre-2000/rooms']]
        agency = Agency.objects.get(slug='department-of-homeland-security')
        agency = add_reading_rooms(agency, reading_room_links)
        agency.save()

        # Retrieve saved
        dhs = Agency.objects.get(slug='department-of-homeland-security')
        self.assertEqual(2, len(dhs.reading_room_urls.all()))
        self.assertEqual(
            'Electronic Reading Room',
            dhs.reading_room_urls.all()[0].link_text)
        self.assertEqual(
            'http://agency.gov/err/',
            dhs.reading_room_urls.all()[0].url)
        self.assertEqual(
            'Pre-2000 Reading Room',
            dhs.reading_room_urls.all()[1].link_text)
        self.assertEqual(
            'http://agency.gov/pre-2000/rooms',
            dhs.reading_room_urls.all()[1].url)

    def test_add_stats(self):
        """
        Confirms all latest records are loaded, no empty records
        are created, and records with a value of `less than one`
        are flagged.
        """
        # Load data
        agency = Agency.objects.get(slug='department-of-homeland-security')
        data = {'request_time_stats': {
            '2012': {'simple_median_days': '2'},
            '2014': {'simple_median_days': 'less than 1'}}}
        add_request_time_statistics(data, agency)

        # Verify latest data is returned when it exists
        retrieved = agency.stats_set.filter(
            stat_type='S').order_by('-year').first()
        self.assertEqual(retrieved.median, 1)

        # Verify that `less than one` records are flagged
        retrieved = agency.stats_set.filter(
            stat_type='S').order_by('-year').first()
        self.assertEqual(retrieved.less_than_one, True)

        # Verify that no empty records are created
        retrieved = agency.stats_set.filter(
            stat_type='C').order_by('-year').first()
        self.assertEqual(retrieved, None)
        with self.assertRaises(AttributeError) as error:
            retrieved.median
        self.assertEqual(type(error.exception), AttributeError)
