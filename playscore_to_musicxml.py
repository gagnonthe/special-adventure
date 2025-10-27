#!/usr/bin/env python3
"""
playscore_to_musicxml.py

Unified utility to extract/convert a single `.playscore` or merge multiple
`.playscore` archives into one MusicXML. This file combines the previous
`playscore_to_musicxml.py` and `playscore_merge_to_musicxml.py` into a single
CLI with options to process single files or multiple files with a `--merge`
flag.

Usage examples:
  # single file -> auto-named output
  python playscore_to_musicxml.py input.playscore

  # multiple files -> individual outputs
  python playscore_to_musicxml.py a.playscore b.playscore

  # merge multiple files into one MusicXML
  python playscore_to_musicxml.py a.playscore b.playscore --merge -o merged.musicxml

Options:
  --merge      Merge parts from all inputs into a single MusicXML output.
  -o/--output  Output file path (for single conversion or merged output).
  --overwrite  Overwrite existing outputs.
  --verbose    Print more information.

Requirements: music21 for MIDI parsing/conversion when needed.
"""

import argparse
import sys
import zipfile
import tempfile
import os
from xml.etree import ElementTree as ET

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
except Exception:
    tk = None
    filedialog = None
    messagebox = None


def is_musicxml_bytes(b: bytes) -> bool:
    try:
        root = ET.fromstring(b.decode('utf-8', errors='replace'))
        tag = root.tag
        if '}' in tag:
            tag = tag.split('}', 1)[1]
        return tag.lower() in ('score-partwise', 'score-timewise', 'score')
    except Exception:
        return False


def write_bytes(path: str, b: bytes):
    with open(path, 'wb') as f:
        f.write(b)


def convert_mid_to_musicxml(mid_bytes: bytes, out_path: str) -> bool:
    try:
        from music21 import converter
    except Exception:
        print('Error: music21 not installed. Install requirements with pip.', file=sys.stderr)
        return False

    with tempfile.NamedTemporaryFile(delete=False, suffix='.mid') as tf:
        tf.write(mid_bytes)
        tf.flush()
        tf_name = tf.name

    try:
        score = converter.parse(tf_name)
        score.write('musicxml', fp=out_path)
        return True
    except Exception as e:
        print('MIDI -> MusicXML conversion failed:', e, file=sys.stderr)
        return False
    finally:
        try:
            os.unlink(tf_name)
        except Exception:
            pass


def parse_playscore_to_score(path: str, verbose: bool = False):
    """Try to return a music21 score/stream parsed from the playscore, or None.
    Uses doc.xml (if MusicXML) or doc.mid fallback.
    """
    try:
        from music21 import converter
    except Exception:
        if verbose:
            print('music21 not available; cannot parse to music21 stream.', file=sys.stderr)
        return None

    try:
        with zipfile.ZipFile(path, 'r') as z:
            names = z.namelist()
            if 'doc.xml' in names:
                b = z.read('doc.xml')
                if is_musicxml_bytes(b):
                    tf = tempfile.NamedTemporaryFile(delete=False, suffix='.musicxml')
                    tf.write(b)
                    tf.flush(); tf.close()
                    try:
                        score = converter.parse(tf.name)
                        return score
                    finally:
                        try:
                            os.unlink(tf.name)
                        except Exception:
                            pass

            if 'doc.mid' in names:
                mb = z.read('doc.mid')
                tf = tempfile.NamedTemporaryFile(delete=False, suffix='.mid')
                tf.write(mb)
                tf.flush(); tf.close()
                try:
                    score = converter.parse(tf.name)
                    return score
                finally:
                    try:
                        os.unlink(tf.name)
                    except Exception:
                        pass

            for name in names:
                if name.lower().endswith('.xml'):
                    b = z.read(name)
                    if is_musicxml_bytes(b):
                        tf = tempfile.NamedTemporaryFile(delete=False, suffix='.musicxml')
                        tf.write(b)
                        tf.flush(); tf.close()
                        try:
                            score = converter.parse(tf.name)
                            return score
                        finally:
                            try:
                                os.unlink(tf.name)
                            except Exception:
                                pass

    except zipfile.BadZipFile:
        if verbose:
            print(f'Warning: {path} is not a valid ZIP/.playscore archive, skipping.', file=sys.stderr)
        return None

    if verbose:
        print(f'No usable MusicXML or MIDI found in {path}, skipping.', file=sys.stderr)
    return None


def extract_musicxml_bytes_from_playscore(path: str):
    """Return MusicXML bytes if present in archive (doc.xml or any .xml that looks like MusicXML), else None."""
    try:
        with zipfile.ZipFile(path, 'r') as z:
            names = z.namelist()
            if 'doc.xml' in names:
                b = z.read('doc.xml')
                if is_musicxml_bytes(b):
                    return b
            if 'doc.mid' in names:
                return None
            for name in names:
                if name.lower().endswith('.xml'):
                    b = z.read(name)
                    if is_musicxml_bytes(b):
                        return b
    except zipfile.BadZipFile:
        return None
    return None


def process_single_file(inp: str, out: str, overwrite: bool = False, verbose: bool = False) -> int:
    """Process single .playscore -> produce MusicXML at out.
    Returns 0 on success, non-zero on error.
    """
    if not os.path.isfile(inp):
        if verbose:
            print('Input file not found:', inp, file=sys.stderr)
        return 2

    if os.path.exists(out) and not overwrite:
        if verbose:
            print('Output exists and --overwrite not set; skipping:', out)
        return 0

    # try to extract an xml directly
    try:
        with zipfile.ZipFile(inp, 'r') as z:
            names = z.namelist()
            if 'doc.xml' in names:
                if verbose:
                    print('Found doc.xml; checking MusicXML...')
                b = z.read('doc.xml')
                if is_musicxml_bytes(b):
                    write_bytes(out, b)
                    if verbose:
                        print('Wrote MusicXML to', out)
                    return 0
                else:
                    if verbose:
                        print('doc.xml is not recognized as MusicXML; will try MIDI.')

            if 'doc.mid' in names:
                if verbose:
                    print('Found doc.mid; converting MIDI -> MusicXML (requires music21)')
                midb = z.read('doc.mid')
                ok = convert_mid_to_musicxml(midb, out)
                if ok:
                    if verbose:
                        print('Wrote MusicXML to', out)
                    return 0
                else:
                    if verbose:
                        print('MIDI conversion failed for', inp, file=sys.stderr)
                    return 3

            # fallback: try any xml
            for name in names:
                if name.lower().endswith('.xml'):
                    b = z.read(name)
                    if is_musicxml_bytes(b):
                        write_bytes(out, b)
                        if verbose:
                            print(f'Found {name} that looks like MusicXML; extracted to {out}')
                        return 0

            if verbose:
                print('No MusicXML or MIDI found in the archive. Entries:')
                for n in names:
                    print(' -', n)
            return 4

    except zipfile.BadZipFile:
        if verbose:
            print('Input is not a valid ZIP/.playscore archive', file=sys.stderr)
        return 2


def merge_files(inputs: list, out_path: str, overwrite: bool = False, verbose: bool = False) -> int:
    """Merge parsed parts from input .playscore files into a single MusicXML.
    Returns 0 on success, non-zero on error.
    """
    if os.path.exists(out_path) and not overwrite:
        if verbose:
            print('Output exists and --overwrite not set; skipping merge:', out_path)
        return 0

    try:
        from music21 import stream
    except Exception:
        print('music21 is required for merging (install with pip).', file=sys.stderr)
        return 3

    parsed_scores = []
    for f in inputs:
        if verbose:
            print('Parsing', f)
        s = parse_playscore_to_score(f, verbose=verbose)
        if s is not None:
            parsed_scores.append((f, s))

    if not parsed_scores:
        if verbose:
            print('No parsable scores found among inputs. Exiting.', file=sys.stderr)
        return 4

    combined = stream.Score()
    part_count = 0
    for fname, s in parsed_scores:
        if hasattr(s, 'parts') and len(s.parts) > 0:
            for p in s.parts:
                combined.append(p)
                part_count += 1
        else:
            combined.append(s)
            part_count += 1

    if verbose:
        print(f'Combined {len(parsed_scores)} scores into {part_count} parts. Writing {out_path} ...')
    try:
        combined.write('musicxml', fp=out_path)
        if verbose:
            print('Wrote merged MusicXML to', out_path)
        return 0
    except Exception as e:
        print('Failed to write combined MusicXML:', e, file=sys.stderr)
        return 5


def main():
    p = argparse.ArgumentParser(description='Convert .playscore to MusicXML (single or multiple; supports merge)')
    p.add_argument('inputs', nargs='*', help='input .playscore files (optional)')
    p.add_argument('-o', '--output', help='output MusicXML file path (for single or merged output)')
    p.add_argument('--merge', action='store_true', help='merge multiple inputs into one MusicXML')
    p.add_argument('--overwrite', action='store_true', help='overwrite existing output files')
    p.add_argument('--verbose', action='store_true', help='verbose output')
    args = p.parse_args()

    files = args.inputs or []

    # If no inputs provided, open file selector (interactive: after each
    # selection ask whether to add another). Use messagebox when available,
    # otherwise fall back to console prompts.
    if not files:
        if filedialog is not None:
            try:
                root = tk.Tk()
                root.withdraw()
                files = []
                # interactive loop: allow selecting multiple files one by one
                while True:
                    sel = filedialog.askopenfilename(title='Select .playscore file', filetypes=[('PlayScore files', '*.playscore'), ('All files', '*.*')])
                    if not sel:
                        break
                    files.append(sel)
                    # if messagebox available, ask yes/no; otherwise ask via console
                    more = None
                    if messagebox is not None:
                        try:
                            more = messagebox.askyesno('Ajouter un fichier', 'Voulez-vous ajouter un autre fichier ?')
                        except Exception:
                            more = None
                    if more is None:
                        try:
                            ans = input('Ajouter un autre fichier ? [y/N]: ').strip().lower()
                            more = ans in ('y', 'yes')
                        except Exception:
                            more = False
                    if not more:
                        break
                root.destroy()
            except Exception:
                files = []
        else:
            if args.verbose:
                print('No input files provided and tkinter not available; using console prompts.', file=sys.stderr)
            files = []
            try:
                while True:
                    inp = input('Enter path to .playscore file (blank to finish): ').strip()
                    if not inp:
                        break
                    files.append(inp)
                    ans = input('Ajouter un autre fichier ? [y/N]: ').strip().lower()
                    if ans not in ('y', 'yes'):
                        break
            except Exception:
                pass

    files = [f for f in files if f and os.path.isfile(f)]
    if not files:
        print('No valid input files selected. Exiting.', file=sys.stderr)
        sys.exit(2)

    # If multiple files selected and --merge not explicitly set, ask interactively
    if len(files) > 1 and not args.merge:
        merge_choice = None
        if messagebox is not None:
            try:
                # create a temporary root to show messagebox if needed
                root_mb = tk.Tk()
                root_mb.withdraw()
                merge_choice = messagebox.askyesno('Fusionner les fichiers', 'Voulez-vous fusionner les fichiers sélectionnés en un seul MusicXML ?')
                root_mb.destroy()
            except Exception:
                merge_choice = None

        if merge_choice is None:
            try:
                ans = input('Voulez-vous fusionner les fichiers sélectionnés en un seul MusicXML ? [y/N]: ').strip().lower()
                merge_choice = ans in ('y', 'yes')
            except Exception:
                merge_choice = False

        if merge_choice:
            args.merge = True

    # Single file path and no merge: process each input independently (or single)
    if not args.merge:
        exit_code = 0
        for f in files:
            if args.output and len(files) == 1:
                out = args.output
            else:
                base = os.path.splitext(os.path.basename(f))[0]
                input_dir = os.path.dirname(os.path.abspath(f)) or os.getcwd()
                out = os.path.join(input_dir, base + '.musicxml')

            rc = process_single_file(f, out, overwrite=args.overwrite, verbose=args.verbose)
            if rc != 0:
                exit_code = rc
        sys.exit(exit_code)

    # Merge mode
    if args.merge:
        if args.output:
            out_path = args.output
        else:
            first_dir = os.path.dirname(os.path.abspath(files[0]))
            out_path = os.path.join(first_dir, 'merged.musicxml')
        rc = merge_files(files, out_path, overwrite=args.overwrite, verbose=args.verbose)
        sys.exit(rc)


if __name__ == '__main__':
    main()
