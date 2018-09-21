import neovim
from jupyter_client import BlockingKernelClient
from jupyter_core.paths import jupyter_runtime_dir
import re
from queue import Empty
from pathlib import Path
from time import time

timeout = 0.5
ansi_re = re.compile('\x1b\[.*?m')

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

    @neovim.command('SendTo', complete='customlist,RunningKernels', nargs='?')
    def send_to(self, args):
        cfs = args or self.running_kernels(None)
        if not cfs:
            self.nvim.command('echom "No kernel found"')
            return

        cf = (self.kerneldir / cfs[0]).as_posix()
        if cf not in self.clients:
            client = BlockingKernelClient()
            client.load_connection_file(cf)
            client.start_channels()
            self.clients[cf] = client
        # run function once to register it for the `funcref` function
        self.nvim.command('call SendLinesToJupyter()')
        cmd = 'let g:send_target = {"ipy_conn": "%s", "send": funcref("SendLinesToJupyter")}' % cf
        self.nvim.command(cmd)

    @neovim.function('SendLinesToJupyter')
    def send_lines(self, args):
        if args:
            cf = self.nvim.vars['send_target']['ipy_conn']
            self.clients[cf].execute('\n'.join(args[0]))

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
            # TODO: use vim's complete_add/complete_check for async operation
            get_info(client, self.completions)
            return {'words': self.completions, 'refresh': 'always'}

def get_info(client, completions):
    # send inspect requests
    msg_ids = {}
    for c in completions:
        msg_ids[client.inspect(c['word'])] = c

    # collect responses until timeout
    stop_time = time() + timeout
    n = len(msg_ids)
    while n > 0 and time() < stop_time:
        try:
            reply = client.get_shell_msg(timeout=timeout)
        except Empty:
            return
        # match reply to inspect request
        c = msg_ids.get(reply['parent_header']['msg_id'])
        if not c:
            continue

        info = reply['content']['data'].get('text/plain')
        if info:
            # remove ANSI escape sequences
            c['info'] = ansi_re.sub('', info)
        n = n - 1
