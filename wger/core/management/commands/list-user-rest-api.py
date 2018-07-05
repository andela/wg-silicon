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
from django.contrib.auth.models import User
from tabulate import tabulate
from wger.core.models import UserProfile


class Command(BaseCommand):
    '''
    Command to list users created via API
    '''
    help = 'List users'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str)

    def handle(self, **options):
        creator_username = options['username']
        try:
            user_creator = User.objects.get(username=creator_username)
        except User.DoesNotExist:
            raise CommandError('User with "%s" username does not exist' % creator_username)

        created_users = UserProfile.objects.all().filter(created_by=creator_username)
        headers = ['First Name', 'Last Name', 'Username', 'Email']
        table_content = list()
        for user in created_users:
            table_content.append([user.user.first_name,
                                  user.user.last_name,
                                  user.user.username,
                                  user.user.email])
        self.stdout.write(tabulate(table_content, headers, tablefmt='rst'))
