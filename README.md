# NVENC HEVC Stream Patcher. Add missing HDR metadata (VUI and SEI)
Tiny python script and binary (Win) adding/altering basic HDR metadata (SEI and SPS VUI) to raw HEVC streams from NVENC encoder

Written on python 3.5-3.6

Prerequisities (for now):
  - VC 2015 redist to run binary
  
How to use:
  - First you need raw HEVC (H265) stream file created with NVENC encoder (Rigaya's NVencC or ffmpeg's hevc_nvenc). if you have already muxed you video to mp4,mkv, unmux and extract raw h.265 stream (for example with "FFMPEG -i infile.mp4 -c:v copy -an outfile.h265"). That will prepare source file.
  - launch cmd in folder and type "nvhsp.exe infile [-params] outfile"
    - you may also type "nvhsp.exe -h" to get help on params and values
    - param names and values are same as in x265
  - Hit "Enter"
  - That's all! nvhsp creates new raw HEVC stream with applied metadata flags and values.
  - Mux the outfile .h265 stream to MP4 or MKV with FFMPEG or whatever
  
Script usage:
  - you may also use the py script (for geeks)
  - prerequisities for this
    - python 3.5-3.6 installed (checked only on these) 
    - bitstring module installed (pip install bitstring)

NOTE: This may not work well with HEVC streams made by x265 (x265 lib) with *REPEATING* NAL and SEI units! Output stream most probably could be corrupted!

TO DO:
 - try to make addition of SEI with Mastering Display Data (D.2.27 Mastering display colour volume SEI message syntax) as Mastering Display params are often specified when encoding HDR10 files with x265.
 - research and decide if Knee Function SEI needed. If needed - make. (ref. D.2.31 Knee function information SEI message syntax)

This script is based on figgis's h265 parser script  (https://gist.github.com/figgis/fd509a02d4b1aa89f6ef)
