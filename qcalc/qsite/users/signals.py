# signals.py
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from calc import QPref, UCals
import qvars
import logging

logger = logging.getLogger(__name__)


@receiver(user_logged_in)
def post_login(sender, request, user, **kwargs):
    pref = QPref.getp({'dummy': True})
    if 'dummy' in pref:
        QPref.setp(qvars.qc_gpref)
    uc = UCals()
    try:
        uc.package_contents_private(request)
        uc.create_catalog_calc_private(request)
        uc.package_contents_shared(request)
        uc.create_catalog_calc_shared(request)
        logger.info(f'*** User Catalog Created')
    except Exception as e:
        logger.error(f">>> PLG: Exception occured while preparing {user.username}'s catalog during logging in. {e}")

    logger.note(f"PLG: {user.username} has successfully logged in.")
