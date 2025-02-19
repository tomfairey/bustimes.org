from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.db.models import Count, Q
from django.db.utils import ConnectionDoesNotExist
from django.contrib.auth import get_user_model
from busstops.models import Operator
from .models import (VehicleType, VehicleFeature, Vehicle, VehicleEdit, VehicleLocation,
                     VehicleJourney, Livery, JourneyCode, VehicleRevision)

UserModel = get_user_model()


@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name', 'double_decker', 'coach')
    list_editable = list_display[1:]


class VehicleAdminForm(forms.ModelForm):
    class Meta:
        widgets = {
            'fleet_number': forms.TextInput(attrs={'style': 'width: 4em'}),
            'fleet_code': forms.TextInput(attrs={'style': 'width: 4em'}),
            'reg': forms.TextInput(attrs={'style': 'width: 8em'}),
            'operator': forms.TextInput(attrs={'style': 'width: 4em'}),
            'branding': forms.TextInput(attrs={'style': 'width: 8em'}),
            'name': forms.TextInput(attrs={'style': 'width: 8em'}),
        }


def user(obj):
    if obj.user_id:
        return mark_safe(f'<a href="?user={obj.user_id}">{obj.user_id}</a>')


class VehicleEditInline(admin.TabularInline):
    model = VehicleEdit
    fields = ['approved', 'datetime', 'fleet_number', 'reg', 'vehicle_type', 'livery_id', 'colours', 'branding',
              'notes', 'changes', 'user']
    readonly_fields = fields[1:]
    show_change_link = True


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('code', 'fleet_number', 'fleet_code', 'reg', 'operator', 'vehicle_type',
                    'get_flickr_link', 'last_seen', 'livery', 'colours', 'branding', 'name', 'notes', 'data')
    list_filter = (
        'withdrawn',
        ('source', admin.RelatedOnlyFieldListFilter),
        ('operator', admin.RelatedOnlyFieldListFilter),
    )
    list_select_related = ['operator', 'livery', 'vehicle_type', 'latest_location']
    list_editable = ('fleet_number', 'fleet_code', 'reg', 'operator',
                     'branding', 'name', 'notes')
    autocomplete_fields = ('vehicle_type', 'livery')
    raw_id_fields = ('operator', 'source')
    search_fields = ('code', 'fleet_code', 'reg')
    ordering = ('-id',)
    actions = ('copy_livery', 'copy_type', 'make_livery')
    inlines = [VehicleEditInline]

    def copy_livery(self, request, queryset):
        livery = Livery.objects.filter(vehicle__in=queryset).first()
        count = queryset.update(livery=livery)
        self.message_user(request, f'Copied {livery} to {count} vehicles.')

    def copy_type(self, request, queryset):
        vehicle_type = VehicleType.objects.filter(vehicle__in=queryset).first()
        count = queryset.update(vehicle_type=vehicle_type)
        self.message_user(request, f'Copied {vehicle_type} to {count} vehicles.')

    def make_livery(self, request, queryset):
        vehicle = queryset.first()
        if vehicle.colours and vehicle.branding:
            livery = Livery.objects.create(name=vehicle.branding, colours=vehicle.colours)
            vehicles = Vehicle.objects.filter(colours=vehicle.colours, branding=vehicle.branding)
            count = vehicles.update(colours='', branding='', livery=livery)
            self.message_user(request, f'Updated {count} vehicles.')
        else:
            self.message_user(request, 'Select a vehicle with colours and branding.')

    def last_seen(self, obj):
        if obj.latest_location:
            return obj.latest_location.datetime
    last_seen.admin_order_field = 'latest_location__datetime'

    def get_changelist_form(self, request, **kwargs):
        kwargs.setdefault('form', VehicleAdminForm)
        return super().get_changelist_form(request, **kwargs)


def vehicle(obj):
    url = reverse('admin:vehicles_vehicle_change', args=(obj.vehicle_id,))
    return mark_safe(f'<a href="{url}">{obj.vehicle}</a>')


def fleet_number(obj):
    return obj.get_diff('fleet_number')


fleet_number.short_description = 'no'


def reg(obj):
    return obj.get_diff('reg')


def vehicle_type(obj):
    return obj.get_diff('vehicle_type')


vehicle_type.short_description = 'type'


def branding(obj):
    return obj.get_diff('branding')


branding.short_description = 'brand'


def name(obj):
    return obj.get_diff('name')


def notes(obj):
    return obj.get_diff('notes')


def features(edit):
    features = []
    vehicle = edit.vehicle
    changed_features = edit.vehicleeditfeature_set.all()
    for feature in changed_features:
        if feature.add:
            if feature.feature in vehicle.features.all():
                features.append(str(feature.feature))  # vehicle already has feature
            else:
                features.append(str(feature))
        elif feature.feature in vehicle.features.all():
            features.append(str(feature))
    for feature in vehicle.features.all():
        if not any(feature.id == edit_feature.feature_id for edit_feature in changed_features):
            features.append(str(feature))

    return mark_safe(', '.join(features))


def changes(obj):
    changes = []
    if obj.changes:
        for key, value in obj.changes.items():
            if not obj.vehicle.data or key not in obj.vehicle.data:
                changes.append(f'{key}: <ins>{value}</ins>')
            elif value != obj.vehicle.data[key]:
                changes.append(f'{key}: <del>{obj.vehicle.data[key]}</del> <ins>{value}</ins>')
    if obj.vehicle.data:
        for key, value in obj.vehicle.data.items():
            if not obj.changes or key not in obj.changes:
                changes.append(f'{key}: {value}')
    return mark_safe('<br>'.join(changes))


def url(obj):
    if obj.url:
        return mark_safe(f'<a href="{obj.url}" target="_blank" rel="noopener">{obj.url}</a>')


vehicle.admin_order_field = 'vehicle'
reg.admin_order_field = 'reg'
vehicle_type.admin_order_field = 'vehicle_type'
branding.admin_order_field = 'branding'
name.admin_order_field = 'name'
notes.admin_order_field = 'notes'
changes.admin_order_field = 'changes'


def apply_edits(queryset):
    for edit in queryset.prefetch_related('vehicleeditfeature_set__feature', 'vehicle__features'):
        ok = True
        vehicle = edit.vehicle
        update_fields = []
        if edit.withdrawn is not None:
            vehicle.withdrawn = edit.withdrawn
            update_fields.append('withdrawn')
        if edit.fleet_number:
            if edit.fleet_number.startswith('-'):
                if edit.fleet_number == f'-{vehicle.fleet_code or vehicle.fleet_number}':
                    vehicle.fleet_code = ''
                    vehicle.fleet_number = None
            else:
                vehicle.fleet_code = edit.fleet_number
                if edit.fleet_number.isdigit():
                    vehicle.fleet_number = edit.fleet_number
                else:
                    vehicle.fleet_number = None
            update_fields.append('fleet_code')
            update_fields.append('fleet_number')
        if edit.changes:
            if vehicle.data:
                vehicle.data = {
                    **vehicle.data, **edit.changes
                }
                for field in edit.changes:
                    if not edit.changes[field]:
                        del vehicle.data[field]
            else:
                vehicle.data = edit.changes
            update_fields.append('data')
        for field in ('branding', 'name', 'notes', 'reg'):
            new_value = getattr(edit, field)
            if new_value:
                if new_value.startswith('-'):
                    if new_value == f'-{getattr(vehicle, field)}':
                        setattr(vehicle, field, '')
                    else:
                        continue
                else:
                    setattr(vehicle, field, new_value)
                update_fields.append(field)
        if edit.vehicle_type:
            try:
                vehicle.vehicle_type = VehicleType.objects.get(name__iexact=edit.vehicle_type)
                update_fields.append('vehicle_type')
            except VehicleType.DoesNotExist:
                ok = False
        if edit.livery_id:
            vehicle.livery_id = edit.livery_id
            vehicle.colours = ''
            update_fields.append('livery')
            update_fields.append('colours')
        elif edit.colours and edit.colours != 'Other':
            vehicle.livery = None
            vehicle.colours = edit.colours
            update_fields.append('livery')
            update_fields.append('colours')
        vehicle.save(update_fields=update_fields)
        for feature in edit.vehicleeditfeature_set.all():
            if feature.add:
                vehicle.features.add(feature.feature)
            else:
                vehicle.features.remove(feature.feature)
        if ok:
            edit.approved = True
            edit.save(update_fields=['approved'])


class OperatorFilter(admin.SimpleListFilter):
    title = 'operator'
    parameter_name = 'operator'

    def lookups(self, request, model_admin):
        operators = Operator.objects.filter(vehicle__vehicleedit__isnull=False,
                                            vehicle__vehicleedit__approved=None)
        operators = operators.annotate(count=Count('vehicle__vehicleedit')).order_by('-count')
        try:
            operators = list(operators.using('read-only-0'))
        except ConnectionDoesNotExist:
            pass
        for operator in operators:
            yield (operator.pk, f'{operator} ({operator.count})')

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(vehicle__operator=self.value())
        return queryset


class ChangeFilter(admin.SimpleListFilter):
    title = 'changed field'
    parameter_name = 'change'

    def lookups(self, request, model_admin):
        return (
            ('fleet_number', 'fleet number'),
            ('reg', 'reg'),
            ('vehicle_type', 'type'),
            ('colours', 'colours'),
            ('branding', 'branding'),
            ('name', 'name'),
            ('notes', 'notes'),
            ('withdrawn', 'withdrawn'),
            ('USB charging', 'USB charging'),
            ('open top', 'open top'),
            ('bike storage', 'bike storage'),
            ('changes__Depot', 'depot'),
            ('changes__Previous reg', 'previous reg'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            if value == 'colours':
                return queryset.filter(~Q(colours='') | Q(livery__isnull=False))
            if value in {'USB charging', 'open top', 'bike storage'}:
                return queryset.filter(vehicleeditfeature__feature__name=value)
            if value.startswith('changes__'):
                return queryset.filter(**{f'{value}__isnull': False})
            return queryset.filter(~Q(**{value: ''}))
        return queryset


class UrlFilter(admin.SimpleListFilter):
    title = 'URL'
    parameter_name = 'url'

    def lookups(self, request, model_admin):
        return (
            ('1', 'Yes'),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.exclude(url='')
        return queryset


class UserFilter(admin.SimpleListFilter):
    title = 'user'
    parameter_name = 'user'

    def lookups(self, request, model_admin):
        users = UserModel.objects
        model = model_admin.model.__name__.lower()
        count = Count(model)
        if model == 'vehicleedit':
            count.filter = Q(**{f'{model}__approved': None})
        users = users.annotate(count=count).filter(count__gt=0).order_by('-count')
        for user in users:
            yield (user.id, f"{user} ({user.count})")

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(user=self.value())
        return queryset


@admin.register(VehicleEdit)
class VehicleEditAdmin(admin.ModelAdmin):
    list_display = ['datetime', vehicle, 'edit_count', 'last_seen', fleet_number, reg, vehicle_type, branding, name,
                    'current', 'suggested', notes, 'withdrawn', features, changes, 'flickr', user, url]
    list_select_related = ['vehicle__vehicle_type', 'vehicle__livery', 'vehicle__operator', 'vehicle__latest_location',
                           'livery']
    list_filter = [
        'approved',
        UrlFilter,
        'withdrawn',
        'vehicle__withdrawn',
        ChangeFilter,
        OperatorFilter,
        UserFilter,
    ]
    raw_id_fields = ['vehicle', 'livery']
    actions = ['apply_edits', 'approve', 'disapprove', 'delete_vehicles']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if 'changelist' in request.resolver_match.view_name:
            edit_count = Count('vehicle__vehicleedit', filter=Q(vehicle__vehicleedit__approved=None))
            queryset = queryset.annotate(edit_count=edit_count)
            return queryset.prefetch_related('vehicleeditfeature_set__feature', 'vehicle__features')
        return queryset

    def apply_edits(self, request, queryset):
        apply_edits(queryset)
        self.message_user(request, 'Applied edits.')

    def approve(self, request, queryset):
        count = queryset.order_by().update(approved=True)
        self.message_user(request, f'Approved {count} edits.')

    def disapprove(self, request, queryset):
        count = queryset.order_by().update(approved=False)
        self.message_user(request, f'Disapproved {count} edits.')

    def delete_vehicles(self, request, queryset):
        Vehicle.objects.filter(vehicleedit__in=queryset).delete()

    def current(self, obj):
        if obj.vehicle.livery:
            return obj.vehicle.livery.preview()
        if obj.vehicle.colours:
            return Livery(colours=obj.vehicle.colours).preview()
    current.admin_order_field = 'vehicle__livery'

    def suggested(self, obj):
        if obj.livery:
            return obj.livery.preview()
        if obj.colours:
            if obj.colours == 'Other':
                return obj.colours
            return Livery(colours=obj.colours).preview()
    suggested.admin_order_field = 'livery'

    def flickr(self, obj):
        return obj.vehicle.get_flickr_link()

    def edit_count(self, obj):
        return obj.edit_count
    edit_count.admin_order_field = 'edit_count'
    edit_count.short_description = 'edits'

    def last_seen(self, obj):
        if obj.vehicle.latest_location:
            return obj.vehicle.latest_location.datetime
    last_seen.admin_order_field = 'vehicle__latest_location__datetime'
    last_seen.short_description = 'seen'


class ServiceIsNullFilter(admin.SimpleListFilter):
    title = 'service is null'
    parameter_name = 'service__isnull'

    def lookups(self, request, model_admin):
        return (
            ('1', 'Yes'),
            ('0', 'No'),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(**{self.parameter_name: self.value() == '1'})
        return queryset


class TripIsNullFilter(ServiceIsNullFilter):
    title = 'trip is null'
    parameter_name = 'trip__isnull'


@admin.register(VehicleJourney)
class VehicleJourneyAdmin(admin.ModelAdmin):
    list_display = ('datetime', 'code', 'vehicle', 'route_name', 'service', 'destination')
    list_select_related = ('vehicle', 'service')
    raw_id_fields = ('vehicle', 'service', 'source', 'trip')
    list_filter = (
        ServiceIsNullFilter,
        TripIsNullFilter,
        'source',
        'vehicle__operator',
    )
    show_full_result_count = False
    ordering = ('-id',)


@admin.register(VehicleLocation)
class VehicleLocationAdmin(admin.ModelAdmin):
    raw_id_fields = ['journey']
    list_display = ['__str__', 'get_delay']
    list_select_related = ['journey']
    list_filter = ['occupancy']


@admin.register(JourneyCode)
class JourneyCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'service', 'destination']
    list_select_related = ['service']
    list_filter = [
        ('data_source', admin.RelatedOnlyFieldListFilter),
        ('siri_source', admin.RelatedOnlyFieldListFilter),
    ]
    raw_id_fields = ['service']


class LiveryAdminForm(forms.ModelForm):
    save_as = True

    class Meta:
        widgets = {
            'colours': forms.Textarea,
            'css': forms.Textarea,
            'left_css': forms.Textarea,
            'right_css': forms.Textarea,
        }


@admin.register(Livery)
class LiveryAdmin(admin.ModelAdmin):
    form = LiveryAdminForm
    search_fields = ['name']
    list_display = ['id', 'name', 'vehicles', 'left', 'right', 'white_text']

    def right(self, obj):
        if obj.right_css:
            return format_html('<div style="height:1.5em;width:2.25em;background:{}"></div>', obj.right_css)
    right.admin_order_field = 'right_css'

    def left(self, obj):
        if obj.left_css:
            return format_html('<div style="height:1.5em;width:2.25em;background:{}"></div>', obj.left_css)
    left.admin_order_field = 'left_css'

    def vehicles(self, obj):
        return obj.vehicles
    vehicles.admin_order_field = 'vehicles'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if 'changelist' in request.resolver_match.view_name:
            return queryset.annotate(vehicles=Count('vehicle'))
        return queryset


class RevisionChangeFilter(admin.SimpleListFilter):
    title = 'changed field'
    parameter_name = 'change'

    def lookups(self, request, model_admin):
        return (
            ('changes__reg', 'reg'),
            ('changes__depot', 'depot'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value and value.startswith('changes__'):
            return queryset.filter(**{f'{value}__isnull': False})
        return queryset


@admin.register(VehicleRevision)
class VehicleRevisionAdmin(admin.ModelAdmin):
    raw_id_fields = ['from_operator', 'to_operator', 'vehicle']
    list_display = ['datetime', 'vehicle', '__str__', user]
    actions = ['revert']
    list_filter = [
        RevisionChangeFilter,
        UserFilter,
        ('vehicle__operator', admin.RelatedOnlyFieldListFilter),
    ]
    list_select_related = ['from_operator', 'to_operator', 'vehicle']

    def revert(self, request, queryset):
        for revision in queryset.prefetch_related('vehicle'):
            if list(revision.changes.keys()) == ['reg']:
                before, after = revision.changes['reg'].split('\n+')
                after = after.replace(' ', '').upper()
                before = before[1:]
                if revision.vehicle.reg == after:
                    revision.vehicle.reg = before
                    revision.vehicle.save(update_fields=['reg'])
                    revision.delete()
                    self.message_user(request, f'Reverted {after} to {before}')


admin.site.register(VehicleFeature)
