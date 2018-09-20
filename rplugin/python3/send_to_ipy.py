import neovim
from jupyter_client import BlockingKernelClient
from jupyter_core.paths import jupyter_runtime_dir
import re
from queue import Empty
from pathlib import Path

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
            # bug in ipykernel returns duplicates
            # neovim removes duplicates, but handling it here
            self.completions = sorted(frozenset(reply['matches']))
            return reply['cursor_start']
        else:
            return get_completions_fast(client, self.completions)

def get_completions(client, completions):
    for i in range(len(completions)):
        try:
            reply = client.inspect(completions[i], reply=True, timeout=timeout)['content']
        except TimeoutError:
            return completions
        info = reply['data'].get('text/plain', '')
        info = re.sub('\x1b\[.*?m', '', info)
        completions[i] = {'word': completions[i], 'info':info}
    return completions

def get_completions_fast(client, completions):
    n = len(completions)

    msg_ids = [0] * n
    for i, c in enumerate(completions):
        msg_ids[i] = client.inspect(c)

    while n > 0:
        try:
            reply = client.get_shell_msg(timeout=timeout)
        except Empty:
            return completions
        try:
            idx = msg_ids.index(reply['parent_header']['msg_id'])
        except ValueError:
            continue

        info = reply['content']['data'].get('text/plain', ' ')
        info = re.sub('\x1b\[.*?m', '', info)
        completions[idx] = {'word': completions[idx], 'info':info}
        n = n - 1
    return completions
