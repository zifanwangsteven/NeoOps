import asyncio

# web specific imports
from quart import Quart, websocket

# neo3 specific imports
from neo3 import settings
from neo3.network import convenience, payloads
from neo3.core import msgrouter

msg_queue = asyncio.Queue()

# web specific part
app = Quart(__name__)

with open('./index.html', 'r') as f:
    html_page = f.read()

@app.route('/')
async def index():
    return html_page

@app.websocket('/ws')
async def ws():
    while True:
        msg = await msg_queue.get()
        await websocket.send(msg)

# neo specific part
def connection_done(node_client, failure):
    if failure:
        asyncio.create_task(
            msg_queue.put(f"Failed to connect to {failure[0]} reason: {failure[1]}."))
    else:
        asyncio.create_task(
            msg_queue.put(f"Connected to node {node_client.version.user_agent} @ {node_client.address}"))

def block_received(from_nodeid: int, block: payloads.Block):
    asyncio.create_task(msg_queue.put(f"Received block with height {block.index} and hash {block.hash()}"))

async def run_neo():
    # set network magic to NEO TestNet
    settings.network.magic = 844378958

    # add a node to test against
    settings.network.seedlist = ['seed1t.neo.org:20333','seed2t.neo.org:20333',
                                 'seed3t.neo.org:20333','seed4t.neo.org:20333','seed5t.neo.org:20333']

    # listen to the connection events broad casted by the node manager
    msgrouter.on_client_connect_done += connection_done

    # listen to block received events
    msgrouter.on_block += block_received

    node_mgr = convenience.NodeManager()
    node_mgr.start()

    sync_mgr = convenience.SyncManager()
    await sync_mgr.start()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(run_neo())
    app.run(loop=loop)