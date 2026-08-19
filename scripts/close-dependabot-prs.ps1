# Close obsolete Dependabot PRs after manual upgrades on main.
# Requires: gh auth login (once)
$ErrorActionPreference = "Stop"
$gh = if (Get-Command gh -ErrorAction SilentlyContinue) { "gh" } else { "C:\Program Files\GitHub CLI\gh.exe" }

& $gh auth status | Out-Null

$closes = @(
  @{
    Number  = 1
    Comment = "Superseded on main: python-multipart is already 0.0.32 (commit 62c55d6)."
  }
  @{
    Number  = 3
    Comment = "Superseded on main: pytest upgraded to 9.1.1 (commit 44250fe)."
  }
  @{
    Number  = 5
    Comment = "Deferred: Python 3.14 is a major runtime bump; staying on 3.12-slim until tested."
  }
  @{
    Number  = 6
    Comment = "Applied manually on main in commit 44250fe (pytest 9.1.1)."
  }
  @{
    Number  = 8
    Comment = "Superseded on main: fastapi is 0.141.1 with starlette 1.6.0 (commit 62c55d6)."
  }
  @{
    Number  = 9
    Comment = "Applied manually on main in commit 44250fe (pyotp 2.10.0)."
  }
  @{
    Number  = 11
    Comment = "Superseded on main: python-multipart is already 0.0.32 (commit 62c55d6)."
  }
  @{
    Number  = 12
    Comment = "Superseded on main: cryptography is 50.0.0 (commit 62c55d6)."
  }
  @{
    Number  = 16
    Comment = "Deferred: TypeScript 7 is a major upgrade; staying on 5.x until a planned frontend bump."
  }
  @{
    Number  = 21
    Comment = "Deferred: Node 25 is a major runtime bump; staying on node:20-alpine until tested."
  }
  @{
    Number  = 23
    Comment = "Deferred: Next.js 16 is a major upgrade; staying on Next 15 until a planned frontend bump."
  }
  @{
    Number  = 24
    Comment = "Deferred: @types/node 26 matches a major Node bump; staying on current 22.x types."
  }
)

foreach ($item in $closes) {
  Write-Host "Closing PR #$($item.Number)..."
  & $gh pr close $item.Number --repo lastphoenx/projektmanagement --comment $item.Comment
}

Write-Host "Done. Open PRs:"
& $gh pr list --repo lastphoenx/projektmanagement --state open
