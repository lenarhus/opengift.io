# -*- coding:utf-8 -*-
__author__ = 'Gvammer'
import datetime, redis
from tracker import settings
from django.core.mail import EmailMultiAlternatives
from django.template import Context, loader
from django.utils import timezone
from PManager.classes.server.message import RedisMessage
from PManager.services.service_queue import service_queue
from django.template.base import TemplateDoesNotExist

def redisSendTaskAdd(fields):
    mess = RedisMessage(service_queue,
                        objectName='task',
                        type='add',
                        fields=fields
    )
    mess.send()

def redisSendTaskUpdate(fields):
    mess = RedisMessage(service_queue,
                        objectName='task',
                        type='update',
                        fields=fields
    )
    mess.send()


class emailMessage:
    templateName = ''
    context = None
    subject = ''
    u_from = "OpenGift <%s>" % settings.NO_REPLY_EMAIL

    def __init__(self, templateName, context, subject, u_from='no-reply@opengift.io'):
        setattr(self, 'templateName', templateName)
        setattr(self, 'context', context)
        setattr(self, 'subject', subject)
        if u_from:
            setattr(self, 'u_from', u_from)

    @staticmethod
    def validateEmail(email):
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError

        try:
            validate_email(email)
            return True
        except ValidationError:
            return False

    def send(self, to):
        t = loader.get_template('mail_templates/' + self.templateName + '.html')
        c = Context(self.context)
        html_content = t.render(c)

        text_content = ''
        try:
            t = loader.get_template('mail_templates/' + self.templateName + '.txt')
            c = Context(self.context)
            text_content = t.render(c)
        except TemplateDoesNotExist:
            pass

        msg = EmailMultiAlternatives(self.subject, text_content, self.u_from, to)
        msg.attach_alternative(html_content, "text/html")
        try:
            msg.send()
        except:
            pass


class templateTools:
    class dateTime:
        dateFormat = '%d.%m.%Y %H:%M'
        dateDBFormat = '%Y-%m-%d %H:%M:%S'

        @staticmethod
        def convertToSite(date, format=None):
            if not format: format = '%d.%m.%Y %H:%M'
            if isinstance(date, datetime.datetime):
                date = timezone.localtime(date)
                return date.strftime(format)

        @staticmethod
        def convertToDateTime(date):
            try:
                return datetime.datetime.strptime(date, '%d.%m.%Y %H:%M')
            except ValueError:
                try:
                    return datetime.datetime.strptime(date, '%d.%m.%Y')
                except ValueError:
                    return None

        @staticmethod
        def convertFromDb(date):
            return datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y %H:%M')

        @staticmethod
        def convertToDb(date):
            if isinstance(date, datetime.datetime):
                # date = timezone.localtime(date)
                return date.strftime('%Y-%m-%d %H:%M:%S')

        @staticmethod
        def timeFromTimestamp(seconds):
            if not seconds: seconds = 0
            return {
                'hours': int(seconds // 3600),
                'minutes': int(seconds % 3600 // 60),
                'seconds': int(seconds % 60),
            }

    def get_random_string(length=12, allowed_chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'):
        """
          Returns a random string of length characters from the set of a-z, A-Z, 0-9
          for use as a salt.

          The default length of 12 with the a-z, A-Z, 0-9 character set returns
          a 71-bit salt. log_2((26+26+10)^12) =~ 71 bits
          """
        import random

        try:
            random = random.SystemRandom()
        except NotImplementedError:
            pass
        return ''.join([random.choice(allowed_chars) for i in range(length)])

    @staticmethod
    def get_task_template(name='task'):
        file_name = "%stracker/templates/item_templates/task/%s.html" % (settings.PROJECT_ROOT, name)
        with file(file_name) as f:
            template = f.read()
        return template

    @staticmethod
    def getMessageTemplates():
        templateFiles = {
            'template': 'task_comment.html',
            'task_close': 'log_message_task_close.html',
            'task_create': 'log_message_task_create.html',
            'status_ready': 'log_message_task_status_ready.html',
            'status_revision': 'log_message_task_status_revision.html',
            'new_responsible': 'log_message_new_responsible.html',
            'donation': 'log_message_donation.html',
            'vote': 'log_message_vote.html',
            'confirmation': 'log_message_confirm.html',
            'critically_up': 'log_message_task_critically_up.html',
            'critically_down': 'log_message_task_close.html',
            'set_plan_time': 'log_message_task_set_plan_time.html',
            'external_requirement': 'log_message_external_requirement.html',
            'time_request': 'log_message_task_time_request.html',
            'confirm_estimation': 'log_message_task_status_revision.html',
            'task_open': 'log_message_task_critically_up.html',
            'git_commit': 'log_message_git_commit.html',
            'solution': 'solution_task_comment.html'
        }
        templates = {}

        for (c, f) in templateFiles.iteritems():
            with file(settings.PROJECT_ROOT + 'tracker/templates/item_templates/messages/' + f) as f:
                templates[c] = f.read()

        return templates


def set_cookie(response, key, value, days_expire=7):
    if days_expire is None:
        max_age = 365 * 24 * 60 * 60  # one year
    else:
        max_age = days_expire * 24 * 60 * 60
    expires = datetime.datetime.strftime(datetime.datetime.utcnow() + datetime.timedelta(seconds=max_age),
                                         "%a, %d-%b-%Y %H:%M:%S GMT")
    response.set_cookie(key, value, max_age=max_age, expires=expires, domain=settings.SESSION_COOKIE_DOMAIN,
                        secure=settings.SESSION_COOKIE_SECURE or None)


class taskExtensions:
    @staticmethod
    def getFileList(queryset):
        from PManager.templatetags.thumbnail import thumbnail, protected

        return [{
                    'id': file.id,
                    'name': file.name,
                    'url': file.src,
                    'viewUrl': '/docx/?f=' + str(file.id) if file.type in ['docx', 'xlsx'] else '',
                    'type': file.type,
                    'thumb100pxUrl': protected(thumbnail(str(file), '100x100')) if file.isPicture else '',
                    'is_picture': file.isPicture,
                    'date_create': templateTools.dateTime.convertToSite(file.date_create)
                } for file in queryset]


class TextFilters:
    @staticmethod
    def escapeText(text):
        text = text.replace('"', "'")
        text = text.replace('<script', '<sc ript')
        return text

    @staticmethod
    def getFormattedText(text):
        import re
        from django.template.defaultfilters import linebreaksbr

        text = re.sub(r'(http|www\.)([^\ ^\,\r\n\"]+)',
                      r'<a target="_blank" href="\1\2">\1\2</a>', text)
        aFindString = re.findall(r'(\>[^\<]+\<\/a>)', text)
        for s in aFindString:
            s1 = s
            s1 = s1.replace('>', '').replace('</a>', '')
            if len(s1) > 35:
                s1 = s1[:35]
                text = text.replace(s, '>' + s1 + '...</a>')

        text = TextFilters.escapeText(text)
        text = linebreaksbr(text)
        text = text.replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
        return text

    @staticmethod
    def convertQuotes(text):
        import re
        text = re.sub(r'\[Q\](.*?)\[\/Q\]', r'<blockquote class="well">\1</blockquote>', text)
        return text
