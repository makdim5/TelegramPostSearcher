Set wdApp = CreateObject("Word.Application")

wdApp.Visible = True

Set fso = CreateObject("Scripting.FileSystemObject")
scriptPath = fso.GetParentFolderName(WScript.ScriptFullName)
docPath = scriptPath & "\Instruction.docx"

wdApp.Documents.Open docPath


