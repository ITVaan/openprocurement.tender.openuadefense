# -*- coding: utf-8 -*-
from openprocurement.tender.openua.views.lot import TenderUaLotResource as TenderLotResource
from openprocurement.tender.openuadefense.utils import calculate_business_date
from openprocurement.api.validation import (
    validate_lot_data,
    validate_patch_lot_data,
)
from openprocurement.api.utils import opresource, json_view, save_tender, context_unpack, apply_patch
from openprocurement.api.models import get_now
from openprocurement.tender.openuadefense.models import TENDERING_EXTRA_PERIOD


@opresource(name='Tender UA.defense Lots',
            collection_path='/tenders/{tender_id}/lots',
            path='/tenders/{tender_id}/lots/{lot_id}',
            procurementMethodType='aboveThresholdUA.defense',
            description="Tender Ua lots")
class TenderUaDefenseLotResource(TenderLotResource):
    def validate_update_tender(self, operation):
        tender = self.request.validated['tender']
        if tender.status not in ['active.tendering']:
            self.request.errors.add(
                'body', 'data', 'Can\'t {} lot in current ({}) tender status'.format(operation, tender.status)
            )
            self.request.errors.status = 403

            return
        if calculate_business_date(get_now(), TENDERING_EXTRA_PERIOD, tender, True) > tender.tenderPeriod.endDate:
            self.request.errors.add(
                'body', 'data', 'tenderPeriod should be extended by {0.days} working days'.format(
                    TENDERING_EXTRA_PERIOD
                )
            )
            self.request.errors.status = 403

            return

        return True

    @json_view(content_type='application/json', validators=(validate_lot_data,), permission='edit_tender')
    def collection_post(self):
        """
        Add a lot
        """
        if not self.validate_update_tender(operation='add'):
            return

        lot = self.request.validated['lot']
        lot.date = get_now()

        tender = self.request.validated['tender']
        tender.lots.append(lot)

        if self.request.authenticated_role == 'tender_owner':
            tender.invalidate_bids_data()

        if save_tender(request=self.request):
            self.LOGGER.info(
                msg='Created tender lot {}'.format(lot.id),
                extra=context_unpack(
                    request=self.request,
                    msg={'MESSAGE_ID': 'tender_lot_create'},
                    params={'lot_id': lot.id}
                )
            )
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url(
                route_name='Tender UA.defense Lots',
                tender_id=tender.id, lot_id=lot.id
            )

            return {'data': lot.serialize('view')}

    @json_view(content_type='application/json', validators=(validate_patch_lot_data,), permission='edit_tender')
    def patch(self):
        """
        Update of lot
        """
        if not self.validate_update_tender(operation='update'):
            return

        if self.request.authenticated_role == 'tender_owner':
            self.request.validated['tender'].invalidate_bids_data()

        if apply_patch(request=self.request, src=self.request.context.serialize()):
            self.LOGGER.info(
                msg='Updated tender lot {}'.format(self.request.context.id),
                extra=context_unpack(
                    request=self.request,
                    msg={'MESSAGE_ID': 'tender_lot_patch'}
                )
            )

            return {'data': self.request.context.serialize('view')}

    @json_view(permission='edit_tender')
    def delete(self):
        """
        Delete lot
        """
        if not self.validate_update_tender(operation='delete'):
            return

        lot = self.request.context

        tender = self.request.validated['tender']
        tender.lots.remove(lot)

        lot = lot.serialize('view')

        if self.request.authenticated_role() == 'tender_owner':
            tender.invalidate_bids_data()

        if save_tender(request=self.request):
            self.LOGGER.info(
                msg='Deleted tender lot {}'.format(self.request.context.id),
                extra=context_unpack(
                    request=self.request,
                    msg={'MESSAGE_ID': 'tender_lot_delete'}
                )
            )

            return {'data': lot}
