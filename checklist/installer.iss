[Setup]
AppName=Wedding Checklist
AppVerName=Wedding Checklist 0.1
AppVersion=0.1
AppPublisher=Daniel Woodhouse
AppPublisherUrl=http://github.com/woodenbrick
DefaultDirName={pf}\WeddingChecklist

[Files]
Source: "dist\*"; DestDir: {app}; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{commonprograms}\WeddingChecklist"; Filename: "{app}\weddingchecklist.exe"
Name: "{commondesktop}\WeddingChecklist"; Filename: "{app}\weddingchecklist.exe"
