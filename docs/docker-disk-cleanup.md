# Docker Desktop: Platz freigeben (WSL2-VHDX kompaktieren)

> Windows-Host, Docker Desktop mit WSL2-Backend. `docker image rm` allein gibt auf `C:` oft
> nichts frei: geteilte Layer bleiben, der BuildKit-Cache wird nicht angefasst, und die
> WSL2-VHDX (`docker_data.vhdx`/`ext4.vhdx`) schrumpft nicht automatisch.

## 1. Im Docker-VM aufräumen (PowerShell)

```powershell
docker system df -v
docker builder prune -af          # BuildKit-Cache, meist der größte Brocken
docker image prune -a             # ungenutzte Images
docker container prune
docker volume prune
# Buildx gezielt:
docker buildx du
docker buildx prune -af --builder sbx-claude-v3   # je Builder
docker buildx rm sbx-claude                       # ungenutzte Alt-Builder inkl. Cache-Volume
```

## 2. VHDX-Dateien finden

```powershell
cmd /c "dir /s /b %LOCALAPPDATA%\Docker\*.vhdx"
Get-ChildItem "$env:LOCALAPPDATA\Docker" -Recurse -Filter *.vhdx |
  Select-Object FullName, @{n='GB';e={[math]::Round($_.Length/1GB,2)}}
```

Auf diesem Host gefunden (`C:\Users\dboec`):

| Datei | Inhalt |
|-------|--------|
| `...\Docker\wsl\disk\docker_data.vhdx` | **Images / Container / Volumes** (der große Brocken) |
| `...\Docker\wsl\main\ext4.vhdx` | Docker-Desktop-Systemdisk (kleiner) |
| `...\Docker\wsl.bak\disk\docker_data.vhdx` | Alt-Backup (Upgrade-Rest) |
| `...\Docker\wsl.bak\main\ext4.vhdx` | Alt-Backup (Upgrade-Rest) |

> `wsl.bak` ist ein Alt-Backup. Läuft Docker Desktop normal (nutzt `wsl\`), kannst du den Ordner
> `wsl.bak` löschen — gibt sofort Platz, unabhängig von der Kompaktierung.

Registry-Variante (falls die Pfade mal anders liegen):

```powershell
Get-ChildItem HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss | ForEach-Object {
  $p = Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue
  if ($p.BasePath -and $p.VhdFileName) {
    $vhd = Join-Path $p.BasePath $p.VhdFileName
    $gb  = if (Test-Path $vhd) { [math]::Round((Get-Item $vhd).Length/1GB,2) } else { 'n/a' }
    "{0,-16} {1}  [{2} GB]" -f $p.DistributionName, $vhd, $gb
  }
}
```

- Neuere Docker-Desktop-Versionen: `...\Docker\wsl\disk\docker_data.vhdx`
- Ältere (`docker-desktop-data`): `...\Docker\wsl\data\ext4.vhdx`

## 3. WSL stoppen

```powershell
wsl --shutdown
```

> Achtung: beendet auch die Agent-Sandbox (läuft in Docker Desktop/WSL2) — vorher offene Arbeit
> sichern. Docker Desktop muss ebenfalls vollständig beendet sein, sonst ist die VHDX gesperrt.

## 4. VHDX kompaktieren (diskpart, als Administrator)

Docker Desktop vollständig beenden, `wsl --shutdown`, dann den **Daten-Disk** (Images/Container/Volumes) kompaktieren:

```text
diskpart
DISKPART> select vdisk file="C:\Users\dboec\AppData\Local\Docker\wsl\disk\docker_data.vhdx"
DISKPART> attach vdisk readonly
DISKPART> compact vdisk
DISKPART> detach vdisk
DISKPART> exit
```

`compact vdisk` dauert je nach Größe einige Minuten.

Optional auch die Systemdisk (`...\Docker\wsl\main\ext4.vhdx`) — gleiche Sequenz mit dem jeweiligen Pfad.

## 5. Prüfen / Docker starten

```powershell
(Get-Item "<vhd-pfad>").Length / 1GB
```

Danach Docker Desktop wieder starten.

## Alternativen

- `Optimize-VHD -Path "<vhd>" -Mode Full` — nur mit aktivem Hyper-V-Feature; VHDX darf vorher nicht attached sein.
- Docker Desktop → Troubleshoot → „Clean / Purge data" (destruktiv: löscht Images/Container/Volumes).
