# -*- coding: utf-8 -*-
__author__ = 'Gvammer'
from django.contrib import admin
from PManager.models import Credit, Specialty, RatingHits, PM_Project_Donation, PM_Project_Problem, \
    PM_Project_Industry, LogData, LikesHits, Agent, PM_File_Category, PM_Milestone, PM_Hackathon, PM_Hackathon_Winner, \
    PM_NoticedUsers, PM_Notice, PM_Task_Status, \
    PM_User_PlanTime, PM_Files, PM_Task_Message, \
    PM_Timer, PM_Role, PM_Task, PM_ProjectRoles, \
    PM_Properties, PM_Project, PM_Tracker, PM_User, Agreement, \
    PM_User_Achievement, PM_Achievement, AccessInterface, \
    PM_Reminder, PM_Project_Achievement, Conditions, Test, Fee, TaskDraft, PaymentRequest, \
    RatingHistory, FineHistory, Release, Integration, SlackIntegration, PM_MilestoneChanges, \
    FaqQuestions, FaqQuestionsCategory, Tags, Dependency
from PManager.models import ObjectTags


class UserRolesInline(admin.TabularInline):
    fieldsets = (
        (
            None,
            {
                'fields': ('user', 'project', 'role', )
            }
            ),
        )

    model = PM_ProjectRoles
    extra = 0

class CreditInline(admin.ModelAdmin):
    list_display = ['user', 'payer', 'project', 'value', 'type', 'date', 'task']
    list_filter = ['user', 'payer', 'project__name']

class TaskInline(admin.ModelAdmin):
    list_filter = ['resp', 'project']

class RatingInline(admin.ModelAdmin):
    list_display = ['user', 'value', 'dateCreate']
    list_filter = ['user']

class FeeInline(admin.ModelAdmin):
    list_display = ['user', 'project', 'value', 'date', 'task']
    list_filter = ['user', 'project__name']

class UserRoles(admin.ModelAdmin):
    list_display = ['user', 'project', 'role']
    list_filter = ['user', 'project', 'role__code']

class LogDatas(admin.ModelAdmin):
    list_display = ['code', 'value', 'datetime', 'project_id', 'user']

class Timers(admin.ModelAdmin):
    list_display = ['seconds', 'user', 'dateEnd', 'task']

class PaymentsInline(admin.ModelAdmin):
    list_display = ['user', 'payer', 'project', 'value', 'date']

class Reminder(admin.ModelAdmin):
    list_display = ['user', 'task', 'date']

class AgreementInline(admin.ModelAdmin):
    list_display = ['date', 'resp', 'payer']

class PM_MilestoneChangesInline(admin.ModelAdmin):
    list_display = ['date', 'value', 'milestone']

class PM_UserInline(admin.ModelAdmin):
    list_display = ['user', 'id', 'in_whitelist', 'in_promo','github_id','github','avatar']

admin.site.register(PM_Role)
admin.site.register(PM_Task, TaskInline)
admin.site.register(PM_ProjectRoles, UserRoles)
admin.site.register(PM_Properties)
admin.site.register(PM_Project)
admin.site.register(PM_Tracker)
admin.site.register(PM_User, PM_UserInline)
admin.site.register(PM_Files)
admin.site.register(PM_Task_Message)
admin.site.register(PM_Timer, Timers)
admin.site.register(PM_Achievement)
admin.site.register(PM_User_Achievement)
admin.site.register(PM_Project_Achievement)
admin.site.register(PM_User_PlanTime)
admin.site.register(PM_Task_Status)
admin.site.register(PM_Notice)
admin.site.register(PM_NoticedUsers)
admin.site.register(PM_Project_Donation)
admin.site.register(PM_Milestone)
admin.site.register(PM_File_Category)
admin.site.register(PM_Reminder, Reminder)
admin.site.register(Agent)
admin.site.register(LogData, LogDatas)
admin.site.register(Specialty)
admin.site.register(Credit, CreditInline)
admin.site.register(Fee, FeeInline)
admin.site.register(AccessInterface)
admin.site.register(Test)
admin.site.register(Conditions)
admin.site.register(TaskDraft)
admin.site.register(PaymentRequest)
admin.site.register(RatingHistory, RatingInline)
admin.site.register(FineHistory)
admin.site.register(Agreement, AgreementInline)
admin.site.register(SlackIntegration)
admin.site.register(Release)
admin.site.register(RatingHits)
admin.site.register(PM_Project_Industry)
admin.site.register(LikesHits)
admin.site.register(PM_Project_Problem)
admin.site.register(FaqQuestionsCategory)
admin.site.register(FaqQuestions)
admin.site.register(PM_Hackathon)
admin.site.register(PM_Hackathon_Winner)
admin.site.register(Dependency)
class TagsAdmin(admin.ModelAdmin):
    list_display = ("tagText", "is_public", "color")
    search_fields = ("tagText",)

admin.site.register(Tags, TagsAdmin)
admin.site.register(PM_MilestoneChanges, PM_MilestoneChangesInline)

from django.contrib.auth.admin import UserAdmin

UserAdmin.list_display += ('id',)


admin.site.register(ObjectTags)

