#!/bin/bash
# BMAD Branch Cleanup Script

echo "🧹 BMAD Branch Cleanup"
echo "====================="

# Update main branch
git checkout main
git pull origin main

echo "📋 Current branches:"
git branch -a --merged main | grep -v main | grep -v "remotes/origin/main"

echo ""
echo "🗑️ Cleaning up merged branches..."

# Delete local branches that are merged into main (except current branch)
git branch --merged main | grep -v "main\|^\*" | xargs -n 1 git branch -d 2>/dev/null || echo "No local merged branches to delete"

echo ""
echo "📊 Remaining active branches:"
git branch -a | grep -v "remotes/origin/HEAD"

echo ""
echo "✅ Cleanup complete!"