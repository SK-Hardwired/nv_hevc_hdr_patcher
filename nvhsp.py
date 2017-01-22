import sys
import os
import re
from bitstring import BitArray, BitStream, pack, Bits

import argparse

### CMD arguments parsing

parser = argparse.ArgumentParser(description='Creates new HEVC raw stream with HDR10 metadata.',)
parser.add_argument('infile',help='First file or filepath should be the source')
parser.add_argument('outfile',help='Second file or filepath should be the destination file')
parser.add_argument('-colorprim',help='Color primaries. Default: undef',choices=['undef', 'bt709', 'bt470m', 'bt470bg', 'smpte170m','smpte240m', 'film', 'bt2020','smpte-st-428'], default='undef')
parser.add_argument('-transfer',help='Transfer characteristics. Default: umdef',choices=['undef','bt709', 'bt470m', 'bt470bg', 'smpte170m','smpte240m', 'linear', 'log100', 'log316', 'iec61966-2-4', 'bt1361e', 'iec61966-2-1','bt2020-10','bt2020-12', 'smpte-st-2084', 'smpte-st-428', 'arib-std-b67'],default='undef')
parser.add_argument('-colormatrix',help='Color matrix. Default: undef',choices=['undef','bt709','fcc','bt470bg','smpte170m','smpte240m','GBR','YCgCo','bt2020nc','bt2020c'],default='undef')
parser.add_argument('-chromaloc',help='Chroma bit sample location. Default: 0',choices= range(6),type=int,default=0)
parser.add_argument('-maxcll',help='MaxCLL and MaxFall in nits. Syntax: "1000,300".',type=str)
parser.add_argument('-videoformat',help='Optional: specify the videoformat. Default: unspecified',choices=['component','pal','ntsc','secam','mac','unspec'],default='unspec')
parser.add_argument('-full_range',help='Full or TV range. Default: tv',choices=['tv','full'],default='tv')
parser.add_argument('-masterdisplay',type=str,help='Mastering display data. For example: "G(13250,34500)B(7500,3000)R(34000,16000)WP(15635,16450)L(10000000,1)" Default: None')
args = parser.parse_args()


# Create the list, from where we will take corresponding value to input param
prim_list = ['reserved','bt709','undef','reserved', 'bt470m', 'bt470bg', 'smpte170m','smpte240m', 'film', 'bt2020','smpte-st-428']
trc_list = ['reserved','bt709','undef','reserved', 'bt470m', 'bt470bg', 'smpte170m','smpte240m', 'linear', 'log100', 'log316', 'iec61966-2-4', 'bt1361e', 'iec61966-2-1','bt2020-10','bt2020-12', 'smpte-st-2084', 'smpte-st-428', 'arib-std-b67']
mtx_list = ['GBR','bt709','undef','reserved','fcc','bt470bg','smpte170m','smpte240m','YCgCo','bt2020nc','bt2020c']
vid_fmt_list = ['component','pal','ntsc','secam','mac','unspec']
range_list = ['tv','full']

### set values from cmd to variables ###
maxcll = args.maxcll                             #MaxCLL parameter to be written into SEI
primaries = prim_list.index(args.colorprim)                            #Primaries to be put into VUI section. Default = 9 (bt2020)
trc = trc_list.index(args.transfer)                                 #Transfer function describing curve. Default = 16 (SMPTE ST2084 curve)
matrix = mtx_list.index(args.colormatrix)                               #Color matrix. Default = 9 (bt2020nc)
chroma_bit = args.chromaloc                           #Chroma bit location = 2 (as required by UHD BD specs)
video_fmt = vid_fmt_list.index(args.videoformat)                            #Video format (COMPONENT,PAL, NTSC, e.t.c.) Default = 5 (Unspecified)
full_range = range_list.index(args.full_range)
md_arg_str = args.masterdisplay


chunk = 8388608
progr = 0
### END OF PUT SETTINGS SECTION ###


class profile_tier_level(object):
    def __init__(self, t, maxNumSubLayersMinus1):
        """
        Interpret next bits in BitString s as an profile_tier_level
        7.3.3 Profile, tier and level syntax
        """

        self.general_profile_space = t.read('uint:2')
        self.general_tier_flag = t.read('uint:1')
        self.general_profile_idc = t.read('uint:5')
        self.general_profile_compatibility_flag = [t.read('uint:1') for _ in range(32)]
        self.general_progressive_source_flag = t.read('uint:1')
        self.general_interlaced_source_flag = t.read('uint:1')
        self.general_non_packed_constraint_flag = t.read('uint:1')
        self.general_frame_only_constraint_flag = t.read('uint:1')
        self.general_reserved_zero_44bits = t.read('uint:44')
        self.general_level_idc = t.read('uint:8')
        self.sub_layer_profile_present_flag = []
        self.sub_layer_level_present_flag = []
  ##      print (maxNumSubLayersMinus1)
        for i in range(maxNumSubLayersMinus1):
            self.sub_layer_profile_present_flag.append(t.read('uint:1'))
            self.sub_layer_level_present_flag.append(t.read('uint:1'))

    def show(self):
        print
        print ('Profile Tier Level')
        print ('\t','==================')
        print ('\t','general_profile_space', self.general_profile_space)
        print ('\t','general_tier_flag', self.general_tier_flag)
        print ('\t','general_profile_idc', self.general_profile_idc)
        for i in range(32):
            print ("{}{}[{:2d}] {}".format('\t', 'general_profile_compatibility_flag', i, self.general_profile_compatibility_flag[i]))
        print ('\t','general_progressive_source_flag', self.general_progressive_source_flag)
        print ('\t','general_interlaced_source_flag', self.general_interlaced_source_flag)
        print ('\t','general_non_packed_constraint_flag', self.general_non_packed_constraint_flag)
        print ('\t','general_frame_only_constraint_flag', self.general_frame_only_constraint_flag)
        print ('\t','general_reserved_zero_44bits', self.general_reserved_zero_44bits)
        if self.general_reserved_zero_44bits:
            print ('\t',"{0:b}".format(self.general_reserved_zero_44bits))
        print ('\t','general_level_idc', self.general_level_idc)
        print ('\t','sub_layer_profile_present_flag', self.sub_layer_profile_present_flag)
        print ('\t','sub_layer_level_present_flag', self.sub_layer_level_present_flag)
                     
class rbsp_trailing_bits(object):
    def __init__ (self,t,NumBytesInRbsp):
        self.rbsp_stop_one_bit = t.read ('uint:1')
        while t.pos < NumBytesInRbsp :
            self.rbsp_alignment_zero_bit = t.read ('uint:1')
        
        

class vui_parameters(object):
    def __init__ (self,t):
        self.aspect_ratio_info_present_flag = t.read ('uint:1')
        if self.aspect_ratio_info_present_flag :
            self.aspect_ratio_idc = t.read ('uint:8')
            if self.aspect_ratio_idc == 255 :
                self.sar_width = t.read ('uint:16')
                self.sar_height = t.read ('uint:16')
        self.overscan_info_present_flag = t.read ('uint:1')
        if self.overscan_info_present_flag :
            self.overscan_appropriate_flag = t.read ('uint:1')
        self.video_signal_type_present_flag = t.read ('uint:1')
        if self.video_signal_type_present_flag :
            self.video_format = t.read ('uint:3')
            self.video_full_range_flag = t.read ('uint:1')
            self.colour_description_present_flag = t.read ('uint:1')
            if self.colour_description_present_flag :
                self.colour_primaries = t.read ('uint:8')
                self.transfer_characteristics = t.read ('uint:8')
                self.matrix_coeffs = t.read ('uint:8')

        if self.video_signal_type_present_flag == 0 :
            self.video_signal_type_present_flag = 1 
            self.video_format = video_fmt
            self.video_full_range_flag = full_range
            self.colour_description_present_flag = 1
            self.colour_primaries = primaries
            self.transfer_characteristics = trc
            self.matrix_coeffs = matrix


        self.chroma_loc_info_present_flag = t.read ('uint:1')
        if self.chroma_loc_info_present_flag :
            self.chroma_sample_loc_type_top_field = t.read ('ue')
            self.chroma_sample_loc_type_bottom_field = t.read ('ue')
### Change Chroma Sample Loc
        if self.chroma_loc_info_present_flag == 0 :
            self.chroma_loc_info_present_flag = 1
            self.chroma_sample_loc_type_top_field = chroma_bit
            self.chroma_sample_loc_type_bottom_field = chroma_bit
        
        self.neutral_chroma_indication_flag = t.read ('uint:1')
        self.field_seq_flag = t.read ('uint:1')
        self.frame_field_info_present_flag = t.read ('uint:1')
        self.default_display_window_flag = t.read ('uint:1')
        if self.default_display_window_flag :
            self.def_disp_win_left_offset = t.read ('ue')
            self.def_disp_win_right_offset = t.read ('ue')
            self.def_disp_win_top_offset = t.read ('ue')
            self.def_disp_win_bottom_offset = t.read ('ue')
        
        self.vui_timing_info_present_flag = t.read ('uint:1')
        if self.vui_timing_info_present_flag :
            self.vui_num_units_in_tick = t.read ('uint:32')
            self.vui_time_scale = t.read ('uint:32')
            self.vui_poc_proportional_to_timing_flag = t.read ('uint:1')
            if self.vui_poc_proportional_to_timing_flag  :
                self.vui_num_ticks_poc_diff_one_minus1 = t.read ('ue')
            self.vui_hrd_parameters_present_flag = t.read ('uint:1')
        """   
            if( vui_hrd_parameters_present_flag )
            hrd_parameters( 1, sps_max_sub_layers_minus1 )
        """
            
        self.bitstream_restriction_flag = t.read ('uint:1')
        if self. bitstream_restriction_flag :
            self.tiles_fixed_structure_flag = t.read ('uint:1')
            self.motion_vectors_over_pic_boundaries_flag = t.read ('uint:1')
            self.restricted_ref_pic_lists_flag = t.read ('uint:1')
            self.min_spatial_segmentation_idc = t.read ('ue')
            self.max_bytes_per_pic_denom = t.read ('ue')
            self.max_bits_per_min_cu_denom  = t.read ('ue')
            self.log2_max_mv_length_horizontal = t.read ('ue')
            self.log2_max_mv_length_vertical = t.read ('ue')
        

   

    def show (self):
        print
        print ('====VUI Block=====')
        print ('aspect_ratio_info_present_flag',self.aspect_ratio_info_present_flag)
        if self.aspect_ratio_info_present_flag :
            print ('aspect_ratio_idc', self.aspect_ratio_idc)
            if self.aspect_ratio_idc == 255 :
                print ('sar_width', self.sar_width)
                print ('sar_height',self.sar_height)
    

        print ('overscan_info_present_flag',self.overscan_info_present_flag)
        if self.overscan_info_present_flag :
            print ('overscan_appropriate_flag',self.overscan_appropriate_flag)
        print ('video_signal_type_present_flag',self.video_signal_type_present_flag)
        if self.video_signal_type_present_flag :
            print ('video_format', self.video_format)
            print ('video_full_range_flag',self.video_full_range_flag)
            print ('colour_description_present_flag',self.colour_description_present_flag)
            if self.colour_description_present_flag :
                print ('colour_primaries',self.colour_primaries)
                print ('transfer_characteristics',self.transfer_characteristics)
                print ('matrix_coeffs',self.matrix_coeffs)
        print ('chroma_loc_info_present_flag',self.chroma_loc_info_present_flag)
        if self.chroma_loc_info_present_flag :
            print ('chroma_sample_loc_type_top_field',self.chroma_sample_loc_type_top_field)
            print ('chroma_sample_loc_type_bottom_field',self.chroma_sample_loc_type_bottom_field)
        print ('neutral_chroma_indication_flag',self.neutral_chroma_indication_flag)
        print ('field_seq_flag',self.field_seq_flag)
        print ('frame_field_info_present_flag',self.frame_field_info_present_flag)
        print ('default_display_window_flag',self.default_display_window_flag)
        if self.default_display_window_flag :
            print ('def_disp_win_left_offset', self.def_disp_win_left_offset)
            print ('def_disp_win_right_offset', self.def_disp_win_right_offset)
            print ('def_disp_win_top_offset', self.def_disp_win_top_offset)
            print ('def_disp_win_bottom_offset', self.def_disp_win_bottom_offset)
        print ('vui_timing_info_present_flag', self.vui_timing_info_present_flag)
        if self.vui_timing_info_present_flag :
            print ('vui_num_units_in_tick', self.vui_num_units_in_tick)
            print ('vui_time_scale', self.vui_time_scale)
            print ('vui_poc_proportional_to_timing_flag', self.vui_poc_proportional_to_timing_flag)
            if self.vui_poc_proportional_to_timing_flag :
                print ('vui_num_ticks_poc_diff_one_minus1',self.vui_num_ticks_poc_diff_one_minus1)
            print ('vui_hrd_parameters_present_flag',self.vui_hrd_parameters_present_flag)
        
        print ('bitstream_restriction_flag',self.bitstream_restriction_flag)
        if self. bitstream_restriction_flag :
            print ('tiles_fixed_structure_flag',self.tiles_fixed_structure_flag)
            print ('motion_vectors_over_pic_boundaries_flag',self.motion_vectors_over_pic_boundaries_flag)
            print ('restricted_ref_pic_lists_flag',self.restricted_ref_pic_lists_flag)
            print ('min_spatial_segmentation_idc',self.min_spatial_segmentation_idc)
            print ('max_bytes_per_pic_denom',self.max_bytes_per_pic_denom)
            print ('max_bits_per_min_cu_denom', self.max_bits_per_min_cu_denom)
            print ('log2_max_mv_length_horizontal',self.log2_max_mv_length_horizontal)
            print ('log2_max_mv_length_vertical',self.log2_max_mv_length_vertical)

    

### MAIN CODE ###

def main():
    """
    """

    if args.infile == args.outfile :
        print ('Error! Source and Destination can not be the same file!')
        sys.exit()

    if not os.path.exists(args.infile) :
        print ('Error! Given input file name not found! Please check path given in CMD or set in script code!')
        sys.exit()
    if md_arg_str :
        md = re.findall('\d+',md_arg_str)
        if len(md) != 10 :
            print ('Specified wrong "-masterdisplay" parameter! Please check!\n Example: G(13250,34500)B(7500,3000)R(34000,16000)WP(15635,16450)L(10000000,1) or do not specify')
            sys.exit()

    if maxcll :
        mcll = re.findall('\d+',maxcll)
    sei_ok = 0 
    
    F = open (args.infile,'r+b')
    o = open (args.outfile,'wb')

    print ('Parsing the infile:')
    print ('')
    print ('==========================')
    print ('')
    print ('Prepending SEI data')
    s = BitStream(F.read(chunk))
    
    nals = list(s.findall('0x000001', bytealigned=True))
    sps_nals = list(s.findall('0x00000142', bytealigned=True))
    sei_pref_nals = list (s.findall('0x0000014e', bytealigned=True))
    size = [y - x for x,y in zip(nals,nals[1:])]
    sps_pos = list(set(nals).intersection(sps_nals))
    sei_pref_nals_pos = list(set(nals).intersection(sei_pref_nals))
    sps_size = size[nals.index(sps_nals[0])]
    if sei_pref_nals :
        sei_pref_nal_size = ( size[nals.index(sei_pref_nals[0])])
### MAXCLL & MAXFALL ###

    if args.maxcll or md_arg_str :
        sei_forbidden_zero_bit  = 0
        sei_nal_unit_type = 39
        sei_nuh_layer_id = 0
        sei_nuh_temporal_id_plus1 = 1
        new_sei_string = pack ('uint:1,2*uint:6,uint:3',sei_forbidden_zero_bit,sei_nal_unit_type,sei_nuh_layer_id,sei_nuh_temporal_id_plus1)
        print ('Starting new SEI NALu...')

        if maxcll :
            sei_last_payload_type_byte = 144
            sei_last_payload_size_byte = 4
            sei_max_content_light_level = int(mcll[0])
            sei_max_pic_average_light_level = int(mcll[1])
            new_sei_string += pack ('2*uint:8,2*uint:16',sei_last_payload_type_byte,sei_last_payload_size_byte,sei_max_content_light_level,sei_max_pic_average_light_level)
            print ('SEI message with MaxCLL=',sei_max_content_light_level,' and MaxFall=',sei_max_pic_average_light_level,' created in SEI NAL')

        if md_arg_str :
            md_sei_last_payload_type_byte = 137
            md_sei_last_payload_size_byte = 24
            #MD string ref
            #G(13250,34500)B(7500,3000)R(34000,16000)WP(15635,16450)L(10000000,1)
            new_sei_string += pack ('2*uint:8',md_sei_last_payload_type_byte,md_sei_last_payload_size_byte)
            for i in range (len(md)-2) :
                new_sei_string += pack ('uint:16',int(md[i]))

            new_sei_string += pack ('uint:32',int(md[8]))
            new_sei_string += pack ('uint:32',int(md[9]))

            new_sei_string.replace ('0x0000','0x000003',bytealigned=True)
            print ('SEI message Mastering Display Data',md_arg_str,'created in SEI NAL')     

        new_sei_string = '0x00000001' + new_sei_string + '0x00'
        sei_ok = True



### ------------------ ###   
    
    print ('Looking for SPS.........', sps_pos)
    print ('SPS_Nals_addresses', sps_pos)
    print ('SPS NAL Size', sps_size)
    print ('Starting reading SPS NAL contents')

    
    s.pos = sps_pos[0]
    t = s.peek(sps_size)

    t.pos = t.pos + 24

    forbidden_zero_bit  = t.read('uint:1')
    nal_unit_type = t.read('uint:6')
    nuh_layer_id = t.read('uint:6')
    nuh_temporal_id_plus1 = t.read('uint:3')
    nal_t = t[:]

# 7.3.1.1
    # Convert NAL data (Annex B format) to RBSP data

    t.tobytes()
    t.replace ('0x000003','0x0000')
    
    
# SPS parse block


    sps_video_parameter_set_id = t.read('uint:4')
    sps_max_sub_layers_minus1 = t.read('uint:3')
    sps_temporal_id_nesting_flag = t.read('uint:1')
    ptl = profile_tier_level(t, sps_max_sub_layers_minus1)
    sps_seq_parameter_set_id = t.read('ue')
    chroma_format_idc = t.read('ue')
    if chroma_format_idc == 3:
        separate_colour_plane_flag = t.read('uint:1')
    pic_width_in_luma_samples = t.read ('ue')
    pic_height_in_luma_samples = t.read ('ue')
    conformance_window_flag = t.read ('uint:1')
    if (conformance_window_flag) :
        conf_win_left_offset = t.read('ue')
        conf_win_right_offset = t.read('ue')
        conf_win_top_offset = t.read('ue')
        conf_win_bottom_offset = t.read('ue')
    bit_depth_luma_minus8 = t.read ('ue')
    bit_depth_chroma_minus8 = t.read ('ue')
    log2_max_pic_order_cnt_lsb_minus4 = t.read('ue')
    sps_sub_layer_ordering_info_present_flag = t.read('uint:1')
#   for (i = (sps_sub_layer_ordering_info_present_flag ? 0 : sps.max_sub_layers_minus1); i <= sps.max_sub_layers_minus1; i++)
    if sps_sub_layer_ordering_info_present_flag :
            sps_max_dec_pic_buffering_minus1 = t.read('ue')
            sps_max_num_reorder_pics = t.read('ue')
            sps_max_latency_increase_plus1 = t.read('ue')

    log2_min_luma_coding_block_size_minus3 = t.read ('ue')
    log2_diff_max_min_luma_coding_block_size = t.read ('ue')
    log2_min_luma_transform_block_size_minus2 = t.read ('ue')
    log2_diff_max_min_luma_transform_block_size = t.read ('ue')
    max_transform_hierarchy_depth_inter = t.read ('ue')
    max_transform_hierarchy_depth_intra = t.read ('ue')
    scaling_list_enabled_flag = t.read ('uint:1')
    """
    if( scaling_list_enabled_flag ) {
    sps_scaling_list_data_present_flag u(1)
    if( sps_scaling_list_data_present_flag )
    scaling_list_data( )
    }
    """
    amp_enabled_flag = t.read ('uint:1')
    sample_adaptive_offset_enabled_flag = t.read ('uint:1')
    pcm_enabled_flag = t.read ('uint:1')
    if pcm_enabled_flag :
        pcm_sample_bit_depth_luma_minus1 = t.read ('uint:4')
        pcm_sample_bit_depth_chroma_minus1 = t.read ('uint:4')
        log2_min_pcm_luma_coding_block_size_minus3  = t.read ('ue')
        log2_diff_max_min_pcm_luma_coding_block_size = t.read ('ue')
        pcm_loop_filter_disabled_flag = t.read ('uint:1')
    num_short_term_ref_pic_sets = t.read ('ue')
    if num_short_term_ref_pic_sets :
        for i in range (num_short_term_ref_pic_sets):
            if i != 0 :
                inter_ref_pic_set_prediction_flag = t.read ('uint:1')
        
            if not 'inter_ref_pic_set_prediction_flag' in globals() :
                """    
            
                if i == num_short_term_ref_pic_sets :
                    delta_idx_minus1 = t.read ('ue')
                if not 'delta_idx_minus1' in globals():
                    delta_idx_minus1 = 0
                delta_rps_sign = t.read ('uint:1')
                abs_delta_rps_minus1 = t.read ('ue')
                for j in range (NumDeltaPoc) :
                    used_by_curr_pic_flag[j] = t.read ('uint:1')
                if used_by_curr_pic_flag[j] :
                    use_delta_flag[j] = t.read ('uint:1')
        
             else:      
                """            
            
                num_negative_pics = t.read ('ue')
                num_positive_pics = t.read ('ue')
                delta_poc_s0_minus1 = [t.read ('ue') for _ in range (num_negative_pics)]
                used_by_curr_pic_s0_flag = [ t.read ('uint:1') for _ in range (num_negative_pics)]
                delta_poc_s1_minus1 = [t.read ('ue') for _ in range(num_positive_pics)]
                used_by_curr_pic_s1_flag = [t.read ('uint:1') for _ in range(num_positive_pics)]

          
    long_term_ref_pics_present_flag = t.read ('uint:1')
    if long_term_ref_pics_present_flag :
        num_long_term_ref_pics_sps = t.read ('ue')
        
        for i in range < (num_long_term_ref_pics_sps): 
            lt_ref_pic_poc_lsb_sps[i] = t.read ('ue')
            used_by_curr_pic_lt_sps_flag[i] = t.read ('uint:1')
       
    sps_temporal_mvp_enabled_flag = t.read ('uint:1')
    strong_intra_smoothing_enabled_flag = t.read ('uint:1')
    vui_parameters_present_flag = t.read ('uint:1')
    if vui_parameters_present_flag :
       vp = vui_parameters(t)
    sps_extension_present_flag = t.read ('uint:1')
    if sps_extension_present_flag :
        sps_range_extension_flag = t.read ('uint:1')
        sps_multilayer_extension_flag = t.read ('uint:1')
        sps_3d_extension_flag = t.read ('uint:1')
        sps_extension_5bits = t.read ('uint:1')
    tb = rbsp_trailing_bits(t,len(t))
    print ('Reading of SPS NAL finished. Read ',len(t),' of SPS NALu data.\n')
    
# print block
    """
    print ('sps_video_parameter_set_id', sps_video_parameter_set_id)
    print ('sps_max_sub_layers_minus1', sps_max_sub_layers_minus1)
    print ('sps_temporal_id_nesting_flag', sps_temporal_id_nesting_flag)
    ptl.show()
    print ('sps_seq_parameter_set_id', sps_seq_parameter_set_id)
    print ('chroma_format_idc', chroma_format_idc)
    if chroma_format_idc == 3:
        print ('separate_colour_plane_flag', separate_colour_plane_flag)
    print ('pic_width_in_luma_samples ', pic_width_in_luma_samples) #produces wrong number
    print ('pic_height_in_luma_samples', pic_height_in_luma_samples) #produces wrong number
    print ('conformance_window_flag', conformance_window_flag)
    print ('bit_depth_luma_minus8', bit_depth_luma_minus8)
    print ('bit_depth_chroma_minus8', bit_depth_chroma_minus8)
    print ('log2_max_pic_order_cnt_lsb_minus4', log2_max_pic_order_cnt_lsb_minus4)
    print ('sps_sub_layer_ordering_info_present_flag', sps_sub_layer_ordering_info_present_flag)

    if sps_sub_layer_ordering_info_present_flag :
       print ('sps_max_dec_pic_buffering_minus1', sps_max_dec_pic_buffering_minus1)
       print ('sps_max_num_reorder_pics', sps_max_num_reorder_pics)
       print ('sps_max_latency_increase_plus1', sps_max_latency_increase_plus1)
    
    print ('log2_min_luma_coding_block_size_minus3',log2_min_luma_coding_block_size_minus3)
    print ('log2_diff_max_min_luma_coding_block_size',log2_diff_max_min_luma_coding_block_size)
    print ('log2_min_luma_transform_block_size_minus2',log2_min_luma_transform_block_size_minus2)
    print ('log2_diff_max_min_luma_transform_block_size', log2_diff_max_min_luma_transform_block_size)
    print ('max_transform_hierarchy_depth_inter', max_transform_hierarchy_depth_inter)
    print ('max_transform_hierarchy_depth_intra', max_transform_hierarchy_depth_intra)
    print ('scaling_list_enabled_flag',scaling_list_enabled_flag)
    print ('amp_enabled_flag',amp_enabled_flag)
    print ('sample_adaptive_offset_enabled_flag',sample_adaptive_offset_enabled_flag)
    print ('pcm_enabled_flag',pcm_enabled_flag)
    if pcm_enabled_flag :
        print ('pcm_sample_bit_depth_luma_minus1',pcm_sample_bit_depth_luma_minus1)
        print ('pcm_sample_bit_depth_chroma_minus1',pcm_sample_bit_depth_chroma_minus1)
        print ('log2_min_pcm_luma_coding_block_size_minus3',log2_min_pcm_luma_coding_block_size_minus3)
        print ('log2_diff_max_min_pcm_luma_coding_block_size',log2_diff_max_min_pcm_luma_coding_block_size)
        print ('pcm_loop_filter_disabled_flag',pcm_loop_filter_disabled_flag)
    print ('num_short_term_ref_pic_sets',num_short_term_ref_pic_sets)
    print ('long_term_ref_pics_present_flag',long_term_ref_pics_present_flag)
    print ('sps_temporal_mvp_enabled_flag',sps_temporal_mvp_enabled_flag)
    print ('strong_intra_smoothing_enabled_flag',strong_intra_smoothing_enabled_flag)
    print ('vui_parameters_present_flag',vui_parameters_present_flag)
    if vui_parameters_present_flag :
        vp.show()
    print ('sps_extension_present_flag',sps_extension_present_flag)
    """
# New BS write Block
    print ('Making modified SPS NALu...')
    new_bs = BitStream()
    new_bs += pack('uint:4,uint:3,uint:1',sps_video_parameter_set_id,sps_max_sub_layers_minus1,sps_temporal_id_nesting_flag)
    new_bs += pack ('uint:2,uint:1,uint:5',ptl.general_profile_space, ptl.general_tier_flag,ptl.general_profile_idc)
    for i in range (32) :
        new_bs += pack('uint:1',int(ptl.general_profile_compatibility_flag[i]))
    new_bs += pack ('uint:1',ptl.general_progressive_source_flag)
    new_bs += pack ('uint:1',ptl.general_interlaced_source_flag)
    new_bs += pack ('uint:1',ptl.general_non_packed_constraint_flag)
    new_bs += pack ('uint:1',ptl.general_frame_only_constraint_flag)
    new_bs += pack ('uint:44',ptl.general_reserved_zero_44bits)
    new_bs += pack ('uint:8',ptl.general_level_idc)
    new_bs += pack ('ue',sps_seq_parameter_set_id)
    new_bs += pack ('ue',chroma_format_idc)
    if chroma_format_idc == 3:
        new_bs += pack ('uint:1',separate_colour_plane_flag)
    new_bs += pack ('ue',pic_width_in_luma_samples)
    new_bs += pack ('ue',pic_height_in_luma_samples)
    new_bs += pack ('uint:1',conformance_window_flag)
    if (conformance_window_flag) :
        new_bs += pack ('ue',conf_win_left_offset)
        new_bs += pack ('ue',conf_win_right_offset)
        new_bs += pack ('ue',conf_win_top_offset)
        new_bs += pack ('ue',conf_win_bottom_offset)
    new_bs += pack ('ue',bit_depth_luma_minus8)
    new_bs += pack ('ue',bit_depth_chroma_minus8)
    new_bs += pack ('ue',log2_max_pic_order_cnt_lsb_minus4)
    new_bs += pack ('uint:1',sps_sub_layer_ordering_info_present_flag)
#   for (i = (sps_sub_layer_ordering_info_present_flag ? 0 : sps.max_sub_layers_minus1); i <= sps.max_sub_layers_minus1; i++)
    if sps_sub_layer_ordering_info_present_flag :
            new_bs += pack ('ue',sps_max_dec_pic_buffering_minus1)
            new_bs += pack ('ue',sps_max_num_reorder_pics)
            new_bs += pack ('ue',sps_max_latency_increase_plus1)
    new_bs += pack ('ue',log2_min_luma_coding_block_size_minus3)
    new_bs += pack ('ue',log2_diff_max_min_luma_coding_block_size)
    new_bs += pack ('ue',log2_min_luma_transform_block_size_minus2)
    new_bs += pack ('ue',log2_diff_max_min_luma_transform_block_size)
    new_bs += pack ('ue',max_transform_hierarchy_depth_inter)
    new_bs += pack ('ue',max_transform_hierarchy_depth_intra)
    new_bs += pack ('uint:1',scaling_list_enabled_flag)
    #
    new_bs += pack ('uint:1',amp_enabled_flag)
    new_bs += pack ('uint:1',sample_adaptive_offset_enabled_flag)
    new_bs += pack ('uint:1',pcm_enabled_flag)
    if pcm_enabled_flag :
        new_bs += pack ('uint:4',pcm_sample_bit_depth_luma_minus1)
        new_bs += pack ('uint:4',pcm_sample_bit_depth_chroma_minus1)
        new_bs += pack ('ue',log2_min_pcm_luma_coding_block_size_minus3)
        new_bs += pack ('ue',log2_diff_max_min_pcm_luma_coding_block_size)
        new_bs += pack ('uint:1',pcm_loop_filter_disabled_flag)
    new_bs += pack ('ue',num_short_term_ref_pic_sets)


    if num_short_term_ref_pic_sets :
        for i in range (num_short_term_ref_pic_sets) :
            if i != 0 :
                new_bs += pack ('uint:1',inter_ref_pic_set_prediction_flag)

        
        
            if  not 'inter_ref_pic_set_prediction_flag' in globals() :
                """     
                if i == num_short_term_ref_pic_sets :
                    new_bs += pack ('ue',delta_idx_minus1)
                new_bs += pack ('uint:1', delta_rps_sign)
                new_bs += pack ('ue',abs_delta_rps_minus1)
                for j in range (NumDeltaPocs[i - (delta_idx_minus1 +1)]) :
                    new_bs += pack ('uint:1', used_by_curr_pic_flag[j])
                    if used_by_curr_pic_flag[j] :
                        new_bs += pack ('uint:1',use_delta_flag[j])
        
            else :
                """    
                new_bs += pack ('ue',num_negative_pics)
                new_bs += pack ('ue',num_positive_pics)
                new_bs += [pack ('ue',delta_poc_s0_minus1[_]) for _ in range (num_negative_pics)]
                new_bs += [pack ('uint:1',used_by_curr_pic_s0_flag[_]) for _ in range (num_negative_pics)]
                new_bs += [pack ('ue',delta_poc_s1_minus1[_]) for _ in range(num_positive_pics)]
                new_bs += [pack ('uint:1',used_by_curr_pic_s1_flag[_]) for _ in range(num_positive_pics)]
        

    new_bs += pack ('uint:1',long_term_ref_pics_present_flag)
    if long_term_ref_pics_present_flag :
        new_bs += pack ('ue',num_long_term_ref_pics_sps)
    new_bs += pack ('uint:1',sps_temporal_mvp_enabled_flag)
    new_bs += pack ('uint:1',strong_intra_smoothing_enabled_flag)
    new_bs += pack ('uint:1',vui_parameters_present_flag)
# VUI VP pack Section
    if vui_parameters_present_flag :
       new_bs += pack ('uint:1',vp.aspect_ratio_info_present_flag)
       if vp.aspect_ratio_info_present_flag :
            new_bs += pack ('uint:8',vp.aspect_ratio_idc)
            if vp.aspect_ratio_idc == 255 :
                new_bs += pack ('uint:16',vp.sar_width)
                new_bs += pack ('uint:16',vp.sar_height)
       new_bs += pack ('uint:1',vp.overscan_info_present_flag)
       if vp.overscan_info_present_flag :
           new_bs += pack ('uint:1',vp.overscan_appropriate_flag)
       new_bs += pack ('uint:1',vp.video_signal_type_present_flag)
       if vp.video_signal_type_present_flag :
           new_bs += pack ('uint:3',vp.video_format)
           new_bs += pack ('uint:1',vp.video_full_range_flag)
           new_bs += pack ('uint:1',vp.colour_description_present_flag)
           if vp.colour_description_present_flag :
               new_bs += pack ('uint:8',vp.colour_primaries)
               new_bs += pack ('uint:8',vp.transfer_characteristics)
               new_bs += pack ('uint:8',vp.matrix_coeffs)
       new_bs += pack ('uint:1',vp.chroma_loc_info_present_flag)
       if vp.chroma_loc_info_present_flag :
           new_bs += pack ('ue',vp.chroma_sample_loc_type_top_field)
           new_bs += pack ('ue',vp.chroma_sample_loc_type_bottom_field)
       new_bs += pack ('uint:1',vp.neutral_chroma_indication_flag)
       new_bs += pack ('uint:1',vp.field_seq_flag)
       new_bs += pack ('uint:1',vp.frame_field_info_present_flag)
       new_bs += pack ('uint:1',vp.default_display_window_flag)
       if vp.default_display_window_flag :
           new_bs += pack ('ue',vp.def_disp_win_left_offset)
           new_bs += pack ('ue',vp.def_disp_win_right_offset)
           new_bs += pack ('ue',vp.def_disp_win_top_offset)
           new_bs += pack ('ue',vp.def_disp_win_bottom_offset)
       new_bs += pack ('uint:1',vp.vui_timing_info_present_flag)
       if vp.vui_timing_info_present_flag :
           new_bs += pack ('uint:32',vp.vui_num_units_in_tick)
           new_bs += pack ('uint:32',vp.vui_time_scale)
           new_bs += pack ('uint:1',vp.vui_poc_proportional_to_timing_flag)
           if vp.vui_poc_proportional_to_timing_flag :
               new_bs += pack ('ue',vp.vui_num_ticks_poc_diff_one_minus1)
           new_bs += pack ('uint:1',vp.vui_hrd_parameters_present_flag)
           """
           if( vui_hrd_parameters_present_flag )
           hrd_parameters( 1, sps_max_sub_layers_minus1 )
           """
       new_bs += pack ('uint:1',vp.bitstream_restriction_flag)
       if vp. bitstream_restriction_flag :
           new_bs += pack ('uint:1',vp.tiles_fixed_structure_flag)
           new_bs += pack ('uint:1',vp.motion_vectors_over_pic_boundaries_flag)
           new_bs += pack ('uint:1',vp.restricted_ref_pic_lists_flag)
           new_bs += pack ('ue',vp.min_spatial_segmentation_idc)
           new_bs += pack ('ue',vp.max_bytes_per_pic_denom)
           new_bs += pack ('ue',vp.max_bits_per_min_cu_denom)
           new_bs += pack ('ue',vp.log2_max_mv_length_horizontal)
           new_bs += pack ('ue',vp.log2_max_mv_length_vertical)

    new_bs += pack ('uint:1',sps_extension_present_flag)
    if sps_extension_present_flag :
        new_bs += pack ('uint:1',sps_range_extension_flag)
        new_bs += pack ('uint:1',sps_multilayer_extension_flag)
        new_bs += pack ('uint:1',sps_3d_extension_flag)
        new_bs += pack ('uint:1',sps_extension_5bits)

    new_bs += pack ('uint:1',tb.rbsp_stop_one_bit)
    while len(new_bs) < t.pos :
        new_bs += pack ('uint:1',tb.rbsp_alignment_zero_bit)

#    self.sub_layer_profile_present_flag = []
#    self.sub_layer_level_present_flag = []
#    for i in range(maxNumSubLayersMinus1):
#        self.sub_layer_profile_present_flag.append(t.read('uint:1'))
#        self.sub_layer_level_present_flag.append(t.read('uint:1'))
    
    pre_new_bs = pack ('uint:1,2*uint:6,uint:3', forbidden_zero_bit,nal_unit_type,nuh_layer_id,nuh_temporal_id_plus1)
    new_bs.replace ('0x0000','0x000003',bytealigned=True)
    new_bs = pre_new_bs + new_bs + '0x00'
    nal_t_rep = nal_t[24:]
    repl = s.replace (nal_t_rep,new_bs, bytealigned=True)
    print ('Made modified SPS NALu - OK')
    if sei_ok :
        s.prepend (new_sei_string)
        print ('New SEI prepended')
    print ('Writing new stream...')
    s.tofile(o)
    progr = chunk
    while True:
        s = F.read(chunk)
        o.write(s)
        if progr < os.path.getsize(args.infile):
            print ('\rProgress ',int(round((progr/os.path.getsize(args.infile))*100)),'%',end='')
        progr = progr + chunk
        if not s:
            break
    o.close()
    F.close()
    print ('\rProgress: 100 %')
    print ('=====================')
    print ('Done!')
    print ('')
    print ('File ',args.outfile,' created.')
    sys.exit()
if __name__ == "__main__":
    main()
