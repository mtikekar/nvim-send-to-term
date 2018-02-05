import neovim
from jupyter_client import BlockingKernelClient, find_connection_file
from jupyter_core.paths import jupyter_runtime_dir
import os, fnmatch

@neovim.plugin
class SendToIPy(object):
    def __init__(self, nvim):
        self.nvim = nvim
        self.clients = {}

    @neovim.function('RunningKernels', sync=True)
    def running_kernels(self, args):
        l = os.listdir(jupyter_runtime_dir())
        l = fnmatch.filter(l, 'kernel-*.json')
        if l:
            l.append('newest')
        return l

    @neovim.command('SendTo', nargs='?', complete='customlist,RunningKernels')
    def send_to(self, args):
        if args[0] == 'newest':
            args = ()
        cf = find_connection_file(*args)

        if cf not in self.clients:
            client = BlockingKernelClient()
            client.load_connection_file(cf)
            client.start_channels()
            self.clients[cf] = client

        self.nvim.vars['send_target'] = {'type': 'ipy', 'id': cf}

    @neovim.function('SendLines')
    def send_lines(self, args):
        cf, line = args
        self.clients[cf].execute(line)
