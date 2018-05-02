'''
Class for the ogs PARTICLE DEFINITION file for RANDOM_WALK.
'''

from __future__ import absolute_import, division, print_function
import os
import numpy as np

CWD = os.getcwd()


class PCT(object):
    """
    Class for the ogs Particle file, if the PCS TYPE is RANDOM_WALK
    """
    def __init__(self, data=None, s_flag=1, task_root=CWD, task_id="ogs"):
        '''
        Input
        -----
        '''
        self.s_flag = s_flag
        self.task_root = task_root
        self.task_id = task_id
        self.f_type = ".pct"
        if data:
            self.data = np.array(data)
        else:
            self.data = np.zeros((0, 10))

    def check(self, verbose=True):
        '''
        Check if the external geometry definition is valid in the sence,
        that the contained data is consistent.

        Parameters
        ----------
        verbose : bool, optional
            Print information for the executed checks. Default: True

        Returns
        -------
        result : bool
            Validity of the given gli.
        '''
        if self.data.ndim != 2:
            if verbose:
                print("PCT: Data shape incorect")
            return False
        elif self.data.shape[1] != 10:
            if verbose:
                print("PCT: Data shape incorect")
            return False
        return True

    def reset(self):
        '''
        Delete every content.
        '''
        self.data = np.zeros((0, 10))

    def save(self, path):
        '''
        Save the actual GLI external file in the given path.

        Parameters
        ----------
        path : str
            path to where to file should be saved
        '''
        if self.data.shape[0] >= 1:
            with open(path, "w") as fout:
                print(str(self.s_flag), file=fout)
                print(str(self.data.shape[0]), file=fout)
                np.savetxt(fout, self.data)

    def read_file(self, path):
        '''
        Write the actual OGS input file to the given folder.
        Its path is given by "task_root+task_id+f_type".
        '''
        with open(path, "r") as fin:
                self.s_flag = int(fin.readline())

        self.data = np.loadtxt(path, skiprows=2)

    def write_file(self):
        '''
        Write the actual OGS input file to the given folder.
        Its path is given by "task_root+task_id+f_type".
        '''
        # create the file path
        if not os.path.exists(self.task_root):
            os.makedirs(self.task_root)
        f_path = os.path.join(self.task_root, self.task_id+self.f_type)
        # save the data
        self.save(f_path)

    def __repr__(self):
        """
        Return a formatted representation of the file.

        Info
        ----
        Type : str
        """
        out = str(self.s_flag)+"\n"
        out += str(self.data.shape[0])+"\n"
        out += str(self.data)
        return out

    def __str__(self):
        """
        Return a formatted representation of the file.

        Info
        ----
        Type : str
        """
        return self.__repr__()