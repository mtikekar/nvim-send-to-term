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

| Name                            | Documentation                                                |
| ------------------------------- | ------------------------------------------------------------ |
| `:SendHere`, `:SendHere <repl>` | Set current terminal as send target with multiline settings for `repl`. If `repl` is not provided, default mutliline settings are used. |
| `[count]ss`                     | Send `count` lines and move cursor to last line.             |
| `<visual>s`                     | Send visual selection.                                       |
| `s<motion>`                     | Send motion or text object (like `y/d` for yank/delete).     |
| `S`                             | Send from current column till end of line (like `D`)         |
| `g:send_multiline`              | Add multiline settings for your favourite REPL here.         |
| `g:send_disable_mapping`        | Disable `s`, `S`, `ss` mappings                              |
| `<Plug>Send`, `<Plug>SendLine`  | Use these to define your own mapping                         |



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

### Provided commands, functions

| Name        |  Documentation           |
|-------------|--------------------------|
| `:SendTo`, `:SendTo <kernel-pid.json>` | Send to existing Jupyter kernel. Run `%connect_info` in the Python session to get value of `kernel-pid.json`. Or, skip it to connect to latest started kernel. |
| `SendComplete()`     | Completion function to be used as `omnifunc` or `completefunc` |
