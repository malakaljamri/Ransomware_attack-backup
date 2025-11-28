PS C:\Users\Administrator> $lastSession = Get-VBRBackupSession | >> Where-Object { $_.JobName -eq $job.Name } | >> Sort-Object EndTime -Descending | >> Select-Object -First 1 PS C:\Users\Administrator> PS C:\Users\Administrator> # Build JSON output PS C:\Users\Administrator> $jobInfo = [PSCustomObject]@{ >> Name = $job.Name >> JobType = $job.JobType >> Description = $job.Description >> >> # Session data >> State = $lastSession.State >> LastResult = $lastSession.Result >> StartTime = $lastSession.CreationTime >> EndTime = $lastSession.EndTime >> } PS C:\Users\Administrator> PS C:\Users\Administrator> # Output JSON PS C:\Users\Administrator> $jobInfo | ConvertTo-Json -Depth 5 { "Name": "Backup-Job-\u003e", "JobType": 0, "Description": "Created by FILESRV\\Administrator at 11/12/2025 11:56 AM.", "State": -1, "LastResult": 0, "StartTime": "\/Date(1763146812067)\/", "EndTime": "\/Date(1763147131636)\/" } PS C:\Users\Administrator>




"JobType": 0, "Description": "Created by FILESRV\\Administrator at 11/12/2025 11:56 AM.", "State": -1, "LastResult": 0, "StartTime": "\/Date(1763146812067)\/", "EndTime": "\/Date(1763147131636)\/" } PS C:\Users\Administrator>

"JobType": "Backup", "Description": "Created by FILESRV\\Administrator at 11/12/2025 11:56 AM.", "State": "Stopped", "LastResult": "Success", "StartTime": "2025-11-14 22:00:12", "EndTime": "2025-11-14 22:05:31" } PS C:\Users\Administrator>

