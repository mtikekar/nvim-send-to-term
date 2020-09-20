# Neovim plugin to send text from a buffer to a terminal

This plugin aims to be simpler in design and easier to use than other similar plugins like
[neoterm](https://github.com/kassio/neoterm),
[vimcmdline](https://github.com/jalvesaq/vimcmdline),
[vim-slime](https://github.com/jpalardy/vim-slime),
[repl.nvim](https://gitlab.com/HiPhish/repl.nvim) and
[iron.nvim](https://github.com/BurningEther/iron.nvim). It does not care for filetype-to-REPL
mappings and starting your REPL. Instead, you go to an existing terminal that is running your REPL
and type `:SendHere`.

After that you can use the `s` operator from any buffer to send text to the terminal. The
behaviour of the `s` operator closely matches vim's built-in `y` or `d` operators. It works
line-wise (`ss`, `3ss`), with visual selection (`vjs`, `Vjjs`) and with motions/text-objects
(`sj`, `sip`).

## Multiline quirks

For multiline text, some REPLs (e.g. IPython) only receive the first line. For them, try
`:SendHere ipy` in the terminal. You can add support for the REPL's multiline quirks in your
init.vim with:

```vim
let g:send_multiline = {
    'repl1': {'begin':..., 'end':..., 'newline':...},
    'repl2': {'begin':..., 'end':..., 'newline':...},
    ...
}
```

Then use them as: `:SendHere repl1`. If the REPL supports
[bracketed paste](https://cirw.in/blog/bracketed-paste), usually, something like
`{'begin':"\e[200~", 'end':"\e[201~\n", 'newline':"\n"}` should work.

## Provided commands, functions, operators

| Name                            | Description                                                  |
| ------------------------------- | ------------------------------------------------------------ |
| `:SendHere`                     | Set current terminal as send target with default multiline settings |
| `:SendHere <repl>`              | Set current terminal as send target with multiline settings for `repl` |
| `[count]ss`                     | Send `count` lines and move cursor to last line.             |
| `<visual>s`                     | Send visual selection.                                       |
| `s<motion>`                     | Send motion or text object (like `y/d` for yank/delete).     |
| `S`                             | Send from current column till end of line (like `D`)         |
| `g:send_multiline`              | Add multiline settings for your favourite REPL here.         |
| `g:send_disable_mapping`        | Disable `s`, `S`, `ss` mappings                              |
| `<Plug>Send`, `<Plug>SendLine`  | Use these to define your own mappings as shown below         |

The default mappings are defined as follows. You can define your own mappings by following these.

```viml
nmap ss <Plug>SendLine
nmap s <Plug>Send
vmap s <Plug>Send
nmap S s$
```

## Other plugins

This plugin works nicely with [vim-pythonsense](https://github.com/jeetsukumaran/vim-pythonsense).
For example, you can do `saf` and `sac` to send functions and classes from your code buffer to the
Python REPL.

## Extensions for other targets

This plugin is extensible: you can define other types of targets to send text to as follows:

1. Define a vim function: `function SendToTarget(lines) ...`. `lines` is a list of strings that
   hold the text to be sent.
2. Save the function to the `send_target` variable: `let g:send_target = {'send': function('SendToTarget')}`
3. Optional: add other fields to `g:send_target` that are relevant to your function.

## Sending to Jupyter kernels

Using the extension feature described above, I have implemented a extension (included with the
plugin) to send code directly to Jupyter kernels running in notebook, lab, qtconsole or console.
You have to install the Neovim [Python client](https://github.com/neovim/python-client) and
Jupyter client in Neovim's python host with:

```bash
pip install pynvim jupyter_client
# or, if you're using conda
conda install -c conda-forge pynvim jupyter_client
```

Then, you start a kernel in any of the Jupyter applications and run `:SendTo <kernel-pid.json>`.
This is useful for sending code to QtConsole and using its rich display of images, inline plots,
etc. You need to enable QtConsole's display of remote commands in its config file (usually
`~/.jupyter/jupyter_qtconsole_config.py`):

```python
c.ConsoleWidget.include_other_output = True
c.ConsoleWidget.other_output_prefix = ''
```

For Jupyter Console, add to `~/.jupyter/jupyter_console_config.py`:

```python
c.ZMQTerminalInteractiveShell.include_other_output = True
c.ZMQTerminalInteractiveShell.other_output_prefix = ''
```

Without these config settings, the kernels receive and execute the code, but do not display
the code or the results.

### Autocomplete with Jupyter kernels

When a connection to a Jupyter kernel is established, you can use the kernel's autocomplete
feature in the editor. At the bare minimum, you would do:

```vim
:SendTo <kernel-pid.json>
:setlocal omnifunc=SendComplete
```

Type Ctrl-x Ctrl-o to see the autocomplete suggestions. You can integrate it with other vim
autocomplete plugins that work with user-defined completions or omnicompletion.

### Provided commands, functions

| Name        |  Documentation           |
|-------------|--------------------------|
| `:SendTo`, `:SendTo <kernel-pid.json>` | Send to existing Jupyter kernel. Run `%connect_info` in the Python session to get value of `kernel-pid.json`. By default, connect to latest started kernel. |
| `SendComplete()`     | Completion function to be used as `omnifunc` or `completefunc` |
| `SendCanComplete(line)`  | Completion is available for `line` |

## To do

1. Allow buffers/windows to have different target terminals.
2. Add motions for IPython-style cell-blocks e.g. send all code between two comments.
