#!/usr/bin/env/python

import os
import dircache

if __name__ == "__main__":
    dir_list = [
        "blue", "chartreuse", "cyan", "dark_gray", "dark_purple", "deep_pink",
        "dodger_blue", "gold", "green_yellow", "orange", "purple", "red",
        "yellow" ]
    rename_list = []
    f_name_list = open("../instruct.txt", "r")
    name = f_name_list.readline()
    while len(name) > 3:
        rename_list.append(name[:-1])
        name = f_name_list.readline()
    for d in dir_list:
        # First rename
        new_file_list = []
        file_list = dircache.opendir(d)
        for f in file_list:
            idx = int(f[f.rfind("c") + 1 : f.rfind(".")])
            if idx < 10:
                idx = "0" + str(idx)
                os.chdir("./" + d)
                new_name = f[:f.rfind("c") + 1] + idx + ".png"
                os.rename(f, new_name)
                os.chdir("..")
                new_file_list.append(new_name)
            else:
                new_file_list.append(f)
        new_file_list.sort()
        print new_file_list
        # Second rename
        os.chdir("./" + d)
        i = 0
        while i < len(new_file_list):
            print new_file_list[i], rename_list[i]
            os.rename(new_file_list[i], rename_list[i])
            i += 1
        os.chdir("..")
