
def enable_abstract_submission(request):
    from django.conf import settings
    return {'ENABLE_ABSTRACT_SUBMISSION': settings.ENABLE_ABSTRACT_SUBMISSION}
