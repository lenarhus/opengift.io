# -*- coding:utf-8 -*-
__author__ = 'Gvammer'
import redis
from django.db import models
from django.contrib.auth.models import User
import datetime, copy, json
from datetime import timedelta
from django.utils import timezone
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from PManager.viewsExt.tools import templateTools
from django.db.models import Q
from django.conf import settings
from django.core.validators import MaxLengthValidator
from PManager.viewsExt.tools import emailMessage
from PManager.classes.server.message import RedisMessage
from PManager.classes.logger.logger import Logger
from PManager.customs.storages import path_and_rename
from tracker.settings import COMISSION
from django.db.models.signals import post_save
from django.db.models import Sum, Max
from PManager.classes.language import transliterate
from django.db.models.signals import post_save, pre_delete, post_delete, pre_save
from PManager.services.service_queue import service_queue
from django.core.exceptions import MultipleObjectsReturned


def redisSendTaskUpdate(fields):
    mess = RedisMessage(service_queue,
                        objectName='task',
                        type='update',
                        fields=fields)
    mess.send()


def redisSendLogMessage(fields):
    mess = RedisMessage(service_queue,
                        objectName='comment',
                        type='add',
                        fields=fields)
    mess.send()


class Tags(models.Model):
    tagText = models.CharField(max_length=100, db_index=True)
    frequency = models.FloatField(default=0)
    parent = models.ForeignKey('self', blank=True, null=True, related_name="subtags")
    allowed = models.BooleanField(default=False, blank=True)
    is_public = models.BooleanField(default=False)
    color = models.CharField(max_length=30, null=True, blank=True)

    weight = 0

    def __unicode__(self):
        return self.tagText

    class Meta:
        app_label = 'PManager'


class ObjectTags(models.Model):
    tag = models.ForeignKey(Tags, related_name='objectLinks')
    weight = models.PositiveIntegerField(default=0)
    content_type = models.ForeignKey(ContentType, db_index=True)
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        app_label = 'PManager'

    @classmethod
    def get_weights(cls, tag_ids, content_type_id, obj_id=None, filter_content=[], order_by=(), limit=None):
        request_str = 'SELECT SUM(`weight`) as weight_sum, `id`, `object_id`, `content_type_id` ' + \
                      'from PManager_objecttags WHERE tag_id in (' + \
                      ', '.join(tag_ids) + ') AND content_type_id=' + \
                      str(content_type_id)
        if obj_id is not None:
            request_str += ' AND object_id=' + str(obj_id)
        if filter_content:
            request_str += ' AND object_id IN (' + ', '.join(str(x) for x in filter_content) + ')'
        request_str += " GROUP BY object_id"
        if order_by and len(order_by) == 2:
            request_str += " ORDER BY %s %s" % order_by
        if limit is not None:
            request_str += " LIMIT %s" % limit
        return cls.objects.raw(request_str)


class PM_Tracker(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    dateCreate = models.DateTimeField(auto_now_add=True, blank=True)
    description = models.TextField(null=True)
    admin = models.ForeignKey(User, related_name='createdTrackers', null=True)
    logo = models.ImageField(upload_to="tracker/media/trackers/", null=True)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'PManager'


class PM_Hackathon(models.Model):
    name = models.CharField(max_length=255)
    url = models.CharField(max_length=255, blank=True, null=True)
    text = models.CharField(max_length=1000)
    date = models.DateTimeField(blank=True)
    description = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'PManager'


class PM_Hackathon_Winner(models.Model):
    hackathon = models.ForeignKey(PM_Hackathon, related_name='hackathon_winners')
    winner = models.ForeignKey(User, related_name='hackathon_winners')

    speed = models.IntegerField(null=True, blank=True)
    requirements = models.IntegerField(null=True, blank=True)
    clarity = models.IntegerField(null=True, blank=True)
    ux = models.IntegerField(null=True, blank=True)
    sort = models.IntegerField(null=True, blank=True)

    @property
    def params(self):
        p = []
        if self.speed:
            p.append({'name': 'Speed', 'stars': [k for k in range(0, self.speed)]})
        if self.ux:
            p.append({'name': 'UX', 'stars': [k for k in range(0, self.ux)]})
        if self.clarity:
            p.append({'name': 'Clarity', 'stars': [k for k in range(0, self.clarity)]})
        if self.requirements:
            p.append({'name': 'Correctness', 'stars': [k for k in range(0, self.requirements)]})

        return p

    @property
    def score(self):
        return str(int(self.speed) + int(self.ux) + int(self.clarity) + int(self.requirements))

    def __unicode__(self):
        return str(self.hackathon) + ' ' + str(self.winner)

    class Meta:
        app_label = 'PManager'


class PM_Project_Problem(models.Model):
    problem = models.CharField(max_length=1000, verbose_name=u'Problem')
    target_group = models.CharField(max_length=2500, verbose_name=u'Target group')
    solution = models.CharField(max_length=2500, verbose_name=u'Solution')
    industry = models.ForeignKey('PM_Project_Industry', related_name="problems", null=True, blank=True)

    def __unicode__(self):
        return self.problem

    def __str__(self):
        return self.problem

    class Meta:
        app_label = 'PManager'


class PM_Project_Industry(models.Model):
    name = models.CharField(max_length=255, verbose_name=u'Title')
    active = models.BooleanField(default=False, blank=True)
    parent = models.ForeignKey('PM_Project_Industry', related_name="categories", null=True, blank=True)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name

    def getPercent(self):
        import random
        return random.randint(0, 100)

    class Meta:
        app_label = 'PManager'


class PM_Project_Donation(models.Model):
    project = models.ForeignKey('PM_Project', related_name="donations")
    user = models.ForeignKey(User, related_name="donations", null=True, blank=True)
    ref = models.ForeignKey(User, related_name="partner_donations", null=True, blank=True)
    sum = models.FloatField()
    milestone = models.ForeignKey('PM_Milestone', related_name="donations", blank=True, null=True)
    task = models.ForeignKey('PM_Task', related_name="donations", blank=True, null=True)
    exchange = models.ForeignKey(User, related_name="passedDonations", null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True, blank=True)

    def __str__(self):
        return self.project.name + ' : ' + str(self.sum)

    def __unicode__(self):
        return self.project.name + ' : ' + unicode(self.sum)

    class Meta:
        app_label = 'PManager'


class PM_Project(models.Model):
    name = models.CharField(max_length=255, verbose_name=u'Name of project')
    blockchain_name = models.CharField(max_length=255, verbose_name=u'Name of project', null=True, blank=True)
    blockchain_registered = models.BooleanField(default=False, blank=True)
    blockchain_state = models.TextField(null=True, blank=True)
    dateCreate = models.DateTimeField(auto_now_add=True, blank=True)
    description = models.TextField(null=True, blank=True, verbose_name=u'Description')
    problem = models.TextField(null=True, blank=True, verbose_name=u'The problem to solve')
    target_group = models.TextField(null=True, blank=True, verbose_name=u'Target groups')
    files = models.ManyToManyField('PM_Files', related_name="fileProjects", null=True, blank=True)
    author = models.ForeignKey(User, related_name='createdProjects')
    opengift_rating = models.IntegerField(null=True, blank=True)
    integration_price = models.FloatField(null=True, blank=True)
    commercial_analogs = models.CharField(max_length=500, null=True, blank=True)
    image = models.ImageField(upload_to=path_and_rename("project_thumbnails"), null=True,
                              verbose_name=u'Picture', blank=True)
    tracker = models.ForeignKey(PM_Tracker, related_name='projects', blank=True, null=True)
    repository = models.CharField(max_length=255, blank=True, verbose_name=u'Repo code')
    link_site = models.CharField(max_length=255, blank=True, verbose_name=u'Site')
    link_github = models.CharField(max_length=255, blank=True, verbose_name=u'Link to GitHub')
    link_demo = models.CharField(max_length=255, blank=True, verbose_name=u'Link to the Demo')
    link_video = models.CharField(max_length=255, blank=True, verbose_name=u'Link to the video')
    share_link_enabled = models.BooleanField(default=False, blank=True, verbose_name=u'Enable shares link')
    api_key = models.CharField(max_length=200, blank=True, verbose_name=u'Ключ проекта')
    closed = models.BooleanField(blank=True, verbose_name=u'Архив', default=False, db_index=True)
    locked = models.BooleanField(blank=True, verbose_name=u'Заблокирован', default=False, db_index=True)
    public = models.BooleanField(blank=True, verbose_name=u'Public', default=False, db_index=True)
    settings = models.CharField(max_length=1000, blank=True, null=True)
    payer = models.ForeignKey(User, blank=True, null=True)
    # tags = models.ManyToManyField(Tags, null=True, blank=True, related_name="tagProjects")
    specialties = models.ManyToManyField('Specialty', blank=True, null=True, related_name='projects',
                                         verbose_name=u'Направления')

    industries = models.ManyToManyField(PM_Project_Industry, blank=True, null=True, related_name='projects',
                                        verbose_name=u'Категории')

    problems = models.ManyToManyField(PM_Project_Problem, blank=True, null=True, related_name='projects',
                                      verbose_name=u'Решаемые проблемы')

    @property
    def donated(self):
        from tracker.settings import GIFT_USD_RATE
        donated = 0
        for m in self.donations.all():
            donated += m.sum or 0

        donated = donated * GIFT_USD_RATE

        return donated

    @property
    def color(self):
        if not self.milestones.exists():
            return 'grey'

        for s in self.industries.all():
            if s.name == 'Blockchain':
                return 'blue'
            elif s.name == 'Applications':
                return 'orange'
            elif s.name == 'API' or s.name == 'Databases' or s.name == 'Web Service':
                return 'green'
            elif s.name == 'IoT':
                return 'yellow'
        import random
        return random.choice(['yellow', 'green', 'orange', 'blue', 'purple'])

    @property
    def firstLetter(self):
        return self.name[0]

    @property
    def url(self):
        return '/project/' + str(self.id) + '/public/'

    @property
    def taskListUrl(self):
        return '/project/' + str(self.id) + '/tasks/'

    @property
    def imagePath(self):
        return unicode(self.image).replace('PManager', '')

    @property
    def votersQty(self):
        return RatingHits.objects.filter(project=self).count()

    @property
    def rating(self):
        return 1.0 * (RatingHits.objects.filter(
            project=self
        ).aggregate(Sum('rating'))['rating__sum'] or 0) / (self.votersQty or 1)

    def setSettings(self, settings):
        self.settings = json.dumps(settings)

    def getSettings(self):
        return json.loads(self.settings) if self.settings else {}

    def generate_rep_name(self):
        if (self.repository):
            return self.repository
        return transliterate(self.name)

    def __unicode__(self):
        return self.name

    def openMilestones(self):
        return PM_Milestone.objects.filter(
            project=self.id,
            closed=0,
        )

    def create_githubrepo(self):
        from github import Github
        import github
        from django.conf import settings
        gh = Github(settings.GITHUB_SUDO_TOKEN_SECRET)
        admin_user = gh.get_user()
        for org in admin_user.get_orgs():
            # search eht opengift organization
            if "opengift" in org.login:
                try:
                    # try to create the project on the organization
                    repo_obj = org.create_repo(self.name)
                    self.repository = repo_obj.clone_url
                    self.link_github = repo_obj.clone_url
                    return True
                except github.GithubException:
                    import traceback
                    traceback.print_exc()
                    return False
                



    def getUsers(self):
        return User.objects.filter(pk__in=[role.user.id for role in
                                           PM_ProjectRoles.objects.filter(project=self)]).distinct()

    def save(self, *args, **kwargs):
        from PManager.services.docker import blockchain_user_newproject_request
        if not self.id:
            self.payer = self.author
            # if self.author.get_profile().blockchain_wallet:
            #     blockchain_user_newproject_request(self.author.username, self.name.lower())

        super(self.__class__, self).save(*args, **kwargs)

    def getJson(self):
        return {
            'id': self.id,
            'name': self.name,
            'imagePath': self.imagePath
        }

    class Meta:
        app_label = 'PManager'


class Dependency(models.Model):
    project = models.ForeignKey('PM_Project', null=True, blank=True, related_name='dependencies')
    user = models.ForeignKey(User, null=True, blank=True, related_name='dependencies')
    dependency = models.ForeignKey('PM_Project', related_name='using')

    class Meta:
        app_label = 'PManager'


class LikesHits(models.Model):
    ip = models.CharField(max_length=255, verbose_name=u'IP', db_index=True)
    milestone = models.ForeignKey('PM_Milestone', null=True, blank=True, related_name='likesHits')
    task = models.ForeignKey('PM_Task', null=True, blank=True, related_name='likesHitsOfTask')
    datetime = models.DateTimeField(auto_now_add=True, blank=True)

    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    @staticmethod
    def userLiked(milestone, request):
        ip = LikesHits.get_client_ip(request)
        return LikesHits.objects.filter(milestone=milestone, ip=ip).exists()

    @staticmethod
    def userLikedTask(task, request):
        ip = LikesHits.get_client_ip(request)
        return LikesHits.objects.filter(task=task, ip=ip).exists()

    def save(self, *args, **kwargs):
        if not 'request' in kwargs:
            raise Exception('Save rating with request object')

        self.ip = LikesHits.get_client_ip(kwargs['request'])
        del kwargs['request']

        super(self.__class__, self).save(*args, **kwargs)

    class Meta:
        app_label = 'PManager'


class RatingHits(models.Model):
    ip = models.CharField(max_length=255, verbose_name=u'IP', db_index=True)
    project = models.ForeignKey(PM_Project, related_name='ratingHits')
    rating = models.IntegerField()

    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    @staticmethod
    def userVoted(project, request):
        ip = RatingHits.get_client_ip(request)
        return RatingHits.objects.filter(project=project, ip=ip).exists()

    def save(self, *args, **kwargs):
        if not 'request' in kwargs:
            raise Exception('Save rating with request object')

        self.ip = RatingHits.get_client_ip(kwargs['request'])
        del kwargs['request']

        super(self.__class__, self).save(*args, **kwargs)

    class Meta:
        app_label = 'PManager'


class Release(models.Model):
    statuses = (
        ('ready', u'Собран'),
        ('done', u'Выпущен'),
        ('new', u'Новый')
    )

    name = models.CharField(max_length=255)
    date = models.DateTimeField()
    status = models.CharField(max_length=30, choices=statuses, default='new')
    description = models.CharField(max_length=1000, blank=True, null=True)
    project = models.ForeignKey(PM_Project, related_name='releases')
    active = models.BooleanField(default=True, blank=True)

    class Meta:
        app_label = 'PManager'


class PM_File_Category(models.Model):
    name = models.CharField(max_length=200)
    #    category = models.ManyToManyField('self', null=True, blank=True, related_name='childrens')
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')
    projects = models.ManyToManyField('PM_Project', null=True, blank=True, related_name='file_categories')

    class Meta:
        app_label = 'PManager'


class PM_Files(models.Model):
    file = models.FileField(max_length=400, upload_to=path_and_rename("projects", 'str(instance.projectId.id)'))
    authorId = models.ForeignKey(User, null=True)
    projectId = models.ForeignKey(PM_Project, null=True)
    category = models.ForeignKey(PM_File_Category, related_name="files", null=True, blank=True)
    versions = models.ManyToManyField('self', related_name="newVersions", null=True, blank=True)
    is_old_version = models.NullBooleanField(null=True, blank=True)
    date_create = models.DateTimeField(auto_now_add=True, blank=True)
    name = models.CharField(max_length=200, null=True)

    def __unicode__(self):
        s = unicode(self.file)
        if not s.startswith(u'media/'): s = u'media/' + s
        if not s.startswith(u'/'): s = u'/' + s
        return s

    def __str__(self):
        s = str(self.file)
        if not s.startswith('media/'): s = 'media/' + s
        if not s.startswith('/'): s = '/' + s
        return s

    def save(self, *args, **kwargs):
        if not self.name:
            import ntpath

            self.name = ntpath.basename(self.src)

        super(self.__class__, self).save(*args, **kwargs)

    @property
    def isPicture(self):
        return str(self).endswith('.jpg') or str(self).endswith('.gif') or str(self).endswith('.png')

    @property
    def src(self):
        url = self.__str__()
        if url.startswith('/'):
            url = url[1:]
        return '/protected/' + url

    @property
    def type(self):
        return str(self.file).split('.')[-1]

    @property
    def size(self):
        import os

        try:
            if os.path.isfile(self.file.path):
                size = os.path.getsize(os.path.join(os.path.dirname(__file__), '..' + self.src).replace('\\', '/'))
                if 10 ** 3 < size < 10 ** 6:
                    size = str(size / (10 ** 3)) + 'K'
                elif 10 ** 6 < size < 10 ** 9:
                    size = str(size / (10 ** 6)) + 'Mb'
                elif 10 ** 9 < size:
                    size = str(size / (10 ** 9)) + 'Gb'
                return size
        except Exception:
            pass
        return ''

    @property
    def hasOldVersions(self):
        return self.versions.all().count() > 0

    def addNewVersion(self, oFile):
        oFile.versions = copy.copy(self.versions.all())
        oFile.versions.add(self)

        if oFile.save():
            self.is_old_version = True
            self.save()
            return True

        return False

    def getJson(self):
        return {
            'type': self.type,
            'src': self.src,
            'isPicture': self.isPicture,
            'id': self.id,
            'name': self.name,
            'size': self.size,
            'date_create': self.date_create.strftime('%d.%m.%Y %H:%M:%S'),
            'hasOldVersions': self.hasOldVersions
        }

    class Meta:
        app_label = 'PManager'


class PM_Task_Status(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'PManager'


class PM_Milestone(models.Model):
    THRESHOLD_DANGER = 1.1
    THRESHOLD_WARNING = 1.3
    STATUS_DANGER = 'danger'
    STATUS_WARNING = 'warning'
    STATUS_NORMAL = 'success'
    crit_choices = (
        (1, u'Не критичная'),
        (2, u'Средняя'),
        (3, u'Критичная'),
    )
    name = models.CharField(max_length=255)
    date = models.DateTimeField(null=True, blank=True, default=datetime.datetime.now())
    date_create = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    critically = models.IntegerField(blank=True, null=True, default=2, choices=crit_choices)
    project = models.ForeignKey(PM_Project, related_name='milestones')
    overdue = models.BooleanField(blank=True)
    author = models.ForeignKey(User, related_name='createdMilestones', null=True, blank=True)
    token_price = models.FloatField(blank=True, null=True, default=0)
    description = models.TextField(null=True, blank=True)
    responsible = models.ManyToManyField(User, null=True, blank=True)
    closed = models.BooleanField(blank=True, default=False)
    confirmed = models.BooleanField(blank=True, default=False)
    is_request = models.BooleanField(blank=True, default=False)
    donated = models.BooleanField(blank=True, default=False)
    min_donate = models.FloatField(blank=True, null=True)
    conditioned_time = models.IntegerField(blank=True, null=True)

    def tasksOrderedByClose(self):
        return self.tasks.order_by('-closed')

    def userLiked(self, request):
        return LikesHits.userLiked(self, request)

    def canConfirm(self, user):
        return user.is_authenticated() and self.donations.filter(user=user).count()

    @staticmethod
    def check():
        milestones = PM_Milestone.objects.filter(
            overdue=False,
            date__lt=datetime.datetime.now()
        )

        for ms in milestones:
            ms.overdue = True
            ms.save()
            for user in ms.responsible.all():
                message = PM_Task_Message(
                    userTo=user,
                    text=u'Цель "' + ms.name + u'" просрочена',
                    code='MILESTONE_OVERDUE',
                    project=ms.project
                )
                message.save()

    def __unicode__(self):
        return self.name

    def get_donation_sum(self):
        sum = 0
        for d in self.donations.all():
            sum += d.sum

        return sum

    def status(self):
        from PManager.classes.datetime.work_time import WorkTime
        planTimeMax = self.tasks.filter(active=True, closed=0).values('resp_id').annotate(
            sumtime=Sum('planTime')).order_by('-sumtime')
        if planTimeMax:
            taskHours = planTimeMax[0]['sumtime']
            if not taskHours:
                return self.STATUS_NORMAL

            endDate = self.date
            if timezone.is_naive(self.date):
                endDate = timezone.make_aware(self.date, timezone.get_default_timezone())
            timeNeeded = WorkTime(startDateTime=datetime.datetime.now(), taskHours=taskHours * self.THRESHOLD_DANGER)
            if timeNeeded.endDateTime >= endDate:
                return self.STATUS_DANGER

            timeNeeded = WorkTime(startDateTime=datetime.datetime.now(), taskHours=taskHours * self.THRESHOLD_WARNING)
            if timeNeeded.endDateTime >= endDate:
                return self.STATUS_WARNING

        return self.STATUS_NORMAL

    def percent(self):
        planTimeTable = self.tasks.filter(active=True).values('closed').annotate(sumtime=Sum('planTime')).order_by(
            '-closed')
        if not planTimeTable:
            return 0
        if len(planTimeTable) == 1:
            return 100 if planTimeTable[0]['closed'] else 0
        if len(planTimeTable) > 1 and planTimeTable[1].get('sumtime', 0) > 0:
            return int(
                round(planTimeTable[0]['sumtime'] * 100 / (planTimeTable[0]['sumtime'] + planTimeTable[1]['sumtime']),
                      0))

        return 0

    class Meta:
        app_label = 'PManager'


class PM_Task(models.Model):
    MANAGER_ADDITION_PER_BUG = 0.1
    RESP_SUBSTRUCTION_PER_BUG = 0.05
    FEE = 0.1
    MAX_OVERTIME = 3

    bool_choices = (
        ('N', u'No'),
        ('Y', u'Yes'),
    )

    colors = (
        ('grey', u'Grey'),
        ('green', u'Green'),
        ('blue', u'Blue'),
        ('red', u'Red'),
        ('yellow', u'Yellow'),
        ('purple', u'Purple'),
        ('orange', u'Orange')
    )

    last_error = ''

    name = models.CharField(max_length=1000, verbose_name=u'Заголовок')
    text = models.TextField(validators=[MaxLengthValidator(7000)], verbose_name=u'Текст', blank=True, null=True)
    number = models.IntegerField()
    project = models.ForeignKey(PM_Project, null=True, blank=True, db_index=True, related_name='projectTasks')
    resp = models.ForeignKey(User, null=True, blank=True, related_name='todo')
    responsible = models.ManyToManyField(User, related_name='hisTasks', null=True, blank=True)
    author = models.ForeignKey(User, related_name='createdTasks', null=True, blank=True)
    lastModifiedBy = models.ForeignKey(User, related_name='modifiedBy', null=True, blank=True)
    status = models.ForeignKey(PM_Task_Status, related_name='tasksByStatus', null=True, blank=True,
                               verbose_name=u'Статус')
    observers = models.ManyToManyField(User, related_name='tasksLooking', null=True, blank=True)

    perhapsResponsible = models.ManyToManyField(User, related_name='hisTasksMaybe', null=True, blank=True)

    dateCreate = models.DateTimeField(auto_now_add=True, blank=True)
    dateModify = models.DateTimeField(auto_now=True, blank=True)
    dateClose = models.DateTimeField(blank=True, null=True)
    dateStart = models.DateTimeField(blank=True, null=True)
    deadline = models.DateTimeField(blank=True, null=True)

    milestone = models.ForeignKey(PM_Milestone, related_name='tasks', null=True, blank=True)
    onPlanning = models.BooleanField(blank=True)
    donate_exists = models.BooleanField(blank=True)
    donate_sum = models.FloatField(blank=True, default=0)
    planTime = models.FloatField(blank=True, null=True, default=0)
    realTime = models.BigIntegerField(blank=True, null=True)
    realDateStart = models.DateTimeField(blank=True, null=True)

    closed = models.BooleanField(blank=True, verbose_name=u'Закрыта')
    started = models.BooleanField(blank=True)
    wasClosed = models.BooleanField(blank=True)
    closedInTime = models.BooleanField(blank=True, default=False)
    public = models.BooleanField(blank=True)
    active = models.BooleanField(default=True, blank=True)

    priority = models.FloatField(default=0.5)
    critically = models.FloatField(default=0.5, verbose_name=u'Критичность')
    hardness = models.FloatField(default=0.5)
    reconcilement = models.FloatField(default=0.5)
    project_knowledge = models.FloatField(default=0.5)

    parentTask = models.ForeignKey('self', related_name="subTasks", null=True, blank=True, verbose_name=u'Контейнер')
    tags = generic.GenericRelation(ObjectTags)

    virgin = models.BooleanField(default=True, blank=True)
    viewedUsers = models.ManyToManyField(User, null=True, blank=True)

    files = models.ManyToManyField(PM_Files, related_name="fileTasks", null=True, blank=True)
    repeatEvery = models.IntegerField(verbose_name=u'Повторите', blank=True, null=True)

    currentTimer = False
    startedTimerExist = False

    color = models.CharField(max_length=100, choices=colors, null=True, blank=True, default='blue')

    release = models.ForeignKey(Release, blank=True, null=True, related_name='tasks')

    isParent = models.BooleanField(default=False, blank=True)
    winner = models.ForeignKey(User, null=True, blank=True, related_name='conquered')

    @property
    def url(self):
        return "/task_detail/?" + (
            ("id=" + str(self.id)) if self.parentTask else ("number=" + str(self.number))) + "&project=" + str(
            self.project.id)

    @property
    def donated(self):
        from tracker.settings import GIFT_USD_RATE
        donated = 0
        for m in self.donations.all():
            donated += m.sum or 0

        donated = donated * GIFT_USD_RATE

        return donated

    @property
    def asked(self):
        asked = 0
        qty = 0
        for m in self.messages.filter(requested_time_approved=True):
            qty += 1
            asked += m.requested_time

        if not qty:
            qty = 1

        asked = round(asked / qty)

        return asked

    @property
    def percent(self):
        return 100 if self.closed else 0

    def userLiked(self, request):
        return LikesHits.userLikedTask(self, request)

    def getWinner(self):
        winners = {}
        votes = {}
        winner = None
        for m in self.messages.filter(code='VOTE'):
            if not votes.get(m.userTo.id, None):
                votes[m.userTo.id] = 0
                winners[m.userTo.id] = m.userTo

            votes[m.userTo.id] += 1

        if len(votes):
            import operator
            sorted_votes = sorted(votes.items(), key=operator.itemgetter(1), reverse=True)
            winnerId = sorted_votes[0][0]
            winner = winners[winnerId]

        return winner

    def safeDelete(self):
        self.active = False
        self.save()
        if self.parentTask and self.parentTask.subTasks.filter(active=True).count() == 0:
            self.parentTask.isParent = False
            self.parentTask.save()

    def setIsInTime(self):
        if not self.deadline or self.deadline > timezone.make_aware(datetime.datetime.now(),
                                                                    timezone.get_current_timezone()):
            self.closedInTime = True
        else:
            self.closedInTime = False

    def Close(self, user):
        from django.contrib.contenttypes.models import ContentType

        logger = Logger()

        def increaseTagsForUser(userForTags, tagRelArray):
            for tagRel in tagRelArray:
                tagRelUser = ObjectTags.objects.filter(
                    tag=tagRel.tag,
                    object_id=userForTags.id,
                    content_type=ContentType.objects.get_for_model(user)
                )
                if tagRelUser:
                    tagRelUser = tagRelUser[0]
                else:
                    tagRelUser = ObjectTags(tag=tagRel.tag, content_object=userForTags)

                tagRelUser.weight = int(tagRelUser.weight) + 1
                tagRelUser.save()

        if self.donations.exists():
            if self.messages.filter(code='RESULT').exists():
                donatedUsers = User.objects.filter(pk__in=self.donations.values_list('user__id', flat=True))\
                    .exclude(pk__in=self.messages.filter(code='VOTE').values_list('author__id', flat=True))\
                    .exclude(pk=user.id)

                if donatedUsers.exists():
                    unvotedDonations = self.donations.filter(user__in=donatedUsers)
                    unvotedDonationSum = 0
                    for unvotedDonation in unvotedDonations:
                        unvotedDonationSum += unvotedDonation.sum

                    if unvotedDonationSum > float(self.donated) / 2:
                        self.last_error = 'Ask ' + ', '.join([u.last_name + ' ' +u.first_name for u in donatedUsers]) \
                                          + ' for voting before the closing.'

        if not self.last_error:
            self.winner = self.getWinner()
            closingDesc = 'Task closed'
            if self.donations.exists():
                from PManager.viewsExt.blockchain import blockchain_goal_confirmation_request
                if self.winner and self.winner.get_profile().blockchain_wallet:
                    blockchain_goal_confirmation_request(
                        user.username,
                        self.project.blockchain_name,
                        'opengift.io:task-' + str(self.id),
                        self.winner.get_profile().blockchain_wallet
                    )

                    closingDesc += ' (winner: ' + self.winner.last_name + ' ' + self.winner.first_name + \
                               ', prize: $' + str(round(self.donated * 0.85, 2)) + \
                               ', token holders fee: $' + str(round(self.donated * 0.1, 2)) + \
                               ', community fee: $' + str(round(self.donated * 0.05, 2)) + ')'

                else:
                    blockchain_goal_confirmation_request(
                        user.username,
                        self.project.blockchain_name,
                        'opengift.io:task-' + str(self.id),
                        ''
                    )

                    closingDesc += ' (no winner, all rewards were returned to the donors)'

            if not self.resp and user:
                self.resp = user

            self.closed = True
            self.critically = 0.5
            self.status = None
            self.dateClose = datetime.datetime.now()

            if not self.wasClosed and not self.subTasks.count():
                self.setCreditForTime()
                self.wasClosed = True

            tagRelArray = ObjectTags.objects.filter(
                object_id=self.id,
                content_type=ContentType.objects.get_for_model(PM_Task)
            ).all()

            for ob in self.observers.all():
                if ob.id != self.author.id and (not self.resp or ob.id != self.resp.id):
                    increaseTagsForUser(ob, tagRelArray)

            if self.resp and self.author.id != self.resp.id:
                increaseTagsForUser(self.resp, tagRelArray)

            redisSendTaskUpdate({
                'id': self.pk,
                'closed': True
            })

            self.save()
            self.systemMessage(closingDesc, user, 'TASK_CLOSE')

    def setCreditForTime(self):
        from PManager.models import Credit, PM_Achievement, PM_Task_Message, Fee
        import math

        allSum = 0
        allRealTime = 0
        # responsibles real time
        table_name = PM_Timer._meta.db_table
        if PM_Timer.objects.filter(task__id=self.id).exists():
            timers = PM_Timer.objects.raw(
                ( 'SELECT SUM(`seconds`) as summ, id, user_id FROM {}'
                ' WHERE `task_id`= %s' 
                ' GROUP BY user_id'.format(table_name)), [ self.id,]
            )
        else:
            timers = []

        bugsQty = self.messages.filter(bug=True).count()
        for obj in timers:
            ob = {}
            if obj.summ:
                cUser = User.objects.get(pk=int(obj.user_id))
                cUserProf = cUser.get_profile()

                if cUserProf.isEmployee(self.project) and cUser.id != self.author.id and cUser.is_active \
                        and cUserProf.is_outsource:

                    ob['time'] = round(float(obj.summ) / 3600., 2)

                    if self.planTime:
                        if ob['time'] > self.planTime:
                            if (ob['time'] - self.planTime) > self.MAX_OVERTIME:
                                ob['time'] = self.planTime + self.MAX_OVERTIME

                            ob['rating'] = -round(20 * (ob['time'] - self.planTime))
                            accCode = 'rating_minus'
                        else:
                            accCode = 'rating_plus'
                            ob['rating'] = 1
                            if not bugsQty:
                                ob['rating'] += 1

                        if accCode:
                            try:
                                acc = PM_Achievement.objects.get(code=accCode)
                                acc.addToUser(cUser)
                            except PM_Achievement.DoesNotExist:
                                pass

                    curUserRating = ob.get('rating', 0)

                    # set user rating
                    profResp = cUser.get_profile()
                    respFine = profResp.getFine()
                    if curUserRating != 0 and profResp.is_outsource:
                        obRating = None

                        if curUserRating < 0:
                            obRating = FineHistory(value=curUserRating, user=cUser)
                        elif curUserRating > 0:
                            if respFine < 0:
                                if -respFine >= curUserRating:
                                    obRating = FineHistory(value=curUserRating, user=cUser)
                                else:
                                    obRating = FineHistory(value=-respFine, user=cUser)
                                    ratingLeft = curUserRating + respFine

                                    if ratingLeft:
                                        ratingLeft = RatingHistory(value=ratingLeft, user=cUser)
                                        ratingLeft.save()
                            else:
                                obRating = RatingHistory(value=curUserRating, user=cUser)

                        if obRating:
                            obRating.save()

                    if ob['time']:
                        allRealTime += ob['time']

                        userBet = profResp.getBet(self.project)
                        if userBet:
                            curPrice = userBet * float(ob['time'])

                            if curPrice:
                                substruction = 0
                                if bugsQty:
                                    substruction = round(curPrice * self.RESP_SUBSTRUCTION_PER_BUG * bugsQty)
                                    curPrice -= substruction

                                allSum = allSum + curPrice

                                respFine = profResp.getFine()
                                fineSum = 0
                                if respFine:
                                    fineSum = - respFine * float(ob['time'])
                                    fee = Fee(
                                        user=profResp.user,
                                        value=fineSum,
                                        project=self.project,
                                        task=self
                                    )
                                    fee.save()

                                feeValue = math.floor(curPrice * self.FEE)

                                fee = Fee(
                                    user=profResp.user,
                                    value=feeValue,
                                    project=self.project,
                                    task=self
                                )
                                fee.save()

                                credit = Credit(
                                    user=profResp.user,
                                    value=curPrice - feeValue - fineSum,
                                    project=self.project,
                                    task=self,
                                    type='Resp real time',
                                    comment=(
                                                ('+' if curUserRating >= 0 else '') + str(
                                                    curUserRating) + u' к рейтингу') +
                                            ((' -' + str(substruction) + u' за ошибки') if substruction else u'')
                                )
                                credit.save()

        if allRealTime or self.planTime:
            if self.planTime:
                managers = PM_ProjectRoles.objects.filter(
                    project=self.project,
                    role__code='manager',
                    user__in=self.observers.all()
                )

                cManagers = 0
                aManagers = []
                for manager in managers:
                    if manager.user.get_profile().is_heliard_manager:
                        bet = manager.user.get_profile().getBet(self.project, None, manager.role.code)
                        if bet:
                            cManagers += 1
                            setattr(manager, 'bet', bet)
                            aManagers.append(manager)

                for manager in aManagers:
                    curTime = self.planTime * 1.0 / cManagers

                    if curTime:
                        bugQty = PM_Task_Message.objects.filter(author=manager, bug=True, task=self).count()
                        if bugQty:
                            curTime += curTime * self.MANAGER_ADDITION_PER_BUG * bugQty

                        bet = manager.user.get_profile().heliard_manager_rate
                        price = bet * float(curTime)
                        if price:
                            credit = Credit(
                                user=manager.user,
                                value=price,
                                project=self.project,
                                task=self,
                                type='Manager with bet'
                            )
                            credit.save()

                            allSum = allSum + price

            if allSum:
                # client
                clientComission = int(self.project.getSettings().get('client_comission', 0) or COMISSION)
                clientFeeSum = math.floor(allSum * clientComission / 100)

                if self.project.payer:
                    credit = Credit(
                        user=self.project.payer,
                        value=-allSum - clientFeeSum,
                        project=self.project,
                        task=self,
                        type='Client with comission'
                    )
                    credit.save()

                    if clientFeeSum:
                        fee = Fee(
                            user=self.project.payer,
                            value=clientFeeSum,
                            project=self.project,
                            task=self
                        )
                        fee.save()

    def Open(self):
        self.closed = False
        self.dateClose = None

        redisSendTaskUpdate({
            'id': self.pk,
            'closed': False
        })

        self.save()

    def Start(self):
        if not self.realDateStart:  # если до этого еще не была запущена
            self.realDateStart = datetime.datetime.now()  # заносим дату запуска
        self.started = True
        self.virgin = False
        self.save()

    def Stop(self):
        self.started = False
        self.save()

    def setPlanTime(self, val, request):
        from PManager.models.scrum import PM_MilestoneChanges
        if request.user.is_authenticated():
            if not self.onPlanning and self.canPMUserSetPlanTime(request.user.get_profile()):
                oldPlanTime = self.planTime or 0

                self.planTime = float(val)
                self.save()

                if self.milestone and oldPlanTime != self.planTime:
                    change = PM_MilestoneChanges(milestone=self.milestone, value=(self.planTime - oldPlanTime))
                    change.save()

            planTime, created = PM_User_PlanTime.objects.get_or_create(user=request.user, task=self)
            planTime.time = float(val)
            planTime.save()

        redisSendTaskUpdate({
            'id': self.pk,
            'planTime': self.planTime if self.onPlanning else float(val)
        })

    def saveTaskTags(self):
        from PManager.models.morphy import trackMorphy
        textManager = trackMorphy()

        tags = textManager.parseTags(self.name + u' ' + self.text)

        for k, tagInfo in tags.iteritems():
            try:
                tagId, created = Tags.objects.get_or_create(tagText=tagInfo["norm"])

                if tagId.id > 0:
                    tagObject, created = ObjectTags.objects.get_or_create(
                        tag=tagId,
                        object_id=self.id,
                        content_type=ContentType.objects.get_for_model(PM_Task)
                    )

                    tagObject.weight = int(tagInfo['weight'])
                    tagObject.content_object = self

                    tagObject.save()
            except MultipleObjectsReturned, Tags.MultipleObjectsReturned:
                pass

    def startTimer(self, user):
        if not self.currentTimer:
            try:
                self.currentTimer = PM_Timer.objects.get(task=self, dateEnd=None)
            except PM_Timer.DoesNotExist:
                self.currentTimer = PM_Timer(task=self, user=user, dateStart=datetime.datetime.now())
                self.currentTimer.save()

        redisSendTaskUpdate({
            'id': self.pk,
            'started': True,
            'startedTimerExist': True,
            'eventAuthor': self.currentTimer.user.id,
            'name': self.name,
            'url': self.url
        })

    def endTimer(self, user=None, comment=None):
        logger = Logger()

        if not self.currentTimer:
            try:
                self.currentTimer = PM_Timer.objects.get(task=self, dateEnd=None)
            except PM_Timer.DoesNotExist:
                return

        if self.currentTimer:
            user_id = self.currentTimer.user.id
            if not comment:
                self.currentTimer.delete()
            else:
                self.currentTimer.dateEnd = datetime.datetime.now()
                self.currentTimer.comment = comment
                delta = timezone.make_aware(self.currentTimer.dateEnd,
                                            timezone.get_default_timezone()) - self.currentTimer.dateStart
                self.currentTimer.seconds = delta.total_seconds()

                self.currentTimer.save()
                if not self.realTime: self.realTime = 0
                self.realTime = int(self.realTime)
                self.realTime = self.realTime + delta.seconds

                logger.log(self.currentTimer.user, 'DAILY_TIME', delta.seconds, self.project.id)

            redisSendTaskUpdate({
                'id': self.pk,
                'started': False,
                'startedTimerExist': False,
                'eventAuthor': user_id
            })
            self.save()

        return self

    @staticmethod
    def getAllTimeOfTasksWithSubtasks(aId):
        if not aId:
            return

        aTime = PM_Timer.getSumsOfTasks(aId)
        aTasksId = aTime.keys()
        timers = PM_Timer.objects.filter(
            Q(Q(task__in=aTasksId) | Q(task__parentTask_id__in=aTasksId)), dateEnd__isnull=True, dateStart__isnull=False
        ).values('dateStart', 'task_id', 'user_id', 'task__parentTask_id')
        now = timezone.make_aware(datetime.datetime.now(), timezone.get_default_timezone())

        for t in timers:
            delta = now - t['dateStart']
            aCurObj = aTime[t['task__parentTask_id']] if 'task__parentTask_id' in t and t[
                                                                                            'task__parentTask_id'] in aTime else \
                aTime[t['task_id']]
            if t['user_id'] not in aCurObj:
                aCurObj[t['user_id']] = 0

            aCurObj[t['user_id']] += delta.seconds

        return aTime

    def getAllTime(self):
        aTime = PM_Timer.getSumsOfTasks([self.id])
        return sum(aTime[self.id].values()) if self.id in aTime else 0

    def canPMUserView(self, pm_user):
        return pm_user.hasAccess(self, 'view')

    def canPMUserRemove(self, pm_user):
        if self.donated:
            return False

        return self.author and pm_user.user.id == self.author.id

    def canPMUserSetPlanTime(self, pm_user):
        return (not self.planTime and pm_user.isManager(self.project)) or not self.realDateStart and (
            pm_user.isManager(self.project) or
            int(self.author.id) == int(pm_user.user.id) or
            self.onPlanning or (
                # is responsible and planTime is empty
                hasattr(self.resp, 'id') and int(self.resp.id) == int(pm_user.user.id) and
                (not self.planTime or self.status and self.status.code == 'not_approved')
            )
        )

    def setChangedForUsers(self, user=None):
        self.viewedUsers.clear()
        if user and isinstance(user, User):
            self.viewedUsers.add(user)

    def isViewed(self, user):
        return user.id in [u.id for u in self.viewedUsers.all()]

    def createTaskContainer(self, user=None):
        container = PM_Task(
            name=self.name,
            project=self.project,
            author=self.author,
            dateCreate=self.dateCreate,
            # deadline=self.deadline,
            planTime=self.planTime,
            critically=self.critically,
            hardness=self.hardness,
            reconcilement=self.reconcilement,
            project_knowledge=self.project_knowledge,
            active=True
        )
        container.save()
        self.setParent(container.id)
        if user:
            container.setChangedForUsers(user)
        return container

    @staticmethod
    def createByString(taskName, currentUser, uploadedFiles, parent=None, project=None):
        import re
        from PManager.models.users import PM_User

        arTags = {
            u' for ': 'responsible',
            u' deadline ': 'deadline',
            u' estimate ': 'about',
            u' file ': 'file',
            u' author ': 'from'
        }

        # TODO: сделать обработку быстрых тегов
        arSaveFields = {}

        if project:
            arSaveFields['project'] = project

        arFiles = []

        if uploadedFiles:
            uploadedFiles = PM_Files.objects.filter(pk__in=uploadedFiles)
            for file in uploadedFiles:
                arFiles.append(file)

        resp = None
        if len(taskName) > 0:
            if taskName[-1] == u'!':
                taskName = taskName[:-1]
                arSaveFields['critically'] = 0.75

            for tagname, tag in arTags.iteritems():
                aritems = taskName.split(tagname)
                i = 0
                for tagSpliced in aritems:
                    i += 1
                    if tagSpliced[0] == '#':
                        tagSpliced = tagSpliced[1:tagSpliced.find('#', 1)]

                        if tag == 'responsible':
                            resp = PM_User.getOrCreateByEmail(tagSpliced, arSaveFields['project'], 'employee')

                        elif tag == 'deadline':
                            def dateFromTag(tag):
                                return {
                                    'today': datetime.datetime.today(),
                                    'tomorrow': datetime.datetime.today() + datetime.timedelta(days=1),
                                    'aftertomorrow': datetime.datetime.today() + datetime.timedelta(days=2),
                                    'week': datetime.datetime.today() + datetime.timedelta(days=7)
                                }.get(tag, None)

                            arSaveFields['deadline'] = dateFromTag(tagSpliced)
                        elif tag == 'about':
                            arSaveFields['planTime'] = int(tagSpliced)

                        elif tag == 'file':
                            file = PM_Files.objects.get(id=tagSpliced)
                            if file.id:
                                arFiles.append(file)

                        elif tag == 'from':
                            arSaveFields['author'] = PM_User.getOrCreateByEmail(tagSpliced, arSaveFields['project'],
                                                                                'client')

            for tagname, tag in arTags.iteritems():
                myRe = re.compile(tagname + ur'\#([^\#]+)\#', re.UNICODE)
                taskName = myRe.sub('', taskName).strip()

            taskName = taskName.split('///')
            arSaveFields['text'] = taskName[1] if len(taskName) > 1 else ''
            arSaveFields['name'] = taskName[0][:300] + "..." if (len(taskName) > 300) else taskName[0]

            if parent:
                try:
                    parentTask = PM_Task.objects.get(id=parent, active=True)
                    parentTask.isParent = True
                    parentTask.save()

                    qtySubtasks = parentTask.subTasks.filter(active=True).count()

                    if qtySubtasks == 0 and parentTask.realDateStart:
                        try:
                            curUserObj = User.objects.get(pk=currentUser.id)
                            arSaveFields['parentTask'] = parentTask.createTaskContainer(
                                curUserObj
                            )
                        except User.DoesNotExist:
                            return False

                    else:
                        arSaveFields['parentTask'] = parentTask

                except PM_Task.DoesNotExist:
                    pass

        if "author" not in arSaveFields:
            arSaveFields["author"] = currentUser

        task = PM_Task(**arSaveFields)

        if resp:
            task.resp = resp

            # если у юзера нет ролей в текущем проекте, назначаем его разработчиком
            if not resp.get_profile().hasRole(task.project, not_guest=True):
                resp.get_profile().setRole('employee', task.project)
                if resp.get_profile().is_outsource:
                    from PManager.models.agreements import Agreement
                    Agreement.objects.get_or_create(payer=task.project.payer, resp=resp)
                    # elif task.parentTask:
                    #     for resp in task.parentTask.responsible.all():
                    #         task.responsible.add(resp) #17.04.2014 task #553

        task.lastModifiedBy = currentUser
        # set deadline https://opengift.io/task_detail/?number=64&project=495

        if not task.deadline:
            days_offset = getattr(settings, "DEADLINE_DAYS", 15)
            two_weeks_date = timezone.now() + datetime.timedelta(days=days_offset)
            task.deadline = two_weeks_date

        task.save()

        for file in arFiles:
            task.files.add(file)

        task.observers.add(task.author)

        PM_Task.saveTaskTags(task)

        task.setChangedForUsers(currentUser)
        arEmail = []
        if task.resp:
            arEmail.append(task.resp.email if task.resp.email is not currentUser.email else None)

            task.sendTaskEmail('new_task', arEmail)

        return task

    def sendTaskEmail(self, type, arEmail, title=''):
        taskdata = {
            'task_url': self.url,
            'name': self.name,
            'text': self.text if self.text != self.name else '',
            'dateCreate': timezone.make_aware(datetime.datetime.now(), timezone.get_current_timezone()),
            'time': unicode(self.currentTimer),
            'author': self.author
        }

        sendMes = emailMessage(type,
                               {
                                   'task': taskdata
                               },
                               (title if title else 'Вас назначили ответственным в новой задаче!')
                               )

        try:
            sendMes.send(arEmail)
        except Exception:
            print 'Message is not sent'

    def getPrice(self, profile):
        bet = profile.getBet(self.project)

        if profile.isClient(self.project):
            pass
        elif profile.isEmployee(self.project):
            pass

    # should be removed, since deprecated
    @staticmethod
    def getListPrepare(tasks, add_tasks, join_project_name=False):
        from PManager.services.task_list import task_list_prepare
        return task_list_prepare(tasks, add_tasks, join_project_name)

    @staticmethod
    def getQtyForUser(user, project=None, addFilter={}):
        filterForUser = PM_Task.getQArgsFilterForUser(user, project)
        if project:
            filterForUser.append(Q(project=project))

        filterForUser.append(Q(**addFilter))
        try:
            return PM_Task.objects.filter(*filterForUser).distinct().count()
        except ValueError:
            return 0

    @staticmethod
    def getQArgsFilterForUser(user, project=None):
        from django.db.models import Count

        filterQArgs = []
        pm_user = None
        if user.is_authenticated():
            pm_user = user.get_profile()

        bExist = False
        if project:
            bExist = True
            # if pm_user.isManager(project):
            #     bExist = True
            # elif pm_user.isEmployee(project):
            #     subtasksSubQuery = PM_Task.objects.exclude(parentTask__isnull=True) \
            #         .filter(resp=user, closed=False).values('parentTask__id') \
            #         .annotate(dcount=Count('parentTask__id'))
            #     aExternalId = []
            #     for obj in subtasksSubQuery:
            #         aExternalId.append(obj['parentTask__id'])
            #
            #     filterQArgs.append((
            #         Q(onPlanning=True) | Q(author=user) | Q(resp=user) | Q(observers=user) | Q(
            #             id__in=aExternalId)
            #     ))
            #     bExist = True
            # elif pm_user.isGuest(project):
            #     filterQArgs.append(Q(observers=user))
            #     bExist = True

        if not bExist:
            # userProjects = user.get_profile().getProjects()
            if user.is_authenticated():
                mProjects = user.get_profile().managedProjects
                q = Q(author=user) | Q(resp=user) | Q(observers=user) | Q(project__in=mProjects)

                filterQArgs.append(
                    Q(q)
                )

        return filterQArgs

    @staticmethod
    def mergeFilterObjAndArray(obj, arr):
        for (k, v) in obj.iteritems():
            arr.append(Q(**{k: v}))
        return arr

    @staticmethod
    def getForUser(user, project, filter={}, filterQArgs=[], arOrderParams={}):
        from django.db.models import Count

        order_by = arOrderParams.get('order_by', 'closed')
        if user.is_authenticated():
            pm_user = user.get_profile()

        if 'id' in filter or 'pk' in filter:
            filter = {
                'id': filter['id'] if 'id' in filter else filter['pk']
            }
            filterQArgs = []

        excludeFilter = {}
        if 'bounty' in filter or not user.is_authenticated():
            filterQArgs += [Q(onPlanning=True, project__closed=False, project__locked=False)]
            if 'closed' not in filter:
                filter['closed'] = False

            if filter['closed'] == True:
                order_by = '-dateClose'

            if 'bounty' in filter:
                del filter['bounty']

            if 'exclude' in filter:
                excludeFilter = filter['exclude']
                del filter['exclude']
                # filter = {}
        else:
            filterQArgs += PM_Task.getQArgsFilterForUser(user, project)

            if 'exclude' in filter:
                excludeFilter = filter['exclude']
                del filter['exclude']

            filter['active'] = True

            # subtasks search
            if filter and not 'isParent' in filter and not 'parentTask' in filter and not 'id' in filter and not 'onlyParent' in arOrderParams:
                filterSubtasks = filter.copy()
                filterSubtasks['parentTask__isnull'] = False
                filterSubtasks['parentTask__active'] = True
                try:
                    subTasks = PM_Task.objects.filter(*filterQArgs, **filterSubtasks).values('parentTask__id').annotate(
                        dcount=Count('parentTask__id'))
                except ValueError:
                    subTasks = []
                aTasksIdFromSubTasks = [subtask['parentTask__id'] for subtask in subTasks]
            else:
                aTasksIdFromSubTasks = None

            filterQArgs = PM_Task.mergeFilterObjAndArray(filter, filterQArgs)

            if aTasksIdFromSubTasks:
                filterQArgs = [Q(*filterQArgs) | Q(
                    id__in=aTasksIdFromSubTasks)]  # old conditions array | ID of parent tasks of match subtasks
                filter = {}

        # import logging
        # logger = logging.getLogger('blockchain')
        # logger.debug(json.dumps(filter))
        # logger.debug(json.dumps(str(PM_Task.objects.filter(*filterQArgs, **filter).query)))
        #assert False, (str( PM_Task.objects.filter(*filterQArgs, **filter).query) )
        #import q; q([i.children for i in filterQArgs], filter)
        try:
            tasks = PM_Task.objects.filter(*filterQArgs, **filter).exclude(project__closed=True,
                                                                           project__locked=True).distinct()
        except ValueError:
            tasks = None

        if arOrderParams.get('group') == 'milestones':
            order = ['-milestone__date']
        else:
            order = []

        if type(order_by) == type([]):
            for i in order_by:
                order.append(i)
        else:
            order.append(order_by)

        order.append('-started')
        order.append('-critically')
        order.append('-dateStart')
        order.append('-dateClose')
        order.append('-id')
        if tasks is not None:
            tasks = tasks.order_by(*order)
            if excludeFilter:
                tasks = tasks.exclude(**excludeFilter)

            tasks = tasks.order_by(*order)

        return {
            'tasks': tasks,
            'filter': filterQArgs
        }

    @staticmethod
    def getSimilar(text, project):
        from PManager.models.morphy import trackMorphy
        SIMILARITY_PERCENT = 40

        def sortByTagsCount(task):
            return task.tagSimilarCount

        textManager = trackMorphy()

        parsedTags = textManager.parseTags(text)

        arText = []
        for k, tagInfo in parsedTags.iteritems():
            arText.append(tagInfo["norm"])

        min_similar_words = len(arText) * SIMILARITY_PERCENT / 100
        arTasks = []

        if arText:
            tags = Tags.objects.filter(tagText__in=arText)
            if tags.count() > 1:
                tasks = PM_Task.objects.filter(project=project, tags__tag__in=tags, active=True).distinct()
                for task in tasks:
                    iSimilarTagCount = task.tags.filter(tag__in=tags).count()
                    if iSimilarTagCount > min_similar_words:
                        setattr(task, 'tagSimilarCount', iSimilarTagCount)
                        arTasks.append(task)
                arTasks.sort(key=sortByTagsCount, reverse=True)

        return arTasks

    # deprecated, since brought by merge from another branch, something is changed?
    # see PManager.services.rating.get_user_quality_for_task
    def getUserQuality(self, userId):
        taskTagRelArray = ObjectTags.objects.filter(object_id=self.id,
                                                    content_type=ContentType.objects.get_for_model(self))

        arTagsId = [str(tagRel.tag.id) for tagRel in taskTagRelArray]

        userTagSums = {}
        if len(arTagsId) > 0:
            for obj1 in ObjectTags.objects.raw(
                                                                            'SELECT SUM(`weight`) as weight_sum, `id`, `object_id`, `content_type_id`' +
                                                                            ' from PManager_objecttags WHERE' +
                                                                    ' tag_id in (' + ', '.join(arTagsId) + ')' +
                                            ' AND content_type_id=' + str(ContentType.objects.get_for_model(User).id) +
                            ' GROUP BY object_id'):
                if obj1.content_object:
                    userTagSums[str(obj1.content_object.id)] = int(obj1.weight_sum)

            minTagCount, maxTagCount = False, 0

            for userId in userTagSums:
                if maxTagCount < userTagSums[userId]: maxTagCount = userTagSums[userId]
                if minTagCount > userTagSums[userId] or minTagCount == False: minTagCount = userTagSums[userId]

            currentRecommendedUser = None
            if maxTagCount > 0:
                for userId in userTagSums:
                    if minTagCount == maxTagCount:
                        userTagSums[userId] = 1 if userTagSums[userId] == minTagCount else 0
                    else:
                        userTagSums[userId] = float((int(userTagSums[userId]) - int(minTagCount))) / float(
                            (int(maxTagCount) - int(minTagCount)))
            return userTagSums[userId] if userId in userTagSums else 0
        return 0

    def getUsersEmail(self, excludeUsers=None):
        if not excludeUsers:
            excludeUsers = []

        arEmail = []
        if self.author and self.author.is_active and self.author.id not in excludeUsers:
            if self.author.email:
                arEmail.append(self.author.email)
            else:
                arEmail.append(self.author.username)

        if self.resp:
            if self.resp.id not in excludeUsers and self.resp.is_active:
                if self.resp.email:
                    arEmail.append(self.resp.email)
                else:
                    arEmail.append(self.resp.username)

        if not isinstance(self.observers, list):
            observers = self.observers.all()
        else:
            observers = self.observers

        for resp in observers:
            if resp.id not in excludeUsers and resp.is_active:
                if resp.email:
                    arEmail.append(resp.email)
                else:
                    arEmail.append(resp.username)

        return arEmail

    def setStatus(self, status):
        try:
            self.status = PM_Task_Status.objects.get(code=status)
            self.save()
        except PM_Task_Status.DoesNotExist:
            pass

    def setParent(self, taskId):
        try:
            parent = None
            if taskId and int(taskId) > 0:
                parent = PM_Task.objects.get(id=int(taskId), parentTask__isnull=True)
                lastSubTask = parent.subTasks.order_by('-number')
                parent.isParent = True
                parent.save()
            else:
                lastSubTask = PM_Task.objects.filter(project=self.project, parentTask__isnull=True).order_by('-number')

            lastNumber = 0
            if lastSubTask.count() and lastSubTask[0]:
                lastNumber = lastSubTask[0].number

            for task in self.subTasks.all():
                task.setParent(parent.id if parent else 0)

            self.number = lastNumber + 1
            self.parentTask = parent
            self.save()

            return self.number
        except PM_Task.DoesNotExist:
            return False

    # deprecated, since brought by merge from another branch, something is changed?
    # see PManager.services.rating.get_user_rating_for_task
    def getUserRating(self, user):
        assert user.id > 0

        userTagSums = {}
        taskTagRelArray = ObjectTags.objects.filter(object_id=self.id,
                                                    content_type=ContentType.objects.get_for_model(self))

        arTagsId = [str(tagRel.tag.id) for tagRel in taskTagRelArray]

        if len(arTagsId) > 0:
            for obj1 in ObjectTags.objects.raw(
                                                                    'SELECT SUM(`weight`) as weight_sum, `id`, `object_id`, `content_type_id` from PManager_objecttags WHERE tag_id in (' + ', '.join(
                                                                arTagsId) + ') AND object_id=' + str(
                                                user.id) + ' AND content_type_id=' + str(
                                ContentType.objects.get_for_model(User).id) + ' GROUP BY object_id'):
                if obj1.content_object:
                    userTagSums[str(obj1.content_object.id)] = int(obj1.weight_sum)

            return userTagSums.get(str(user.id), 0)
        return 0

    def systemMessage(self, text, user=None, code=None):
        message = PM_Task_Message(text=text, task=self, author=user, isSystemLog=True, code=code)
        message.save()
        redisSendLogMessage(message.getJson({
            'noveltyMark': True,
            'onlyForUsers': [message.author.id] + ([message.userTo.id] if message.userTo else [])
            if message.hidden else
            (
                [u.id for u in message.task.observers.all()] +
                [message.author.id] +
                [message.userTo.id] if message.userTo else [] +
                                                           [self.author.id] +
                                                           [self.resp.id] if self.resp else [] +
                                                                                            [r['user__id'] for r in
                                                                                             PM_ProjectRoles.objects.filter(
                                                                                                 project=self.project,
                                                                                                 role__code='manager'
                                                                                             ).values('user__id')]
            )
        }))

        return message

    def canEdit(self, user):
        return (
            user.is_superuser
            or
            (self.author and self.author.id == user.id)
            or
            (self.project and user.get_profile().isManager(self.project))
        )

    def save(self, *args, **kwargs):
        self.dateModify = datetime.datetime.now()
        if not self.project:
            if self.author:
                roles = self.author.userRoles.all()[:1]
                if roles and roles[0] and roles[0].project:
                    self.project = roles[0].project

        # if task is new, add number
        if not self.id:
            try:
                lastTaskInProject = PM_Task.objects.filter(project=self.project).order_by('-number')
                if self.parentTask:
                    lastTaskInProject = lastTaskInProject.filter(parentTask=self.parentTask)
                else:
                    lastTaskInProject = lastTaskInProject.filter(parentTask__isnull=True)

                lastTaskInProject = lastTaskInProject[0]

                self.number = int(lastTaskInProject.number) + 1 if lastTaskInProject.number else 1
            except:
                self.number = 1

        super(self.__class__, self).save(*args, **kwargs)

    def getJson(self):
        return {
            'name': self.name,
            'text': self.text,
            'number': self.number,
            'id': self.id,
            'project': {
                'id': self.project.id,
                'name': self.project.name
            }
        }

    def __str__(self):
        return (unicode(self.parentTask.name) + ' / ' if self.parentTask else '') + unicode(self.name)

    def __unicode__(self):
        return (unicode(self.parentTask.name) + ' / ' if self.parentTask else '') + unicode(self.name)

    class Meta:
        app_label = 'PManager'


class PM_Timer(models.Model):
    task = models.ForeignKey(PM_Task, db_index=True)
    dateStart = models.DateTimeField(auto_now_add=True, blank=True)
    dateEnd = models.DateTimeField(blank=True, null=True)
    user = models.ForeignKey(User, db_index=True)
    seconds = models.BigIntegerField(blank=True, null=True)
    comment = models.CharField(max_length=1000, blank=True, null=True)
    price = models.FloatField(blank=True, null=True)

    def __unicode__(self):
        timeTimer = self.getTime()
        if timeTimer['hours'] < 10: timeTimer['hours'] = u'0' + unicode(timeTimer['hours'])
        if timeTimer['minutes'] < 10: timeTimer['minutes'] = u'0' + unicode(timeTimer['minutes'])
        if timeTimer['seconds'] < 10: timeTimer['seconds'] = u'0' + unicode(timeTimer['seconds'])

        return unicode(timeTimer['hours']) + u':' + unicode(timeTimer['minutes']) + u':' + unicode(timeTimer['seconds'])

    def getTime(self):
        dateEnd = timezone.make_aware(datetime.datetime.now(),
                                      timezone.get_current_timezone()) if not self.dateEnd else self.dateEnd
        delta = None
        if self.seconds:
            delta = datetime.timedelta(seconds=int(self.seconds))
        else:
            try:
                delta = dateEnd - self.dateStart
            except TypeError:
                # if dateEnd is recently appended (not received from DB)
                if not timezone.is_aware(dateEnd):
                    dateEnd = timezone.make_aware(dateEnd, timezone.get_current_timezone())
                if self.dateStart:
                    delta = dateEnd - self.dateStart

        objTime = templateTools.dateTime.timeFromTimestamp(delta.total_seconds())

        return objTime

    @staticmethod
    def getSumsOfTasks(aTaskId):
        if not aTaskId:
            return

        timers = PM_Timer.objects.filter(task_id__in=aTaskId).values('task_id', 'user_id').annotate(summ=Sum('seconds'))
        allTime = {}
        for timer in timers:
            if timer['task_id'] not in allTime:
                allTime[timer['task_id']] = {}

            allTime[timer['task_id']][timer['user_id']] = timer['summ'] if timer['summ'] else 0

        aSubtasksByTask = dict()
        subTasks = PM_Task.objects.filter(parentTask__in=aTaskId, virgin=False, active=True).values('id',
                                                                                                    'parentTask_id')

        for s in subTasks:
            if s['parentTask_id'] not in aSubtasksByTask:
                aSubtasksByTask[s['parentTask_id']] = []

            aSubtasksByTask[s['parentTask_id']].append(s['id'])

        for taskId in aSubtasksByTask:
            if not taskId in allTime:
                allTime[taskId] = {}
            timers = PM_Timer.objects.filter(task_id__in=aSubtasksByTask[taskId]).values('task_id', 'user_id').annotate(
                summ=Sum('seconds'))
            for t in timers:
                if t['user_id'] not in allTime[taskId]:
                    allTime[taskId][t['user_id']] = 0

                allTime[taskId][t['user_id']] += t['summ'] if t['summ'] else 0

        return allTime

    class Meta:
        app_label = 'PManager'


class PM_Properties(models.Model):
    code = models.CharField(max_length=255, null=True)
    name = models.CharField(max_length=255)

    class Meta:
        app_label = 'PManager'


class PM_Property_Values(models.Model):
    propertyId = models.ForeignKey(PM_Properties)
    value = models.CharField(max_length=1000)
    taskId = models.ForeignKey(PM_Task)

    class Meta:
        app_label = 'PManager'


class PM_TaskShareDonations(models.Model):
    project = models.ForeignKey(PM_Project, related_name="promisedShares")
    amount = models.FloatField()
    task = models.ForeignKey(PM_Task, related_name="promisedShares")
    author = models.ForeignKey(User, related_name="promisedShares")

    class Meta:
        app_label = 'PManager'


class PM_Task_Message(models.Model):
    text = models.CharField(max_length=10000)
    author = models.ForeignKey(User, related_name="outputMessages", null=True, blank=True, db_index=True)
    dateCreate = models.DateTimeField(auto_now_add=True, blank=True)
    dateModify = models.DateTimeField(auto_now=True, blank=True, null=True)
    modifiedBy = models.ForeignKey(User, null=True, blank=True)
    task = models.ForeignKey(PM_Task, null=True, related_name="messages", db_index=True)
    project = models.ForeignKey(PM_Project, null=True, db_index=True)
    commit = models.CharField(max_length=42, null=True, blank=True)
    userTo = models.ForeignKey(User, null=True, related_name="incomingMessages", blank=True, db_index=True)
    files = models.ManyToManyField(PM_Files, related_name="msgTasks", null=True, blank=True)
    filesExist = models.BooleanField(default=False, db_index=True)
    hidden = models.BooleanField(default=False)
    hidden_from_clients = models.BooleanField(default=False)
    hidden_from_employee = models.BooleanField(default=False)
    isSystemLog = models.BooleanField(blank=True)
    code = models.CharField(max_length=255, null=True, blank=True)
    read = models.BooleanField(blank=True)
    todo = models.BooleanField(blank=True, db_index=True)
    checked = models.BooleanField(blank=True, db_index=True)
    bug = models.BooleanField(blank=True, db_index=True)
    solution = models.BooleanField(default=False)
    vote = models.BooleanField(default=False)
    requested_time = models.IntegerField(blank=True, null=True)
    donated = models.FloatField(blank=True, null=True)
    jira_integration_id = models.CharField(max_length=255, blank=True, null=True)
    jira_issue_id = models.IntegerField(null=True, blank=True)
    requested_time_approved = models.BooleanField(default=False)
    requested_time_approved_by = models.ForeignKey(User, null=True, blank=True, related_name="approvedTimeRequests")
    requested_time_approve_date = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        return self.text

    def save(self, *args, **kwargs):
        if not self.project and self.task:
            if not isinstance(self.task, PM_Task):
                try:
                    self.task = PM_Task.objects.get(pk=self.task)
                except PM_Task.DoesNotExist:
                    return False

            self.project = self.task.project

        if self.author and not self.author.get_profile().hasRole(self.project):
            self.author.get_profile().setRole('guest', self.project)

        super(self.__class__, self).save(*args, **kwargs)

    @classmethod
    def create_commit_message(cls, df, author, task):

        return cls.objects.create(text=df.message,
                                  author=author,
                                  task=task,
                                  commit=df.hash,
                                  project=task.project,
                                  code="GIT_COMMIT"
                                  )

    def updateFromRequestData(self, data, user):
        changed = False
        if 'checked' in data and self.checked != bool(int(data['checked'])):
            self.checked = bool(int(data['checked']))
            changed = True

        if self.canEdit(user):
            if 'todo' in data and self.todo != bool(int(data['todo'])):
                self.todo = bool(int(data['todo']))
                changed = True
            if 'bug' in data and self.bug != bool(int(data['bug'])):
                self.bug = bool(int(data['bug']))
                changed = True
            if 'hidden_from_employee' in data:
                r = not not data['hidden_from_employee']
                if self.hidden_from_employee != r:
                    self.hidden_from_employee = r
                    changed = True
            if 'hidden_from_clients' in data:
                r = bool(data['hidden_from_clients'])
                if self.hidden_from_clients != r:
                    self.hidden_from_clients = r
                    changed = True

            if 'text' in data and not changed:
                self.text = data['text']
                changed = True

            if 'task' in data:
                try:
                    self.task = PM_Task.objects.get(pk=int(data['task']))
                    changed = True
                except (PM_Task.DoesNotExist, TypeError):
                    pass

        return changed

    def getJson(self, addParams=None, cur_user=None):
        from django.utils.html import escape
        from PManager.viewsExt.tools import TextFilters, taskExtensions
        from PManager.templatetags.thumbnail import thumbnail

        if not addParams:
            addParams = {}

        profileAuthor = self.author.get_profile() if self.author else None
        cur_profile = cur_user.get_profile() if cur_user else None
        if self.code == 'SET_PLAN_TIME' and cur_profile:
            if self.task.onPlanning and cur_profile.id != profileAuthor.id:
                p = self.task.project

                if cur_profile and (
                                cur_profile.user.id == self.project.payer.id
                        or
                            cur_profile.isEmployee(p)
                ):
                    try:
                        planTime = PM_User_PlanTime.objects.get(
                            user=self.author,
                            task=self.task
                        )

                        if profileAuthor.isEmployee(p):
                            bet = cur_profile.getBet(self.project, None, 'client') \
                                  or self.author.get_profile().getBet(self.project, None, 'employee')

                        elif profileAuthor.isClient(p):
                            bet = cur_profile.getBet(self.project, None, 'employee') \
                                  or self.author.get_profile().getBet(self.project, None, 'client')

                        else:
                            bet = cur_profile.getBet(self.project) \
                                  or self.author.get_profile().getBet(self.project)

                        addParams.update({
                            'confirmation': (
                                '<div>'
                                # '<p>Стоимость задачи составит <b>' + str(planTime.time * bet) + ' руб.</b></p>'
                                '<a class="button orange-button" href="' + self.task.url + '&confirm=' + str(
                                    self.id) + '" ' +
                                '" class="js-confirm-estimate agree-with-button">Choose responsible</a></div>'
                            )
                        })

                    except PM_User_PlanTime.DoesNotExist:
                        pass

        elif self.code == 'TIME_REQUEST':
            if not self.requested_time_approved:
                if cur_profile and (
                                cur_profile.user.id == self.project.payer.id or cur_profile.isManager(self.project)):
                    addParams.update({
                        'confirmation': (
                            '<div class="message-desc-right"><a class="btn" href="' + self.task.url + '&confirm=' + str(
                                self.id) + '" ' +
                            '" class="js-confirm-estimate agree-with-button">Money request: $' + str(
                                self.requested_time) + '</a></div>'
                        )
                    })
            else:
                d = self.requested_time_approve_date
                addParams.update({
                    'confirmation': (
                        u'<div class="message-desc-right">' +
                        unicode(
                            self.requested_time_approved_by.last_name + ' ' + self.requested_time_approved_by.first_name if
                            self.requested_time_approved_by else '') +
                        u' set cost <b>' +
                        unicode(self.requested_time) + u'$.</b> at <b>' +
                        unicode(templateTools.dateTime.convertToSite(d) if d.tzinfo is not None else 'now') +
                        u'</b></div>'
                    )
                })

        addParams.update({
            'id': self.id,
            'userTo': {
                'id': self.userTo.id,
                'name': self.userTo.last_name + ' ' + self.userTo.first_name
            } if self.userTo else {},
            'task': {
                'id': self.task.id,
                'name': self.task.name,
                'url': self.task.url,
                'parent': {
                    'id': self.task.parentTask.id,
                    'name': self.task.parentTask.name,
                    'url': self.task.parentTask.url,
                } if self.task.parentTask else None
            } if self.task else {},
            'code': self.code,
            'text': self.text,
            'date': templateTools.dateTime.convertToSite(timezone.localtime(self.dateCreate)),
            'files': taskExtensions.getFileList(self.files.all()),
            # 'hidden_from_clients': self.hidden_from_clients,
            # 'hidden_from_responsible': self.hidden_from_responsible,
            'hidden': self.hidden,
            'system': self.isSystemLog,
            'todo': self.todo,
            'checked': self.checked,
            'bug': self.bug,
            'project': {
                'id': self.project.id,
                'name': self.project.name,
                'url': '/project/' + str(self.project.id) + '/tasks/'
            } if self.project else None,
            'author': {
                'id': self.author.id,
                'name': self.author.first_name,
                'last_name': self.author.last_name,
                'username': self.author.username,
                'avatar': profileAuthor.avatarSrc,
                'avatar_color': profileAuthor.avatar_color
            } if self.author else {},
            'modifiedBy': {
                'last_name': self.modifiedBy.last_name,
                'first_name': self.modifiedBy.first_name
            } if self.modifiedBy else {},
            'dateModify': templateTools.dateTime.convertToSite(
                timezone.localtime(self.dateModify)) if self.dateModify else ''
        })

        if self.author and profileAuthor.avatarSrc:
            addParams.update({
                'avatar': thumbnail(profileAuthor.avatarSrc, '75x75', 3)
            })
        if self.code == 'GIT_COMMIT':
            addParams.update({
                'commit': self.commit,
                "canEdit": False,
                "canDelete": False
            })
            if cur_user:
                addParams.update({
                    "canView": self.canView(cur_user),
                })
        return addParams

    def canEdit(self, user):
        return (
            (self.author and self.author.id == user.id)
        )

    def canDelete(self, user):
        prof = user.get_profile()
        return self.author and self.author.id == user.id or prof.isManager(self.task.project)

    def canView(self, user):
        if not user:
            return False

        if self.author and self.author.id == user.id:
            return True

        if self.userTo and self.userTo.id == user.id:
            return True

        prof = user.get_profile()
        if user.is_superuser and prof.hasRole(self.task.project):
            return True

        if self.hidden:
            return False

        if prof.isManager(self.task.project):
            return True

        if self.task.resp and self.task.resp.id == user.id:
            return True

        if prof.isEmployee(self.task.project) and \
                        user.id in [u.id for u in self.task.observers.all()]:
            return True

        return (
            self.task.onPlanning and prof.hasRole(self.project, not_guest=True)
        )
        # todo: добавить про hidden_from_clients и from_employee

    def getUsersForNotice(self):
        pass

    def safeDelete(self):
        self.delete()
        return True

    class Meta:
        app_label = 'PManager'


class PM_Role(models.Model):
    code = models.CharField(max_length=100)
    name = models.CharField(max_length=500)
    tracker = models.ForeignKey(PM_Tracker)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'PManager'


class PM_ProjectRoles(models.Model):
    type_choices = (
        ('real_time', u'За реальное время'),
        ('plan_time', u'За плановое время'),
        ('fix', u'Фиксированнаяза проект'),
    )
    user = models.ForeignKey(User, related_name='userRoles')
    project = models.ForeignKey(PM_Project, related_name='projectRoles')
    role = models.ForeignKey(PM_Role)
    rate = models.IntegerField(null=True, blank=True)
    payment_type = models.CharField(max_length=100, default='real_time', choices=type_choices)

    def __unicode__(self):
        return self.role.name + ' ' + self.project.name

    def isLastRequiredRole(self):
        lastRequiredRoleCode = 'manager'
        return self.role.code == lastRequiredRoleCode and \
               not PM_ProjectRoles.objects.filter(
                   project=self.project,
                   role__code=lastRequiredRoleCode
               ).exclude(id=self.id).exists()

    def safeDelete(self):
        if self.isLastRequiredRole():
            return False

        self.delete()
        return True

    class Meta:
        app_label = 'PManager'


class listManager:
    taskId = None
    modelClass = models

    def __init__(self, modelClass):
        self.modelClass = modelClass

    def validate(self, val, validator):
        if callable(validator):
            return validator(val)

    def validateInt(self, val):
        print 'int'
        val = int(val)
        return val

    def validateStr(self, val):
        print 'str'
        return val

    def validateFloat(self, val):
        print 'float'
        return val

    def validateDate(self, val):
        print 'date'
        return val

    def validateModel(self, val):
        print 'model'
        return val

    def validateUser(self, val):
        print 'user'
        return val

    def parseFilter(self, filter):
        if filter and isinstance(filter, dict):
            tempFilter = copy.deepcopy(filter)

            for field, val in tempFilter.iteritems():
                fitField = field[:]
                if '__' in fitField:
                    fitField = fitField[:fitField.index('__')]

                obj = self.modelClass({fitField: val})
                for i in obj._meta.fields:
                    field_name = i.get_attname()
                    if field_name == fitField or field_name == (fitField + '_id'):
                        try:
                            if field_name == (fitField + '_id'):
                                i.clean(val.id, self.modelClass())
                            else:
                                i.clean(val, self.modelClass())
                        except Exception:
                            del filter[field]  # validation error
        return filter


class PM_User_PlanTime(models.Model):
    user = models.ForeignKey(User)
    task = models.ForeignKey(PM_Task)
    time = models.FloatField(blank=True, null=True)

    def __unicode__(self):
        return self.user.username + ' ' + self.task.name

    def hour_rate(self):
        profile = self.user.get_profile()
        return profile.sp_price + profile.getRating(self.task.project)

    def total_cost(self):
        return self.time * self.hour_rate()

    class Meta:
        app_label = 'PManager'


class PM_Reminder(models.Model):
    task = models.ForeignKey(PM_Task)
    date = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name=u'Напоминание')
    user = models.ForeignKey(User)

    def __unicode__(self):
        return unicode(self.date.strftime('%d.%m.%Y %H:%M:%S'))

    class Meta:
        app_label = 'PManager'


class RatingHistory(models.Model):
    value = models.FloatField(blank=True, verbose_name=u'Рейтинг', default=0)
    user = models.ForeignKey(User, blank=True, verbose_name=u'Пользователь', db_index=True)
    dateCreate = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        app_label = 'PManager'


class FineHistory(models.Model):
    value = models.FloatField(blank=True, verbose_name=u'Штраф', default=0)
    user = models.ForeignKey(User, blank=True, verbose_name=u'Пользователь', db_index=True)
    dateCreate = models.DateTimeField(auto_now_add=True, blank=True)

    def __str__(self):
        return str(self.value) + ' ' + str(self.user)

    class Meta:
        app_label = 'PManager'


# SIGNALS

def setActivityOfMessageAuthor(sender, instance, created, **kwargs):
    if instance.author:
        prof = instance.author.get_profile()
        prof.last_activity_date = datetime.datetime.now()
        prof.save()


def setOnlySolution(sender, instance, **kwargs):
    if instance.solution:
        instance.code = u"SOLUTION"
        try:
            solution_messages_old = PM_Task_Message.objects.filter(code=u"SOLUTION", project=instance.task.project)
            for message in solution_messages_old:
                message.solution = False
                message.code = None
                message.save()
        except (PM_Task_Message.DoesNotExist, ValueError) as e:
            pass


def remove_git(sender, instance, **kwargs):
    from tracker.settings import USE_GIT_MODULE
    from PManager.classes.git.gitolite_manager import GitoliteManager
    if USE_GIT_MODULE:
        if instance.repository and GitoliteManager.repository_exists(instance.repository):
            GitoliteManager.remove_repo(instance)


def update_git(sender, instance, **kwargs):
    from tracker.settings import USE_GIT_MODULE
    from PManager.classes.git.gitolite_manager import GitoliteManager
    from PManager.models.interfaces import AccessInterface
    if USE_GIT_MODULE:
        if instance.repository and not GitoliteManager.repository_exists(instance.repository):
            GitoliteManager.add_repo(instance, instance.author)
            AccessInterface.create_git_interface(instance)
        else:
            if instance.repository:
                GitoliteManager.regenerate_access(instance)


def rewrite_git_access(sender, instance, **kwargs):
    from tracker.settings import USE_GIT_MODULE
    from PManager.classes.git.gitolite_manager import GitoliteManager
    try:
        project = instance.project
    except PM_Project.DoesNotExist:
        return

    if isinstance(instance.project, PM_Project):
        project = instance.project
    else:
        try:
            project = PM_Project.objects.get(pk=int(instance.project))
        except Exception:
            pass

    if USE_GIT_MODULE and project and project.repository:
        GitoliteManager.regenerate_access(project)


def check_task_save(sender, instance, **kwargs):
    # При каждом сохранении задачи проверка, укладывается ли ответственный в свои задачи. Если нет, вывести сообщение.
    from PManager.services.check_milestone import check_milestones
    task = instance
    if not task.resp or task.closed:
        return

    try:
        origin = PM_Task.objects.get(id=task.id)

        if (
                                task.critically == origin.critically and
                                task.planTime == origin.planTime and
                            (task.milestone.id if task.milestone else None) == (
                                origin.milestone.id if origin.milestone else None) and
                        (task.resp.id if task.resp else None) == (origin.resp.id if origin.resp else None)
        ):
            return
    except PM_Task.DoesNotExist:
        origin = {}

    overdueMilestones = check_milestones(task)
    if not overdueMilestones:
        return
    else:
        # task.critically = 0
        # Send message
        template = u'При изменении данной задачи '
        if task.lastModifiedBy == task.resp:
            template += u'вы не уложитесь в срок по '
        else:
            template += task.resp.last_name + u' ' + task.resp.first_name + u' не будет укладываться в срок по '

        if len(overdueMilestones) > 1:
            template += u'следующим целям:'
            for milestone in overdueMilestones:
                template += "\n" + milestone['project__name'] + u': ' + milestone['name'] + ' '

        else:
            template += u'цели ' + overdueMilestones[0]['project__name'] + u': ' + overdueMilestones[0]['name']

        template += "\n" + u'Измените критичность или ответственного задачи, или сдвиньте сроки цели.'

        secondsAgo = datetime.datetime.now() - datetime.timedelta(seconds=5)
        secondsAgo = timezone.make_aware(secondsAgo, timezone.get_default_timezone())

        lastMessages = PM_Task_Message.objects.filter(
            userTo=task.lastModifiedBy, author=task.resp,
            code='WARNING', text=template, dateCreate__gt=secondsAgo
        ).exists()  # Проверка на дублирование

        if not lastMessages:
            message = PM_Task_Message(text=template, task=task, project=task.project, author=task.resp,
                                      userTo=task.lastModifiedBy, code='WARNING', hidden=True)
            message.save()
            responseJson = message.getJson()

            mess = RedisMessage(service_queue,
                                objectName='comment',
                                type='add',
                                fields=responseJson
                                )
            mess.send()


post_save.connect(rewrite_git_access, sender=PM_ProjectRoles)
post_delete.connect(rewrite_git_access, sender=PM_ProjectRoles)
post_save.connect(update_git, sender=PM_Project)
pre_delete.connect(remove_git, sender=PM_Project)
post_save.connect(setActivityOfMessageAuthor, sender=PM_Task_Message)
pre_save.connect(setOnlySolution, sender=PM_Task_Message)
pre_save.connect(check_task_save, sender=PM_Task)
