function! s:SendHere(...)
    if !exists("b:terminal_job_id")
        echoerr "This buffer is not a terminal."
        return
    end

    let g:send_term_id = b:terminal_job_id

    if a:0 == 0
        unlet! g:send_bp
    elseif a:0 == 1 && a:1 ==# "bracketed"
        " bracketed paste
        let g:send_bp = ["\e[200~", "\e[201~", ""]
    else
        echoerr "Unknown arguments: " . join(a:000)
    endif
endfunction

function! s:SendOpts(ArgLead, CmdLine, CursorPos)
    return ["bracketed"]
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
    let send_bp = (exists("g:send_bp") && len(lines) > 1)? g:send_bp: ['', '', '']
    let lines[0] = send_bp[0] . lines[0]
    let lines[-1] = lines[-1] . send_bp[1]
    call jobsend(g:send_term_id, lines + send_bp[2:])
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
