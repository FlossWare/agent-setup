# FlossWare AI native Windows installer.
[CmdletBinding()]
param([ValidateSet('personal','redhat')][string]$Profile='personal',[switch]$Reinstall,[switch]$Clean,[switch]$ForceSource)
$ErrorActionPreference='Stop';$InstallRoot=if($env:FLOSSWARE_INSTALL_ROOT){$env:FLOSSWARE_INSTALL_ROOT}else{Join-Path $HOME '.flossware\ai'};$Venv=Join-Path $InstallRoot 'venv';$SetupDir=Join-Path $InstallRoot 'coding-agent-setup';$Ref=if($env:FLOSSWARE_RELEASE_REF){$env:FLOSSWARE_RELEASE_REF}else{'main'};$Repo='https://github.com/FlossWare/coding-agent-ai.git';$SetupRepo='https://github.com/FlossWare/coding-agent-setup.git'
function Log($s){Write-Host "`n[FlossWare] $s"}
if($Clean){if(Test-Path $InstallRoot){Remove-Item -Recurse -Force $InstallRoot};$shim=Join-Path $HOME '.local\bin\flossware-ai.cmd';if(Test-Path $shim){Remove-Item -Force $shim};Log 'Clean complete. Native agent/provider credentials were not touched.';exit 0}
if(-not(Get-Command git -ErrorAction SilentlyContinue)){throw 'Git is required. Install Git for Windows first.'};$py=Get-Command py -ErrorAction SilentlyContinue;if(-not $py){$py=Get-Command python -ErrorAction SilentlyContinue};if(-not $py){throw 'Python 3.11+ is required.'};$pyCmd=$py.Source;&$pyCmd -c "import sys; assert sys.version_info >= (3,11), 'Python 3.11+ required'; print('Python',sys.version.split()[0])";New-Item -ItemType Directory -Force -Path $InstallRoot|Out-Null
if($Reinstall){foreach($p in @($Venv,$SetupDir,(Join-Path $InstallRoot 'bin'))){if(Test-Path $p){Remove-Item -Recurse -Force $p}}};if(-not(Test-Path $Venv)){&$pyCmd -m venv $Venv};$Vpy=Join-Path $Venv 'Scripts\python.exe';&$Vpy -m pip install --upgrade pip setuptools wheel fastmcp windows-curses
if($ForceSource -or $env:FLOSSWARE_USE_SOURCE -eq 'true'){&$Vpy -m pip install --upgrade "coding-agent-ai[all,tui] @ git+$Repo@$Ref"}else{if(-not (&$Vpy -m pip install --upgrade --prefer-binary 'coding-agent-ai[all,tui]')){&$Vpy -m pip install --upgrade "coding-agent-ai[all,tui] @ git+$Repo@$Ref"}}
if(Test-Path(Join-Path $SetupDir '.git')){git -C $SetupDir fetch --force origin $Ref;git -C $SetupDir checkout --force $Ref;git -C $SetupDir reset --hard "origin/$Ref"}else{git clone --depth 1 --branch $Ref $SetupRepo $SetupDir}
foreach($required in @('scripts\setup.py','scripts\tui.py','scripts\setup_tui.py','scripts\agent_setup.py','scripts\flossware-ai','scripts\discovery.py','scripts\mcp.py','scripts\runtime.py')){if(-not(Test-Path(Join-Path $SetupDir $required))){throw "Missing $required"}};&$Vpy -m compileall -q (Join-Path $SetupDir 'scripts')
$profileDir=Join-Path $InstallRoot "config\profiles\$Profile";New-Item -ItemType Directory -Force -Path $profileDir,(Join-Path $InstallRoot 'bin'),(Join-Path $InstallRoot 'state'),(Join-Path $InstallRoot 'cache'),(Join-Path $InstallRoot 'mcp')|Out-Null;Copy-Item (Join-Path $SetupDir "profiles\$Profile.toml") (Join-Path $profileDir 'profile.toml') -Force;foreach($f in @('flossware-ai','tui.py','setup_tui.py','agent_setup.py','setup.py','discovery.py','mcp.py','runtime.py')){Copy-Item (Join-Path $SetupDir "scripts\$f") (Join-Path $InstallRoot $f) -Force};Set-Content (Join-Path $InstallRoot 'state\active-profile') $Profile;Set-Content (Join-Path $profileDir 'profile.json') ('{"profile":"'+$Profile+'","credential_values_written":false,"credential_source":"native-agent-store-or-environment"}')
$LauncherDir=Join-Path $HOME '.local\bin';New-Item -ItemType Directory -Force -Path $LauncherDir|Out-Null;$Launcher=Join-Path $LauncherDir 'flossware-ai.cmd';@"
@echo off
setlocal
set "ROOT=$InstallRoot"
set "PY=$Vpy"
if /I "%~1"=="tui" ("%PY%" "%ROOT%\setup_tui.py" & exit /b %ERRORLEVEL%)
if /I "%~1"=="runtime" ("%PY%" "%ROOT%\runtime.py" %2 %3 %4 %5 & exit /b %ERRORLEVEL%)
if /I "%~1"=="doctor" ("%PY%" "%ROOT%\discovery.py" doctor & exit /b %ERRORLEVEL%)
if /I "%~1"=="accounts" ("%PY%" "%ROOT%\discovery.py" accounts %2 %3 %4 & exit /b %ERRORLEVEL%)
if /I "%~1"=="models" ("%PY%" "%ROOT%\discovery.py" models %2 %3 %4 & exit /b %ERRORLEVEL%)
"%ROOT%\bin\flossware-ai" %*
"@ | Set-Content $Launcher
Log 'Installation complete';Write-Host "AI root: $InstallRoot";Write-Host "Profile: $Profile";Write-Host "Run: flossware-ai tui";Write-Host "Run: flossware-ai doctor";Write-Host "Reinstall: .\scripts\install.ps1 -Reinstall";Write-Host "Clean: .\scripts\install.ps1 -Clean"
