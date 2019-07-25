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
        self.client = None
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

        if self.client is not None:
            self.client.stop_channels()

        cf = cfs[0]
        self.client = BlockingKernelClient()
        self.client.load_connection_file(self.kerneldir / cf)
        self.client.start_channels()

        # run function once to register it for the `funcref` function
        self.nvim.command('call SendLinesToJupyter()')
        self.nvim.command('let g:send_target = {"send": funcref("SendLinesToJupyter")}')
        self.nvim.command('echom "Sending to %s"' % cf)

    @neovim.function('SendLinesToJupyter')
    def send_lines(self, args):
        if args:
            self.client.execute('\n'.join(args[0]))

    @neovim.function('SendComplete', sync=True)
    def complete(self, args):
        if self.client is None:
            return -1 # cancel completion with error message

        findstart, base = args

        if findstart:
            line = self.nvim.current.line
            pos = self.nvim.current.window.cursor[1]
            try:
                reply = self.client.complete(line, pos, reply=True, timeout=timeout)['content']
            except TimeoutError:
                return -2
            self.completions = [{'word':w, 'info':' '} for w in reply['matches']]
            return reply['cursor_start']
        else:
            # TODO: use vim's complete_add/complete_check for async operation
            get_info(self.client, self.completions)
            return {'words': self.completions, 'refresh': 'always'}

    @neovim.function('SendCanComplete', sync=True)
    def can_complete(self, args):
        return args[0] != '' and self.client is not None and self.client.is_alive()

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
