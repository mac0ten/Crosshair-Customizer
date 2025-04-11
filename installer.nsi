
; CrosshairTool Installer Script
!include "MUI2.nsh"

; Basic definitions
Name "Crosshair Tool"
OutFile "dist\CrosshairTool-Installer-v1.0.0-1744401063.exe"
InstallDir "$PROGRAMFILES64\CrosshairTool"
InstallDirRegKey HKCU "Software\CrosshairTool" ""

; Request application privileges
RequestExecutionLevel admin

; Interface settings
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "English"

; Installation section
Section "Install"
    SetOutPath "$INSTDIR"
    
    ; Add files/directories
    File /r "dist\CrosshairTool\*.*"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
    
    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\Crosshair Tool"
    CreateShortcut "$SMPROGRAMS\Crosshair Tool\Crosshair Tool.lnk" "$INSTDIR\CrosshairTool.exe"
    CreateShortcut "$SMPROGRAMS\Crosshair Tool\Uninstall.lnk" "$INSTDIR\uninstall.exe"
    CreateShortcut "$DESKTOP\Crosshair Tool.lnk" "$INSTDIR\CrosshairTool.exe"
    
    ; Write registry keys for uninstall
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CrosshairTool" \
                     "DisplayName" "Crosshair Tool"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CrosshairTool" \
                     "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CrosshairTool" \
                     "DisplayIcon" "$INSTDIR\CrosshairTool.exe,0"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CrosshairTool" \
                     "Publisher" "Your Organization"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CrosshairTool" \
                     "DisplayVersion" "1.0.0"
SectionEnd

; Uninstallation section
Section "Uninstall"
    ; Remove files and uninstaller
    RMDir /r "$INSTDIR"
    
    ; Remove shortcuts
    Delete "$DESKTOP\Crosshair Tool.lnk"
    RMDir /r "$SMPROGRAMS\Crosshair Tool"
    
    ; Remove registry keys
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CrosshairTool"
SectionEnd
