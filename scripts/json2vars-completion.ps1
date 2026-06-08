# json2vars PowerShell tab completion (robust + discoverable).
#
# Dot-source this from your $PROFILE:
#     . "<path-to-repo>\scripts\json2vars-completion.ps1"
#
# Why not `json2vars --show-completion`? Typer's generated completer splits each
# `value:::help` candidate on ":::" and builds a CompletionResult whose tooltip
# must be non-empty. Long option help is wrapped across lines by Typer/rich; the
# wrapped fragment has no ":::", so the tooltip is empty and CompletionResult
# throws -- a whole command (e.g. cache-version) then returns no completions and
# the completion env vars leak (a later `json2vars --help` prints completion noise
# instead of help). This completer keeps only ":::" lines, splits on the first
# separator, falls back to the value for an empty tooltip, resets the env vars in
# finally, and -- only when a bare word matched nothing -- re-queries so option
# names are discoverable without typing a leading dash.

$json2varsCompleter = {
    param($wordToComplete, $commandAst, $cursorPosition)
    $base = $commandAst.ToString()
    $seen = @{}
    $results = [System.Collections.Generic.List[System.Management.Automation.CompletionResult]]::new()
    $fetch = {
        param($a, $w)
        $Env:_JSON2VARS_COMPLETE = "complete_powershell"
        $Env:_TYPER_COMPLETE_ARGS = $a
        $Env:_TYPER_COMPLETE_WORD_TO_COMPLETE = $w
        try {
            json2vars | Where-Object { $_ -like '*:::*' } | ForEach-Object {
                $i = $_.IndexOf(':::')
                $v = $_.Substring(0, $i)
                if ([string]::IsNullOrWhiteSpace($v) -or $seen.ContainsKey($v)) { return }
                $seen[$v] = $true
                $h = $_.Substring($i + 3).Trim()
                if ([string]::IsNullOrWhiteSpace($h)) { $h = $v }
                $results.Add([System.Management.Automation.CompletionResult]::new(
                        $v, $v, 'ParameterValue', $h))
            }
        }
        finally {
            $Env:_JSON2VARS_COMPLETE = ""
            $Env:_TYPER_COMPLETE_ARGS = ""
            $Env:_TYPER_COMPLETE_WORD_TO_COMPLETE = ""
        }
    }
    & $fetch $base $wordToComplete
    # Nothing matched at an empty word (an option position, no dash typed): offer
    # the command's option names so they are discoverable without a leading '-'.
    if ($results.Count -eq 0 -and [string]::IsNullOrEmpty($wordToComplete)) {
        & $fetch ($base.TrimEnd() + ' -') '-'
    }
    $results
}
Register-ArgumentCompleter -Native -CommandName json2vars -ScriptBlock $json2varsCompleter
