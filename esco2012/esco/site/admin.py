from django.contrib import admin

from django.contrib.auth.models import User
from esco.site.models import UserProfile, UserAbstract2 as UserAbstract

class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff')

    actions_on_top = False
    actions_on_bottom = False

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

class UserProfileAdmin(admin.ModelAdmin):
    def full_name(obj):
        return obj.user.get_full_name()

    full_name.short_description = 'Full Name'

    list_display = (full_name, 'affiliation', 'address', 'city', 'postal_code',
        'country', 'speaker', 'student', 'accompanying', 'vegeterian', 'arrival',
        'departure', 'postconf', 'tshirt')

    actions_on_top = False
    actions_on_bottom = False

admin.site.register(UserProfile, UserProfileAdmin)

class UserAbstractAdmin(admin.ModelAdmin):
    def full_name(obj):
        return obj.user.get_full_name()

    def email(obj):
        return '<a href="mailto:%(email)s">%(email)s</a>' % {'email': obj.user.email}

    def title(obj):
        return obj.to_cls().title

    def tex(obj):
        return '<a href="/account/abstracts/tex/%s">TEX</a>' % obj.id

    def pdf(obj):
        return '<a href="/account/abstracts/pdf/%s">PDF</a>' % obj.id

    def log(obj):
        return '<a href="/account/abstracts/log/%s">LOG</a>' % obj.id

    full_name.short_description = 'Full Name'

    email.short_description = 'E-mail'
    email.allow_tags = True

    title.short_description = 'Title'

    tex.short_description = 'TEX'
    tex.allow_tags = True

    pdf.short_description = 'PDF'
    pdf.allow_tags = True

    log.short_description = 'LOG'
    log.allow_tags = True

    list_display = (full_name, email, title, 'submit_date', 'modify_date', 'compiled', 'verified', 'accepted', tex, pdf, log)
    list_editable = ('verified', 'accepted')

    class Media:
        css = {
            'all': ('css/admin.css',),
        }

        js = ('js/jquery/jquery.js', 'js/admin.js')

    actions_on_top = False
    actions_on_bottom = False

admin.site.register(UserAbstract, UserAbstractAdmin)
