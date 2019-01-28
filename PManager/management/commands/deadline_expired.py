
__author__ = 'zodman'
from django.core.management.base import NoArgsCommand
from django.utils import timezone
from django.contrib.auth.models import User
from PManager.models import PM_Task

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        now = timezone.now()
        user = User.objects.get(username="opengift@opengift.io")
        tasks = PM_Task.objects.filter(onPlanning=True, deadline__isnull=False, closed=False)
        for task in tasks:
            if task.deadline < now:
                text_desc = "Task deadline expired"

                task.Close(user)
                if task.closed:
                    task.systemMessage(text=text_desc, user=user, code="DEADLINE_EXPIRED")

                    print "Contest %s closed by deadline" % task.id

        tasks = PM_Task.objects.filter(onPlanning=True, deadline__isnull=True, closed=False)
        for task in tasks:
            donorMessage = task.messages.filter(code='DONATION')
            if donorMessage.exists():
                task.Close(donorMessage[0].author)
            else:
                task.Close(user)

            print "Contest %s closed by result" % task.id
