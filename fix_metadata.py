#!/usr/bin/env python3

import subprocess
from glob import glob
import argparse
import os
from pathlib import Path
import shutil
import sys


def sh(args):
    p = subprocess.run(args)
    p.check_returncode()

def p(s):
    print(s, file=sys.stderr)


def run_mattwilson1024_google_photos_exif(albumdir, outdir, errdir, check_errdir=True):
    os.makedirs(albumdir, exist_ok=True)
    os.makedirs(outdir, exist_ok=True)
    os.makedirs(errdir, exist_ok=True)

    sh(
        [
            "yarn", "start",
            "--inputDir", albumdir,
            "--outputDir", outdir,
            "--errorDir", errdir,
        ]
    )

    if not check_errdir:
        return

    errdir_not_empty = len(glob(f"{errdir}/*")) > 0
    if errdir_not_empty:
        sh(
            [
                "exiftool", "-all=", "-tagsfromfile", "@",
                "-all:all", "-unsafe", "-icc_profile", errdir,
            ]
        )
        # rerun analysis
        run_mattwilson1024_google_photos_exif(
            albumdir, outdir, errdir, check_errdir=False
        )

def process_albums(rootdir):
    globstr = f"{rootdir}/Albums/*/"
    albums = glob(globstr)
    if len(albums) == 0:
        p(f"WARN: No albums found at {globstr}")

    for albumdir in albums:
        p(f"Processing album {albumdir}...")
        album_name = Path(albumdir).stem
        outdir = f"{rootdir}/AlbumsProcessed/{album_name}"
        errdir = f"{rootdir}/AlbumsError/{album_name}"
        run_mattwilson1024_google_photos_exif(albumdir, outdir, errdir)

def process_photos(rootdir):
    # also run the exif fix for the Photos
    p(f"Processing photos...")
    albumdir = f"{rootdir}/Photos"
    outdir = f"{rootdir}/PhotosProcessed"
    errdir = f"{rootdir}/PhotosError"

    run_mattwilson1024_google_photos_exif(albumdir, outdir, errdir)
    
def _restructure_if_needed(folders, target_dir):
    if os.path.exists(target_dir) and len(glob(f"{target_dir}/*")) > 0:
        p(f"{target_dir} exists and is non-empty, assuming no further restructuring is needed")
        return

    os.makedirs(target_dir, exist_ok=True)

    if len(folders) == 0:
        p(f"Warning: no folders were moved to {target_dir}")

    for folder in folders:
        shutil.move(folder, target_dir)

    p(f"Restructured {len(folder)} folders")
    

def restructure_folders_if_needed(rootdir):
    # before
    # $rootdir/My Album 1
    # $rootdir/My Album 2
    # $rootdir/Photos from 2008

    # after
    # $rootdir/Albums/My Album 1
    # $rootdir/Albums/My Album 2
    # $rootdir/Photos/Photos from 2008

    photos_dir = f"{rootdir}/Photos/"

    # move the "Photos from $YEAR" directories to Photos/
    _restructure_if_needed(glob(f"{rootdir}/Photos from */"), photos_dir)

    # move everything else to Albums/, so we end up with two top-level folders
    everything_except_photos_dir = set(glob(f"{rootdir}/*/")) - set([photos_dir])

    _restructure_if_needed(everything_except_photos_dir, f"{rootdir}/Albums")


def main(rootdir):
    # at least in my takeout, the Takeout folder contains a subfolder
    # Takeout/Google Foto
    # rootdir refers to that subfolder

    rootdir = glob(f"{rootdir}/Google*/")[0].rstrip('/')
    restructure_folders_if_needed(rootdir)

    process_albums(rootdir)
    process_photos(rootdir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('rootdir', help="Path to the Takeout/ folder")
    args = parser.parse_args()
    main(args.rootdir)
