if !exists("g:send_multiline")
    let g:send_multiline = {}
endif
let g:send_multiline.ipy = ["\e[200~", "\e[201~\n\r", "\n"]

function! s:SendHere(...)
    if !exists("b:terminal_job_id")
        echoerr "This buffer is not a terminal."
        return
    end

    let g:send_term_id = b:terminal_job_id

    if a:0 == 0
        let s:send_bp = ["", "\n", "\n"]
    elseif a:0 == 1 && has_key(g:send_multiline, a:1)
        let s:send_bp = g:send_multiline[a:1]
    else
        echoerr "Unsupported terminal multiline arguments: " . join(a:000)
    endif
endfunction

function! s:SendOpts(ArgLead, CmdLine, CursorPos)
    return keys(g:send_multiline)
endfunction

function! s:SendToTerm(mode, ...)
    if !exists("g:send_term_id")
        echoerr "Destination terminal not set. Do :SendHere in the desired terminal."
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
            let [c0, c1] = map(copy(marks), "getpos(v:val)[2] - 1")
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
    if len(lines) > 1
        let line = s:send_bp[0] . join(lines, s:send_bp[2]) . s:send_bp[1]
    else
        let line = lines[0] . "\n"
    endif
    call jobsend(g:send_term_id, line)
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
