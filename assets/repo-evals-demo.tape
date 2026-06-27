Output assets/repo-evals-demo.gif
Set Shell "bash"
Set FontSize 22
Set Width 1200
Set Height 720

Type "npx skills add zinan92/repo-evals -g"
Enter
Sleep 1

Type "Evaluate https://github.com/owner/repo against its README promises. Write the result in Chinese."
Enter
Sleep 1

Type "scripts/new-repo-eval.sh owner/repo skill"
Enter
Sleep 1

Type "python3 scripts/render_verdict_html.py owner--repo --lang zh"
Enter
Sleep 1

Type "open repos/owner--repo/verdicts/<date>-verdict.html"
Enter
