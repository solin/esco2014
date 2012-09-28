from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from django.conf import settings
from django.template import Context, loader

from django.contrib.auth.models import User
from femtec.site.models import UserProfile, UserAbstract2 as UserAbstract
#from titlecase import titlecase

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
    list_display = ('username', 'first_name', 'last_name', 'is_staff')
    
    actions = None
    actions_on_top = False
    actions_on_bottom = False

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

class UserProfileAdmin(admin.ModelAdmin):
    def first_name(self, profile):
        return profile.user.first_name

    def last_name(self, profile):
        return profile.user.last_name

    def email(self, profile):
        return '<a href="mailto:%(email)s">%(email)s</a>' % {'email': profile.user.email }

    first_name.admin_order_field = 'user__first_name'
    first_name.short_description = 'First Name'

    last_name.admin_order_field = 'user__last_name'
    last_name.short_description = 'Last Name'

    email.admin_order_field = 'user__email'
    email.allow_tags = True

    #list_select_related = True

    list_display = ('last_name', 'first_name', 'email', 'affiliation', 'address', 'city', 'postal_code',
        'country', 'speaker', 'student', 'postconf', 'vegeterian', 'arrival',
        'departure', 'accompanying', 'tshirt', 'payment', 'remark' )

    list_editable = ['remark']

    actions = None
    actions_on_top = False
    actions_on_bottom = False

admin.site.register(UserProfile, UserProfileAdmin)

class UserAbstractAdmin(admin.ModelAdmin):
    def first_name(self, profile):
        return profile.user.first_name

    def last_name(self, profile):
        return '<a href="mailto:%(email)s">%(last)s</a>' % {'email': profile.user.email, 'last': profile.user.last_name }

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
    last_name.allow_tags = True

    title.short_description = 'Title'

    tex.short_description = 'TEX'
    tex.allow_tags = True

    pdf.short_description = 'PDF'
    pdf.allow_tags = True

    log.short_description = 'LOG'
    log.allow_tags = True

    #list_select_related = True

    list_display = ('user', 'last_name', 'first_name', title, 'submit_date', 'modify_date', 'compiled', 'verified', 'accepted', tex, pdf, log)
    list_editable = ('verified', 'accepted')

    class Media:
        css = {
            'all': ('css/admin.css',),
        }

        js = ('js/jquery/jquery.js', 'js/admin.js')

    actions = None
    actions_on_top = False
    actions_on_bottom = False

    # not working correctly in Home/Site/User abstracts
    def save_model(self, request, obj, form, change):
        if request.method == 'POST' and change == True:
            #data = json.loads(form.cleaned_data['data'])
            #data['title'] = titlecase(data['title'])
            #data = json.dumps(data)
                        
            #obj.data = data

            date = datetime.datetime.today()            
            obj.modify_date = date
            obj.save()

            cls = obj.to_cls()
            compiled = cls.build(obj.get_path())

            obj.compiled = True
            obj.save()

        if 'verified' in form.changed_data:
            verified = form.cleaned_data['verified']

            if verified is True:
                template = loader.get_template('e-mails/user/verified.txt')
                body = template.render(Context({'user': obj.user}))

                if settings.SEND_EMAIL:
                    obj.user.email_user("Abstract Status Update", body)
            elif verified is False:
                host = request.META.get("HTTP_ORIGIN", "http://femtec2013.femhub.com")
                modify_url = "%s/account/abstracts/modify/%s/" % (host, obj.id)
                template = loader.get_template('e-mails/user/not-verified.txt')
                body = template.render(Context({'user': obj.user, 'modify_url': modify_url}))

                if settings.SEND_EMAIL:
                    obj.user.email_user("Abstract Status Update", body)

        super(UserAbstractAdmin, self).save_model(request, obj, form, change)

admin.site.register(UserAbstract, UserAbstractAdmin)
