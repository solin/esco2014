from __future__ import with_statement

from django.conf.urls.defaults import patterns

from django.http import HttpResponse, HttpResponsePermanentRedirect, Http404
from django.template import RequestContext, Context, loader

from django.shortcuts import render_to_response, get_object_or_404
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required

from django.core.mail import mail_admins

from femtec.site.models import UserProfile, UserAbstract2 as UserAbstract

from femtec.site.forms import LoginForm, ReminderForm, RegistrationForm, ChangePasswordForm
from femtec.site.forms import UserProfileForm

from django.conf import settings
from femtec.settings import MIN_PASSWORD_LEN

from femtec.settings import MEDIA_ROOT, ABSTRACTS_PATH

from collections import OrderedDict

import subprocess
import os
import shutil

try:
    import json
except ImportError:
    import simplejson as json

import os
import re
import shutil
import datetime

from functools import wraps

urlpatterns = patterns('femtec.site.views',
    (r'^$',      'index_view'),
    (r'^home/$', 'index_view'),

    (r'^topics/$',        '_render_template', {'template': 'content/topics.html'}),
    (r'^committees/$',    '_render_template', {'template': 'content/committees.html'}),
    (r'^participants/$',  'participants'),
    (r'^minisymposia/$',  '_render_template', {'template': 'content/minisymposia.html'}),
    (r'^payment/$',       '_render_template', {'template': 'content/payment.html'}),
    (r'^accommodation/$', '_render_template', {'template': 'content/accommodation.html'}),
    (r'^venue/$',        '_render_template', {'template': 'content/venue.html'}),
    (r'^postconf/$',      '_render_template', {'template': 'content/postconf.html'}),
    (r'^contact/$',       '_render_template', {'template': 'content/contact.html'}),
    (r'^sponsorship/$',       '_render_template', {'template': 'content/sponsorship.html'}),
    (r'^sponsors/$',       '_render_template', {'template': 'content/sponsors.html'}),

    (r'^account/$',       '_render_template', {'template': 'account/account.html'}),

    (r'^account/login/$', 'account_login_view'),
    (r'^account/logout/$', 'account_logout_view'),

    (r'^account/create/$', 'account_create_view'),
    (r'^account/create/success/$', 'account_login_view',
        {'message': 'New account was created. You can login now.'}),

    (r'^account/delete/$', 'account_delete_view'),
    (r'^account/delete/success/$', 'index_view',
        {'message': 'Your account was successfully removed.'}),

    (r'^account/password/change/$', 'account_password_change_view'),

    (r'^account/password/remind/$', 'account_password_remind_view'),
    (r'^account/password/remind/success/$', 'account_login_view',
        {'message': 'New auto-generated password was sent to you.'}),

    (r'^account/profile/$', 'account_profile_view'),

    (r'^account/badges/tex/$', 'badges_tex'),
    (r'^account/badges/pdf/$', 'badges_pdf'),
    (r'^account/certificates/tex/$', 'certificates_tex'),
    (r'^account/certificates/pdf/$', 'certificates_pdf'),
    (r'^account/receipts/tex/$', 'receipts_tex'),
    (r'^account/receipts/pdf/$', 'receipts_pdf'),
    (r'^account/registration/tex/$', 'registration_tex'),
    (r'^account/registration/pdf/$', 'registration_pdf'),
    (r'^account/letter/tex/(\d+)/$', 'letter_tex'),
    (r'^account/letter/pdf/(\d+)/$', 'letter_pdf'),

    (r'^account/abstracts/$', 'abstracts_view'),
    (r'^account/abstracts/book/tex/$', 'abstracts_book_tex'),
    (r'^account/abstracts/book/pdf/$', 'abstracts_book_pdf'),
    (r'^account/abstracts/submit/$', 'abstracts_submit_view'),
    (r'^account/abstracts/modify/(\d+)/$', 'abstracts_modify_view'),
    (r'^account/abstracts/delete/(\d+)/$', 'abstracts_delete_view'),
    (r'^account/abstracts/tex/(\d+)/$', 'abstracts_tex_view'),
    (r'^account/abstracts/pdf/(\d+)/$', 'abstracts_pdf_view'),
    (r'^account/abstracts/log/(\d+)/$', 'abstracts_log_view'),

    (r'^admin/site/userabstract/(\d+)/tex/$', 'abstracts_tex_view'),
    (r'^admin/site/userabstract/(\d+)/pdf/$', 'abstracts_pdf_view'),
    (r'^admin/site/userabstract/(\d+)/log/$', 'abstracts_log_view'),
)


def _render_to_response(page, request, args=None):
    return render_to_response(page, RequestContext(request, args))

def _render_template(request, **args):
    conf_settings = {'conf_name_upper': settings.CONF_NAME_UPPER, 'conf_name_lower': settings.CONF_NAME_LOWER, 'conf_year': settings.CONF_YEAR, 'conf_email': settings.CONF_EMAIL,'conf_web': settings.CONF_WEB}
    return _render_to_response(args.get('template'), request, conf_settings)

def handler404(request):
    return _render_to_response('errors/404.html', request)

def handler500(request):
    return _render_to_response('errors/500.html', request)

def index_view(request, **args):
    conf_settings = {'conf_name_upper': settings.CONF_NAME_UPPER, 'conf_name_lower': settings.CONF_NAME_LOWER, 'conf_year': settings.CONF_YEAR, 'conf_email': settings.CONF_EMAIL,'conf_web': settings.CONF_WEB}
    return _render_to_response('base.html', request, conf_settings)

def participants(request, **args):
    userprofile_list = User.objects.all().order_by('last_name')
    participants = {'userprofile_list': userprofile_list}
    return _render_to_response('content/participants.html', request, participants)  

def account_login_view(request, **args):
    next = request.REQUEST.get('next', '/account/')

    if request.method == 'POST':
        if request.session.test_cookie_worked():
            request.session.delete_test_cookie()
        else:
            return HttpResponse("Please enable cookies and try again.")

        form = LoginForm(request.POST)

        if form.is_valid():
            login(request, form.user)
            request.session.set_test_cookie()

            return HttpResponsePermanentRedirect(next)
    else:
        form = LoginForm()

    request.session.set_test_cookie()

    local_args = {'form': form, 'next': next, 'conf_name_upper': settings.CONF_NAME_UPPER, 'conf_name_lower': settings.CONF_NAME_LOWER, 'conf_year': settings.CONF_YEAR, 'conf_email': settings.CONF_EMAIL,'conf_web': settings.CONF_WEB}
    local_args.update(args)

    return _render_to_response('account/login.html', request, local_args)

@login_required
def account_logout_view(request, **args):
    logout(request)

    return HttpResponsePermanentRedirect('/')

@login_required
def account_delete_view(request, **args):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()

        return HttpResponsePermanentRedirect('/account/delete/success/')
    else:
        return _render_to_response('account/delete.html', request, args)

def account_create_view(request, **args):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = User.objects.create_user(
                username = form.cleaned_data['username'], # XXX: this will get truncated
                password = form.cleaned_data['password'],
                email    = form.cleaned_data['username'],
            )

            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.save()

            if settings.SEND_EMAIL:
                conf_name_upper = settings.CONF_NAME_UPPER
                conf_year = settings.CONF_YEAR
                conf_web = settings.CONF_WEB

                template = loader.get_template('e-mails/user/create.txt')
                body = template.render(Context({'user': user, 'conf_name_upper': conf_name_upper, 'conf_year': conf_year, 'conf_web': conf_web }))

                user.email_user("[%(conf_name_upper)s %(conf_year)s] Account Creation Notification" % {'conf_name_upper': conf_name_upper, 'conf_year': conf_year }, body)

                template = loader.get_template('e-mails/admin/create.txt')
                body = template.render(Context({'user': user}))

                mail_admins("[%(conf_name_upper)s %(conf_year)s][ADMIN] New Account" % {'conf_name_upper': conf_name_upper, 'conf_year': conf_year }, body)

            return HttpResponsePermanentRedirect('/account/create/success/')
    else:
        form = RegistrationForm()

    return _render_to_response('account/create.html', request, {'form': form})

@login_required
def account_password_change_view(request, **args):
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)

        if form.is_valid():
            password = form.cleaned_data['password_new']

            request.user.set_password(password)
            request.user.save()

            form = ChangePasswordForm()

            return _render_to_response('password/change.html', request, {'form': form,
                'message': 'Your password was successfully changed.'})
    else:
        form = ChangePasswordForm()

    return _render_to_response('password/change.html', request, {'form': form})

def account_password_remind_view(request, **args):
    if request.method == 'POST':
        form = ReminderForm(request.POST)

        if form.is_valid():
            password = User.objects.make_random_password(length=MIN_PASSWORD_LEN)

            user = User.objects.get(email=form.cleaned_data['username'])
            user.set_password(password)
            user.save()

            if settings.SEND_EMAIL:
                conf_name_upper = settings.CONF_NAME_UPPER
                conf_year = settings.CONF_YEAR
                conf_web = settings.CONF_WEB

                template = loader.get_template('e-mails/user/reminder.txt')
                body = template.render(Context({'user': user, 'password': password, 'conf_web': conf_web}))

                user.email_user("[%(conf_name_upper)s %(conf_year)s] Password Reminder Notification" % {'conf_name_upper': conf_name_upper, 'conf_year': conf_year }, body)

            return HttpResponsePermanentRedirect('/account/password/remind/success/')
    else:
        form = ReminderForm()

    return _render_to_response('password/remind.html', request, {'form': form})

@login_required
def account_profile_view(request, **args):
    if request.method == 'POST':
        form = UserProfileForm(request.POST)

        if form.is_valid():
            try:
                profile = request.user.get_profile()
            except UserProfile.DoesNotExist:
                profile = UserProfile(user=request.user)

            for field in form.base_fields.iterkeys():
                if field == 'first_name':
                    first_name = form.cleaned_data.get('first_name')

                    if first_name and first_name != request.user.first_name:
                        request.user.first_name = first_name
                        request.user.save()
                elif field == 'last_name':
                    last_name = form.cleaned_data.get('last_name')

                    if last_name and last_name != request.user.last_name:
                        request.user.last_name = last_name
                        request.user.save()
                else:
                    value = form.cleaned_data.get(field)

                    if value != getattr(profile, field):
                        setattr(profile, field, value)

            profile.save()

            if settings.SEND_EMAIL:
                conf_name_upper = settings.CONF_NAME_UPPER
                conf_year = settings.CONF_YEAR
                conf_web = settings.CONF_WEB

                template = loader.get_template('e-mails/user/profile.txt')
                body = template.render(Context({'user': request.user, 'profile': profile, 'conf_name_upper': conf_name_upper, 'conf_year': conf_year, 'conf_web': conf_web}))

                request.user.email_user("[%(conf_name_upper)s %(conf_year)s] User Profile Confirmation" % {'conf_name_upper': conf_name_upper, 'conf_year': conf_year }, body)

            message = 'Your profile was updated successfully.'

            if profile.speaker:
                message += '<br />Click <a href="/account/abstracts/">here</a> to submit your abstract.'

            return _render_to_response('account/profile.html', request, {'form': form, 'message': message})
    else:
        data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
        }

        try:
            profile = request.user.get_profile()

            for field in UserProfileForm.base_fields.iterkeys():
                if field in ['first_name', 'last_name']:
                    continue

                if field in ['arrival', 'departure']:
                    data[field] = getattr(profile, field).strftime('%m/%d/%Y')
                else:
                    data[field] = getattr(profile, field)
        except UserProfile.DoesNotExist:
            pass

        form = UserProfileForm(initial=data)

    return _render_to_response('account/profile.html', request, {'form': form})

def conditional(name):
    doit = getattr(settings, name, False)

    def wrapper(func):
        if doit:
            return func
        else:
            @wraps(func)
            def _func(*args, **kwargs):
                raise Http404

            return _func

    return wrapper

def get_object_if_can(request, model, query):
    if not (request.user.is_staff and request.user.is_superuser):
        obj = get_object_or_404(UserAbstract, user=request.user, **query)
    else:
        obj = get_object_or_404(UserAbstract, **query)

    return obj

@login_required
@conditional('ENABLE_ABSTRACT_SUBMISSION')
def abstracts_view(request, **args):
    abstracts = UserAbstract.objects.filter(user=request.user)

    try:
        request.user.get_profile()
    except UserProfile.DoesNotExist:
        has_profile = False
    else:
        has_profile = True

    return _render_to_response('abstracts/abstracts.html', request, {'abstracts': abstracts, 'has_profile': has_profile})

@login_required
def badges_tex(request, **args):
    tex_template_path = os.path.join(MEDIA_ROOT, 'tex')
    tex_output_path = os.path.join(ABSTRACTS_PATH, 'badges')

    str_list = []
    f = open(os.path.join(tex_template_path, 'badges_template.tex'), 'r')
    str_list.append(f.read())
    f.close()
    
    user_list = User.objects.all().order_by('last_name')

    for i in range(len(User.objects.all())):
        try:
            full_name = user_list[i].get_full_name()
            affiliation = user_list[i].get_profile().affiliation
            city = user_list[i].get_profile().city
            country = user_list[i].get_profile().country
            str_list.append('\\card{%(full_name)s}{%(affiliation)s}{%(city)s}{%(country)s}\n' % {'full_name': full_name, 'affiliation': affiliation, 'city': city, 'country': country })
            str_list.append('\\card{%(full_name)s}{%(affiliation)s}{%(city)s}{%(country)s}\n' % {'full_name': full_name, 'affiliation': affiliation, 'city': city, 'country': country })        
        except UserProfile.DoesNotExist:
            continue

    str_list.append('\\end{document}' )
    output = ''.join(str_list)

    if os.path.exists(tex_output_path):
        shutil.rmtree(tex_output_path, True)

    os.mkdir(tex_output_path)

    with open(os.path.join(tex_output_path, 'badges.tex'), 'wb') as f:
        f.write(output.encode('utf-8'))
    f.close()

    response = HttpResponse(output, mimetype='text/plain')
    response['Content-Type'] = 'application/octet-stream'
    response['Cache-Control'] = 'must-revalidate'
    response['Content-Disposition'] = 'inline; filename=badges.tex'

    return response

@login_required
def badges_pdf(request, **args):
    tex_template_path = os.path.join(MEDIA_ROOT, 'tex')
    tex_output_path = os.path.join(ABSTRACTS_PATH, 'badges')

    str_list = []
    f = open(os.path.join(tex_template_path, 'badges_template.tex'), 'r')
    str_list.append(f.read())
    f.close()
    
    user_list = User.objects.all().order_by('last_name')

    for i in range(len(User.objects.all())):
        try:
            full_name = user_list[i].get_full_name()
            affiliation = user_list[i].get_profile().affiliation
            city = user_list[i].get_profile().city
            country = user_list[i].get_profile().country
            str_list.append('\\card{%(full_name)s}{%(affiliation)s}{%(city)s}{%(country)s}\n' % {'full_name': full_name, 'affiliation': affiliation, 'city': city, 'country': country })
            str_list.append('\\card{%(full_name)s}{%(affiliation)s}{%(city)s}{%(country)s}\n' % {'full_name': full_name, 'affiliation': affiliation, 'city': city, 'country': country })        
        except UserProfile.DoesNotExist:
            continue

    str_list.append('\\end{document}' )
    output = ''.join(str_list)

    if os.path.exists(tex_output_path):
        shutil.rmtree(tex_output_path, True)
    os.mkdir(tex_output_path)

    with open(os.path.join(tex_output_path, 'badges.tex'), 'wb') as f:
        f.write(output.encode('utf-8'))
    f.close()

    cmd = ['pdflatex', '-halt-on-error', 'badges.tex']
    pipe = subprocess.PIPE

    for i in xrange(3):
        proc = subprocess.Popen(cmd, cwd=tex_output_path, stdout=pipe, stderr=pipe)
        outputs, errors = proc.communicate()  

    f = open(os.path.join(tex_output_path, 'badges.pdf'), 'r')

    response = HttpResponse(f.read(), mimetype='application/pdf')
    response['Cache-Control'] = 'must-revalidate'
    response['Content-Disposition'] = 'inline; filename=badges.pdf'

    return response

@login_required
def abstracts_book_tex(request, **args):
    tex_template_path = os.path.join(MEDIA_ROOT, 'tex')
    tex_output_path = os.path.join(ABSTRACTS_PATH, 'abstracts_book')

    str_list = []
    f = open(os.path.join(tex_template_path, 'boa_template.tex'), 'r')
    str_list.append(f.read())
    f.close()

    abstracts = UserAbstract.objects.order_by("id")

    compiled_abstracts = {}
    compiled_authors = {}

    for abstract in abstracts:
        cls = abstract.to_cls()
        compiled_abstracts[cls.title] = cls.build_raw()
        compiled_authors[cls.title] = cls.build_presenting()

    abstract_keys = compiled_abstracts.keys()
    abstract_keys.sort()

    for a in abstract_keys:
        str_list.append(compiled_abstracts[a])
    str_list.append('\\newpage\n')
    str_list.append('\\part{List of Participants}\n')
    for a in abstract_keys:
        str_list.append(compiled_authors[a])

    str_list.append('\\end{document}')
    output = ''.join(str_list)
    output = output.replace('&amp;','&')
    output = output.replace('&lt;','<')
    output = output.replace('&gt;','>')
    output = output.replace('&quot;','"')
    output = output.replace('&#39;',"'")
    output = output.replace('&#','&\#')
    output = output.replace('displaystyleK','displaystyle')

    if os.path.exists(tex_output_path):
        shutil.rmtree(tex_output_path, True)

    os.mkdir(tex_output_path)

    shutil.copy(
        os.path.join(tex_template_path, 'llncs.cls'),
        os.path.join(tex_output_path, 'llncs.cls'))

    with open(os.path.join(tex_output_path, 'boa.tex'), 'wb') as f:
        f.write(output.encode('utf-8'))
    f.close()


    cmd = ['zip', 'boa', 'boa.tex', 'llncs.cls']
    pipe = subprocess.PIPE

    proc = subprocess.Popen(cmd, cwd=tex_output_path, stdout=pipe, stderr=pipe)
    outputs, errors = proc.communicate()  

    f = open(os.path.join(tex_output_path, 'boa.zip'), 'r')

    response = HttpResponse(f.read(), mimetype='application/zip')
    response['Cache-Control'] = 'must-revalidate'
    response['Content-Disposition'] = 'inline; filename=boa.zip'

    return response

@login_required
def abstracts_book_pdf(request, **args):
    tex_template_path = os.path.join(MEDIA_ROOT, 'tex')
    tex_output_path = os.path.join(ABSTRACTS_PATH, 'abstracts_book')

    str_list = []
    f = open(os.path.join(tex_template_path, 'boa_template.tex'), 'r')
    str_list.append(f.read())
    f.close()

    abstracts = UserAbstract.objects.order_by("id")

    compiled_abstracts = {}
    compiled_authors = {}

    for abstract in abstracts:
        cls = abstract.to_cls()
        compiled_abstracts[cls.title] = cls.build_raw()
        compiled_authors[cls.title] = cls.build_presenting()

    abstract_keys = compiled_abstracts.keys()
    abstract_keys.sort()

    for a in abstract_keys:
        str_list.append(compiled_abstracts[a])
    str_list.append('\\newpage\n')
    str_list.append('\\part{List of Participants}\n')
    for a in abstract_keys:
        str_list.append(compiled_authors[a])

    str_list.append('\\end{document}')
    output = ''.join(str_list)
    output = output.replace('&amp;','&')
    output = output.replace('&lt;','<')
    output = output.replace('&gt;','>')
    output = output.replace('&quot;','"')
    output = output.replace('&#39;',"'")
    output = output.replace('&#','&\#')
    output = output.replace('displaystyleK','displaystyle')

    if os.path.exists(tex_output_path):
        shutil.rmtree(tex_output_path, True)

    os.mkdir(tex_output_path)

    shutil.copy(
        os.path.join(tex_template_path, 'llncs.cls'),
        os.path.join(tex_output_path, 'llncs.cls'))

    with open(os.path.join(tex_output_path, 'boa.tex'), 'wb') as f:
        f.write(output.encode('utf-8'))
    f.close()

    cmd = ['pdflatex', '-halt-on-error', 'boa.tex']
    pipe = subprocess.PIPE

    for i in xrange(3):
        proc = subprocess.Popen(cmd, cwd=tex_output_path, stdout=pipe, stderr=pipe)
        outputs, errors = proc.communicate()  

    f = open(os.path.join(tex_output_path, 'boa.pdf'), 'r')

    response = HttpResponse(f.read(), mimetype='application/pdf')
    response['Cache-Control'] = 'must-revalidate'
    response['Content-Disposition'] = 'inline; filename=boa.pdf'

    return response

@login_required
def certificates_tex(request, **args):
    tex_template_path = os.path.join(MEDIA_ROOT, 'tex')
    tex_output_path = os.path.join(ABSTRACTS_PATH, 'certificates')

    str_list = []
    f = open(os.path.join(tex_template_path, 'certificates_template.tex'), 'r')
    str_list.append(f.read())
    f.close()
    
    user_list = User.objects.all().order_by('last_name')

    for i in range(len(User.objects.all())):
        try:
            full_name = user_list[i].get_full_name()
            affiliation = user_list[i].get_profile().affiliation
            address = user_list[i].get_profile().address
            postal_code = user_list[i].get_profile().postal_code
            city = user_list[i].get_profile().city
            country = user_list[i].get_profile().country
            str_list.append('\\certificate{%(full_name)s}{%(affiliation)s}{%(address)s}{%(postal_code)s}{%(city)s}{%(country)s}\n' % {'full_name': full_name, 'affiliation': affiliation,'address': address, 'postal_code' : postal_code , 'city': city, 'country': country })
        except UserProfile.DoesNotExist:
            continue

    str_list.append('\\end{document}' )
    output = ''.join(str_list)

    if os.path.exists(tex_output_path):
        shutil.rmtree(tex_output_path, True)

    os.mkdir(tex_output_path)

    shutil.copy(
        os.path.join(tex_template_path, 'femhub_logo.png'),
        os.path.join(tex_output_path, 'femhub_logo.png'))
    shutil.copy(
        os.path.join(tex_template_path, 'femhub_footer.png'),
        os.path.join(tex_output_path, 'femhub_footer.png'))

    with open(os.path.join(tex_output_path, 'certificates.tex'), 'wb') as f:
        f.write(output.encode('utf-8'))
    f.close()

    cmd = ['zip', 'certificates', 'certificates.tex', 'femhub_logo.png', 'femhub_footer.png']
    pipe = subprocess.PIPE

    proc = subprocess.Popen(cmd, cwd=tex_output_path, stdout=pipe, stderr=pipe)
    outputs, errors = proc.communicate()  

    f = open(os.path.join(tex_output_path, 'certificates.zip'), 'r')

    response = HttpResponse(f.read(), mimetype='application/zip')
    response['Cache-Control'] = 'must-revalidate'
    response['Content-Disposition'] = 'inline; filename=certificates.zip'

    return response

@login_required
def certificates_pdf(request, **args):
    tex_template_path = os.path.join(MEDIA_ROOT, 'tex')
    tex_output_path = os.path.join(ABSTRACTS_PATH, 'certificates')

    str_list = []
    f = open(os.path.join(tex_template_path, 'certificates_template.tex'), 'r')
    str_list.append(f.read())
    f.close()
    
    user_list = User.objects.all().order_by('last_name')

    for i in range(len(User.objects.all())):
        try:
            full_name = user_list[i].get_full_name()
            affiliation = user_list[i].get_profile().affiliation
            address = user_list[i].get_profile().address
            postal_code = user_list[i].get_profile().postal_code
            city = user_list[i].get_profile().city
            country = user_list[i].get_profile().country
            str_list.append('\\certificate{%(full_name)s}{%(affiliation)s}{%(address)s}{%(postal_code)s}{%(city)s}{%(country)s}\n' % {'full_name': full_name, 'affiliation': affiliation,'address': address, 'postal_code' : postal_code , 'city': city, 'country': country })
        except UserProfile.DoesNotExist:
            continue

    str_list.append('\\end{document}' )
    output = ''.join(str_list)

    if os.path.exists(tex_output_path):
        shutil.rmtree(tex_output_path, True)

    os.mkdir(tex_output_path)

    shutil.copy(
        os.path.join(tex_template_path, 'femhub_logo.png'),
        os.path.join(tex_output_path, 'femhub_logo.png'))
    shutil.copy(
        os.path.join(tex_template_path, 'femhub_footer.png'),
        os.path.join(tex_output_path, 'femhub_footer.png'))

    with open(os.path.join(tex_output_path, 'certificates.tex'), 'wb') as f:
        f.write(output.encode('utf-8'))
    f.close()

    cmd = ['pdflatex', '-halt-on-error', 'certificates.tex']
    pipe = subprocess.PIPE

    for i in xrange(3):
        proc = subprocess.Popen(cmd, cwd=tex_output_path, stdout=pipe, stderr=pipe)
        outputs, errors = proc.communicate()  

    f = open(os.path.join(tex_output_path, 'certificates.pdf'), 'r')

    response = HttpResponse(f.read(), mimetype='application/pdf')
    response['Cache-Control'] = 'must-revalidate'
    response['Content-Disposition'] = 'inline; filename=certificates.pdf'

    return response

@login_required
def receipts_tex(request, **args):
    tex_template_path = os.path.join(MEDIA_ROOT, 'tex')
    tex_output_path = os.path.join(ABSTRACTS_PATH, 'receipts')

    str_list = []
    f = open(os.path.join(tex_template_path, 'receipts_template.tex'), 'r')
    str_list.append(f.read())
    f.close()
    
    user_list = User.objects.all().order_by('last_name')

    for i in range(len(User.objects.all())):
        try:
            if not (user_list[i].get_profile().payment == ''):
                full_name = user_list[i].get_full_name()
                affiliation = user_list[i].get_profile().affiliation
                address = user_list[i].get_profile().address
                postal_code = user_list[i].get_profile().postal_code
                city = user_list[i].get_profile().city
                country = user_list[i].get_profile().country
                payment = user_list[i].get_profile().payment
                str_list.append('\\receipt{%(full_name)s}{%(affiliation)s}{%(address)s}{%(postal_code)s}{%(city)s}{%(country)s}{%(payment)s}\n' % {'full_name': full_name, 'affiliation': affiliation,'address': address, 'postal_code': postal_code, 'city': city, 'country': country, 'payment': payment})
        except UserProfile.DoesNotExist:
            continue

    str_list.append('\\end{document}' )
    output = ''.join(str_list)

    if os.path.exists(tex_output_path):
        shutil.rmtree(tex_output_path, True)

    os.mkdir(tex_output_path)

    shutil.copy(
        os.path.join(tex_template_path, 'femhub_logo.png'),
        os.path.join(tex_output_path, 'femhub_logo.png'))
    shutil.copy(
        os.path.join(tex_template_path, 'femhub_footer.png'),
        os.path.join(tex_output_path, 'femhub_footer.png'))

    with open(os.path.join(tex_output_path, 'receipts.tex'), 'wb') as f:
        f.write(output.encode('utf-8'))
    f.close()

    cmd = ['zip', 'receipts', 'receipts.tex', 'femhub_logo.png', 'femhub_footer.png']
    pipe = subprocess.PIPE

    proc = subprocess.Popen(cmd, cwd=tex_output_path, stdout=pipe, stderr=pipe)
    outputs, errors = proc.communicate()  

    f = open(os.path.join(tex_output_path, 'receipts.zip'), 'r')

    response = HttpResponse(f.read(), mimetype='application/zip')
    response['Cache-Control'] = 'must-revalidate'
    response['Content-Disposition'] = 'inline; filename=receipts.zip'

    return response

@login_required
def receipts_pdf(request, **args):
    tex_template_path = os.path.join(MEDIA_ROOT, 'tex')
    tex_output_path = os.path.join(ABSTRACTS_PATH, 'receipts')

    str_list = []
    f = open(os.path.join(tex_template_path, 'receipts_template.tex'), 'r')
    str_list.append(f.read())
    f.close()
  
    user_list = User.objects.all().order_by('last_name')

    for i in range(len(User.objects.all())):
        try:
            if not (user_list[i].get_profile().payment == ''):
                full_name = user_list[i].get_full_name()
                affiliation = user_list[i].get_profile().affiliation
                address = user_list[i].get_profile().address
                postal_code = user_list[i].get_profile().postal_code
                city = user_list[i].get_profile().city
                country = user_list[i].get_profile().country
                payment = user_list[i].get_profile().payment
                str_list.append('\\receipt{%(full_name)s}{%(affiliation)s}{%(address)s}{%(postal_code)s}{%(city)s}{%(country)s}{%(payment)s}\n' % {'full_name': full_name, 'affiliation': affiliation,'address': address, 'postal_code': postal_code, 'city': city, 'country': country, 'payment': payment})
        except UserProfile.DoesNotExist:
            continue

    str_list.append('\\end{document}' )
    output = ''.join(str_list)

    if os.path.exists(tex_output_path):
        shutil.rmtree(tex_output_path, True)

    os.mkdir(tex_output_path)

    shutil.copy(
        os.path.join(tex_template_path, 'femhub_logo.png'),
        os.path.join(tex_output_path, 'femhub_logo.png'))
    shutil.copy(
        os.path.join(tex_template_path, 'femhub_footer.png'),
        os.path.join(tex_output_path, 'femhub_footer.png'))

    with open(os.path.join(tex_output_path, 'receipts.tex'), 'wb') as f:
        f.write(output.encode('utf-8'))
    f.close()

    cmd = ['pdflatex', '-halt-on-error', 'receipts.tex']
    pipe = subprocess.PIPE

    for i in xrange(3):
        proc = subprocess.Popen(cmd, cwd=tex_output_path, stdout=pipe, stderr=pipe)
        outputs, errors = proc.communicate()  

    f = open(os.path.join(tex_output_path, 'receipts.pdf'), 'r')

    response = HttpResponse(f.read(), mimetype='application/pdf')
    response['Cache-Control'] = 'must-revalidate'
    response['Content-Disposition'] = 'inline; filename=receipts.pdf'

    return response

@login_required
def registration_tex(request, **args):
    tex_template_path = os.path.join(MEDIA_ROOT, 'tex')
    tex_output_path = os.path.join(ABSTRACTS_PATH, 'registration')

    str_list = []
    f = open(os.path.join(tex_template_path, 'registration_template.tex'), 'r')
    str_list.append(f.read())
    f.close()
    
    user_list = User.objects.all().order_by('last_name')

    for i in range(len(User.objects.all())):
        try:
            last_name = user_list[i].last_name
            first_name = user_list[i].first_name
            affiliation = user_list[i].get_profile().affiliation
            tshirt = user_list[i].get_profile().tshirt
            departure = user_list[i].get_profile().departure
            str_list.append('\\registration{%(last_name)s}{%(first_name)s}{%(affiliation)s}{%(tshirt)s}{%(departure)s}\n' % {'last_name': last_name, 'first_name': first_name, 'affiliation': affiliation,'tshirt': tshirt, 'departure': departure})
        except UserProfile.DoesNotExist:
            continue

    str_list.append('\\end{longtable}' )
    str_list.append('\\end{landscape}' )
    str_list.append('\\end{document}' )
    output = ''.join(str_list)

    if os.path.exists(tex_output_path):
        shutil.rmtree(tex_output_path, True)

    os.mkdir(tex_output_path)

    with open(os.path.join(tex_output_path, 'registration.tex'), 'wb') as f:
        f.write(output.encode('utf-8'))
    f.close()

    f = open(os.path.join(tex_output_path, 'registration.tex'), 'r')

    response = HttpResponse(f.read(), mimetype='application/octet-stream')
    response['Cache-Control'] = 'must-revalidate'
    response['Content-Disposition'] = 'inline; filename=registration.tex'

    return response

@login_required
def registration_pdf(request, **args):
    tex_template_path = os.path.join(MEDIA_ROOT, 'tex')
    tex_output_path = os.path.join(ABSTRACTS_PATH, 'registration')

    str_list = []
    f = open(os.path.join(tex_template_path, 'registration_template.tex'), 'r')
    str_list.append(f.read())
    f.close()
    
    user_list = User.objects.all().order_by('last_name')

    for i in range(len(User.objects.all())):
        try:
            last_name = user_list[i].last_name
            first_name = user_list[i].first_name
            affiliation = user_list[i].get_profile().affiliation
            tshirt = user_list[i].get_profile().tshirt
            departure = user_list[i].get_profile().departure
            str_list.append('\\registration{%(last_name)s}{%(first_name)s}{%(affiliation)s}{%(tshirt)s}{%(departure)s}\n' % {'last_name': last_name, 'first_name': first_name, 'affiliation': affiliation,'tshirt': tshirt, 'departure': departure})
        except UserProfile.DoesNotExist:
            continue

    str_list.append('\\end{longtable}' )
    str_list.append('\\end{landscape}' )
    str_list.append('\\end{document}' )
    output = ''.join(str_list)

    if os.path.exists(tex_output_path):
        shutil.rmtree(tex_output_path, True)

    os.mkdir(tex_output_path)

    with open(os.path.join(tex_output_path, 'registration.tex'), 'wb') as f:
        f.write(output.encode('utf-8'))
    f.close()

    cmd = ['pdflatex', '-halt-on-error', 'registration.tex']
    pipe = subprocess.PIPE

    for i in xrange(3):
        proc = subprocess.Popen(cmd, cwd=tex_output_path, stdout=pipe, stderr=pipe)
        outputs, errors = proc.communicate()  

    f = open(os.path.join(tex_output_path, 'registration.pdf'), 'r')

    response = HttpResponse(f.read(), mimetype='application/pdf')
    response['Cache-Control'] = 'must-revalidate'
    response['Content-Disposition'] = 'inline; filename=registration.pdf'

    return response


@login_required
def letter_tex(request, profile_id, **args):
    tex_template_path = os.path.join(MEDIA_ROOT, 'tex')
    tex_letters_path = os.path.join(ABSTRACTS_PATH, 'letters')
    tex_output_path = os.path.join(tex_letters_path, profile_id)

    str_list = []
    f = open(os.path.join(tex_template_path, 'letter_template.tex'), 'r')
    str_list.append(f.read())
    f.close()
    
    person = UserProfile.objects.get(id = profile_id)
    user_id = person.user_id
    first_name = person.user.first_name
    last_name = person.user.last_name
    full_name = person.user.get_full_name()
    affiliation = person.affiliation
    city = person.city
    country = person.country
    address = person.address
    postal_code = person.postal_code

    userabstract_list = UserAbstract.objects.all()  

    abstractstr = ''
    appended_s = ''
    counter = 0

    for i in range(len(userabstract_list) + 1):
        try:
            if user_id == UserAbstract.objects.get(id = i + 1).user_id:
                abstract_title = UserAbstract.objects.get(id = i + 1).to_cls().title
                abstractstr += (abstract_title.encode('utf-8') + ' and ')
                counter += 1
        except UserAbstract.DoesNotExist:
            continue

    if counter == 0:
        return HttpResponse('TeX file incomplete - the user has not submited the Abstract!')

    if (counter > 1):
        appended_s = 's'
    abstractstr = abstractstr[:-5]

    str_list.append('\\letter{%(full_name)s}{%(affiliation)s}{%(address)s}{%(city)s}{%(postal_code)s}{%(country)s}{' % {'full_name': full_name, 'affiliation': affiliation,'address': address, 'city': city, 'postal_code' : postal_code, 'country': country})
    str_list.append('%(abstractstr)s}{%(appended_s)s}\n' % {'abstractstr': abstractstr, 'appended_s': appended_s} )
    str_list.append('\\end{document}' )
    output = ''.join(str_list)

    if os.path.exists(tex_output_path):
        shutil.rmtree(tex_output_path, True)

    os.mkdir(tex_output_path)

    shutil.copy(
        os.path.join(tex_template_path, 'horizon_no_slogan.jpg'),
        os.path.join(tex_output_path, 'horizon_no_slogan.jpg'))

    filename = 'letter_%(last_name)s_%(first_name)s' % {'first_name': first_name, 'last_name': last_name}  
    filename_tex = 'letter_%(last_name)s_%(first_name)s.tex' % {'first_name': first_name, 'last_name': last_name} 
    filename_zip = 'letter_%(last_name)s_%(first_name)s.zip' % {'first_name': first_name, 'last_name': last_name} 

    with open(os.path.join(tex_output_path, filename_tex), 'wb') as f:
        f.write(output.encode('utf-8'))
    f.close()

    cmd = ['zip', filename, filename_tex, 'horizon_no_slogan.jpg']
    pipe = subprocess.PIPE

    proc = subprocess.Popen(cmd, cwd=tex_output_path, stdout=pipe, stderr=pipe)
    outputs, errors = proc.communicate()  

    f = open(os.path.join(tex_output_path, filename_zip), 'r')

    response = HttpResponse(f.read(), mimetype='application/zip')
    response['Cache-Control'] = 'must-revalidate'
    response['Content-Disposition'] = 'inline; filename=letter_%(last_name)s_%(first_name)s.zip' % {'first_name': first_name, 'last_name': last_name}

    return response

@login_required
def letter_pdf(request, profile_id, **args):
    tex_template_path = os.path.join(MEDIA_ROOT, 'tex')
    tex_letters_path = os.path.join(ABSTRACTS_PATH, 'letters')
    tex_output_path = os.path.join(tex_letters_path, profile_id)

    str_list = []
    f = open(os.path.join(tex_template_path, 'letter_template.tex'), 'r')
    str_list.append(f.read())
    f.close()
    
    person = UserProfile.objects.get(id = profile_id)
    user_id = person.user_id
    first_name = person.user.first_name
    last_name = person.user.last_name
    full_name = person.user.get_full_name()
    affiliation = person.affiliation
    city = person.city
    country = person.country
    address = person.address
    postal_code = person.postal_code

    userabstract_list = UserAbstract.objects.all()  

    abstractstr = ''
    appended_s = ''
    counter = 0

    for i in range(len(userabstract_list) + 1):
        try:
            if user_id == UserAbstract.objects.get(id = i + 1).user_id:
                abstract_title = UserAbstract.objects.get(id = i + 1).to_cls().title
                abstractstr += (abstract_title.encode('utf-8') + ' and ')
                counter += 1
        except UserAbstract.DoesNotExist:
            continue

    if counter == 0:
        return HttpResponse('Impossible to generate PDF file - the user has not submited the Abstract!')

    if (counter > 1):
        appended_s = 's'
    abstractstr = abstractstr[:-5]

    str_list.append('\\letter{%(full_name)s}{%(affiliation)s}{%(address)s}{%(city)s}{%(postal_code)s}{%(country)s}{' % {'full_name': full_name, 'affiliation': affiliation,'address': address, 'city': city, 'postal_code' : postal_code, 'country': country})
    str_list.append('%(abstractstr)s}{%(appended_s)s}\n' % {'abstractstr': abstractstr, 'appended_s': appended_s} )
    str_list.append('\\end{document}' )
    output = ''.join(str_list)

    if os.path.exists(tex_output_path):
        shutil.rmtree(tex_output_path, True)

    os.mkdir(tex_output_path)

    shutil.copy(
        os.path.join(tex_template_path, 'horizon_no_slogan.jpg'),
        os.path.join(tex_output_path, 'horizon_no_slogan.jpg'))

    filename = 'letter_%(last_name)s_%(first_name)s.tex' % {'first_name': first_name, 'last_name': last_name}
    filename_pdf = 'letter_%(last_name)s_%(first_name)s.pdf' % {'first_name': first_name, 'last_name': last_name}

    with open(os.path.join(tex_output_path, filename), 'wb') as f:
        f.write(output.encode('utf-8'))
    f.close()

    cmd = ['pdflatex', '-halt-on-error', filename]
    pipe = subprocess.PIPE

    for i in xrange(3):
        proc = subprocess.Popen(cmd, cwd=tex_output_path, stdout=pipe, stderr=pipe)
        outputs, errors = proc.communicate()  

    f = open(os.path.join(tex_output_path, filename_pdf), 'r')

    response = HttpResponse(f.read(), mimetype='application/pdf')
    response['Cache-Control'] = 'must-revalidate'
    response['Content-Disposition'] = 'inline; filename=letter_%(last_name)s_%(first_name)s.pdf' % {'first_name': first_name, 'last_name': last_name}

    return response

def get_submit_form_data(post, user):
    title = post['title']
    abstract = post['abstract']

    first_names = post.getlist('first_name')
    last_names = post.getlist('last_name')
    full_names = ['']*len(first_names)
    affiliations = post.getlist('affiliation')
    emails = post.getlist('email')
    presentings = ['no']*len(first_names)

    #bibitems_bibid = post.getlist('bibitem_bibid')
    bibitems_authors = post.getlist('bibitem_authors')
    bibitems_title = post.getlist('bibitem_title')
    bibitems_other = post.getlist('bibitem_other')

    for i, (first_name, last_name) in enumerate(zip(first_names, last_names)):
        if (first_name == user.first_name and last_name == user.last_name):
            presentings[i] = 'yes'
            break

    for i, (first_name, last_name) in enumerate(zip(first_names, last_names)):
        full_names[i] = first_names[i] + ' ' + last_names[i]

    authors = zip(first_names, last_names, full_names, affiliations, emails, presentings)
    fields = ('first_name', 'last_name', 'full_name', 'affiliation', 'email', 'presenting')

    for i, author in enumerate(authors):
        author = dict(zip(fields, author))
        authors[i] = author

    fields = ('bibauthor_first_name', 'bibauthor_last_name')
    bibitems_authors = [[ dict(zip(fields, re.split("\s+", author, 1)))
        for author in re.split("\s*,\s*", bibitem_authors) ] for bibitem_authors in bibitems_authors ]

    #bibitems = zip(bibitems_bibid, bibitems_authors, bibitems_title, bibitems_other)
    #fields = ('bibid', 'authors', 'title', 'other')
    
    bibitems = zip(bibitems_authors, bibitems_title, bibitems_other)
    fields = ('bibitem_authors', 'bibitem_title', 'bibitem_other')

    for i, bibitem in enumerate(bibitems):
        bibitem = dict(zip(fields, bibitem))
        bibitems[i] = bibitem

    authgroup_authors = zip(full_names, emails, presentings)
    fields = ('auth_full_name', 'auth_email', 'auth_presenting')

    for i, authgroups_author in enumerate(authgroup_authors):
        authgroups_author = dict(zip(fields, authgroups_author))
        authgroup_authors[i] = authgroups_author
  
    res = OrderedDict()
    for v, k in zip(authgroup_authors, affiliations):
        if k in res:
            res[k].append(v)
        else:
            res[k] = [v]

    authgroups = [{'authgroup_authors':v, 'authgroup_affiliation':k,} for k,v in res.items()]

    data = {
        'title': title,
        'abstract': abstract,
        'authors': authors,
        'bibitems': bibitems,
        'authgroups' : authgroups,
    }

    return json.dumps(data)

@login_required
@conditional('ENABLE_ABSTRACT_SUBMISSION')
def abstracts_submit_view(request, **args):
    conf_settings = {'conf_name_upper': settings.CONF_NAME_UPPER, 'conf_name_lower': settings.CONF_NAME_LOWER, 'conf_year': settings.CONF_YEAR, 'conf_email': settings.CONF_EMAIL,'conf_web': settings.CONF_WEB}
    if request.method == 'POST':
        post = request.POST

        data = get_submit_form_data(post, request.user)
        date = datetime.datetime.today()

        abstract = UserAbstract(
            user=request.user,
            data=data,
            submit_date=date,
            modify_date=date,
        )

        abstract.save()

        cls = abstract.to_cls()
        compiled = cls.build(abstract.get_path())

        abstract.compiled = compiled
        abstract.save()

        if settings.SEND_EMAIL:
            conf_name_upper = settings.CONF_NAME_UPPER
            conf_year = settings.CONF_YEAR
            
            template = loader.get_template('e-mails/user/abstract.txt')
            body = template.render(Context({'user': request.user, 'abstract': abstract, 'conf_name_upper': conf_name_upper, 'conf_year': conf_year}))

            request.user.email_user("[%(conf_name_upper)s %(conf_year)s] Abstract Submission Notification" % {'conf_name_upper': conf_name_upper, 'conf_year': conf_year }, body)

            template = loader.get_template('e-mails/admin/abstract.txt')
            body = template.render(Context({'user': request.user, 'abstract': abstract}))

            mail_admins("[%(conf_name_upper)s %(conf_year)s][ADMIN] New Abstract" % {'conf_name_upper': conf_name_upper, 'conf_year': conf_year }, body)

        return HttpResponsePermanentRedirect('/account/abstracts/')
    else:
        return _render_to_response('abstracts/submit.html', request, conf_settings)

@login_required
@conditional('ENABLE_ABSTRACT_SUBMISSION')
def abstracts_modify_view(request, abstract_id, **args):
    abstract = get_object_or_404(UserAbstract, pk=abstract_id, user=request.user)

    if request.method == 'POST':
        post = request.POST

        data = get_submit_form_data(post, request.user)
        date = datetime.datetime.today()

        abstract.data = data
        abstract.verified = None
        abstract.modify_date = date
        abstract.save()

        cls = abstract.to_cls()
        compiled = cls.build(abstract.get_path())

        abstract.compiled = compiled
        abstract.save()

        return HttpResponsePermanentRedirect('/account/abstracts/')
    else:
        return _render_to_response('abstracts/modify.html', request, dict(initial=abstract.data))

@login_required
@conditional('ENABLE_ABSTRACT_SUBMISSION')
def abstracts_delete_view(request, abstract_id, **args):
    try:
        abstract = get_object_or_404(UserAbstract, pk=abstract_id, user=request.user)
    except UserAbstract.DoesNotExist:
        pass # don't care about missing abstract
    else:
        shutil.rmtree(abstract.get_path(), True)
        abstract.delete()

    return HttpResponsePermanentRedirect('/account/abstracts/')

@login_required
@conditional('ENABLE_ABSTRACT_SUBMISSION')
def abstracts_tex_view(request, abstract_id, **args):
    abstract = get_object_if_can(request, UserAbstract, dict(pk=abstract_id))
    tex = abstract.get_data_or_404("tex")

    response = HttpResponse(tex, mimetype='text/plain')
    response['Content-Type'] = 'application/octet-stream'
    response['Cache-Control'] = 'must-revalidate'
    response['Content-Disposition'] = 'inline; filename=abstract.tex'

    return response

@login_required
@conditional('ENABLE_ABSTRACT_SUBMISSION')
def abstracts_pdf_view(request, abstract_id, **args):
    abstract = get_object_if_can(request, UserAbstract, dict(pk=abstract_id))
    pdf = abstract.get_data_or_404("pdf")

    response = HttpResponse(pdf, mimetype='application/pdf')
    response['Cache-Control'] = 'must-revalidate'
    response['Content-Disposition'] = 'inline; filename=abstract.pdf'

    return response

@login_required
@conditional('ENABLE_ABSTRACT_SUBMISSION')
def abstracts_log_view(request, abstract_id, **args):
    abstract = get_object_if_can(request, UserAbstract, dict(pk=abstract_id))
    log = abstract.get_data_or_404("log")

    response = HttpResponse(log, mimetype='text/plain')
    response['Cache-Control'] = 'must-revalidate'
    response['Content-Disposition'] = 'inline; filename=abstract.log'

    return response

