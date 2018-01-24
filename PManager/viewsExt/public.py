__author__ = 'Gvammer'
from django.shortcuts import HttpResponse, HttpResponseRedirect
from PManager.models import PM_User, PM_Project, PM_Project_Donation, PM_Task
from django.template import loader, RequestContext

class Public:
    @staticmethod
    def mainPage(request):
        try:
            project = PM_Project.objects.get(pk=495)
        except PM_Project.DoesNotExist:
            project = PM_Project.objects.all()[0]

        if request.GET.get('logout', None) == 'yes':
            from django.contrib.auth import logout
            logout(request)
            return HttpResponseRedirect('/pub/')

        c = RequestContext(request, {
            'projects_qty': PM_Project.objects.filter(public=True).count(),
            'developers_qty': PM_User.objects.filter(blockchain_wallet__isnull=False).count(),
            'donations_qty': PM_Project_Donation.objects.count(),
            'milestones': project.milestones.filter(closed=False, donated=False).order_by('date'),
            'w': request.GET.get('w', '')
        })

        return HttpResponse(loader.get_template('public/index.html').render(c))

    @staticmethod
    def icoPage(request):
        try:
            project = PM_Project.objects.get(pk=495)
        except PM_Project.DoesNotExist:
            project = PM_Project.objects.all()[0]

        c = RequestContext(request, {
            'tasksQty': PM_Task.objects.filter(closed=True).count(),
            'projects_qty': PM_Project.objects.filter(public=True).count(),
            'developers_qty': PM_User.objects.filter(blockchain_wallet__isnull=False).count(),
            'donations_qty': PM_Project_Donation.objects.count(),
            'milestones': project.milestones.filter(closed=False, donated=False).order_by('date'),
            'w': request.GET.get('w', '')
        })

        return HttpResponse(loader.get_template('public/ico.html').render(c))