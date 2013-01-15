from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from django.conf import settings
from django.template import Context, loader

from django.contrib.auth.models import User
from femtec.site.models import UserProfile, UserAbstract2 as UserAbstract

import datetime

from django.contrib.auth.models import Group
from django.contrib.sites.models import Site

try:
    import json
except ImportError:
    import simplejson as json

admin.site.unregister(Group)
admin.site.unregister(Site)

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'last_name', 'first_name', 'is_active', 'is_staff', 'is_superuser')
    
    list_editable = ['last_name', 'first_name']

    actions = None
    actions_on_top = False
    actions_on_bottom = False
    save_on_top = True

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

class UserProfileAdmin(admin.ModelAdmin):
    def first_name(self, profile):
        return profile.user.first_name

    def last_name(self, profile):
        return profile.user.last_name

    def email(self, profile):
        return '<a href="mailto:%(email)s">%(email)s</a>' % {'email': profile.user.email }

    def letter_tex(obj):
        return '<a href="/account/letter/tex/%(obj_id)s">TeX</a>' % {'obj_id': obj.id }

    def letter_pdf(obj):
        return '<a href="/account/letter/pdf/%(obj_id)s">PDF</a>' % {'obj_id': obj.id }

    first_name.admin_order_field = 'user__first_name'
    first_name.short_description = 'First Name'

    last_name.admin_order_field = 'user__last_name'
    last_name.short_description = 'Last Name'

    email.admin_order_field = 'user__email'
    email.allow_tags = True

    #list_select_related = True

    letter_tex.short_description = 'Letter'
    letter_tex.allow_tags = True

    letter_pdf.short_description = 'Letter'
    letter_pdf.allow_tags = True

    list_display = ('last_name', 'first_name', 'email', 'affiliation', 'address', 'city', 'postal_code', 'country', 'speaker', 'student', 'postconf', 'vegeterian', 'arrival', 'departure', 'accompanying', 'tshirt', 'payment', 'remark', letter_tex, letter_pdf)

    list_editable = ['remark']

    actions = None
    actions_on_top = False
    actions_on_bottom = False
    save_on_top = True

admin.site.register(UserProfile, UserProfileAdmin)

class UserAbstractAdmin(admin.ModelAdmin):
    def first_name(self, profile):
        return profile.user.first_name

    def last_name(self, profile):
        return profile.user.last_name

    def email(self, profile):
        return '<a href="mailto:%(email)s">%(email)s</a>' % {'email': profile.user.email }

    def title(obj):
        return obj.to_cls().title

    def tex(obj):
        return '<a href="/account/abstracts/tex/%s">TEX</a>' % obj.id

    def pdf(obj):
        return '<a href="/account/abstracts/pdf/%s">PDF</a>' % obj.id

    def log(obj):
        return '<a href="/account/abstracts/log/%s">LOG</a>' % obj.id

    first_name.admin_order_field = 'user__first_name'
    first_name.short_description = 'First Name'

    last_name.admin_order_field = 'user__last_name'
    last_name.short_description = 'Last Name'

    email.admin_order_field = 'user__email'
    email.allow_tags = True

    title.short_description = 'Title'

    tex.short_description = 'TEX'
    tex.allow_tags = True

    pdf.short_description = 'PDF'
    pdf.allow_tags = True

    log.short_description = 'LOG'
    log.allow_tags = True

    #list_select_related = True

    list_display = ('last_name', 'first_name', 'email', title, 'submit_date', 'modify_date', 'compiled', 'verified', 'accepted', tex, pdf, log)

    list_editable = ('verified', 'accepted')

    class Media:
        css = {
            'all': ('css/admin.css',),
        }

        js = ('js/jquery/jquery.js', 'js/admin.js')

    actions = None
    actions_on_top = False
    actions_on_bottom = False
    save_on_top = True

    def save_model(self, request, obj, form, change):
        if request.method == 'POST' and change == True:
            date = datetime.datetime.today()            
            obj.modify_date = date
            obj.save()

            cls = obj.to_cls()
            compiled = cls.build(obj.get_path())

            obj.compiled = True
            obj.save()

            conf_name_upper = settings.CONF_NAME_UPPER
            conf_year = settings.CONF_YEAR
            conf_web = settings.CONF_WEB

        if ('accepted' in form.changed_data) and ('verified' in form.changed_data):
            accepted = form.cleaned_data['accepted']

            if accepted is True:
                template = loader.get_template('e-mails/user/accepted.txt')
                body = template.render(Context({'user': obj.user}))

                if settings.SEND_EMAIL:
                    obj.user.email_user("[%(conf_name_upper)s %(conf_year)s] Abstract Status Update" % {'conf_name_upper': conf_name_upper, 'conf_year': conf_year }, body)

        elif 'verified' in form.changed_data:
            verified = form.cleaned_data['verified']

            if verified is True:
                template = loader.get_template('e-mails/user/verified.txt')
                body = template.render(Context({'user': obj.user}))

                if settings.SEND_EMAIL:
                    obj.user.email_user("[%(conf_name_upper)s %(conf_year)s] Abstract Status Update" % {'conf_name_upper': conf_name_upper, 'conf_year': conf_year }, body)

            elif verified is False:
                host = request.META.get("HTTP_ORIGIN", "%(conf_web)s" % {'conf_web' : conf_web })
                modify_url = "%s/account/abstracts/modify/%s/" % (host, obj.id)
                template = loader.get_template('e-mails/user/not-verified.txt')
                body = template.render(Context({'user': obj.user, 'modify_url': modify_url, 'conf_name_upper': conf_name_upper, 'conf_year': conf_year}))

                if settings.SEND_EMAIL:
                    obj.user.email_user("[%(conf_name_upper)s %(conf_year)s] Abstract Status Update" % {'conf_name_upper': conf_name_upper, 'conf_year': conf_year }, body)

        elif 'accepted' in form.changed_data:
            accepted = form.cleaned_data['accepted']

            if accepted is True:
                template = loader.get_template('e-mails/user/accepted.txt')
                body = template.render(Context({'user': obj.user}))

                if settings.SEND_EMAIL:
                    obj.user.email_user("[%(conf_name_upper)s %(conf_year)s] Abstract Status Update" % {'conf_name_upper': conf_name_upper, 'conf_year': conf_year }, body)

        super(UserAbstractAdmin, self).save_model(request, obj, form, change)

admin.site.register(UserAbstract, UserAbstractAdmin)
