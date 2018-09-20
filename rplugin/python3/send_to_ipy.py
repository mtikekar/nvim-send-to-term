import neovim
from jupyter_client import BlockingKernelClient
from jupyter_core.paths import jupyter_runtime_dir
import re
from queue import Empty
from pathlib import Path
from time import time

timeout = 0.5

@neovim.plugin
class SendToIPython(object):
    def __init__(self, nvim):
        self.nvim = nvim
        self.clients = {}
        self.kerneldir = Path(jupyter_runtime_dir())

    @neovim.function('RunningKernels', sync=True)
    def running_kernels(self, args):
        l = self.kerneldir.glob('kernel-*.json')
        l = sorted(l, reverse=True, key=lambda f: f.stat().st_ctime)
        return [f.name for f in l]

    @neovim.function('_SendToJupyter', sync=True)
    def send_to(self, args):
        cfs = args or self.running_kernels(None)
        if not cfs:
            return
        cf = (self.kerneldir / cfs[0]).as_posix()

        if cf not in self.clients:
            client = BlockingKernelClient()
            client.load_connection_file(cf)
            client.start_channels()
            self.clients[cf] = client

        return cf

    @neovim.function('_SendLinesToJupyter')
    def send_lines(self, args):
        cf, lines = args
        self.clients[cf].execute('\n'.join(lines))

    @neovim.function('SendComplete', sync=True)
    def complete(self, args):
        findstart, base = args
        v = self.nvim
        try:
            cf = v.vars['send_target']['ipy_conn']
        except:
            return -1 # cancel completion with error message
        client = self.clients[cf]

        if findstart:
            line = v.current.line
            pos = v.current.window.cursor[1]
            try:
                reply = client.complete(line, pos, reply=True, timeout=timeout)['content']
            except TimeoutError:
                return -2
            self.completions = [{'word':w, 'info':' '} for w in reply['matches']]
            return reply['cursor_start']
        else:
            # TODO: use vim's complete_add/complete_check for asyc operation
            get_info(client, self.completions)
            return {'words': self.completions, 'refresh': 'always'}

def get_info(client, completions):
    # send inspect requests until first timeout
    stop_time = time() + timeout
    msg_ids = []
    for c in completions:
        msg_ids.append(client.inspect(c['word']))
        if time() > stop_time:
            break

    # collect responses until second timeout
    stop_time = time() + timeout
    n = len(msg_ids)
    while n > 0 and time() < stop_time:
        for reply in client.shell_channel.get_msgs():
            # match reply to inspect request
            try:
                idx = msg_ids.index(reply['parent_header']['msg_id'])
            except ValueError:
                continue

            info = reply['content']['data'].get('text/plain')
            if info:
                # remove ANSI escape sequences
                completions[idx]['info'] = re.sub('\x1b\[.*?m', '', info)
            n = n - 1
