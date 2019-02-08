# -*- coding:utf-8 -*-
from __future__ import division

__author__ = 'Gvammer'
from PManager.models import PM_Project, PM_Task, PM_Timer, PM_Task_Message, LogData
from django.contrib.auth.models import User
from PManager.viewsExt.headers import TRACKER
from PManager.viewsExt.tasks import TaskWidgetManager
from django.db.models import Q
import datetime
from django.utils import timezone
from collections import deque


def set_to_midnight(dt):
    midnight = datetime.time(0)
    return datetime.datetime.combine(dt.date(), midnight)


def widget(request, headerValues, a, b):
    bAllUsers = request.GET.get('show_all') == 'Y'
    projects = PM_Project.objects.filter(closed=False, locked=False)
    now = timezone.make_aware(datetime.datetime.now(), timezone.get_current_timezone())

    users = TaskWidgetManager.getUsersThatUserHaveAccess(request.user, headerValues['CURRENT_PROJECT'])
    if not bAllUsers:
        users = users.filter(id__in=PM_Timer.objects.filter(
            Q(Q(dateEnd=None) | Q(dateEnd__gt=datetime.datetime.now() - datetime.timedelta(days=1)))
        ).values('user__id'))

    users = users.order_by('last_name')

    # arFilter = {}

    usersResult = []
    maxTaskEffective = 0
    maxEventsQty = 1
    ratingUsers = deque()
    for user in users:
        userJoinTime = now - datetime.timedelta(days=30)
        # userJoinTime = userJoinTime.days if userJoinTime.days > 0 else 1
        # userJoinTime = 30
        taskClosedQty = PM_Task.objects.filter(closed=True, resp=user, dateClose__gte=userJoinTime, active=True).count()
        userRoles = user.userRoles.filter(project__in=projects)
        setattr(user, 'roles_in_projects', userRoles)

        profile = user.get_profile()

        if profile.avatar:
            profile.avatar = str(profile.avatar).replace('PManager', '')

        eventsQty = PM_Task_Message.objects.filter(
            dateCreate__gte=userJoinTime,
            author=user
        ).count()
        time = LogData.objects.raw(
            'SELECT SUM(`value`) as summ, id, user_id from PManager_logdata WHERE `user_id`=' + str(int(user.id)) + '' +
            ' AND datetime > \'' + userJoinTime.strftime('%Y-%m-%d %H:%M:%S') + '\'' +
            ' AND code = \'DAILY_TIME\''
        )
        allTime = 0
        for timer in time:
            allTime += timer.summ if timer.summ else 0

        setattr(user, 'profile', profile)
        setattr(user, 'tasksQty', taskClosedQty)
        setattr(user, 'eventsQty', eventsQty + round(allTime / 3600))

        if user.eventsQty > maxEventsQty:
            maxEventsQty = user.eventsQty

        if taskClosedQty:
            setattr(user, 'tasksEffective', round(taskClosedQty / 30, 4))

            if user.tasksEffective > maxTaskEffective:
                maxTaskEffective = user.tasksEffective
                ratingUsers.append(user.id)

        try:
            if user.pk:
                startedTimer = PM_Timer.objects.filter(user__id=user.pk).order_by('-dateEnd')
                if startedTimer:
                    startedTimer = startedTimer[0]
                    bHaveAccessToStartedTask = request.user.get_profile().hasAccess(startedTimer.task, 'view')
                    if bHaveAccessToStartedTask:
                        setattr(user, 'startedTask', startedTimer.task)
                        setattr(user, 'startedTimer', startedTimer)
                        setattr(user, 'taskTime', startedTimer.task.getAllTime())
                    else:
                        continue

        except PM_Timer.DoesNotExist:
            pass

        if not user.email and user.username.find('@'):
            setattr(user, 'email', user.username)

        usersResult.append(user)

    for user in usersResult:
        setattr(user, 'activity', int(round(float(user.eventsQty) / float(maxEventsQty), 2) * 100))

    projects = request.user.get_profile().getProjects()
    aProjects = []
    arWeekDays = {
        1: u'Пн',
        2: u'Вт',
        3: u'Ср',
        4: u'Чт',
        5: u'Пт',
        6: u'Сб',
        7: u'Вс',
    }

    for project in projects:
        weekdays = range(1, 7)
        now = datetime.datetime.combine(datetime.date.today(), datetime.time.max)
        now = timezone.make_aware(now, timezone.get_current_timezone())
        date1, date2 = None, None
        events = []
        for dayLost in weekdays:
            if not date2:
                date2 = now

            date1 = now - datetime.timedelta(days=dayLost)
            eventsQty = PM_Task_Message.objects.filter(
                dateCreate__lt=date2,
                dateCreate__gte=date1,
                project=project
            ).count()
            time = LogData.objects.raw(
                'SELECT SUM(`value`) as summ, id, user_id from PManager_logdata WHERE `project_id`=' + str(
                    int(project.id)) + '' +
                ' AND DATE(datetime) = \'' + date2.date().isoformat() + '\'' +
                ' AND code = \'DAILY_TIME\''
            )

            allTime = 0
            for timer in time:
                allTime += timer.summ if timer.summ else 0

            eventsQty += int(round(float(allTime) / float(3600)))
            events.append({
                'date': arWeekDays[date2.isoweekday()],
                'qty': eventsQty
            })
            date2 = date1

        events.reverse()
        setattr(project, 'events', events)
        aProjects.append(project)

    return {
        'title': u'Активность пользователей',
        'users': usersResult,
        'currentProject': int(request.GET.get('project', 0)),
        'projects': aProjects,
        'topUser': ratingUsers.pop() if len(ratingUsers) > 0 and bAllUsers else 0
    }