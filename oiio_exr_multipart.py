#!/usr/bin/python
 
from genericpath import exists
import os
import shutil
import sys
from itertools import groupby
from unicodedata import name

from OpenImageIO import ImageOutput, ImageBuf, ImageBufAlgo



aov_defs = {
    # 
    # "AOV" :  ["siname", (chnames), "bitdepth", si_index] 
    #  

    # GENERAL
    "AO" : ["AO", ("Y",), "half", "data"],  
    "Beauty" : ["rgba", ("R", "G", "B", "A"), "half", "", 0],
    "Noise" : ["noise", ("R", "G", "B", "A"), "half", "data"],
    "Z" : ["depth", ("Z"), "float", "data"],
    "Emit" : ["emission", ("R", "G", "B"), "half", "data"],
     
    
    # OCTANE
    "LiDir" : ["light_direction", ("X", "Y", "Z"), "half", "data"],
    "DeMain" : ["rgba_denoised", ("R", "G", "B", "A"), "half", "data"],
    "DeMainNV" : ["rgba_nv", ("R", "G", "B", "A"), "half", ""],
    "Dif" : ["diffuse", ("R", "G", "B", "A"), "half", ""],
    "DifD" : ["diffuse_direct", ("R", "G", "B"), "half", ""],
    "DifF" : ["diffuse_filter", ("R", "G", "B"), "half", ""],
    "DifI" : ["diffuse_indirect", ("R", "G", "B"), "half", ""],
    "GN" : ["geometric_normals", ("X", "Y", "Z"), "float", "data"],
    "Irr" : ["irradiance", ("R", "G", "B"), "half", ""],
    "Main" : ["rgba", ("R", "G", "B", "A"), "half", "", 0],
    "MV" : ["motion", ("u", "v", "u", "v"), "float", "data"],
    "Pos" : ["pos", ("X", "Y", "Z"), "float", "data"],
    "Post" : ["post_process", ("R", "G", "B"), "half", ""],
    "Ref" : ["reflection", ("R", "G", "B"), "half", ""],
    "RefD" : ["reflection_direct", ("R", "G", "B"), "half", ""],
    "RefI" : ["reflection_indirect", ("R", "G", "B"), "half", ""],
    "RflF" : ["reflection_filter", ("R", "G", "B"), "half", ""],
    "Shdw" : ["shadow", ("R", "G", "B"), "half", ""],
    "ShN" : ["shadow_normal", ("X", "Y", "Z"), "float", "data"],
    "Tang" : ["texture_tangent", ("X", "Y", "Z"), "half", "data"],
    "TN" : ["tangent_normal", ("X", "Y", "Z"), "float", "data"],
    "Tran" : ["transmission", ("R", "G", "B"), "half", "data"],
    "SSS" : ["sss", ("R", "G", "B"), "half", ""],
    "DeDifD" : ["diffuse_direct_denoised", ("R", "G", "B", "A"), "half", ""],
    "DeDifI" : ["diffuse_indirect_denoised", ("R", "G", "B", "A"), "half", ""],
    "DeRefD" : ["reflection_direct_denoised", ("R", "G", "B", "A"), "half", ""],
    "DeRefI" : ["reflection_indirect_denoised", ("R", "G", "B", "A"), "half", ""],
    "DeRem" : ["remainder_denoised", ("R", "G", "B", "A"), "half", ""],
    "DeVol" : ["volume_denoised", ("R", "G", "B",), "half", ""],
    "volume" : ["volume", ("R", "G", "B"), "half", ""],
    "Vol" : ["volume", ("R", "G", "B"), "half", ""],   
    "VolZFr" : ["volume_depth", ("Y",), "float", "data"],
    "DeVolE" : ["volume_emission_denoised", ("R", "G", "B",), "half", "data"],

    "Post" : ["post", ("R", "G", "B", "A"), "half", ""],

    "Li2" : ["light2", ("R", "G", "B"), "half", ""],



    # CYCLES
    "Composite" : ["rgba", ("R", "G", "B", "A"), "half", "", 0],
    "rgba" : ["rgba", ("R", "G", "B", "A"), "half", "", 0],
    "Depth" : ["depth", ("Z",), "float", "data"], 
    "Position" : ["pos", ("X", "Y", "Z"), "float", "data"],
    "Normal" : ["normal", ("X", "Y", "Z"), "float", "data"],
    "DifDir" : ["DifDir", ("R", "G", "B"), "half", ""],
    "DifInd" : ["DifInd", ("R", "G", "B"), "half", ""],
    "DifCol" : ["DifCol", ("R", "G", "B"), "half", ""],
    "GlossDir" : ["GlossDir", ("R", "G", "B"), "half", ""],
    "GlossInd" : ["GlossInd", ("R", "G", "B"), "half", ""],
    "GlossCol" : ["GlossCol", ("R", "G", "B"), "half", ""],
    "TransDir" : ["TransDir", ("R", "G", "B"), "half", ""],
    "TransInd" : ["TransInd", ("R", "G", "B"), "half", ""],
    "TransCol" : ["TransCol", ("R", "G", "B"), "half", ""],
    "VolumeDir" : ["VolumeDir", ("R", "G", "B"), "half", ""],
    "VolumeCol" : ["VolumeCol", ("R", "G", "B"), "half", ""],
    "Vector" : ["motion", ("X", "Y", "Z", "W"), "float", "data"], 
    "Shadow" : ["shadow", ("R", "G", "B"), "half", ""],
    "ShadowCatcher" : ["ShadowCatcher", ("R", "G", "B"), "half", ""],
    "UV" : ["UV", ("A", "U", "V"), "float", "data"],
    
    "Denoising Albedo" : ["Denoising Albedo", ("R", "G", "B"), "half", "data"],
    "Denoising Normal" : ["Denoising Normal", ("R", "G", "B"), "float", "data"],
    "Denoising Depth" : ["Denoising Depth", ("Z"), "float", "data"],

    "Mist" : ["mist", ("Z"), "float", "data"],
    
    "Noisy Image" : ["Noisy Image", ("R", "G", "B"), "half", ""],
    "Noisy Shadow Catcher" : ["Noisy Shadow Catcher", ("R", "G", "B"), "half", ""],



}

# Extra AOVs will simply be copied to output dir
aov_extras = ["cm-Ii", "cm-On", "cm-Mn", "cm-Mnn", "cm-UID", "crypto", "Crypto", "Util", "util", "Deep"]



############################


def construct_channelnames(aov_name):
    channelnames = []
    for c in aov_defs[aov_name][1]:
        chname = aov_defs[aov_name][0] + "." + c
        channelnames.append(chname)
    return channelnames


def output_multipart(file, specs, bufs):
    

    print("\nWriting to file", file, "\n")
    # Create new output file and open
    dst = os.path.dirname(file)
    if not exists(dst) : 
            os.makedirs(dst)
    
    out = ImageOutput.create(file)
    out.open(file, specs)

    # Write subimages to output file      
    for s in range(len(bufs)):
        print("Writing channels:", bufs[s].spec().channelnames)
        if s > 0:
            out.open(file, specs[s], "AppendSubimage")
        bufs[s].write(out)
    out.close()
    

def query_delete_files():
    global del_files
    del_files = False
    while ( r:=input("Delete original files? (y/n)").lower() ) not in {"y", "n"}: 
        pass
    if r=='y':
        del_files=True
    elif r=='n':
        del_files=False


def delete_originals(del_origs):
    if del_files == True : 
        for file in del_origs:
            print("\nDeleting file", file)
            os.remove(file)
    return


def get_inputs(default_dir_in):
    global dir_in
    inp_in = str(input("Enter input directory (default: " + str(default_dir_in) + "):")).strip()
    if inp_in == '' :
        dir_in = default_dir_in
        return dir_in
    elif os.path.exists(inp_in) :
        dir_in = inp_in
        return dir_in
    else :
        raise Exception('Input directory does not exist.')


def get_outputs(default_dir_out): 
    global dir_out
    inp_out = str(input("Enter output directory (default: " + str(default_dir_out) + "):")).strip()
    if inp_out == '' :
        dir_out = default_dir_out
        return dir_out
    else :
        if not os.path.exists(inp_out) :
            os.mkdir(inp_out)
        dir_out = inp_out
        return dir_out


def get_framebase(default_framebase):
    global framebase
    framebase = default_framebase
    inp_framebase = input("Enter base frame (default: " + str(default_framebase) +"):")
    if inp_framebase == '' :
        return framebase
    elif isinstance(int(inp_framebase), int) :
        framebase = int(inp_framebase)
        return framebase
    else :
        raise Exception("Please enter a valid number as framebase")



def copy_extras(extras):    
    extra_aov = [s for s in extras if any(xs in s for xs in aov_extras)]
    for c in extra_aov:
        src_dir = str(c)
        dst_dir = str(dir_out) + os.path.relpath(os.path.join(c), os.path.join(dir_in))
        print("\nCopying extras: " + str(c))
        if not exists(os.path.dirname(dst_dir)) : 
            os.makedirs(os.path.dirname(dst_dir))
        shutil.copy(src_dir, dst_dir)

def parse_filename(n) :
        return lambda a: a.split(".")[n]
    
###################################

def main():
    os.chdir(os.getcwd())
    '''
    
    INPUT HANDLING
    
    Input expects files named by convention: < project.aov.####.exr >
    

    '''
    
    get_inputs("./in/")
    get_outputs("./out/")
    query_delete_files()
        
    parse_filetype = parse_filename(-1)
    parse_frame = parse_filename(-2)
    parse_aov = parse_filename(-3)
    parse_basename = parse_filename(-4)

    files = []

    for r, d, f in os.walk(dir_in):
        for q in range(len(f)) :
            if not f[q].startswith('.') and not f[q].startswith('_') :
                file = os.path.join(r, f[q])
                files.append(file)




    # Create cascading lists by filename and framenumber
    sort_by_name = sorted(files, key = parse_basename)
    
    
    name_groups = [list(i) for j, i in groupby(sort_by_name, parse_basename)]
    frame_groups = []

    for v in range(len(name_groups)) : 
        sort_by_frame = sorted(name_groups[v], key = parse_frame)
        frame_group = [list(i) for j, i in groupby(sort_by_frame, parse_frame)]
        frame_groups.append(frame_group)
    
    
    '''
    DATA MERGE

    Merges AOVs from Single Channel EXRs to Multipart EXRs as defined in aov_defs
    Outputs multipars EXRs to < project.beauty.####.exr >,< project.data.####.exr >, ...
    
    '''
    
    # LOOP OVER ALL FILENAMES
    for f in range(len(frame_groups)) : 
        
        basename = parse_basename(os.path.relpath(frame_groups[f][0][0], os.path.abspath(dir_in)))
        filetype = parse_filetype(frame_groups[f][0][0])


        # LOOP OVER ALL FRAMES
        for v in range(len(frame_groups[f])):
            index_offset = 1
            
            current_files = frame_groups[f][v]

            frame =  parse_frame(current_files[0])
            file_out_beauty = dir_out + basename + ".beauty." + frame + "." + filetype
            file_out_data = dir_out + basename + ".data." + frame + "." + filetype

            print("\nPreparing frame", frame)

            
            # Initialize empty lists to hold subimage infos
            buf_beauty, specs_beauty, img_all = [], [], [] 
            buf_beauty_sorted, specs_beauty_sorted = [], []
            buf_data, specs_data = [], []
            channel_index = [(0,), (0, 1), (0, 1, 2), (0, 1, 2, 3)]

            
            #Interate for all AOVs
            for file in current_files : 
                aov = parse_aov(file)
            
            
                # Print error message if AOV not defined in aov_defs
                if not aov_defs.get(aov) and not aov in aov_extras:
                        print(aov, ": Channel not defined. Undefined channels will be ignored!")
                        input("Press any key to continue or Ctrl+C to exit")
                
                elif bool([e for e in aov_extras if(e in aov)]) == False :
                    
                    aov_params =  aov_defs[aov]
                    
                    # Create ImageBuf for current AOV
                    img = file
                    buf = ImageBuf(img)
        
                    chnames = construct_channelnames(aov)
                    chnames = tuple(chnames)
                    
                    buf = ImageBufAlgo.channels(buf, channel_index[len(aov_params[1])-1], chnames)
                    
                    # Convert bit depth as defined in aov_defs
                    if aov_params[2] == "half":
                        buf = ImageBufAlgo.copy(buf, convert="half")

                    
                    # Add ImageBuf and ImageSpec to their respective lists for "data" and "beauty" passes
                    if aov_params[3] == "data":
                        buf_data.append(buf)   
                        spec = buf.spec()
                        specs_data.append(spec)

                    else:
                        buf_beauty.append(buf)   
                        spec = buf.spec()
                        specs_beauty.append(spec)
                        try : 
                            si_index = aov_params[4]
                        except : 
                            index_offset+=1
                            si_index = index_offset
                        finally :
                            buf_beauty_sorted.insert(si_index, buf)
                            specs_beauty_sorted.insert(si_index, spec)

                elif bool([e for e in aov_extras if(e in aov)]) == True : 
                                        
                    copy_extras(current_files) 

            # Convert lists to tuples, as ImageOutput expects tuples
            buf_beauty, specs_beauty, buf_beauty_sorted = tuple(buf_beauty), tuple(specs_beauty), tuple(buf_beauty_sorted)
            buf_data, specs_data = tuple(buf_data), tuple(specs_data)

            output_multipart(file_out_beauty, specs_beauty_sorted, buf_beauty_sorted)
            output_multipart(file_out_data, specs_data, buf_data)

            

    '''
    
    ADDITIONAL FILE HANDLING

    Simply copy extra files to output destination if defined in extra_aovs
    Delete original files if specified

    '''

    
    delete_originals(files)
    



if __name__ == "__main__" :

    main()
    sys.exit()