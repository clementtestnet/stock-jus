; stock_jus_setup.iss — Inno Setup Script pour Stock Jus
; Génère un setup.exe installateur professionnel Windows
; Télécharger Inno Setup : https://jrsoftware.org/isinfo.php

#define AppName      "Stock Jus"
#define AppVersion   "5.0"
#define AppPublisher "Votre Boutique"
#define AppURL       ""
#define AppExeName   "StockJus.exe"
#define AppId        "{A4B8C2D1-1234-5678-ABCD-EF0123456789}"

[Setup]
AppId={{#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
; Icône de l'installateur
SetupIconFile=assets\icon.ico
; Compression maximale
Compression=lzma2/ultra64
SolidCompression=yes
; Apparence moderne
WizardStyle=modern
WizardResizable=no
; Nécessite Windows 10 minimum
MinVersion=10.0
; Fichier de sortie
OutputDir=dist
OutputBaseFilename=StockJus_Setup_v{#AppVersion}
; Privilèges (installation par utilisateur, pas besoin d'admin)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; Splash / bannière
; WizardImageFile=assets\banner.bmp  ; décommentez si vous avez une bannière 164x314
; WizardSmallImageFile=assets\logo.bmp

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";    Description: "Créer un raccourci sur le Bureau";    GroupDescription: "Raccourcis :"; Flags: unchecked
Name: "quicklaunchicon"; Description: "Raccourci dans la barre des tâches"; GroupDescription: "Raccourcis :"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Application compilée
Source: "dist\StockJus\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Base de données initiale (si présente)
Source: "stock_jus.db"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist; Check: FileExists(ExpandConstant('{src}\stock_jus.db'))

[Icons]
; Menu Démarrer
Name: "{group}\{#AppName}";        Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"
Name: "{group}\Désinstaller {#AppName}"; Filename: "{uninstallexe}"
; Bureau
Name: "{autodesktop}\{#AppName}";  Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"; Tasks: desktopicon
; Barre de lancement rapide
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Lancer {#AppName} maintenant"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Supprimer la base de données lors de la désinstallation
; Décommentez si vous voulez supprimer les données :
; Type: files; Name: "{app}\stock_jus.db"

[Code]
// Vérification Windows 10+
function InitializeSetup(): Boolean;
begin
  Result := True;
  if not IsWin64 then begin
    MsgBox('Stock Jus nécessite Windows 10 (64-bit) ou supérieur.', mbError, MB_OK);
    Result := False;
  end;
end;
