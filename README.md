Model importer for Monster Hunter (PS2) games.

Made for Blender 4.0.

Note: this importer is highly experimental and in dire need of a full rewrite.

# Features

* Model Import (_amh.bin files)
    * Vertex Color Import
    * Material Import
    * Weights Import
    * UV Import
* Texture Import
    * For MH1 and MHG, you can leave the texture path empty to attempt to autoload from a _tex.bin file.
    * For MH1, MHG, MH2 and Frontier, you can specify a folder with PNG textures instead.

# Usage

## Installation

Click [Here](https://github.com/GReinoso96/ps2-amh-importer/archive/refs/heads/main.zip) and download the file.

In Blender, go to `Edit->Preferences->Addons->Install...` and install the file you just downloaded.

## General notes

For Stage models, tick the "Ignore Additive" option in the model import window, and keep "Delta Rotation" ticked to make the model appear upright.

For other models, if you find they import with broken transparency, try again and tick the "Ignore Additive" option.

## Monster Hunter and Monster Hunter G (PS2)

First, grab [AFS Packer](https://github.com/MaikelChan/AFSPacker) and [PZZ Compressor](https://github.com/infval/pzzcompressor_jojo) and put them in a folder.

Next, open the game ISO with 7zip or by mounting it.

Copy the file named "AFS_DATA.AFS" into the folder containing AFS Packer and PZZ Compressor, then open a command line interface and navigate to that folder (you can also click on the navigation bar of the file browser, then type CMD and press enter).

Run the following command

`afspacker -e AFS_DATA.AFS data data.txt`

When it is finished, you'll see a new folder named "data", inside you'll find all of the game's assets.

For models, you want the files that end in _amh.bin, and for textures, the ones that end in _tex.bin.

### How to mass-prepare files

Copy all the _amh files and their corresponding _tex files to a new folder named "models" outside of the "data" folder, then run the next command in the command line used previously:

`for %i in (models\*.bin) do pzzcomp_jojo -d %i %i`

After this is done, all model files will have been decompressed and are now ready for use with the plugin.

## Monster Hunter 2

Follow the same procedure, except the data file is named DATA.BIN instead of AFS_DATA.AFS.

`afspacker -e DATA.BIN data data.txt`

After this, when you go inside the folder you'll only see 2 files, copy the first one to the prevous folder and run:

`afspacker -e [filename] assets assets.txt`

Replace `[filename]` with the name of the file you just copied (remove the [] brackets).

Inside this new assets folder you'll find the model files.

Do note that texture importing does not work with MH2's _tex files, you need to disable texture loading or find a way to unpack the TM2 files from them into PNG.

## Monster Hunter Frontier

Use [ReFrontier](https://github.com/mhvuze/refrontier) (You may find a compiled build by googling) on the files you want to unpack.

Use the fmod import option to import .fmod files, refrontier will automatically unpack textures so you can copy the path to the corresponding textures folder to use with the plugin.