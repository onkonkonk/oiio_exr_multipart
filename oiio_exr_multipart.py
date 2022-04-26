#!/usr/bin/python
 
import os
import shutil
import sys
import subprocess
from itertools import groupby

import OpenImageIO as oiio
from OpenImageIO import ImageOutput, ImageBuf, ImageBufAlgo


aov_defs = {
    # 
    # AOV :  ["siname", (chnames), "bitdepth", si_index] 
    #  

    # OCTANE
    "AO" : ["AO", ("Y",), "half"],  
    "Beauty" : ["rgba", ("R", "G", "B", "A"), "half", 0],
    "LiDir" : ["light_direction", ("X", "Y", "Z"), "half"],
    "DeMain" : ["rgba_denoised", ("R", "G", "B", "A"), "half"],
    "Dif" : ["diffuse", ("R", "G", "B", "A"), "half"],
    "DifD" : ["diffuse_direct", ("R", "G", "B"), "half"],
    "DifF" : ["diffuse_filter", ("R", "G", "B"), "half"],
    "DifI" : ["diffuse_indirect", ("R", "G", "B"), "half"],
    "Emit" : ["emitters", ("R", "G", "B"), "half"],
    "GN" : ["geometric_normals", ("X", "Y", "Z"), "half"],
    "Irr" : ["irradiance", ("R", "G", "B"), "half"],
    "Main" : ["rgba", ("R", "G", "B", "A"), "half", 0],
    "MV" : ["motion", ("u", "v", "u", "v"), "float"],
    "Noise" : ["noise", ("R", "G", "B", "A"), "half"],
    "Pos" : ["pos", ("X", "Y", "Z"), "float"],
    "Post" : ["post_process", ("R", "G", "B"), "half"],
    "Ref" : ["reflection", ("R", "G", "B"), "half"],
    "RefD" : ["reflection_direct", ("R", "G", "B"), "half"],
    "RefI" : ["reflection_indirect", ("R", "G", "B"), "half"],
    "RflF" : ["reflection_filter", ("R", "G", "B"), "half"],
    "Shdw" : ["shadow", ("R", "G", "B"), "half"],
    "ShN" : ["shadow_normal", ("X", "Y", "Z"), "half"],
    "Tang" : ["texture_tangent", ("X", "Y", "Z"), "half"],
    "TN" : ["tangent_normal", ("X", "Y", "Z"), "half"],
    "Z" : ["depth", ("Z"), "float", 1],
    "DeDifD" : ["diffuse_direct_denoised", ("R", "G", "B", "A"), "half"],
    "DeDifI" : ["diffuse_indirect_denoised", ("R", "G", "B", "A"), "half"],
    "DeRefD" : ["reflection_direct_denoised", ("R", "G", "B", "A"), "half"],
    "DeRefI" : ["reflection_indirect_denoised", ("R", "G", "B", "A"), "half"],
    "DeRem" : ["remainder_denoised", ("R", "G", "B", "A"), "half"],
    
    
    # CYCLES
    "rgba" : ["rgba", ("R", "G", "B", "A"), "half", 0],
    "depth" : ["depth", ("Y",), "float", 1], 
    "pos" : ["pos", ("X", "Y", "Z"), "float"],
    "DifDir" : ["DifDir", ("R", "G", "B", "A"), "half"],
    "DifInd" : ["DifInd", ("R", "G", "B", "A"), "half"],
    "DifCol" : ["DifCol", ("R", "G", "B", "A"), "half"],
    "GlossDir" : ["GlossDir", ("R", "G", "B", "A"), "half"],
    "GlossInd" : ["GlossInd", ("R", "G", "B", "A"), "half"],
    "GlossCol" : ["GlossCol", ("R", "G", "B", "A"), "half"],
    "TransDir" : ["TransDir", ("R", "G", "B", "A"), "half"],
    "TransInd" : ["TransInd", ("R", "G", "B", "A"), "half"],
    "TransCol" : ["TransCol", ("R", "G", "B", "A"), "half"],
    
}

# FOR NOW, EXCLUDE CRYPTOMATTE LAYERS 
# TO DO: Correctly merge Cryptomatte metadata 
aov_exclude = ["cm-", "crypto", "Crypto"]


############################






def construct_channelnames(aov_name):
    channelnames = []
    for c in aov_defs[aov_name][1]:
        chname = aov_defs[aov_name][0] + "." + c
        channelnames.append(chname)
    return channelnames


def output_multipart(file, specs, bufs):
    # Create new output file and open
    out = ImageOutput.create(file)
    out.open(file, specs)
    # Write subimages to output file    
    for s in range(len(bufs)):
        print("Writing channels", bufs[s].spec().channelnames)
        if s > 0:
            out.open(file, specs[s], "AppendSubimage")
        bufs[s].write(out)
    out.close()


def delete_originals(del_files):
    for file in del_files:
            os.remove(dir_in + file)
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
    elif os.path.exists(inp_out) : 
        dir_out = inp_out
        return dir_out
    else : 
        raise Exception('Output directory does not exist.')
    


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



def query_keep_files(default_keep_files):
    global keep_files
    keep_files = default_keep_files
    while ( res:=input("Do you want to keep the original files? (y/n)").lower() ) not in {"y", "n"}: 
        pass
    if res=='y':
        keep_files=True
    elif res=='n':
        keep_files=False


def copy_crypto(cryptos):    
    cryptomattes = [s for s in cryptos if any(xs in s for xs in aov_exclude)]
    for c in cryptomattes:
        src_dir = str(dir_in) + str(c)
        dst_dir = str(dir_out) + str(c)
        print("Copying cryptomattes:" + str(c))
        shutil.copy(src_dir, dst_dir)
        
        
    '''
    # Get Cryptomatte attribs
    for i in range(len(spec.extra_attribs)) :
        if "cryptomatte" in spec.extra_attribs[i].name:
            print(spec.extra_attribs[i].name)
    '''

###################################





def main():

    get_inputs("./in/")
    get_outputs("./out/")
    get_framebase(1001)
    
    files = os.listdir(dir_in)

    query_keep_files(True)
    

    # Sort files by frame number
    frame_mask = lambda a: a.split(".")[-2]
    frames = sorted(files, key = frame_mask)

    # Group by frame number - create separate lists for all frames
    aovs_sorted = [list(i) for j, i in groupby(frames, frame_mask)]

    # LOOP OVER ALL FRAMES
    for f in range(len(aovs_sorted)):
        # Create string for padded frame number
        fn = str(framebase + f)
        frame_num = fn.zfill(max(4, len(fn)))

        # File Output: out_dir + base name + frame number + extension
        basename = aovs_sorted[f][0].split(".")[0]
        out_filename = dir_out + basename + "." + frame_num + ".exr"

        # Initialize empty lists to hold subimage infos
        buf_all, specs_all, img_all, buf_sorted, specs_sorted = [], [], [], [], []
        channel_index = [(0,), (0, 1), (0, 1, 2), (0, 1, 2, 3)]

        # Set offset for sorting subimages (0, 1 definded in aov_defs)
        index_offset = 2

        
        print("\nMerging frame", frame_num +"\n")
        # LOOP OVER ALL AOVS PER FRAME
        for file in aovs_sorted[f]:
            aov = file.split(".")[-3]
            
            # Print error message if AOV not defined in aov_defs
            if not aov_defs.get(aov):  
                print("Channel >>", aov, "<< not defined. Check for correct entries in aov_defs") 
            
            # Exclude Cryptomattes
            elif bool([e for e in aov_exclude if(e in aov)]) == False :
                img = dir_in + file
                img_all.append(img)
                            
                buf = ImageBuf(img)
                           
                chnames = construct_channelnames(aov)
                chnames = tuple(chnames)
                buf = ImageBufAlgo.channels(buf, channel_index[len(aov_defs[aov][1]) -1], chnames)

                # Convert bit depth for half float aovs
                if aov_defs[aov][2] == "half":
                    buf = ImageBufAlgo.copy(buf, convert="half")
                
                buf_all.append(buf)   

                spec = buf.spec()
                specs_all.append(spec)

                try : 
                    si_index = aov_defs[aov][3]
                except : 
                    index_offset+=1
                    si_index = index_offset
                finally :
                    specs_sorted.insert(si_index, spec)


    
        # Convert lists to tuples, as ImageOutput expects tuples
        buf_all, specs_all, img_all, buf_sorted = tuple(buf_all), tuple(specs_all), tuple(img_all), tuple(buf_sorted)

        # EXPORT MULTIPART FILE
        output_multipart(out_filename, specs_sorted, buf_sorted)
    
    copy_crypto(files)

    if keep_files == False :
        delete_originals(files)
        return

def debug_export_si_order(file):
    si = ImageBuf(file).nsubimages
    for i in range(si) : 
        print("SubImage " + str(i) + ": " + str(ImageBuf(file, i, 0).spec().channelnames))
    print("\nZ-Channel: " + str(ImageBuf(file).spec().z_channel))
    print("Alpha Channel: " + str(ImageBuf(file).spec().alpha_channel) + "\n")



if __name__ == "__main__" :

    main()
    #debug_export_si_order("./out/Intro_shot01_preview_v3.1001.exr")
    sys.exit()




'''
GENERAL TO DOs: 


- add Blender channelist
- handle Cryptomattes?

- add Multichannel Support: 
    - split channelgroups to ImageBufs
    - Blender: Split ViewLayers?
    - rename, sort

- Blender shuffle pos Y/Z ?


'''