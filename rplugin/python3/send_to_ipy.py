import neovim
from jupyter_client import BlockingKernelClient, find_connection_file
from jupyter_core.paths import jupyter_runtime_dir
import os, fnmatch

@neovim.plugin
class SendToIPython(object):
    def __init__(self, nvim):
        self.nvim = nvim
        self.clients = {}

    @neovim.function('RunningKernels', sync=True)
    def running_kernels(self, args):
        rdir = jupyter_runtime_dir()
        l = fnmatch.filter(os.listdir(rdir), 'kernel-*.json')
        if len(l) > 1:
            cf = os.path.relpath(find_connection_file(), rdir)
            l = [f + '(newest)' if f == cf else f for f in l]
        return l

    @neovim.command('SendTo', nargs='?', complete='customlist,RunningKernels')
    def send_to(self, args):
        if args and args[0].endswith('(newest)'):
            args[0] = args[0][:-len('(newest)')]
        cf = find_connection_file(*args)

        if cf not in self.clients:
            client = BlockingKernelClient()
            client.load_connection_file(cf)
            client.start_channels()
            self.clients[cf] = client

        self.nvim.vars['send_target'] = {'type': 'ipy', 'id': cf}

    @neovim.function('SendToIPy')
    def send_lines(self, args):
        lines, = args
        cf = self.nvim.vars['send_target']['id']
        self.clients[cf].execute('\n'.join(lines))

    @neovim.function('SendComplete', sync=True)
    def complete(self, args):
        findstart, base = args
        if findstart:
            v = self.nvim
            cf = v.vars['send_target']['id']
            line = v.current.line
            pos = v.current.window.cursor[1]
            reply = self.clients[cf].complete(line, pos, reply=True)['content']
            self.completions = reply['matches']
            return reply['cursor_start']
        else:
            return self.completions
