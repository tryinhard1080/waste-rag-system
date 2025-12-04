# Accessing Email Data from Multiple Apps

Once your email data is in GitHub, you can access it from any application. Here's how:

---

## 🔑 Setup: GitHub Personal Access Token

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name: `email-warehouse-data-access`
4. Scopes: Select `repo` (Full control of private repositories)
5. Click "Generate token"
6. **Copy the token** - you won't see it again!

---

## 📱 Method 1: Direct GitHub API Access (Recommended for Apps)

### Python (for WasteWise, etc.)

```python
import requests
import json
import base64
from datetime import datetime

class EmailDataAccess:
    def __init__(self, github_token):
        self.token = github_token
        self.repo = "tryinhard1080/email-warehouse-data"
        self.base_url = f"https://api.github.com/repos/{self.repo}/contents"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def get_daily_emails(self, date=None):
        """Get emails for a specific date"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        url = f"{self.base_url}/daily/{date}.json"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            # Decode base64 content
            content = base64.b64decode(response.json()['content']).decode('utf-8')
            return json.loads(content)
        else:
            return None

    def get_gemini_batch(self, batch_name):
        """Get Gemini markdown batch"""
        url = f"{self.base_url}/gemini/{batch_name}.md"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            content = base64.b64decode(response.json()['content']).decode('utf-8')
            return content
        else:
            return None

    def list_all_dates(self):
        """List all available date files"""
        url = f"{self.base_url}/daily"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            files = response.json()
            return [f['name'].replace('.json', '') for f in files if f['name'].endswith('.json')]
        else:
            return []

# Usage Example
if __name__ == "__main__":
    # Set your token
    GITHUB_TOKEN = "ghp_your_token_here"

    # Initialize
    data = EmailDataAccess(GITHUB_TOKEN)

    # Get today's emails
    emails = data.get_daily_emails()
    print(f"Found {len(emails['emails'])} emails")

    # Get specific date
    emails_nov = data.get_daily_emails("2025-11-15")

    # List all available dates
    dates = data.list_all_dates()
    print(f"Available dates: {dates}")
```

### JavaScript/Node.js (for bolt.new)

```javascript
class EmailDataAccess {
    constructor(githubToken) {
        this.token = githubToken;
        this.repo = 'tryinhard1080/email-warehouse-data';
        this.baseUrl = `https://api.github.com/repos/${this.repo}/contents`;
    }

    async getDailyEmails(date = null) {
        if (!date) {
            date = new Date().toISOString().split('T')[0];
        }

        const url = `${this.baseUrl}/daily/${date}.json`;
        const response = await fetch(url, {
            headers: {
                'Authorization': `token ${this.token}`,
                'Accept': 'application/vnd.github.v3+json'
            }
        });

        if (response.ok) {
            const data = await response.json();
            const content = atob(data.content);
            return JSON.parse(content);
        }
        return null;
    }

    async listAllDates() {
        const url = `${this.baseUrl}/daily`;
        const response = await fetch(url, {
            headers: {
                'Authorization': `token ${this.token}`,
                'Accept': 'application/vnd.github.v3+json'
            }
        });

        if (response.ok) {
            const files = await response.json();
            return files
                .filter(f => f.name.endsWith('.json'))
                .map(f => f.name.replace('.json', ''));
        }
        return [];
    }
}

// Usage in bolt.new
const GITHUB_TOKEN = import.meta.env.VITE_GITHUB_TOKEN;
const emailData = new EmailDataAccess(GITHUB_TOKEN);

// Get emails
const emails = await emailData.getDailyEmails('2025-12-03');
console.log(`Found ${emails.emails.length} emails`);
```

---

## 📦 Method 2: Git Clone (Best for Local Apps)

### One-time Setup

```bash
# Clone the data repository
cd ~/projects
git clone https://github.com/tryinhard1080/email-warehouse-data.git

# Configure credentials (so you don't need to enter password)
cd email-warehouse-data
git config credential.helper store
```

### Python App with Git Clone

```python
import json
import subprocess
from pathlib import Path
from datetime import datetime

class EmailDataLocal:
    def __init__(self, repo_path):
        self.repo_path = Path(repo_path)

    def sync(self):
        """Pull latest data from GitHub"""
        subprocess.run(['git', 'pull'], cwd=self.repo_path)

    def get_daily_emails(self, date=None):
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        file_path = self.repo_path / 'daily' / f'{date}.json'
        if file_path.exists():
            with open(file_path) as f:
                return json.load(f)
        return None

    def get_all_emails_since(self, start_date):
        """Get all emails since a specific date"""
        emails = []
        daily_dir = self.repo_path / 'daily'

        for file in daily_dir.glob('*.json'):
            date = file.stem
            if date >= start_date:
                with open(file) as f:
                    data = json.load(f)
                    emails.extend(data['emails'])

        return emails

# Usage
data = EmailDataLocal('~/projects/email-warehouse-data')
data.sync()  # Pull latest
emails = data.get_daily_emails()
```

---

## 🌐 Method 3: GitHub Raw Content (Simplest for Web Apps)

### Direct URL Access (No Auth for Public Files)

```javascript
// If repo is public, you can access raw content directly
const date = '2025-12-03';
const url = `https://raw.githubusercontent.com/tryinhard1080/email-warehouse-data/master/daily/${date}.json`;

const response = await fetch(url);
const emails = await response.json();
```

**Note:** This only works if the repo is public. For private repos, use Method 1.

---

## 🚀 Integration Examples

### Example 1: WasteWise Invoice Processing

```python
# In your WasteWise app
from email_data_access import EmailDataAccess

class InvoiceProcessor:
    def __init__(self):
        self.email_data = EmailDataAccess(GITHUB_TOKEN)

    def find_similar_invoices(self, vendor, property_name):
        # Get last 90 days of emails
        emails = []
        for i in range(90):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            daily = self.email_data.get_daily_emails(date)
            if daily:
                emails.extend(daily['emails'])

        # Filter for vendor and property
        similar = [e for e in emails
                  if vendor.lower() in e['subject'].lower()
                  and property_name.lower() in e['body_preview'].lower()]

        return similar
```

### Example 2: bolt.new Dashboard

```javascript
// In your bolt.new app
import { EmailDataAccess } from './emailData';

const App = () => {
    const [emails, setEmails] = useState([]);

    useEffect(() => {
        const loadEmails = async () => {
            const data = new EmailDataAccess(process.env.GITHUB_TOKEN);
            const today = await data.getDailyEmails();
            setEmails(today.emails);
        };
        loadEmails();
    }, []);

    return (
        <div>
            <h1>Emails: {emails.length}</h1>
            {emails.map(email => (
                <EmailCard key={email.id} email={email} />
            ))}
        </div>
    );
};
```

### Example 3: Scheduled Analysis Script

```python
# Runs daily to analyze emails
import schedule
from email_data_access import EmailDataAccess

def analyze_daily_emails():
    data = EmailDataAccess(GITHUB_TOKEN)
    emails = data.get_daily_emails()

    # Your analysis logic
    urgent = [e for e in emails['emails'] if e['importance'] == 'high']

    # Send notification
    send_slack_notification(f"Found {len(urgent)} urgent emails")

schedule.every().day.at("09:00").do(analyze_daily_emails)
```

---

## 🔒 Security Best Practices

1. **Never commit tokens to code**
   ```bash
   # Use environment variables
   export GITHUB_TOKEN=ghp_your_token_here

   # Or use .env file (add to .gitignore)
   echo "GITHUB_TOKEN=ghp_your_token_here" > .env
   ```

2. **Use token with minimal permissions**
   - Only grant `repo` access
   - Create separate tokens for different apps
   - Regularly rotate tokens

3. **Keep repo private**
   - Email data should be in a private repository
   - Never make it public

---

## 📊 Data Structure Reference

### Daily JSON Format
```json
{
  "export_date": "2025-12-03",
  "emails": [{
    "id": "...",
    "type": "received|sent",
    "from": {"name": "...", "email": "..."},
    "to": ["..."],
    "subject": "...",
    "body_preview": "...",
    "conversation_id": "...",
    "received_time": "2025-12-03T14:30:00",
    "importance": "normal|high|low"
  }]
}
```

---

## 🎯 Next Steps

1. Create private GitHub repo for data
2. Run initial sync: `.\Sync-DataToGitHub.ps1`
3. Set up automated daily sync in Task Scheduler
4. Install access library in your apps
5. Start querying data from anywhere!

---

**Questions? Check the troubleshooting section in CLAUDE.md**
