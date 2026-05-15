# EventManagement — Deploy to costofliving-01 VM
# Copies app files to C:\Users\indal\deploy_em\ first (no spaces), then SCPs to VM

$SRC = "C:\Users\indal\OneDrive\My Documents\Spain\Tech\My Apps\EventManagement"
$STAGING = "C:\Users\indal\deploy_em"
$KEY = "C:\Users\indal\.ssh\google_compute_engine"
$VM = "indal@34.154.177.76"
$REMOTE = "/opt/eventmanagement"

# Files to deploy
$files = @(
    "app.py",
    "models.py",
    "config.py",
    "calendar_sync.py",
    "qr_generator.py",
    "email_sender.py",
    "requirements.txt"
)

$folders = @(
    "templates",
    "static"
)

Write-Host "=== Staging files ===" -ForegroundColor Cyan

# Clean and create staging directory
if (Test-Path $STAGING) { Remove-Item $STAGING -Recurse -Force }
New-Item -ItemType Directory -Path $STAGING -Force | Out-Null

# Copy individual files
foreach ($f in $files) {
    $src_path = Join-Path $SRC $f
    if (Test-Path $src_path) {
        Copy-Item $src_path $STAGING
        Write-Host "  $f"
    }
}

# Copy folders
foreach ($d in $folders) {
    $src_path = Join-Path $SRC $d
    if (Test-Path $src_path) {
        Copy-Item $src_path (Join-Path $STAGING $d) -Recurse
        Write-Host "  $d/"
    }
}

Write-Host ""
Write-Host "=== Uploading to VM ===" -ForegroundColor Cyan
scp -i $KEY -r "$STAGING\*" "${VM}:${REMOTE}/"

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Green
Write-Host "Next: SSH to VM and run 'sudo systemctl restart eventmanagement'"
