```bash
$ ./nisten_hffs.py

╭────────────────────────────────────────╮
│  🐱 NISTEN HFFS v1.0                   │
│  HuggingFace FileSystem                │
╰────────────────────────────────────────╯

🔍 Checking requirements...
   ✓ Python packages
   ✓ HuggingFace auth
   ✓ FUSE support

📝 Configuration
────────────────────────────────────────

HuggingFace repository:
  Format: username/repo-name
  Example: meta-llama/Llama-2-7b

→ Repository: TheBloke/Llama-2-7B-GGUF
→ Folder: llama2

🔌 Mounting TheBloke/Llama-2-7B-GGUF...
   ✓ Read mount ready
   ✓ Write cache ready
   ✓ Mount complete

✅ NISTEN HFFS READY
📁 Mounted: TheBloke/Llama-2-7B-GGUF
📍 Location: ~/llama2/

Press Ctrl+C to unmount and exit
```

## ⚡ Quick Start

```bash
# First time only
huggingface-cli login

# Run
./nisten_hffs.py
```

## 📦 Install

```bash
# Ubuntu/Debian
sudo apt-get install fuse
sudo usermod -a -G fuse $USER
# Logout & login after this

# Arch/CachyOS
sudo pacman -S fuse2
```

## 🎮 Usage

```bash
# In another terminal while mounted:

$ ls ~/llama2/
READ/  WRITE/

$ ls ~/llama2/READ/
llama-2-7b.Q4_K_M.gguf  llama-2-7b.Q5_K_M.gguf  README.md

$ du -sh ~/llama2/READ/llama-2-7b.Q4_K_M.gguf
3.8G ~/llama2/READ/llama-2-7b.Q4_K_M.gguf
# ☝️ Shows size but doesn't download!

$ head -c 1000 ~/llama2/READ/llama-2-7b.Q4_K_M.gguf | xxd
# ☝️ Streams first 1KB only!

$ cp my_lora.bin ~/llama2/WRITE/
$ echo "training complete" > ~/llama2/WRITE/status.txt
# ☝️ Auto-uploads in 2 min!
```

## 🚀 Examples

```bash
# Mount Llama model
→ Repository: meta-llama/Llama-2-7b
→ Folder: llama2

# Mount your own repo  
→ Repository: username/my-dataset
→ Folder: data

# Mount with 40GB models
→ Repository: microsoft/phi-2
→ Folder: phi2
# Then: cat ~/phi2/READ/model.bin  # Streams, no download!
```

## ⚠️ Gotchas

```
❌ Deletions don't sync (Git limitation)
❌ Max write: RAM/2 (usually 8GB)  
❌ Writes take 2min to appear on HF
❌ Can't edit existing files, only add new
```

## 🔧 Troubleshooting

```bash
# "Not authenticated"
huggingface-cli login

# "FUSE not found"  
sudo apt-get install fuse

# "Mount failed"
fusermount -u ~/folder  # Clear old mount
rm /tmp/.nisten_hffs.lock

# "No space left" 
df -h /dev/shm  # Check RAM disk
# Solution: Write smaller files

# Mount hanging
pkill -f nisten_hffs
fusermount -u ~/folder

# Can't see files
ls ~/folder/READ/  # Files here
ls ~/folder/WRITE/ # Your uploads here
```

## 💡 Pro Tips

```bash
# Stream 40GB model without downloading
cat ~/mount/READ/pytorch_model.bin | head -c 1000000 > sample.bin

# Upload folder
cp -r my_dataset/* ~/mount/WRITE/

# Check sync status  
ls ~/mount/WRITE/  # Local cache
# Wait 2 min
# Check https://huggingface.co/username/repo

# Multiple mounts
./nisten_hffs.py  # Mount 1
./nisten_hffs.py  # Mount 2 (different folder)
```

## 🏗️ Architecture

```
┌─────────────┐
│ HuggingFace │ ← Every 2 min
└──────┬──────┘
       │
    ┌──▼──┐
    │ FUSE│ Streaming
    └──┬──┘
       │
┌──────▼──────┐
│  ~/folder/  │
├─────────────┤
│ READ/  │ ← HF files (read-only)
│ WRITE/ │ ← Your files (RAM cache)
└─────────────┘
       │
    ┌──▼──┐
    │ RAM │ /dev/shm
    └─────┘
```

## 🐛 Known Issues

- Append-only (no deletes)
- 2 min sync delay
- RAM limited writes
- No file editing (only new files)

## 🎯 Perfect For

✅ Reading huge models without downloading  
✅ Uploading datasets without Git  
✅ Shared team storage  
✅ CI/CD with zero disk  
✅ Working on machines with no disk space  

## 🚫 Not For

❌ Real-time collaboration  
❌ Frequent small edits  
❌ Large video editing  
❌ Database storage  

---

```
  /\_/\  
 ( o.o ) Made with 🐱 by Nisten
  > ^ <  Zero disk. Pure vibes.
```
