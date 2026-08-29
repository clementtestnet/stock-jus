; stock_jus_setup.iss — Script Inno Setup
; Crée un installateur Windows professionnel (Setup.exe)
; Télécharger Inno Setup sur : https://jrsoftware.org/isdl.php

[Setup]
AppName=Stock Jus
AppVersion=5.0
AppPublisher=LE ROCHER
AppPublisherURL=
AppSupportURL=
AppUpdatesURL=
DefaultDirName={autopf}\StockJus
DefaultGroupName=Stock Jus
AllowNoIcons=yes
OutputDir=installer
OutputBaseFilename=StockJus_Setup_v5
SetupIconFile=assets\icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\StockJus.exe
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer une icône sur le Bureau"; \
    GroupDescription: "Icônes supplémentaires :"; Flags: unchecked

[Files]
; Copier tout le dossier compilé par PyInstaller
Source: "dist\StockJus\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Menu Démarrer
Name: "{group}\Stock Jus";       Filename: "{app}\StockJus.exe"
Name: "{group}\Désinstaller";    Filename: "{uninstallexe}"
; Bureau (optionnel)
Name: "{autodesktop}\Stock Jus"; Filename: "{app}\StockJus.exe"; \
    Tasks: desktopicon

[Run]
Filename: "{app}\StockJus.exe"; \
    Description: "Lancer Stock Jus maintenant"; \
    Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Supprimer la base de données à la désinstallation (optionnel)
; Type: files; Name: "{app}\stock_jus.db"
