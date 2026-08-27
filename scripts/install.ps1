# FlossWare AI native Windows installer.
[CmdletBinding()]
param([string]$Profile='default',[switch]$Reinstall,[switch]$Clean,[switch]$ForceSource)
$ErrorActionPreference='Stop';$InstallRoot=if($env:FLOSSWARE_INSTALL_ROOT){$env:FLOSSWARE_INSTALL_ROOT}else{Join-Path $HOME '.flossware\ai'};$Venv=Join-Path $InstallRoot 'venv';$SetupDir=Join-Path $InstallRoot 'coding-agent-setup';$Ref=if($env:FLOSSWARE_RELEASE_REF){$env:FLOSSWARE_RELEASE_REF}else{'main'};$Repo='https://github.com/FlossWare/coding-agent-ai.git';$SetupRepo='https://github.com/FlossWare/coding-agent-setup.git'
function Show-Log($s){Write-Output "`n[FlossWare] $s"}
if($Clean){if(Test-Path $InstallRoot){Remove-Item -Recurse -Force $InstallRoot};$shim=Join-Path $HOME '.local\bin\flossware-ai.cmd';if(Test-Path $shim){Remove-Item -Force $shim};Show-Log 'Clean complete. Native agent/provider credentials were not touched.';exit 0}
# Git is optional: when absent, setup is fetched via codeload archive (same as Unix install.sh).
function Get-SetupTree {
  param([string]$Dest,[string]$Ref)
  if(Get-Command git -ErrorAction SilentlyContinue){
    if(Test-Path (Join-Path $Dest '.git')){ git -C $Dest fetch --depth 1 origin $Ref; git -C $Dest checkout --force $Ref; return }
    git clone --depth 1 --branch $Ref $SetupRepo $Dest; return
  }
  $zip = Join-Path $env:TEMP "coding-agent-setup-$Ref.zip"
  $url = "https://codeload.github.com/FlossWare/coding-agent-setup/zip/refs/heads/$Ref"
  if($Ref -match '^[0-9a-f]{7,40}$'){ $url = "https://codeload.github.com/FlossWare/coding-agent-setup/zip/$Ref" }
  Invoke-WebRequest -Uri $url -OutFile $zip
  $extract = Join-Path $env:TEMP "cas-extract-$Ref"
  if(Test-Path $extract){ Remove-Item -Recurse -Force $extract }
  Expand-Archive -Path $zip -DestinationPath $extract -Force
  $inner = Get-ChildItem $extract | Select-Object -First 1
  if(Test-Path $Dest){ Remove-Item -Recurse -Force $Dest }
  Move-Item $inner.FullName $Dest
}
$py=Get-Command py -ErrorAction SilentlyContinue;if(-not $py){$py=Get-Command python -ErrorAction SilentlyContinue};if(-not $py){throw 'Python 3.11+ is required.'};$pyCmd=$py.Source;&$pyCmd -c "import sys; assert sys.version_info >= (3,11), 'Python 3.11+ required'; print('Python',sys.version.split()[0])";New-Item -ItemType Directory -Force -Path $InstallRoot|Out-Null
if($Reinstall){foreach($p in @($Venv,$SetupDir,(Join-Path $InstallRoot 'bin'))){if(Test-Path $p){Remove-Item -Recurse -Force $p}}};if(-not(Test-Path $Venv)){&$pyCmd -m venv $Venv};$Vpy=Join-Path $Venv 'Scripts\python.exe';&$Vpy -m pip install --upgrade pip setuptools wheel fastmcp windows-curses
if($ForceSource -or $env:FLOSSWARE_USE_SOURCE -eq 'true'){&$Vpy -m pip install --upgrade "coding-agent-ai[all,tui] @ git+$Repo@$Ref"}else{if(-not (&$Vpy -m pip install --upgrade --prefer-binary 'coding-agent-ai[all,tui]')){&$Vpy -m pip install --upgrade "coding-agent-ai[all,tui] @ git+$Repo@$Ref"}}
Get-SetupTree -Dest $SetupDir -Ref $Ref
foreach($required in @('scripts\setup.py','scripts\tui.py','scripts\agent_setup.py','scripts\flossware-ai','scripts\discovery.py','scripts\mcp.py','scripts\runtime.py','profiles\default.toml')){if(-not(Test-Path(Join-Path $SetupDir $required))){throw "Missing $required"}}
$profileToml=Join-Path $SetupDir "profiles\$Profile.toml";if(-not(Test-Path $profileToml)){$profileToml=Join-Path $SetupDir 'profiles\default.toml'};if(-not(Test-Path $profileToml)){throw "Missing profiles/default.toml"}
&$Vpy -m compileall -q (Join-Path $SetupDir 'scripts') (Join-Path $SetupDir 'flossware_setup')
&$Vpy -m pip install -e $SetupDir --quiet
$profileDir=Join-Path $InstallRoot "config\profiles\$Profile";New-Item -ItemType Directory -Force -Path $profileDir,(Join-Path $InstallRoot 'bin'),(Join-Path $InstallRoot 'state'),(Join-Path $InstallRoot 'cache'),(Join-Path $InstallRoot 'mcp')|Out-Null;Copy-Item $profileToml (Join-Path $profileDir 'profile.toml') -Force;foreach($f in @('flossware-ai','tui.py','agent_setup.py','setup.py','discovery.py','mcp.py','runtime.py','dogfood.py')){Copy-Item (Join-Path $SetupDir "scripts\$f") (Join-Path $InstallRoot $f) -Force};Set-Content (Join-Path $InstallRoot 'state\active-profile') $Profile;Set-Content (Join-Path $profileDir 'profile.json') ('{"profile":"'+$Profile+'","credential_values_written":false,"credential_source":"native-agent-store-or-environment"}')
$LauncherDir=Join-Path $HOME '.local\bin';New-Item -ItemType Directory -Force -Path $LauncherDir|Out-Null;$Launcher=Join-Path $LauncherDir 'flossware-ai.cmd'
@"
@echo off
setlocal
set "ROOT=$InstallRoot"
set "PY=$Vpy"
if /I "%~1"=="tui" ("%PY%" "%ROOT%\setup.py" & exit /b %ERRORLEVEL%)
if /I "%~1"=="setup" ("%PY%" "%ROOT%\setup.py" & exit /b %ERRORLEVEL%)
if /I "%~1"=="runtime" ("%PY%" "%ROOT%\runtime.py" %2 %3 %4 %5 & exit /b %ERRORLEVEL%)
if /I "%~1"=="doctor" ("%PY%" "%ROOT%\discovery.py" doctor & exit /b %ERRORLEVEL%)
if /I "%~1"=="accounts" ("%PY%" "%ROOT%\discovery.py" accounts %2 %3 %4 & exit /b %ERRORLEVEL%)
if /I "%~1"=="models" ("%PY%" "%ROOT%\discovery.py" models %2 %3 %4 & exit /b %ERRORLEVEL%)
"%ROOT%\bin\flossware-ai" %*
"@ | Set-Content $Launcher
Show-Log 'Installation complete';Write-Host "AI root: $InstallRoot";Write-Host "Profile: $Profile";Write-Host "Run: flossware-ai tui";Write-Host "Run: flossware-ai doctor";Write-Host "Reinstall: .\scripts\install.ps1 -Reinstall";Write-Host "Clean: .\scripts\install.ps1 -Clean"Get-SetupTree -Dest $SetupDir -Ref $Refre AI native Windows installer.
[CmdletBinding()]
param([string]$Profile='default',[switch]$Reinstall,[switch]$Clean,[switch]$ForceSource)
$ErrorActionPreference='Stop';$InstallRoot=if($env:FLOSSWARE_INSTALL_ROOT){$env:FLOSSWARE_INSTALL_ROOT}else{Join-Path $HOME '.flossware\ai'};$Venv=Join-Path $InstallRoot 'venv';$SetupDir=Join-Path $InstallRoot 'coding-agent-setup';$Ref=if($env:FLOSSWARE_RELEASE_REF){$env:FLOSSWARE_RELEASE_REF}else{'main'};$Repo='https://github.com/FlossWare/coding-agent-ai.git';$SetupRepo='https://github.com/FlossWare/coding-agent-setup.git'
function Show-Log($s){Write-Output "`n[FlossWare] $s"}
if($Clean){if(Test-Path $InstallRoot){Remove-Item -Recurse -Force $InstallRoot};$shim=Join-Path $HOME '.local\bin\flossware-ai.cmd';if(Test-Path $shim){Remove-Item -Force $shim};Show-Log 'Clean complete. Native agent/provider credentials were not touched.';exit 0}
# Git is optional: when absent, setup is fetched via codeload archive (same as Unix install.sh).
function Get-SetupTree {
  param([string]$Dest,[string]$Ref)
  if(Get-Command git -ErrorAction SilentlyContinue){
    if(Test-Path (Join-Path $Dest '.git')){ git -C $Dest fetch --depth 1 origin $Ref; git -C $Dest checkout --force $Ref; return }
    git clone --depth 1 --branch $Ref $SetupRepo $Dest; return
  }
  $zip = Join-Path $env:TEMP "coding-agent-setup-$Ref.zip"
  $url = "https://codeload.github.com/FlossWare/coding-agent-setup/zip/refs/heads/$Ref"
  if($Ref -match '^[0-9a-f]{7,40}$'){ $url = "https://codeload.github.com/FlossWare/coding-agent-setup/zip/$Ref" }
  Invoke-WebRequest -Uri $url -OutFile $zip
  $extract = Join-Path $env:TEMP "cas-extract-$Ref"
  if(Test-Path $extract){ Remove-Item -Recurse -Force $extract }
  Expand-Archive -Path $zip -DestinationPath $extract -Force
  $inner = Get-ChildItem $extract | Select-Object -First 1
  if(Test-Path $Dest){ Remove-Item -Recurse -Force $Dest }
  Move-Item $inner.FullName $Dest
}
$py=Get-Command py -ErrorAction SilentlyContinue;if(-not $py){$py=Get-Command python -ErrorAction SilentlyContinue};if(-not $py){throw 'Python 3.11+ is required.'};$pyCmd=$py.Source;&$pyCmd -c "import sys; assert sys.version_info >= (3,11), 'Python 3.11+ required'; print('Python',sys.version.split()[0])";New-Item -ItemType Directory -Force -Path $InstallRoot|Out-Null
if($Reinstall){foreach($p in @($Venv,$SetupDir,(Join-Path $InstallRoot 'bin'))){if(Test-Path $p){Remove-Item -Recurse -Force $p}}};if(-not(Test-Path $Venv)){&$pyCmd -m venv $Venv};$Vpy=Join-Path $Venv 'Scripts\python.exe';&$Vpy -m pip install --upgrade pip setuptools wheel fastmcp windows-curses
if($ForceSource -or $env:FLOSSWARE_USE_SOURCE -eq 'true'){&$Vpy -m pip install --upgrade "coding-agent-ai[all,tui] @ git+$Repo@$Ref"}else{if(-not (&$Vpy -m pip install --upgrade --prefer-binary 'coding-agent-ai[all,tui]')){&$Vpy -m pip install --upgrade "coding-agent-ai[all,tui] @ git+$Repo@$Ref"}}
Get-SetupTree -Dest $SetupDir -Ref $Ref
foreach($required in @('scripts\setup.py','scripts\tui.py','scripts\agent_setup.py','scripts\flossware-ai','scripts\discovery.py','scripts\mcp.py','scripts\runtime.py','profiles\default.toml')){if(-not(Test-Path(Join-Path $SetupDir $required))){throw "Missing $required"}}
$profileToml=Join-Path $SetupDir "profiles\$Profile.toml";if(-not(Test-Path $profileToml)){$profileToml=Join-Path $SetupDir 'profiles\default.toml'};if(-not(Test-Path $profileToml)){throw "Missing profiles/default.toml"}
&$Vpy -m compileall -q (Join-Path $SetupDir 'scripts') (Join-Path $SetupDir 'flossware_setup')
&$Vpy -m pip install -e $SetupDir --quiet
$profileDir=Join-Path $InstallRoot "config\profiles\$Profile";New-Item -ItemType Directory -Force -Path $profileDir,(Join-Path $InstallRoot 'bin'),(Join-Path $InstallRoot 'state'),(Join-Path $InstallRoot 'cache'),(Join-Path $InstallRoot 'mcp')|Out-Null;Copy-Item $profileToml (Join-Path $profileDir 'profile.toml') -Force;foreach($f in @('flossware-ai','tui.py','agent_setup.py','setup.py','discovery.py','mcp.py','runtime.py','dogfood.py')){Copy-Item (Join-Path $SetupDir "scripts\$f") (Join-Path $InstallRoot $f) -Force};Set-Content (Join-Path $InstallRoot 'state\active-profile') $Profile;Set-Content (Join-Path $profileDir 'profile.json') ('{"profile":"'+$Profile+'","credential_values_written":false,"credential_source":"native-agent-store-or-environment"}')
$LauncherDir=Join-Path $HOME '.local\bin';New-Item -ItemType Directory -Force -Path $LauncherDir|Out-Null;$Launcher=Join-Path $LauncherDir 'flossware-ai.cmd'
@"
@echo off
setlocal
set "ROOT=$InstallRoot"
set "PY=$Vpy"
if /I "%~1"=="tui" ("%PY%" "%ROOT%\setup.py" & exit /b %ERRORLEVEL%)
if /I "%~1"=="setup" ("%PY%" "%ROOT%\setup.py" & exit /b %ERRORLEVEL%)
if /I "%~1"=="runtime" ("%PY%" "%ROOT%\runtime.py" %2 %3 %4 %5 & exit /b %ERRORLEVEL%)
if /I "%~1"=="doctor" ("%PY%" "%ROOT%\discovery.py" doctor & exit /b %ERRORLEVEL%)
if /I "%~1"=="accounts" ("%PY%" "%ROOT%\discovery.py" accounts %2 %3 %4 & exit /b %ERRORLEVEL%)
if /I "%~1"=="models" ("%PY%" "%ROOT%\discovery.py" models %2 %3 %4 & exit /b %ERRORLEVEL%)
"%ROOT%\bin\flossware-ai" %*
"@ | Set-Content $Launcher
Show-Log 'Installation complete';Write-Host "AI root: $InstallRoot";Write-Host "Profile: $Profile";Write-Host "Run: flossware-ai tui";Write-Host "Run: flossware-ai doctor";Write-Host "Reinstall: .\scripts\install.ps1 -Reinstall";Write-Host "Clean: .\scripts\install.ps1 -Clean"
