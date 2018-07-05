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
# along with Workout Manager.  If not, see <http://www.gnu.org/licenses/>.

import json
from django.contrib.auth.models import User, Group, Permission
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from django.http import HttpResponse
from django.db.utils import IntegrityError

from wger.core.models import (UserProfile, Language, DaysOfWeek, License,
                              RepetitionUnit, WeightUnit)
from wger.core.api.serializers import (
    UsernameSerializer,
    LanguageSerializer,
    DaysOfWeekSerializer,
    LicenseSerializer,
    RepetitionUnitSerializer,
    WeightUnitSerializer,
    UserSerializer
)
from wger.core.api.serializers import UserprofileSerializer
from wger.utils.permissions import UpdateOnlyPermission, WgerPermission


class UserProfileViewSet(viewsets.ModelViewSet):
    '''
    API endpoint for workout objects
    '''
    is_private = True
    serializer_class = UserprofileSerializer
    permission_classes = (WgerPermission, UpdateOnlyPermission)
    ordering_fields = '__all__'

    def get_queryset(self):
        '''
        Only allow access to appropriate objects
        '''
        return UserProfile.objects.filter(user=self.request.user)

    def get_owner_objects(self):
        '''
        Return objects to check for ownership permission
        '''
        return [(User, 'user')]

    @detail_route()
    def username(self, request, pk):
        '''
        Return the username
        '''

        user = self.get_object().user
        return Response(UsernameSerializer(user).data)


class LanguageViewSet(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint for workout objects
    '''
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    ordering_fields = '__all__'
    filter_fields = ('full_name', 'short_name')


class DaysOfWeekViewSet(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint for workout objects
    '''
    queryset = DaysOfWeek.objects.all()
    serializer_class = DaysOfWeekSerializer
    ordering_fields = '__all__'
    filter_fields = ('day_of_week', )


class LicenseViewSet(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint for workout objects
    '''
    queryset = License.objects.all()
    serializer_class = LicenseSerializer
    ordering_fields = '__all__'
    filter_fields = ('full_name', 'short_name', 'url')


class RepetitionUnitViewSet(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint for repetition units objects
    '''
    queryset = RepetitionUnit.objects.all()
    serializer_class = RepetitionUnitSerializer
    ordering_fields = '__all__'
    filter_fields = ('name', )


class WeightUnitViewSet(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint for weight units objects
    '''
    queryset = WeightUnit.objects.all()
    serializer_class = WeightUnitSerializer
    ordering_fields = '__all__'
    filter_fields = ('name', )


class UserViewSet(viewsets.ModelViewSet):
    '''
    API endpoint for creating new users
    '''
    is_private = True
    serializer_class = UserSerializer
    ordering_fields = (
        'first_name', 'last_name', 'username', 'email', 'password'
    )
    queryset = User.objects.all()

    def create(self, request):
        '''
        Create a user via a REST API
        '''
        api_user = self.request.user
        creator_profile = UserProfile.objects.get(user=api_user)

        # Check if user has rights to create users via API
        allowed_user = self.validate_user_api_rights(api_user)
        if isinstance(allowed_user, HttpResponse):
            return allowed_user

        serializer = UserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors)

        # Create user
        try:
            serializer = serializer.check_valid_fields(request.data)
            new_user = User.objects.create_user(**serializer)
            new_user.save()
        except IntegrityError:
            return Response({'Message': 'User already exist'},
                            status=status.HTTP_409_CONFLICT)

        # flag who created the user
        new_user.userprofile.created_by = creator_profile.user.username
        new_user.userprofile.save()

        return Response({'Message': 'User successfully created'},
                        status=status.HTTP_201_CREATED)

    def validate_user_api_rights(self, api_user=None):
        '''
        Validate that user has the right to create users
        '''
        if not api_user.userprofile.add_user_enabled:
            msg = {'Message': 'Request wger Admin for API user creation rights.'}
            return Response(msg, status=status.HTTP_403_FORBIDDEN)
