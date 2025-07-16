#define MyAppName "SuperAppStore"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "ASLant"
#define MyAppURL "https://aslant.top"
#define MyAppExeName "SuperAppStore.exe"

[Setup]
; ע: AppId��ֵΪ������ʶ��Ӧ�ó���
; ��ҪΪ������װ����ʹ����ͬ��AppIdֵ��
AppId={{36E4AA33-3464-48E9-A418-CDAE5D3CA041}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={commonpf64}\SuperAppStore
DisableProgramGroupPage=yes
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=commandline dialog
OutputDir=dist
OutputBaseFilename={#MyAppName}_V{#MyAppVersion}
SetupIconFile=App.ico

; ����ʱ�Զ�ж�ؾɰ汾
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
AppMutex=SuperAppStoreMutex
CloseApplications=yes
RestartApplications=no
CreateAppDir=yes

; �Ż�ѹ������
Compression=lzma2/ultra64
SolidCompression=yes
InternalCompressLevel=max
WizardStyle=modern

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\main.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent runascurrentuser

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  UninstallExe: String;
  ResultCode: Integer;
begin
  if CurStep = ssInstall then
  begin
    if RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{36E4AA33-3464-48E9-A418-CDAE5D3CA041}_is1', 'UninstallString', UninstallExe) then
    begin
      UninstallExe := RemoveQuotes(UninstallExe);
      if UninstallExe <> '' then
      begin
        Exec(UninstallExe, '/SILENT /NORESTART', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
      end;
    end;
  end;
end;

