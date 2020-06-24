from google.transit import gtfs_realtime_pb2
from datetime import datetime
from django.contrib.gis.geos import Point
from django.conf import settings
from django.utils import timezone
from busstops.models import Service
from ...models import Vehicle, VehicleLocation, VehicleJourney
from ..import_live_vehicles import ImportLiveVehiclesCommand


class Command(ImportLiveVehiclesCommand):
    source_name = 'TfWM'
    url = 'http://api.tfwm.org.uk/gtfs/vehicle_positions'
    routes = {}
    routes_by_operator = {
        'Select Bus Services': set(),
        'LandFlight': set(),
        'Kevs Cars and Coaches': set(),
        'Walsall Community Transport': set(),
        'Johnson\'s Excelbus': set(),
        'Evergreen Coaches Ltd': set(),
    }

    @staticmethod
    def get_datetime(item):
        return timezone.make_aware(datetime.fromtimestamp(item.vehicle.timestamp))

    def get_items(self):
        if not self.routes:
            response = self.session.get('http://api.tfwm.org.uk/line/route', params={**settings.TFWM,
                                                                                     'formatter': 'json'}, timeout=10)
            for route in response.json()['ArrayOfLine']['Line']:
                self.routes[route['Id']] = route
                operator = route['Operators']['Operator'][0]['Name']
                if operator in self.routes_by_operator:
                    self.routes_by_operator[operator].add(route['Name'])

        response = self.session.get(self.url, params=settings.TFWM, timeout=10)
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)
        return feed.entity

    def get_vehicle(self, item):
        vehicle_code = item.vehicle.vehicle.id

        defaults = {
            'source': self.source
        }

        if item.vehicle.HasField('trip'):
            route = self.routes.get(item.vehicle.trip.route_id)
            if route:
                operator = route['Operators']['Operator'][0]['Name']
                if operator == 'Midland Classic' or operator == 'Diamond Bus':
                    return None, None

                vehicle_code = vehicle_code[:-len(route['Name'])]
                if operator == 'Select Bus Services':
                    operator = 'SLBS'
                elif operator == 'First Worcestershire':
                    operator = 'FSMR'
                elif operator == 'LandFlight':
                    operator = 'SLVL'
                elif operator == 'Kevs Cars and Coaches':
                    operator = 'KEVS'
                elif operator == 'Walsall Community Transport':
                    operator = 'WACT'
                else:
                    print(item, vehicle_code, operator)
                    return None, None

                if vehicle_code.isdigit():
                    defaults['fleet_number'] = vehicle_code

                return self.vehicles.get_or_create(defaults, operator_id=operator, code=vehicle_code)

        if len(vehicle_code) > 5 and vehicle_code[:5].isdigit():
            vehicle_code = vehicle_code[:5]
            defaults['fleet_number'] = vehicle_code
            try:
                vehicle, created = self.vehicles.get_or_create(defaults, operator__in=['DIAM', 'FSMR'],
                                                               code=vehicle_code)
                if not vehicle.operator_id:
                    print(item)
                if vehicle.operator_id == 'DIAM':
                    return None, None
                return vehicle, created
            except Vehicle.MultipleObjectsReturned as e:
                print(e)

        elif vehicle_code.startswith('BUS_'):
            for line_name in self.routes_by_operator['Select Bus Services']:
                if vehicle_code.endswith(line_name) and not vehicle_code.endswith('_' + line_name):
                    vehicle_code = vehicle_code[:-len(line_name)]
                    defaults['fleet_number'] = vehicle_code.split('_')[-1]
                    return self.vehicles.get_or_create(defaults, operator_id='SLBS', code=vehicle_code)

        else:
            reg = vehicle_code.replace('_', '')
            if len(reg) > 7:
                route = reg[7:]
                reg = reg[:7]
                defaults['reg'] = reg
                vehicle_code = vehicle_code[:-len(route)]

                for line_name in self.routes_by_operator['LandFlight']:
                    if route.lower() == line_name.lower():
                        return self.vehicles.get_or_create(defaults, operator_id='SLVL', code=vehicle_code)
                for line_name in self.routes_by_operator['Johnson\'s Excelbus']:
                    if route.lower() == line_name.lower():
                        return self.vehicles.get_or_create(defaults, operator_id='JOHS', code=vehicle_code)
                try:
                    return self.vehicles.get_or_create(defaults, code=vehicle_code)
                except Vehicle.MultipleObjectsReturned:
                    pass
        return None, None
        print(vehicle_code, item)


    def get_journey(self, item, vehicle):
        journey = VehicleJourney()

        if item.vehicle.HasField('trip'):
            if vehicle.latest_location and vehicle.latest_location.journey.code == item.vehicle.trip.trip_id:
                return vehicle.latest_location.journey

            journey.code = item.vehicle.trip.trip_id
            journey.datetime = timezone.make_aware(
                datetime.strptime(item.vehicle.trip.start_date + item.vehicle.trip.start_time, '%Y%m%d%H:%M:%S')
            )

        vehicle_code = item.vehicle.vehicle.id
        if vehicle_code.startswith(vehicle.code) and len(vehicle.code) < len(vehicle_code):
            journey.route_name = vehicle_code[len(vehicle.code):]

        if item.vehicle.HasField('trip'):
            route = self.routes.get(item.vehicle.trip.route_id)
            if route:
                journey.route_name = route['Name']

        if vehicle.operator_id:
            try:
                journey.service = Service.objects.get(current=True, line_name__iexact=journey.route_name,
                                                      operator=vehicle.operator_id)
            except (Service.MultipleObjectsReturned, Service.DoesNotExist) as e:
                print(e, vehicle.operator_id, vehicle, journey.route_name)

        return journey

    def create_vehicle_location(self, item):
        return VehicleLocation(
            latlong=Point(item.vehicle.position.longitude, item.vehicle.position.latitude)
        )
