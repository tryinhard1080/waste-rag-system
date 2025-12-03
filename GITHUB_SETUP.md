# GitHub Repository Setup Guide

Complete guide to create and push your Waste RAG System to GitHub.

## Quick Options

### Option 1: Install GitHub CLI (Fastest)

**Windows (recommended):**
```powershell
# Using winget
winget install --id GitHub.cli

# Or using Chocolatey
choco install gh

# Or download from: https://cli.github.com/
```

**After installation:**
```bash
# Authenticate with GitHub
gh auth login

# Navigate to project
cd C:\Users\richard.bates\Documents\waste-rag-system

# Create repository and push (all in one)
gh repo create waste-rag-system --private --source=. --remote=origin --push --description "Production-ready RAG system for waste management using Google Gemini File API"
```

### Option 2: Manual Setup (Web + Git)

**Step 1: Create Repository on GitHub**

1. Go to: https://github.com/new
2. Fill in details:
   - **Repository name**: `waste-rag-system`
   - **Description**: `Production-ready RAG system for waste management using Google Gemini File API`
   - **Visibility**: 🔒 Private (recommended) or 🌐 Public
   - **⚠️ Important**: Do NOT check "Add README", "Add .gitignore", or "Choose a license"
3. Click **"Create repository"**

**Step 2: Copy Repository URL**

After creation, copy the URL shown (looks like):
```
https://github.com/YOUR_USERNAME/waste-rag-system.git
```

**Step 3: Run Setup Script**

**Windows PowerShell:**
```powershell
cd C:\Users\richard.bates\Documents\waste-rag-system
.\setup_github.ps1
```

**Or Git Bash:**
```bash
cd /c/Users/richard.bates/Documents/waste-rag-system
bash setup_github.sh
```

### Option 3: Manual Git Commands

**For Windows PowerShell or Git Bash:**

```bash
# Navigate to project
cd C:\Users\richard.bates\Documents\waste-rag-system

# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/waste-rag-system.git

# Verify remote
git remote -v

# Push to GitHub
git push -u origin master
```

If you get authentication errors:
```bash
# Configure credential storage
git config --global credential.helper store

# Try push again
git push -u origin master
```

## Detailed Manual Setup

### Prerequisites

1. **Git installed** - Already have it ✓
2. **GitHub account** - Create at https://github.com/join if needed
3. **Git configured** with your details:

```bash
# Check current configuration
git config --global user.name
git config --global user.email

# Set if needed
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Step-by-Step Process

#### 1. Create Repository on GitHub

**Via Web Interface:**
- URL: https://github.com/new
- Repository name: `waste-rag-system`
- Description: `Production-ready RAG system for waste management using Google Gemini File API`
- Visibility: Private (recommended for business use)
- **DO NOT** initialize with README or any files

**Via GitHub CLI (if installed):**
```bash
gh repo create waste-rag-system --private --description "Production-ready RAG system for waste management using Google Gemini File API"
```

#### 2. Link Local Repository to GitHub

```bash
# Navigate to project
cd C:\Users\richard.bates\Documents\waste-rag-system

# Add GitHub as remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/waste-rag-system.git

# Verify
git remote -v
# Should show:
# origin  https://github.com/YOUR_USERNAME/waste-rag-system.git (fetch)
# origin  https://github.com/YOUR_USERNAME/waste-rag-system.git (push)
```

#### 3. Check Local Repository Status

```bash
# Check current branch
git branch
# Should show: * master

# Check commits
git log --oneline
# Should show your 2 commits:
# 64126bd docs: Add comprehensive documentation and CI/CD workflows
# 50b1f6f Initial commit: Waste RAG System with Gemini File API

# Check status
git status
# Should show: nothing to commit, working tree clean
```

#### 4. Push to GitHub

```bash
# Push master branch to GitHub
git push -u origin master
```

**If this is your first time:**
- You may be prompted for GitHub credentials
- Use your GitHub username
- Use a **Personal Access Token** as password (not your GitHub password)

**To create a Personal Access Token:**
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Give it a name: "waste-rag-system"
4. Select scopes: ✓ repo
5. Click "Generate token"
6. Copy the token and use it as your password

#### 5. Verify Push

```bash
# Check remote status
git remote show origin

# Visit your repository
# URL: https://github.com/YOUR_USERNAME/waste-rag-system
```

### Troubleshooting

#### Error: "remote origin already exists"

```bash
# Remove existing remote
git remote remove origin

# Add correct remote
git remote add origin https://github.com/YOUR_USERNAME/waste-rag-system.git
```

#### Error: "authentication failed"

**Option 1: Use Personal Access Token**
1. Create token at: https://github.com/settings/tokens
2. Use token as password when pushing

**Option 2: Configure credential helper**
```bash
# Windows
git config --global credential.helper wincred

# All platforms
git config --global credential.helper store
```

**Option 3: Use SSH instead**
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your.email@example.com"

# Add key to GitHub: https://github.com/settings/keys

# Use SSH URL
git remote set-url origin git@github.com:YOUR_USERNAME/waste-rag-system.git
```

#### Error: "Updates were rejected"

```bash
# Force push (use with caution - only on initial push to empty repo)
git push -u origin master --force
```

#### Error: "Permission denied"

- Verify you created the repository under your account
- Check repository name matches exactly
- Ensure you have write access to the repository

### Post-Push Checklist

After successful push, verify on GitHub:

✅ **Files visible**:
- [ ] README.md displays on repository home
- [ ] All 27+ files are present
- [ ] .github/workflows directory exists

✅ **Documentation**:
- [ ] README renders correctly
- [ ] Badges display properly
- [ ] Links work

✅ **GitHub Actions**:
- [ ] Workflows appear in "Actions" tab
- [ ] No errors in workflow files

✅ **Settings**:
- [ ] Repository is Private (if intended)
- [ ] Description is set
- [ ] Topics added (optional): `rag`, `gemini`, `waste-management`, `python`

### Configure Repository Settings (Optional)

**Add Topics:**
1. Go to repository homepage
2. Click "⚙️" next to "About"
3. Add topics: `rag`, `gemini-api`, `waste-management`, `python`, `document-processing`

**Enable GitHub Actions:**
- Go to "Settings" → "Actions" → "General"
- Ensure "Allow all actions" is selected

**Add Collaborators:**
- Go to "Settings" → "Collaborators"
- Click "Add people"
- Enter GitHub usernames

**Branch Protection (recommended):**
- Go to "Settings" → "Branches"
- Add rule for `master` branch
- Enable: "Require pull request reviews before merging"

## Next Steps After GitHub Setup

1. **Share repository URL** with your team
2. **Clone on other machines**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/waste-rag-system.git
   ```

3. **Set up continuous deployment** (optional)
4. **Add GitHub badges** to README (optional)
5. **Create first issue** or project board

## Useful Git Commands

```bash
# Check status
git status

# View commit history
git log --oneline --graph --all

# View remote details
git remote -v

# Pull latest changes
git pull origin master

# Create new branch
git checkout -b feature-name

# Switch branches
git checkout master

# View differences
git diff
```

## Getting Help

- **Git Documentation**: https://git-scm.com/doc
- **GitHub Guides**: https://guides.github.com/
- **GitHub CLI**: https://cli.github.com/manual/
- **This Project's Issues**: (after creating repo) https://github.com/YOUR_USERNAME/waste-rag-system/issues

---

**Ready to push to GitHub!** 🚀

Choose your preferred method above and follow the steps. The repository is ready and waiting!
