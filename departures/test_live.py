# coding=utf-8
"""Tests for live departures
"""
import vcr
from datetime import time, datetime
from unittest.mock import patch
from django.test import TestCase
from django.shortcuts import render
from freezegun import freeze_time
from busstops.models import StopPoint, Service, Region, Operator, StopUsage, AdminArea, DataSource, SIRISource
from bustimes.models import Route, Trip, Calendar, StopTime
from vehicles.models import VehicleJourney
from . import live


class LiveDeparturesTest(TestCase):
    """Tests for live departures
    """
    @classmethod
    def setUpTestData(cls):
        cls.region = Region.objects.create(id='W', name='Wales')

        cls.london_stop = StopPoint.objects.create(
            pk='490014721F',
            common_name='Wilmot Street',
            locality_centre=False,
            active=True
        )
        cls.london_service = Service.objects.create(service_code='tfl_60-8-_-y05', line_name='8',
                                                    region_id='W', date='2017-01-01')
        StopUsage.objects.create(stop=cls.london_stop, service=cls.london_service, order=1)

        cls.cardiff_stop = StopPoint.objects.create(
            pk='5710WDB48471',
            common_name='Wood Street',
            locality_centre=False,
            active=True
        )

        cls.yorkshire_stop = StopPoint.objects.create(
            pk='3290YYA00215',
            naptan_code='32900215',
            common_name='Victoria Bar',
            locality_centre=False,
            active=True
        )

        admin_area = AdminArea.objects.create(
            pk=109,
            atco_code=200,
            name='Worcestershire',
            region=cls.region
        )
        siri_source = SIRISource.objects.create(
            name='SPT',
            url='http://worcestershire-rt-http.trapezenovus.co.uk:8080',
            requestor_ref='Traveline_To_Trapeze',
        )
        source = DataSource.objects.create()
        siri_source.admin_areas.add(admin_area)
        cls.worcester_stop = StopPoint.objects.create(
            pk='2000G000106',
            common_name='Crowngate Bus Station',
            locality_centre=False,
            active=True,
            admin_area=admin_area
        )
        worcester_44 = Service.objects.create(service_code='44', line_name='44', region_id='W', date='2017-01-01')
        worcester_44.operator.add(Operator.objects.create(id='FMR', name='First Midland Red', region_id='W'))
        StopUsage.objects.create(stop=cls.worcester_stop, service=worcester_44, order=0)

        cls.stagecoach_stop = StopPoint.objects.create(atco_code='64801092', active=True,
                                                       locality_centre=False)
        stagecoach_operator = Operator.objects.create(id='SCOX',
                                                      name='Stagecoach Oxenholme',
                                                      region_id='W')
        cls.stagecoach_service = Service.objects.create(service_code='15', line_name='15',
                                                        region_id='W', date='2017-01-01')
        cls.stagecoach_service.operator.add(stagecoach_operator)
        StopUsage.objects.create(stop=cls.stagecoach_stop, service=cls.stagecoach_service, order=1)

        translink_metro_operator = Operator.objects.create(id='MET', name='Translink Metro', region_id='W')
        cls.translink_metro_stop = StopPoint.objects.create(atco_code='700000001415', active=True,
                                                            locality_centre=False)
        translink_metro_service = Service.objects.create(service_code='2D_MET', line_name='2D', region_id='W',
                                                         date='2017-01-01')
        translink_metro_service.operator.add(translink_metro_operator)
        StopUsage.objects.create(stop=cls.translink_metro_stop, service=translink_metro_service, order=0)

        calendar_1 = Calendar.objects.create(mon=False, tue=True, wed=False, thu=False, fri=False, sat=False, sun=False,
                                             start_date='2017-03-14', end_date='2017-03-14')
        calendar_2 = Calendar.objects.create(mon=False, tue=True, wed=False, thu=False, fri=False, sat=False, sun=False,
                                             start_date='2017-03-28', end_date='2017-03-28')
        route = Route.objects.create(service=cls.stagecoach_service, start_date='2017-03-04', source=source)
        trip_1 = Trip.objects.create(calendar=calendar_1, route=route, destination=cls.cardiff_stop,
                                     start='0', end='21:23:00')
        trip_2 = Trip.objects.create(calendar=calendar_2, route=route, destination=cls.cardiff_stop,
                                     start='0', end='20:00:00')
        StopTime.objects.bulk_create(
            StopTime(trip=trip, sequence=0, arrival=when, departure=when, stop_id='64801092')
            for trip, when in (
                (trip_1, '20:23:00'),
                (trip_1, '21:23:00'),
                (trip_2, '18:53:00')
            )
        )

        calendar = Calendar.objects.create(mon=True, tue=True, wed=True, thu=True, fri=True, sat=True, sun=True,
                                           start_date='2019-02-09', end_date='2019-02-09')
        worcester_route = Route.objects.create(service=worcester_44, start_date='2017-03-04', source=source, code='44')
        trip = Trip.objects.create(calendar=calendar, route=worcester_route, destination=cls.worcester_stop,
                                   start='0', end='11:00:00')
        StopTime.objects.create(trip=trip, sequence=0, arrival='10:54:00', departure='10:54:00',
                                stop_id=cls.worcester_stop.pk)
        StopUsage.objects.create(stop_id=cls.worcester_stop.pk, service=worcester_44, order=1)

    def test_abstract(self):
        departures = live.Departures(None, ())
        self.assertIsNone(departures.get_request_url())
        self.assertRaises(NotImplementedError, departures.departures_from_response, None)

    def test_tfl(self):
        """Test the Transport for London live departures source
        """
        with vcr.use_cassette('data/vcr/tfl_arrivals.yaml'):
            row = live.TflDepartures(
                self.london_stop,
                [self.london_service]
            ).get_departures()[0]
        self.assertEqual('Bow Church', row['destination'])
        self.assertEqual(self.london_service, row['service'])
        self.assertEqual(2016, row['live'].date().year)
        self.assertEqual(7, row['live'].date().month)
        self.assertEqual(26, row['live'].date().day)

        with vcr.use_cassette('data/vcr/tfl_arrivals.yaml'):
            response = self.client.get('/stops/' + self.london_stop.pk)

        self.assertContains(response, """
            <div class="aside">
                <h2>Next departures</h2>
                <table><tbody>
                    <tr><td><a href="/services/8">8</a></td><td>Bow Church</td><td>18:22⚡</td></tr>
                    <tr><td>D3</td><td>Bethnal Green, Chest Hospital</td><td>18:23⚡</td></tr>
                    <tr><td><a href="/services/8">8</a></td><td>Bow Church</td><td>18:26⚡</td></tr>
                    <tr><td>388</td><td>Stratford City</td><td>18:26⚡</td></tr>
                    <tr><td><a href="/services/8">8</a></td><td>Bow Church</td><td>18:33⚡</td></tr>
                    <tr><td>D3</td><td>Bethnal Green, Chest Hospital</td><td>18:33⚡</td></tr>
                    <tr><td><a href="/services/8">8</a></td><td>Bow Church</td><td>18:37⚡</td></tr>
                    <tr><td>388</td><td>Stratford City</td><td>18:44⚡</td></tr>
                    <tr><td>D3</td><td>Bethnal Green, Chest Hospital</td><td>18:44⚡</td></tr>
                    <tr><td><a href="/services/8">8</a></td><td>Bow Church</td><td>18:44⚡</td></tr>
                    <tr><td><a href="/services/8">8</a></td><td>Bow Church</td><td>18:49⚡</td></tr>
                </tbody></table>
                <p class="credit">⚡ denotes ‘live’ times guessed (sometimes badly) from buses’ actual locations </p>
            </div>
        """, html=True)

    @freeze_time('27 October 2018')
    def test_translink_metro(self):
        with vcr.use_cassette('data/vcr/translink_metro.yaml'):
            res = self.client.get(self.translink_metro_stop.get_absolute_url())
        self.assertNotContains(res, '<h3>')
        self.assertContains(res, '<tr><td>14B</td><td>City Express</td><td>08:22</td></tr>', html=True)
        self.assertContains(res, '<tr><td>1A</td><td>City Centre</td><td>07:54⚡</td></tr>', html=True)

    def test_translink_metro_no_services_running(self):
        with vcr.use_cassette('data/vcr/translink_metro.yaml', match_on=['body']):
            departures = live.AcisHorizonDepartures(StopPoint(pk='700000000748'), ())
            self.assertEqual([], departures.get_departures())

    @freeze_time('14 Mar 2017 20:00')
    def test_stagecoach(self):
        with vcr.use_cassette('data/vcr/stagecoach.yaml'):
            with self.assertNumQueries(9):
                res = self.client.get('/stops/64801092')
        self.assertContains(res, '<td><a href=/services/15>15</a></td>', html=True)
        self.assertContains(res, '<td>Hillend</td>')
        self.assertEqual(3, len(res.context_data['departures']))
        self.assertEqual(res.context_data['departures'][0]['service'], self.stagecoach_service)
        self.assertEqual(res.context_data['departures'][0]['live'].time(), time(20, 37, 51))
        self.assertEqual(res.context_data['departures'][1]['service'], self.stagecoach_service)
        self.assertEqual(res.context_data['departures'][1]['live'].time(), time(21, 38, 21))
        self.assertEqual(res.context_data['departures'][2]['service'], '7')
        self.assertEqual(res.context_data['departures'][2]['live'].time(), time(21, 17, 28))

    @freeze_time('28 Mar 2017 17:00')
    def test_stagecoach_timezone(self):
        with vcr.use_cassette('data/vcr/stagecoach_timezone.yaml'):
            with self.assertNumQueries(9):
                res = self.client.get('/stops/64801092')
        self.assertEqual(6, len(res.context_data['departures']))
        self.assertEqual(res.context_data['departures'][0]['destination'].common_name, 'Wood Street')
        self.assertEqual(res.context_data['departures'][1]['destination'], 'Hillend')
        self.assertEqual(res.context_data['departures'][2]['destination'], 'Hillend')

        self.assertEqual(res.context_data['departures'][1]['service'], '7')
        self.assertEqual(res.context_data['departures'][0]['service'].line_name, '15')
        self.assertEqual(res.context_data['departures'][0]['service'].line_name, '15')
        self.assertEqual(str(res.context_data['departures'][0]['time']), '2017-03-28 18:53:00+01:00')
        self.assertEqual(str(res.context_data['departures'][2]['time']), '2017-03-28 19:08:00+01:00')
        self.assertEqual(str(res.context_data['departures'][2]['live']), '2017-03-28 19:08:25+01:00')

    def test_blend(self):
        service = Service(line_name='X98')
        a = [{
            'service': 'X98',
            'time': datetime(2017, 4, 21, 20, 10),
            'live': datetime(2017, 4, 21, 20, 2)
        }]
        b = [{
            'service': service,
            'time': datetime(2017, 4, 21, 20, 10),
            'live': datetime(2017, 4, 21, 20, 5)
        }]

        live.blend(a, b)
        self.assertEqual(a, [{
            'service': 'X98',
            'time': datetime(2017, 4, 21, 20, 10),
            'live': datetime(2017, 4, 21, 20, 5)
        }])

        live.blend(b, a)
        self.assertEqual(b, [{
            'service': service,
            'time': datetime(2017, 4, 21, 20, 10),
            'live': datetime(2017, 4, 21, 20, 5)
        }])

    def test_render(self):
        response = render(None, 'departures.html', {
            'departures': [
                {
                    'time': datetime(1994, 5, 4, 11, 53),
                    'service': 'X98',
                    'destination': 'Bratislava'
                },
                {
                    'time': datetime(1994, 5, 7, 11, 53),
                    'service': '9',
                    'destination': 'Shilbottle'
                }
            ]
        })
        self.assertContains(response, """
            <div class="aside">
                <h2>Next departures</h2>
                <h3>Wednesday</h3>
                <table><tbody>
                    <tr><td>X98</td><td>Bratislava</td><td>11:53</td></tr>
                </tbody></table>
                <h3>Saturday</h3>
                <table><tbody>
                    <tr><td>9</td><td>Shilbottle</td><td>11:53</td></tr>
                </tbody></table>
            </div>
        """, html=True)

    @patch('vehicles.tasks.log_vehicle_journey.delay')
    def test_worcestershire(self, log_vehicle_journey):
        with freeze_time('Sat Feb 09 10:45:45 GMT 2019'):
            with vcr.use_cassette('data/vcr/worcester.yaml'):
                with self.assertNumQueries(10):
                    response = self.client.get(self.worcester_stop.get_absolute_url())
            with vcr.use_cassette('data/vcr/worcester.yaml'):
                with self.assertNumQueries(3):
                    xml_response = self.client.get(self.worcester_stop.get_absolute_url() + '.xml')
        self.assertContains(response, """
            <tr>
                <td>
                    <a href=/services/44>44</a>
                </td>
                <td>Crowngate Bus Station</td>
                <td>10:54</td>
            </tr>
        """, html=True)
        self.assertContains(response, 'EVESHAM Bus Station')
        self.assertNotContains(response, 'WORCESTER')

        log_vehicle_journey.assert_called_with(
            None,
            {
                'LineRef': 'X50',
                'DirectionRef': 'O',
                'FramedVehicleJourneyRef': {
                    'DataFrameRef': '2019_02_09_311_4560_220',
                    'DatedVehicleJourneyRef': '311_4560_220',
                },
                'OperatorRef': 'FMR',
                'OriginRef': '2000G000106',
                'OriginName': 'Crowngate Bus Station',
                'DestinationRef': '2000G000400',
                'DestinationName': 'EVESHAM Bus Station',
                'OriginAimedDepartureTime': '2019-02-09T12:10:00Z',
                'Monitored': 'true',
                'Delay': 'PT0M0S',
                'VehicleRef': 'FMR-66692',
                'MonitoredCall': {
                    'AimedDepartureTime': '2019-02-09T12:10:00Z',
                    'ExpectedDepartureTime': '2019-02-09T12:10:00Z',
                    'DepartureStatus': 'onTime',
                },
            },
            None, 'EVESHAM Bus Station', 'SPT', 'http://worcestershire-rt-http.trapezenovus.co.uk:8080'
        )
        self.assertEqual(0, VehicleJourney.objects.count())

        self.assertEqual(xml_response['Content-Type'], 'text/xml')
