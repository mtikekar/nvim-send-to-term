# Neovim plugin to send text from a buffer to a terminal

It is much simpler than other similar plugins like
[neoterm](https://github.com/kassio),
[vimcmdline](https://github.com/jalvesaq/vimcmdline),
[vim-slime](https://github.com/jpalardy/vim-slime),
[repl.nvim](https://gitlab.com/HiPhish/repl.nvim), etc. It does not care for
filetypes and REPLs. Instead, you go to an existing terminal and type
`:SendHere`. After that you can use the `s` operator from any buffer to send
text to the terminal. The behaviour of the `s` operator closely matches vim's
built-in `y` or `d` operators.

## To do

1. Allow buffers/windows to have different target terminals.
2. Add motions for IPython-style cell-blocks (e.g. send all code between two
   comments), function, indent-level, etc.
