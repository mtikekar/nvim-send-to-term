function! s:SendHere()
    if exists("b:terminal_job_id")
        let g:term_id = b:terminal_job_id
    else
        echoerr "This buffer is not a terminal."
    endif
endfunction

function! s:GetCol(e)
    return getpos(a:e)[2] - 1
endfunction

function! s:SendToTerm(mode, ...)
    if !exists("g:term_id")
        echoerr "Destination terminal not set. Do :SendHere in the desired terminal."
        return 0
    end

    if a:0 > 0
        " explicit lines provided as function arguments
        return jobsend(g:term_id, add(a:000, ''))
    end

    " mode tells how the operator s was used. e.g.
    " viws  v
    " Vjjs  V
    " siw   char
    " sG    line
    " In first two cases, marks are < and >. In the last two, marks are [ ]
    if a:mode ==# 'v' || a:mode ==# 'V'
        let smark = "'<"
        let emark = "'>"
    else
        let smark = "'["
        let emark = "']"
    end
    let lines = getline(smark, emark)
    if a:mode ==# 'char' || a:mode ==# 'v'
        " For char-based modes, truncate first and last lines
        let lines[0] = lines[0][s:GetCol(smark):]
        let lines[-1] = lines[-1][s:GetCol(emark)]
    end
    " echom a:mode . string(getpos(smark)) . string(getpos(emark))
    return jobsend(g:term_id, add(lines, ''))
endfunction

command! SendHere :call <SID>SendHere()

nmap <silent> ss :call <SID>SendToTerm('', getline('.'))<cr>
nmap <silent> S s$

nmap <silent> s :set opfunc=<SID>SendToTerm<cr>g@
vmap <silent> s :<c-u>call <SID>SendToTerm(visualmode())<cr>
