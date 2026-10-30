#define MyAppName "SaúdePrática Desktop"
#ifndef MyAppVersion
  #define MyAppVersion "0.4.1"
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

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir a SaúdePrática Desktop"; Flags: nowait postinstall skipifsilent

; O desinstalador deixa os dados pessoais em %LOCALAPPDATA%\SaudePraticaDesktop.
; Nunca apagar dados clínicos sem uma confirmação específica.
