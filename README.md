# nv_hevc_hdr_patcher
Tiny python script adding/altering basic HDR metadata (SEI and SPS VUI) to raw HEVC streams from NVENC

Written on python 3.6

Prerequisities (for now)
  - python 3.6 installed
  - bitstring module installed
  
How to use:
1) First you need raw HEVC (H265) stream file created with NVENC encoder (Rigaya's NVencC or ffmpeg's hevc_nvenc)
  - if you have already muxed you video to mp4,mkv, unmux and extract raw h.265 stream (for example with FFMPEG -i infile.mp4 -c:v copy -an outfile.h265

TO BE CONTINUED
