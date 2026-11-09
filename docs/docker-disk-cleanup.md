# Docker Desktop: Platz freigeben (WSL2-VHDX kompaktieren)

> Windows-Host, Docker Desktop mit WSL2-Backend. `docker image rm` allein gibt auf `C:` oft
> nichts frei: geteilte Layer bleiben, der BuildKit-Cache wird nicht angefasst, und die
> WSL2-VHDX (`docker_data.vhdx`/`ext4.vhdx`) schrumpft nicht automatisch.

## 1. Im Docker-VM aufräumen (PowerShell)

Für die Kit-Images gibt es ein fertiges Script, das die Alt-Builder entfernt und den Cache
**je aktivem Builder** prunt:

Nur anzeigen, was passieren würde (Dry-Run):

```powershell
.\local-test\docker-buildx-cleanup.cmd --dry-run
```

Ausführen:

```powershell
.\local-test\docker-buildx-cleanup.cmd
```

Alternativ direkt mit Python (läuft im aktuellen Fenster):

```powershell
python .\local-test\docker-buildx-cleanup.py
```

Es entfernt `sbx-opencode`/`sbx-claude` (pre-v3, inkl. Cache-Volume) und prunt
`sbx-opencode-v3`, `sbx-claude-v3`, `sbx-mammouth`, `sbx-pi`, `sbx-vibe`. Die Ausgabe wird
zusätzlich nach `target/docker-buildx-cleanup.log` geschrieben. Auf diesem Host freigegeben:
**~64,6 GB Build-Cache** (`sbx-pi` 30,66 GB, `sbx-vibe` 33,97 GB).

> Manueller Weg (ohne Script): siehe [Manueller Weg (Alternative)](#manueller-weg-alternative) am Ende.

## 2. VHDX-Dateien finden

Per `cmd`:

```powershell
cmd /c "dir /s /b %LOCALAPPDATA%\Docker\*.vhdx"
```

Oder per PowerShell (inkl. Größe):

```powershell
Get-ChildItem "$env:LOCALAPPDATA\Docker" -Recurse -Filter *.vhdx |
  Select-Object FullName, @{n='GB';e={[math]::Round($_.Length/1GB,2)}}
```

Auf diesem Host gefunden (`C:\Users\dboec`):

| Datei | Inhalt |
|-------|--------|
| `...\Docker\wsl\disk\docker_data.vhdx` | **Images / Container / Volumes** (der große Brocken) |
| `...\Docker\wsl\main\ext4.vhdx` | Docker-Desktop-Systemdisk (kleiner) |

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

## Manueller Weg (Alternative)

Verbrauch und freigegebenen Platz anzeigen:

```powershell
docker system df -v
```

Gestoppte Container entfernen:

```powershell
docker container prune
```

Ungenutzte Volumes entfernen:

```powershell
docker volume prune
```

BuildKit-Cache je Builder messen (ohne `--builder` = aktueller Builder):

```powershell
docker buildx du
```

Cache eines einzelnen Builders leeren:

```powershell
docker buildx prune --builder sbx-claude-v3 -af
```

Ungenutzten Alt-Builder `sbx-opencode` inkl. Cache-Volume entfernen (pre-v3):

```powershell
docker buildx rm sbx-opencode
```

Ungenutzten Alt-Builder `sbx-claude` inkl. Cache-Volume entfernen (pre-v3):

```powershell
docker buildx rm sbx-claude
```

> **Wichtig:** `docker buildx prune -af` ohne `--builder` prunt nur den **aktuellen** Builder,
> `docker builder prune -af` nur den `default`-Builder. Jedes Kit baut mit eigenem Builder
> (`BUILDER` in `local-test/build-and-publish-*-image.py`), daher alle aktiven prunen:
>
> ```powershell
> "sbx-opencode-v3","sbx-claude-v3","sbx-mammouth","sbx-pi","sbx-vibe" |
>   ForEach-Object { docker buildx prune --builder $_ -af }
> ```
>
> `buildx prune` löscht nur Cache/Layer — **keine** Images und **keine** Builder. `buildx rm`
> entfernt Builder + Cache-Volume, die gebauten Images (z. B. `:local`) bleiben erhalten.

Alte Timestamp-Tags der Kit-Images (nur Images **ohne** `:local` geben dabei Platz frei; ein
zusätzlicher Tag auf einem `:local`-Image wird nur entfernt).

Alte Timestamp-Tags auflisten:

```powershell
docker images --format "{{.Repository}}:{{.Tag}}" | Select-String 'sbx-.*\.\d{14}$'
```

Dann gezielt entfernen (`<repo>`/`<tag>` ersetzen):

```powershell
docker rmi <repo>:<tag>
```
