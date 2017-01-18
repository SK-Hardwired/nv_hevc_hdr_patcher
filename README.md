# nv_hevc_hdr_patcher
Tiny python script adding/altering basic HDR metadata (SEI and SPS VUI) to raw HEVC streams from NVENC encoder

Written on python 3.6

Prerequisities (for now)
  - python 3.6 installed
  - bitstring module installed
  - manual filenames and parameters setting in script
  
How to use:
  - First you need raw HEVC (H265) stream file created with NVENC encoder (Rigaya's NVencC or ffmpeg's hevc_nvenc). if you have already muxed you video to mp4,mkv, unmux and extract raw h.265 stream (for example with "FFMPEG -i infile.mp4 -c:v copy -an outfile.h265"
  - Open script in IDLE and set parameters, infile and outfile. Press F5 to launch.
      - Alternatively, this script can be used from CMD by giving INFILE and OUTFILE as arguments. Color settings params still to be specified in script code  
  - That's all!
  - Mux the outfile .h265 stream to MP4 or MKV with FFMPEG or whatever

NOTE: This may not work well with HEVC streams made by x265 (x265 lib) as it creates a lot of repeating NALS and SEIs.

TO DO:
 - try to make addition of SEI with Mastering Display Data (D.2.27 Mastering display colour volume SEI message syntax) as Mastering Display params are often specified when encoding HDR10 files with x265.
 - research and decide if Knee Function SEI needed. If needed - make. (ref. D.2.31 Knee function information SEI message syntax)

This script is based on figgis's h265 parser script  (https://gist.github.com/figgis/fd509a02d4b1aa89f6ef)
