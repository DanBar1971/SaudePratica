#define MyAppName "SaúdePrática Desktop"
#ifndef MyAppVersion
  #define MyAppVersion "0.6.5"
#endif
#define MyAppPublisher "SaúdePrática"
#define MyAppExeName "SaudePraticaDesktop.exe"

[Setup]
AppId={{1D13C332-4A78-4B9C-B08A-6A14D855B9F2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion} (experimental)
AppPublisher={#MyAppPublisher}
AppPublisherURL=https://danbar1971.github.io/SaudePratica/
AppSupportURL=https://github.com/DanBar1971/SaudePratica/issues
AppUpdatesURL=https://github.com/DanBar1971/SaudePratica/releases
DefaultDirName={localappdata}\Programs\SaudePraticaDesktop
DefaultGroupName=SaúdePrática
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\SaudePratica.ico
OutputDir=..\..\dist\installer
OutputBaseFilename=SaudePratica-Setup
SetupIconFile=..\..\dist\saude_icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
MinVersion=10.0
CloseApplications=yes
RestartApplications=no
UsePreviousAppDir=yes
UsePreviousTasks=yes

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar um atalho no Ambiente de Trabalho"; GroupDescription: "Atalhos:"; Flags: unchecked

[Files]
Source: "..\..\dist\SaudePraticaDesktop\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\dist\saude_icon.ico"; DestDir: "{app}"; DestName: "SaudePratica.ico"; Flags: ignoreversion

[Icons]
Name: "{userprograms}\SaúdePrática Desktop"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\SaudePratica.ico"
Name: "{userdesktop}\SaúdePrática Desktop"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\SaudePratica.ico"; Tasks: desktopicon

[Registry]
; User-only autostart of the independent Agenda reminder worker.
; Runs after Windows sign-in, even if the desktop UI was closed.
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "SaudePraticaAgendaReminders"; ValueData: """{app}\{#MyAppExeName}"" --reminder-agent"; Flags: uninsdeletevalue

[Run]
; Always start background reminders after upgrading, even when the UI is not opened.
Filename: "{app}\{#MyAppExeName}"; Parameters: "--reminder-agent"; Flags: nowait runhidden
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir a SaúdePrática Desktop"; Flags: nowait postinstall skipifsilent

; O desinstalador deixa os dados pessoais em %LOCALAPPDATA%\SaudePraticaDesktop.
; Nunca apagar dados clínicos sem uma confirmação específica.

[Code]
const
  EVENT_MODIFY_STATE = $0002;
  REMINDER_STOP_EVENT = 'Local\SaudePraticaAgendaReminderAgentStop';

function OpenEventW(dwDesiredAccess: Cardinal; bInheritHandle: Boolean;
  lpName: String): Integer;
  external 'OpenEventW@kernel32.dll stdcall';
function SetEvent(hEvent: Integer): Boolean;
  external 'SetEvent@kernel32.dll stdcall';
function CloseHandle(hObject: Integer): Boolean;
  external 'CloseHandle@kernel32.dll stdcall';

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  handle: Integer;
  script: String;
  exitCode: Integer;
  executable: String;
begin
  Result := '';
  { Do not end the main UI process. Request graceful agent shutdown first. }
  handle := OpenEventW(EVENT_MODIFY_STATE, False, REMINDER_STOP_EVENT);
  if handle <> 0 then begin
    SetEvent(handle);
    CloseHandle(handle);
    Sleep(1600);
  end else begin
    { For installations upgrading from v0.7.2: the legacy helper did not
      implement the stop event. Stop only its resident background instance,
      using the exact EXE path and the --reminder-agent command-line flag.
      Never terminate unrelated programs or a foreground editor. }
    executable := ExpandConstant('{app}\{#MyAppExeName}');
    StringChangeEx(executable, '''', '''''', True);
    script :=
      'Get-CimInstance Win32_Process -Filter ''Name = "SaudePraticaDesktop.exe"'' ' +
      '| Where-Object { $_.CommandLine -like ''*--reminder-agent*'' -and ' +
      '$_.ExecutablePath -eq ''' + executable + ''' } ' +
      '| ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }';
    Exec(ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'),
      '-NoProfile -NonInteractive -Command "' + script + '"',
      '', SW_HIDE, ewWaitUntilTerminated, exitCode);
  end;
end;
