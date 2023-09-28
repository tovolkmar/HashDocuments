import argparse
import hashlib
import glob
import os
import json
import sqlite3
from datetime import datetime
from stat import S_IREAD, S_IRGRP, S_IROTH

def main (config_file):
    # Opening JSON file
    config = open(config_file, "rb")

    # returns JSON object as a dictionary
    config_data = json.load(config)


    con = sqlite3.connect(config_data['database'])
    cur = con.cursor()

    outputFileName = datetime.now().strftime('%Y-%m-%d') + '.txt'
    newFiles = 0

    for directory in config_data['input_directories']:
        print('Start searching directory ' + directory['path'])

        dir_name = directory['path']
        if 'number_range' in directory:
            dir_name + directory['number_range']
        # Get list of all files in a given directory sorted by name
        list_of_files = sorted(filter(os.path.isfile, glob.glob(f'{dir_name}*')))
        # Iterate over sorted list of files one by one.
        for file_path in list_of_files:
            # file modification timestamp of a file
            m_time = os.path.getmtime(file_path)
            # convert timestamp into DateTime object
            dt_m = datetime.fromtimestamp(m_time)

            # get file creation time on mac
            stat = os.stat(file_path)
            c_timestamp = stat.st_birthtime
            dt_c = datetime.fromtimestamp(c_timestamp)

            print(f"{os.path.basename(file_path)} (created on {dt_c}) (modified on {dt_m})")

            file_name_base_dir = file_path[file_path.find(config_data['base_directory']) :]
            hash_sha256 = hashlib.sha256()

            if checkFileExists := cur.execute(
                "SELECT * FROM documents WHERE filepath=?", (file_name_base_dir,)
            ).fetchone():
                print(f"File {file_path} already exists in database. Skipping...")
                continue

            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)

                dt = datetime.now()

                output_file = config_data['output_dir'] + '/' + outputFileName
                with open(output_file, "a") as target:
                    target.write(f'{hash_sha256.hexdigest()} - {file_name_base_dir}' + '\n')
            
            # Insert data into database with 
            InsertData = cur.execute(
                "INSERT INTO documents VALUES (?,?,?,?,?)",
                (file_name_base_dir, dt_c, dt_m, hash_sha256.hexdigest(), dt),
            )
            con.commit()

            # Set the immutable flag on the file and set them read only
            flags = os.stat(file_path).st_flags
            os.chflags(file_path, flags | stat.UF_IMMUTABLE)
            os.chmod(file_path, S_IREAD|S_IRGRP|S_IROTH)

            newFiles += 1
    print('Done!')
    print(f'New files: {newFiles}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Arguments for hash documents"
    )
    parser.add_argument(
        "-c", "--Config", help="Config file", required=True
    )

    args = parser.parse_args()
    main(args.Config)
   