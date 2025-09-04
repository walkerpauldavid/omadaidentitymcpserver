<# 
Export AD user→group memberships to CSV
- Run on a DC (or anywhere with RSAT + AD module).
- Outputs rows: user,samAccountName,userPrincipalName,displayName,group,group_dn
- Expands nested groups.
- Excludes disabled users and Builtin groups by default.

USAGE (default path):
  .\Export-AdUserGroupMemberships.ps1

Optionally set a target OU for groups or change output:
  .\Export-AdUserGroupMemberships.ps1 -OutFile "C:\Temp\ad_memberships.csv" -GroupSearchBase "OU=Groups,DC=example,DC=com"

Include disabled users or Builtin groups if you want:
  .\Export-AdUserGroupMemberships.ps1 -IncludeDisabledUsers -IncludeBuiltin
#>

param(
  [string]$OutFile = "C:\Temp\ad_memberships.csv",
  # Optional: limit which groups to scan (Distinguished Name of an OU/Container)
  [string]$GroupSearchBase = "DC=corporate,DC=com",
  [switch]$IncludeDisabledUsers = $true,
  [switch]$IncludeBuiltin = $true
)

# Ensure the AD module is available
Import-Module ActiveDirectory -ErrorAction Stop

# Create output folder if needed
$null = New-Item -ItemType Directory -Path (Split-Path $OutFile) -Force -ErrorAction SilentlyContinue

# 1) Get security groups (optionally scoped to an OU/Container)
$groupFilter = '*'
$groupProps  = 'DistinguishedName','SamAccountName','Name'
$searchScope = 'Subtree'  # one of: Base, OneLevel, Subtree

if ([string]::IsNullOrWhiteSpace($GroupSearchBase)) {
  $groups = Get-ADGroup -Filter $groupFilter -SearchScope $searchScope -Properties $groupProps -ResultSetSize $null
} else {
  $groups = Get-ADGroup -Filter $groupFilter -SearchScope $searchScope -SearchBase $GroupSearchBase -Properties $groupProps -ResultSetSize $null
}

# Exclude Builtin container unless asked not to
if (-not $IncludeBuiltin) {
  $groups = $groups | Where-Object { $_.DistinguishedName -notmatch '^CN=Builtin,' }
}

# 2) Walk each group; expand members recursively; keep only users
$rows = foreach ($g in $groups) {
  try {
    Get-ADGroupMember -Identity $g.DistinguishedName -Recursive -ErrorAction Stop |
      Where-Object { $_.ObjectClass -eq 'user' } |
      ForEach-Object {
        # Re-resolve as AD user to fetch Enabled/UPN reliably
        $u = $null
        try {
          $u = Get-ADUser -Identity $_.DistinguishedName -Properties Enabled,UserPrincipalName,SamAccountName,DisplayName
        } catch {}

        if ($u -and ($IncludeDisabledUsers -or $u.Enabled)) {
          [pscustomobject]@{
            user                = $u.SamAccountName
            user_upn            = $u.UserPrincipalName
            user_display_name   = $u.DisplayName
            group               = $g.SamAccountName
            group_dn            = $g.DistinguishedName
          }
        }
      }
  } catch {
    Write-Warning "Failed to enumerate $($g.SamAccountName): $($_.Exception.Message)"
  }
}

# 3) Export CSV (deduped & sorted)
$rows `
| Sort-Object user, group `
| Select-Object user, user_upn, user_display_name, group, group_dn `
| Get-Unique `
| Export-Csv -Path $OutFile -NoTypeInformation -Encoding UTF8

Write-Host "Wrote $((Get-Item $OutFile).Length) bytes to $OutFile"
Write-Host "Rows: $($rows.Count)  File: $OutFile"
