# 01 — PC Setup & Prerequisites

> **Goal:** Get your machine ready before touching any code.

---

## 🖥️ System Requirements

| Item | Minimum | Recommended |
|------|---------|-------------|
| OS | Windows 10 / Ubuntu 20.04 / macOS 11 | Windows 11 / Ubuntu 22.04 |
| RAM | 8 GB | 16 GB |
| CPU | 4 cores | 8 cores |
| Disk | 20 GB free | 50 GB free |
| GPU | Optional | NVIDIA (speeds up InsightFace) |
| Webcam | 720p | 1080p |

---

## 📦 Step 1 — Install Python 3.10+

### Windows
1. Go to https://www.python.org/downloads/
2. Download **Python 3.11.x** (recommended)
3. During install: ✅ **Check "Add Python to PATH"**
4. Verify in Command Prompt:
   ```
   python --version
   # Should print: Python 3.11.x
   pip --version
   ```

### Ubuntu / WSL2
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev python3-pip -y
python3.11 --version
```

### macOS
```bash
brew install python@3.11
python3.11 --version
```

---

## 📦 Step 2 — Install Node.js 18+ (for React frontend)

Go to https://nodejs.org/ and download **LTS version (18 or 20)**.

Verify:
```bash
node --version    # v18.x.x or v20.x.x
npm --version     # 9.x.x or above
```

---

## 📦 Step 3 — Install PostgreSQL

### Windows
1. Download from https://www.postgresql.org/download/windows/
2. Install version **15 or 16**
3. During setup:
   - Set a password for `postgres` user (remember this!)
   - Default port: **5432** ← keep this
4. After install, open **pgAdmin** or **psql** to verify

### Ubuntu
```bash
sudo apt install postgresql postgresql-contrib -y
sudo systemctl start postgresql
sudo systemctl enable postgresql
# Set password for postgres user:
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'yourpassword';"
```

### macOS
```bash
brew install postgresql@15
brew services start postgresql@15
```

---

## 📦 Step 4 — Install Git

### Windows
Download from https://git-scm.com/download/win

### Ubuntu
```bash
sudo apt install git -y
```

### macOS
```bash
brew install git
```

Verify:
```bash
git --version
```

---

## 📦 Step 5 — Install Visual Studio Code (Recommended IDE)

Download from https://code.visualstudio.com/

**Recommended Extensions:**
- Python (Microsoft)
- ES7+ React/Redux/React-Native snippets
- Tailwind CSS IntelliSense
- GitLens
- REST Client (for testing APIs)

---

## ⚠️ IMPORTANT — About InsightFace Models (MUST READ)

InsightFace downloads AI models **automatically** when first used, BUT you need to ensure the download works properly.

### What will be downloaded automatically:
| Model | Size | Purpose |
|-------|------|---------|
| `buffalo_l` (detection) | ~500 MB | Face detection (RetinaFace) |
| `buffalo_l` (recognition) | ~300 MB | Face embeddings (ArcFace) |
| **Total** | **~800 MB** | - |

### Where models are stored:
- **Windows:** `C:\Users\<YourName>\.insightface\models\buffalo_l\`
- **Linux/Mac:** `~/.insightface/models/buffalo_l/`

### How download happens:
When you first run code with InsightFace (during enrollment), it will auto-download from Hugging Face. This requires an **internet connection** at first run. After that, models are cached locally.

### If auto-download fails (common in India/slow connections):
You can manually download from:
- https://github.com/deepinsight/insightface/releases
- Look for `buffalo_l.zip`
- Extract to `~/.insightface/models/buffalo_l/`

---

## 📦 Step 6 — Install Build Tools (Required for InsightFace)

### Windows
InsightFace needs C++ build tools. Install:
1. Download **Visual Studio Build Tools** from:
   https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. During install, select: **"Desktop development with C++"**

OR use the simpler way:
```bash
pip install cmake
```

### Ubuntu
```bash
sudo apt install build-essential cmake libgl1-mesa-glx libglib2.0-0 -y
```

### macOS
```bash
xcode-select --install
brew install cmake
```

---

## 📦 Step 7 — Optional: Install Docker (for later deployment)

Not needed right now for local development. Install later when you do production deployment.

Download from https://www.docker.com/products/docker-desktop/

---

## ✅ Pre-flight Checklist

Run this to check everything:

```bash
python --version          # 3.10+ ✓
pip --version             # 23.x ✓
node --version            # 18.x or 20.x ✓
npm --version             # 9.x+ ✓
git --version             # 2.x+ ✓
psql --version            # 15.x+ ✓ (or pg_ctl --version)
```

If all pass, you're ready for the next step!

---

**Next →** `02_DJANGO_PROJECT_SETUP.md`
