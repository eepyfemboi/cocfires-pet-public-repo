from pypresence import AioPresence
import time
import asyncio
async def main(loop):
    rpc = AioPresence('1197328431164170250')
    #rpc.loop = loop
    await rpc.connect()
    activity_details = {
        "state": "below",
        "details": "Click the button",
        "buttons": [
            {"label": "My server", "url": "https://discord.gg/8nVfVGWTUb"},
            {"label": "A bot I'm working on", "url": "https://discord.com/oauth2/authorize?client_id=1093032431298285598&permissions=1632590228727&scope=bot"}
        ],
        "large_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Octicons-mark-github.svg/2048px-Octicons-mark-github.svg.png",
        "large_text": "Join my server!",
        "buttons": [
            {"label": "My server", "url": "https://discord.gg/8nVfVGWTUb"},
            {"label": "A bot I'm working on", "url": "https://discord.com/oauth2/authorize?client_id=1093032431298285598&permissions=1632590228727&scope=bot"}
        ]
    }
    await rpc.update(**activity_details)
    try:
        while True:
            time.sleep(15)
            await rpc.update(**activity_details)
    except BaseException:
        pass

loop = asyncio.new_event_loop()
loop.create_task(main(loop))
loop.run_forever()
