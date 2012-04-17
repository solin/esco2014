from __future__ import with_statement

from django.conf.urls.defaults import patterns

from django.http import HttpResponse, HttpResponsePermanentRedirect, Http404
from django.template import RequestContext, Context, loader

from django.shortcuts import render_to_response, get_object_or_404

from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required

from django.core.mail import mail_admins

from femtec.site.models import UserProfile, UserAbstract2 as UserAbstract

from femtec.site.forms import LoginForm, ReminderForm, RegistrationForm, ChangePasswordForm
from femtec.site.forms import UserProfileForm

from django.conf import settings
from femtec.settings import MIN_PASSWORD_LEN

try:
    import json
except ImportError:
    import simplejson as json

import re
import shutil
import datetime

from functools import wraps

urlpatterns = patterns('femtec.site.views',
    (r'^$',      'index_view'),
    (r'^home/$', 'index_view'),

    (r'^topics/$',        '_render_template', {'template': 'content/topics.html'}),
    (r'^committees/$',    '_render_template', {'template': 'content/committees.html'}),
    (r'^minisymposia/$',  '_render_template', {'template': 'content/minisymposia.html'}),
    (r'^payment/$',       '_render_template', {'template': 'content/payment.html'}),
    (r'^accommodation/$', '_render_template', {'template': 'content/accommodation.html'}),
    (r'^travel/$',        '_render_template', {'template': 'content/travel.html'}),
    (r'^postconf/$',      '_render_template', {'template': 'content/postconf.html'}),
    (r'^contact/$',       '_render_template', {'template': 'content/contact.html'}),

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

    (r'^account/abstracts/$', 'abstracts_view'),
    (r'^account/abstracts/book/$', 'abstracts_book'),
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
    return _render_to_response(args.get('template'), request)

def handler404(request):
    return _render_to_response('errors/404.html', request)

def handler500(request):
    return _render_to_response('errors/500.html', request)

def index_view(request, **args):
    return _render_to_response('base.html', request, args)

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

    local_args = {'form': form, 'next': next}
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
                template = loader.get_template('e-mails/user/create.txt')
                body = template.render(Context({'user': user}))

                user.email_user("[ESCO 2012] Account Creation Notification", body)

                template = loader.get_template('e-mails/admin/create.txt')
                body = template.render(Context({'user': user}))

                mail_admins("[ESCO 2012][ADMIN] New Account", body)

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
                template = loader.get_template('e-mails/user/reminder.txt')
                body = template.render(Context({'user': user, 'password': password}))

                user.email_user("[ESCO 2012] Password Reminder Notification", body)

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
                template = loader.get_template('e-mails/user/profile.txt')
                body = template.render(Context({'user': request.user, 'profile': profile}))

                request.user.email_user("[ESCO 2012] User Profile Confirmation", body)

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
                    data[field] = getattr(profile, field).strftime('%d/%m/%Y')
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
def abstracts_book(request, **args):
    abstracts = UserAbstract.objects.order_by("id")

    compiled_abstracts = []
    compiled_authors = []

    for abstract in abstracts:
        cls = abstract.to_cls()
        compiled_abstracts.append(cls.build_raw())
        compiled_authors.append(cls.build_presenting())

    compiled_abstracts.sort()
    compiled_authors.sort()

    return render_to_response('abstracts/book.html', RequestContext(request, {'abstracts': compiled_abstracts, 'authors' : compiled_authors}), mimetype="text/plain")

def get_submit_form_data(post, user):
    title = post['title']
    abstract = post['abstract']

    first_names = post.getlist('first_name')
    last_names = post.getlist('last_name')
    addresses = post.getlist('address')
    emails = post.getlist('email')
    presentings = ['no']*len(first_names)
    bibitems_bibid = post.getlist('bibitem_bibid')
    bibitems_authors = post.getlist('bibitem_authors')
    bibitems_title = post.getlist('bibitem_title')
    bibitems_other = post.getlist('bibitem_other')

    for i, (first_name, last_name) in enumerate(zip(first_names, last_names)):
        if first_name == user.first_name and last_name == user.last_name:
            presentings[i] = 'yes'
            break

    authors = zip(first_names, last_names, addresses, emails, presentings)
    fields = ('first_name', 'last_name', 'address', 'email', 'presenting')

    for i, author in enumerate(authors):
        author = dict(zip(fields, author))
        authors[i] = author

    fields = ('first_name', 'last_name')

    bibitems_authors = [ [ dict(zip(fields, re.split("\s+", author, 1)))
        for author in re.split("\s*,\s*", bibitem_authors) ] for bibitem_authors in bibitems_authors ]

    bibitems = zip(bibitems_bibid, bibitems_authors, bibitems_title, bibitems_other)
    fields = ('bibid', 'authors', 'title', 'other')

    for i, bibitem in enumerate(bibitems):
        bibitem = dict(zip(fields, bibitem))
        bibitems[i] = bibitem

    data = {
        'title': title,
        'abstract': abstract,
        'authors': authors,
        'bibitems': bibitems,
    }

    return json.dumps(data)

@login_required
@conditional('ENABLE_ABSTRACT_SUBMISSION')
def abstracts_submit_view(request, **args):
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
            body = template.render(Context({'user': request.user, 'abstract': abstract}))

            request.user.email_user("[ESCO 2012] Abstract Submission Notification", body)

            template = loader.get_template('e-mails/admin/abstract.txt')
            body = template.render(Context({'user': request.user, 'abstract': abstract}))

            mail_admins("[ESCO 2012][ADMIN] New Abstract", body)

        return HttpResponsePermanentRedirect('/account/abstracts/')
    else:
        return _render_to_response('abstracts/submit.html', request)

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
