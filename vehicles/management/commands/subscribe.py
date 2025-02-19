import requests
import uuid
from base64 import b64encode
from django.core.cache import cache
from datetime import timedelta
from requests_toolbelt.adapters.source import SourceAddressAdapter
from django.utils import timezone
from django.core.management.base import BaseCommand
from busstops.models import DataSource


class Command(BaseCommand):
    consumer_address = 'http://68.183.252.225/siri'

    @staticmethod
    def add_arguments(parser):
        parser.add_argument(
            '--terminate',
            action='store_true'
        )
        parser.add_argument('source', type=str)

    def post(self, xml):
        headers = {
           'Content-Type': 'application/xml'
        }
        if self.source.settings:
            app_id = self.source.settings['app_id']
            app_key = self.source.settings['app_key']
            authorization = b64encode(f'{app_id}:{app_key}'.encode()).decode()
            headers['Authorization'] = f'Basic {authorization}'
            xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Siri xmlns="http://www.siri.org.uk/siri" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="2.0"
xsi:schemaLocation="http://www.siri.org.uk/siri http://www.siri.org.uk/schema/2.0/xsd/siri.xsd">{xml}</Siri>"""
        else:
            xml = f'<?xml version="1.0" ?><Siri xmlns="http://www.siri.org.uk/siri" version="1.3">{xml}</Siri>'
        response = self.session.post(self.source.url, data=xml.replace('    ', ''), headers=headers, timeout=30)
        print(response, response.content)

    def terminate_subscription(self, timestamp, requestor_ref):
        self.post(f"""
            <TerminateSubscriptionRequest>
                <RequestTimestamp>{timestamp}</RequestTimestamp>
                <RequestorRef>{requestor_ref}</RequestorRef>
                <All/>
            </TerminateSubscriptionRequest>
        """)

    def subscribe(self, timestamp, requestor_ref, xml):
        self.post(f"""
            <SubscriptionRequest>
                <RequestTimestamp>{timestamp}</RequestTimestamp>
                <RequestorRef>{requestor_ref}</RequestorRef>
                <ConsumerAddress>{self.consumer_address}</ConsumerAddress>
                {xml}
            </SubscriptionRequest>
        """)

    def tfn(self, terminate):
        if not terminate and cache.get('Heartbeat:TransportAPI'):
            return  # received a heartbeat recently, no need to resubscribe

        self.source = DataSource.objects.get(name='Transport for the North')

        now = timezone.now()

        self.session = requests.Session()

        timestamp = now.isoformat()
        requestor_ref = self.source.settings['app_id']

        # terminate any previous subscription just in case
        self.terminate_subscription(timestamp, requestor_ref)

        if terminate:
            return

        termination_time = (now + timedelta(hours=24)).isoformat()
        subscription_id = str(uuid.uuid4())

        self.subscribe(timestamp, requestor_ref, f"""
            <SituationExchangeSubscriptionRequest>
                <SubscriptionIdentifier>{subscription_id}</SubscriptionIdentifier>
                <SubscriberRef>{requestor_ref}</SubscriberRef>
                <InitialTerminationTime>{termination_time}</InitialTerminationTime>
                <IncrementalUpdates>true</IncrementalUpdates>
                <SituationExchangeRequest version="2.0">
                </SituationExchangeRequest>
            </SituationExchangeSubscriptionRequest>
        """)

    def arriva(self, terminate):
        if not terminate and cache.get('Heartbeat:HAConTest'):
            return  # received a heartbeat recently, no need to resubscribe

        self.source = DataSource.objects.get(name='Arriva')

        now = timezone.now()

        self.session = requests.Session()

        timestamp = now.isoformat()
        requestor_ref = 'HAConToBusTimesET'

        # Access to the subscription endpoint is restricted to certain IP addresses,
        # so use a Digital Ocean floating IP address
        self.session.mount('http://', SourceAddressAdapter('10.16.0.7'))

        # terminate any previous subscription just in case
        self.terminate_subscription(timestamp, requestor_ref)

        # (re)subscribe
        if not terminate:
            termination_time = (now + timedelta(hours=24)).isoformat()

            self.subscribe(timestamp, requestor_ref, f"""
                <SubscriptionContext>
                    <HeartbeatInterval>PT2M</HeartbeatInterval>
                </SubscriptionContext>
                <EstimatedTimetableSubscriptionRequest>
                    <SubscriberRef>{requestor_ref}</SubscriberRef>
                    <SubscriptionIdentifier>{requestor_ref}</SubscriptionIdentifier>
                    <InitialTerminationTime>{termination_time}</InitialTerminationTime>
                    <EstimatedTimetableRequest version="1.3">
                        <RequestTimestamp>{timestamp}</RequestTimestamp>
                        <PreviewInterval>PT2H</PreviewInterval>
                    </EstimatedTimetableRequest>
                    <ChangeBeforeUpdates>PT1M</ChangeBeforeUpdates>
                </EstimatedTimetableSubscriptionRequest>
            """)

    def handle(self, source, **options):
        if source == 'tfn':
            self.tfn(options['terminate'])
        elif source == 'arriva':
            self.arriva(options['terminate'])
