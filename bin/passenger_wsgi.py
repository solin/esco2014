import sys, os

def setup_esco_retail():
    sys.path.insert(0, os.getcwd())
    os.environ['DJANGO_SETTINGS_MODULE'] = "esco.settings"
    import django.core.handlers.wsgi
    return django.core.handlers.wsgi.WSGIHandler()

def setup_esco_debug():
    sys.stdout = sys.stderr
    sys.path.insert(0, os.getcwd())
    os.environ['DJANGO_SETTINGS_MODULE'] = "esco.settings"
    sys.path.insert(0, os.path.expanduser('~'))
    from paste.exceptions.errormiddleware import ErrorMiddleware
    import django.core.handlers.wsgi
    application = django.core.handlers.wsgi.WSGIHandler()
    # To cut django out of the loop, comment the above application = ... line ,
    # and remove "test" from the below function definition.
    def testapplication(environ, start_response):
        status = '200 OK'
        output = 'Hello World! Running Python version ' + sys.version + '\n\n'
        response_headers = [('Content-type', 'text/plain'), ('Content-Length', str(len(output)))]
        # to test paste's error catching prowess, uncomment the following line
        # while this function is the "application"
        #raise("error")
        start_response(status, response_headers)
        return [output]
    return ErrorMiddleware(application, debug=True)

def setup_esco(debug=False):
    if not debug:
        return setup_esco_retail()
    else:
        return setup_esco_debug()

application = setup_esco()
