source venv/bin/activate

pip install flask


//why i have the backup job null response =
//because $job.Info does NOT contain session data for Veeam backup jobs.
That’s expected: Veeam job objects don’t store state/results directly — only sessions do.