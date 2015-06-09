# coding=utf-8
__author__ = 'Alwx'
'''
При изменении критичности задачи, проставлении ответственного, создании новой задачи, изменении планового времени
делается проверка, укладывается ли ответственный в свои цели.
Если нет, то выдавается сообщение подтверждения текущей операции.
Если ответственный не укладывается в цели чужих проектов, делать эти операции не разрешается.
'''
from PManager.models.tasks import PM_Task, PM_Milestone
from PManager.viewsExt.gantt import WorkTime
from django.utils import timezone
import datetime


def check_milestones(task):
    result = [True]
    order = ['-critically', '-dateCreate']
    initTask = task  #PM_Task.objects.get(id=task_id)
    responsible = initTask.resp
    if not responsible:
        return result
    tasks = PM_Task.objects.filter(resp=responsible, closed=False, virgin=True)
    tasks = tasks.order_by(*order)
    tasks = tasks.values(
        'id',
        'planTime',
        'dateCreate',
        'project__id',
        'milestone__id',
        'resp__id',
        'critically'
    )
    milestones = PM_Milestone.objects.filter(closed=False).order_by('-date')
    milestones = milestones.values(
        'id',
        'name',
        'date',
        'project'
    )
    aTasks = []
    for task in tasks:
        aTasks.append(task)

    # К сортированному списку добавляем примерные даты начала и конца задачи
    now = timezone.make_aware(datetime.datetime.now(), timezone.get_current_timezone())
    step = None
    for task in aTasks:
        if step:
            task['dateCreateGantt'] = step
        else:
            task['dateCreateGantt'] = now

        if task['planTime']:
            taskTimer = WorkTime(
                startDateTime=task['dateCreateGantt'],
                taskHours=task['planTime']
            )
            endTime = step = task['dateCreateGantt'] + datetime.timedelta(hours=taskTimer.taskRealTime)
        else:
            endTime = step = task['dateCreateGantt'] + datetime.timedelta(hours=1)

        task['endTime'] = endTime
        task['resp__id'] = task['resp__id'] if task['resp__id'] else 0

    # Сама проверка
    for task in aTasks:
        if task['id'] == initTask.id:
            if task['dateCreateGantt'] > milestones[0]['date']:
                return [True]  # Если старт изначальная задача будет позже уже просроченных майлстоунов
        if task['milestone__id']:
            milestone = milestones.get(id=task['milestone__id'])
            if milestone not in result:
                if task['endTime'] > milestone['date']:
                    result[0] = False
                    result.append(milestone)

    return result
