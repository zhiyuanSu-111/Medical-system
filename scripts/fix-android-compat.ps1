$root = Split-Path -Parent $PSScriptRoot

$buildGradle = Join-Path $root "android\build.gradle"
$wrapperProps = Join-Path $root "android\gradle\wrapper\gradle-wrapper.properties"
$variablesGradle = Join-Path $root "android\variables.gradle"

if (!(Test-Path $buildGradle) -or !(Test-Path $wrapperProps) -or !(Test-Path $variablesGradle)) {
  throw "未找到 Android 工程关键文件，请确认在项目根目录执行。"
}

$buildText = Get-Content -Path $buildGradle -Raw
$buildText = [regex]::Replace($buildText, "classpath\s+'com\.android\.tools\.build:gradle:[^']+'", "classpath 'com.android.tools.build:gradle:8.8.0'")
Set-Content -Path $buildGradle -Value $buildText -Encoding UTF8

$wrapperText = Get-Content -Path $wrapperProps -Raw
$wrapperText = [regex]::Replace($wrapperText, "distributionUrl=.*", "distributionUrl=https\://services.gradle.org/distributions/gradle-8.10.2-all.zip")
Set-Content -Path $wrapperProps -Value $wrapperText -Encoding UTF8

$varText = Get-Content -Path $variablesGradle -Raw
$varText = [regex]::Replace($varText, "compileSdkVersion\s*=\s*\d+", "compileSdkVersion = 35")
$varText = [regex]::Replace($varText, "targetSdkVersion\s*=\s*\d+", "targetSdkVersion = 35")
$varText = [regex]::Replace($varText, "androidxCoreVersion\s*=\s*'[^']+'", "androidxCoreVersion = '1.16.0'")
Set-Content -Path $variablesGradle -Value $varText -Encoding UTF8

Write-Host "已修正 Android 兼容版本："
Write-Host "- AGP 8.8.0"
Write-Host "- Gradle 8.10.2"
Write-Host "- compile/targetSdk 35"
Write-Host "- androidx.core 1.16.0"
Write-Host "下一步建议：npm run mobile:build"
