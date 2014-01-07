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
from django.db.models import Max
from django.conf import settings

from conference.site.models import UserProfile, UserAbstract2 as UserAbstract
from conference.site.forms import LoginForm, ReminderForm, RegistrationForm, ChangePasswordForm
from conference.site.forms import UserProfileForm

from conference.settings import MIN_PASSWORD_LEN
from conference.settings import MEDIA_ROOT, ABSTRACTS_PATH

from conference.site.myordereddict import MyOrderedDict

import zipfile

from conference.site.latex_replacement import latex_replacement

try:
    import json
except ImportError:
    import simplejson as json

import os
import re
import shutil
import datetime
import subprocess
from functools import wraps

urlpatterns = patterns('conference.site.views',
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

    (r'^admin/logout/$', 'admin_logout_view'),

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

    (r'^account/program_tex/$', 'program_tex'),
    (r'^account/csv_export/$', 'csv_export'),

    (r'^account/badges/tex/$', 'badges_tex'),
    (r'^account/badges/pdf/$', 'badges_pdf'),
    (r'^account/certificates/tex/$', 'certificates_tex'),
    (r'^account/certificates/pdf/$', 'certificates_pdf'),
    (r'^account/all_certificates/$', 'all_certificates'),
    (r'^account/certificate/tex/(\d+)/$', 'certificate_tex'),
    (r'^account/certificate/pdf/(\d+)/$', 'certificate_pdf'),
    (r'^account/receipts/tex/$', 'receipts_tex'),
    (r'^account/receipts/pdf/$', 'receipts_pdf'),
    (r'^account/all_receipts/$', 'all_receipts'),
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

def userprofile_counter():
    user_count = 0
    user_list = User.objects.all().order_by('last_name')
    for user in user_list:
        try:
            if user.get_profile() != None:
                user_count = user_count + 1
        except UserProfile.DoesNotExist:
            continue
    return user_count

def _render_to_response(page, request, args=None):
    return render_to_response(page, RequestContext(request, args))

def _render_template(request, **args):
    local_args = {'user_count': userprofile_counter(), 'conf_name_upper': settings.CONF_NAME_UPPER, 'conf_name_lower': settings.CONF_NAME_LOWER, 'conf_year': settings.CONF_YEAR, 'conf_email': settings.CONF_EMAIL,'conf_web': settings.CONF_WEB}
    return _render_to_response(args.get('template'), request, local_args)

def handler404(request):
    return _render_to_response('errors/404.html', request)

def handler500(request):
    return _render_to_response('errors/500.html', request)

def index_view(request, **args):
    local_args = {'user_count': userprofile_counter(), 'conf_name_upper': settings.CONF_NAME_UPPER, 'conf_name_lower': settings.CONF_NAME_LOWER, 'conf_year': settings.CONF_YEAR, 'conf_email': settings.CONF_EMAIL,'conf_web': settings.CONF_WEB}
    return _render_to_response('base.html', request, local_args)

def participants(request, **args):
    user_list = User.objects.all().order_by('last_name')
    local_args = {'user_count': userprofile_counter(), 'user_list': user_list, 'conf_name_upper': settings.CONF_NAME_UPPER, 'conf_name_lower': settings.CONF_NAME_LOWER, 'conf_year': settings.CONF_YEAR, 'conf_email': settings.CONF_EMAIL,'conf_web': settings.CONF_WEB}
    return _render_to_response('content/participants.html', request, local_args)  

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

    local_args = {'form': form, 'next': next, 'user_count': userprofile_counter(), 'conf_name_upper': settings.CONF_NAME_UPPER, 'conf_name_lower': settings.CONF_NAME_LOWER, 'conf_year': settings.CONF_YEAR, 'conf_email': settings.CONF_EMAIL,'conf_web': settings.CONF_WEB}
    local_args.update(args)

    return _render_to_response('account/login.html', request, local_args)

@login_required
def account_logout_view(request, **args):
    logout(request)

    return HttpResponsePermanentRedirect('/')

@login_required
def admin_logout_view(request, **args):
    logout(request)

    return HttpResponsePermanentRedirect('/admin')

@login_required
def account_delete_view(request, **args):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()

        return HttpResponsePermanentRedirect('/account/delete/success/')
    else:
        local_args = {'user_count': userprofile_counter(), 'conf_name_upper': settings.CONF_NAME_UPPER, 'conf_name_lower': settings.CONF_NAME_LOWER, 'conf_year': settings.CONF_YEAR, 'conf_email': settings.CONF_EMAIL,'conf_web': settings.CONF_WEB}
        return _render_to_response('account/delete.html', request, local_args)

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

                template = loader.get_template('e-mails/user/create.txt')
                body = template.render(Context({'user': user, 'conf_name_upper': settings.CONF_NAME_UPPER, 'conf_year': settings.CONF_YEAR, 'conf_web': settings.CONF_WEB}))

                user.email_user("[%(conf_name_upper)s %(conf_year)s] Account Creation Notification" % {'conf_name_upper': settings.CONF_NAME_UPPER, 'conf_year': settings.CONF_YEAR}, body)

                template = loader.get_template('e-mails/admin/create.txt')
                body = template.render(Context({'user': user}))

                mail_admins("[ADMIN] New Account", body)

            return HttpResponsePermanentRedirect('/account/create/success/')
    else:
        form = RegistrationForm()

    local_args = {'form': form, 'conf_name_upper': settings.CONF_NAME_UPPER, 'conf_name_lower': settings.CONF_NAME_LOWER, 'conf_year': settings.CONF_YEAR, 'conf_email': settings.CONF_EMAIL,'conf_web': settings.CONF_WEB}

    return _render_to_response('account/create.html', request, local_args)

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

    local_args = {'form': form, 'user_count': userprofile_counter(), 'conf_name_upper': settings.CONF_NAME_UPPER, 'conf_name_lower': settings.CONF_NAME_LOWER, 'conf_year': settings.CONF_YEAR, 'conf_email': settings.CONF_EMAIL,'conf_web': settings.CONF_WEB}

    return _render_to_response('password/change.html', request, local_args)

def account_password_remind_view(request, **args):
    if request.method == 'POST':
        form = ReminderForm(request.POST)

        if form.is_valid():
            password = User.objects.make_random_password(length=MIN_PASSWORD_LEN)

            user = User.objects.get(email=form.cleaned_data['username'])
            user.set_password(password)
            user.save()

            if settings.SEND_EMAIL:

                template = loader.get_template('e-mails/user/reminder.txt')
                body = template.render(Context({'user': user, 'password': password, 'conf_web': settings.CONF_WEB}))

                user.email_user("[%(conf_name_upper)s %(conf_year)s] Password Reminder Notification" % {'conf_name_upper': settings.CONF_NAME_UPPER, 'conf_year': settings.CONF_YEAR}, body)

            return HttpResponsePermanentRedirect('/account/password/remind/success/')
    else:
        form = ReminderForm()

    local_args = {'form': form, 'user_count': userprofile_counter(), 'conf_name_upper': settings.CONF_NAME_UPPER, 'conf_name_lower': settings.CONF_NAME_LOWER, 'conf_year': settings.CONF_YEAR, 'conf_email': settings.CONF_EMAIL,'conf_web': settings.CONF_WEB}

    return _render_to_response('password/remind.html', request, local_args)

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

                template = loader.get_template('e-mails/user/profile.txt')
                body = template.render(Context({'user': request.user, 'profile': profile, 'conf_name_upper': settings.CONF_NAME_UPPER, 'conf_year': settings.CONF_YEAR, 'conf_web': settings.CONF_WEB}))

                request.user.email_user("[%(conf_name_upper)s %(conf_year)s] User Profile Confirmation" % {'conf_name_upper': settings.CONF_NAME_UPPER, 'conf_year': settings.CONF_YEAR}, body)

            message = 'Your profile was updated successfully.'

            if profile.speaker:
                message += '<br />Click <a href="/account/abstracts/">here</a> to submit your abstract.'

            local_args = {'form': form, 'message': message, 'user_count': userprofile_counter(), 'conf_name_upper': settings.CONF_NAME_UPPER, 'conf_name_lower': settings.CONF_NAME_LOWER, 'conf_year': settings.CONF_YEAR, 'conf_email': settings.CONF_EMAIL,'conf_web': settings.CONF_WEB}

            return _render_to_response('account/profile.html', request, local_args)
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
                    data[field] = getattr(profile, field).strftime('%d/%m/%Y')
                else:
                    data[field] = getattr(profile, field)

        except UserProfile.DoesNotExist:
            pass

        form = UserProfileForm(initial=data)

    local_args = {'form': form, 'user_count': userprofile_counter(), 'conf_name_upper': settings.CONF_NAME_UPPER, 'conf_name_lower': settings.CONF_NAME_LOWER, 'conf_year': settings.CONF_YEAR, 'conf_email': settings.CONF_EMAIL,'conf_web': settings.CONF_WEB}

    return _render_to_response('account/profile.html', request, local_args)

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

def zipdir(path, zip):
    for root, dirs, files in os.walk(path):
        for file in files:
            zip.write(os.path.join(root, file))

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

    local_args = {'abstracts': abstracts, 'has_profile': has_profile, 'user_count': userprofile_counter(), 'conf_name_upper': settings.CONF_NAME_UPPER, 'conf_name_lower': settings.CONF_NAME_LOWER, 'conf_year': settings.CONF_YEAR, 'conf_email': settings.CONF_EMAIL,'conf_web': settings.CONF_WEB}

    return _render_to_response('abstracts/abstracts.html', request, local_args)

def badges():
    tex_template_path = os.path.join(MEDIA_ROOT, 'tex')
    tex_output_path = os.path.join(ABSTRACTS_PATH, 'badges')

    str_list_to_modify = []
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
            str_list_to_modify.append('\\card{%(full_name)s}{%(affiliation)s}{%(city)s}{%(country)s}\n' % {'full_name': full_name, 'affiliation': affiliation, 'city': city, 'country': country })
            str_list_to_modify.append('\\card{%(full_name)s}{%(affiliation)s}{%(city)s}{%(country)s}\n' % {'full_name': full_name, 'affiliation': affiliation, 'city': city, 'country': country })        
        except UserProfile.DoesNotExist:
            continue

    str_list.append(latex_replacement(''.join(str_list_to_modify)))
    str_list.append('\\end{document}' )
    output = ''.join(str_list)

    if os.path.exists(tex_output_path):
        shutil.rmtree(tex_output_path, True)

    os.mkdir(tex_output_path)

    with open(os.path.join(tex_output_path, 'badges.tex'), 'wb') as f:
        f.write(output.encode('utf-8'))
    f.close()

    return tex_output_path

@login_required
def badges_tex(request, **args):
    tex_output_path = badges()
    
    f = open(os.path.join(tex_output_path, 'badges.tex'), 'r')    

    response = HttpResponse(f.read(), mimetype='application/octet-stream')
    response['Cache-Control'] = 'must-revalidate'
    response['Content-Disposition'] = 'inline; filename=badges.tex'
    return response

@login_required
def badges_pdf(request, **args):
    tex_output_path = badges()

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

def abstracts_book():
    tex_template_path = os.path.join(MEDIA_ROOT, 'tex')
    tex_output_path = os.path.join(ABSTRACTS_PATH, 'abstracts_book')

    str_list = []
    f = open(os.path.join(tex_template_path, 'boa_template.tex'), 'r')
    str_list.append(f.read())
    f.close()

    compiled_abstracts = {}
    compiled_authors = {}

    str_list.append('\\part{List of Participants}\n')

    abstracts = UserAbstract.objects.order_by("user__last_name", "id")

    for abstract in abstracts:
        cls = abstract.to_cls()
        str_list.append(cls.build_raw())

    str_list.append('\\newpage\n')

    for abstract in abstracts:
        cls = abstract.to_cls()
        str_list.append(cls.build_presenting())


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

    return tex_output_path

@login_required
def abstracts_book_tex(request, **args):
    tex_output_path = abstracts_book()

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

    for i in range(len(UserAbstract.objects.all())):
        try:
            if (UserAbstract.objects.order_by("id")[i].compiled == False):
                return HttpResponse('Impossible to generate PDF file of Book of Abstracts - some Abstract is not correctly compiled!')
        except UserAbstract.DoesNotExist:
            continue

    tex_output_path = abstracts_book()

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

def all_certificates(request, **args):

    max_profile_id_dict = UserProfile.objects.all().aggregate(Max('id'))
    max_profile_id = max_profile_id_dict['id__max']

    tex_template_path = os.path.join(MEDIA_ROOT, 'tex')
    tex_certificate_path = os.path.join(ABSTRACTS_PATH, 'certificates')  
    tex_individual_certificate_path = os.path.join(tex_certificate_path, 'individual_certificates')  

    for i in range(1, max_profile_id + 1):
        str_list_to_modify = []
        str_list = []
        f = open(os.path.join(tex_template_path, 'certificates_template.tex'), 'r')
        str_list.append(f.read())
        f.close()
    
        try:
            person = UserProfile.objects.get(id = i)
            first_name = person.user.first_name
            last_name = person.user.last_name
            full_name = person.user.get_full_name()
            affiliation = person.affiliation
            address = person.address
            postal_code = person.postal_code
            city = person.city
            country = person.country
        except UserProfile.DoesNotExist:
            pass
    
        filename = create_filename(first_name, last_name)
        tex_output_path = os.path.join(tex_individual_certificate_path, filename)

        str_list_to_modify.append('\\certificate{%(full_name)s}{%(affiliation)s}{%(address)s}{%(postal_code)s}{%(city)s}{%(country)s}\n' % {'full_name': full_name, 'affiliation': affiliation,'address': address, 'postal_code' : postal_code , 'city': city, 'country': country })
        str_list.append(latex_replacement(''.join(str_list_to_modify)))
        str_list.append('\\end{document}' )
        output = ''.join(str_list)

        if os.path.exists(tex_output_path):
            shutil.rmtree(tex_output_path, True)

        if not os.path.exists(tex_certificate_path):
            os.mkdir(tex_certificate_path)

        if not os.path.exists(tex_individual_certificate_path):
            os.mkdir(tex_individual_certificate_path)

        os.mkdir(tex_output_path)

        shutil.copy(
            os.path.join(tex_template_path, 'femhub_logo.png'),
            os.path.join(tex_output_path, 'femhub_logo.png'))
        shutil.copy(
            os.path.join(tex_template_path, 'femhub_footer.png'),
            os.path.join(tex_output_path, 'femhub_footer.png'))

        filename_tex = filename + '.tex'
  
        with open(os.path.join(tex_output_path, filename_tex), 'wb') as f:
            f.write(output.encode('utf-8'))
        f.close()

        cmd = ['pdflatex', '-halt-on-error', filename_tex]
        pipe = subprocess.PIPE
    
        for i in xrange(3):
            proc = subprocess.Popen(cmd, cwd=tex_output_path, stdout=pipe, stderr=pipe)
            outputs, errors = proc.communicate()

        os.remove(os.path.join(tex_output_path, filename + '.log'))
        os.remove(os.path.join(tex_output_path, filename + '.aux'))

    filename_zip = 'individual_certificates.zip'

    zip = zipfile.ZipFile(os.path.join(tex_certificate_path, filename_zip), 'w')
    zipdir(tex_individual_certificate_path, zip)
    zip.close()    

    f = open(os.path.join(tex_certificate_path, filename_zip), 'r')

    response = HttpResponse(f.read(), mimetype='application/zip')
    response['Cache-Control'] = 'must-revalidate'
    response['Content-Disposition'] = 'inline; filename=%(filename_zip)s' % {'filename_zip': filename_zip}
    return response

def certificate(profile_id):
    tex_template_path = os.path.join(MEDIA_ROOT, 'tex')
    tex_certificate_path = os.path.join(ABSTRACTS_PATH, 'certificates')  

    str_list_to_modify = []
    str_list = []
    f = open(os.path.join(tex_template_path, 'certificates_template.tex'), 'r')
    str_list.append(f.read())
    f.close()
    
    try:
        person = UserProfile.objects.get(id = profile_id)
        first_name = person.user.first_name
        last_name = person.user.last_name
        full_name = person.user.get_full_name()
        affiliation = person.affiliation
        address = person.address
        postal_code = person.postal_code
        city = person.city
        country = person.country
    except UserProfile.DoesNotExist:
        pass
    
    filename = create_filename(first_name, last_name)
    tex_output_path = os.path.join(tex_certificate_path, filename)

    str_list_to_modify.append('\\certificate{%(full_name)s}{%(affiliation)s}{%(address)s}{%(postal_code)s}{%(city)s}{%(country)s}\n' % {'full_name': full_name, 'affiliation': affiliation,'address': address, 'postal_code' : postal_code , 'city': city, 'country': country })
    str_list.append(latex_replacement(''.join(str_list_to_modify)))
    str_list.append('\\end{document}' )
    output = ''.join(str_list)

    if os.path.exists(tex_output_path):
        shutil.rmtree(tex_output_path, True)

    if not os.path.exists(tex_certificate_path):
        os.mkdir(tex_certificate_path)

    os.mkdir(tex_output_path)

    shutil.copy(
        os.path.join(tex_template_path, 'femhub_logo.png'),
        os.path.join(tex_output_path, 'femhub_logo.png'))
    shutil.copy(
        os.path.join(tex_template_path, 'femhub_footer.png'),
        os.path.join(tex_output_path, 'femhub_footer.png'))
  
    with open(os.path.join(tex_output_path, filename + '.tex'), 'wb') as f:
        f.write(output.encode('utf-8'))
    f.close()

    return tex_output_path, filename

@login_required
def certificate_tex(request, profile_id, **args):
    tex_output_path, filename = certificate(profile_id)

    filename_tex = filename + '.tex'
    filename_zip = filename + '.zip'

    cmd = ['zip', filename, filename_tex, 'femhub_logo.png', 'femhub_footer.png']
    pipe = subprocess.PIPE

    proc = subprocess.Popen(cmd, cwd=tex_output_path, stdout=pipe, stderr=pipe)
    outputs, errors = proc.communicate()  

    f = open(os.path.join(tex_output_path, filename_zip), 'r')

    response = HttpResponse(f.read(), mimetype='application/zip')
    response['Cache-Control'] = 'must-revalidate'
    response['Content-Disposition'] = 'inline; filename=%(filename_zip)s' % {'filename_zip': filename_zip}
    return response

@login_required
def certificate_pdf(request, profile_id, **args):
    tex_output_path, filename = certificate(profile_id)

    filename_tex = filename + '.tex'
    filename_pdf = filename + '.pdf'

    cmd = ['pdflatex', '-halt-on-error', filename_tex]
    pipe = subprocess.PIPE

    for i in xrange(3):
        proc = subprocess.Popen(cmd, cwd=tex_output_path, stdout=pipe, stderr=pipe)
        outputs, errors = proc.communicate()  

    f = open(os.path.join(tex_output_path, filename_pdf), 'r')

    os.remove(os.path.join(tex_output_path, filename + '.log'))
    os.remove(os.path.join(tex_output_path, filename + '.aux'))

    response = HttpResponse(f.read(), mimetype='application/pdf')
    response['Cache-Control'] = 'must-revalidate'
    response['Content-Disposition'] = 'inline; filename=%(filename_pdf)s' % {'filename_pdf': filename_pdf}
    return response

def certificates():
    tex_template_path = os.path.join(MEDIA_ROOT, 'tex')
    tex_output_path = os.path.join(ABSTRACTS_PATH, 'certificates')

    str_list_to_modify = []
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
            str_list_to_modify.append('\\certificate{%(full_name)s}{%(affiliation)s}{%(address)s}{%(postal_code)s}{%(city)s}{%(country)s}\n' % {'full_name': full_name, 'affiliation': affiliation,'address': address, 'postal_code' : postal_code , 'city': city, 'country': country })
        except UserProfile.DoesNotExist:
            continue

    str_list.append(latex_replacement(''.join(str_list_to_modify)))
    str_list.append('\\end{document}' )
    output = ''.join(str_list)

    if not os.path.exists(tex_output_path):
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
    return tex_output_path

@login_required
def certificates_tex(request, **args):
    tex_output_path = certificates()

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
    tex_output_path = certificates()

    cmd = ['pdflatex', '-halt-on-error', 'certificates.tex']
    pipe = subprocess.PIPE

    for i in xrange(3):
        proc = subprocess.Popen(cmd, cwd=tex_output_path, stdout=pipe, stderr=pipe)
        outputs, errors = proc.communicate()  

    f = open(os.path.join(tex_output_path, 'certificates.pdf'), 'r')

    os.remove(os.path.join(tex_output_path, 'certificates.log'))
    os.remove(os.path.join(tex_output_path, 'certificates.aux'))

    response = HttpResponse(f.read(), mimetype='application/pdf')
    response['Cache-Control'] = 'must-revalidate'
    response['Content-Disposition'] = 'inline; filename=certificates.pdf'
    return response

def all_receipts(request, **args):

    max_profile_id_dict = UserProfile.objects.all().aggregate(Max('id'))
    max_profile_id = max_profile_id_dict['id__max']

    tex_template_path = os.path.join(MEDIA_ROOT, 'tex')
    tex_receipts_path = os.path.join(ABSTRACTS_PATH, 'receipts')  
    tex_individual_receipts_path = os.path.join(tex_receipts_path, 'individual_receipts')  

    for i in range(1, max_profile_id + 1):
        str_list_to_modify = []
        str_list = []
        f = open(os.path.join(tex_template_path, 'receipts_template.tex'), 'r')
        str_list.append(f.read())
        f.close()
    
        try:
            person = UserProfile.objects.get(id = i)
            first_name = person.user.first_name
            last_name = person.user.last_name
            full_name = person.user.get_full_name()
            affiliation = person.affiliation
            address = person.address
            postal_code = person.postal_code
            city = person.city
            country = person.country
            payment = "WRITE AMOUNT AND CURRENCY HERE" #
        except UserProfile.DoesNotExist:
            pass
    
        filename = create_filename(first_name, last_name)
        tex_output_path = os.path.join(tex_individual_receipts_path, filename)

        str_list_to_modify.append('\\receipt{%(full_name)s}{%(payment)s}{%(affiliation)s}{%(address)s}{%(postal_code)s}{%(city)s}{%(country)s}\n' % {'full_name': full_name, 'payment': payment, 'affiliation': affiliation,'address': address, 'postal_code': postal_code, 'city': city, 'country': country})
        str_list.append(latex_replacement(''.join(str_list_to_modify)))
        str_list.append('\\end{document}' )
        output = ''.join(str_list)

        if os.path.exists(tex_output_path):
            shutil.rmtree(tex_output_path, True)

        if not os.path.exists(tex_receipts_path):
            os.mkdir(tex_receipts_path)

        if not os.path.exists(tex_individual_receipts_path):
            os.mkdir(tex_individual_receipts_path)

        os.mkdir(tex_output_path)

        shutil.copy(
            os.path.join(tex_template_path, 'femhub_logo.png'),
            os.path.join(tex_output_path, 'femhub_logo.png'))
        shutil.copy(
            os.path.join(tex_template_path, 'femhub_footer.png'),
            os.path.join(tex_output_path, 'femhub_footer.png'))

        filename_tex = filename + '.tex'
  
        with open(os.path.join(tex_output_path, filename_tex), 'wb') as f:
            f.write(output.encode('utf-8'))
        f.close()

    filename_zip = 'individual_receipts.zip'

    zip = zipfile.ZipFile(os.path.join(tex_receipts_path, filename_zip), 'w')
    zipdir(tex_individual_receipts_path, zip)
    zip.close()    

    f = open(os.path.join(tex_receipts_path, filename_zip), 'r')

    response = HttpResponse(f.read(), mimetype='application/zip')
    response['Cache-Control'] = 'must-revalidate'
    response['Content-Disposition'] = 'inline; filename=%(filename_zip)s' % {'filename_zip': filename_zip}
    return response


def receipts():
    tex_template_path = os.path.join(MEDIA_ROOT, 'tex')
    tex_output_path = os.path.join(ABSTRACTS_PATH, 'receipts')

#    str_list_to_modify = []
    str_list = []
    counter = 0

    f = open(os.path.join(tex_template_path, 'receipts_template.tex'), 'r')
    str_list.append(f.read())
    f.close()

    user_list = User.objects.all().order_by('last_name')

    for i in range(len(User.objects.all())):
        try:
#            if not (user_list[i].get_profile().payment == ''):
            full_name = user_list[i].get_full_name()
            affiliation = user_list[i].get_profile().affiliation
            address = user_list[i].get_profile().address
            postal_code = user_list[i].get_profile().postal_code
            city = user_list[i].get_profile().city
            country = user_list[i].get_profile().country
#            payment = user_list[i].get_profile().payment
            payment = "WRITE AMOUNT AND CURRENCY HERE" #
            str_list.append('%') #
            str_list_to_modify = [] #
            str_list_to_modify.append('\\receipt{%(full_name)s}{%(payment)s}{%(affiliation)s}{%(address)s}{%(postal_code)s}{%(city)s}{%(country)s}\n' % {'full_name': full_name, 'payment': payment, 'affiliation': affiliation,'address': address, 'postal_code': postal_code, 'city': city, 'country': country})
            str_list.append(latex_replacement(''.join(str_list_to_modify))) #
            counter += 1
        except UserProfile.DoesNotExist:
            continue
    
#    str_list.append(latex_replacement(''.join(str_list_to_modify)))
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

    return tex_output_path, counter

@login_required
def receipts_tex(request, **args):
    tex_output_path, counter = receipts()

    if counter == 0:
        return HttpResponse('Error: TeX file is incomplete - No entry in column payments!')

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
    tex_output_path, counter = receipts()

    if counter == 0:
        return HttpResponse('Error: Impossible to generate PDF file - No entry in column payments!')

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

def registration():
    tex_template_path = os.path.join(MEDIA_ROOT, 'tex')
    tex_output_path = os.path.join(ABSTRACTS_PATH, 'registration')

    str_list_to_modify = []
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
            str_list_to_modify.append('\\registration{%(last_name)s}{%(first_name)s}{%(affiliation)s}{%(tshirt)s}{%(departure)s}\n' % {'last_name': last_name, 'first_name': first_name, 'affiliation': affiliation,'tshirt': tshirt, 'departure': departure})
        except UserProfile.DoesNotExist:
            continue

    str_list.append(latex_replacement(''.join(str_list_to_modify)))
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

    return tex_output_path

@login_required
def registration_tex(request, **args):
    tex_output_path = registration()

    f = open(os.path.join(tex_output_path, 'registration.tex'), 'r')

    response = HttpResponse(f.read(), mimetype='application/octet-stream')
    response['Cache-Control'] = 'must-revalidate'
    response['Content-Disposition'] = 'inline; filename=registration.tex'
    return response

@login_required
def registration_pdf(request, **args):
    tex_output_path = registration()

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

def create_filename(user_first_name, user_last_name, prefix=''):

    def filename_replacement(name):
        name = name.replace(u'\xe1','a')
        name = name.replace(u'\u0161','s')
        name = name.replace(u'\u011b','e')
        name = name.replace(u'\u010d','c')
        name = name.replace(u'\u0159','r')
        name = name.replace(u'\u017e','z')
        name = name.replace(u'\xfd','y')
        name = name.replace(u'\xed','i')
        name = name.replace(u'\xe9','e')
        name = name.replace(u'\xfa','u')
        name = name.replace(u'\u016f','u')
        return name.replace(' ','_')

    first = filename_replacement(user_first_name).encode('ascii','ignore')
    last = filename_replacement(user_last_name).encode('ascii','ignore')
    filename = prefix + last + '_' + first      
    filename = "".join([x for x in filename if (((ord(x) >= 48) and (ord(x) <= 57)) or ((ord(x) >= 65) and (ord(x) <= 90)) or ((ord(x) >= 97) and (ord(x) <= 122)) or (ord(x) == 95))])   
    return filename

def letter(profile_id):
    tex_template_path = os.path.join(MEDIA_ROOT, 'tex')
    tex_letters_path = os.path.join(ABSTRACTS_PATH, 'letters')
    tex_output_path = os.path.join(tex_letters_path, profile_id)

    str_list = []
    str_list_to_modify = []
    f = open(os.path.join(tex_template_path, 'letter_template.tex'), 'r')
    str_list.append(f.read())
    f.close()

    try:
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
    except UserProfile.DoesNotExist:
        pass

    abstractstr = ''
    appended_s = ''
    counter = 0
    message = ''
    abstr = []

    try:
        abstr = User.objects.get(id = user_id).userabstract2_set.all()
    except UserAbstract.DoesNotExist:
        pass

    for k in range(len(abstr)):
        try:
            abstract_title = abstr[k].to_cls().title
            abstractstr += (abstract_title + ' and ')
            counter += 1
        except UserAbstract.DoesNotExist:
            continue

    if counter == 0:
        message = (' - probably the user with user_id = %(user_id)s and profile_id = %(profile_id)s has not submited the Abstract!' % {'user_id': user_id, 'profile_id': profile_id})

    if (counter > 1):
        appended_s = 's'
    abstractstr = abstractstr[:-5]

    str_list_to_modify.append('\\letter{%(full_name)s}{%(affiliation)s}{%(address)s}{%(city)s}{%(postal_code)s}{%(country)s}{' % {'full_name': full_name, 'affiliation': affiliation,'address': address, 'city': city, 'postal_code' : postal_code, 'country': country})
    str_list_to_modify.append('%(abstractstr)s}{%(appended_s)s}\n' % {'abstractstr': abstractstr, 'appended_s':appended_s} )
    str_list.append(latex_replacement(''.join(str_list_to_modify)))
    str_list.append('\\end{document}' )
    output = ''.join(str_list)

    if os.path.exists(tex_output_path):
        shutil.rmtree(tex_output_path, True)

    if not os.path.exists(tex_letters_path):
        os.mkdir(tex_letters_path)

    os.mkdir(tex_output_path)

    shutil.copy(
        os.path.join(tex_template_path, 'horizon_no_slogan.jpg'),
        os.path.join(tex_output_path, 'horizon_no_slogan.jpg'))

    filename = create_filename(first_name, last_name, 'letter_')

    with open(os.path.join(tex_output_path, filename + '.tex'), 'wb') as f:
        f.write(output.encode('utf-8'))
    f.close()

    return tex_output_path, counter, message, filename

@login_required
def letter_tex(request, profile_id, **args):
    tex_output_path, counter, message, filename = letter(profile_id)
 
    if counter == 0:
        return HttpResponse('TeX file incomplete' + message)

    filename_tex = filename + '.tex'
    filename_zip = filename + '.zip'

    cmd = ['zip', filename, filename_tex, 'horizon_no_slogan.jpg']
    pipe = subprocess.PIPE

    proc = subprocess.Popen(cmd, cwd=tex_output_path, stdout=pipe, stderr=pipe)
    outputs, errors = proc.communicate()  

    f = open(os.path.join(tex_output_path, filename_zip), 'r')

    response = HttpResponse(f.read(), mimetype='application/zip')
    response['Cache-Control'] = 'must-revalidate'
    response['Content-Disposition'] = 'inline; filename=%(filename_zip)s' % {'filename_zip': filename_zip}
    return response

@login_required
def letter_pdf(request, profile_id, **args):
    tex_output_path, counter, message, filename = letter(profile_id)

    if counter == 0:
        return HttpResponse('Unable to create PDF file' + message)

    filename_pdf = filename + '.pdf'

    cmd = ['pdflatex', '-halt-on-error', filename]
    pipe = subprocess.PIPE

    for i in xrange(3):
        proc = subprocess.Popen(cmd, cwd=tex_output_path, stdout=pipe, stderr=pipe)
        outputs, errors = proc.communicate()  

    f = open(os.path.join(tex_output_path, filename_pdf), 'r')

    response = HttpResponse(f.read(), mimetype='application/pdf')
    response['Cache-Control'] = 'must-revalidate'
    response['Content-Disposition'] = 'inline; filename=%(filename_pdf)s' % {'filename_pdf': filename_pdf}

    return response

def program():
    tex_template_path = os.path.join(MEDIA_ROOT, 'tex')
    tex_output_path = os.path.join(ABSTRACTS_PATH, 'program')

    str_list_to_modify = []
    str_list = []
    f = open(os.path.join(tex_template_path, 'program_template.tex'), 'r')
    str_list.append(f.read())
    f.close()
    
    user_list = User.objects.all().order_by('last_name')

    for i in range(len(User.objects.all())):
        try:
            first_name = user_list[i].first_name
            last_name = user_list[i].last_name                    
            user_id = user_list[i].id
            
            first_name_initials = []
            first_name_upper = re.findall("[A-Z]",first_name)
            for j in range(len(first_name_upper)):
                first_name_initials.append(first_name_upper[j] + ". ")

            abstr = []
            try:
                abstr = user_list[i].userabstract2_set.all()
            except UserAbstract.DoesNotExist:
                continue

            for k in range(len(abstr)):
                try:
                    abstract_title = abstr[k].to_cls().title
                    str_list_to_modify.append('{%(first_name)s%(last_name)s}: {%(title)s}\n' % {'first_name': ''.join(first_name_initials), 'last_name': last_name, 'title': abstract_title})                   
                except UserAbstract.DoesNotExist:
                    continue

        except User.DoesNotExist:
            continue

    str_list.append(latex_replacement(''.join(str_list_to_modify)))
    str_list.append('\\end{document}' )
    output = ''.join(str_list)

    if os.path.exists(tex_output_path):
        shutil.rmtree(tex_output_path, True)

    os.mkdir(tex_output_path)

    with open(os.path.join(tex_output_path, 'program.tex'), 'wb') as f:
        f.write(output.encode('utf-8'))
    f.close()

    return tex_output_path

@login_required
def program_tex(request, **args):
    tex_output_path = program()

    f = open(os.path.join(tex_output_path, 'program.tex'), 'r')

    response = HttpResponse(f.read(), mimetype='application/octet-stream')
    response['Cache-Control'] = 'must-revalidate'
    response['Content-Disposition'] = 'inline; filename=program.tex'
    return response

def get_submit_form_data(post, user):
    title = post['title']
    abstract = post['abstract']
##---
    first_names = post.getlist('first_name')
    last_names = post.getlist('last_name')
    full_names = ['']*len(first_names)
    affiliations = post.getlist('affiliation')
#    addresses = post.getlist('address')
##***
    emails = post.getlist('email')
    presentings = ['no']*len(first_names)

    ##---this code was used for bibid---
    ##bibitems_bibid = post.getlist('bibitem_bibid')
    ##bibitems = zip(bibitems_bibid, bibitems_authors, bibitems_title, bibitems_other)
    ##fields = ('bibid', 'authors', 'title', 'other')
    ##---this code was used for bibid---

    bibitems_authors = post.getlist('bibitem_authors')
    bibitems_title = post.getlist('bibitem_title')
    bibitems_other = post.getlist('bibitem_other')

    for i, (first_name, last_name) in enumerate(zip(first_names, last_names)):
        if (first_name == user.first_name and last_name == user.last_name):
            presentings[i] = 'yes'
            break
##---
    for i, (first_name, last_name) in enumerate(zip(first_names, last_names)):
        full_names[i] = first_names[i] + ' ' + last_names[i]
    
    authors = zip(first_names, last_names, full_names, affiliations, emails, presentings)
    fields = ('first_name', 'last_name', 'full_name', 'affiliation', 'email', 'presenting')

#    authors = zip(first_names, last_names, addresses, emails, presentings)
#    fields = ('first_name', 'last_name', 'address', 'email', 'presenting')
##***

    for i, author in enumerate(authors):
        author = dict(zip(fields, author))
        authors[i] = author

##---
    fields = ('bibauthor_first_name', 'bibauthor_last_name')
#    fields = ('first_name', 'last_name')
##***
    bibitems_authors = [[ dict(zip(fields, re.split("\s+", author, 1)))
        for author in re.split("\s*,\s*", bibitem_authors) ] for bibitem_authors in bibitems_authors ]

    bibitems = zip(bibitems_authors, bibitems_title, bibitems_other)
##---
    fields = ('bibitem_authors', 'bibitem_title', 'bibitem_other')
#    fields = ('authors', 'title', 'other')
##***

    for i, bibitem in enumerate(bibitems):
        bibitem = dict(zip(fields, bibitem))
        bibitems[i] = bibitem

##--- code for groups of authors of same institution on abstract
    authgroup_authors = zip(full_names, emails, presentings)
    fields = ('auth_full_name', 'auth_email', 'auth_presenting')
    
    for i, authgroups_author in enumerate(authgroup_authors):
        authgroups_author = dict(zip(fields, authgroups_author))
        authgroup_authors[i] = authgroups_author
    
    res = MyOrderedDict()
    for v, k in zip(authgroup_authors, affiliations):
        if k in res:
            res[k].append(v)
        else:
            res[k] = [v]
    
    authgroups = [{'authgroup_authors':v, 'authgroup_affiliation':k,} for k,v in res.items()]
##***

    data = {
        'title': title,
        'abstract': abstract,
        'authors': authors,
        'bibitems': bibitems,
##---
        'authgroups' : authgroups,
##***
    }

    return json.dumps(data)

@login_required
@conditional('ENABLE_ABSTRACT_SUBMISSION')
def abstracts_submit_view(request, **args):
    local_args = {'user_count': userprofile_counter(), 'conf_name_upper': settings.CONF_NAME_UPPER, 'conf_name_lower': settings.CONF_NAME_LOWER, 'conf_year': settings.CONF_YEAR, 'conf_email': settings.CONF_EMAIL,'conf_web': settings.CONF_WEB}
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
           
            template = loader.get_template('e-mails/user/abstract.txt')
            body = template.render(Context({'user': request.user, 'abstract': abstract, 'conf_name_upper': settings.CONF_NAME_UPPER, 'conf_year': settings.CONF_YEAR}))
            request.user.email_user("[%(conf_name_upper)s %(conf_year)s] Abstract Submission Notification" % {'conf_name_upper': settings.CONF_NAME_UPPER, 'conf_year': settings.CONF_YEAR}, body)

            template = loader.get_template('e-mails/admin/abstract.txt')
            body = template.render(Context({'user': request.user, 'abstract': abstract}))

            mail_admins("[ADMIN] New Abstract", body)

        return HttpResponsePermanentRedirect('/account/abstracts/')
    else:
        return _render_to_response('abstracts/submit.html', request, local_args)

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

@login_required
def csv_export(request, **args):
    tex_output_path = os.path.join(ABSTRACTS_PATH, 'csv_export')

    str_list = [u'title,first,last,email\n']
    
    user_list = User.objects.all().order_by('last_name')

    for i in range(len(User.objects.all())):
        try:
            first_name = user_list[i].first_name
            last_name = user_list[i].last_name
            email = user_list[i].email
            str_list.append(u'\"Dr.\",\"%(first_name)s\",\"%(last_name)s\",\"%(email)s\"\n' % {'first_name': first_name, 'last_name': last_name, 'email': email })
        except UserProfile.DoesNotExist:
            continue

    output = ''.join(str_list)

    if os.path.exists(tex_output_path):
        shutil.rmtree(tex_output_path, True)

    os.mkdir(tex_output_path)

    filename = '%(conf_name_lower)s_%(conf_year)s_to_ELSTS.csv' % {'conf_name_lower': settings.CONF_NAME_LOWER, 'conf_year': settings.CONF_YEAR}

    with open(os.path.join(tex_output_path, filename), 'wb') as f:
        f.write(output.encode('utf-8'))
    f.close()

    f = open(os.path.join(tex_output_path, filename), 'r')    

    response = HttpResponse(f.read(), mimetype='application/octet-stream')
    response['Cache-Control'] = 'must-revalidate'
    response['Content-Disposition'] = 'inline; filename=%(filename)s' % {'filename': filename}
    return response  

