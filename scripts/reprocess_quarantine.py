from pika import BlockingConnection
from pika import URLParameters
from sdc.rabbit.publishers import QueuePublisher, PublishMessageError


def reprocess():
    # To use this script, fill in the credentials for rabbit.  They should be found in app/settings.py
    rabbit_url = 'amqp://<user>:<pass>@<host>:<port>/%2f'
    connection = BlockingConnection(URLParameters(rabbit_url))
    channel = connection.channel()
    method, properties, body = channel.basic_get('Seft.Responses.Quarantine')
    if method:
        try:
            print("Recovered quarantine message")
            print("Headers:")
            print(properties.headers)

            # Uncomment if extra information is needed (payload is encrypted so it's not likely to be useful)
            # print("Body:")
            # print(body)

            publisher = QueuePublisher(urls=[rabbit_url],
                                       queue='Seft.Responses')

            publisher.publish_message(body, headers=properties.headers)
            print("Message successfully reprocessed")

            channel.basic_ack(method.delivery_tag)
            print("Message ACK")
        except PublishMessageError as e:
            print(e)
            channel.basic_nack(method.delivery_tag)
    else:
        print('No message found on quarantine queue')


if __name__ == '__main__':
    reprocess()
