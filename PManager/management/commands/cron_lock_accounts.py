__author__ = 'gvammer'
from django.core.management.base import NoArgsCommand
from django.conf import settings
from django.contrib.auth.models import User
from PManager.models import PM_User, PM_Project
import datetime
from django.utils import timezone

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        users = User.objects.filter(
            is_staff=True,
            id__in=PM_User.objects.filter(
                premium_till__lt=timezone.make_aware(datetime.datetime.now(), timezone.get_default_timezone())
            ).values_list('user__id', flat=True)
        ).exclude(is_superuser=True)

        print PM_User.objects.filter(
                premium_till__lt=timezone.make_aware(datetime.datetime.now(), timezone.get_default_timezone())
            ).values_list('user__id', flat=True)
        print users.values_list('id')
        users.update(is_staff=False)
        print users.values_list('username', flat=True)
        print "\r\n"
        projects = PM_Project.objects.filter(author__in=users, locked=False)
        projects.update(locked=True)
        print projects.values_list('name', flat=True)
        print "\r\n\r\n"