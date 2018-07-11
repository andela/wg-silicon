# -*- coding: utf-8 -*-

# This file is part of wger Workout Manager.
#
# wger Workout Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# wger Workout Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License

import logging
import csv
import datetime
import requests
import os
import base64
import urllib
import settings 

from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy
from django.db.models import Min
from django.db.models import Max
from django.views.generic import CreateView
from django.views.generic import UpdateView

from rest_framework.response import Response
from rest_framework.decorators import api_view

from formtools.preview import FormPreview

from wger.weight.forms import WeightForm
from wger.weight.models import WeightEntry, Fitbit
from wger.core.models import UserProfile
from wger.weight import helpers
from wger.utils.helpers import check_access
from wger.utils.generic_views import WgerFormMixin

logger = logging.getLogger(__name__)


class WeightAddView(WgerFormMixin, CreateView):
    '''
    Generic view to add a new weight entry
    '''
    model = WeightEntry
    form_class = WeightForm
    title = ugettext_lazy('Add weight entry')
    form_action = reverse_lazy('weight:add')

    def get_initial(self):
        '''
        Set the initial data for the form.

        Read the comment on weight/models.py WeightEntry about why we need
        to pass the user here.
        '''
        return {'user': self.request.user, 'date': datetime.date.today()}

    def form_valid(self, form):
        '''
        Set the owner of the entry here
        '''
        form.instance.user = self.request.user
        return super(WeightAddView, self).form_valid(form)

    def get_success_url(self):
        '''
        Return to overview with username
        '''
        return reverse(
            'weight:overview', kwargs={'username': self.object.user.username})


class WeightUpdateView(WgerFormMixin, UpdateView):
    '''
    Generic view to edit an existing weight entry
    '''
    model = WeightEntry
    form_class = WeightForm

    def get_context_data(self, **kwargs):
        context = super(WeightUpdateView, self).get_context_data(**kwargs)
        context['form_action'] = reverse(
            'weight:edit', kwargs={'pk': self.object.id})
        context['title'] = _('Edit weight entry for the %s') % self.object.date

        return context

    def get_success_url(self):
        '''
        Return to overview with username
        '''
        return reverse(
            'weight:overview', kwargs={'username': self.object.user.username})


@login_required
def export_csv(request):
    '''
    Exports the saved weight data as a CSV file
    '''

    # Prepare the response headers
    response = HttpResponse(content_type='text/csv')

    # Convert all weight data to CSV
    writer = csv.writer(response)

    weights = WeightEntry.objects.filter(user=request.user)
    writer.writerow([_('Weight').encode('utf8'), _('Date').encode('utf8')])

    for entry in weights:
        writer.writerow([entry.weight, entry.date])

    # Send the data to the browser
    response['Content-Disposition'] = 'attachment; filename=Weightdata.csv'
    response['Content-Length'] = len(response.content)
    return response


def overview(request, username=None):
    '''
    Shows a plot with the weight data

    More info about the D3 library can be found here:
        * https://github.com/mbostock/d3
        * http://d3js.org/
    '''
    is_owner, user = check_access(request.user, username)

    template_data = {}

    min_date = WeightEntry.objects.filter(user=user).\
        aggregate(Min('date'))['date__min']
    max_date = WeightEntry.objects.filter(user=user).\
        aggregate(Max('date'))['date__max']
    if min_date:
        template_data['min_date'] = \
            'new Date(%(year)s, %(month)s, %(day)s)' % \
            {'year': min_date.year,
             'month': min_date.month,
             'day': min_date.day}
    if max_date:
        template_data['max_date'] = \
            'new Date(%(year)s, %(month)s, %(day)s)' % \
            {'year': max_date.year,
             'month': max_date.month,
             'day': max_date.day}

    last_weight_entries = helpers.get_last_entries(user)

    template_data['is_owner'] = is_owner
    template_data['owner_user'] = user
    template_data['show_shariff'] = is_owner
    template_data['last_five_weight_entries_details'] = last_weight_entries
    return render(request, 'overview.html', template_data)


@api_view(['GET'])
def get_weight_data(request, username=None):
    '''
    Process the data to pass it to the JS libraries to generate an SVG image
    '''

    is_owner, user = check_access(request.user, username)

    date_min = request.GET.get('date_min', False)
    date_max = request.GET.get('date_max', True)

    if date_min and date_max:
        weights = WeightEntry.objects.filter(
            user=user, date__range=(date_min, date_max))
    else:
        weights = WeightEntry.objects.filter(user=user)

    chart_data = []

    for i in weights:
        chart_data.append({'date': i.date, 'weight': i.weight})

    # Return the results to the client
    return Response(chart_data)


class WeightCsvImportFormPreview(FormPreview):
    preview_template = 'import_csv_preview.html'
    form_template = 'import_csv_form.html'

    def get_context(self, request, form):
        '''
        Context for template rendering.
        '''

        return {
            'form': form,
            'stage_field': self.unused_name('stage'),
            'state': self.state,
            'form_action': reverse('weight:import-csv')
        }

    def process_preview(self, request, form, context):
        context[
            'weight_list'], context['error_list'] = helpers.parse_weight_csv(
                request, form.cleaned_data)
        return context

    def done(self, request, cleaned_data):
        weight_list, error_list = helpers.parse_weight_csv(
            request, cleaned_data)
        WeightEntry.objects.bulk_create(weight_list)
        return HttpResponseRedirect(
            reverse(
                'weight:overview', kwargs={'username': request.user.username}))

class FitbitWeightFormPreview(FormPreview):
    preview_template = 'import_from_fitbit_form_preview.html'
    form_template = 'import_from_fitbit_form.html'
    def get_context(self, request, form):
        '''
        Context for template rendering.
        '''
        # Check if user has authorized wger to Fitbit
        try:
            profile = Fitbit.objects.get(user=request.user)
        except Fitbit.DoesNotExist:
            profile = None
        fitbit_connect = True if profile is not None else False
        fitbit_config = True if (os.getenv('FITBIT_CLIENT_ID') and
                             os.getenv('FITBIT_CLIENT_SECRET')) is not None else False
        return {
            'form': form,
            'stage_field': self.unused_name('stage'),
            'state': self.state,
            'fitbit_connect': fitbit_connect,
            'fitbit_config': fitbit_config,
            'form_action': reverse('weight:import-from-fitbit')
        }

    def process_preview(self, request, form, context):
        # Retrieve user's weights from Fitbit on a specified date and period
        spec_date = form.cleaned_data['date']
        period = form.cleaned_data['period']
        creds = Fitbit.objects.get(user=request.user)
        try:
            access_token = '{} {}'.format(creds.token_type, creds.access_token)
            url = "https://api.fitbit.com/1/user/-/body/log/weight/date/{}/{}.json".format(spec_date, period)
            r = requests.get(url,
                                headers={'accept': 'application/json',
                                        'authorization': access_token})
            # Check unauthorized token
            if r.status_code == 401:
                creds.delete() # Delete existing credentials
                return HttpResponseRedirect(reverse('weight:import-from-fitbit'))
            if r.status_code == 200:
                response = r.json()
            else:
                response = r.json()
        except requests.HTTPError:
            print('Something went wrong')
            weight_list = []
        if 'weight' in response:
            weight_list = response['weight']
        else:
            weight_list = []
        request.session['weight_list'] = weight_list
        context['weight_list'] = weight_list
        
        return context

    def done(self, request, cleaned_data):
        weight_list = request.session['weight_list']
        weight_entries = []
        for log in weight_list:
            try:
                exist_entry = WeightEntry.objects.get(date=log['date'])
                if exist_entry.weight == log['weight']:
                    exist_entry.weight == log['weight']
                    exist_entry.save()
            except WeightEntry.DoesNotExist:
                entry = WeightEntry(user=request.user, date=log['date'], weight=log['weight'])
                entry.save()

        return HttpResponseRedirect(
            reverse(
                'weight:overview', kwargs={'username': request.user.username}))


@login_required
def connectFitbit(request):
    '''
    Request access to Fitbit user details
    '''
    oauth_code = request.GET.get('code')
    redirect_uri = '{}/en/weight/import-from-fitbit/authorize'.format(settings.SITE_URL)
    expires_in = 31536000
    if(oauth_code is None):
        redirect_uri = '{}/en/weight/import-from-fitbit/authorize'.format(settings.SITE_URL)
        data = {
            'response_type':'code',
            'client_id':os.getenv('FITBIT_CLIENT_ID'),
            'redirect_uri': redirect_uri,
            'scope':'activity heartrate location nutrition profile settings sleep social weight',
            'expires_in': expires_in
        }
        payload = urllib.parse.urlencode(data)
        url = "https://www.fitbit.com/oauth2/authorize?{}".format(payload)
        return HttpResponseRedirect(url)
    try:
        code = oauth_code # From redirect uri
        payload = {
            'grant_type':'authorization_code',
            'clientId': os.getenv('FITBIT_CLIENT_SECRET'),
            'code': code,
            'redirect_uri': redirect_uri,
            'expires_in': expires_in
        }
        credentials = '{}:{}'.format(os.getenv('FITBIT_CLIENT_ID'),os.getenv('FITBIT_CLIENT_SECRET'))
        basic_token = base64.standard_b64encode(bytes(credentials,'utf-8'))
        basic_token = 'Basic {}'.format(basic_token.decode('utf-8'))
        r = requests.post("https://api.fitbit.com/oauth2/token",
                            data=payload,
                            headers={'Content-Type': 'application/x-www-form-urlencoded',
                                    'Authorization': basic_token})
        response = r.json()
        fitbit_creds = Fitbit(
            user=request.user,
            access_token=response['access_token'],
            refresh_token=response['refresh_token'],
            scopes=response['scope'],
            token_type=response['token_type'],
            expiration_date=datetime.datetime.now() + datetime.timedelta(seconds=int(response['expires_in'])),
            fitbit_user_id=response['user_id']
        )
        fitbit_creds.save()
    except requests.HTTPError:
        print('Something went wrong')

    return HttpResponseRedirect(
            reverse(
                'weight:import-from-fitbit'))