# nv_hevc_hdr_patcher
Tiny python script adding/altering basic HDR metadata (SEI and SPS VUI) to raw HEVC streams from NVENC encoder

Written on python 3.6

Prerequisities (for now)
  - python 3.6 installed
  - bitstring module installed
  - manual filenames and parameters setting in script
  
How to use:
1) First you need raw HEVC (H265) stream file created with NVENC encoder (Rigaya's NVencC or ffmpeg's hevc_nvenc). if you have already muxed you video to mp4,mkv, unmux and extract raw h.265 stream (for example with "FFMPEG -i infile.mp4 -c:v copy -an outfile.h265"

2) Open script in IDLE and set parameters, infile and outfile. Press F5 to launch.

3) That's all!

4) Mux the outfile .h265 stream to MP4 or MKV with FFMPEG or whatever

NOTE: This may not work well with HEVC streams made by x265 (x265 lib) as it creates a lot of repeating NALS and SEIs.

TO BE CONTINUED
