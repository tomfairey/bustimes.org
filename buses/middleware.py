from django.middleware.common import BrokenLinkEmailsMiddleware
from django.shortcuts import redirect
from busstops.models import Service

class BrokenLinkEmailsMiddleware(BrokenLinkEmailsMiddleware, object):

    def process_response(self, request, response):
        if 'HTTP_X_FORWARDED_FOR' in request.META:
            request.META['REMOTE_ADDR'] = request.META['HTTP_X_FORWARDED_FOR'].split(',')[0].strip()
        return super(BrokenLinkEmailsMiddleware, self).process_response(request, response)


class NotFoundRedirectMiddleware(object):
    """
    Redirects from /services/17-N4-_-y08-1 to /services/17-N4-_-y08-2, for example,
    if the former doesn't exist (any more) and the latter does.
    """

    def process_response(self, request, response):
        if (response.status_code == 404 and request.path.startswith('/services/')
                and len(request.path.split('-')) >= 4):
            service_code_parts = request.path.split('/')[-1].split('-')[:4]
            suggestion = Service.objects.filter(service_code__icontains='-'.join(service_code_parts)).exclude(current=False).first()
            if suggestion is not None:
                return redirect(suggestion)
        return response
