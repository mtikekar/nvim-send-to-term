if exists("g:loaded_sendtoterm")
  finish
endif
let g:loaded_sendtoterm = 1

" Parts specific to terminal destination
let s:nl = has("win32")? "\r\n": "\n"
let g:send_multiline = get(g:, 'send_multiline', {})
let g:send_multiline.default = {'begin':'', 'end': s:nl, 'newline': s:nl}
let g:send_multiline.ipy = {'begin':"\e[200~", 'end':"\e[201~\r\r\r", 'newline': s:nl}
" This works too:
" let g:send_multiline.ipy = {'begin':'', 'end':"\r\r\r", 'newline':"\<c-q>\n"}

function! s:SendHere(...)
    if !exists('b:terminal_job_id')
        echoerr 'This buffer is not a terminal.'
        return
    end

    let term_type = get(a:000, 0, 'default')
    let g:send_target = {'term_id': b:terminal_job_id, 'send': function("s:SendLinesToTerm")}
    call extend(g:send_target, g:send_multiline[term_type])
endfunction

function! s:SendOpts(ArgLead, CmdLine, CursorPos)
    return keys(g:send_multiline)
endfunction

function! s:SendLinesToTerm(lines) dict
    " destination is a term
    if len(a:lines) > 1
        let line = self.begin . join(a:lines, self.newline) . self.end
    else
        let line = a:lines[0] . s:nl
    endif
    call jobsend(self.term_id, line)
    " If sending over multiple commands ([count]ss), slow down a little to
    " let some REPLs catch up (IPython, basically)
    if v:count1 > 1
        sleep 100m
    endif
endfunction

command! -complete=customlist,<SID>SendOpts -nargs=? SendHere :call <SID>SendHere(<f-args>)

" Parts specific to jupyter kernel destination
function! s:SendToJupyter(...)
    let cf = call('_SendToJupyter', a:000)
    if cf == v:null
        echom "No kernel found"
    else
        let g:send_target = {'ipy_conn': cf, 'send': function("s:SendLinesToJupyter")}
    endif
endfunction

function! s:SendLinesToJupyter(lines) dict
    call _SendLinesToJupyter(self.ipy_conn, a:lines)
endfunction

command! -complete=customlist,RunningKernels -nargs=? SendTo :call <SID>SendToJupyter(<f-args>)

" General 'Send' framework
function! s:Send(mode, ...)
    if !exists('g:send_target')
        echoerr 'Target terminal not set. Run :SendHere or :SendTo first.'
        return 0
    endif

    if a:mode ==# 'direct'
        " explicit lines provided as function arguments
        let lines = copy(a:000)
    else
        " mode tells how the operator s was used. e.g.
        " viws  v     (char-wise visual)
        " Vjjs  V     (line-vise visual)
        " siw   char  (char-wise normal text-object)
        " sG    line  (line-wise normal text-object)
        " In first two cases, marks are < and >. In the last two, marks are [ ]
        let marks = (a:mode ==? 'v')? ["'<", "'>"]: ["'[", "']"]
        let lines = getline(marks[0], marks[1])
        if a:mode ==# 'char' || a:mode ==# 'v'
            " For char-based modes, truncate first and last lines
            let col0 = col(marks[0]) - 1
            let col1 = col(marks[1]) - 1
            if len(lines) == 1
                let lines[0] = lines[0][col0:col1]
            else
                let lines[0] = lines[0][col0:]
                let lines[-1] = lines[-1][:col1]
            endif
        end
    endif

    call g:send_target.send(lines)
endfunction

nmap <silent> <Plug>SendLine :call <SID>Send('direct', getline('.'))<cr>
nmap <silent> <Plug>Send :set opfunc=<SID>Send<cr>g@
vmap <silent> <Plug>Send :<c-u>call <SID>Send(visualmode())<cr>

if get(g:, "send_disable_mapping", 0)
    finish
endif

nmap ss <Plug>SendLine
nmap s <Plug>Send
vmap s <Plug>Send
nmap S s$
