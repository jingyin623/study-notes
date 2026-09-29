# srcfile 需要复制、移动的文件
# dstpath 目的地址

import os
import shutil
from glob import glob


def mycopyfile(srcfile, dstpath):  # 复制函数
    if not os.path.isfile(srcfile):
        print("%s not exist!" % (srcfile))
    else:
        fpath, fname = os.path.split(srcfile)  # 分离文件名和路径
        if not os.path.exists(dstpath):
            os.makedirs(dstpath)  # 创建路径
        shutil.copy(srcfile, dstpath + fname)  # 复制文件
        print("copy %s -> %s" % (srcfile, dstpath + fname))


def mycopyfile1(srcfile, dstpath):  # 复制函数
    if not os.path.isfile(srcfile):
        print("%s not exist!" % (srcfile))
    else:
        fpath, fname = os.path.split(srcfile)  # 分离文件名和路径
        if not os.path.exists(dstpath):
            os.makedirs(dstpath)  # 创建路径
        shutil.copy(srcfile, dstpath + fname)  # 复制文件
        print("copy %s -> %s" % (srcfile, dstpath + fname))

if __name__ == '__main__':

    src_dir = 'D:/Program Files/JetBrains/.vennv/PyQt5_Trading/Lib/site-packages/futu/common/pb/'
    dst_dir = 'D:/Program Files/JetBrains/pythonProject/PyQt5_Trading/PyQt5_Trading_GetsJumpPoint/dist/GetsJumpPoint_Pane/_internal/'  # 目的路径记得加斜杠
    src_file_list = glob(src_dir + '*')  # glob获得路径下所有文件，可根据需要修改
    for srcfile in src_file_list:
        mycopyfile(srcfile, dst_dir)  # 复制文件

    src_dir1 = 'D:/Program Files/JetBrains/.vennv/PyQt5_Trading/Lib/site-packages/futu/'
    dst_dir1 = 'D:/Program Files/JetBrains/pythonProject/PyQt5_Trading/PyQt5_Trading_GetsJumpPoint/dist/GetsJumpPoint_Pane/_internal/futu/'  # 目的路径记得加斜杠
    src_file_list = glob(src_dir1 + 'VERSION.txt')  # glob获得路径下所有文件，可根据需要修改
    for srcfile in src_file_list:
        mycopyfile1(srcfile, dst_dir1)  # 复制文件