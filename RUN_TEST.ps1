# PowerShell doesn't have UNC path issues
Write-Host "================================================================================`n"
Write-Host "Bloomberg Account Capability Test`n"
Write-Host "================================================================================`n"
Write-Host "Running test...`n"

Set-Location "\\Mac\Dropbox-1\AAA Backup\A Working\BloombergGPT"

python test_account_capabilities.py | Tee-Object -FilePath test_output.txt

Write-Host "`n================================================================================`n"
Write-Host "Test complete! Results saved to test_output.txt`n"
Write-Host "================================================================================`n"

Read-Host "Press Enter to exit"

