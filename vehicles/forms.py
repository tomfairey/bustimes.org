from django import forms
from django.db.models import Count
from busstops.models import Operator
from .models import VehicleType, Livery


def get_livery_choices(operator):
    choices = {}
    liveries = Livery.objects.filter(vehicle__operator=operator).annotate(popularity=Count('vehicle'))
    for livery in liveries.order_by('-popularity').distinct():
        choices[livery.id] = livery
    for vehicle in operator.vehicle_set.exclude(colours='').distinct('colours', 'notes'):
        if vehicle.colours in choices:
            choices[vehicle.colours].name = ''
        else:
            choices[vehicle.colours] = Livery(colours=vehicle.colours, name=vehicle.notes)
    choices = [(key, livery.preview(name=True)) for key, livery in choices.items()]
    choices.append(('Other', 'Other'))
    return choices


class EditVehiclesForm(forms.Form):
    operator = forms.ModelChoiceField(queryset=None, label='Operator', required=False)
    vehicle_type = forms.ModelChoiceField(queryset=VehicleType.objects, label='Type', required=False)
    colours = forms.ChoiceField(label='Livery', widget=forms.RadioSelect, required=False)
    branding = forms.CharField(required=False)
    notes = forms.CharField(required=False)
    withdrawn = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        operator = kwargs.pop('operator', None)
        super().__init__(*args, **kwargs)

        if operator:
            self.fields['colours'].choices = get_livery_choices(operator)

        if operator and operator.name.startswith('Stagecoach '):
            queryset = Operator.objects.filter(name__startswith='Stagecoach ', service__current=True)
            self.fields['operator'].queryset = queryset.order_by('name').distinct()
        else:
            del(self.fields['operator'])


class EditVehicleForm(EditVehiclesForm):
    fleet_number = forms.IntegerField(required=False, min_value=0)
    reg = forms.CharField(label='Registration', required=False)
    name = forms.CharField(label='Name', required=False)

    field_order = ['operator', 'fleet_number', 'reg', 'vehicle_type', 'colours', 'branding', 'name', 'notes']

    def __init__(self, *args, **kwargs):
        vehicle = kwargs.pop('vehicle', None)
        super().__init__(*args, **kwargs)

        if str(vehicle.fleet_number) in vehicle.code:
            self.fields['fleet_number'].disabled = True
