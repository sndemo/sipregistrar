import argparse
import asyncio
from collections import defaultdict
import logging

import aiosip

locations = defaultdict(set)
srv_host = 'xxxxxx'
srv_port = '7000'
realm = 'XXXXXX'
user = 'YYYYYY'
pwd = 'ZZZZZZ'
local_host = '0.0.0.0'
local_port = 6000


async def on_register(request, message):
    expires = int(message.headers['Expires'])
    # TODO: challenge registrations
    dialog = await request.prepare(status_code=200)

    if not expires:
        return

    # TODO: multiple contact fields
    contact_uri = message.contact_details['uri']
    user = contact_uri['user']
    addr = contact_uri['host'], contact_uri['port']
    locations[user].add(addr)
    print('Registration established for {} at {}'.format(user, addr))

    async for message in dialog:
        expires = int(message.headers['Expires'])

        # TODO: challenge registrations
        await dialog.reply(message, 200)
        if not expires:
            break

    locations[user].remove(addr)
    print('Unregistering {} at {}'.format(user, addr))

class Dialplan(aiosip.BaseDialplan):

    async def resolve(self, *args, **kwargs):
        await super().resolve(*args, **kwargs)

        if kwargs['method'] == 'SUBSCRIBE':
            return on_subscribe
        elif kwargs['method'] == 'REGISTER':
            return on_register


def start(app, protocol):
    app.loop.run_until_complete( app.run( protocol=protocol, local_addr=(local_host, local_port)))

    print('Serving on {} {}'.format( (local_host, local_port), protocol))

    try:
        app.loop.run_forever()
    except KeyboardInterrupt:
        pass

    print('Closing')
    app.loop.run_until_complete(app.close())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--protocol', default='tcp')
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    app = aiosip.Application(loop=loop, dialplan=Dialplan())

    if args.protocol == 'udp':
        start(app, aiosip.UDP)
    elif args.protocol == 'tcp':
        start(app, aiosip.TCP)
    elif args.protocol == 'ws':
        start(app, aiosip.WS)
    else:
        raise RuntimeError("Unsupported protocol: {}".format(args.protocol))

    loop.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()