# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
from django.contrib import admin
from PManager.views import MainPage, Brains, add_timer
from PManager.viewsExt.git_view import GitView
from PManager.viewsExt.tasks import jiraCreateTask, jiraGetAssigned, jiraAssign, taskSimilar, taskListAjax, ajaxNewTaskWizardResponder, microTaskAjax, taskDetail
from PManager.viewsExt.messages import ajaxResponder as messagesAjaxResponder
from PManager.viewsExt.files import fileSave, ajaxFilesResponder, AjaxFileUploader, DeleteUploadedFile
from PManager.viewsExt.setup import register, recall
from PManager.viewsExt.milestones import ajaxMilestonesResponder, milestonesResponder, milestoneForm
from PManager.viewsExt.releases import releasesResponder
from PManager.viewsExt.users import userHandlers
from PManager.viewsExt.faq import list as faq_list
from PManager.viewsExt.notice import noticeSetRead
from PManager.viewsExt.task_drafts import taskdraft_detail, taskdraft_task_discussion, \
    taskdraft_resend_invites, taskdraft_accept_developer
from PManager.viewsExt.projects import projectDetailDonate, requirementsList, projectList, projectListFrame, projectListFrameAjax, \
    projectDetailAjax, projectDetailAdd, projectDetailEdit, projectDetailServer, \
    projectDetail, projectDetailPublic, addInterface, removeInterface, \
    checkUniqRepNameResponder, \
    project_server_setup, project_server_status
from PManager.viewsExt.file_view import docxView
from PManager.viewsExt.keys import KeyHandler
from PManager.viewsExt.assets import protected_file, stat_excel
from PManager.viewsExt.sniffer import get_errors
from PManager.viewsExt.forms import sendFeedback
from PManager.viewsExt.specialty import specialty_ajax
from robo.views import paysystems, payment
from PManager.xml_import.xml_import import XML_Import
from django.shortcuts import HttpResponse
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings

admin.autodiscover()

from ajaxuploader.backends.local import LocalUploadBackend
from yandex_money.signals import payment_completed
from PManager.models.tasks import PM_Project
from PManager.models.payments import Fee, Credit, PaymentRequest
from django.contrib.auth.models import User
from PManager.viewsExt.agreements import ajax_handler as agreements_ajax
from PManager.viewsExt.blockchain import blockchainMain, blockchainAjax, \
    blockchainIncome, paypalExecute
from PManager.viewsExt.telegram import botPage
from PManager.viewsExt.public import Public
from PManager.viewsExt.crypto import get_paid_btc
import datetime
from django.views.generic.base import RedirectView
from django.views.generic import TemplateView
import logging
logger = logging.getLogger('yandex_money')

def ya_payment_completed(sender, **kwargs):

    try:
        project = PM_Project.objects.get(pk=sender.article_id)
    except PM_Project.DoesNotExist:
        project = None
    logger.info(sender)
    logger.info(sender.user)
    logger.info(project)
    credit = Credit(
                user=sender.user,
                value=sender.shop_amount,
                project=project,
                comment=u"Зачисление по договору ИИС№" + str(sender.user.id)
            )
    credit.save()

payment_completed.connect(ya_payment_completed)

default_storage_uploader = AjaxFileUploader(backend=LocalUploadBackend)

urlpatterns = patterns('',
                       url(r'^$', MainPage.indexRender,
                           {'widgetList': ["tasklist"], 'activeMenuItem': 'main'}),

                       url(r'^gantt/$', MainPage.indexRender, {'widgetList': ["gantt"], 'activeMenuItem': 'gantt'}),
                       url(r'^widgets/js/(?P<widget_name>[A-z_]+)/(?P<script_name>[A-z_\.]+)\.js',
                           MainPage.jsWidgetProxy),
                       url(r'^widget_update/(?P<widget_name>[A-z_]+)', MainPage.widgetUpdate),
                       url(r'^user_list/', MainPage.indexRender, {'widgetList': ["user_list"], 'activeMenuItem': 'user_list'}),
                       url(r'^life/', MainPage.indexRender, {'widgetList': ["life"]}),
                       url(r'^pro/', MainPage.likeAPro),
                       url(r'^achievements/', MainPage.indexRender, {'widgetList': ["achievements"]}),
                       url(r'^user_detail/', MainPage.indexRender, {'widgetList': ["user_detail"], 'template': 'new'}, name='user-detail'),
                       
                       url(r'^sendfile/', fileSave),
                       url(r'^calendar/', MainPage.indexRender,
                           {'widgetList': ["project_calendar"], 'activeMenuItem': 'calendar'}),
                       url(r'^opengifters/(?P<user_id>[0-9_]+)/', Public.backerProfile),
                       url(r'^profile/edit/', MainPage.indexRender,
                           {'widgetList': ["profile_edit"], 'activeMenuItem': 'profile', 'template': 'new'}),
                       # {{{ Project URLS 
                       url(r'^project/(?P<project_id>[0-9_]+)/server-setup', project_server_setup),
                       url(r'^project/(?P<project_id>[0-9_]+)/server-status', project_server_status),
                       url(r'^project/(?P<project_id>[0-9_]+)/public/', projectDetailPublic),
                       url(r'^project/(?P<project_id>[0-9_]+)/tasks/', MainPage.projectWidgets,
                           {'widgetList': ["tasklist"]}),
                       url(r'^project/(?P<project_id>[0-9_]+)/donate/', projectDetailDonate),
                       url(r'^project/(?P<project_id>[0-9_]+)/server/', projectDetailServer),
                       url(r'^project/(?P<project_id>[0-9_]+)/edit/', projectDetailEdit, {'need_inverse': True}),
                       url(r'^project/(?P<project_id>[0-9_]+)/ajax/', projectDetailAjax),
                       url(r'^project/(?P<project_id>[0-9_]+)', projectDetail),
                       url(r'^project/edit/', MainPage.indexRender,
                           {'widgetList': ["project_edit"], 'activeMenuItem': 'project'}),
                       url(r'^project/add/', projectDetailAdd),
                       url(r'^project/list/jira/ajax/', projectListFrameAjax, {'need_inverse': True}),
                       url(r'^project/list/jira/requirements/', requirementsList, {'need_inverse': True}),
                       url(r'^project/list/jira/', projectListFrame, {'need_inverse': True}),
                       url(r'^tasks/get_similar', taskSimilar),
                       url(r'^tasks/jira/assign/', jiraAssign),
                       url(r'^tasks/jira/get_assigned/', jiraGetAssigned),
                       url(r'^tasks/jira/create/', jiraCreateTask),
                        url(r'^project/list/', projectList, {'need_inverse': True}),
                       url(r'^project/edit/check_repository_name', checkUniqRepNameResponder),
                       # }}}

                       # {{{ Tasks
                       url(r'^task_handler', taskListAjax, name='task-handler'),
                       url(r'^task/add/', taskDetail),
                       url(r'^task_edit/$', MainPage.indexRender,
                           {'widgetList': ["task_edit"], 'activeMenuItem': 'tasks'}),
                       url(r'^task_detail/$', MainPage.projectWidgets,
                           {'widgetList': ["task_detail"], 'activeMenuItem': 'tasks'}),

                       # }}}
                       url(r'^bounty/', MainPage.projectWidgets,
                           {'widgetList': ["tasklist"], 'activeMenuItem': 'bounty', 'widgetParams': {'bounty': True}}),
                       url(r'^add_interface/', addInterface),
                       url(r'^remove_interface/', removeInterface),
                       url(r'^commit/show', GitView.show_commit),
                       url(r'^upload/receiver$', default_storage_uploader, name="ajax-upload-default-storage"),
                       url(r'^upload/receiver/(?P<handler_id>[A-z0-9_\-]+)$', DeleteUploadedFile),
                       url(r'^files/$', MainPage.indexRender, {'widgetList': ["file_list"], 'activeMenuItem': 'files'}),
                       url(r'^new_task_wizard/$', ajaxNewTaskWizardResponder),
                       url(r'^milestone_ajax/$', ajaxMilestonesResponder),
                       url(r'^taskdrafts/$', MainPage.indexRender,
                           {'widgetList': ['taskdrafts'], 'activeMenuItem': 'main'}),
                       url(r'^taskdraft/(?P<draft_slug>[0-9A-z_]{64})/resend-invites$', taskdraft_resend_invites),
                       url(r'^taskdraft/(?P<draft_slug>[0-9A-z_]{64})/accept-developer$',
                           taskdraft_accept_developer),
                       url(r'^taskdraft/(?P<draft_slug>[0-9A-z_]{64})/(?P<task_id>[0-9]+)/accept-developer$',
                           taskdraft_accept_developer),
                       url(r'^taskdraft/(?P<draft_slug>[0-9A-z_]{64})/(?P<task_id>[0-9]+)$', taskdraft_task_discussion),
                       url(r'^taskdraft/(?P<draft_slug>[0-9A-z_]{64})$', taskdraft_detail),
                       url(r'^milestones/$', milestonesResponder, {'activeMenuItem': 'milestones'}),
                       url(r'^releases/$', releasesResponder, {'activeMenuItem': 'releases'}),
                       url(r'^files_ajax/$', ajaxFilesResponder),
                       url(r'^messages_ajax/$', messagesAjaxResponder),
                       url(r'^users_ajax/$', userHandlers.setUserOptions),
                       url(r'^diagram_editor/$', MainPage.indexRender,
                           {'widgetList': ['diagram_editor']}),
                       url(r'^user_key_handle/add/$', KeyHandler.key_add),
                       url(r'^user_key_handle/remove/(?P<key_id>[0-9_]+)', KeyHandler.key_remove),
                       url(r'^import_teamlab/', XML_Import.importView),
                       url(r'^statistic/$', MainPage.indexRender, {'widgetList': ["user_statistic"]}),
                       url(r'^stat/$', MainPage.indexRender, {'widgetList': ["project_statistic"], 'activeMenuItem': 'stat'}),
                       url(r'^projects_summary/$', MainPage.indexRender, {'widgetList': ["project_summary"]}),
                       url(r'^register/$', register),
                       url(r'^phone_invite/$', recall),
                       url(r'^docx/$', docxView),
                       url(r'^train/$', Brains.trainTasksBrains),
                       url(r'^ajax/notice$', noticeSetRead),
                       url(r'^cost/$', MainPage.paymentReport),
                       url(r'^credits/$', MainPage.creditReport),
                       url(r'^credit_chart/$', MainPage.creditChart),
                       # {{{ AUTHS VIEWS
                       url(r'^login/github/callback$', MainPage.github_callback),
                       url(r'^login/github/connect$', MainPage.github_connect),
                       url(r'^login/github/$', MainPage.github_auth),
                       url(r'^login/$', MainPage.auth),
                       # }}}
                       
                       url(r'^take_your_gift/$', MainPage.takeGift),
                       url(r'^change_password/$', MainPage.changePassword),
                       url(r'^add_timer/', add_timer),
                       url(r'^kanban/', MainPage.indexRender, {'widgetList': ["kanban"], 'activeMenuItem': 'kanban'}),
                       url(r'^ajax/micro_task/(?P<task_id>[0-9_]+)', microTaskAjax),
                       url(r'^ajax/responsible_menu/$', userHandlers.getResponsibleMenu),
                       url(r'^ajax/milestone_create/$', milestoneForm),
                       url(r'^ajax/feedback/$', sendFeedback),
                       url(r'^ajax/specialty/$', specialty_ajax),
                       url(r'^ajax/stat_excel/$', stat_excel),
                       url(r'^agreements/$', agreements_ajax),
                       url(r'^file_access/', protected_file),
                       url(r'^sniffer/get_errors/', get_errors),
                       url(r'^admin/', include(admin.site.urls)),
                       (r'^robots\.txt$',
                        lambda r: HttpResponse("User-agent: *\r\nAllow: /\r\nDisallow: /static/\r\n", mimetype="text/plain")),
                       # (r'^search/', include('haystack.urls')),
                       url(r'^robokassa/', include('robokassa.urls')),
                       url(r'^fail-payment/$', TemplateView.as_view(template_name='yandex/fail.html'), name='payment_fail'),
                       url(r'^success-payment/$', TemplateView.as_view(template_name='yandex/success.html'), name='payment_success'),
                       url(r'^kassa/', include('yandex_money.urls')),
                       url(r'^payment_info/', paysystems),
                       url(r'^payment/', payment),
                       url(r'^promo_tmp/', MainPage.promoTmp),
                       url(r'^support/', MainPage.support),

                       url(r'^blockchain/ajax/', blockchainAjax),
                       url(r'^crypto/electrum', blockchainIncome),
                       url(r'^crypto/getpaid', get_paid_btc),
                       url(r'^wallet/', blockchainMain),
                       url(r'^pub/', Public.mainPage),
                       url(r'^ico/', Public.icoPage),
                       url(r'^hackathon_register/', Public.hackathon_register),
                       url(r'^debug_on/', Public.debug_on),
                       url(r'^debug_off/', Public.debug_off),
                       url(r'^backers/$', TemplateView.as_view(template_name='public/backers.html'), {'need_inverse': True}),
                       url(r'^offer_ru/$', TemplateView.as_view(template_name='public/offer_ru.html')),
                       url(r'^offer/$', TemplateView.as_view(template_name='public/offer.html')),
                       url(r'^startups/$', Public.startups),
                       url(r'^christmas/$', Public.christmas),
					   # url(r'^january/$', Public.january),
                       url(r'^cofounder/$', Public.cofounders),
                       url(r'^business_ru/$', TemplateView.as_view(template_name='public/ico_details.html')),
                       url(r'^apps/$', TemplateView.as_view(template_name='public/apps.html')),
                       url(r'^telegram/bot/$', botPage),
                       url(r'^ref/$', TemplateView.as_view(template_name='public/ref.html'), {'need_inverse': True}),
                       url(r'^dev/$', TemplateView.as_view(template_name='public/developers.html'), {'need_inverse': True}),
                       url(r'^hackathon/$', Public.hackathon, {'need_inverse': True}),
                       url(r'^credits-hackathon/$', Public.credits_hackathon, {'need_inverse': True}),
                       url(r'^hackaton/$', RedirectView.as_view(url='/hackathon/', permanent=False), {'need_inverse': True}),
                       url(r'^faq/$', faq_list),
                       url(r'^paypal/$', paypalExecute),
                       url(r'^.well-known/pki-validation/33964DF816EB9D15A1764F04818FB7E7.txt', lambda r: HttpResponse("893D709E4EFBB5DD6799956FA602579A9AFFA233377F7DBB3F14C48ACBD21211\r\nCOMODOCA.COM\r\nw0617990001512489411")),
                       url(r'^wiki/', include('wiking.urls'))
                       )
urlpatterns += staticfiles_urlpatterns()



if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
   )
