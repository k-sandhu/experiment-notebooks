$env:ASTRA_SQL_PREPARED_DIR = $PSScriptRoot
$env:ASTRA_SQL_EFFORT = 'xhigh'
$env:ASTRA_SQL_KEEP_HISTORY = '1'
$env:ASTRA_SQL_ATTEMPT = '1'
$boundedSqlHarness = Join-Path (Split-Path $PSScriptRoot -Parent) 'run_astra_weights.py'
& 'C:\Users\sandh\.codex\scratch\macrostories-19969-venv\Scripts\python.exe' -X utf8 $boundedSqlHarness
