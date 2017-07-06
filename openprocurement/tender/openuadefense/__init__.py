# -*- coding: utf-8 -*-
from logging import getLogger
from pkg_resources import get_distribution

from openprocurement.tender.openuadefense.models import Tender


PKG = get_distribution(__package__)

LOGGER = getLogger(PKG.project_name)


def includeme(config):
    LOGGER.info('Init openua.defense plugin.')
    config.add_tender_procurementMethodType(Tender)
    config.scan("openprocurement.tender.openuadefense.views")
