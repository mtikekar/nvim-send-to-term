# Neovim plugin to send text from a buffer to a terminal

This plugin aims to be simpler in design and easier to use than other similar
plugins like [neoterm](https://github.com/kassio/neoterm),
[vimcmdline](https://github.com/jalvesaq/vimcmdline),
[vim-slime](https://github.com/jpalardy/vim-slime),
[repl.nvim](https://gitlab.com/HiPhish/repl.nvim) and
[iron.nvim](https://github.com/BurningEther/iron.nvim). It does not care for
filetype-to-REPL mappings and starting your REPL. Instead, you go to an
existing terminal that is running your REPL and type `:SendHere`.

After that you can use the `s` operator from any buffer to send
text to the terminal. The behaviour of the `s` operator closely matches vim's
built-in `y` or `d` operators. It works line-wise (`ss`, `3ss`), with visual
selection (`vjs`, `Vjjs`) and with motions/text-objects (`sj`, `sip`).

## Multiline quirks

For multiline text, some REPLs (e.g. IPython) only receive the first line. For
them, try `:SendHere ipy` in the terminal. You can add support for your own
REPL's multiline quirks in your init.vim with:

```vim
let g:send_multiline = {
    'repl1': {'begin':..., 'end':..., 'newline':...},
    'repl2': {'begin':..., 'end':..., 'newline':...},
    ...
}
```

Then use them as: `:SendHere repl1`.

## Provided commands, functions, operators

```vim
g:send_multiline
:SendHere <repl>
:SendHere         " send with default multiline settings
[count]ss
<visual selection>s
s<motion>
S
```

## To do

1. Allow buffers/windows to have different target terminals.
2. Add motions for IPython-style cell-blocks (e.g. send all code between two
   comments), function, indent-level, etc.

## Sending to Jupyter kernels

This "Send" framework is very extensible. You only need to define a vim
function: `function SendToTarget(lines) ...` and save it in a variable:
`let g:send_target = {'send': function('SendToTarget')}`. You can add other data
to `g:send_target` that may be relevant to your function.

If you have the Neovim [Python client](https://github.com/neovim/python-client)
and Jupyter client packages installed in Neovim's python host, you can send
directly to Jupyter kernels. Simply do `:SendTo <kernel-pid.json>`. This is
useful for sending code to QtConsole and using its rich display of images,
inline plots, etc. You need to turn on QtConsole's display of remote commands
in one of the following ways:

1. Put `c.ConsoleWidget.include_other_output = True` in `~/.jupyter/jupyter_qtconsole_config.py`
2. Or, starting QtConsole with `jupyter qtconsole --JupyterWidget.include_other_output=True`

You can install the necessary packages with `pip install neovim jupyter_client`.

### Autocomplete with Jupyter kernels

When a connection to a Jupyter kernel is established, you can use the kernel's
autocomplete feature in the editor. At the bare minimum, you would do:

```vim
:SendTo <kernel-pid.json>
:setlocal omnifunc=SendComplete
```

Type Ctrl-x Ctrl-o to see the autocomplete suggestions. You can integrate it
with other vim autocomplete plugins that work with user-defined completions or
omnicompletion.

### Provided commands

```vim
:SendTo <kernel-pid.json>
:SendTo           " send to the kernel started latest
SendComplete()
```
