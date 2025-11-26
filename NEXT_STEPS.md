NEXT STEPS
1. Optionally copy hooks/ into .git/hooks (git won't trust them automatically):
   cp hooks/* .git/hooks/ && chmod +x .git/hooks/*

2. Set up an upstream remote (GitHub/GitLab/Bitbucket):
   git remote add origin git@github.com:${USERNAME}/${REPO}.git
   git push -u origin main

3. Use the scripts:
   ./scripts/create_diagram_entry.sh project-01-serverless-data-qc architecture
   ./scripts/atomic_commit.sh "feat(serverless): initial lambda handler"

4. Use atomic, small commits. Follow Conventional Commits.

5. Edit each project README with concrete details & add screenshots to diagrams/exported/.

