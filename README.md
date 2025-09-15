# 🐱 NISTEN HFFS

HuggingFace as a filesystem. Zero disk. Pure cloud.

## 📸 What It Looks Like

```bash
$ ./nisten_hffs.py

╭────────────────────────────────────────╮
│  🐱 NISTEN HFFS v1.0                   │
│  HuggingFace FileSystem                │
╰────────────────────────────────────────╯

→ Repository: nisten/cats_4b_bfloat16
→ Folder: nisten_cats

🔌 Mounting nisten/cats_4b_bfloat16...
   ✓ Read mount ready
   ✓ Write cache ready

✅ READY at ~/nisten_cats/
Press Ctrl+C to unmount
```

## ⚡ Quick Start

```bash
huggingface-cli login  # First time only
./nisten_hffs.py
```

## 🎮 Usage

```bash
# Read from HuggingFace
cat ~/nisten_cats/READ/README.md    # Stream file
ls ~/nisten_cats/READ/               # List files

# Write to HuggingFace  
cp data.txt ~/nisten_cats/WRITE/    # Upload file
echo "done" > ~/nisten_cats/WRITE/status.txt # Create file
```

## 🔧 Configure Your Own

```bash
$ ./nisten_hffs.py
→ Repository: YOUR_USERNAME/YOUR_REPO  # Enter your repo
→ Folder: my_mount                     # Pick folder name
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

## 🏗️ Architecture

```
HuggingFace ←──[2 min sync]── WRITE/
     │                           │
  [stream]                    [RAM cache]
     │                           │
   READ/ ←──────[~/folder/]──────┘
```

## 🌟 Real World

```bash
# 20GB disk, 128GB RAM machine
$ df -h /
/dev/sda1  20G  19G  1G  95% /

$ ./nisten_hffs.py
→ Repository: meta-llama/Llama-2-70b

# Access 140GB model without downloading!
$ python train.py --model ~/llama70b/READ/pytorch_model.bin
Loading... [streams from cloud]
Saving checkpoint to ~/llama70b/WRITE/checkpoint.pt
✓ Auto-uploads!
```

---

```
  /\_/\  
 ( o.o ) Made with 🐱 by Nisten
  > ^ <  Zero disk. Pure vibes.
```