"Model definitions"

from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.core.urlresolvers import reverse
from urllib import urlencode
import re


class Region(models.Model):
    "The largest type of geographical area."
    id = models.CharField(max_length=2, primary_key=True)
    name = models.CharField(max_length=48)

    def __unicode__(self):
        return self.name

    def the(self):
        "The name for use in a sentence, with the definite article prepended if appropriate."
        if self.name[-1:] == 't' or self.name[-2:] == 'ds':
            return 'the ' + self.name
        else:
            return self.name

    def get_absolute_url(self):
        return reverse('region-detail', args=(self.id,))


class AdminArea(models.Model):
    """
    An administrative area within a region,
    or possibly a national transport (rail/air/ferry) network.
    """
    id = models.PositiveIntegerField(primary_key=True)
    atco_code = models.PositiveIntegerField()
    name = models.CharField(max_length=48)
    short_name = models.CharField(max_length=48)
    country = models.CharField(max_length=3)
    region = models.ForeignKey(Region)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('adminarea-detail', args=(self.id,))


class District(models.Model):
    """
    A district within an administrative area.

    Note: some administrative areas *do not* have districts.
    """
    id = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=48)
    admin_area = models.ForeignKey(AdminArea)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('district-detail', args=(self.id,))


class Locality(models.Model):
    """
    A locality within an administrative area, and possibly within a district.

    Localities may be children of other localities...
    """
    id = models.CharField(max_length=48, primary_key=True)
    name = models.CharField(max_length=48)
    # short_name? 
    qualifier_name = models.CharField(max_length=48, blank=True)
    admin_area = models.ForeignKey(AdminArea)
    district = models.ForeignKey(District, null=True)
    parent = models.ForeignKey('Locality', null=True, editable=False)
    location = models.PointField(srid=27700, null=True)

    def __unicode__(self):
        return self.name

    def get_qualified_name(self):
        "Name with a comma and the qualifier_name (e.g. 'York, York')"
        if self.qualifier_name:
            return "%s, %s" % (self.name, self.qualifier_name)
        return self.name

    def get_absolute_url(self):
        return reverse('locality-detail', args=(self.id,))


class StopArea(models.Model):
    "A small area containing multiple stops, such as a bus station."

    id = models.CharField(max_length=16, primary_key=True)
    name = models.CharField(max_length=48)
    admin_area = models.ForeignKey(AdminArea)

    TYPE_CHOICES = (
        ('GPBS', 'on-street pair'),
        ('GCLS', 'on-street cluster'),
        ('GAIR', 'airport building'),
        ('GBCS', 'bus/coach station'),
        ('GFTD', 'ferry terminal/dock'),
        ('GTMU', 'tram/metro station'),
        ('GRLS', 'rail station'),
        ('GCCH', 'coach service coverage'),
    )
    stop_area_type = models.CharField(max_length=4, choices=TYPE_CHOICES)

    parent = models.ForeignKey('StopArea', null=True, editable=False)
    location = models.PointField(srid=27700)
    active = models.BooleanField()

    def __unicode__(self):
        return self.name


class StopPoint(models.Model):
    "The smallest type of geographical point; a point at which vehicles stop."
    atco_code = models.CharField(max_length=16, primary_key=True)
    naptan_code = models.CharField(max_length=16)

    common_name = models.CharField(max_length=48)
    landmark = models.CharField(max_length=48)
    street = models.CharField(max_length=48)
    crossing = models.CharField(max_length=48)
    indicator = models.CharField(max_length=48)

    latlong = models.PointField()
    location = models.PointField(srid=27700, null=True)
    objects = models.GeoManager()

    stop_area = models.ForeignKey(StopArea, null=True, editable=False)
    locality = models.ForeignKey('Locality', editable=False)
    suburb = models.CharField(max_length=48)
    town = models.CharField(max_length=48)
    locality_centre = models.BooleanField()

    BEARING_CHOICES = (
        ('N', 'north'),
        ('NE', 'north east'),
        ('E', 'east'),
        ('SE', 'south east'),
        ('S', 'south'),
        ('SW', 'south west'),
        ('W', 'west'),
        ('NW', 'north west')
    )
    bearing = models.CharField(max_length=2, choices=BEARING_CHOICES)

    stop_type = models.CharField(max_length=3)
    bus_stop_type = models.CharField(max_length=3)
    timing_status = models.CharField(max_length=3)
    admin_area = models.ForeignKey('AdminArea')
    active = models.BooleanField()

    def __unicode__(self):
        if self.indicator:
            return "%s (%s)" % (self.common_name, self.indicator)
        return self.common_name

    def heading(self):
        "Return the stop's bearing converted to degrees, for use with Google Street View."
        headings = {
            'N':    0,
            'NE':  45,
            'E':   90,
            'SE': 135,
            'S':  180,
            'SW': 125,
            'W':  270,
            'NW': 315,
        }
        return headings.get(self.bearing)

    def get_absolute_url(self):
        return reverse('stoppoint-detail', args=(self.atco_code,))


class Operator(models.Model):
    "An entity that operates public transport services."

    id = models.CharField(max_length=10, primary_key=True) # e.g. 'YCST'
    name = models.CharField(max_length=100)
    vehicle_mode = models.CharField(max_length=48)
    parent = models.CharField(max_length=48)
    region = models.ForeignKey(Region)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('operator-detail', args=(self.id,))

    def get_a_mode(self):
        """
        Return the the name of the operator's vehicle mode, with the correct indefinite article
        depending on whether it begins with a vowel sound.

        'Airline' becomes 'An airline', 'Bus' becomes 'A bus'.

        Doesn't support mode names that begin with other vowels.
        """
        mode = str(self.vehicle_mode).lower()
        if mode:
            if mode[0] == 'a':
                return 'An ' + mode
            return 'A ' + mode
        return 'An' # 'An operator'


class Service(models.Model):
    "A bus service."
    service_code = models.CharField(max_length=24, primary_key=True)
    line_name = models.CharField(max_length=24)
    description = models.CharField(max_length=100)
    mode = models.CharField(max_length=10)
    operator = models.ManyToManyField(Operator)
    net = models.CharField(max_length=3, blank=True)
    stops = models.ManyToManyField(StopPoint, editable=False)

    def __unicode__(self):
        if self.line_name and self.description:
            return '%s - %s' % (self.line_name, self.description)
        else:
            return self.service_code

    def has_long_line_name(self):
        "Is this service's line_name more than 4 characters long?"
        return len(self.line_name) > 4

    def get_a_mode(self):
        if not self.mode:
            return 'A'
        elif self.mode[0] == 'a':
            return 'An %s' % self.mode
        else:
            return 'A %s' % self.mode

    def get_absolute_url(self):
        return reverse('service-detail', args=(self.service_code,))

    def get_traveline_url(self):
        if self.net != '':
            regex = re.compile(r'([0-9]+)-([0-9A-z]+)-([A-Z_])-([a-z0-9]+)-([0-9])')
            matches = regex.match(self.service_code)

            if matches is not None:
                query = [('line', matches.group(1).zfill(2) + matches.group(2).zfill(3)),
                     ('lineVer', matches.group(5)),
                     ('net', self.net),
                     ('project', matches.group(4)),
                     ('outputFormat', '0'),
                     ('command', 'direct'),
                     ('itdLPxx_displayHeader', 'false')]

                if matches.group(3) != '_':
                    query.append(('sup', matches.group(3)))

                base_url = 'http://www.travelinesoutheast.org.uk/se'

                return '%s/XSLT_TTB_REQUEST?%s' % (base_url, urlencode(query))


class ServiceVersion(models.Model):
    """
    A "version" of a service, usually represented as a separate file in a region's TNDS zip archive.

    There are usually at least two versions of a service, one per direction of travel.
    Further "versions" exist when services are revised.
    """
    name = models.CharField(max_length=24, primary_key=True) # e.g. 'YEABCL1-2015-04-10-1'
    description = models.CharField(max_length=100)
    service = models.ForeignKey(Service, editable=False)
    start_date = models.DateField()
    end_date = models.DateField(null=True)

    def __unicode__(self):
        return self.description

