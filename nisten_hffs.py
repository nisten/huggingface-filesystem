#!/usr/bin/env python3
"""
🐱 NISTEN HFFS - HuggingFace FileSystem
Zero-disk network storage for AI models and datasets
"""

import os
import sys
import time
import signal
import json
import threading
import subprocess
from pathlib import Path
from datetime import datetime

# Enable fast transfers
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"

class NistenHFFS:
    """Nisten's HuggingFace FileSystem"""
    
    VERSION = "1.0.0"
    LOCK_FILE = Path("/tmp/.nisten_hffs.lock")
    
    def __init__(self):
        self.repo = None
        self.folder = None
        self.mount_point = None
        self.cache_dir = None
        self.readonly_mount = None
        self.is_mounted = False
        self.mount_thread = None
        self.scheduler = None
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def show_banner(self):
        """Show welcome banner"""
        self.clear_screen()
        print("""
╭────────────────────────────────────────╮
│  🐱 NISTEN HFFS v1.0                   │
│  HuggingFace FileSystem                │
╰────────────────────────────────────────╯
        """)
    
    def check_existing(self):
        """Check for existing mounts"""
        if self.LOCK_FILE.exists():
            try:
                with open(self.LOCK_FILE) as f:
                    mounts = json.load(f)
                    if mounts:
                        print("\n⚠️  Found existing mount:")
                        for m in mounts:
                            print(f"   • {m['folder']} → {m['repo']}")
                            print(f"     Started: {m['time']}")
                        
                        print("\nOptions:")
                        print("  [u] Unmount existing")
                        print("  [c] Continue anyway")
                        print("  [q] Quit")
                        
                        choice = input("\n→ ").strip().lower()
                        if choice == 'u':
                            self.cleanup_existing(mounts)
                            return True
                        elif choice == 'q':
                            return False
                        return True
            except:
                pass
        return True
    
    def cleanup_existing(self, mounts):
        """Clean up existing mounts"""
        for mount in mounts:
            path = Path.home() / mount['folder']
            subprocess.run(['fusermount', '-u', str(path / 'READ')], capture_output=True)
            subprocess.run(['rm', '-rf', f"/tmp/.nisten_{mount['folder']}_ro"], capture_output=True)
            subprocess.run(['rm', '-rf', f"/dev/shm/nisten_{mount['folder']}_cache"], capture_output=True)
        self.LOCK_FILE.unlink(missing_ok=True)
        print("✅ Cleaned up existing mounts")
        time.sleep(1)
    
    def check_requirements(self):
        """Check system requirements"""
        print("\n🔍 Checking requirements...")
        
        # Check Python packages
        try:
            from huggingface_hub import HfFileSystem, HfFolder, CommitScheduler
            from fsspec.fuse import run
            print("   ✓ Python packages")
        except ImportError:
            print("   📦 Installing packages...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-q",
                "huggingface_hub[hf_transfer]", "fsspec[fuse]"
            ])
            from huggingface_hub import HfFileSystem, HfFolder, CommitScheduler
            from fsspec.fuse import run
            print("   ✓ Python packages installed")
        
        # Check auth
        from huggingface_hub import HfFolder
        token = HfFolder.get_token()
        if not token:
            print("\n❌ Not logged in to HuggingFace")
            print("\nPlease run:")
            print("  huggingface-cli login")
            print("\nThen try again.")
            return False
        print("   ✓ HuggingFace auth")
        
        # Check FUSE
        if not Path("/dev/fuse").exists():
            print("\n❌ FUSE not installed")
            print("\nPlease run:")
            print("  sudo apt-get install fuse")
            print("  sudo usermod -a -G fuse $USER")
            print("\nThen logout and login again.")
            return False
        print("   ✓ FUSE support")
        
        return True
    
    def get_config(self):
        """Get configuration from user"""
        print("\n📝 Configuration")
        print("─" * 40)
        
        # Get repo
        print("\nHuggingFace repository:")
        print("  Format: username/repo-name")
        print("  Example: meta-llama/Llama-2-7b")
        self.repo = input("\n→ Repository: ").strip()
        if not self.repo:
            print("❌ Repository required")
            return False
        
        # Get folder name
        default_folder = self.repo.split('/')[-1].replace('-', '_').lower()
        print(f"\nLocal folder name (default: {default_folder}):")
        self.folder = input("→ Folder: ").strip() or default_folder
        
        # Setup paths
        self.mount_point = Path.home() / self.folder
        self.cache_dir = Path("/dev/shm") / f"nisten_{self.folder}_cache"
        self.readonly_mount = Path("/tmp") / f".nisten_{self.folder}_ro"
        
        # Check if mount point exists
        if self.mount_point.exists() and list(self.mount_point.iterdir()):
            print(f"\n⚠️  ~/{self.folder}/ already exists and has files")
            print("  [o] Overwrite")
            print("  [c] Choose different name")
            choice = input("\n→ ").strip().lower()
            if choice == 'c':
                return self.get_config()
            elif choice != 'o':
                return False
        
        return True
    
    def mount(self):
        """Mount the filesystem"""
        from huggingface_hub import HfFileSystem, CommitScheduler
        from fsspec.fuse import run
        
        print(f"\n🔌 Mounting {self.repo}...")
        
        # Clean any existing
        self.mount_point.mkdir(parents=True, exist_ok=True)
        subprocess.run(['fusermount', '-u', str(self.readonly_mount)], capture_output=True)
        
        # Create directories
        self.readonly_mount.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Mount HF repo read-only
        fs = HfFileSystem()
        
        def mount_worker():
            try:
                run(fs, f"{self.repo}/", str(self.readonly_mount),
                    foreground=True, threads=False)
            except:
                pass
        
        self.mount_thread = threading.Thread(target=mount_worker, daemon=True)
        self.mount_thread.start()
        
        # Wait for mount
        for _ in range(30):
            time.sleep(0.1)
            try:
                list(self.readonly_mount.iterdir())
                break
            except:
                continue
        else:
            print("❌ Mount failed")
            return False
        
        # Setup write scheduler
        print("   ✓ Read mount ready")
        
        self.scheduler = CommitScheduler(
            repo_id=self.repo,
            folder_path=self.cache_dir,
            path_in_repo="uploads",
            every=2,
            squash_history=True
        )
        print("   ✓ Write cache ready")
        
        # Create symlinks
        read_link = self.mount_point / "READ"
        write_link = self.mount_point / "WRITE"
        
        for link in [read_link, write_link]:
            if link.exists():
                link.unlink()
        
        read_link.symlink_to(self.readonly_mount)
        write_link.symlink_to(self.cache_dir)
        
        # Update lock file
        lock_data = [{
            'repo': self.repo,
            'folder': self.folder,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }]
        with open(self.LOCK_FILE, 'w') as f:
            json.dump(lock_data, f)
        
        self.is_mounted = True
        print("   ✓ Mount complete")
        
        return True
    
    def show_tutorial(self):
        """Show usage tutorial"""
        self.clear_screen()
        print(f"""
╭────────────────────────────────────────╮
│  ✅ NISTEN HFFS READY                  │
╰────────────────────────────────────────╯

📁 Mounted: {self.repo}
📍 Location: ~/{self.folder}/

🎓 QUICK TUTORIAL:
─────────────────

1. READ files from HuggingFace:
   cat ~/{self.folder}/READ/README.md
   ls ~/{self.folder}/READ/
   
2. WRITE files (auto-uploads):
   cp myfile.txt ~/{self.folder}/WRITE/
   echo "test" > ~/{self.folder}/WRITE/note.txt
   
3. Files in WRITE/ sync every 2 minutes

⚡ FEATURES:
• Zero disk usage (streams from cloud)
• Write cache in RAM (/dev/shm)
• Auto-sync to HuggingFace
• Fast transfers (HF_TRANSFER enabled)

⚠️  NOTES:
• Deletions don't sync (Git limitation)
• Max write cache: {self.get_cache_limit()}GB
• Read-only files stream on-demand

Press Ctrl+C to unmount and exit
        """)
    
    def get_cache_limit(self):
        """Get RAM cache limit"""
        try:
            result = subprocess.run(['df', '-BG', '/dev/shm'], 
                                  capture_output=True, text=True)
            size = result.stdout.split('\n')[1].split()[1]
            return size.replace('G', '')
        except:
            return "8"
    
    def monitor(self):
        """Monitor mount status"""
        while self.is_mounted:
            time.sleep(60)
            # Could add status checks here
    
    def unmount(self):
        """Clean unmount"""
        if not self.is_mounted:
            return
        
        print("\n\n🧹 Unmounting...")
        
        # Sync final changes
        if self.scheduler:
            print("   📤 Syncing changes...")
            try:
                self.scheduler.push_to_hub()
                self.scheduler.stop()
            except:
                pass
        
        # Unmount FUSE
        subprocess.run(['fusermount', '-u', str(self.readonly_mount)], 
                      capture_output=True)
        
        # Clean cache
        if self.cache_dir and self.cache_dir.exists():
            subprocess.run(['rm', '-rf', str(self.cache_dir)], 
                          capture_output=True)
        
        # Clean mount point
        if self.mount_point:
            for link in ['READ', 'WRITE']:
                (self.mount_point / link).unlink(missing_ok=True)
        
        # Remove lock
        self.LOCK_FILE.unlink(missing_ok=True)
        
        print("   ✓ Unmounted cleanly")
        print("\nThanks for using Nisten HFFS! 🐱")
    
    def run(self):
        """Main run loop"""
        try:
            # Welcome
            self.show_banner()
            
            # Check existing
            if not self.check_existing():
                return 0
            
            # Check requirements
            if not self.check_requirements():
                return 1
            
            # Get config
            if not self.get_config():
                return 1
            
            # Mount
            if not self.mount():
                return 1
            
            # Show tutorial
            self.show_tutorial()
            
            # Setup signal handlers
            def signal_handler(sig, frame):
                self.unmount()
                sys.exit(0)
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            # Monitor
            self.monitor()
            
        except KeyboardInterrupt:
            self.unmount()
        except Exception as e:
            print(f"\n❌ Error: {e}")
            self.unmount()
            return 1
        
        return 0

def main():
    """Entry point"""
    hffs = NistenHFFS()
    return hffs.run()

if __name__ == "__main__":
    sys.exit(main())