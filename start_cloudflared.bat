@echo off
pushd "\\mac\Dropbox-1\AAA Backup\A Working\BloombergGPT"
cloudflared.exe tunnel --config "C:\Users\macbook2024\Documents\cloudflared-broker.yml" run bloomberg-broker
popd
