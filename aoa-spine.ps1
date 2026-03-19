param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

python -m core.cli @Arguments
