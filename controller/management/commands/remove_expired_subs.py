from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

import requests
import urlparse
import time
import json
import logging

import controller.util as util
from controller.models import Submission

log = logging.getLogger(__name__)

class Command(BaseCommand):
    args = "<queue_name>"
    help = "Pull items from given queues and send to grading controller"

    def handle(self, *args, **options):
        flag=True
        log.debug("Starting check for expired subs.")
        while flag:
            subs=Submission.objects.all()
            util.reset_timed_out_submissions(subs)
            expired_list=util.get_submissions_that_have_expired(subs)
            if len(expired_list)>0:
                error,msg=util.post_expired_submissions_to_xqueue(expired_list)

            time.sleep(settings.TIME_BETWEEN_EXPIRED_CHECKS)