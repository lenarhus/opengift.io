# -*- coding:utf-8 -*-
# Create your views here.
from django.shortcuts import HttpResponse, HttpResponseRedirect
from django.db.models import Sum
from PManager.models import PM_User, PM_Task, PM_Notice, PM_Timer, PM_User_Achievement, PM_Task_Message, Fee, Agreement
from PManager.models import Tags
from PManager import widgets
from django.template import loader, RequestContext
from PManager.viewsExt.tools import emailMessage
from tracker import settings
import os
from PManager.viewsExt.tools import set_cookie
from PManager.viewsExt import headers
from django.shortcuts import redirect
# from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from PManager.services.mind.task_mind_core import TaskMind
from PManager.github_auth import GithubAuth


class Brains:
    @staticmethod
    def trainTasksBrains(request):
        net = TaskMind()
        tasksForBrain = PM_Task.objects.filter(
            closed=False, realDateStart__isnull=False, active=True
        ).order_by('?')[:5]
        net.train(tasksForBrain)
        return HttpResponse('trained')


class MainPage:

    @staticmethod
    def support(request):
        from bitrix24 import Bitrix24
        # bx24 = Bitrix24(
        #     'b24-n58c67058c2ec8', request.GET.get('AUTH_ID') or request.POST.get('AUTH_ID'))

        c = RequestContext(request)
        return HttpResponse(loader.get_template('main/support.html').render(c))

    @staticmethod
    def likeAPro(request):
        from robokassa.forms import RobokassaForm
        userFee = Fee.objects.filter(user=request.user).order_by('-id')
        c = RequestContext(request)
        fee = userFee.aggregate(Sum('value'))['value__sum'] or 0
        feeLatId = userFee[0].id if userFee else None
        if feeLatId:
            form = RobokassaForm(initial={
                'OutSum': fee,  # order.total,
                'InvId': feeLatId,  # order.id,
                'Desc': 'Пополнение счета Heliard',  # order.name,
                'Email': request.user.email,
                'user': request.user.id,
                'request': ''
            })
            c.update(
                {
                    'fee': fee,
                    'form': form
                }
            )

        return HttpResponse(loader.get_template('main/pro.html').render(c))

    @staticmethod
    def promoTmp(request):
        c = RequestContext(request)
        return HttpResponse(loader.get_template('main/promo_tmp.html').render(c))

    @staticmethod
    def changePassword(request):
        message = ''
        uname = request.POST.get('username', None)
        vcode = request.POST.get('code', None)
        if uname:
            from PManager.services.recaptcha import validate as validate_recaptcha
            if not validate_recaptcha(request.POST['g-recaptcha-response'], request.POST.get('skip_recaptcha', None)):
                return HttpResponse(
                    loader.get_template('main/change_password.html').render(
                        RequestContext(request, {"message": "incorrect_captcha"})
                    )
                )

            try:
                user = User.objects.get(username=uname)
                if vcode:
                    if vcode == user.get_profile().verification_code:
                        new_password = request.POST.get('password', None)
                        if new_password:
                            user.set_password(new_password)
                            user.save()

                            prof = user.get_profile()
                            prof.verification_code = ''
                            prof.save()

                            message = 'success'
                else:
                    prof = user.get_profile()
                    prof.verification_code = User.objects.make_random_password()
                    prof.save()
                    message = 'success_code_sent'
                    context = {
                        'user_name': ' '.join([user.first_name, user.last_name]),
                        'user_login': user.username,
                        'link': 'https://opengift.io/change_password/?code=' + prof.verification_code + '&uname=' + user.username
                    }

                    mess = emailMessage(
                        'hello_new_user',
                        context,
                        'OpenGift - Password changing.'
                    )
                    mess.send([user.username])
                    mess.send(['gvamm3r@gmail.com'])

            except User.DoesNotExist:
                message = 'not_found'

        c = RequestContext(request, {"message": message, 'is_confirmation': not not request.GET.get('code')})
        return HttpResponse(loader.get_template('main/change_password.html').render(c))

    @staticmethod
    def takeGift(request):
        setattr(request, 'isPromo', True)
        return MainPage.auth(request)


    @staticmethod
    def github_callback(request):
        code = request.GET.get("code")
        return HttpResponseRedirect('/login/?code=%s' % code) 

    @staticmethod
    def github_connect(request):
        code = request.GET.get("code")
        if code and request.user.is_authenticated():
            resp = GithubAuth.get_token(code)
            access_token = resp.get("access_token")
            user_data = GithubAuth.get_user_info(access_token)
            profile = request.user.profile
            profile.github_id = user_data.id
            profile.github = user_data.login
            profile.save()
            return HttpResponseRedirect('/profile/edit/') 
        else:
            return HttpResponseRedirect('/profile/edit/?error=no_auth')
        
        

    @staticmethod
    def github_auth(request):
        import urllib
        redirect = request.GET.get("redirect", None)
        if redirect and redirect == "connect":
            redirect_uri = settings.GITHUB_REDIR_URI + '/github/connect'
        else:
            redirect_uri = settings.GITHUB_REDIR_URI
    

        params = {
            'client_id': getattr(settings, "GITHUB_CLIENT_ID"),
            'redirect_uri': redirect_uri,
            'scope': 'read:user, user:email'
        }
        qs = urllib.urlencode(params)
        url = "https://github.com/login/oauth/authorize?"
        return HttpResponseRedirect(url + qs)

    @staticmethod
    def auth(request):
        from django.contrib.auth import authenticate, login
        from PManager.viewsExt.tools import emailMessage

        if request.user.is_authenticated():
            return HttpResponseRedirect('/')

        if request.GET.get("code"):
            code = request.GET.get("code")
            user = authenticate(code=code)
            if user and user.is_active:
                login(request, user)
                backurl = request.GET.get('backurl', '')
                if backurl:
                    return HttpResponseRedirect(backurl)

                return HttpResponseRedirect( '/wallet/')           
            else:
                resp = GithubAuth.get_token(code)
                if 'error' in resp:
                    return HttpResponse(
                        loader.get_template('main/unauth.html').render(
                            RequestContext(request, {"error": "github", 'error_description': resp.get("error_description")})
                    )
                )

                    

        if ( request.method == 'POST' and 
           'username' in request.POST and 
           'password' in request.POST):    
            username = request.POST['username']
            password = request.POST['password']
    
            from PManager.services.recaptcha import validate as validate_recaptcha
            if not validate_recaptcha(request.POST['g-recaptcha-response'], request.POST.get('skip_recaptcha', None)):
                return HttpResponse(
                    loader.get_template('main/unauth.html').render(
                        RequestContext(request, {"error": "incorrect_captcha"})
                    )
                )

            backurl = request.POST.get('backurl', None)
            if not backurl:
                backurl = '/wallet/'

            

            try:
                u = User.objects.filter(username=username).get()
                user = authenticate(username=username, password=password)
                if user is not None:
                    if user.is_active:
                        login(request, user)
                        if request.GET.get('from', '') == 'mobile':
                            return HttpResponse('{"unauthorized": false}', content_type='application/json')
                        else:
                            return HttpResponseRedirect(backurl)
                    else:
                        return HttpResponse(loader
                                            .get_template('main/unauth.html')
                                            .render(RequestContext(request, {"error": "not_active"})))
                else:
                    return HttpResponse(loader
                                        .get_template('main/unauth.html')
                                        .render(RequestContext(request, {"error": "not_found"})))

            except User.DoesNotExist:
                error = None
                if not request.POST.get('registration', None):
                    error = u'Enter correct email'
                elif not emailMessage.validateEmail(username):
                    error = u'Enter correct email'
                else:
                    user = PM_User.getOrCreateByEmail(username, None, None, password)
                    if request.POST.get('name'):
                        user.first_name = request.POST.get('name')
                        user.last_name = request.POST.get('surname')
                        user.save()

                    white_list_registraton = request.POST.get('whitelist', None)
                    promo_reg = request.POST.get('promo_reg', None)

                    prof = user.get_profile()
                    if white_list_registraton or promo_reg:
                        prof.in_whitelist = True if white_list_registraton else False
                        prof.in_promo = True if promo_reg else False
                        prof.tokens_to_buy = request.POST.get('gift_qty')
                        prof.eth = request.POST.get('eth_address')

                        mess = emailMessage(
                            'whitelist',
                            {
                                'first_name': user.first_name,
                                'last_name': user.last_name
                            },
                            'OpenGift - Thanks for registering in the WhiteList!'
                        )
                        mess.send([username])
                        from tracker.settings import ADMIN_EMAIL
                        mess.send([ADMIN_EMAIL])

                    prof.is_bc_user = True
                    prof.referrer = request.COOKIES.get('partner_id', None)
                    prof.save()

                    user.backend = 'django.contrib.auth.backends.ModelBackend'
                    login(
                        request,
                        user
                    )
                    return HttpResponseRedirect(backurl)

                if error:
                    return HttpResponse(
                        loader.get_template('main/unauth.html').render(
                            RequestContext(request, {"error": "incorrect_email"})
                        )
                    )
        elif 'logout' in request.GET and request.GET['logout'] == 'Y':
            from django.contrib.auth import logout
            logout(request)
            return HttpResponseRedirect('/login/')

        if request.GET.get('from', '') == 'mobile':
            if request.user.is_authenticated():
                return HttpResponse('{"unauthorized": false}', content_type='application/json')

        c = RequestContext(request)
        return HttpResponse(loader.get_template('main/unauth.html').render(c))

    @staticmethod
    def projectWidgets(request, project_id=None, widgetList=None, activeMenuItem=None, widgetParams={}, template=None):
        # agents
        from PManager.models import Agent
        from django.db.models import Q
        import datetime
        from PManager.viewsExt.tools import TextFilters
        from django.utils.html import escape
        import urllib

        cType = 'text/html'
        mimeType = None
        bXls = request.GET.get('xls_output', False)

        agents = Agent.objects.filter(Q(Q(datetime__lt=datetime.datetime.now()) | Q(datetime__isnull=True)))
        for agent in agents:
            agent.process()

        if project_id:
            request.COOKIES["CURRENT_PROJECT"] = project_id

        if widgetParams.get('bounty'):
            request.COOKIES["CURRENT_PROJECT"] = 0

        headerValues = headers.initGlobals(request)
        if headerValues['REDIRECT']:
            return redirect(headerValues['REDIRECT'])

        # stop timers
        leastHours = datetime.datetime.now() - datetime.timedelta(hours=9)
        for timer in PM_Timer.objects.filter(dateStart__lt=leastHours, dateEnd__isnull=True):
            timer.delete()

        headerWidgets = []
        widgetsInTabs = []
        c = RequestContext(request, {})
        userTimer = None
        userAchievement = None
        messages = None
        messages_qty = 0
        aMessages = []
        pageTitle = ''

        agreementForApprove = None

        taskNumber = int(request.GET.get('number', 0))
        taskId = int(request.GET.get('id', 0))
        projectId = int(request.GET.get('project', 0))

        if not widgetList:
            widgetList = ['tasklist']

        # uAchievement = PM_User_Achievement.objects.filter(user=request.user, read=False)
        # userAchievement = uAchievement[0] if uAchievement and uAchievement[0] else None
        #
        # if userAchievement:
        #     if userAchievement.achievement.delete_on_first_view:
        #         userAchievement.delete()
        #     else:
        #         userAchievement.read = True
        #         userAchievement.save()

        if request.user.is_authenticated():
            if (not 'chat' in widgetList) and ('tasklist' in widgetList):
                widgetList.append('chat')

            messages = PM_Task_Message.objects.filter(
                userTo=request.user,
                read=False
            ).order_by('-dateCreate')


            if projectId:
                if taskId:
                    messages = messages.exclude(
                        task=taskId,
                        project=projectId
                    )
                elif taskNumber:
                    messages = messages.exclude(
                        task__number=taskNumber,
                        project=projectId
                    )

            messages = messages.exclude(code="WARNING")
            messages_qty = messages.count()

            for mes in messages:
                setattr(mes, 'text', TextFilters.getFormattedText(escape(mes.text)))
                setattr(mes, 'text', TextFilters.convertQuotes(mes.text))
                aMessages.append(mes)

            unapprovedAgreements = Agreement.objects.filter(payer=request.user, approvedByPayer=False)
            unapprovedAgreementsResp = Agreement.objects.filter(resp=request.user, approvedByResp=False)

            if unapprovedAgreements:
                agreementForApprove = unapprovedAgreements[0]
            elif unapprovedAgreementsResp:
                agreementForApprove = unapprovedAgreementsResp[0]

            userTimer = PM_Timer.objects.filter(user=request.user, dateEnd__isnull=True)
            if userTimer:
                userTimer = userTimer[0]
                timerDataForJson = userTimer.getTime()
                timerDataForJson['started'] = True if not userTimer.dateEnd else False
                setattr(userTimer, 'jsonData', timerDataForJson)


        arPageParams = {
            'pageCount': 10,
            'page': int(request.POST.get('page', 1))
        }

        for widgetName in widgetList:
            str = 'widget = widgets.%s' % widgetName
            exec (str)
            if widgetName == 'tasklist':
                widget = widget.widget(request, headerValues, widgetParams, [], arPageParams)
            else:
                widget = widget.widget(request, headerValues, widgetParams, [])

            if widget:
                if 'redirect' in widget:
                    return HttpResponseRedirect(widget['redirect'])
                if 'title' in widget:
                    pageTitle = widget['title']

                c.update({widgetName: widget})
                if bXls:
                    templateName = 'xls'
                else:
                    templateName = 'widget'

                widgetHtml = loader.get_template("%s/templates/%s.html" % (widgetName, templateName)).render(c)

                if 'tab' in widget and widget['tab']:
                    widgetsInTabs.append({
                        'code': widgetName,
                        'name': widget['name'],
                        'html': widgetHtml
                    })
                else:
                    headerWidgets.append(widgetHtml)

        if request.is_ajax():
            if request.GET.get('modal', None) is not None:
                t = loader.get_template('main/xhr_response_modal.html')
            else:
                t = loader.get_template('main/xhr_response.html')
        else:
            if request.GET.get('frame_mode', False):
                t = loader.get_template('index_frame.html')
            elif bXls:
                cType = 'application/xls'
                mimeType = 'application/xls'
                t = loader.get_template('index_xls.html')
            elif template == 'new':
                t = loader.get_template('index_new.html')
            else:
                t = loader.get_template('index.html')
        c.update({'widget_header': u" ".join(headerWidgets)})
        c.update({'widgets': widgetsInTabs})
        if not headerValues['FIRST_STEP_FORM']:
            cur_notice = PM_Notice.getForUser(
                request.user,
                request.get_full_path()
            )
            if cur_notice:
                # cur_notice.setRead(request.user)
                c.update({
                    'current_notice': cur_notice
                })

        c.update({
            'pageTitle': pageTitle,
            'activeMenuItem': activeMenuItem,
            'userTimer': userTimer,
            'currentProject': headerValues['CURRENT_PROJECT'],
            # 'userAchievement': userAchievement,
            'messages': aMessages,
            'messages_qty': messages_qty,
            'agreementForApprove': agreementForApprove,
            'activeWidget': headerValues['COOKIES']['ACTIVE_WIDGET'] if 'ACTIVE_WIDGET' in headerValues[
                'COOKIES'] and request.user.is_authenticated() else None
        })

        render = t.render(c)
        response = HttpResponse(render, content_type=cType, mimetype=mimeType)
       
        if bXls:
            response['Content-Disposition'] = 'attachment; filename="file.xls"'

        for key in headerValues['SET_COOKIE']:
            set_cookie(response, key, headerValues['SET_COOKIE'][key])

        return response

    @staticmethod
    def indexRender(request, widgetList=None, activeMenuItem=None, widgetParams={}, template=None):
        # agents
        from PManager.models import Agent
        from django.db.models import Q
        import datetime
        from PManager.viewsExt.tools import TextFilters
        from django.utils.html import escape
        import urllib

        if activeMenuItem == 'main':
            return HttpResponseRedirect('/pub/')

        cType = 'text/html'
        mimeType = None
        bXls = request.GET.get('xls_output', False)

        agents = Agent.objects.filter(Q(Q(datetime__lt=datetime.datetime.now()) | Q(datetime__isnull=True)))
        for agent in agents:
            agent.process()

        headerValues = headers.initGlobals(request)
        if headerValues['REDIRECT']:
            return redirect(headerValues['REDIRECT'])

        # stop timers
        leastHours = datetime.datetime.now() - datetime.timedelta(hours=9)
        for timer in PM_Timer.objects.filter(dateStart__lt=leastHours, dateEnd__isnull=True):
            timer.delete()

        headerWidgets = []
        widgetsInTabs = []
        c = RequestContext(request, {})
        userTimer = None
        userAchievement = None
        messages = None
        messages_qty = 0
        aMessages = []
        pageTitle = ''

        agreementForApprove = None
        if request.user.is_authenticated():
            messages = PM_Task_Message.objects.filter(
                userTo=request.user,
                read=False
            ).order_by('-dateCreate')

            taskNumber = int(request.GET.get('number', 0))
            taskId = int(request.GET.get('id', 0))
            projectId = int(request.GET.get('project', 0))

            if projectId:
                if taskId:
                    messages = messages.exclude(
                        task=taskId,
                        project=projectId
                    )
                elif taskNumber:
                    messages = messages.exclude(
                        task__number=taskNumber,
                        project=projectId
                    )

            messages = messages.exclude(code="WARNING")
            messages_qty = messages.count()

            for mes in messages:
                setattr(mes, 'text', TextFilters.getFormattedText(escape(mes.text)))
                setattr(mes, 'text', TextFilters.convertQuotes(mes.text))
                aMessages.append(mes)

            if not widgetList:
                widgetList = ['tasklist']

            unapprovedAgreements = Agreement.objects.filter(payer=request.user, approvedByPayer=False)
            unapprovedAgreementsResp = Agreement.objects.filter(resp=request.user, approvedByResp=False)

            if unapprovedAgreements:
                agreementForApprove = unapprovedAgreements[0]
            elif unapprovedAgreementsResp:
                agreementForApprove = unapprovedAgreementsResp[0]

            userTimer = PM_Timer.objects.filter(user=request.user, dateEnd__isnull=True)
            if userTimer:
                userTimer = userTimer[0]
                timerDataForJson = userTimer.getTime()
                timerDataForJson['started'] = True if not userTimer.dateEnd else False
                setattr(userTimer, 'jsonData', timerDataForJson)

            arPageParams = {
                'pageCount': 10,
                'page': int(request.POST.get('page', 1))
            }

            for widgetName in widgetList:
                # TODO: change this!!
                str = 'widget = widgets.%s' % widgetName
                exec (str)
                if widgetName == 'tasklist':
                    widget = widget.widget(request, headerValues, widgetParams, [], arPageParams)
                else:
                    widget = widget.widget(request, headerValues, widgetParams, [])

                if widget:
                    if 'redirect' in widget:
                        return HttpResponseRedirect(widget['redirect'])
                    if 'title' in widget:
                        pageTitle = widget['title']

                    c.update({widgetName: widget})
                    if bXls:
                        templateName = 'xls'
                    else:
                        templateName = 'widget'

                    widgetHtml = loader.get_template("%s/templates/%s.html" % (widgetName, templateName)).render(c)

                    if 'tab' in widget and widget['tab']:
                        widgetsInTabs.append({
                            'code': widgetName,
                            'name': widget['name'],
                            'html': widgetHtml
                        })
                    else:
                        headerWidgets.append(widgetHtml)

            if request.is_ajax():
                if request.GET.get('modal', None) is not None:
                    t = loader.get_template('main/xhr_response_modal.html')
                else:
                    t = loader.get_template('main/xhr_response.html')
            else:
                if request.GET.get('frame_mode', False):
                    t = loader.get_template('index_frame.html')
                elif bXls:
                    cType = 'application/xls'
                    mimeType = 'application/xls'
                    t = loader.get_template('index_xls.html')
                elif template == 'new':
                    t = loader.get_template('index_new.html')
                else:
                    t = loader.get_template('index.html')

            c.update({'widget_header': u" ".join(headerWidgets)})
            c.update({'widgets': widgetsInTabs})

            # uAchievement = PM_User_Achievement.objects.filter(user=request.user, read=False)
            # userAchievement = uAchievement[0] if uAchievement and uAchievement[0] else None
            #
            # if userAchievement:
            #     if userAchievement.achievement.delete_on_first_view:
            #         userAchievement.delete()
            #     else:
            #         userAchievement.read = True
            #         userAchievement.save()
        else:
            import re
            # if is not main page
            if re.sub(r'([^/]+)', '', request.get_full_path()) == '/':
                t = loader.get_template(
                    'public/index.html' if request.META['HTTP_HOST'] == 'opengift.io' else 'main/promo.html')
            else:
                return HttpResponseRedirect('/login/?backurl=' + urllib.quote(request.get_full_path()))

        if not headerValues['FIRST_STEP_FORM']:
            cur_notice = PM_Notice.getForUser(
                request.user,
                request.get_full_path()
            )
            if cur_notice:
                # cur_notice.setRead(request.user)
                c.update({
                    'current_notice': cur_notice
                })

        c.update({
            'pageTitle': pageTitle,
            'activeMenuItem': activeMenuItem,
            'userTimer': userTimer,
            'currentProject': headerValues['CURRENT_PROJECT'],
            # 'userAchievement': userAchievement,
            'messages': aMessages,
            'messages_qty': messages_qty,

            'agreementForApprove': agreementForApprove,
            'activeWidget': headerValues['COOKIES']['ACTIVE_WIDGET'] if 'ACTIVE_WIDGET' in headerValues[
                'COOKIES'] else None
        })

        response = HttpResponse(t.render(c), content_type=cType, mimetype=mimeType)
        if bXls:
            response['Content-Disposition'] = 'attachment; filename="file.xls"'

        for key in headerValues['SET_COOKIE']:
            set_cookie(response, key, headerValues['SET_COOKIE'][key])
        return response

    @staticmethod
    def widgetUpdate(request, widget_name):
        headerValues = headers.initGlobals(request)
        if headerValues['REDIRECT']:
            return redirect(headerValues['REDIRECT'])

        widget = {}
        str = 'widget = widgets.%s' % widget_name
        exec (str)
        widget = widget.widget(request, headerValues, {}, [])
        c = RequestContext(request, {})
        if widget:
            if 'redirect' in widget:
                return HttpResponseRedirect(widget['redirect'])

        c.update({widget_name: widget})
        return HttpResponse(loader.get_template("%s/templates/widget.html" % widget_name).render(c))

    @staticmethod
    def returnWidgetJs(widgetName, script_name='widget'):
        if not widgetName: return False
        fn = os.path.join(os.path.dirname(__file__), "widgets/%s/js/%s.js" % (widgetName, script_name))

        try:
            js = open(fn, 'r').read()
            return js
        except Exception:
            return ''

    @staticmethod
    def jsWidgetProxy(request, widget_name=None, script_name=''):
        if widget_name:
            if script_name == 'script': script_name = 'widget'

            return HttpResponse(MainPage.returnWidgetJs(widget_name, script_name), mimetype='text/javascript')

    @staticmethod
    def creditReport(request):

        filterUser = request.GET.get('user', None)
        filterPayer = request.GET.get('payer', None)
        aFilter = {}
        if filterUser:
            aFilter['user'] = filterUser
        if filterPayer:
            aFilter['payer'] = filterPayer
        from PManager.models import Credit

        if request.user.is_superuser:
            headerValues = headers.initGlobals(request)
            p = headerValues['CURRENT_PROJECT']

            credits = Credit.objects.filter(task__project=p, value__gt=0)
            if aFilter:
                credits = Credit.objects.filter(**aFilter)

            credits = credits.order_by('-pk')
            aCredits = []
            sumCreditUserTo = 0
            sumCreditUserFrom = 0
            for credit in credits:
                if credit.user and credit.user.id:
                    sumCreditUserTo += credit.value
                else:
                    sumCreditUserFrom += credit.value

                aCredits.append(credit)
            payments = Credit.objects.filter(value__lt=0).order_by('-pk')
            c = RequestContext(request, {})
            c.update({
                'credits': aCredits,
                'payments': payments,
                'sumFrom': sumCreditUserFrom,
                'sumManager': sumCreditUserFrom * 0.15,
                'total': (sumCreditUserFrom * 0.85 - sumCreditUserTo),
                'sumTo': sumCreditUserTo
            })
            t = loader.get_template('report/credit_report.html')
            return HttpResponse(t.render(c))

    @staticmethod
    def paymentReport(request):
        from PManager.models import PM_Task, Credit, PM_ProjectRoles

        resp_id = request.GET.get('resp', None)
        headerValues = headers.initGlobals(request)
        p = headerValues['CURRENT_PROJECT']
        profile = request.user.get_profile()
        if not profile.isClient(p) and not profile.isManager(p):
            return HttpResponse('')

        clientBet = 0
        try:
            clientRole = PM_ProjectRoles.objects.get(role__code='client', project=p)
            client = clientRole.user
            clientBet = client.get_profile().getBet(p)
        except PM_ProjectRoles.DoesNotExist:
            pass

        userBets = {}
        atasks = []
        allsum = {
            'plan_cost': 0.,
            'cost': 0.,
            'plan_payment': 0.,
            'payment': 0.,
            'project_cost': 0.,
            'plan_profit': 0.,
            'profit': 0.
        }

        tasks = PM_Task.objects.filter(
            active=True,
            project=p
            # planTime__isnull=False
        )
        if resp_id:
            tasks = tasks.filter(resp=resp_id)

        tasks = tasks.order_by('-dateCreate')
        for task in tasks:
            if task.subTasks.filter(active=True).count():
                continue

            if task.resp:
                resp = task.resp
                if resp.id in userBets:
                    userBet = userBets[resp.id]
                else:
                    userBet = resp.get_profile().getBet(p)
                    userBets[resp.id] = userBet

                cost = sum(c.value for c in Credit.objects.filter(user__isnull=False, task=task))
                payment = sum(d.value for d in Credit.objects.filter(payer__isnull=False, task=task))

                setattr(task, 'resp', resp)
                planTime = (float(task.planTime) if (task.planTime) else 0)

                setattr(task, 'plan_cost', round(planTime * userBet, 2))
                setattr(task, 'cost', round(cost, 2))
                # setattr(task, 'cost', round(float(task.getAllTime()) * userBet / 3600., 2))

                setattr(task, 'plan_payment', planTime * clientBet)
                setattr(task, 'project_cost', payment * 0.15)
                setattr(task, 'plan_profit', task.plan_payment - task.plan_cost - task.project_cost)

                if task.wasClosed or task.closed or p.id == 34:
                    if not payment and clientRole.payment_type == 'fix':
                        payment = task.cost

                    setattr(task, 'payment', payment)
                    setattr(task, 'profit', task.payment - task.cost - task.project_cost)

                    allsum['payment'] += task.payment
                    allsum['profit'] += task.profit

                allsum['cost'] += task.cost
                allsum['plan_cost'] += task.plan_cost
                allsum['project_cost'] += task.project_cost
                allsum['plan_payment'] += task.plan_payment
                allsum['plan_profit'] += task.plan_profit

                atasks.append(task)

        c = RequestContext(request, {})

        payed = sum(p.value for p in Credit.objects.filter(value__lt=0, project=p, payer__isnull=False))
        total = sum(d.value for d in Credit.objects.filter(value__gt=0, project=p, payer__isnull=False))

        c.update({
            'is_manager': request.user.get_profile().isManager(p),
            'tasks': atasks,
            'sum': allsum,
            'total': total,
            'payed': payed,
            'debt': allsum['payment'] - payed,
            'credits': Credit.objects.filter(project=p, payer__isnull=False)
        })
        t = loader.get_template('report/payment_report.html')
        return HttpResponse(t.render(c))

    @staticmethod
    def creditChart(request):
        import datetime
        from PManager.models.payments import Credit

        project = request.GET.get('project', None)
        if project:
            projects = [project]
        else:
            projects = request.user.get_profile().managedProjects

        days = 30
        dateEnd = datetime.datetime.now()
        dateStart = dateEnd - datetime.timedelta(days=days)
        aSums = []
        sOut = 0
        sIn = 0
        pIn = 0
        pOut = 0
        for m in range(0, days + 1):
            date = dateStart + datetime.timedelta(days=m)
            credit = Credit.objects.filter(
                date__range=(datetime.datetime.combine(date, datetime.time.min),
                             datetime.datetime.combine(date, datetime.time.max)),
                project__in=projects
            )

            creditOut = credit.filter(user__isnull=False)
            creditIn = credit.filter(payer__isnull=False)

            sOut += sum(c.value for c in creditOut)
            sIn += sum(c.value for c in creditIn)

            payments = Credit.objects.filter(date__range=(datetime.datetime.combine(date, datetime.time.min),
                                                          datetime.datetime.combine(date, datetime.time.max)),
                                             project__in=projects, value__lt=0)

            paymentsOut = payments.filter(user__isnull=False)
            paymentsIn = payments.filter(payer__isnull=False)
            pOut += sum(c.value for c in paymentsOut)
            pIn += sum(c.value for c in paymentsIn)

            aSums.append({
                'date': date,
                'in': sIn,
                'pin': pIn,
                'out': sOut,
                'pout': pOut,
            })
        c = RequestContext(request, {
            'sums': aSums
        })
        t = loader.get_template('report/credit_chart.html')
        return HttpResponse(t.render(c))


def add_timer(request):
    from PManager.classes.logger.logger import Logger
    import datetime

    if not request.user.is_authenticated:
        return redirect('/')

    headerValues = headers.initGlobals(request)

    userTasks = PM_Task.objects.filter(
        active=True,
        closed=False
        # resp=request.user
    ).exclude(status__code='not_approved')
    if headerValues['CURRENT_PROJECT']:
        userTasks = userTasks.filter(project=headerValues['CURRENT_PROJECT'])

    seconds = request.POST.get('seconds', 0)
    comment = request.POST.get('comment', '')
    task_id = request.POST.get('task_id', 0)

    if seconds and comment and task_id:
        task = userTasks.get(pk=int(task_id))
        if task:
            if task.canPMUserView(request.user.get_profile()):
                # add timer
                dateEnd = datetime.datetime.now() + datetime.timedelta(seconds=int(seconds))
                timer = PM_Timer(dateEnd=dateEnd, seconds=seconds, task=task, user=request.user, comment=comment)
                timer.save()
                # add comment
                comment = PM_Task_Message(
                    task=task, text=str(timer) + '<br />' + comment, author=request.user, project=task.project,
                    hidden_from_clients=True)
                comment.save()
                # add user log
                logger = Logger()
                logger.log(request.user, 'DAILY_TIME', seconds, task.project.id)
                return redirect(
                    '/add_timer/?' + 'project=' + str(comment.project.id) + '&text=' + u'Успешно%20добавлено')
            else:
                return HttpResponse('Operation not permitted')

    tasks = []
    for task in userTasks:
        if not task.subTasks.filter(active=True).count():
            tasks.append(task)

    c = RequestContext(request, {
        'tasks': tasks
    })

    t = loader.get_template('report/add_timer.html')

    return HttpResponse(t.render(c))
