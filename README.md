# NVENC HEVC Stream Patcher. Add missing HDR metadata (VUI and SEI)
Tiny python script and binary (Win) adding/altering basic HDR metadata (SEI and SPS VUI) to raw HEVC streams from NVENC encoder.
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

###History behind this app:
In my work and research I need to create HDR10 compatible HEVC files. I used x265 codec for this to encode with HDR10 metadata. But encoding 4K HEVC videos is slow. So I hoped to speedup process using nVidia GTX10x0 GPUs with it's brilliant hardware HEVC (10,12 bit) encoding support. But reality (at this moment) is that no any encoder using NVENC support writing HDR10 metadata into HEVC stream. So you have nice HDR graded deep color video, but your TV or player have no idea that this is HDR video and you have **to turn on** HDR mode on TV or app **manually**. Not user friendly, right?
As HDR10 metadata is stored in NON-VCL NAL units (i.e. not part of encoded picture data), it can be altered without touching the picture data in video stream. I.e. no need to re-encode video to put HDR signaling flags. 
As result this app was created to help content creators make HDR videos quicker and easier. 

**This script is based on figgis's h265 parser script  (https://gist.github.com/figgis/fd509a02d4b1aa89f6ef)**

**CC0 License. I.e. you may use code or binaries as you like** 
