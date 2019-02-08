# -*- coding:utf-8 -*-
__author__ = 'Gvammer'
from django.shortcuts import HttpResponse
from django.contrib.auth.models import User
from PManager.models import PM_User, PM_Project, PM_Tracker, PM_Task, PM_Achievement, PM_Project_Achievement
from PManager.viewsExt.tools import emailMessage
from tracker.settings import ADMIN_EMAIL, INFO_EMAIL
import datetime
from django.contrib.auth import login


def recall(request):
    phone = request.POST.get('phone', None)
    if phone:
        mess = emailMessage(
            'phone_recall',
            {
                'phone': phone
            },
            u'Перезвонить по этому номеру'
        )
        mess.send([ADMIN_EMAIL, INFO_EMAIL])

    return HttpResponse(u'Спасибо! Мы перезвоним вам в течение нескольких минут.')


def register(request):
    email = request.POST.get('email', None)
    if email:
        if not emailMessage.validateEmail(email):
            return HttpResponse(u'Введите правильный email')

        if not User.objects.filter(email=email).count():
            project = PM_Project(
                name=u'Мой проект',
                description=u'Описание нового проекта',
                author=User.objects.get(pk=1),
                payer=User.objects.get(pk=1)
            )

            project.save()

            user = PM_User.getOrCreateByEmail(email, project, 'manager')
            user.is_staff = True

            user.save()

            project.author = user
            project.payer = user

            project.setSettings({'client_comission': 10})
            project.save()
            request.COOKIES["CURRENT_PROJECT"] = project.id

            prof = user.get_profile()
            # prof.setRole('client', project, 'plan_time')
            # prof.sp_price = 1500
            # prof.account_total = 0
            prof.premium_till = datetime.datetime.now() + datetime.timedelta(days=(365*10))
            prof.save()

            # task = PM_Task.createByString(
            #     u'Ознакомиться с сервисом контроля удаленной работы Heliard',
            #     user,
            #     None,
            #     None,
            #     project=project
            # )
            # task.resp = user
            # task.systemMessage(u'Задача создана', user, 'TASK_CREATE')
            # task.setStatus('revision')

            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(
                request,
                user
            )

            return HttpResponse(u'OK')
        else:
            return HttpResponse(u'Такой email уже существует в системе!')

    return HttpResponse(u'Ошибка')