param(
  [Parameter(Mandatory = $true)]
  [ValidateSet("emulator", "device")]
  [string]$Target,

  [string]$DeviceIp = ""
)

$root = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $root ".env.mobile"

if (!(Test-Path $envFile)) {
  New-Item -Path $envFile -ItemType File -Force | Out-Null
}

if ($Target -eq "emulator") {
  $apiBase = "http://10.0.2.2:5000"
} else {
  if ([string]::IsNullOrWhiteSpace($DeviceIp)) {
    throw "Target=device 时必须传 -DeviceIp，例如: -DeviceIp 10.18.112.252"
  }
  $apiBase = "http://$DeviceIp`:5000"
}

$line = "VITE_API_BASE_URL=$apiBase"
Set-Content -Path $envFile -Value $line -Encoding UTF8

Write-Host "已切换移动端目标: $Target"
Write-Host ".env.mobile -> $line"
Write-Host "下一步请执行: npm run mobile:build"
