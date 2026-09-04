#ifndef SourceDir
  #define SourceDir "build\exe.win-amd64-3.8"
#endif

#ifndef AppVersion
  #define AppVersion "1.7.1"
#endif

[Setup]
AppId={{1A444D72-6C74-4BA7-BC48-C4649397B44B}
AppName=SportOrg Tourism
AppVersion={#AppVersion}
AppPublisher=SportOrg
DefaultDirName={localappdata}\Programs\SportOrg Tourism
DefaultGroupName=SportOrg Tourism
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=img\icon\sportorg.ico
UninstallDisplayIcon={app}\SportOrg.exe
OutputDir=dist
OutputBaseFilename=SportOrg-Tourism-Setup-{#AppVersion}-x64

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SportOrg Tourism"; Filename: "{app}\SportOrg.exe"
Name: "{autodesktop}\SportOrg Tourism"; Filename: "{app}\SportOrg.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительные ярлыки:"

[Run]
Filename: "{app}\SportOrg.exe"; Description: "Запустить SportOrg Tourism"; Flags: nowait postinstall skipifsilent
