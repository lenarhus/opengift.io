# -*- coding:utf-8 -*-
__author__ = 'Gvammer'
from django.db import models
from django.contrib.auth.models import User
from PManager.models.tasks import PM_Tracker, PM_ProjectRoles, PM_Role, PM_Project, RatingHistory, FineHistory
from PManager.models.achievements import PM_User_Achievement, PM_Project_Achievement
from PManager.models.payments import Credit
from PManager.viewsExt import headers
from PManager.viewsExt.tools import emailMessage
from django.db.models.signals import post_save, pre_delete
from PManager.customs.storages import path_and_rename
from django.db import connection
from django.db.models import Sum
from sorl.thumbnail import get_thumbnail


class Specialty(models.Model):
    name = models.CharField(max_length=500)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='subspecialties')
    connected = models.ManyToManyField('self', blank=True, null=True, related_name="siblings")

    def __str__(self):
        return self.name or ''

    def __unicode__(self):
        return self.name or ''

    def getPercent(self):
        import random
        return random.randint(0, 100)

    class Meta:
        app_label = 'PManager'


def get_random_color():
    import random

    v = random.randint(0, len(PM_User.color_choices) - 1)
    return PM_User.color_choices[v][0]


class PM_User(models.Model):
    color_choices = (
        ('#DA70D6', '#DA70D6'),
        ('#9400D3', '#9400D3'),
        ('#6495ED', '#6495ED'),
        ('#4169E1', '#4169E1'),
        ('#87CEEB', '#87CEEB'),
        ('#008080', '#008080'),
        ('#EEE8AA', '#EEE8AA'),
        ('#F0E68C', '#F0E68C'),
        ('#DCDCDC', '#DCDCDC'),
        ('#708090', '#708090'),
        ('#eed5b7', '#eed5b7'),
        ('#ffdead', '#ffdead'),
        ('#e0eee0', '#e0eee0'),
        ('#836fff', '#836fff'),
        ('#00ee76', '#00ee76'),
        ('#00cd66', '#00cd66'),
        ('#76ee00', '#76ee00'),
        ('#bcee68', '#bcee68'),
        ('#eedc82', '#eedc82'),
        ('#cd5555', '#cd5555'),
        ('#ab82ff', '#ab82ff'),
    )

    OPENGIFTER = 'opengifter'
    DONATOR = 'donator'
    BACKER = 'backer'

    level_choices = (
        (DONATOR, 'Donator'),
        (BACKER, 'Backer'),
        (OPENGIFTER, 'OpenGifter'),
    )

    level_sum = {
        DONATOR: 1000,
        BACKER: 10000,
        OPENGIFTER: 50000,
    }

    user = models.OneToOneField(User, db_index=True, related_name='profile')
    second_name = models.CharField(max_length=100, null=True, blank=True, verbose_name=u'Second name')
    trackers = models.ManyToManyField(PM_Tracker, null=True)
    icq = models.CharField(max_length=70, null=True, blank=True)
    paypal = models.CharField(max_length=270, null=True, blank=True,
                              verbose_name=u'Paypal account (for money receiving from OpenGift Exchange)')
    btc_wallet = models.CharField(max_length=270, null=True, blank=True, verbose_name=u'BTC wallet')
    skype = models.CharField(max_length=70, null=True, blank=True, verbose_name=u'Skype')
    telegram = models.CharField(max_length=70, null=True, blank=True, verbose_name=u'Telegram account')
    linkedin = models.CharField(max_length=70, null=True, blank=True, verbose_name=u'Linkedin account')
    facebook = models.CharField(max_length=70, null=True, blank=True, verbose_name=u'Facebook account')
    eth = models.CharField(max_length=100, null=True, blank=True, verbose_name=u'Eth account')
    tokens_to_buy = models.CharField(max_length=70, null=True, blank=True, verbose_name=u'Tokens to buy')
    phoneNumber = models.CharField(max_length=20, null=True, blank=True, verbose_name=u'Phone number')
    documentNumber = models.CharField(max_length=10, null=True, blank=True, verbose_name=u'Серия и номер паспорта')
    documentIssueDate = models.DateTimeField(blank=True, null=True, verbose_name=u'Дата выдачи')
    documentIssuedBy = models.CharField(max_length=255, blank=True, null=True, verbose_name=u'Кем выдан')
    # docIssuedBy = models.CharField(max_length=255, blank=True, null=True, verbose_name=u'Кем выдан')
    order = models.CharField(max_length=255, blank=True, null=True, verbose_name=u'Лицевой счет')
    bank = models.CharField(max_length=255, blank=True, null=True, verbose_name=u'Банк')
    bik = models.CharField(max_length=255, blank=True, null=True, verbose_name=u'БИК')
    referrer = models.CharField(max_length=255, blank=True, null=True, verbose_name=u'Referrer')
    hackathon_registered = models.CharField(max_length=255, blank=True, null=True, verbose_name=u'Hackathon')
    github = models.CharField(max_length=255, blank=True, null=True, verbose_name=u'GitHub')
    hackathon_reg_date = models.DateTimeField(blank=True, null=True, verbose_name=u'Hackathon date')

    birthday = models.DateTimeField(blank=True, null=True)
    avatar = models.ImageField(blank=True, upload_to=path_and_rename("users"))
    sp_price = models.IntegerField(blank=True, null=True, default=0, verbose_name=u'Желаемая ставка')

    premium_till = models.DateTimeField(blank=True, null=True, verbose_name=u'Оплачен до')
    verification_code = models.CharField(max_length=100, blank=True, null=True)
    paid = models.IntegerField(blank=True, null=True, default=0)  # todo: deprecated
    specialty = models.ForeignKey(Specialty, blank=True, null=True)  # TODO: deprecated
    specialties = models.ManyToManyField(Specialty, blank=True, null=True, related_name='profiles',
                                         verbose_name=u'Специальности')
    # all_sp = models.IntegerField(null=True,blank=True)
    avatar_color = models.CharField(blank=True, null=True, default=get_random_color, choices=color_choices,
                                    max_length=20)

    # account_total = models.IntegerField(blank=True, null=True, verbose_name='Счет')
    # rating = models.FloatField(blank=True, null=True, verbose_name='Рейтинг', default=0)
    last_activity_date = models.DateTimeField(null=True, blank=True)

    is_outsource = models.BooleanField(blank=True, verbose_name=u'Аутсорс', default=False)
    is_bc_user = models.BooleanField(blank=True, verbose_name=u'Blockchain user', default=False)
    is_heliard_manager = models.BooleanField(blank=True, verbose_name=u'Менеджер Heliard', default=False)
    in_whitelist = models.BooleanField(blank=True, verbose_name=u'In whitelist', default=False)
    in_promo = models.BooleanField(blank=True, verbose_name=u'In Promo', default=False)
    heliard_manager_rate = models.FloatField(blank=True, null=True, verbose_name=u'Ставка менеджера')
    overdraft = models.IntegerField(blank=True, null=True, verbose_name=u'Максимальный овердрафт')

    hoursQtyPerDay = models.IntegerField(blank=True, null=True, verbose_name=u'Максимальное кол-во часов в день')
    blockchain_key = models.CharField(blank=True, null=True, max_length=2000)
    blockchain_cert = models.CharField(blank=True, null=True, max_length=2000)
    blockchain_wallet = models.CharField(blank=True, null=True, max_length=100)
    opengifter_level = models.CharField(blank=True, null=True, max_length=100, choices=level_choices)
    github_id = models.CharField(max_length=255, null=True, blank=True)
    jira_account = models.CharField(max_length=255, null=True, blank=True)

    @property
    def rating(self):
        rAll = RatingHistory.objects.filter(
            user=self.user
        ).aggregate(Sum('value'))
        return rAll['value__sum'] or 0

    @property
    def account_total(self):
        from PManager.models import Credit

        table_name = Credit._meta.db_table

        if not Credit.objects.filter(user_id=self.user.id).count() > 0:
            return 0
        qText = """
                  SELECT
                      sum(
                        CASE WHEN user_id=""" + str(
            self.user.id) + """ THEN value ELSE -value END) as summ, user_id FROM %s where user_id=""" + str(
            self.user.id) + """
                      or payer_id=""" + str(self.user.id) + """
              """
        cursor = connection.cursor()
        sql = qText % table_name
        cursor.execute(sql.strip())

        for x in cursor.fetchall():
            if not x[0]:
                continue

            return x[0]
        return 0

    @property
    def allTasksQty(self):
        return self.user.todo.filter(active=True, closed=False).exclude(project__closed=True, project__locked=True,
                                                                        status__code='ready').count()

    def is_donator(self):
        return self.opengifter_level in [self.DONATOR, self.BACKER, self.OPENGIFTER]

    def is_backer(self):
        return self.opengifter_level in [self.BACKER, self.OPENGIFTER]

    def is_opengifter(self):
        return self.opengifter_level == self.OPENGIFTER

    def get_donation_sum(self, taskId=None, projectId=None):
        sum = 0
        donations = self.user.donations.all()
        if taskId:
            donations = donations.filter(task=taskId)

        if projectId:
            donations = donations.filter(project=projectId)

        for d in donations:
            sum += d.sum

        return sum

    def update_opengifter_level(self):
        sum = self.get_donation_sum()

        dl = None
        if sum > self.level_sum[self.OPENGIFTER]:
            dl = self.OPENGIFTER
        elif sum > self.level_sum[self.BACKER]:
            dl = self.BACKER
        elif sum > self.level_sum[self.DONATOR]:
            dl = self.DONATOR

        if self.opengifter_level != dl:
            self.opengifter_level = dl
            self.save()

    def account_total_project(self, project):
        from PM_Project.models import Credit
        if not project:
            return 0

        table_name = Credit._meta.db_table

        qText = """
                  SELECT
                      sum(CASE WHEN user_id=""" + str(
            self.user.id) + """ THEN value ELSE -value END) as summ, user_id FROM %s where (user_id=""" + str(
            self.user.id) + """
                      or payer_id=""" + str(self.user.id) + """)
                      AND project_id=""" + str(project.id) + """
              """
        cursor = connection.cursor()
        sql = qText % table_name
        cursor.execute(sql)

        for x in cursor.fetchall():
            if not x[0]:
                continue

            return x[0]
        return 0

    @property
    def url(self):
        return "/user_detail/?id=" + str(self.user.id)

    @property
    def avatarSrc(self):
        # from django.core.exceptions import SuspiciousOperation
        if self.avatar:
            try:
                avatar = get_thumbnail(self.avatar, '120x120')
                return avatar.url
            except Exception:
                avatar = str(self.avatar.url) if self.avatar else ''
                if avatar:
                    if avatar.find('media') < 0:
                        avatar = '/media/' + avatar

            return avatar
        else:
            avatar = 'https://robohash.org/opengift_' + str(self.id) + '.png'
            return avatar
        
    @property
    def avatarSquare(self):
        return '<div style="background: url(' + self.avatarSrc + ');background-repeat: no-repeat;background-size: cover;height: 120px;width: 120px;"></div>'

    @property
    def avatarCircle(self):
        return '<div style="border-radius: 50%;background: url(' + self.avatarSrc + ');background-repeat: no-repeat;background-size: cover;height: 120px;width: 120px;"></div>'

    @property
    def avatar_rel(self):
        if self.avatarSrc:
            return {
                'image': self.avatarSrc,
                'id': self.user.id
            }
        else:
            return {
                'id': self.user.id,
                'color': self.avatar_color,
                'initials': self.user.last_name[0] + self.user.first_name[
                    0] if self.user.last_name and self.user.first_name else ''
            }

    @property
    def managedProjects(self):
        try:
            return PM_Project.objects.filter(pk__in=PM_ProjectRoles.objects.filter(
                user=self.user,
                role=PM_Role.objects.get(code='manager')
            ).values('project__id')).exclude(closed=True, locked=True)
        except PM_Role.DoesNotExist:
            return None

    @staticmethod
    def getCurrent(request):  # возвращает текущего пользователя
        if headers.TRACKER and request.user.is_authenticated():
            return PM_User.getByUser(request.user)

    @staticmethod
    def getByUser(user):
        if headers.TRACKER and user:
            try:
                pm_user = PM_User.objects.get(user=user, trackers=headers.TRACKER)
            except PM_User.DoesNotExist:
                try:
                    pm_user = PM_User.objects.get(user=user)
                except PM_User.DoesNotExist:
                    pm_user = PM_User(user=user)
                    pm_user.save()
                pm_user.trackers.add(headers.TRACKER)

            return pm_user

    @staticmethod
    def getOrCreateByEmail(email, project, role, password=None):
        try:
            user = User.objects.filter(username=email).get()  # достанем пользователя по логину
            is_new = False
        except User.DoesNotExist:
            is_new = True
            generated_password = False

            if not password:
                generated_password = True
                password = User.objects.make_random_password()
            login = email
            if len(login) > 30:
                login = login[0:login.find('@')]
            user = User.objects.create_user(login, email, password)
            context = {
                'user_name': ' '.join([user.first_name, user.last_name]),
                'user_login': login
            }

            if generated_password:
                context['user_password'] = password

            message = emailMessage(
                'hello_new_user',
                context,
                'Welcome to OpenGift!'
            )

            message.send([email])
            # admin
            # todo: Move this method to a service
            from tracker.settings import ADMIN_EMAIL
            message.send([ADMIN_EMAIL])

        if not user.is_active:
            user.is_active = True
            user.save()

        if project and role and not user.get_profile().hasRole(project, not_guest=True):
            user.get_profile().setRole(role, project)

        return user

    def getFine(self):
        rAll = FineHistory.objects.filter(
            user=self.user
        ).aggregate(Sum('value'))
        return rAll['value__sum'] or 0

    def getRating(self, project=None):
        if not self.is_outsource:
            return 0

        if project:
            if self.isClient(project):
                return 0

        rate = self.rating or 0
        for uac in PM_User_Achievement.objects.filter(user=self.user, project=project):
            try:
                pac = PM_Project_Achievement.objects.get(
                    project=project,
                    achievement=uac.achievement,
                    type='bet',
                    value__isnull=False
                )
                rate += pac.value

            except PM_Project_Achievement.DoesNotExist:
                continue

        return rate

    def isClient(self, project):
        return self.isRole('client', project)

    def isManager(self, project):
        return self.isRole('manager', project)

    def isEmployee(self, project):
        return self.isRole('employee', project)

    def isGuest(self, project):
        return self.isRole('guest', project)

    def hasRole(self, project, not_guest=False):
        try:
            qs = PM_ProjectRoles.objects.filter(user=self.user, project=project)
            if not_guest:
                qs = qs.exclude(role__code='guest')
            if qs.count() > 0:
                return True
            else:
                return False

        except PM_ProjectRoles.DoesNotExist:
            return False

    def isRole(self, roleCode, project):
        if self.user and project and roleCode:
            try:
                clientRole = PM_Role.objects.get(code=roleCode)
                try:
                    userRole = PM_ProjectRoles.objects.filter(user=self.user, role=clientRole, project=project)
                    if userRole and userRole[0]:
                        return True
                except PM_ProjectRoles.DoesNotExist:
                    pass
            except PM_Role.DoesNotExist:
                pass

        return False

    def setRole(self, roleCode, project):
        if self.user and project and roleCode:
            try:
                clientRole = PM_Role.objects.get(code=roleCode, tracker=headers.TRACKER)
            except PM_Role.DoesNotExist:
                return False

            if clientRole:
                deletedOld = True
                for role in PM_ProjectRoles.objects.filter(user=self.user, project=project):
                    deletedOld = role.safeDelete()

                if deletedOld:
                    PM_ProjectRoles.objects.get_or_create(
                        user=self.user,
                        role=clientRole,
                        project=project
                    )

        return self

    def getProjects(self, only_managed=False, locked=False, exclude_guest=False, closed=False):
        userRoles = PM_ProjectRoles.objects.filter(user=self.user)
        if only_managed:
            userRoles = userRoles.filter(role__code='manager')
        if exclude_guest:
            userRoles = userRoles.exclude(role__code='guest')

        arId = [role.project.id for role in userRoles]
        projects = PM_Project.objects.filter(id__in=arId, closed=closed)
        if not locked:
            projects = projects.filter(locked=False)

        projects = projects.distinct()
        return projects

    def getRoles(self, project):
        return [r.role for r in PM_ProjectRoles.objects.filter(user=self.user, project=project)]

    def getProjectUsers(self, project):
        return project.getUsers()

    def deleteRole(self, role, project):
        if self.user:
            userRole = PM_ProjectRoles.objects.get(user=self.user, role__code=role, project=project)
            if userRole:
                userRole.delete()

        return self

    def hasAccess(self, task, rule):
        if task and hasattr(task, 'project') and task.project:
            # if self.isManager(task.project):
            #     return True

            if task.author.id == self.user.id:
                return True

            if rule == 'view':
                return True

                # if task.onPlanning and not task.resp:
                #     return self.hasRole(task.project)
                #
                # return (task.resp and self.user.id == task.resp.id) \
                #        or self.user.id in [u.id for u in task.observers.all()] \
                #        or task.subTasks.filter(resp=self.user.id, active=True).exists() \
                #        or task.subTasks.filter(author=self.user.id, active=True).exists()

            elif rule == 'change':
                # todo: разделить по конкретным изменениям
                # (разработчики могут только принимать задачи без ответственного)
                return self.isEmployee(task.project) and not task.resp \
                       or self.user.id == task.resp.id

    def getBet(self, project, type=None, role_code=None):
        try:
            projectRole = PM_ProjectRoles.objects.filter(user=self.user, project=project, rate__isnull=False)

            if type:
                projectRole = projectRole.filter(payment_type=type)

            if role_code:
                projectRole = projectRole.filter(role__code=role_code)

            rate = self.sp_price

            if projectRole:
                projectRole = projectRole[0]

                rate = projectRole.rate if projectRole.rate is not None else (
                    int(self.sp_price) if self.sp_price else 0)

            if rate:
                rate += self.getRating(project)

            return rate

        except PM_ProjectRoles.DoesNotExist:
            return 0

    def getPaymentType(self, project, roleCode=False):
        for role in PM_ProjectRoles.objects.filter(user=self.user, project=project):
            if role.payment_type and (not roleCode or roleCode == role.role.code):
                return role.payment_type

        return 'real_time'

    def __str__(self):
        return "%s's profile" % self.user

    class Meta:
        app_label = 'PManager'


def remove_keys(sender, instance, **kwargs):
    from tracker.settings import USE_GIT_MODULE
    from PManager.classes.git.gitolite_manager import GitoliteManager
    from PManager.models.keys import Key

    keys = Key.objects.filter(user=instance)
    for key in keys:
        GitoliteManager.remove_key_from_user(key, instance)


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile, created = PM_User.objects.get_or_create(user=instance)


pre_delete.connect(remove_keys, sender=User)
post_save.connect(create_user_profile, sender=User)
