# ffUtils

**ffUtils** is a collection of Python utility scripts designed to automate, test, and streamline common audio and video processing tasks using FFmpeg.

## 🧰 Included Scripts

* **`ffu.py`** - The core utility script/module that likely handles the primary FFmpeg wrapper functions and shared logic.
* **`checkMedia.py`** - Analyzes media files to check their integrity, validate formats, or extract important metadata.
* **`encoderTests.py`** - Benchmarks and tests different FFmpeg encoders (e.g., H.264, HEVC, AV1) to evaluate quality, speed, and compression ratios.
* **`optimizeAV.py`** - Optimizes and compresses audio and video files, making them ideal for web streaming or saving storage space without significant quality loss.
* **`takeSamples.py`** - Quickly extracts short video clips or frame samples from larger media files.

## ⚙️ Prerequisites

Before using these scripts, ensure you have the following installed on your system:
* **Python 3.x**
* **FFmpeg**: Must be installed and added to your system's PATH variable. 

## 🚀 Getting Started

1. Clone the repository:
   ```bash
   git clone [https://github.com/gxjit/ffUtils.git](https://github.com/gxjit/ffUtils.git)
   cd ffUtils
   ```
2. Run any of the standalone scripts via Python. For example:
   ```bash
   python optimizeAV.py --help
   ```
   *(Note: Add your specific command-line arguments here if applicable)*
