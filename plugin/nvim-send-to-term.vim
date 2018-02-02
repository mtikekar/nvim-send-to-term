if !exists('g:send_multiline')
    let g:send_multiline = {}
endif
let g:send_multiline.default = {'begin':'', 'end':"\n", 'newline':"\n"}
let g:send_multiline.ipy = {'begin':"\e[200~", 'end':"\e[201~\r\r\r", 'newline':"\n"}
" This works too:
" let g:send_multiline.ipy = {'begin':'', 'end':"\r\r\r", 'newline':"\<c-q>\n"}

function! s:SendHere(...)
    if !exists('b:terminal_job_id')
        echoerr 'This buffer is not a terminal.'
        return
    end

    let term_type = get(a:000, 0, 'default')
    let g:send_target = {'id': b:terminal_job_id}
    call extend(g:send_target, g:send_multiline[term_type])
endfunction

function! s:SendOpts(ArgLead, CmdLine, CursorPos)
    return keys(g:send_multiline)
endfunction

function! s:SendToTerm(mode, ...)
    if !exists('g:send_target')
        echoerr 'Target terminal not set. Do :SendHere in the desired terminal.'
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
            let [c0, c1] = map(copy(marks), 'getpos(v:val)[2] - 1')
            if len(lines) == 1
                let lines[0] = lines[0][c0:c1]
            else
                let lines[0] = lines[0][c0:]
                let lines[-1] = lines[-1][:c1]
            endif
        end
        " echom string(marks)
        " echom join([a:mode, getpos(marks[0]), getpos(marks[1]), lines])
    endif
    " echom string(lines)
    let term = g:send_target
    if len(lines) > 1
        let line = term.begin . join(lines, term.newline) . term.end
    else
        let line = lines[0] . "\n"
    endif
    call jobsend(term.id, line)
    " If sending multiple lines over multiple commands, slow down a little to
    " let some REPLs catch up (IPython, basically)
    if v:count1 > 1
        " echom v:count1
        sleep 100m
    endif
endfunction

command! -complete=customlist,<SID>SendOpts -nargs=? SendHere :call <SID>SendHere(<f-args>)

nmap <silent> ss :call <SID>SendToTerm('direct', getline('.'))<cr>
nmap <silent> S s$

nmap <silent> s :set opfunc=<SID>SendToTerm<cr>g@
vmap <silent> s :<c-u>call <SID>SendToTerm(visualmode())<cr>
