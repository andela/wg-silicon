# -*- coding: utf-8 *-*

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


from django.core.management.base import BaseCommand, CommandError
from wger.core.models import UserProfile


class Command(BaseCommand):
    help = 'Allow creation of new users via REST API'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str)

        parser.add_argument('--enable',
                            action='store_true',
                            dest='enable',
                            help='Grant user right to create users via REST API')

        parser.add_argument('--disable',
                            action='store_true',
                            dest='disable',
                            help='Revoke user right to create users via REST API')

        parser.add_argument('--status',
                            action='store_true',
                            dest='status',
                            help='Check user rights to create users via REST API')

    def handle(self, *args, **options):
        username = options['username']
        try:
            profile = UserProfile.objects.get(user__username=username)
        except UserProfile.DoesNotExist:
            raise CommandError('User with "%s" username does not exist' % username)

        if options['enable']:
            profile.add_user_enabled = True
            profile.save()
            self.stdout.write(self.style.SUCCESS(
                'Successfully ENABLED REST API user creation for "%s"' % username))
        elif options['disable']:
            profile.add_user_enabled = False
            profile.save()
            self.stdout.write(self.style.WARNING(
                'Successfully DISABLED REST API user creation for "%s"' % username))
        elif options['status']:
            status = 'ENABLED' if profile.add_user_enabled == 1 else 'DISABLED'
            self.stdout.write(self.style.WARNING(
                'User creation right for "%s" is %s' % (username, status)))
        else:
            raise CommandError('Unknown value for option use [--enable, --disable, --status]')
