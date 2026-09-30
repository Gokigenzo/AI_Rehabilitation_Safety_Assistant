; Inno Setup Script for AI REHABILITATION & SAFETY ASSISTANT
; Generates a professional single-file Windows Installer (Setup_AI_Rehab_Safety_Assistant.exe)

#define MyAppName "AI Rehabilitation & Safety Assistant"
#define MyAppVersion "3.0"
#define MyAppPublisher "AI Care & Rehabilitation Team"
#define MyAppExeName "AI_Rehab_Safety_Assistant.exe"
#define MyAppSourceDir "dist\AI_Rehab_Safety_Assistant"

[Setup]
; Basic Application Info
AppId={{C6B5E891-884A-4D78-9B53-159D5B48B124}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\AI_Rehab_Safety_Assistant
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=release_installer
OutputBaseFilename=Setup_AI_Rehab_Safety_Assistant_v3.0
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copy all bundled application files from dist
Source: "{#MyAppSourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
; Ensure writable data and log directories exist
Name: "{app}\data"; Permissions: users-modify
Name: "{app}\data\users"; Permissions: users-modify
Name: "{app}\data\fall_events"; Permissions: users-modify
Name: "{app}\data\sessions"; Permissions: users-modify
Name: "{app}\logs"; Permissions: users-modify
Name: "{app}\shared"; Permissions: users-modify
Name: "{app}\shared\data"; Permissions: users-modify
Name: "{app}\shared\results"; Permissions: users-modify

[Icons]
; Start Menu Shortcut
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\Gỡ cài đặt {#MyAppName}"; Filename: "{uninstallexe}"
; Desktop Shortcut
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
; Option to launch application immediately after setup finishes
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
