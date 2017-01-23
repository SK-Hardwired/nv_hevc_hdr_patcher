# NVENC HEVC Stream Patcher. Add missing HDR metadata (VUI and SEI)
Tiny python script and binary (Win) adding/altering basic HDR metadata (SEI and SPS VUI) to raw HEVC streams from NVENC encoder (if you have PASCAL gen GPU).

**This app not re-encode video! So works very fast.**

This could be handy if you want to add following flags (metadata) to HEVC streams from NVENC encoders (nVidia SDK currently does not support emit of this data to HEVC streams):
  - color primaries (for example, bt2020)
  - transfer characteristics (for example, SMPTE ST 2084)
  - color matrix (for example, bt2020nc)
  - chroma bit location
  - video format (PAL, NTSC, COMPONENT, e.t.c)
  - signal range flag (Full (0-255) or TV(16-235))
  - MaxCLL (in nits)
  - MaxFall (in nits)
  - Mastering display data (in format `G(13250,34500)B(7500,3000)R(34000,16000)WP(15635,16450)L(10000000,1)`) 

Written on python 3.5-3.6

Prerequisities (for now):
  - VC 2015 redist to run binary
  
How to use:
  - First you need raw HEVC (H265) stream file created with NVENC encoder (Rigaya's NVencC or ffmpeg's hevc_nvenc). if you have already muxed you video to mp4,mkv, unmux and extract raw h.265 stream (for example with "FFMPEG -i infile.mp4 -c:v copy -an outfile.h265"). That will prepare source file.
  - launch cmd in folder and type `nvhsp.exe infile [-params] outfile`
    - you may also type `nvhsp.exe -h` to get help on params and values
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
 - research and decide if Knee Function SEI needed. If needed - make. (ref. D.2.31 Knee function information SEI message syntax)

**This script is based on figgis's h265 parser script  (https://gist.github.com/figgis/fd509a02d4b1aa89f6ef)**

**CC0 License. I.e. you may use code or binaries as you like** 
