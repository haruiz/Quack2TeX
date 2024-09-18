import argparse
from pathlib import Path


def create_resource_file_from_folder_files(folder: Path, output_file: Path):
    """Create a PyQt5 resource file from a list of files.
    Arguments:
        files -- a list of file names to be included in the resource file
        resource_file_name -- the name of the resource file to be generated
    Returns:
        None
    """
    print(f"Creating resource file {output_file} from files in folder {folder}")
    file_extensions = ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp", "*.tiff", "*.ico", "*.qss", "*.ttf", "*.html"]
    resource_files = [file for ext in file_extensions for file in folder.rglob(ext)]
    with open(output_file, "w") as f:
        f.write("<RCC>\n")
        f.write('  <qresource prefix="/">\n')
        for file in resource_files:
            print(f"Adding file {file}")
            f.write("    <file>{}</file>\n".format(file.relative_to(folder)))
        f.write("  </qresource>\n")
        f.write("</RCC>\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create a PyQt5 resource file from a list of files."
    )
    parser.add_argument(
        "folder",
        type=Path,
        help="The folder containing the files to be included in the resource file",
    )
    parser.add_argument(
        "output_file", type=Path, help="The name of the resource file to be generated"
    )
    args = parser.parse_args()

    create_resource_file_from_folder_files(args.folder, args.output_file)
